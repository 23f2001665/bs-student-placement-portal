from ..extensions import ma
from marshmallow import validate, validates_schema

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

class ResetPasswordSchema(ma.Schema):

    email = ma.Email(required=True)

    otp = ma.String(required=False, load_only=True, validate=validate.Regexp(r"^\d{6}$"))
    reset_token = ma.String(required=False, load_only=True)
    new_password = ma.String(required=False, load_only=True, validate=validate.Length(min=8, max=128))


    @validates_schema
    def validate_flow(self, data, **kwargs):

        otp = data.get("otp")
        token = data.get("reset_token")
        pwd = data.get("new_password")

        # Step 1: only email
        if not otp and not token and not pwd:
            return

        # Step 2: otp verification
        if otp and not token and not pwd:
            return

        # Step 3: reset
        if token and pwd:
            return

        raise ma.ValidationError(
            "Invalid reset password request format"
        )

user_login_schema = UserLoginValidator()
student_register_schema = StudentRegisterValidator()
company_register_schema = CompanyRegisterValidator()
reset_password_schema = ResetPasswordSchema()

__all__ = ["user_login_schema", "student_register_schema", "company_register_schema", "reset_password_schema"]