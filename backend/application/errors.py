DB_CONSTRAINT_MESSAGES = {
    "user_email_not_blank": "Email cannot be blank.",
    "user_name_not_blank": "Name cannot be blank.",
    "student_roll_not_blank": "Roll number cannot be blank.",
    "student_current_level_positive": "Current level must be at least 1.",
    "student_cgpa_valid": "CGPA must be between 0 and 10.",
    "company_website_not_blank": "Website cannot be blank.",
    "drive_title_not_blank": "Title cannot be blank.",
    "drive_date_order_valid": "End date must be on or after start date.",
    "drive_start_not_before_create": "Start date/time cannot be before drive creation time.",
    "drive_pending_must_be_active": "Pending drives cannot be blocked.",
    "drive_rejected_must_be_inactive": "Rejected drives cannot be active.",
    "drive_end_not_past_for_active": "End date/time cannot be in the past for an approved active drive.",
    "drive_min_cgpa_valid": "Min CGPA must be between 0 and 10.",
    "drive_max_applications_positive": "Max applications must be greater than 0.",
    "uq_student_drive": "You have already applied to this drive.",
    "application_date_not_future": "Application time cannot be in the future.",
    "interview_datetime_not_past": "Interview date/time cannot be in the past.",
    "interview_details_not_blank": "Interview message cannot be blank.",
    # SQLite reports UNIQUE failures by column names instead of named constraints.
    "UNIQUE constraint failed: user.email": "Email already registered.",
    "UNIQUE constraint failed: student.roll": "Roll number already registered.",
    "UNIQUE constraint failed: application.student_id, application.drive_id": "You have already applied to this drive.",
}


def db_error_message(exc, constraint_messages=None):
    raw = str(getattr(exc, "orig", exc) or "")

    if "non-deterministic use of julianday() in a CHECK constraint" in raw:
        return "Database schema is outdated for date validation. Please rebuild and reseed the configured database."

    messages = dict(DB_CONSTRAINT_MESSAGES)
    if constraint_messages:
        messages.update(constraint_messages)

    for constraint, message in messages.items():
        if constraint in raw:
            return message

    if "NOT NULL constraint failed" in raw:
        field = raw.split(":", 1)[-1].strip() if ":" in raw else raw
        return f"Missing required value for {field}."

    if "UNIQUE constraint failed" in raw:
        return "A record with the same unique value already exists."

    return raw or "Database validation failed."


def is_conflict_db_message(message):
    text = str(message or "").lower()
    conflict_tokens = ("already", "duplicate", "exists")
    return any(token in text for token in conflict_tokens)
