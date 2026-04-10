from .auth import auth_bp
from .company import company_bp
from .student import student_bp
from .admin import admin_bp

from flask import Blueprint
from ..models import Branches, IndustryType, Gender, UserType
from ..services.cache import RouteCache

api_bp = Blueprint('api', __name__, url_prefix='/api')
route_cache = RouteCache()

@api_bp.route('/')
def index():
    return {"message": "Welcome to the API!", "version": "1.0"}

@api_bp.route('/branches')
def branches():
    cache_key = "api:enums:branches"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "branches": [
            {"value": item.name, "label": item.value}
            for item in Branches
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

@api_bp.route('/brances')
def brances_alias():
    # Backward-compatible alias for a common misspelling.
    cache_key = "api:enums:branches"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "branches": [
            {"value": item.name, "label": item.value}
            for item in Branches
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

@api_bp.route('/industries')
def industries():
    cache_key = "api:enums:industries"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "industries": [
            {"value": item.name, "label": item.value}
            for item in IndustryType
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

@api_bp.route('/genders')
def genders():
    cache_key = "api:enums:genders"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "genders": [
            {"value": item.name, "label": item.value}
            for item in Gender
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

@api_bp.route('/user-types')
def user_types():
    cache_key = "api:enums:user-types"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "user_types": [
            {"value": item.name, "label": item.value}
            for item in UserType
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

@api_bp.route('/enums')
def enums():
    cache_key = "api:enums:all"
    cached = route_cache.get_json(cache_key)
    if cached is not None:
        return cached

    payload = {
        "branches": [
            {"value": item.name, "label": item.value}
            for item in Branches
        ],
        "industries": [
            {"value": item.name, "label": item.value}
            for item in IndustryType
        ],
        "genders": [
            {"value": item.name, "label": item.value}
            for item in Gender
        ],
        "user_types": [
            {"value": item.name, "label": item.value}
            for item in UserType
        ]
    }
    route_cache.set_json(cache_key, payload, 300)
    return payload

api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(company_bp)
api_bp.register_blueprint(student_bp)
api_bp.register_blueprint(admin_bp)