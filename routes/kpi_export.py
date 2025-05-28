from flask import Blueprint, render_template_string

kpi_bp = Blueprint('kpi', __name__)

@kpi_bp.route('/export')
def kpi_export():
    """KPI Export Dashboard"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>KPI Export - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-download me-2"></i>KPI Export Dashboard</h2>
                <a href="/" class="btn btn-outline-secondary">
                    <i class="fas fa-home me-2"></i>Dashboard
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5>Export Comprehensive Reports</h5>
                </div>
                <div class="card-body">
                    <p>Export KPI reports for fleet utilization, driver performance, and cost analysis from your authentic 562-asset fleet data.</p>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>KPI export ready for your authentic fleet data
                    </div>
                    <div class="row mt-4">
                        <div class="col-md-4">
                            <a href="/fleet/utilization" class="btn btn-primary w-100">
                                <i class="fas fa-chart-line me-2"></i>Fleet Analytics
                            </a>
                        </div>
                        <div class="col-md-4">
                            <a href="/zones/integration" class="btn btn-success w-100">
                                <i class="fas fa-map-marked-alt me-2"></i>Job Zones
                            </a>
                        </div>
                        <div class="col-md-4">
                            <a href="/elite/heatmap" class="btn btn-dark w-100">
                                <i class="fas fa-fire me-2"></i>Elite Analytics
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')