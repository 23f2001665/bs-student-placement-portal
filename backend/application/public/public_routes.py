from flask import Blueprint
from ..extension import db
from ..model import Programme
from .validators import ProgrammePublicSchema, BranchPublicSchema

public_bp = Blueprint("public", __name__, url_prefix="/public")

@public_bp.route("/ping", methods=["GET"])
def ping():
    return {"message": "pong"}, 200

@public_bp.route("/programmes_and_branches", methods=["GET"])
def get_programmes_and_branches():
    programmes = Programme.query.all()          # both included
    schema = ProgrammePublicSchema(many=True)
    return schema.dump(programmes), 200
    