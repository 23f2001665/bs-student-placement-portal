from ..extension import ma
from marshmallow import validate

class UserLoginValidator(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True, load_only=True)

    class Meta:
        unknown = ma.RAISE


class UserRegisterValidator(ma.Schema):
    email = ma.Email(required=True)

    password = ma.String(
        required=True,
        load_only=True,
        validate=[
            validate.Length(min=8, max=128),
        ],
    )

    name = ma.String(
        required=True,
        validate=[
            validate.Length(min=3, max=63),
            validate.Regexp(r"^[a-zA-Z ]+$"),
        ],
    )

    # intent, not authority
    role = ma.String(
        required=True,
        validate=validate.OneOf(["student", "company"]),
    )

    class Meta:
        unknown = ma.RAISE

class StudentRegisterValidator(UserRegisterValidator):
    dob = ma.Date(required=True)
    gender = ma.String(
    required=True,
    validate=validate.OneOf(["m", "f", "o"]))
    roll_number = ma.String(
    required=True,
    validate=validate.Regexp(r"^[A-Z0-9]{10}$"))
    admission_year = ma.Integer(
    required=True,
    validate=validate.Range(min=2000, max=2100))
    current_level = ma.Integer(required=True, validate=validate.Range(min=1, max=10)) # check validity based on programme
    cgpa = ma.Float(required=True, validate=validate.Range(min=0.0, max=10.0))
    programme_id = ma.Integer(required=True)
    branch_id = ma.Integer(required=True)


class CompanyRegisterValidator(UserRegisterValidator):
    industry = ma.String(required=True, validate=validate.Length(min=3, max=63))
    location = ma.String(required=True, validate=validate.Length(min=3, max=255))
    website = ma.URL(required=True)
    description = ma.String(required=True, validate=validate.Length(min=10, max=1000))
    contact_number = ma.String(
    required=True,
    validate=validate.Regexp(
        r"^\+?[0-9\-]{10,15}$",
        error="Invalid contact number"
        )
    )


user_login_schema = UserLoginValidator()
student_register_schema = StudentRegisterValidator()
company_register_schema = CompanyRegisterValidator()

__all__ = ["user_login_schema", "student_register_schema", "company_register_schema"]