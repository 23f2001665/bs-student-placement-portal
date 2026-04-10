import smtplib
from datetime import date, datetime, time, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import and_, func, or_, select

from ..application.models import (
    Application,
    ApplicationStatus,
    Company,
    Drive,
    DriveApprovalStatus,
    Interview,
    Student,
    User,
    UserType,
)
from ..extensions import celery, db
from flask import current_app, render_template


def _send_email(to_email, subject, body_text, body_html=None):
    if body_html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
    else:
        msg = MIMEText(body_text)

    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_USERNAME"]
    msg["To"] = to_email

    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"]
    ) as server:
        server.starttls()
        server.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )
        server.sendmail(
            current_app.config["MAIL_USERNAME"],
            [to_email],
            msg.as_string()
        )


def _is_export_notification(subject, body):
    subject_text = str(subject or "").strip().lower()
    body_text = str(body or "").strip().lower()
    return (
        "placement applications export is ready" in subject_text
        or "placement application history csv is ready for download" in body_text
    )


def _previous_month_window(anchor_date):
    first_of_current_month = date(anchor_date.year, anchor_date.month, 1)
    previous_month_last_day = first_of_current_month - timedelta(days=1)
    previous_month_first_day = date(previous_month_last_day.year, previous_month_last_day.month, 1)
    period_start = datetime.combine(previous_month_first_day, time.min)
    period_end = datetime.combine(first_of_current_month, time.min)
    return previous_month_first_day, previous_month_last_day, period_start, period_end


def _resolve_admin_report_recipient():
    configured = str(current_app.config.get("ADMIN_REPORT_EMAIL") or "").strip()
    if configured:
        return configured

    admin_user = (
        db.session.execute(
            select(User)
            .where(
                User.user_type == UserType.admin,
                User.is_active.is_(True),
            )
            .order_by(User.id.asc())
        )
        .scalars()
        .first()
    )
    if admin_user and admin_user.email:
        return admin_user.email

    fallback = str(current_app.config.get("MAIL_USERNAME") or "").strip()
    return fallback or None


def _build_monthly_activity_metrics(period_start, period_end):
    drives_conducted = int(
        db.session.execute(
            select(func.count(Drive.id)).where(
                Drive.start_date >= period_start,
                Drive.start_date < period_end,
                Drive.approval_status == DriveApprovalStatus.approved,
            )
        ).scalar_one()
    )

    applications_total = int(
        db.session.execute(
            select(func.count(Application.id)).where(
                Application.application_date >= period_start,
                Application.application_date < period_end,
            )
        ).scalar_one()
    )

    students_applied = int(
        db.session.execute(
            select(func.count(func.distinct(Application.student_id))).where(
                Application.application_date >= period_start,
                Application.application_date < period_end,
            )
        ).scalar_one()
    )

    selected_applications_total = int(
        db.session.execute(
            select(func.count(Application.id)).where(
                Application.application_date >= period_start,
                Application.application_date < period_end,
                Application.status == ApplicationStatus.selected,
            )
        ).scalar_one()
    )

    students_selected = int(
        db.session.execute(
            select(func.count(func.distinct(Application.student_id))).where(
                Application.application_date >= period_start,
                Application.application_date < period_end,
                Application.status == ApplicationStatus.selected,
            )
        ).scalar_one()
    )

    return {
        "drives_conducted": drives_conducted,
        "applications_total": applications_total,
        "students_applied": students_applied,
        "selected_applications_total": selected_applications_total,
        "students_selected": students_selected,
    }


@celery.task(bind=True, max_retries=3)
def send_otp_email(self, to_email, otp):
    try:
        body = f"""
Your OTP is: {otp}

This OTP will expire in 5 minutes.
Do not share it with anyone.
"""
        _send_email(to_email, "Your OTP Code", body)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@celery.task(bind=True, max_retries=3)
def send_application_status_email(self, to_email, subject, body):
    try:
        if _is_export_notification(subject, body):
            return
        _send_email(to_email, subject, body)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@celery.task(bind=True, max_retries=3)
def send_student_daily_digest_email(self, to_email, subject, body_text, body_html=None):
    try:
        _send_email(to_email, subject, body_text, body_html)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)


@celery.task(bind=True, max_retries=1)
def send_daily_student_drive_and_interview_digest(self):
    today = date.today()
    now = datetime.now()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)

    drives_for_today = (
        db.session.execute(
            select(Drive, Company)
            .join(Company, Company.id == Drive.company_id)
            .where(
                Drive.is_active.is_(True),
                Drive.approval_status == DriveApprovalStatus.approved,
                Company.is_active.is_(True),
                Company.is_approved.is_(True),
                or_(
                    and_(Drive.start_date >= today_start, Drive.start_date <= today_end),
                    and_(Drive.start_date <= today_end, Drive.end_date >= today_start),
                ),
            )
            .order_by(Drive.start_date.asc(), Drive.id.asc())
        )
        .all()
    )

    active_students = (
        db.session.execute(select(Student).where(Student.is_active.is_(True)).order_by(Student.id.asc()))
        .scalars()
        .all()
    )

    sent_count = 0
    skipped_count = 0
    eligible_drive_mentions = 0

    for student in active_students:
        if not student.email:
            skipped_count += 1
            continue

        interviews_today = (
            db.session.execute(
                select(Interview, Application, Drive, Company)
                .join(Application, Interview.application_id == Application.id)
                .join(Drive, Application.drive_id == Drive.id)
                .join(Company, Drive.company_id == Company.id)
                .where(
                    Application.student_id == student.id,
                    Interview.interview_date == today,
                )
                .order_by(Interview.interview_time.asc(), Interview.id.asc())
            )
            .all()
        )

        eligible_drives_for_today = []
        for drive, company in drives_for_today:
            if drive.min_cgpa is not None and (student.cgpa is None or student.cgpa < drive.min_cgpa):
                continue

            allowed_branches = drive.allowed_branches_list
            if allowed_branches:
                student_branch_key = student.branch.name if student.branch else None
                if not student_branch_key or student_branch_key not in allowed_branches:
                    continue

            eligible_drives_for_today.append((drive, company))

        if not eligible_drives_for_today and not interviews_today:
            skipped_count += 1
            continue

        drive_lines = []
        for drive, company in eligible_drives_for_today:
            if now < drive.start_date:
                status_label = "Upcoming today"
            elif drive.start_date <= now <= drive.end_date:
                status_label = "Active"
            else:
                status_label = "Open today"
            drive_lines.append(
                f"- [{status_label}] {drive.title} | {company.name} | "
                f"{drive.start_date.strftime('%d %b %Y %I:%M %p')} - {drive.end_date.strftime('%d %b %Y %I:%M %p')}"
            )
            eligible_drive_mentions += 1

        interview_lines = []
        for interview, _application, drive, company in interviews_today:
            interview_lines.append(
                f"- {interview.interview_time.strftime('%I:%M %p')} | {company.name} | {drive.title}"
            )

        body_parts = [
            f"Hello {student.name},",
            "",
            f"Here is your placement update for {today.strftime('%d %b %Y')}.",
            "",
            "Drives (upcoming/active for today):",
            *(drive_lines or ["- No upcoming/active drives for today."]),
            "",
            "Your interviews for today:",
            *(interview_lines or ["- No interviews scheduled for today."]),
            "",
            "Regards,",
            "Placement Portal",
        ]

        body_text = "\n".join(body_parts)
        body_html = render_template(
            "emails/daily_digest.html",
            student_name=student.name,
            date_label=today.strftime('%d %b %Y'),
            drive_lines=drive_lines,
            interview_lines=interview_lines,
        )

        send_student_daily_digest_email.delay(
            student.email,
            f"Daily Placement Update - {today.strftime('%d %b %Y')}",
            body_text,
            body_html,
        )
        sent_count += 1

    return {
        "date": today.isoformat(),
        "students_total": len(active_students),
        "emails_queued": sent_count,
        "students_skipped": skipped_count,
        "drives_listed": len(drives_for_today),
        "eligible_drive_mentions": eligible_drive_mentions,
    }


@celery.task(bind=True, max_retries=2)
def send_monthly_admin_activity_report(self):
    try:
        today = date.today()
        month_start, month_end, period_start, period_end = _previous_month_window(today)
        recipient = _resolve_admin_report_recipient()

        if not recipient:
            return {
                "status": "skipped",
                "reason": "No admin email configured",
            }

        metrics = _build_monthly_activity_metrics(period_start, period_end)
        month_label = month_start.strftime("%B %Y")
        generated_on = datetime.now().strftime("%d %b %Y %I:%M %p")

        body_text = "\n".join(
            [
                f"Monthly Placement Activity Report - {month_label}",
                f"Report period: {month_start.strftime('%d %b %Y')} to {month_end.strftime('%d %b %Y')}",
                "",
                f"Drives conducted: {metrics['drives_conducted']}",
                f"Students applied: {metrics['students_applied']}",
                f"Students selected: {metrics['students_selected']}",
                f"Applications received: {metrics['applications_total']}",
                f"Selected applications: {metrics['selected_applications_total']}",
                "",
                f"Generated on: {generated_on}",
            ]
        )

        body_html = render_template(
            "emails/monthly_activity_report.html",
            month_label=month_label,
            month_start_label=month_start.strftime("%d %b %Y"),
            month_end_label=month_end.strftime("%d %b %Y"),
            generated_on=generated_on,
            metrics=metrics,
        )

        _send_email(
            recipient,
            f"Monthly Placement Activity Report - {month_label}",
            body_text,
            body_html,
        )

        return {
            "status": "sent",
            "recipient": recipient,
            "month": month_label,
            **metrics,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)