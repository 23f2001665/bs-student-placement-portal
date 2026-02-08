from ..data_seed import seed_company
from flask import jsonify
from . import company_bp

@company_bp.route('/seed', methods=["GET", "POST"])
def seed_company_data():
    """Endpoint to seed company data into the database."""
    seed_company()
    return jsonify({"message": "Company data seeded successfully."}), 200

