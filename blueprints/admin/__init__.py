from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
def index():
    return f"{'admin'.title()} module - under development"

@admin_bp.route('/health')
def health():
    return {"status": "ok", "module": "admin"}
