from ..models import Drive


def parse_enum(enum_cls, value, field_name, required=True):
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required")
        return None

    as_text = str(value).strip()
    if not as_text:
        if required:
            raise ValueError(f"{field_name} is required")
        return None

    enum_member = enum_cls.__members__.get(as_text)
    if enum_member:
        return enum_member

    normalized = as_text.lower()
    enum_member = enum_cls.__members__.get(normalized)
    if enum_member:
        return enum_member

    for member in enum_cls:
        if str(member.value).lower() == normalized:
            return member

    raise ValueError(f"Invalid {field_name}")

def derive_drive_status(drive, now=None):
    if now is None:
        return drive.effective_status

    return Drive._derive_effective_status(
        drive.approval_status,
        drive.status,
        drive.is_active,
        drive.start_date,
        drive.end_date,
        now,
    )
