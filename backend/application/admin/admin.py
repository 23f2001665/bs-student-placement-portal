from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from ..model import *
from ..extensions import db, jwt
from ..data_seed import seed_programme_branches, clear_programme_branches

from datetime import datetime
from functools import wraps

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        user = User.query.filter_by(id=identity).first()
        if not user or user.user_type != UserType.admin:
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/ping')
@admin_required
def admin_index():
    return "Pong! Admin Blueprint is working!" 

@admin_bp.route('/seed_programmes_branches', methods=['POST', "GET"])
@admin_required
def seed_programmes_branches():
    try:
        seed_programme_branches()
        return jsonify({"message": "Programmes and Branches seeded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/clear_programmes_branches', methods=['GET'])
@admin_required
def clear_programmes_branches():
    try:
        clear_programme_branches()
        return jsonify({"message": "Cleared programmes and branches successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

###########################################################
# Programme and Branch Management
###########################################################

# all programmes and branches data -> public/programmes_and_branches/

# create a branch
@admin_bp.route('/create_branch', methods=['POST'])
@admin_required
def create_branch():
    data = request.get_json()
    name = data.get('name')
    programme_id = data.get('programme_id')

    if not name or not programme_id:
        return jsonify({"error": "Name and Programme ID are required"}), 400

    programme = Programme.query.get(programme_id)
    if not programme:
        return jsonify({"error": "Programme not found"}), 404

    new_branch = Branch(name=name, programme_id=programme_id)
    db.session.add(new_branch)
    db.session.commit()

    return jsonify({"message": f"Branch '{name}' created successfully under Programme '{programme.name}'"}), 201


@admin_bp.route('/students', methods=['GET'])
@admin_required
def list_students():
    students = Student.query.all()
    student_list = []
    for student in students:
        student_info = {
            "id": student.id,
            "email": student.email,
            "name": student.name,
            "roll": student.roll,
            "admission_year": student.admission_year,
            "current_level": student.current_level,
            "cgpa": student.cgpa,
            "programme": student.programme.name if student.programme else None,
            "branch": student.branch.name if student.branch else None,
            "last_login": student.last_login.isoformat() if student.last_login else None,
            "is_active": student.is_active
        }
        student_list.append(student_info)
    return jsonify(student_list), 200


@admin_bp.route('/student/<int:student_id>', methods=['GET'])
@admin_required
def get_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    student_info = {
        "id": student.id,
        "email": student.email,
        "name": student.name,
        "roll": student.roll,
        "admission_year": student.admission_year,
        "current_level": student.current_level,
        "cgpa": student.cgpa,
        "programme": student.programme.name if student.programme else None,
        "branch": student.branch.name if student.branch else None,
        "last_login": student.last_login.isoformat() if student.last_login else None,
        "is_active": student.is_active
    }
    return jsonify(student_info), 200


@admin_bp.route('/block_student/<int:student_id>', methods=['PATCH'])
@admin_required
def block_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    if not student.is_active:
        return jsonify({"message": "Student is already blocked"}), 400
    
    student.is_active = False
    db.session.commit()
    return jsonify({"message": f"Student '{student.name}' blocked successfully"}), 200

@admin_bp.route('/unblock_student/<int:student_id>', methods=['PATCH'])
@admin_required
def unblock_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    if student.is_active:
        return jsonify({"message": "Student is already active"}), 400
    
    student.is_active = True
    db.session.commit()
    return jsonify({"message": f"Student '{student.name}' unblocked successfully"}), 200


@admin_bp.route('/companies', methods=['GET'])
@admin_required
def list_companies():
    companies = Company.query.all()
    company_list = []
    for company in companies:
        company_info = {
            "id": company.id,
            "email": company.email,
            "name": company.name,
            "profile_photo": company.profile_photo,
            "industry": company.industry,
            "website": company.website,
            "location": company.location,
            "description": company.description,
            "last_login": company.last_login.isoformat() if company.last_login else None
        }
        company_list.append(company_info)
    return jsonify(company_list), 200

@admin_bp.route('/approve_company/<int:company_id>', methods=['POST'])
@admin_required
def approve_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    if company.is_approved:
        return jsonify({"message": "Company is already approved"}), 400
    
    company.is_approved = True
    db.session.commit()
    return jsonify({"message": f"Company '{company.name}' approved successfully"}), 200

# block company
@admin_bp.route('/block_company/<int:company_id>', methods=['PATCH'])
@admin_required
def block_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    if not company.is_active:
        return jsonify({"message": "Company is already blocked"}), 400
    
    company.is_active = False
    db.session.commit()
    return jsonify({"message": f"Company '{company.name}' blocked successfully"}), 200

# unblock company
@admin_bp.route('/unblock_company/<int:company_id>', methods=['PATCH'])
@admin_required
def unblock_company(company_id):
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"error": "Company not found"}), 404
    if company.is_active:
        return jsonify({"message": "Company is already active"}), 400
    
    company.is_active = True
    db.session.commit()
    return jsonify({"message": f"Company '{company.name}' unblocked successfully"}), 200

@admin_bp.route('/drives', methods=['GET'])
@admin_required
def list_drives():
    drives = PlacementDrive.query.all()
    drive_list = []
    for drive in drives:
        drive_info = {
            "id": drive.id,
            "company": drive.company.name if drive.company else None,
            "position": drive.position,
            "description": drive.description,
            "drive_date": drive.drive_date.isoformat() if drive.drive_date else None,
            "eligibility_criteria": drive.eligibility_criteria,
            "created_at": drive.created_at.isoformat() if drive.created_at else None
        }
        drive_list.append(drive_info)
    return jsonify(drive_list), 200

# approve drive
@admin_bp.route('/approve_drive/<int:drive_id>', methods=['POST'])
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Placement Drive not found"}), 404
    if drive.approval_status == DriveApprovalStatus.approved:
        return jsonify({"message": "Placement Drive is already approved"}), 400
    
    drive.approval_status = DriveApprovalStatus.approved
    db.session.commit()
    return jsonify({"message": f"Placement Drive '{drive.position}' approved successfully"}), 200

# block drive
@admin_bp.route('/block_drive/<int:drive_id>', methods=['PATCH'])
@admin_required
def block_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Placement Drive not found"}), 404
    if drive.status == DriveStatus.cancelled:
        return jsonify({"message": "Placement Drive is already cancelled"}), 400
    
    drive.status = DriveStatus.cancelled
    db.session.commit()
    return jsonify({"message": f"Placement Drive '{drive.position}' blocked successfully"}), 200

# unblock drive
@admin_bp.route('/unblock_drive/<int:drive_id>', methods=['PATCH'])
@admin_required
def unblock_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Placement Drive not found"}), 404
    if drive.status != DriveStatus.cancelled:
        return jsonify({"message": "Placement Drive is not cancelled"}), 400
    
    drive.status = DriveStatus.upcoming  # or set to appropriate status based on drive_date
    db.session.commit()
    return jsonify({"message": f"Placement Drive '{drive.position}' unblocked successfully"}), 200

@admin_bp.route('/summary', methods=['GET'])
@admin_required
def summary():
    total_programmes = Programme.query.count()
    active_programmes = Programme.query.filter_by(is_active=True).count()

    total_branches = Branch.query.count()
    active_branches = Branch.query.filter_by(is_active=True).count()

    total_students = Student.query.count()
    active_students = Student.query.filter_by(is_active=True).count()
    not_active_students = total_students - active_students

    total_companies = Company.query.count()
    approved_companies = Company.query.filter_by(is_approved=True, is_active=True).count()
    pending_companies = Company.query.filter_by(is_approved=False, is_active=True).count()
    not_active_companies = Company.query.filter_by(is_active=False).count()

    total_drives = PlacementDrive.query.count()
    pending_drives = PlacementDrive.query.filter_by(approval_status=DriveApprovalStatus.pending).count()
    approved_drives = PlacementDrive.query.filter_by(approval_status=DriveApprovalStatus.approved).count()
    upcoming_drives = PlacementDrive.query.filter_by(status=DriveStatus.upcoming).count()
    ongoing_drives = PlacementDrive.query.filter_by(status=DriveStatus.active).count()
    completed_drives = PlacementDrive.query.filter_by(status=DriveStatus.closed).count()
    cancelled_drives = PlacementDrive.query.filter_by(status=DriveStatus.cancelled).count()

    number_of_applications = Application.query.count()
    selected_applications = Application.query.filter_by(status=ApplicationStatus.selected).count()
    rejected_applications = Application.query.filter_by(status=ApplicationStatus.rejected).count()

    summary_data = {
        "programmes": {
            "total": total_programmes,
            "active": active_programmes
        },
        "branches": {
            "total": total_branches,
            "active": active_branches
        },
        "students": {
            "total": total_students,
            "active": active_students,
            "not_active": not_active_students
        },
        "companies": {
            "total": total_companies,
            "approved": approved_companies,
            "pending": pending_companies,
            "not_active": not_active_companies
        },
        "placement_drives": {
            "total": total_drives,
            "pending_approval": pending_drives,
            "approved": approved_drives,
            "upcoming": upcoming_drives,
            "ongoing": ongoing_drives,
            "completed": completed_drives,
            "cancelled": cancelled_drives
        },
        "applications": {
            "total": number_of_applications,
            "selected": selected_applications,
            "rejected": rejected_applications
        },
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    return jsonify(summary_data), 200