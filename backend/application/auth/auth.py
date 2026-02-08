from flask import request, current_app, Blueprint
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..model import User, Student, UserType, Company
from ..extension import db, password_hasher, argon2_exceptions, DUMMY_HASH
from marshmallow import ValidationError

from .validators import user_login_schema, student_register_schema, company_register_schema

from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/ping", methods=["GET", "POST"])
def ping():
    if request.method == "GET":
        return {"message": "pong"}, 200
    else:
        data = request.get_json(silent=True)
        print(data)
        return {"message": "pong", "data": data}, 200

@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 204

    json_data = request.get_json()

    if not json_data:
        return {"error": "Missing JSON body"}, 400

    try:
        data = user_login_schema.load(json_data)

    except ValidationError as err:
        return {"errors": err.messages}, 400
    email = data["email"].strip().lower()
    password = data["password"]

    user = db.session.query(User).filter_by(email=email).first()

    if not user:
        current_app.logger.warning(
            f"Failed login attempt (no such user): {email}"
        )
        password_hasher.verify(DUMMY_HASH, password)
        return {"error": "invalid credentials"}, 401

    try:
        password_hasher.verify(user.password, password)

    except argon2_exceptions.VerifyMismatchError:
        current_app.logger.warning(
            f"Failed login attempt (password mismatch): {email}"
        )
        return {"error": "invalid credentials"}, 401

    except argon2_exceptions.VerificationError as e:
        current_app.logger.error(
            f"Password verification error for {email}\n{e}"
        )
        return {"error": "internal server error"}, 500

    except Exception as e:
        current_app.logger.exception(
            f"Unexpected login error for {email}"
        )
        return {"error": "internal server error"}, 500
    
    user.last_login = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": user.user_type.value
        }
    )


    return {"access_token": access_token}, 200



@auth_bp.route("/register/student", methods=["POST"])
def register_student():
    data = student_register_schema.load(request.get_json(silent=True))

    email = data["email"].strip().lower()

    if db.session.query(User).filter_by(email=email).first():
        return {"error": "email already registered"}, 409
    
    if db.session.query(Student).filter_by(roll=data["roll_number"]).first():
        return {"error": "roll number already registered"}, 409

    student = Student(
    email=email,
    password=password_hasher.hash(data["password"]),
    name=data["name"].strip(),
    user_type=UserType.student,
    dob=data["dob"],
    gender=data["gender"],
    roll=data["roll_number"],
    admission_year=data["admission_year"],
    current_level=data["current_level"],
    prog_id=data["programme_id"],
    branch_id=data["branch_id"],
    cgpa=data["cgpa"],
    is_active=True,
    )

    db.session.add(student)
    db.session.commit()

    current_app.logger.info(f"New student registered: {email}")

    access_token = create_access_token(
        identity=str(student.id),
        additional_claims={
            "email": student.email,
            "role": student.user_type.value
        }
    )

    return {"access_token": access_token}, 201

@auth_bp.route("/register/company", methods=["POST"])
def register_company():
    data = company_register_schema.load(request.get_json(silent=True))

    email = data["email"].strip().lower()

    if db.session.query(User).filter_by(email=email).first():
        return {"error": "email already registered"}, 409

    company = Company(
        email=email,
        password=password_hasher.hash(data["password"]),
        name=data["name"].strip(),
        user_type=UserType.company,
        industry=data["industry"],
        location=data["location"],
        website=data["website"],
        contact_number=data["contact_number"],
        description=data["description"],
    )

    db.session.add(company)
    db.session.commit()

    current_app.logger.info(f"New company registered: {email}")

    access_token = create_access_token(
        identity=str(company.id),
        additional_claims={
            "email": company.email,
            "role": company.user_type.value
        }
    )

    return {"access_token": access_token}, 201

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    id = get_jwt_identity()
    current_app.logger.info(f"User: {id}")
    user = db.session.get(User, int(id))

    return {"message": f"Hello {user.name}!",
            "email": user.email,
            "role": user.user_type.value,
            "is_active": user.is_active}, 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # this should be frontend logic.
    return {"message": "Logged out successfully"}, 200

## implement password reset, email verification etc. later.