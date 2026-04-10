from ...extensions import *
from ..models import User, UserType, Student, Company, Branches, Gender, IndustryType
from ..errors import db_error_message, is_conflict_db_message
from ..services.otp import OTPService, OTP
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from argon2.exceptions import VerifyMismatchError, VerificationError
from flask import Blueprint, request, jsonify, session, current_app
from functools import partial
from pathlib import Path
from time import time

otp_service = OTPService()
otp_generator = partial(OTP, service=otp_service)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/')
def index():
    return "Welcome to the PPA API", 200

@auth_bp.route('/register/student/', methods=['POST'])
def register_user():
    is_multipart = request.content_type and request.content_type.startswith('multipart/form-data')
    data = request.form if is_multipart else (request.get_json(silent=True) or {})

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    branch_str = data.get('branch')
    gender_str = data.get('gender')
    roll = data.get('roll')
    current_level = data.get('current_level')
    cgpa = data.get('cgpa')
    resume_file = request.files.get('resume') if is_multipart else None


    if not email or not password:
        return {"error": "Email and password required"}, 400

    if not roll or not branch_str or not current_level or not name:
        return {"error": "Roll number, branch, current level and name are required"}, 400

    if not resume_file or not resume_file.filename:
        return {"error": "Resume PDF is required"}, 400

    if not resume_file.filename.lower().endswith('.pdf'):
        return {"error": "Resume must be a PDF file"}, 400

    resume_file.stream.seek(0, 2)
    resume_size = resume_file.stream.tell()
    resume_file.stream.seek(0)

    if resume_size > 1024 * 1024:
        return {"error": "Resume file must be 1MB or smaller"}, 400

    try:
        gender = Gender[gender_str] if gender_str else None
        branch = Branches[branch_str] if branch_str else None
        current_level = int(current_level)
        cgpa = float(cgpa) if cgpa not in (None, "") else None
    except KeyError:
        return {"error": "Invalid enum key"}, 400
    except ValueError:
        return {"error": "Invalid enum value"}, 400

    try:
        new_user = Student(
            email=email,
            password=password_hasher.hash(password),
            name=name,
            user_type=UserType.student,  # important
            gender=gender,
            roll=roll,
            branch=branch,
            current_level=current_level,
            cgpa=cgpa
        )

        db.session.add(new_user)
        db.session.flush()

        uploads_dir = Path(current_app.root_path).parent / 'uploads'
        uploads_dir.mkdir(parents=True, exist_ok=True)

        resume_filename = f"{new_user.id}.pdf"
        resume_path = uploads_dir / resume_filename
        resume_file.save(resume_path)

        new_user.resume_path = f"uploads/{resume_filename}"
        db.session.commit()

        return new_user.to_dict(), 201

    except (IntegrityError, DataError, StatementError) as e:
        db.session.rollback()
        message = db_error_message(e)
        if is_conflict_db_message(message):
            return {"error": message}, 409
        return {
            "error": "Student registration failed",
            "details": message,
        }, 400
    
@auth_bp.route('/register/company/', methods=['POST'])
def register_company():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    industry_type_str = data.get('industry_type')
    website = data.get('website')
    description = data.get('description')

    if not email or not password:
        return {"error": "Email and password required"}, 400

    try:
        industry_type = IndustryType[industry_type_str] if industry_type_str else None
    except KeyError:
        return {"error": "Invalid enum key"}, 400
    except ValueError:
        return {"error": "Invalid enum value"}, 400

    try:
        new_company = Company(
            email=email,
            password=password_hasher.hash(password),
            name=name,
            user_type=UserType.company,  # important
            industry_type=industry_type,
            website=website,
            description=description
        )

        db.session.add(new_company)
        db.session.commit()

        return new_company.to_dict(), 201

    except (IntegrityError, DataError, StatementError) as e:
        db.session.rollback()
        message = db_error_message(e)
        if is_conflict_db_message(message):
            return {"error": message}, 409
        return {
            "error": "Company registration failed",
            "details": message,
        }, 400

@auth_bp.route('/login/', methods=['POST'])
def login_user():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return {
            "success": False,
            "message": "Email and password required",
            "data": None
        }, 400

    user = db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    try:
        if user and password_hasher.verify(user.password, password):

            if not user.is_active:
                return {
                    "success": False,
                    "message": "Account is blocked. Please contact admin.",
                    "data": None
                }, 403

            if session.get("current_user"):
                return {
                    "success": False,
                    "message": "Already logged in",
                    "data": None
                }, 400

            session["current_user"] = user.id
            session["last_active"] = time()

            return {
                "success": True,
                "message": "Login successful",
                "data": user.to_dict()
            }, 200

    except (VerifyMismatchError, VerificationError):
        return {
            "success": False,
            "message": "Invalid credentials",
            "data": None
        }, 401
    except Exception as e:
        return {
            "success": False,
            "message": "An error occurred during login",
            "error": str(e),
            "data": None
        }, 500

    return {
        "success": False,
        "message": "Invalid credentials",
        "data": None
    }, 401


@auth_bp.route('/logout/', methods=['POST'])
def logout_user():
    current = session.get("current_user")

    if current:
        session.pop("current_user", None)
        return {"message": "Logged out successfully"}, 200

    # Idempotent logout response for token/local-storage based clients.
    return {"message": "No active session, logout treated as successful"}, 200


#### Forgot Password Flow ####

@auth_bp.route('/send-otp/', methods=['POST'])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get('email')

    if not email:
        return {"error": "Email required"}, 400

    user = db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        return {"error": "User not found"}, 404

    otp = otp_generator(email=email)
    otp.send()

    return {"message": "OTP sent to email"}, 200

@auth_bp.route('/reset-password/', methods=['POST'])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    otp_value = data.get('otp')
    new_password = data.get('password')

    if not email or not otp_value or not new_password:
        return {"error": "Email, OTP and new password required"}, 400

    user = db.session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()

    if not user:
        return {"error": "User not found"}, 404

    # OTP is single-use and expiry is enforced by Redis TTL in OTPService.
    if not otp_generator(email=email).verify(otp_value):
        return {"error": "Invalid or expired OTP"}, 400

    user.password = password_hasher.hash(new_password)
    db.session.commit()

    return {"message": "Password reset successful"}, 200
