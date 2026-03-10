from flask import Blueprint
from ..extensions import db, redis_client
from ..model import Programme
from .validators import ProgrammePublicSchema, BranchPublicSchema
from .tasks import send_email

import json

public_bp = Blueprint("public", __name__, url_prefix="/public")

@public_bp.route("/ping", methods=["GET"])
def ping():
    return {"message": "pong"}, 200

@public_bp.route("/programmes_and_branches", methods=["GET"])
def get_programmes_and_branches():
    
    cached_data = redis_client.get("programmes_and_branches")
    if cached_data:
        return {"data": json.loads(cached_data), "source": "cache"}, 200
    
    programmes = Programme.query.all()          # both included
    schema = ProgrammePublicSchema(many=True)
    data = schema.dump(programmes)
    redis_client.set(name="programmes_and_branches", value=json.dumps(data), ex=3600)  # cache for 1 hour
    return data, 200

@public_bp.route("/test_task", methods=["GET"])
def test_task():
    body = """
    This is a test email sent from the Celery task in the Placement Portal application.
    """
    send_email.delay("Test Email from Placement Portal", ["23f2001665@ds.study.iitm.ac.in"], body)
    return {"message": "Email task has been triggered!"}, 200

@public_bp.route("/check_email_status", methods=["GET"])
def check_email_status():
    return ""