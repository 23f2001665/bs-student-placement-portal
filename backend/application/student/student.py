from flask import Blueprint, request, jsonify
from ..model import *
from ..extensions import db
from ..data_seed import seed_students, clear_students

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/', methods=['GET'])
def index():
    return "Student Blueprint is working!", 200

@student_bp.route('/students', methods=['GET'])
def get_users():
    users = db.session.query(Student).all()
    return str(users), 200
    
@student_bp.route('/seed_students', methods=['POST', "GET"])
def seed_students_route():
    try:
        clear_students()
        seed_students(request.args.get('n', default=1000, type=int))
        return jsonify({"message": "Students seeded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@student_bp.route('/clear_students', methods=['GET'])
def clear_students_route():
    try:
        num_deleted = clear_students()
        return jsonify({"message": f"Deleted {num_deleted} students."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@student_bp.route('/students', methods=['GET'])
def get_students():
    students = db.session.query(Student).all()
    students = [student.to_dict() for student in students]
    return jsonify(students), 200

