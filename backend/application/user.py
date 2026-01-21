from flask import Blueprint, request, jsonify
from .model import *
from .extension import db

# fix the url_prefix argument later

user_bp = Blueprint('user', __name__, url_prefix='/user', )

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(Programme).all()
    return str([user.__dict__ for user in users])