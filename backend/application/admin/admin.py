from flask import Blueprint, request, jsonify
from ..model import *
from ..extension import db
from ..data_seed import seed_programme_branches, clear_programme_branches

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/ping')
def admin_index():
    return "Pong! Admin Blueprint is working!"

@admin_bp.route('/seed_programmes_branches', methods=['POST', "GET"])
def seed_programmes_branches():
    try:
        seed_programme_branches()
        return jsonify({"message": "Programmes and Branches seeded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/clear_programmes_branches', methods=['GET'])
def clear_programmes_branches():
    try:
        clear_programme_branches()
        return jsonify({"message": "Cleared programmes and branches successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@admin_bp.route('/programmes', methods=['GET'])
def get_programmes():
    programmes = db.session.query(Programme).all()
    programmes = [programme.to_dict() for programme in programmes]
    return jsonify(programmes), 200

