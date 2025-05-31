from flask import Blueprint

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def index():
    return f"{'api'.title()} module - under development"

@api_bp.route('/health')
def health():
    return {"status": "ok", "module": "api"}
