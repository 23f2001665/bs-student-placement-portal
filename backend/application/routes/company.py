from datetime import datetime, date, time
from pathlib import Path

from flask import Blueprint, current_app, request, send_file, session
from ..errors import db_error_message
from .common import parse_enum
from ..models import Branches, User, UserType, Company, Drive, DriveStatus, WorkMode, Application, DriveApprovalStatus, IndustryType, ApplicationStatus, Student, Interview
from ..services.cache import RouteCache
from ...tasks.send_email import send_application_status_email
from ...extensions import db
from sqlalchemy import select, and_, func, or_
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from functools import wraps

route_cache = RouteCache()


def _parse_iso_datetime(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO datetime") from exc


def _parse_iso_datetime_optional(value, field_name):
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO datetime") from exc


def _parse_iso_date(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")

    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO date (YYYY-MM-DD)") from exc


def _parse_iso_time(value, field_name):
    if not value:
        raise ValueError(f"{field_name} is required")

    raw = str(value).strip()
    if len(raw) == 5:
        raw = f"{raw}:00"

    try:
        return time.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO time (HH:MM or HH:MM:SS)") from exc


def _normalize_allowed_branches(raw):
    if raw is None:
        return None

    if isinstance(raw, list):
        branch_names = [str(item).strip().lower() for item in raw if str(item).strip()]
    else:
        branch_names = [item.strip().lower() for item in str(raw).split(",") if item.strip()]

    valid = {branch.name for branch in Branches}
    if any(name not in valid for name in branch_names):
        raise ValueError("allowed_branches contains invalid branch keys")

    if not branch_names:
        return None

    return ",".join(branch_names)


def _resolve_branch_member(raw):
    if raw in (None, ""):
        return None

    token = str(raw).strip().lower()
    if not token:
        return None

    by_name = Branches.__members__.get(token)
    if by_name:
        return by_name

    for member in Branches:
        if str(member.value).lower() == token:
            return member

    return None


def _enum_distribution(rows):
    return {str(key.value if hasattr(key, "value") else key): int(count) for key, count in rows}


def _pagination_payload(pagination, page, limit):
    total_pages = max(1, int(pagination.pages))
    return {
        "page": int(page),
        "limit": int(limit),
        "total": int(pagination.total),
        "total_pages": total_pages,
        "has_prev": bool(pagination.has_prev),
        "has_next": bool(pagination.has_next),
        "prev_page": int(pagination.prev_num) if pagination.prev_num else None,
        "next_page": int(pagination.next_num) if pagination.next_num else None,
    }


def _public_student_payload(student):
    if not student:
        return {
            "id": None,
            "name": "Deleted student",
            "roll": None,
            "branch": None,
            "current_level": None,
            "cgpa": None,
            "resume_path": None,
        }

    return {
        "id": student.id,
        "name": student.name,
        "roll": student.roll,
        "branch": student.branch.value if student.branch else None,
        "current_level": student.current_level,
        "cgpa": student.cgpa,
        "resume_path": student.resume_path,
    }


def _format_interview_line(interview, fallback_details=None):
    if not interview:
        if fallback_details:
            return f"Message: {fallback_details}"
        return "Interview: Not scheduled"

    date_str = interview.interview_date.isoformat() if interview.interview_date else "-"
    time_str = interview.interview_time.strftime("%H:%M") if interview.interview_time else "-"
    details = interview.details or fallback_details or "N/A"
    return f"Interview: {date_str} {time_str} | Details: {details}"


def _send_application_status_notifications(app_obj, fallback_message=None):
    student = app_obj.student
    drive = app_obj.drive
    company = drive.company if drive else None

    if not student or not company or not drive:
        return

    status_label = app_obj.status.value if app_obj.status else "Unknown"
    if app_obj.status in {ApplicationStatus.selected, ApplicationStatus.rejected}:
        interview_line = f"Message: {fallback_message or 'Status decision has been communicated.'}"
    else:
        interview_line = _format_interview_line(app_obj.interview, fallback_details=fallback_message)

    subject = f"Application Update: {status_label} - {drive.title}"
    student_body = (
        f"Hello {student.name},\n\n"
        f"Your application status has been updated.\n"
        f"Drive: {drive.title}\n"
        f"Company: {company.name}\n"
        f"Status: {status_label}\n"
        f"{interview_line}\n\n"
        f"Regards,\nPlacement Portal"
    )

    company_body = (
        f"Hello {company.name},\n\n"
        f"You updated an application status.\n"
        f"Drive: {drive.title}\n"
        f"Student: {student.name} ({student.roll})\n"
        f"Status: {status_label}\n"
        f"{interview_line}\n\n"
        f"Regards,\nPlacement Portal"
    )

    notification_jobs = [
        (student.email, subject, student_body),
        (company.email, subject, company_body),
    ]

    for to_email, mail_subject, mail_body in notification_jobs:
        # Prefer async delivery, but fall back to inline task execution if broker queueing fails.
        try:
            send_application_status_email.delay(to_email, mail_subject, mail_body)
        except Exception:
            send_application_status_email.apply(args=[to_email, mail_subject, mail_body])


def _sync_company_drive_statuses(company_id):
    del company_id
    # Status is derived via Drive.effective_status; no persistence sync required.

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = session.get("current_user")
        if not current_user_id:
            return {"error": "Authentication required"}, 401

        current_user = db.session.execute(
            select(User).where(User.id == current_user_id)).scalar_one_or_none()

        if not current_user:
            return {"error": "Authentication required"}, 401

        if current_user.user_type != UserType.company:
            return {"error": "Company access required"}, 403

        company = db.session.execute(
            select(Company).where(Company.id == current_user.id)
        ).scalar_one_or_none()

        if not company:
            session.clear()
            return {"error": "Company not found"}, 401
        
        if not company.is_active:
            return {"error": "Company account is blocked"}, 403
        
        if not company.is_approved:
            session.clear()
            return {"error": "Company account is not verified"}, 401

        _sync_company_drive_statuses(company.id)
        
        return f(company, *args, **kwargs)

    return decorated_function 
    

company_bp = Blueprint('company', __name__, url_prefix='/company')


@company_bp.route('/profile/', methods=['GET'])
@company_required
def view_profile(company):
    return {"company": company.to_dict()}, 200


@company_bp.route('/profile/update/', methods=['PUT'])
@company_required
def update_profile(company):
    data = request.get_json(silent=True) or {}

    try:
        if "name" in data:
            company.name = (data.get("name") or "").strip()

        if "website" in data:
            company.website = (data.get("website") or "").strip()

        if "description" in data:
            company.description = data.get("description")

        db.session.commit()
    except (IntegrityError, DataError, StatementError) as exc:
        db.session.rollback()
        return {"error": db_error_message(exc)}, 400

    return {
        "message": "Profile updated successfully",
        "company": company.to_dict(),
    }, 200

@company_bp.route('/drives/', methods=['GET'])
@company_required
def view_drives(company):
    page_arg = request.args.get("page", type=int)
    limit_arg = request.args.get("limit", type=int)
    status_filter = request.args.get("status")
    approval_filter = request.args.get("approval_status")
    work_mode_filter = request.args.get("work_mode")
    search = (request.args.get("search") or "").strip()

    try:
        start_from = _parse_iso_datetime_optional(request.args.get("start_from"), "start_from")
        start_to = _parse_iso_datetime_optional(request.args.get("start_to"), "start_to")
        create_from = _parse_iso_datetime_optional(request.args.get("create_from"), "create_from")
        create_to = _parse_iso_datetime_optional(request.args.get("create_to"), "create_to")
        status_enum = parse_enum(DriveStatus, status_filter, "status", required=False)
        approval_enum = parse_enum(DriveApprovalStatus, approval_filter, "approval_status", required=False)
        work_mode_enum = parse_enum(WorkMode, work_mode_filter, "work_mode", required=False)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    filters = [Drive.company_id == company.id, Drive.is_active.is_(True)]
    if status_enum is not None:
        filters.append(Drive.effective_status == status_enum.name)
    if approval_enum is not None:
        filters.append(Drive.approval_status == approval_enum)
    if work_mode_enum is not None:
        filters.append(Drive.work_mode == work_mode_enum)
    if start_from is not None:
        filters.append(Drive.start_date >= start_from)
    if start_to is not None:
        filters.append(Drive.start_date <= start_to)
    if create_from is not None:
        filters.append(Drive.create_date >= create_from)
    if create_to is not None:
        filters.append(Drive.create_date <= create_to)
    if search:
        filters.append(or_(Drive.title.ilike(f"%{search}%"), Drive.description.ilike(f"%{search}%")))

    filter_key = ":".join([
        f"status={status_filter or ''}",
        f"approval={approval_filter or ''}",
        f"mode={work_mode_filter or ''}",
        f"search={search or ''}",
        f"start_from={request.args.get('start_from') or ''}",
        f"start_to={request.args.get('start_to') or ''}",
        f"create_from={request.args.get('create_from') or ''}",
        f"create_to={request.args.get('create_to') or ''}",
    ])

    # Backward-compatible mode: no pagination params means return all drives.
    if page_arg is None and limit_arg is None:
        cache_key = f"api:company:{company.id}:drives:all:{filter_key}"
        cached = route_cache.get_json(cache_key)
        if cached is not None:
            return cached, 200

        drives = db.session.execute(select(Drive).where(and_(*filters))).scalars().all()
        payload = {"drives": [drive.to_dict() for drive in drives]}
        route_cache.set_json(cache_key, payload, 30)
        return payload, 200

    page = page_arg or 1
    limit = limit_arg or 10

    if page < 1:
        return {"error": "page must be >= 1"}, 400

    if limit < 1 or limit > 50:
        return {"error": "limit must be between 1 and 50"}, 400

    cache_key = f"api:company:{company.id}:drives:page:{page}:limit:{limit}:{filter_key}"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    drive_query = (
        select(Drive)
        .where(and_(*filters))
        .order_by(Drive.create_date.desc(), Drive.id.desc())
    )
    pagination = db.paginate(drive_query, page=page, per_page=limit, error_out=False)
    if pagination.pages and page > pagination.pages:
        page = pagination.pages
        pagination = db.paginate(drive_query, page=page, per_page=limit, error_out=False)

    drives = pagination.items

    payload = {
        "drives": [drive.to_dict() for drive in drives],
        "pagination": _pagination_payload(pagination, page, limit),
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


@company_bp.route('/drives/summary/', methods=['GET'])
@company_required
def drive_summaries(company):
    page = request.args.get("page", type=int) or 1
    limit = request.args.get("limit", type=int) or 10

    if page < 1:
        return {"error": "page must be >= 1"}, 400
    if limit < 1 or limit > 50:
        return {"error": "limit must be between 1 and 50"}, 400

    status_filter = request.args.get("status")
    approval_filter = request.args.get("approval_status")
    work_mode_filter = request.args.get("work_mode")
    search = (request.args.get("search") or "").strip()

    try:
        start_from = _parse_iso_datetime_optional(request.args.get("start_from"), "start_from")
        start_to = _parse_iso_datetime_optional(request.args.get("start_to"), "start_to")
        create_from = _parse_iso_datetime_optional(request.args.get("create_from"), "create_from")
        create_to = _parse_iso_datetime_optional(request.args.get("create_to"), "create_to")
        status_enum = parse_enum(DriveStatus, status_filter, "status", required=False)
        approval_enum = parse_enum(DriveApprovalStatus, approval_filter, "approval_status", required=False)
        work_mode_enum = parse_enum(WorkMode, work_mode_filter, "work_mode", required=False)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    filters = [Drive.company_id == company.id, Drive.is_active.is_(True)]
    if status_enum is not None:
        filters.append(Drive.effective_status == status_enum.name)
    if approval_enum is not None:
        filters.append(Drive.approval_status == approval_enum)
    if work_mode_enum is not None:
        filters.append(Drive.work_mode == work_mode_enum)
    if start_from is not None:
        filters.append(Drive.start_date >= start_from)
    if start_to is not None:
        filters.append(Drive.start_date <= start_to)
    if create_from is not None:
        filters.append(Drive.create_date >= create_from)
    if create_to is not None:
        filters.append(Drive.create_date <= create_to)
    if search:
        filters.append(or_(Drive.title.ilike(f"%{search}%"), Drive.description.ilike(f"%{search}%")))

    filter_key = ":".join([
        f"page={page}",
        f"limit={limit}",
        f"status={status_filter or ''}",
        f"approval={approval_filter or ''}",
        f"mode={work_mode_filter or ''}",
        f"search={search or ''}",
        f"start_from={request.args.get('start_from') or ''}",
        f"start_to={request.args.get('start_to') or ''}",
        f"create_from={request.args.get('create_from') or ''}",
        f"create_to={request.args.get('create_to') or ''}",
    ])
    cache_key = f"api:company:{company.id}:drives:summary:{filter_key}"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    drive_query = (
        select(Drive)
        .where(and_(*filters))
        .order_by(Drive.create_date.desc(), Drive.id.desc())
    )
    pagination = db.paginate(drive_query, page=page, per_page=limit, error_out=False)
    if pagination.pages and page > pagination.pages:
        page = pagination.pages
        pagination = db.paginate(drive_query, page=page, per_page=limit, error_out=False)

    drives = pagination.items

    drive_ids = [d.id for d in drives]
    app_counts = {}
    app_status_map = {}
    if drive_ids:
        app_count_rows = db.session.execute(
            select(Application.drive_id, func.count(Application.id))
            .where(Application.drive_id.in_(drive_ids))
            .group_by(Application.drive_id)
        ).all()
        app_counts = {int(drive_id): int(count) for drive_id, count in app_count_rows}

        app_status_rows = db.session.execute(
            select(Application.drive_id, Application.status, func.count(Application.id))
            .where(Application.drive_id.in_(drive_ids))
            .group_by(Application.drive_id, Application.status)
        ).all()
        for drive_id, status, count in app_status_rows:
            key = int(drive_id)
            app_status_map.setdefault(key, {})[str(status.value if hasattr(status, "value") else status)] = int(count)

    drive_items = []
    for drive in drives:
        did = drive.id
        drive_items.append({
            "drive": drive.to_dict(),
            "summary": {
                "application_total": app_counts.get(did, 0),
                "application_status_distribution": app_status_map.get(did, {}),
            },
        })

    drive_status_dist = _enum_distribution(
        db.session.execute(
            select(Drive.effective_status, func.count(Drive.id)).where(and_(*filters)).group_by(Drive.effective_status)
        ).all()
    )
    drive_approval_dist = _enum_distribution(
        db.session.execute(
            select(Drive.approval_status, func.count(Drive.id)).where(and_(*filters)).group_by(Drive.approval_status)
        ).all()
    )
    drive_work_mode_dist = _enum_distribution(
        db.session.execute(
            select(Drive.work_mode, func.count(Drive.id)).where(and_(*filters)).group_by(Drive.work_mode)
        ).all()
    )

    app_filters = [Application.drive_id == Drive.id, Drive.company_id == company.id, Drive.is_active.is_(True)]
    application_status_dist = _enum_distribution(
        db.session.execute(
            select(Application.status, func.count(Application.id))
            .select_from(Application)
            .join(Drive, Application.drive_id == Drive.id)
            .where(and_(*app_filters))
            .group_by(Application.status)
        ).all()
    )

    payload = {
        "items": drive_items,
        "pagination": _pagination_payload(pagination, page, limit),
        "chart_summary": {
            "drive_status_distribution": drive_status_dist,
            "drive_approval_distribution": drive_approval_dist,
            "drive_work_mode_distribution": drive_work_mode_dist,
            "application_status_distribution": application_status_dist,
        },
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


@company_bp.route('/summary/', methods=['GET'])
@company_required
def company_summary(company):
    cache_key = f"api:company:{company.id}:summary"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    drive_filters = [Drive.company_id == company.id, Drive.is_active.is_(True)]

    total_drives = db.session.execute(
        select(func.count(Drive.id)).where(and_(*drive_filters))
    ).scalar_one()

    active_drives = db.session.execute(
        select(func.count(Drive.id)).where(and_(*drive_filters, Drive.effective_status == DriveStatus.active.name))
    ).scalar_one()

    app_rows = db.session.execute(
        select(Application.status, func.count(Application.id))
        .select_from(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Drive.company_id == company.id, Drive.is_active.is_(True)))
        .group_by(Application.status)
    ).all()
    app_status_dist = _enum_distribution(app_rows)
    total_applications = sum(app_status_dist.values())

    allowed_branch_counts = {}
    drive_allowed_rows = db.session.execute(
        select(Drive.allowed_branches).where(and_(*drive_filters))
    ).all()
    for (allowed_raw,) in drive_allowed_rows:
        if not allowed_raw:
            allowed_branch_counts["all"] = allowed_branch_counts.get("all", 0) + 1
            continue

        for branch in str(allowed_raw).split(","):
            token = branch.strip()
            if not token:
                continue

            member = _resolve_branch_member(token)
            key = member.value if member else token
            allowed_branch_counts[key] = allowed_branch_counts.get(key, 0) + 1

    applied_branch_rows = db.session.execute(
        select(Student.branch, func.count(Application.id))
        .select_from(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .join(Student, Student.id == Application.student_id)
        .where(and_(Drive.company_id == company.id, Drive.is_active.is_(True)))
        .group_by(Student.branch)
    ).all()
    applied_branch_counts = {
        str(branch.value if hasattr(branch, "value") else branch): int(count)
        for branch, count in applied_branch_rows
    }

    work_mode_dist = _enum_distribution(
        db.session.execute(
            select(Drive.work_mode, func.count(Drive.id))
            .where(and_(*drive_filters))
            .group_by(Drive.work_mode)
        ).all()
    )

    monthly_application_rows = db.session.execute(
        select(
            func.strftime('%Y-%m', Application.application_date),
            func.count(Application.id),
        )
        .select_from(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Drive.company_id == company.id, Drive.is_active.is_(True)))
        .group_by(func.strftime('%Y-%m', Application.application_date))
        .order_by(func.strftime('%Y-%m', Application.application_date))
    ).all()
    monthly_applications = [
        {"month": month or "unknown", "count": int(count)}
        for month, count in monthly_application_rows
    ]

    monthly_application_status_rows = db.session.execute(
        select(
            func.strftime('%Y-%m', Application.application_date),
            Application.status,
            func.count(Application.id),
        )
        .select_from(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Drive.company_id == company.id, Drive.is_active.is_(True)))
        .group_by(func.strftime('%Y-%m', Application.application_date), Application.status)
        .order_by(func.strftime('%Y-%m', Application.application_date))
    ).all()

    monthly_status_map = {}
    for month, status, count in monthly_application_status_rows:
        month_key = month or "unknown"
        if month_key not in monthly_status_map:
            monthly_status_map[month_key] = {
                "applied": 0,
                "shortlisted": 0,
                "selected": 0,
                "rejected": 0,
            }

        status_key = str(status.value if hasattr(status, "value") else status).lower()
        if status_key in monthly_status_map[month_key]:
            monthly_status_map[month_key][status_key] += int(count)

    monthly_application_status = [
        {
            "month": month,
            **monthly_status_map[month],
        }
        for month in sorted(monthly_status_map.keys())
    ]

    payload = {
        "totals": {
            "drives": int(total_drives),
            "active_drives": int(active_drives),
            "applications": int(total_applications),
        },
        "distribution": {
            "drive_status": _enum_distribution(
                db.session.execute(
                    select(Drive.effective_status, func.count(Drive.id))
                    .where(and_(*drive_filters))
                    .group_by(Drive.effective_status)
                ).all()
            ),
            "drive_approval": _enum_distribution(
                db.session.execute(
                    select(Drive.approval_status, func.count(Drive.id))
                    .where(and_(*drive_filters))
                    .group_by(Drive.approval_status)
                ).all()
            ),
            "applications": app_status_dist,
            "work_mode": work_mode_dist,
            "branches": {
                "allowed": allowed_branch_counts,
                "applied": applied_branch_counts,
            },
            "monthly_applications": monthly_applications,
            "monthly_application_status": monthly_application_status,
        },
        "drive_application": {
            "total": int(total_applications),
            **app_status_dist,
        },
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


@company_bp.route('/drives/<int:drive_id>/summary/', methods=['GET'])
@company_required
def drive_summary(company, drive_id):
    cache_key = f"api:company:{company.id}:drives:{drive_id}:summary"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    drive = db.session.execute(
        select(Drive).where(and_(Drive.id == drive_id, Drive.company_id == company.id, Drive.is_active.is_(True)))
    ).scalar_one_or_none()
    if not drive:
        return {"error": "Drive not found"}, 404

    app_count = db.session.execute(
        select(func.count(Application.id)).where(Application.drive_id == drive.id)
    ).scalar_one()
    app_status_dist = _enum_distribution(
        db.session.execute(
            select(Application.status, func.count(Application.id))
            .where(Application.drive_id == drive.id)
            .group_by(Application.status)
        ).all()
    )

    payload = {
        "drive": drive.to_dict(),
        "summary": {
            "application_total": app_count,
            "application_status_distribution": app_status_dist,
        },
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200

@company_bp.route('/drives/create/', methods=['POST'])
@company_required
def create_drive(company):
    data = request.get_json(silent=True) or {}

    if "approval_status" in data or "status" in data:
        return {"error": "approval_status and status are managed by the system"}, 400

    try:
        start_date = _parse_iso_datetime(data.get("start_date"), "start_date")
        end_date = _parse_iso_datetime(data.get("end_date"), "end_date")
        if end_date < datetime.now():
            return {"error": "end_date cannot be in the past"}, 400

        drive = Drive(
            company_id=company.id,
            title=(data.get("title") or "").strip(),
            description=data.get("description"),
            create_date=datetime.now(),
            start_date=start_date,
            end_date=end_date,
            approval_status=DriveApprovalStatus.pending,
            status=DriveStatus.pending,
            work_mode=parse_enum(WorkMode, data.get("work_mode"), "work_mode"),
            min_cgpa=float(data["min_cgpa"]) if data.get("min_cgpa") not in (None, "") else None,
            allowed_branches=_normalize_allowed_branches(data.get("allowed_branches")),
            max_applications=int(data["max_applications"]) if data.get("max_applications") not in (None, "") else None,
        )

        db.session.add(drive)
        db.session.commit()
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400
    except (IntegrityError, DataError, StatementError) as exc:
        db.session.rollback()
        return {"error": db_error_message(exc)}, 400

    route_cache.delete_prefix(f"api:company:{company.id}:drives")
    route_cache.delete_prefix(f"api:company:{company.id}:summary")
    route_cache.delete_prefix("api:admin:")
    route_cache.delete_prefix("api:student:")
    return {"message": "Drive created successfully", "drive": drive.to_dict()}, 201

@company_bp.route('/drives/<int:drive_id>/', methods=['GET'])
@company_required
def view_drive_applications(company, drive_id):
    status_filter = request.args.get("status")
    cache_key = f"api:company:{company.id}:drives:{drive_id}:applications:status:{status_filter or 'all'}"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    drive = db.session.execute(
        select(Drive).where(and_(Drive.id == drive_id, Drive.company_id == company.id, Drive.is_active.is_(True)))
    ).scalar_one_or_none()
    if not drive:
        return {"error": "Drive not found"}, 404
    try:
        app_status_enum = parse_enum(ApplicationStatus, status_filter, "status", required=False)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    app_query = select(Application).where(Application.drive_id == drive.id)
    if app_status_enum is not None:
        app_query = app_query.where(Application.status == app_status_enum)

    applications = db.session.execute(
        app_query.order_by(Application.application_date.desc(), Application.id.desc())
    ).scalars().all()
    payload = {
        "drive": drive.to_dict(),
        "applications": [
            {
                **app.to_dict(),
                "student": _public_student_payload(app.student),
            }
            for app in applications
        ],
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


@company_bp.route('/applications/<int:application_id>/', methods=['GET'])
@company_required
def view_application(company, application_id):
    cache_key = f"api:company:{company.id}:applications:detail:{application_id}"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    app_obj = db.session.execute(
        select(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Application.id == application_id, Drive.company_id == company.id))
    ).scalar_one_or_none()

    if not app_obj:
        return {"error": "Application not found"}, 404

    drive = app_obj.drive
    student = app_obj.student
    payload = {
        "application": app_obj.to_dict(),
        "drive": drive.to_dict() if drive else None,
        "student": _public_student_payload(student),
        "actions": {
            "allowed_status_updates": [status.name for status in _allowed_next_statuses(app_obj.status)],
        },
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


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


@company_bp.route('/applications/<int:application_id>/resume/', methods=['GET'])
@company_required
def view_application_resume(company, application_id):
    source = (request.args.get("source") or "applied").strip().lower()
    if source not in {"applied", "current"}:
        return {"error": "source must be one of: applied, current"}, 400

    app_obj = db.session.execute(
        select(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Application.id == application_id, Drive.company_id == company.id))
    ).scalar_one_or_none()

    if not app_obj:
        return {"error": "Application not found"}, 404

    resume_source = app_obj.resume_link if source == "applied" else (app_obj.student.resume_path if app_obj.student else None)
    resolved, error_payload, status_code = _resolve_resume_file_path(resume_source)
    if error_payload is not None:
        return error_payload, status_code

    return send_file(resolved, mimetype="application/pdf")


@company_bp.route('/applications/', methods=['GET'])
@company_required
def list_company_applications(company):
    page = request.args.get("page", type=int) or 1
    limit = request.args.get("limit", type=int) or 10
    status_filter = request.args.get("status")
    search = (request.args.get("search") or "").strip()

    if page < 1:
        return {"error": "page must be >= 1"}, 400
    if limit < 1 or limit > 50:
        return {"error": "limit must be between 1 and 50"}, 400

    try:
        app_status_enum = parse_enum(ApplicationStatus, status_filter, "status", required=False)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    filters = [Drive.company_id == company.id, Drive.is_active.is_(True)]
    if app_status_enum is not None:
        filters.append(Application.status == app_status_enum)
    if search:
        filters.append(or_(Student.name.ilike(f"%{search}%"), Student.roll.ilike(f"%{search}%"), Drive.title.ilike(f"%{search}%")))

    filter_key = ":".join([
        f"page={page}",
        f"limit={limit}",
        f"status={status_filter or ''}",
        f"search={search or ''}",
    ])
    cache_key = f"api:company:{company.id}:applications:list:{filter_key}"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached, 200

    app_query = (
        select(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .join(Student, Student.id == Application.student_id)
        .where(and_(*filters))
        .order_by(Application.application_date.desc(), Application.id.desc())
    )
    pagination = db.paginate(app_query, page=page, per_page=limit, error_out=False)
    if pagination.pages and page > pagination.pages:
        page = pagination.pages
        pagination = db.paginate(app_query, page=page, per_page=limit, error_out=False)

    rows = pagination.items

    items = [
        {
            "application": app.to_dict(),
            "drive": {
                "id": app.drive.id if app.drive else None,
                "title": app.drive.title if app.drive else None,
                "status": app.drive.effective_status.value if app.drive and app.drive.effective_status else None,
                "approval_status": app.drive.approval_status.value if app.drive and app.drive.approval_status else None,
            },
            "student": _public_student_payload(app.student),
        }
        for app in rows
    ]

    status_distribution = _enum_distribution(
        db.session.execute(
            select(Application.status, func.count(Application.id))
            .select_from(Application)
            .join(Drive, Application.drive_id == Drive.id)
            .where(and_(Drive.company_id == company.id, Drive.is_active.is_(True)))
            .group_by(Application.status)
        ).all()
    )

    payload = {
        "items": items,
        "pagination": _pagination_payload(pagination, page, limit),
        "summary": {
            "status_distribution": status_distribution,
        },
    }
    route_cache.set_json(cache_key, payload, 30)
    return payload, 200


@company_bp.route('/applications/<int:application_id>/status/', methods=['PUT'])
@company_required
def update_application_status(company, application_id):
    app_obj = db.session.execute(
        select(Application)
        .join(Drive, Application.drive_id == Drive.id)
        .where(and_(Application.id == application_id, Drive.company_id == company.id))
    ).scalar_one_or_none()

    if not app_obj:
        return {"error": "Application not found"}, 404

    data = request.get_json(silent=True) or {}
    try:
        next_status = parse_enum(ApplicationStatus, data.get("status"), "status")
    except ValueError as exc:
        return {"error": str(exc)}, 400

    if next_status == ApplicationStatus.applied:
        return {"error": "Status cannot be set to applied by company"}, 400

    allowed_next = _allowed_next_statuses(app_obj.status)
    is_terminal_repeat_update = (
        next_status == app_obj.status
        and app_obj.status in {ApplicationStatus.selected, ApplicationStatus.rejected}
    )
    if not is_terminal_repeat_update and next_status not in allowed_next:
        allowed_values = ", ".join([status.name for status in allowed_next]) or "none"
        return {
            "error": f"Invalid status transition from {app_obj.status.name} to {next_status.name}. Allowed: {allowed_values}"
        }, 400

    interview_date_value = data.get("interview_date")
    interview_time_value = data.get("interview_time")
    interview_details = data.get("interview_details")
    interview_message = str(interview_details or "").strip()

    requires_interview = next_status == ApplicationStatus.short_listed
    requires_message = next_status in {
        ApplicationStatus.short_listed,
        ApplicationStatus.selected,
        ApplicationStatus.rejected,
    }

    if requires_interview:
        if not interview_date_value or not interview_time_value:
            return {
                "error": "interview_date and interview_time are required for shortlisted status"
            }, 400
    if requires_message and not interview_message:
        return {"error": "interview_details message is required for this status"}, 400

    decision_message_for_email = None

    try:
        if requires_interview:
            parsed_date = _parse_iso_date(interview_date_value, "interview_date")
            parsed_time = _parse_iso_time(interview_time_value, "interview_time")
            scheduled_at = datetime.combine(parsed_date, parsed_time)
            if scheduled_at < datetime.now():
                return {"error": "Interview date/time cannot be in the past"}, 400

            if app_obj.interview:
                app_obj.interview.interview_date = parsed_date
                app_obj.interview.interview_time = parsed_time
                app_obj.interview.details = interview_message
            else:
                app_obj.interview = Interview(
                    interview_date=parsed_date,
                    interview_time=parsed_time,
                    details=interview_message,
                )
        elif next_status in {ApplicationStatus.selected, ApplicationStatus.rejected}:
            decision_message_for_email = interview_message

        app_obj.status = next_status
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400
    except (IntegrityError, DataError, StatementError) as exc:
        db.session.rollback()
        return {"error": db_error_message(exc)}, 400

    _send_application_status_notifications(app_obj, fallback_message=decision_message_for_email)

    route_cache.delete_prefix(f"api:company:{company.id}:drives:{app_obj.drive_id}:applications")
    route_cache.delete_prefix(f"api:company:{company.id}:drives")
    route_cache.delete_prefix(f"api:company:{company.id}:applications")
    route_cache.delete_prefix(f"api:company:{company.id}:summary")
    route_cache.delete_prefix(f"api:student:{app_obj.student_id}:")
    return {
        "message": "Application status updated successfully",
        "application": app_obj.to_dict(),
    }, 200


def _allowed_next_statuses(current_status):
    workflow = {
        ApplicationStatus.applied: [ApplicationStatus.short_listed, ApplicationStatus.rejected],
        ApplicationStatus.short_listed: [ApplicationStatus.selected, ApplicationStatus.rejected],
        ApplicationStatus.selected: [],
        ApplicationStatus.rejected: [],
    }
    return workflow.get(current_status, [])

@company_bp.route('/drives/<int:drive_id>/update/', methods=['PUT'])
@company_required
def update_drive(company, drive_id):
    drive = db.session.execute(
        select(Drive).where(and_(Drive.id == drive_id, Drive.company_id == company.id, Drive.is_active.is_(True)))
    ).scalar_one_or_none()
    if not drive:
        return {"error": "Drive not found"}, 404

    data = request.get_json(silent=True) or {}

    if "approval_status" in data or "status" in data:
        return {"error": "approval_status and status are managed by the system"}, 400

    try:
        now = datetime.now()

        if "title" in data:
            drive.title = (data.get("title") or "").strip()

        if "description" in data:
            drive.description = data.get("description")

        if "start_date" in data:
            parsed_start_date = _parse_iso_datetime(data.get("start_date"), "start_date")
            # Once drive reaches its start time, start_date is immutable.
            if drive.start_date and now >= drive.start_date and parsed_start_date != drive.start_date:
                return {"error": "Start date/time cannot be changed after the drive has started"}, 400
            drive.start_date = parsed_start_date

        if "end_date" in data:
            parsed_end_date = _parse_iso_datetime(data.get("end_date"), "end_date")
            if parsed_end_date < now:
                return {"error": "end_date cannot be in the past"}, 400
            drive.end_date = parsed_end_date

        if "work_mode" in data:
            drive.work_mode = parse_enum(WorkMode, data.get("work_mode"), "work_mode")

        if "min_cgpa" in data:
            drive.min_cgpa = float(data["min_cgpa"]) if data.get("min_cgpa") not in (None, "") else None

        if "allowed_branches" in data:
            drive.allowed_branches = _normalize_allowed_branches(data.get("allowed_branches"))

        if "max_applications" in data:
            drive.max_applications = int(data["max_applications"]) if data.get("max_applications") not in (None, "") else None

        db.session.commit()
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400
    except (IntegrityError, DataError, StatementError) as exc:
        db.session.rollback()
        return {"error": db_error_message(exc)}, 400

    route_cache.delete_prefix(f"api:company:{company.id}:drives")
    route_cache.delete_prefix(f"api:company:{company.id}:drives:{drive_id}:applications")
    route_cache.delete_prefix(f"api:company:{company.id}:summary")
    route_cache.delete_prefix("api:student:")
    route_cache.delete_prefix("api:admin:")
    return {"message": "Drive updated successfully", "drive": drive.to_dict()}, 200

@company_bp.route('/drives/<int:drive_id>/delete/', methods=['DELETE'])
@company_required
def delete_drive(company, drive_id):
    drive = db.session.execute(
        select(Drive).where(and_(Drive.id == drive_id, Drive.company_id == company.id, Drive.is_active.is_(True)))
    ).scalar_one_or_none()
    if not drive:
        return {"error": "Drive not found"}, 404
    if drive.approval_status == DriveApprovalStatus.pending:
        return {"error": "Drive can be blocked only after admin approval decision"}, 400

    drive.is_active = False
    db.session.commit()
    route_cache.delete_prefix(f"api:company:{company.id}:drives")
    route_cache.delete_prefix(f"api:company:{company.id}:drives:{drive_id}:applications")
    route_cache.delete_prefix(f"api:company:{company.id}:summary")
    route_cache.delete_prefix("api:student:")
    route_cache.delete_prefix("api:admin:")
    return {"message": "Drive deleted successfully", "drive": drive.to_dict()}, 200