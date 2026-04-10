from functools import wraps
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from flask import Blueprint, current_app, request, send_file, session
from sqlalchemy import select, func, or_

from ...extensions import db
from ..services.cache import RouteCache
from ..models import Application, ApplicationStatus, Company, Drive, DriveApprovalStatus, Student, User, UserType


route_cache = RouteCache()


def _parse_pagination():
	page = request.args.get("page", type=int) or 1
	limit = request.args.get("limit", type=int) or 10
	page = max(1, page)
	limit = max(1, min(limit, 50))
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


def _build_cache_key(prefix):
	params = [(k, v) for k, v in request.args.items() if v is not None and str(v).strip() != ""]
	params.sort(key=lambda item: item[0])
	query = urlencode(params)
	return f"{prefix}?{query}" if query else prefix


def _resolve_resume_file_path(path_value):
	raw_path = str(path_value or "").strip()
	if not raw_path:
		return None, {"error": "Resume not found"}, 404

	project_root = Path(current_app.root_path).parent
	resolved = (project_root / raw_path).resolve()
	uploads_root = (project_root / "uploads").resolve()

	if uploads_root not in resolved.parents:
		return None, {"error": "Invalid resume path"}, 400
	if not resolved.exists() or not resolved.is_file():
		return None, {"error": "Resume file not found"}, 404

	return resolved, None, None


def admin_required(f):
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

		if current_user.user_type != UserType.admin:
			return {"error": "Admin access required"}, 403

		if not current_user.is_active:
			return {"error": "Admin account is blocked"}, 403

		return f(current_user, *args, **kwargs)

	return decorated_function


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/companies/pending/", methods=["GET"])
@admin_required
def pending_companies(admin_user):
	del admin_user
	cache_key = "api:admin:companies:pending"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	companies = db.session.execute(
		select(Company).where(Company.is_approved.is_(False))
	).scalars().all()
	payload = {"companies": [company.to_dict() for company in companies]}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/dashboard/", methods=["GET"])
@admin_required
def dashboard(admin_user):
	del admin_user
	cache_key = "api:admin:dashboard"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	totals = {
		"companies": int(db.session.execute(select(func.count(Company.id))).scalar_one()),
		"students": int(db.session.execute(select(func.count(Student.id))).scalar_one()),
		"drives": int(db.session.execute(select(func.count(Drive.id))).scalar_one()),
		"applications": int(db.session.execute(select(func.count(Application.id))).scalar_one()),
	}

	pending = {
		"companies": int(
			db.session.execute(
				select(func.count(Company.id)).where(
					(Company.is_approved.is_(False)) & (Company.is_active.is_(True))
				)
			).scalar_one()
		),
		"drives": int(
			db.session.execute(
				select(func.count(Drive.id)).where(Drive.approval_status == DriveApprovalStatus.pending)
			).scalar_one()
		),
	}

	rejected = {
		"companies": int(
			db.session.execute(
				select(func.count(Company.id)).where(
					(Company.is_approved.is_(False)) & (Company.is_active.is_(False))
				)
			).scalar_one()
		),
		"drives": int(
			db.session.execute(
				select(func.count(Drive.id)).where(Drive.approval_status == DriveApprovalStatus.rejected)
			).scalar_one()
		),
	}

	active = {
		"companies": int(
			db.session.execute(
				select(func.count(Company.id)).where(Company.is_active.is_(True))
			).scalar_one()
		),
		"students": int(
			db.session.execute(
				select(func.count(Student.id)).where(Student.is_active.is_(True))
			).scalar_one()
		),
		"drives": int(
			db.session.execute(
				select(func.count(Drive.id)).where(Drive.is_active.is_(True))
			).scalar_one()
		),
	}

	drive_status_rows = db.session.execute(
		select(Drive.effective_status, func.count(Drive.id)).group_by(Drive.effective_status)
	).all()
	drive_status_distribution = {
		str(status.value if hasattr(status, "value") else status): int(count)
		for status, count in drive_status_rows
	}

	drive_approval_rows = db.session.execute(
		select(Drive.approval_status, func.count(Drive.id)).group_by(Drive.approval_status)
	).all()
	drive_approval_distribution = {
		str(status.value if hasattr(status, "value") else status): int(count)
		for status, count in drive_approval_rows
	}

	application_status_rows = db.session.execute(
		select(Application.status, func.count(Application.id)).group_by(Application.status)
	).all()
	application_status_distribution = {
		str(status.value if hasattr(status, "value") else status): int(count)
		for status, count in application_status_rows
	}

	def _status_count(distribution, key):
		normalized_key = str(key or "").strip().lower().replace(" ", "").replace("_", "")
		for raw_key, raw_count in distribution.items():
			raw_normalized = str(raw_key or "").strip().lower().replace(" ", "").replace("_", "")
			if raw_normalized == normalized_key:
				return int(raw_count or 0)
		return 0

	rejected["applications"] = int(
		_status_count(application_status_distribution, "rejected")
	)

	student_inactive = max(0, totals["students"] - active["students"])
	companies_approved_active = int(
		db.session.execute(
			select(func.count(Company.id)).where(
				(Company.is_approved.is_(True)) & (Company.is_active.is_(True))
			)
		).scalar_one()
	)
	companies_approved_inactive = int(
		db.session.execute(
			select(func.count(Company.id)).where(
				(Company.is_approved.is_(True)) & (Company.is_active.is_(False))
			)
		).scalar_one()
	)
	drives_approved_active = int(
		db.session.execute(
			select(func.count(Drive.id)).where(
				(Drive.approval_status == DriveApprovalStatus.approved) & (Drive.is_active.is_(True))
			)
		).scalar_one()
	)
	drives_approved_inactive = int(
		db.session.execute(
			select(func.count(Drive.id)).where(
				(Drive.approval_status == DriveApprovalStatus.approved) & (Drive.is_active.is_(False))
			)
		).scalar_one()
		)

	applications = {
		"total": totals["applications"],
		"status_distribution": application_status_distribution,
	}

	summary = {
		"students": {
			"total": totals["students"],
			"active": active["students"],
			"inactive": student_inactive,
		},
		"companies": {
			"total": totals["companies"],
			"approved_active": companies_approved_active,
			"pending_approval": pending["companies"],
			"rejected_or_blocked": rejected["companies"],
			"approved_inactive": companies_approved_inactive,
		},
		"drives": {
			"total": totals["drives"],
			"approved_active": drives_approved_active,
			"pending_approval": pending["drives"],
			"rejected_approval": rejected["drives"],
			"approved_inactive": drives_approved_inactive,
		},
		"applications": {
			"total": totals["applications"],
			"applied": _status_count(application_status_distribution, "applied"),
			"short_listed": _status_count(application_status_distribution, "short_listed"),
			"selected": _status_count(application_status_distribution, "selected"),
			"rejected": _status_count(application_status_distribution, "rejected"),
		},
	}

	payload = {
		"totals": totals,
		"pending": pending,
		"active": active,
		"rejected": rejected,
		"summary": summary,
		"applications": applications,
		"distribution": {
			"drive_status": drive_status_distribution,
			"drive_approval": drive_approval_distribution,
			"applications": application_status_distribution,
		},
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/students/", methods=["GET"])
@admin_required
def list_students(admin_user):
	del admin_user
	cache_key = _build_cache_key("api:admin:students")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	search = (request.args.get("search") or "").strip()
	active = (request.args.get("active") or "").strip().lower()
	branch = (request.args.get("branch") or "").strip()
	current_level = request.args.get("current_level", type=int)
	cgpa_min = request.args.get("cgpa_min", type=float)
	cgpa_max = request.args.get("cgpa_max", type=float)
	page, limit = _parse_pagination()
	sort_by = (request.args.get("sort_by") or "id").strip().lower()
	sort_order = (request.args.get("sort_order") or "desc").strip().lower()
	allowed_sort_fields = {
		"id": Student.id,
		"name": Student.name,
		"email": Student.email,
		"roll": Student.roll,
		"branch": Student.branch,
		"current_level": Student.current_level,
		"cgpa": Student.cgpa,
		"is_active": Student.is_active,
	}
	if sort_by not in allowed_sort_fields:
		sort_by = "id"
	if sort_order not in {"asc", "desc"}:
		sort_order = "desc"

	query = select(Student)
	if search:
		pattern = f"%{search}%"
		query = query.where(
			or_(
				Student.name.ilike(pattern),
				Student.email.ilike(pattern),
				Student.roll.ilike(pattern),
			)
		)
	if active in {"true", "false"}:
		query = query.where(Student.is_active.is_(active == "true"))
	if branch:
		query = query.where(Student.branch == branch)
	if current_level is not None:
		if current_level < 1:
			return {"error": "current_level must be >= 1"}, 400
		query = query.where(Student.current_level == current_level)
	if cgpa_min is not None:
		query = query.where(Student.cgpa >= cgpa_min)
	if cgpa_max is not None:
		query = query.where(Student.cgpa <= cgpa_max)
	if cgpa_min is not None and cgpa_max is not None and cgpa_min > cgpa_max:
		return {"error": "cgpa_min cannot be greater than cgpa_max"}, 400

	total = int(db.session.execute(select(func.count()).select_from(query.order_by(None).subquery())).scalar_one())
	sort_column = allowed_sort_fields[sort_by]
	order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
	query = query.order_by(order_expression, Student.id.desc())
	query = query.offset((page - 1) * limit).limit(limit)
	students = db.session.execute(query).scalars().all()
	payload = {
		"items": [student.to_dict() for student in students],
		"students": [student.to_dict() for student in students],
		"pagination": _pagination_payload(page, limit, total),
		"sorting": {
			"sort_by": sort_by,
			"sort_order": sort_order,
			"allowed": list(allowed_sort_fields.keys()),
		},
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/companies/", methods=["GET"])
@admin_required
def list_companies(admin_user):
	del admin_user
	cache_key = _build_cache_key("api:admin:companies")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	company_id = request.args.get("company_id", type=int)
	search = (request.args.get("search") or "").strip()
	active = (request.args.get("active") or "").strip().lower()
	approved = (request.args.get("approved") or "").strip().lower()
	page, limit = _parse_pagination()
	sort_by = (request.args.get("sort_by") or "id").strip().lower()
	sort_order = (request.args.get("sort_order") or "desc").strip().lower()
	allowed_sort_fields = {
		"id": Company.id,
		"name": func.lower(Company.name),
		"is_approved": Company.is_approved,
		"industry_type": Company.industry_type,
		"is_active": Company.is_active,
	}
	if sort_by not in allowed_sort_fields:
		sort_by = "id"
	if sort_order not in {"asc", "desc"}:
		sort_order = "desc"

	query = select(Company)
	if company_id is not None:
		if company_id < 1:
			return {"error": "company_id must be >= 1"}, 400
		query = query.where(Company.id == company_id)
	if search:
		pattern = f"%{search}%"
		query = query.where(
			or_(
				Company.name.ilike(pattern),
				Company.email.ilike(pattern),
				Company.website.ilike(pattern),
			)
		)
	if active in {"true", "false"}:
		query = query.where(Company.is_active.is_(active == "true"))
	if approved in {"true", "false"}:
		query = query.where(Company.is_approved.is_(approved == "true"))

	total = int(db.session.execute(select(func.count()).select_from(query.order_by(None).subquery())).scalar_one())
	sort_column = allowed_sort_fields[sort_by]
	order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
	query = query.order_by(order_expression, Company.id.desc())
	query = query.offset((page - 1) * limit).limit(limit)
	companies = db.session.execute(query).scalars().all()
	payload = {
		"items": [company.to_dict() for company in companies],
		"companies": [company.to_dict() for company in companies],
		"pagination": _pagination_payload(page, limit, total),
		"sorting": {
			"sort_by": sort_by,
			"sort_order": sort_order,
			"allowed": list(allowed_sort_fields.keys()),
		},
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/drives/", methods=["GET"])
@admin_required
def list_drives(admin_user):
	del admin_user
	cache_key = _build_cache_key("api:admin:drives")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	company_id = request.args.get("company_id", type=int)
	search = (request.args.get("search") or "").strip()
	active = (request.args.get("active") or "").strip().lower()
	status = (request.args.get("status") or "").strip().lower()
	approval_status = (request.args.get("approval_status") or "").strip().lower()
	page, limit = _parse_pagination()
	sort_by = (request.args.get("sort_by") or "create_date").strip().lower()
	sort_order = (request.args.get("sort_order") or "desc").strip().lower()
	allowed_sort_fields = {
		"id": Drive.id,
		"title": func.lower(Drive.title),
		"company_id": Drive.company_id,
		"is_active": Drive.is_active,
		"create_date": Drive.create_date,
		"start_date": Drive.start_date,
		"end_date": Drive.end_date,
		"approval_status": Drive.approval_status,
		"status": Drive.effective_status,
		"work_mode": Drive.work_mode,
	}
	if sort_by not in allowed_sort_fields:
		sort_by = "create_date"
	if sort_order not in {"asc", "desc"}:
		sort_order = "desc"

	query = select(Drive).join(Company, Company.id == Drive.company_id)
	if company_id is not None:
		if company_id < 1:
			return {"error": "company_id must be >= 1"}, 400
		query = query.where(Company.id == company_id)
	if search:
		pattern = f"%{search}%"
		query = query.where(
			or_(
				Drive.title.ilike(pattern),
				Drive.description.ilike(pattern),
				Company.name.ilike(pattern),
			)
		)
	if active in {"true", "false"}:
		query = query.where(Drive.is_active.is_(active == "true"))
	if status:
		query = query.where(Drive.effective_status == status)
	if approval_status:
		query = query.where(func.lower(Drive.approval_status.cast(db.String)) == approval_status)

	total = int(db.session.execute(select(func.count()).select_from(query.order_by(None).subquery())).scalar_one())
	sort_column = allowed_sort_fields[sort_by]
	order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
	query = query.order_by(order_expression, Drive.id.desc())
	query = query.offset((page - 1) * limit).limit(limit)
	drives = db.session.execute(query).scalars().all()
	payload = {
		"items": [
			{
				**drive.to_dict(),
				"company_name": drive.company.name if drive.company else None,
			}
			for drive in drives
		],
		"drives": [
			{
				**drive.to_dict(),
				"company_name": drive.company.name if drive.company else None,
			}
			for drive in drives
		],
		"pagination": _pagination_payload(page, limit, total),
		"sorting": {
			"sort_by": sort_by,
			"sort_order": sort_order,
			"allowed": list(allowed_sort_fields.keys()),
		},
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/drives/<int:drive_id>/", methods=["GET"])
@admin_required
def drive_detail(admin_user, drive_id):
	del admin_user
	cache_key = f"api:admin:drives:{drive_id}:detail"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	drive = db.session.execute(select(Drive).where(Drive.id == drive_id)).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404

	payload = {
		"drive": {
			**drive.to_dict(),
			"company_name": drive.company.name if drive.company else None,
			"company": {
				"id": drive.company.id if drive.company else None,
				"name": drive.company.name if drive.company else None,
				"email": drive.company.email if drive.company else None,
				"website": drive.company.website if drive.company else None,
				"industry_type": drive.company.industry_type.value if drive.company and drive.company.industry_type else None,
			},
			"applications_count": int(
				db.session.execute(
					select(func.count(Application.id)).where(Application.drive_id == drive.id)
				).scalar_one()
			),
		}
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/applications/", methods=["GET"])
@admin_required
def list_applications(admin_user):
	del admin_user
	cache_key = _build_cache_key("api:admin:applications")
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	company_id = request.args.get("company_id", type=int)
	drive_id = request.args.get("drive_id", type=int)
	search = (request.args.get("search") or "").strip()
	status_filter = (request.args.get("status") or "").strip().lower()
	page, limit = _parse_pagination()
	sort_by = (request.args.get("sort_by") or "application_date").strip().lower()
	sort_order = (request.args.get("sort_order") or "desc").strip().lower()

	allowed_sort_fields = {
		"application_date": Application.application_date,
		"status": Application.status,
		"id": Application.id,
		"student_id": Student.id,
		"student_name": Student.name,
		"roll": Student.roll,
		"drive_id": Drive.id,
		"drive_title": Drive.title,
		"company_name": Company.name,
	}
	if sort_by not in allowed_sort_fields:
		sort_by = "application_date"
	if sort_order not in {"asc", "desc"}:
		sort_order = "desc"

	query = (
		select(Application)
		.join(Student, Student.id == Application.student_id)
		.join(Drive, Drive.id == Application.drive_id)
		.join(Company, Company.id == Drive.company_id)
	)

	if company_id is not None:
		if company_id < 1:
			return {"error": "company_id must be >= 1"}, 400
		query = query.where(Company.id == company_id)

	if drive_id is not None:
		if drive_id < 1:
			return {"error": "drive_id must be >= 1"}, 400
		query = query.where(Drive.id == drive_id)

	if status_filter:
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
			or_(
				Student.name.ilike(pattern),
				Student.email.ilike(pattern),
				Student.roll.ilike(pattern),
				Drive.title.ilike(pattern),
				Drive.description.ilike(pattern),
				Company.name.ilike(pattern),
			)
		)

	filtered_subquery = query.order_by(None).subquery()
	total = int(db.session.execute(select(func.count()).select_from(filtered_subquery)).scalar_one())
	status_rows = db.session.execute(
		select(filtered_subquery.c.status, func.count())
		.group_by(filtered_subquery.c.status)
	).all()
	status_distribution_all = {
		"applied": 0,
		"shortlisted": 0,
		"selected": 0,
		"rejected": 0,
	}
	for raw_status, raw_count in status_rows:
		status_key = str(raw_status.value if hasattr(raw_status, "value") else raw_status)
		normalized = status_key.lower().replace(" ", "").replace("_", "")
		if normalized in status_distribution_all:
			status_distribution_all[normalized] = int(raw_count or 0)

	sort_column = allowed_sort_fields[sort_by]
	order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
	query = query.order_by(order_expression, Application.id.desc())
	query = query.offset((page - 1) * limit).limit(limit)

	applications = db.session.execute(query).scalars().all()
	items = []
	for app in applications:
		drive = app.drive
		company = drive.company if drive else None
		student = app.student
		items.append(
			{
				"application": app.to_dict(),
				"student": {
					"id": student.id if student else None,
					"name": student.name if student else None,
					"email": student.email if student else None,
					"roll": student.roll if student else None,
					"branch": student.branch.value if student and student.branch else None,
					"current_level": student.current_level if student else None,
				},
				"drive": {
					"id": drive.id if drive else None,
					"title": drive.title if drive else "Deleted drive",
					"status": drive.effective_status.value if drive and drive.effective_status else None,
					"approval_status": drive.approval_status.value if drive and drive.approval_status else None,
				},
				"company": {
					"id": company.id if company else None,
					"name": company.name if company else "Deleted company",
				},
			}
		)

	page_status_distribution = {
		"applied": 0,
		"shortlisted": 0,
		"selected": 0,
		"rejected": 0,
	}
	for item in items:
		status_key = str((item.get("application") or {}).get("status") or "").lower().replace(" ", "").replace("_", "")
		if status_key in page_status_distribution:
			page_status_distribution[status_key] += 1

	summary = {
		"total_matching": total,
		"current": status_distribution_all["applied"] + status_distribution_all["shortlisted"],
		"history": status_distribution_all["selected"] + status_distribution_all["rejected"],
		"status_distribution": status_distribution_all,
		"page_status_distribution": page_status_distribution,
	}

	payload = {
		"items": items,
		"applications": items,
		"pagination": _pagination_payload(page, limit, total),
		"summary": summary,
		"sorting": {
			"sort_by": sort_by,
			"sort_order": sort_order,
			"allowed": list(allowed_sort_fields.keys()),
		},
	}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/applications/<int:application_id>/", methods=["GET"])
@admin_required
def application_detail(admin_user, application_id):
	del admin_user
	cache_key = f"api:admin:applications:detail:{application_id}"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	app = db.session.execute(
		select(Application)
		.join(Student, Student.id == Application.student_id)
		.join(Drive, Drive.id == Application.drive_id)
		.join(Company, Company.id == Drive.company_id)
		.where(Application.id == application_id)
	).scalar_one_or_none()

	if not app:
		return {"error": "Application not found"}, 404

	drive = app.drive
	company = drive.company if drive else None
	student = app.student

	payload = {
		"application": app.to_dict(),
		"student": {
			"id": student.id if student else None,
			"name": student.name if student else None,
			"email": student.email if student else None,
			"roll": student.roll if student else None,
			"branch": student.branch.value if student and student.branch else None,
			"current_level": student.current_level if student else None,
			"cgpa": student.cgpa if student else None,
			"resume_path": student.resume_path if student else None,
		},
		"drive": {
			"id": drive.id if drive else None,
			"title": drive.title if drive else None,
			"description": drive.description if drive else None,
			"status": drive.effective_status.value if drive and drive.effective_status else None,
			"approval_status": drive.approval_status.value if drive and drive.approval_status else None,
			"work_mode": drive.work_mode.value if drive and drive.work_mode else None,
			"start_date": drive.start_date.isoformat() if drive and drive.start_date else None,
			"end_date": drive.end_date.isoformat() if drive and drive.end_date else None,
			"min_cgpa": drive.min_cgpa if drive else None,
			"allowed_branches": drive.allowed_branches_list if drive else [],
			"max_applications": drive.max_applications if drive else None,
		},
		"company": {
			"id": company.id if company else None,
			"name": company.name if company else None,
			"email": company.email if company else None,
			"website": company.website if company else None,
			"industry_type": company.industry_type.value if company and company.industry_type else None,
		},
	}

	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/applications/<int:application_id>/resume/", methods=["GET"])
@admin_required
def application_resume(admin_user, application_id):
	del admin_user
	source = (request.args.get("source") or "applied").strip().lower()
	if source not in {"applied", "current"}:
		return {"error": "source must be one of: applied, current"}, 400

	app = db.session.execute(
		select(Application)
		.join(Student, Student.id == Application.student_id)
		.join(Drive, Drive.id == Application.drive_id)
		.join(Company, Company.id == Drive.company_id)
		.where(Application.id == application_id)
	).scalar_one_or_none()

	if not app:
		return {"error": "Application not found"}, 404

	resume_source = app.resume_link if source == "applied" else (app.student.resume_path if app.student else None)
	resolved, error_payload, status_code = _resolve_resume_file_path(resume_source)
	if error_payload is not None:
		return error_payload, status_code

	return send_file(resolved, mimetype="application/pdf")


@admin_bp.route("/companies/<int:company_id>/approve/", methods=["PUT"])
@admin_required
def approve_company(admin_user, company_id):
	del admin_user
	company = db.session.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
	if not company:
		return {"error": "Company not found"}, 404

	company.is_approved = True
	company.is_active = True
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	return {"message": "Company approved successfully", "company": company.to_dict()}, 200


@admin_bp.route("/companies/<int:company_id>/reject/", methods=["PUT"])
@admin_required
def reject_company(admin_user, company_id):
	del admin_user
	company = db.session.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
	if not company:
		return {"error": "Company not found"}, 404

	company.is_approved = False
	company.is_active = False
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{company.id}:")
	return {"message": "Company rejected successfully", "company": company.to_dict()}, 200


@admin_bp.route("/drives/pending/", methods=["GET"])
@admin_required
def pending_drives(admin_user):
	del admin_user
	cache_key = "api:admin:drives:pending"
	cached = route_cache.get_json(cache_key)
	if cached is not None:
		return cached, 200

	drives = db.session.execute(
		select(Drive).where(
			(Drive.approval_status == DriveApprovalStatus.pending) & (Drive.is_active.is_(True))
		)
	).scalars().all()
	payload = {"drives": [drive.to_dict() for drive in drives]}
	route_cache.set_json(cache_key, payload, 30)
	return payload, 200


@admin_bp.route("/drives/<int:drive_id>/approve/", methods=["PUT"])
@admin_required
def approve_drive(admin_user, drive_id):
	del admin_user
	drive = db.session.execute(select(Drive).where(Drive.id == drive_id)).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404
	if drive.end_date and drive.end_date < datetime.now():
		return {"error": "Cannot approve a drive whose end date/time is in the past"}, 400

	drive.approval_status = DriveApprovalStatus.approved
	drive.is_active = True
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:")
	route_cache.delete_prefix("api:student:")
	return {"message": "Drive approved successfully", "drive": drive.to_dict()}, 200


@admin_bp.route("/drives/<int:drive_id>/reject/", methods=["PUT"])
@admin_required
def reject_drive(admin_user, drive_id):
	del admin_user
	drive = db.session.execute(select(Drive).where(Drive.id == drive_id)).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404

	drive.approval_status = DriveApprovalStatus.rejected
	drive.is_active = False
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:")
	route_cache.delete_prefix("api:student:")
	return {"message": "Drive rejected successfully", "drive": drive.to_dict()}, 200


@admin_bp.route("/students/<int:student_id>/block/", methods=["PUT"])
@admin_required
def block_student(admin_user, student_id):
	del admin_user
	student = db.session.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
	if not student:
		return {"error": "Student not found"}, 404

	student.is_active = False
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	return {"message": "Student blocked successfully", "student": student.to_dict()}, 200


@admin_bp.route("/students/<int:student_id>/unblock/", methods=["PUT"])
@admin_required
def unblock_student(admin_user, student_id):
	del admin_user
	student = db.session.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
	if not student:
		return {"error": "Student not found"}, 404

	student.is_active = True
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	return {"message": "Student unblocked successfully", "student": student.to_dict()}, 200


@admin_bp.route("/companies/<int:company_id>/block/", methods=["PUT"])
@admin_required
def block_company(admin_user, company_id):
	del admin_user
	company = db.session.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
	if not company:
		return {"error": "Company not found"}, 404

	company.is_active = False
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{company.id}:")
	return {"message": "Company blocked successfully", "company": company.to_dict()}, 200


@admin_bp.route("/companies/<int:company_id>/unblock/", methods=["PUT"])
@admin_required
def unblock_company(admin_user, company_id):
	del admin_user
	company = db.session.execute(select(Company).where(Company.id == company_id)).scalar_one_or_none()
	if not company:
		return {"error": "Company not found"}, 404

	company.is_active = True
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{company.id}:")
	return {"message": "Company unblocked successfully", "company": company.to_dict()}, 200


@admin_bp.route("/drives/<int:drive_id>/block/", methods=["PUT"])
@admin_required
def block_drive(admin_user, drive_id):
	del admin_user
	drive = db.session.execute(select(Drive).where(Drive.id == drive_id)).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404
	if drive.approval_status == DriveApprovalStatus.pending:
		return {"error": "Drive can be blocked only after admin approval decision"}, 400

	drive.is_active = False
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:")
	route_cache.delete_prefix("api:student:")
	return {"message": "Drive blocked successfully", "drive": drive.to_dict()}, 200


@admin_bp.route("/drives/<int:drive_id>/unblock/", methods=["PUT"])
@admin_required
def unblock_drive(admin_user, drive_id):
	del admin_user
	drive = db.session.execute(select(Drive).where(Drive.id == drive_id)).scalar_one_or_none()
	if not drive:
		return {"error": "Drive not found"}, 404
	if drive.approval_status == DriveApprovalStatus.rejected:
		return {"error": "Rejected drives cannot be unblocked"}, 400
	if drive.end_date and drive.end_date < datetime.now():
		return {"error": "Cannot unblock a drive whose end date/time is in the past"}, 400

	drive.is_active = True
	db.session.commit()
	route_cache.delete_prefix("api:admin:")
	route_cache.delete_prefix(f"api:company:{drive.company_id}:")
	route_cache.delete_prefix("api:student:")
	return {"message": "Drive unblocked successfully", "drive": drive.to_dict()}, 200
