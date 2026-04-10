import csv
from datetime import datetime, timedelta
from pathlib import Path

from flask import current_app
from sqlalchemy import select

from ..extensions import celery, db
from ..application.models import Application, Student


def _export_root_dir() -> Path:
    root_value = current_app.config.get("EXPORT_TEMP_ROOT", "temp")
    root_path = Path(str(root_value))
    project_root = Path(__file__).resolve().parents[2]

    if not root_path.is_absolute():
        root_path = project_root / root_path

    resolved_root = root_path.resolve()
    instance_root = (project_root / "instance").resolve()

    # Never allow export files under instance, even if env/config is misconfigured.
    if resolved_root == instance_root or instance_root in resolved_root.parents:
        fallback_root = (project_root / "temp").resolve()
        current_app.logger.warning(
            "EXPORT_TEMP_ROOT points inside instance (%s); using %s instead",
            resolved_root,
            fallback_root,
        )
        return fallback_root

    return resolved_root


def get_student_export_dir(student_id) -> Path:
    return _export_root_dir() / str(student_id)


@celery.task(bind=True, max_retries=1)
def export_student_applications_csv(self, student_id):
    student = db.session.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
    student_roll = student.roll if student and getattr(student, "roll", None) else str(student_id)

    applications = db.session.execute(
        select(Application)
        .where(Application.student_id == student_id)
        .order_by(Application.application_date.desc(), Application.id.desc())
    ).scalars().all()

    export_dir = get_student_export_dir(student_id)
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"applications_{student_id}_{timestamp}.csv"
    file_path = export_dir / filename

    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "Roll Number",
                "Company Name",
                "Drive Title",
                "Application Status",
                "Application Date",
                "Drive Start Date",
                "Drive End Date",
            ]
        )

        for app in applications:
            drive = app.drive
            company = drive.company if drive else None
            app_student = app.student
            roll_number = app_student.roll if app_student and getattr(app_student, "roll", None) else student_roll
            writer.writerow(
                [
                    roll_number,
                    company.name if company else "Deleted company",
                    drive.title if drive else "Deleted drive",
                    app.status.value if app.status else "unknown",
                    app.application_date.isoformat() if app.application_date else "",
                    drive.start_date.isoformat() if drive and drive.start_date else "",
                    drive.end_date.isoformat() if drive and drive.end_date else "",
                ]
            )

    task_id = self.request.id
    download_url = f"/api/student/applications/export/{task_id}/download"

    return {
        "student_id": student_id,
        "row_count": len(applications),
        "file_path": str(file_path),
        "file_name": filename,
        "download_url": download_url,
    }


@celery.task(bind=True, max_retries=1)
def cleanup_student_export_files(self):
    del self

    export_root = _export_root_dir()
    retention_hours = int(current_app.config.get("EXPORT_CLEANUP_RETENTION_HOURS", 24) or 24)
    cutoff = datetime.now() - timedelta(hours=retention_hours)

    removed_files = 0
    removed_dirs = 0

    if not export_root.exists():
        return {
            "export_root": str(export_root),
            "retention_hours": retention_hours,
            "removed_files": removed_files,
            "removed_dirs": removed_dirs,
        }

    for file_path in export_root.rglob("*"):
        if not file_path.is_file():
            continue

        modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
        if modified_at <= cutoff:
            file_path.unlink(missing_ok=True)
            removed_files += 1

    for dir_path in sorted((path for path in export_root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True):
        try:
            dir_path.rmdir()
            removed_dirs += 1
        except OSError:
            pass

    return {
        "export_root": str(export_root),
        "retention_hours": retention_hours,
        "removed_files": removed_files,
        "removed_dirs": removed_dirs,
    }
