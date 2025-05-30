from flask import Blueprint, jsonify

api_assets = Blueprint('api_assets', __name__)

@api_assets.route('/api/assets')
def get_assets():
    # Replace this with Supabase query
    return jsonify({
        "total": 717,
        "active": 614,
        "utilization": 87.5,
        "assets": [
            {
                "id": "EQ-1023",
                "description": "CAT 305E2",
                "category": "Mini Excavator",
                "make_model": "CAT 305E2",
                "year": 2018,
                "status": "Active",
                "location": "DFW Yard"
            }
        ]
    })
