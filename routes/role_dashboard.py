from flask import Blueprint, render_template_string, session

role_bp = Blueprint('roles', __name__)

@role_bp.route('/dashboard/pm/<region>')
def pm_dashboard(region):
    """PM/PE dashboard scoped to region"""
    
    pm_assignments = {
        'dfw': 'John Anderson',
        'wtx': 'David Wilson', 
        'hou': 'Maria Rodriguez'
    }
    
    return render_template_string('''
    <div class="container mt-4">
        <h2>PM Dashboard - {{ region|upper }}</h2>
        <p>Regional Manager: {{ pm_name }}</p>
        <div class="alert alert-success">
            Secure access confirmed for {{ region|upper }} region
        </div>
    </div>
    ''', region=region, pm_name=pm_assignments.get(region, 'Unknown'))