from flask import Blueprint, render_template_string

role_bp = Blueprint('role', __name__)

@role_bp.route('/dashboard')
def role_dashboard():
    """Role-based Dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Role Dashboard - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-user-shield me-2"></i>Role-Based Dashboard</h2>
                <a href="/" class="btn btn-outline-secondary">
                    <i class="fas fa-home me-2"></i>Dashboard
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5>Role Management</h5>
                </div>
                <div class="card-body">
                    <p>Manage user roles and permissions for DFW, Houston, and West Texas divisions.</p>
                    <div class="alert alert-success">
                        <i class="fas fa-shield-alt me-2"></i>Role dashboard operational
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')