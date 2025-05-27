from flask import Blueprint, render_template

attendance_bp = Blueprint('attendance_workflow', __name__, template_folder='templates')

@attendance_bp.route('/')
def dashboard():
    return render_template('attendance_workflow/dashboard.html')