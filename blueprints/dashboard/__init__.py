from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    return f"{'dashboard'.title()} module - under development"

@dashboard_bp.route('/health')
def health():
    return {"status": "ok", "module": "dashboard"}
