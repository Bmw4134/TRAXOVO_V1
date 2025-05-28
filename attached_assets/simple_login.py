from flask import Blueprint, request, session, redirect, url_for
from flask_wtf.csrf import csrf_exempt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/direct-login', methods=['POST'])
@csrf_exempt
def direct_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == "admin" and password == "TRAXOVO_Fleet_2025!@#":
        session['user'] = username
        return redirect(url_for('dashboard'))

    return "Login failed", 403
