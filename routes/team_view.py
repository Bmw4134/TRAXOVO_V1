from flask import Blueprint, render_template_string

team_bp = Blueprint('team', __name__)

@team_bp.route('/zones/team/<job_number>')
def team_view(job_number):
    """Team view for specific job zone"""
    
    # Sample team data for the job
    team_members = [
        {'name': 'John Smith', 'emp_id': '200045', 'role': 'Equipment Operator', 'hours_ytd': 1247, 'status': 'Active'},
        {'name': 'Mike Johnson', 'emp_id': '200067', 'role': 'Lead Operator', 'hours_ytd': 1389, 'status': 'Active'},
        {'name': 'David Wilson', 'emp_id': '200089', 'role': 'Equipment Operator', 'hours_ytd': 1156, 'status': 'Active'},
        {'name': 'Carlos Rodriguez', 'emp_id': '200123', 'role': 'Equipment Operator', 'hours_ytd': 1203, 'status': 'Active'},
    ]
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team View - Job {{ job_number }} - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-users me-2"></i>Team - Job {{ job_number }}</h2>
                <a href="/zones/job-zones" class="btn btn-outline-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Job Zones
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Assigned Team Members</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Employee ID</th>
                                    <th>Role</th>
                                    <th>YTD Hours</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for member in team_members %}
                                <tr>
                                    <td>{{ member.name }}</td>
                                    <td>#{{ member.emp_id }}</td>
                                    <td>{{ member.role }}</td>
                                    <td>{{ member.hours_ytd }}</td>
                                    <td><span class="badge bg-success">{{ member.status }}</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', job_number=job_number, team_members=team_members)