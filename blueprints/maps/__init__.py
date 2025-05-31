from flask import Blueprint

maps_bp = Blueprint('maps', __name__)

@maps_bp.route('/')
def index():
    return "Maps module - under development"

@maps_bp.route('/health')
def health():
    return {"status": "ok", "module": "maps"}