from celery.schedules import crontab


def _parse_cron_expression(expr):
    token = str(expr or "").strip()
    parts = token.split()
    if len(parts) != 5:
        return "15", "8", "1", "*", "*"

    minute, hour, day_of_month, month_of_year, day_of_week = parts
    return minute, hour, day_of_month, month_of_year, day_of_week


def get_beat_schedule(config):
    daily_digest_hour = int(config.get("CELERY_BEAT_DAILY_DIGEST_HOUR", 8))
    daily_digest_minute = int(config.get("CELERY_BEAT_DAILY_DIGEST_MINUTE", 0))
    cleanup_hour = int(config.get("CELERY_BEAT_EXPORT_CLEANUP_HOUR", 2))
    cleanup_minute = int(config.get("CELERY_BEAT_EXPORT_CLEANUP_MINUTE", 0))
    cron_expr = config.get("CELERY_BEAT_MONTHLY_REPORT_CRON", "15 8 1 * *")
    monthly_minute, monthly_hour, monthly_day_of_month, monthly_month_of_year, monthly_day_of_week = _parse_cron_expression(cron_expr)

    return {
        "daily-student-drive-interview-digest": {
            "task": "backend.tasks.send_email.send_daily_student_drive_and_interview_digest",
            "schedule": crontab(hour=daily_digest_hour, minute=daily_digest_minute),
        },
        "daily-student-export-cleanup": {
            "task": "backend.tasks.export.cleanup_student_export_files",
            "schedule": crontab(hour=cleanup_hour, minute=cleanup_minute),
        },
        "monthly-admin-placement-activity-report": {
            "task": "backend.tasks.send_email.send_monthly_admin_activity_report",
            "schedule": crontab(
                minute=monthly_minute,
                hour=monthly_hour,
                day_of_month=monthly_day_of_month,
                month_of_year=monthly_month_of_year,
                day_of_week=monthly_day_of_week,
            ),
        },
    }
