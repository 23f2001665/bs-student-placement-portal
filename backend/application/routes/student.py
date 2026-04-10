from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

from flask import Blueprint, current_app, request, send_file, session
from sqlalchemy import and_, select, func, or_
from sqlalchemy.exc import DataError, IntegrityError, StatementError

from ...extensions import celery, db
from ...tasks.export import export_student_applications_csv, get_student_export_dir
from ..errors import db_error_message
from .common import parse_enum
from ..services.cache import RouteCache
from ..models import (
	Application,
	ApplicationStatus,
	Company,
	Drive,
	DriveApprovalStatus,
	DriveStatus,
	Gender,
	Student,
	User,
	UserType,
	WorkMode,
)


route_cache = RouteCache()


def _build_cache_key(prefix):
	params = [(k, v) for k, v in request.args.items() if v is not None and str(v).strip() != ""]
	params.sort(key=lambda item: item[0])
	query = urlencode(params)
	return f"{prefix}?{query}" if query else prefix


def _parse_pagination():
	page = request.args.get("page", type=int)
	limit = request.args.get("limit", type=int)

	if page is None and limit is None:
		return None, None

	page = page or 1
	limit = limit or 10

	if page < 1:
		raise ValueError("page must be >= 1")
	if limit < 1 or limit > 50:
		raise ValueError("limit must be between 1 and 50")

	return page, limit


def _pagination_payload(page, limit, total):
	total_pages = max(1, (total + limit - 1) // limit)
	has_prev = page > 1
	has_next = page < total_pages
	return {
		"page": int(page),
		"limit": int(limit),
		"total": int(total),
		"total_pages": int(total_pages),
		"has_prev": has_prev,
		"has_next": has_next,
		"prev_page": int(page - 1) if has_prev else None,
		"next_page": int(page + 1) if has_next else None,
	}


def _export_job_cache_key(student_id, task_id):
	return f"api:student:{student_id}:exports:{task_id}"


def _session_export_tasks_key(student_id):
	return f"student_export_tasks:{student_id}"


def _get_session_export_tasks(student_id):
	key = _session_export_tasks_key(student_id)
	items = session.get(key)
	if not isinstance(items, list):
		return []
	return [str(item) for item in items if item]


def _remember_session_export_task(student_id, task_id, max_items=30):
	key = _session_export_tasks_key(student_id)
	items = _get_session_export_tasks(student_id)
	task_token = str(task_id)
	if task_token in items:
		items = [token for token in items if token != task_token]
	items.insert(0, task_token)
	session[key] = items[:max_items]
	session.modified = True


def _normalize_export_status(state):
	state_key = (state or "pending").lower()
	if state_key == "success":
		return "completed"
	if state_key in {"failure", "revoked"}:
		return "failed"
	if state_key in {"started", "retry"}:
		return "running"
	return "queued"


def _student_drive_eligibility_payload(student, drive):
	reasons = []
	if drive.min_cgpa is not None and (student.cgpa is None or student.cgpa < drive.min_cgpa):
		reasons.append(f"Minimum CGPA required: {drive.min_cgpa}")

	allowed = drive.allowed_branches_list
	if allowed and student.branch and student.branch.name not in allowed:
		reasons.append("Branch not eligible")

	return {
		"eligible_for_apply": len(reasons) == 0,
		"eligibility_reasons": reasons,
	}


def student_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		current_user_id = session.get("current_user")
		if not current_user_id:
			return {"error": "Authentication required"}, 401

		current_user = db.session.execute(
			select(User).where(User.id == current_user_id)
		).scalar_one_or_none()

		if not current_user:
			return {"error": "Authentication required"}, 401

		if current_user.user_type != UserType.student:
			return {"error": "Student access required"}, 403

		student = db.session.execute(
			select(Student).where(Student.id == current_user.id)
		).scalar_one_or_none()

		if not student:
			session.clear()
			return {"error": "Student not found"}, 401

		if not student.is_active:
			return {"error": "Student account is blocked"}, 403

		return f(student, *args, **kwargs)

	return decorated_function


student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/profile/", methods=["GET"])
@student_required
def view_profile(student):
	cache_key = f"api:student:{student.id}:profile"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	payload = {"student": student.to_dict()}
	route_cache.set_json(cache_key, payload, 60)
	return payload, 200


@student_bp.route("/profile/resume/", methods=["GET"])
@student_required
def view_profile_resume(student):
	resume_path = (student.resume_path or "").strip()
	if not resume_path:
		return {"error": "Resume not found"}, 404

	project_root = Path(current_app.root_path).parent
	resolved = (project_root / resume_path).resolve()
	uploads_root = (project_root / "uploads").resolve()

	if uploads_root not in resolved.parents:
		return {"error": "Invalid resume path"}, 400
	if not resolved.exists() or not resolved.is_file():
		return {"error": "Resume file not found"}, 404

	return send_file(resolved, mimetype="application/pdf")


@student_bp.route("/profile/update/", methods=["PUT"])
@student_required
def update_profile(student):
	is_multipart = bool(request.content_type and request.content_type.startswith("multipart/form-data"))
	data = request.form if is_multipart else (request.get_json(silent=True) or {})
	resume_file = request.files.get("resume") if is_multipart else None

	try:
		if "name" in data:
			student.name = (data.get("name") or "").strip()

		if "gender" in data:
			student.gender = parse_enum(Gender, data.get("gender"), "gender", required=False)

		if "current_level" in data:
			student.current_level = int(data.get("current_level"))

		if "cgpa" in data:
			student.cgpa = float(data["cgpa"]) if data.get("cgpa") not in (None, "") else None

		if "resume_path" in data:
			student.resume_path = (data.get("resume_path") or "").strip() or None

		if resume_file and resume_file.filename:
			if not resume_file.filename.lower().endswith(".pdf"):
				return {"error": "Resume must be a PDF file"}, 400

			resume_file.stream.seek(0, 2)
			resume_size = resume_file.stream.tell()
			resume_file.stream.seek(0)

			if resume_size > 1024 * 1024:
				return {"error": "Resume file must be 1MB or smaller"}, 400

			uploads_dir = Path(current_app.root_path).parent / "uploads"
			uploads_dir.mkdir(parents=True, exist_ok=True)

			resume_filename = f"{student.id}.pdf"
			resume_path = uploads_dir / resume_filename
			resume_file.save(resume_path)
			student.resume_path = f"uploads/{resume_filename}"

		db.session.commit()
	except (ValueError, TypeError) as exc:
		db.session.rollback()
		return {"error": str(exc)}, 400
	except (IntegrityError, DataError, StatementError) as exc:
		db.session.rollback()
		return {
			"error": "Profile validation failed",
			"details": db_error_message(exc),
		}, 400

	route_cache.delete_prefix(f"api:student:{student.id}:")
	return {
		"message": "Profile updated successfully",
		"student": student.to_dict(),
	}, 200


@student_bp.route("/drives/", methods=["GET"])
@student_required
def view_available_drives(student):
	cache_key = _build_cache_key(f"api:student:{student.id}:drives")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	search = (request.args.get("search") or "").strip()
	status_filter = (request.args.get("status") or "").strip()
	work_mode_filter = (request.args.get("work_mode") or "").strip()
	application_filter = (request.args.get("application_filter") or "").strip().lower()
	sort_by = (request.args.get("sort_by") or "priority").strip().lower()
	sort_order = (request.args.get("sort_order") or "asc").strip().lower()

	try:
		page, limit = _parse_pagination()
		status_enum = parse_enum(DriveStatus, status_filter, "status", required=False)
		work_mode_enum = parse_enum(WorkMode, work_mode_filter, "work_mode", required=False)
	except ValueError as exc:
		return {"error": str(exc)}, 400

	if sort_order not in {"asc", "desc"}:
		return {"error": "sort_order must be 'asc' or 'desc'"}, 400

	allowed_application_filters = {
		"applied",
		"not_applied_but_eligible",
		"not_eligible",
	}
	if application_filter and application_filter not in allowed_application_filters:
		allowed = ", ".join(sorted(allowed_application_filters))
		return {"error": f"Invalid application_filter. Allowed values: {allowed}"}, 400

	sort_columns = {
		"priority": None,
		"id": Drive.id,
		"create_date": Drive.create_date,
		"start_date": Drive.start_date,
		"end_date": Drive.end_date,
		"title": func.lower(Drive.title),
		"min_cgpa": Drive.min_cgpa,
	}
	if sort_by not in sort_columns:
		allowed = ", ".join(sorted(sort_columns.keys()))
		return {"error": f"Invalid sort_by. Allowed values: {allowed}"}, 400
	sort_column = sort_columns[sort_by]

	query = select(Drive).where(
		and_(
			Drive.is_active.is_(True),
			Drive.approval_status == DriveApprovalStatus.approved,
			Drive.effective_status.in_([
				DriveStatus.active.name,
				DriveStatus.pending.name,
				DriveStatus.upcoming.name,
				DriveStatus.closed.name,
			]),
		)
	)
	query = query.join(Company, Company.id == Drive.company_id).where(
		and_(
			Company.is_active.is_(True),
			Company.is_approved.is_(True),
		)
	)

	if search:
		pattern = f"%{search}%"
		query = query.where(or_(Drive.title.ilike(pattern), Drive.description.ilike(pattern)))

	if status_enum is not None:
		query = query.where(Drive.effective_status == status_enum.name)

	if work_mode_enum is not None:
		query = query.where(Drive.work_mode == work_mode_enum)

	if sort_by == "priority":
		# Keep deterministic base order before in-memory priority sort.
		query = query.order_by(Drive.create_date.desc(), Drive.id.desc())
	else:
		order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
		query = query.order_by(order_clause, Drive.id.desc())
	drives = db.session.execute(query).scalars().all()
	drive_ids = [drive.id for drive in drives]
	application_map = {}
	if drive_ids:
		applied_rows = db.session.execute(
			select(Application.drive_id, Application.status).where(
				and_(
					Application.student_id == student.id,
					Application.drive_id.in_(drive_ids),
				)
			)
		).all()
		application_map = {
			int(drive_id): status.value if status else None
			for drive_id, status in applied_rows
		}

	visible_drives = []
	for drive in drives:
		drive_payload = drive.to_dict()
		drive_payload["drive_status"] = drive.effective_status.value if drive.effective_status else None
		drive_payload.update(_student_drive_eligibility_payload(student, drive))
		drive_payload["already_applied"] = drive.id in application_map
		drive_payload["application_status"] = application_map.get(drive.id)
		visible_drives.append(drive_payload)

	if application_filter == "applied":
		visible_drives = [item for item in visible_drives if item.get("already_applied")]
	elif application_filter == "not_applied_but_eligible":
		visible_drives = [
			item
			for item in visible_drives
			if (not item.get("already_applied")) and item.get("eligible_for_apply")
		]
	elif application_filter == "not_eligible":
		visible_drives = [item for item in visible_drives if not item.get("eligible_for_apply")]

	if sort_by == "priority":
		status_rank = {
			"active": 0,
			"upcoming": 1,
			"closed": 2,
			"pending": 3,
			"cancelled": 4,
		}

		def _priority_key(item):
			eligible_rank = 0 if item.get("eligible_for_apply") else 1
			status_key = str(item.get("drive_status") or item.get("status") or "").lower()
			status_order = status_rank.get(status_key, 9)
			applied_rank = 1 if item.get("already_applied") else 0
			return (eligible_rank, status_order, applied_rank)

		visible_drives.sort(key=_priority_key, reverse=(sort_order == "desc"))
	else:
		visible_drives.sort(key=lambda item: 0 if item.get("eligible_for_apply") else 1)

	if page is None and limit is None:
		payload = {"drives": visible_drives}
		route_cache.set_json(cache_key, payload, 30)
		return payload, 200

	total = len(visible_drives)
	start = (page - 1) * limit
	end = start + limit
	payload = {
		"drives": visible_drives[start:end],
		"pagination": _pagination_payload(page, limit, total),
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@student_bp.route("/drives/<int:drive_id>/", methods=["GET"])
@student_required
def view_drive_detail(student, drive_id):
	drive = db.session.execute(
		select(Drive)
		.join(Company, Company.id == Drive.company_id)
		.where(
			and_(
				Drive.id == drive_id,
				Drive.is_active.is_(True),
				Drive.approval_status == DriveApprovalStatus.approved,
				Drive.effective_status.in_([
					DriveStatus.active.name,
					DriveStatus.pending.name,
					DriveStatus.upcoming.name,
					DriveStatus.closed.name,
				]),
				Company.is_active.is_(True),
				Company.is_approved.is_(True),
			)
		)
	).scalar_one_or_none()

	if not drive:
		return {"error": "Drive not found"}, 404

	existing_application = db.session.execute(
		select(Application).where(
			and_(Application.student_id == student.id, Application.drive_id == drive.id)
		)
	).scalar_one_or_none()
	already_applied = existing_application is not None

	payload = drive.to_dict()
	payload["drive_status"] = drive.effective_status.value if drive and drive.effective_status else None
	payload.update(_student_drive_eligibility_payload(student, drive))
	payload["already_applied"] = already_applied
	payload["application_status"] = (
		existing_application.status.value if existing_application and existing_application.status else None
	)
	if drive.company:
		payload["company"] = {
			"id": drive.company.id,
			"name": drive.company.name,
			"industry_type": drive.company.industry_type.value if drive.company.industry_type else None,
		}

	return {"drive": payload}, 200


@student_bp.route("/companies/<int:company_id>/", methods=["GET"])
@student_required
def view_company_detail(student, company_id):
	cache_key = f"api:student:{student.id}:companies:detail:{company_id}"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	company = db.session.execute(
		select(Company).where(
			and_(
				Company.id == company_id,
				Company.is_active.is_(True),
				Company.is_approved.is_(True),
			)
		)
	).scalar_one_or_none()

	if not company:
		return {"error": "Company not found"}, 404

	drives = db.session.execute(
		select(Drive)
		.where(
			and_(
				Drive.company_id == company.id,
				Drive.approval_status == DriveApprovalStatus.approved,
			)
		)
		.order_by(Drive.start_date.desc(), Drive.id.desc())
	).scalars().all()

	drives_payload = []
	for drive in drives:
		drive_payload = drive.to_dict()
		drive_payload["drive_status"] = drive.effective_status.value if drive.effective_status else None
		drives_payload.append(drive_payload)

	payload = {
		"company": {
			"id": company.id,
			"name": company.name,
			"industry_type": company.industry_type.value if company.industry_type else None,
			"website": company.website,
			"description": company.description,
		},
		"drives": drives_payload,
	}

	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@student_bp.route("/drives/<int:drive_id>/apply/", methods=["POST"])
@student_required
def apply_to_drive(student, drive_id):
	if db.session.bind and db.session.bind.dialect.name == "sqlite":
		db.session.execute(db.text("BEGIN IMMEDIATE"))

	drive = db.session.execute(
		select(Drive).where(Drive.id == drive_id).with_for_update()
	).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404

	if drive.approval_status != DriveApprovalStatus.approved:
		return {"error": "Only approved drives can be applied to"}, 400

	if not drive.is_active:
		return {"error": "Drive is unavailable"}, 400

	if drive.effective_status != DriveStatus.active:
		return {"error": "Drive is not accepting applications"}, 400

	company = drive.company
	if not company or not company.is_active:
		return {"error": "Company is unavailable"}, 400

	if not company.is_approved:
		return {"error": "Company is not approved"}, 400

	if drive.min_cgpa is not None and (student.cgpa is None or student.cgpa < drive.min_cgpa):
		return {"error": "You are not eligible for this drive"}, 400

	allowed = drive.allowed_branches_list
	if allowed and student.branch and student.branch.name not in allowed:
		return {"error": "You are not eligible for this drive"}, 400

	if drive.max_applications is not None:
		total_applications = db.session.execute(
			select(func.count(Application.id)).where(Application.drive_id == drive.id)
		).scalar_one()
		if total_applications >= drive.max_applications:
			return {"error": "Application limit reached for this drive"}, 400

	data = request.get_json(silent=True) or {}
	resume_note = (data.get("resume_note") or "").strip() or None

	application = Application(
		student_id=student.id,
		drive_id=drive.id,
		application_date=datetime.now(),
		status=ApplicationStatus.applied,
		resume_note=resume_note,
		resume_link=student.resume_path,
	)

	db.session.add(application)
	try:
		db.session.commit()
	except (IntegrityError, DataError, StatementError) as exc:
		db.session.rollback()
		message = db_error_message(exc)
		if "already applied" in message.lower() or "duplicate" in message.lower():
			return {"error": "Already applied to this drive"}, 409
		return {"error": message}, 400

	route_cache.delete_prefix(f"api:student:{student.id}:")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:drives:{drive.id}:applications")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:applications")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:summary")
	return {
		"message": "Application submitted successfully",
		"application": application.to_dict(),
	}, 201


@student_bp.route("/applications/", methods=["GET"])
@student_required
def view_applications(student):
	cache_key = _build_cache_key(f"api:student:{student.id}:applications")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	status_filter = (request.args.get("status") or "").strip().lower()
	search = (request.args.get("search") or "").strip()
	sort_by = (request.args.get("sort_by") or "application_date").strip().lower()
	sort_order = (request.args.get("sort_order") or "desc").strip().lower()

	try:
		page, limit = _parse_pagination()
	except ValueError as exc:
		return {"error": str(exc)}, 400

	if sort_order not in {"asc", "desc"}:
		return {"error": "sort_order must be 'asc' or 'desc'"}, 400

	sort_columns = {
		"application_date": Application.application_date,
		"status": Application.status,
		"drive_id": Drive.id,
		"drive_title": func.lower(Drive.title),
	}
	sort_column = sort_columns.get(sort_by)
	if sort_column is None:
		allowed = ", ".join(sorted(sort_columns.keys()))
		return {"error": f"Invalid sort_by. Allowed values: {allowed}"}, 400

	query = select(Application).where(Application.student_id == student.id)
	needs_drive_join = bool(search) or sort_by in {"drive_title", "drive_id"}
	if needs_drive_join:
		query = query.outerjoin(Drive, Application.drive_id == Drive.id)

	if status_filter:
		if status_filter in {"current", "active"}:
			query = query.where(Application.status.in_([ApplicationStatus.applied, ApplicationStatus.short_listed]))
		elif status_filter in {"history", "completed"}:
			query = query.where(Application.status.in_([ApplicationStatus.selected, ApplicationStatus.rejected]))
		else:
			status_member = {member.name.lower(): member for member in ApplicationStatus}.get(status_filter)
			if status_member is None:
				for member in ApplicationStatus:
					if str(member.value).lower() == status_filter:
						status_member = member
						break
			if status_member is None:
				return {"error": "Invalid status filter"}, 400
			query = query.where(Application.status == status_member)

	if search:
		pattern = f"%{search}%"
		query = query.where(
			or_(Drive.title.ilike(pattern), Drive.description.ilike(pattern))
		)

	order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
	applications = db.session.execute(
		query.order_by(order_clause, Application.id.desc())
	).scalars().all()

	payload = []
	for app in applications:
		drive = app.drive
		company = drive.company if drive else None

		app_payload = app.to_dict()
		app_payload["drive"] = (
			{
				"id": drive.id,
				"title": drive.title,
				"status": drive.effective_status.value if drive.effective_status else None,
				"approval_status": drive.approval_status.value if drive.approval_status else None,
				"company_id": drive.company_id,
			}
			if drive
			else {
				"id": None,
				"title": "Deleted drive",
				"status": None,
				"approval_status": None,
				"company_id": None,
			}
		)
		app_payload["company"] = (
			{
				"id": company.id,
				"name": company.name,
				"is_active": company.is_active,
				"is_approved": company.is_approved,
			}
			if company
			else {
				"id": None,
				"name": "Deleted company",
				"is_active": None,
				"is_approved": None,
			}
		)
		payload.append(app_payload)

	def _is_history_application(status):
		s = str(status or "").strip().lower()
		return s in {"selected", "rejected"}

	total_matching = len(payload)
	history_total = sum(1 for item in payload if _is_history_application(item.get("status")))
	current_total = total_matching - history_total
	summary_payload = {
		"total_matching": total_matching,
		"current": current_total,
		"history": history_total,
	}

	if page is None and limit is None:
		response_payload = {"applications": payload, "summary": summary_payload}
		route_cache.set_json(cache_key, response_payload, 30)
		return response_payload, 200

	total = len(payload)
	start = (page - 1) * limit
	end = start + limit
	response_payload = {
		"applications": payload[start:end],
		"pagination": _pagination_payload(page, limit, total),
		"summary": summary_payload,
	}
	route_cache.set_json(cache_key, response_payload, 30)
	return response_payload, 200


@student_bp.route("/applications/<int:application_id>/", methods=["GET"])
@student_required
def view_application_detail(student, application_id):
	cache_key = f"api:student:{student.id}:applications:detail:{application_id}"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	app = db.session.execute(
		select(Application)
		.where(
			and_(
				Application.id == application_id,
				Application.student_id == student.id,
			)
		)
	).scalar_one_or_none()

	if not app:
		return {"error": "Application not found"}, 404

	drive = app.drive
	company = drive.company if drive else None

	payload = {
		"application": app.to_dict(),
		"drive": (
			{
				"id": drive.id,
				"title": drive.title,
				"description": drive.description,
				"status": drive.effective_status.value if drive.effective_status else None,
				"approval_status": drive.approval_status.value if drive.approval_status else None,
				"work_mode": drive.work_mode.value if drive.work_mode else None,
				"start_date": drive.start_date.isoformat() if drive.start_date else None,
				"end_date": drive.end_date.isoformat() if drive.end_date else None,
				"company_id": drive.company_id,
			}
			if drive
			else None
		),
		"company": (
			{
				"id": company.id,
				"name": company.name,
				"email": company.email,
				"website": company.website,
				"is_active": company.is_active,
				"is_approved": company.is_approved,
			}
			if company
			else None
		),
	}

	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@student_bp.route("/applications/export/", methods=["POST"])
@student_required
def export_applications(student):
	task = export_student_applications_csv.delay(student.id)
	_remember_session_export_task(student.id, task.id)
	cache_key = _export_job_cache_key(student.id, task.id)
	route_cache.set_json(
		cache_key,
		{
			"student_id": student.id,
			"task_id": task.id,
			"status": "queued",
			"requested_at": datetime.now(timezone.utc).isoformat(),
		},
		3600,
	)

	return {
		"message": "Export started",
		"task_id": task.id,
	}, 202


@student_bp.route("/applications/export/<string:task_id>/status", methods=["GET"])
@student_required
def export_applications_status(student, task_id):
	cache_key = _export_job_cache_key(student.id, task_id)
	job_meta = route_cache.get_json(cache_key)
	session_tasks = set(_get_session_export_tasks(student.id))
	if not job_meta and task_id not in session_tasks:
		return {"error": "Export job not found"}, 404

	result = celery.AsyncResult(task_id)
	state = (result.state or "PENDING").lower()
	normalized_status = _normalize_export_status(state)
	payload = {
		"task_id": task_id,
		"state": state,
		"status": normalized_status,
		"requested_at": (job_meta or {}).get("requested_at"),
	}

	if state == "success":
		result_payload = result.result if isinstance(result.result, dict) else {}
		if result_payload.get("student_id") not in (None, student.id):
			return {"error": "Forbidden"}, 403

		payload.update(
			{
				"ready": True,
				"row_count": int(result_payload.get("row_count") or 0),
				"file_name": result_payload.get("file_name"),
				"download_url": result_payload.get("download_url"),
				"completed_at": datetime.now(timezone.utc).isoformat(),
			}
		)
	elif state in {"failure", "revoked"}:
		payload.update(
			{
				"ready": False,
				"error": str(result.result),
				"completed_at": datetime.now(timezone.utc).isoformat(),
			}
		)
	else:
		payload.update({"ready": False})

	persisted = {
		**(job_meta or {}),
		"student_id": student.id,
		"task_id": task_id,
		"requested_at": payload.get("requested_at") or (job_meta or {}).get("requested_at"),
		"status": payload.get("status"),
		"state": payload.get("state"),
		"ready": payload.get("ready", False),
		"row_count": payload.get("row_count"),
		"file_name": payload.get("file_name"),
		"download_url": payload.get("download_url"),
		"completed_at": payload.get("completed_at") or job_meta.get("completed_at"),
		"error": payload.get("error"),
	}
	route_cache.set_json(cache_key, persisted, 7 * 24 * 3600)

	return payload, 200


@student_bp.route("/applications/export/<string:task_id>/download", methods=["GET"])
@student_required
def export_applications_download(student, task_id):
	cache_key = _export_job_cache_key(student.id, task_id)
	job_meta = route_cache.get_json(cache_key)
	session_tasks = set(_get_session_export_tasks(student.id))
	if not job_meta and task_id not in session_tasks:
		return {"error": "Export job not found"}, 404

	result = celery.AsyncResult(task_id)
	if (result.state or "").lower() != "success":
		return {"error": "Export is not ready yet"}, 409

	result_payload = result.result if isinstance(result.result, dict) else {}
	if result_payload.get("student_id") not in (None, student.id):
		return {"error": "Forbidden"}, 403

	file_path = result_payload.get("file_path")
	if not file_path:
		return {"error": "Export file is unavailable"}, 404

	resolved = Path(file_path).resolve()
	base = get_student_export_dir(student.id).resolve()
	if base not in resolved.parents:
		return {"error": "Invalid export file path"}, 400
	if not resolved.exists() or not resolved.is_file():
		return {"error": "Export file not found"}, 404

	filename = result_payload.get("file_name") or f"applications_{student.id}.csv"
	return send_file(resolved, as_attachment=True, download_name=filename, mimetype="text/csv")
