"""
TRAXOVO - Comprehensive Fleet Management Platform
Main application with integrated modules
"""
from flask import Flask, render_template_string, redirect, url_for
import os

# Import all modules
from routes.daily_driver_authentic import daily_driver_bp
from routes.job_zone_integration import job_zone_bp  
from routes.payroll_integration import payroll_bp
from routes.user_access_control import access_control_bp
# from routes.equipment_billing import equipment_billing_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo_fleet_2025")

# Register all blueprints
app.register_blueprint(daily_driver_bp, url_prefix='/driver')
app.register_blueprint(job_zone_bp, url_prefix='/zones')
app.register_blueprint(payroll_bp, url_prefix='/payroll')
app.register_blueprint(access_control_bp, url_prefix='/access')
# app.register_blueprint(equipment_billing_bp, url_prefix='/billing')

@app.route('/')
def dashboard():
    """Main TRAXOVO Dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TRAXOVO Fleet Management</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .module-card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: transform 0.2s;
                height: 100%;
            }
            .module-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .page-header {
                background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
                color: white;
                padding: 3rem 0;
                margin-bottom: 3rem;
            }
            .module-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="page-header">
            <div class="container text-center">
                <h1 class="display-4 fw-bold mb-3">TRAXOVO</h1>
                <p class="lead mb-0">Comprehensive Fleet Management Platform</p>
                <p class="mb-0">Ragle Inc • Select Maintenance • Unified Specialties</p>
            </div>
        </div>
        
        <div class="container">
            <div class="row g-4">
                <!-- Driver Attendance -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-primary">
                            <i class="fas fa-users-clock"></i>
                        </div>
                        <h4 class="fw-bold mb-3">Driver Attendance</h4>
                        <p class="text-muted mb-4">Track 92 active drivers with timecard validation and attendance monitoring.</p>
                        <a href="{{ url_for('daily_driver_authentic.daily_driver_reports') }}" class="btn btn-primary">
                            <i class="fas fa-chart-line me-2"></i>View Reports
                        </a>
                    </div>
                </div>
                
                <!-- Job Zone Integration -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-success">
                            <i class="fas fa-map-marked-alt"></i>
                        </div>
                        <h4 class="fw-bold mb-3">Job Zone Integration</h4>
                        <p class="text-muted mb-4">Map drivers to job sites with PM/PE assignments across DFW, Houston, and West Texas.</p>
                        <a href="{{ url_for('job_zone_integration.job_zones_dashboard') }}" class="btn btn-success">
                            <i class="fas fa-map me-2"></i>View Zones
                        </a>
                    </div>
                </div>
                
                <!-- Payroll Integration -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-warning">
                            <i class="fas fa-calculator"></i>
                        </div>
                        <h4 class="fw-bold mb-3">Payroll Integration</h4>
                        <p class="text-muted mb-4">Excel timecard processing with quantity review and cost validation.</p>
                        <a href="{{ url_for('payroll_integration.payroll_dashboard') }}" class="btn btn-warning">
                            <i class="fas fa-file-excel me-2"></i>Process Payroll
                        </a>
                    </div>
                </div>
                
                <!-- PM/PE Access -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-info">
                            <i class="fas fa-user-shield"></i>
                        </div>
                        <h4 class="fw-bold mb-3">PM/PE Access</h4>
                        <p class="text-muted mb-4">Secure login for project managers to view assets on their assigned jobs.</p>
                        <a href="{{ url_for('access_control.login') }}" class="btn btn-info">
                            <i class="fas fa-sign-in-alt me-2"></i>Login
                        </a>
                    </div>
                </div>
                
                <!-- Equipment Billing -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-danger">
                            <i class="fas fa-dollar-sign"></i>
                        </div>
                        <h4 class="fw-bold mb-3">Equipment Billing</h4>
                        <p class="text-muted mb-4">Verify billing allocations for 562 GPS assets across all divisions.</p>
                        <button class="btn btn-danger" onclick="alert('Equipment billing module coming soon!')">
                            <i class="fas fa-receipt me-2"></i>Review Billing
                        </button>
                    </div>
                </div>
                
                <!-- GPS Asset Map -->
                <div class="col-lg-4 col-md-6">
                    <div class="module-card p-4 text-center">
                        <div class="module-icon text-secondary">
                            <i class="fas fa-satellite-dish"></i>
                        </div>
                        <h4 class="fw-bold mb-3">Live GPS Map</h4>
                        <p class="text-muted mb-4">Real-time tracking of all fleet assets with job site integration.</p>
                        <button class="btn btn-secondary" onclick="alert('GPS Map integration coming soon!')">
                            <i class="fas fa-map me-2"></i>View Map
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- System Status -->
            <div class="row mt-5">
                <div class="col-12">
                    <div class="module-card p-4">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <div class="fs-4 fw-bold text-primary">92</div>
                                <div class="text-muted">Active Drivers</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fs-4 fw-bold text-success">562</div>
                                <div class="text-muted">GPS Assets</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fs-4 fw-bold text-info">3</div>
                                <div class="text-muted">Companies</div>
                            </div>
                            <div class="col-md-3">
                                <div class="fs-4 fw-bold text-warning">3</div>
                                <div class="text-muted">Divisions</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="mt-5 py-4 bg-light text-center">
            <div class="container">
                <p class="text-muted mb-0">TRAXOVO Fleet Management • Powered by authentic Gauge API data</p>
            </div>
        </footer>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)