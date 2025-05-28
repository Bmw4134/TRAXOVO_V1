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

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo_fleet_2025")

# Import GPS Asset Status
from routes.gps_asset_status import gps_asset_bp
from routes.fleet_analytics_simple import fleet_bp
from routes.team_view import team_bp
from routes.team_admin import team_admin_bp
from routes.kpi_export import kpi_bp
from routes.role_dashboard import role_bp
from routes.qa_dashboard import qa_bp
from routes.elite_modules import elite_bp

# Register all blueprints
app.register_blueprint(daily_driver_bp, url_prefix='/driver')
app.register_blueprint(job_zone_bp, url_prefix='/zones')
app.register_blueprint(payroll_bp, url_prefix='/payroll')
app.register_blueprint(access_control_bp, url_prefix='/access')
app.register_blueprint(gps_asset_bp, url_prefix='/fleet')
app.register_blueprint(fleet_bp)
app.register_blueprint(team_bp)
app.register_blueprint(team_admin_bp)
app.register_blueprint(kpi_bp)
app.register_blueprint(role_bp)
app.register_blueprint(qa_bp)
app.register_blueprint(elite_bp)

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
            .module-card { transition: transform 0.2s; }
            .module-card:hover { transform: translateY(-5px); }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <!-- Header -->
            <div class="row bg-primary text-white py-3 mb-4">
                <div class="col">
                    <h1 class="mb-0"><i class="fas fa-truck me-2"></i>TRAXOVO Fleet Management</h1>
                    <p class="mb-0">Comprehensive Fleet Operations Platform</p>
                </div>
                <div class="col-auto">
                    <span class="badge bg-success fs-6">562 Assets Active</span>
                    <span class="badge bg-info fs-6 ms-2">92 Drivers</span>
                </div>
            </div>
            
            <!-- Quick Stats -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h3>1,847</h3>
                            <p class="mb-0">Hours MTD</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <h3>92.8%</h3>
                            <p class="mb-0">Fleet Efficiency</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-dark">
                        <div class="card-body text-center">
                            <h3>8</h3>
                            <p class="mb-0">Active Projects</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body text-center">
                            <h3>3</h3>
                            <p class="mb-0">Divisions</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main Modules -->
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0"><i class="fas fa-chart-line me-2"></i>Fleet Analytics</h5>
                        </div>
                        <div class="card-body">
                            <p>Process Fleet Utilization reports from Gauge with QA validation and Foundation cost integration.</p>
                            <a href="/fleet/utilization" class="btn btn-primary">Open Fleet Analytics</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0"><i class="fas fa-map-marked-alt me-2"></i>Job Zones</h5>
                        </div>
                        <div class="card-body">
                            <p>Manage driver assignments across DFW, Houston, and West Texas divisions with real-time tracking.</p>
                            <a href="/zones/integration" class="btn btn-success">Manage Job Zones</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-warning text-dark">
                            <h5 class="mb-0"><i class="fas fa-users me-2"></i>Daily Driver Reports</h5>
                        </div>
                        <div class="card-body">
                            <p>Authentic attendance tracking for 92 active drivers with GPS validation and timecard integration.</p>
                            <a href="/driver/reports" class="btn btn-warning">View Driver Reports</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Additional Modules Row -->
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="fas fa-clipboard-check me-2"></i>QA Dashboard</h5>
                        </div>
                        <div class="card-body">
                            <p>Data validation and quality assurance for all authentic data sources with complete traceability.</p>
                            <a href="/qa/status" class="btn btn-info">QA Status</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-secondary text-white">
                            <h5 class="mb-0"><i class="fas fa-satellite-dish me-2"></i>GPS Assets</h5>
                        </div>
                        <div class="card-body">
                            <p>Real-time GPS tracking for 562 assets across Ragle, Select Maintenance, and Unified Specialties.</p>
                            <a href="/fleet/gps-assets" class="btn btn-secondary">GPS Status</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card module-card h-100">
                        <div class="card-header bg-dark text-white">
                            <h5 class="mb-0"><i class="fas fa-fire me-2"></i>Elite Analytics</h5>
                        </div>
                        <div class="card-body">
                            <p>Advanced predictive analytics, optimization engine, and driver performance heatmaps.</p>
                            <a href="/elite/heatmap" class="btn btn-dark me-2">Elite Dashboard</a>
                            <a href="/admin/teams" class="btn btn-outline-dark">Team Admin</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)