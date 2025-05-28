"""
User Access Control Module
Manages PM/PE login access to view assets on their assigned jobs
"""
from flask import Blueprint, render_template_string, request, session, redirect, url_for
import pandas as pd

access_control_bp = Blueprint('access_control', __name__)

# PM/PE User Database (in production, this would be in your database)
USER_ROLES = {
    'john.anderson': {
        'name': 'John Anderson',
        'role': 'Project Manager',
        'region': 'DFW',
        'jobs': ['2023-032', '2024-016', '2024-019'],
        'password': 'dfw2025'
    },
    'maria.rodriguez': {
        'name': 'Maria Rodriguez', 
        'role': 'Project Manager',
        'region': 'Houston',
        'jobs': ['2024-025', '2024-030'],
        'password': 'hou2025'
    },
    'david.wilson': {
        'name': 'David Wilson',
        'role': 'Project Engineer', 
        'region': 'West Texas',
        'jobs': ['2022-008'],
        'password': 'wtx2025'
    }
}

@access_control_bp.route('/login', methods=['GET', 'POST'])
def login():
    """PM/PE Login for job-specific asset access"""
    
    if request.method == 'POST':
        username = request.form.get('username', '').lower()
        password = request.form.get('password', '')
        
        if username in USER_ROLES and USER_ROLES[username]['password'] == password:
            session['user'] = USER_ROLES[username]
            session['username'] = username
            return redirect(url_for('access_control.my_assets'))
        else:
            error = "Invalid credentials"
            return render_template_string(login_template, error=error)
    
    return render_template_string(login_template)

@access_control_bp.route('/my-assets')
def my_assets():
    """Show assets assigned to logged-in PM/PE"""
    
    if 'user' not in session:
        return redirect(url_for('access_control.login'))
    
    user = session['user']
    
    # Load timecard data to get job assignments
    try:
        tc_df = pd.read_excel('RAG-SEL TIMECARDS - APRIL 2025.xlsx')
        
        # Filter for user's assigned jobs
        user_jobs = tc_df[tc_df['job_no'].isin(user['jobs'])]
        
        # Get unique drivers on user's jobs
        user_drivers = []
        for _, row in user_jobs.iterrows():
            user_drivers.append({
                'employee_id': row['sort_key_no'],
                'job_number': row['job_no'],
                'hours': row['hours'],
                'description': row.get('detail_desc', '')
            })
        
        # Load GPS asset data
        assets_summary = {
            'total_drivers': len(set([d['employee_id'] for d in user_drivers])),
            'total_jobs': len(user['jobs']),
            'total_hours': sum([d['hours'] for d in user_drivers]),
            'active_assets': get_user_assets(user['jobs'])
        }
        
    except Exception as e:
        user_drivers = []
        assets_summary = {'total_drivers': 0, 'total_jobs': 0, 'total_hours': 0, 'active_assets': 0}
    
    return render_template_string(assets_template, user=user, drivers=user_drivers, summary=assets_summary)

@access_control_bp.route('/logout')
def logout():
    """Logout PM/PE user"""
    session.clear()
    return redirect(url_for('access_control.login'))

def get_user_assets(job_numbers):
    """Get GPS assets assigned to user's jobs"""
    # This would integrate with your GPS asset tracking
    # For now, return estimated count based on job activity
    return len(job_numbers) * 15  # Estimated assets per job

# Login template
login_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PM/PE Login - TRAXOVO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .login-card { max-width: 400px; margin: 5rem auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-card">
            <div class="card shadow">
                <div class="card-body p-5">
                    <h3 class="text-center mb-4">PM/PE Access</h3>
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" name="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" name="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Login</button>
                    </form>
                    <hr>
                    <small class="text-muted">Test users: john.anderson, maria.rodriguez, david.wilson</small>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''

# Assets template
assets_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Assets - TRAXOVO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .page-header { background: white; padding: 2rem 0; margin-bottom: 2rem; border-bottom: 1px solid #dee2e6; }
    </style>
</head>
<body>
    <div class="page-header">
        <div class="container">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h1 class="fw-bold mb-1">Welcome, {{ user.name }}</h1>
                    <p class="text-muted mb-0">{{ user.role }} - {{ user.region }} Region</p>
                </div>
                <a href="{{ url_for('access_control.logout') }}" class="btn btn-outline-secondary">
                    <i class="fas fa-sign-out-alt me-1"></i>Logout
                </a>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- Summary Cards -->
        <div class="row g-4 mb-4">
            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <div class="fs-3 fw-bold text-primary">{{ summary.total_drivers }}</div>
                    <div>Active Drivers</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <div class="fs-3 fw-bold text-success">{{ summary.active_assets }}</div>
                    <div>GPS Assets</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <div class="fs-3 fw-bold text-info">{{ summary.total_jobs }}</div>
                    <div>Assigned Jobs</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card p-3 text-center">
                    <div class="fs-3 fw-bold text-warning">{{ "%.1f"|format(summary.total_hours) }}</div>
                    <div>Total Hours</div>
                </div>
            </div>
        </div>
        
        <!-- Job Map Button -->
        <div class="row">
            <div class="col-12">
                <div class="card p-4 text-center">
                    <h4 class="mb-3">View Your Job Assets</h4>
                    <button class="btn btn-primary btn-lg">
                        <i class="fas fa-map me-2"></i>Open GPS Asset Map
                    </button>
                    <p class="text-muted mt-2">Track assets assigned to jobs: {{ user.jobs|join(', ') }}</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
'''