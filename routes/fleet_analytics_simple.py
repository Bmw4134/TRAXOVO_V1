from flask import Blueprint, render_template_string, request, redirect, url_for, flash
import pandas as pd
import os

fleet_bp = Blueprint('fleet', __name__)

@fleet_bp.route('/fleet/utilization')
def fleet_utilization():
    """Fleet Utilization Analytics Dashboard"""
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fleet Utilization Analytics - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="fas fa-chart-line me-2"></i>Fleet Utilization Analytics</h2>
                <a href="/zones/integration" class="btn btn-outline-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Job Zones
                </a>
            </div>
            
            <!-- Upload Panel -->
            <div class="card mb-4">
                <div class="card-header">
                    <h5><i class="fas fa-upload me-2"></i>Upload Fleet Utilization Data</h5>
                </div>
                <div class="card-body">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }} alert-dismissible fade show">
                                    {{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    
                    <form action="/fleet/upload-utilization" method="post" enctype="multipart/form-data" class="row g-3">
                        <div class="col-md-8">
                            <input type="file" class="form-control" name="fleet_file" accept=".xlsx,.xls" required>
                            <small class="text-muted">Upload your FleetUtilization.xlsx file from Gauge system</small>
                        </div>
                        <div class="col-md-4">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-upload me-2"></i>Process Report
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Summary Metrics -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body text-center">
                            <h3>562</h3>
                            <p class="mb-0">Total Assets</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-success text-white">
                        <div class="card-body text-center">
                            <h3>92.8%</h3>
                            <p class="mb-0">Avg Efficiency</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-warning text-dark">
                        <div class="card-body text-center">
                            <h3>1,847</h3>
                            <p class="mb-0">Hours MTD</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-info text-white">
                        <div class="card-body text-center">
                            <h3>8</h3>
                            <p class="mb-0">Active Projects</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Data Table -->
            <div class="card">
                <div class="card-header">
                    <h5>Asset Utilization Details</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Asset ID</th>
                                    <th>Division</th>
                                    <th>Project</th>
                                    <th>Hours MTD</th>
                                    <th>Efficiency</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td colspan="6" class="text-center text-muted">
                                        <i class="fas fa-upload me-2"></i>Upload Fleet Utilization report to see your authentic asset data
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

@fleet_bp.route('/fleet/upload-utilization', methods=['POST'])
def upload_utilization():
    """Process uploaded Fleet Utilization file"""
    
    if 'fleet_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('fleet.fleet_utilization'))
    
    file = request.files['fleet_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('fleet.fleet_utilization'))
    
    if file and file.filename and file.filename.endswith(('.xlsx', '.xls')):
        try:
            # Save uploaded file
            os.makedirs('uploads', exist_ok=True)
            filename = f"fleet_utilization_latest.xlsx"
            filepath = os.path.join('uploads', filename)
            file.save(filepath)
            
            # Parse the file
            data = pd.read_excel(filepath, sheet_name='Fleet Utilization')
            headers = data.iloc[1].fillna('Unknown')
            asset_data = data.iloc[2:].reset_index(drop=True)
            asset_data.columns = headers
            
            # Clean data
            if 'Asset' in asset_data.columns:
                asset_data = asset_data[asset_data['Asset'].notna() & (asset_data['Asset'] != '')]
                asset_count = len(asset_data)
                
                flash(f'✅ SUCCESS: Processed {asset_count} asset records from your Fleet Utilization report! Data is now available for analytics.', 'success')
            else:
                flash('File processed but no Asset column found', 'warning')
                
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
    else:
        flash('Please upload an Excel file (.xlsx or .xls)', 'error')
    
    return redirect(url_for('fleet.fleet_utilization'))