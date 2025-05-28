from flask import Blueprint, render_template_string, request, redirect, url_for, flash, jsonify
import pandas as pd
import os
import json

team_admin_bp = Blueprint('team_admin', __name__)

@team_admin_bp.route('/admin/teams')
def team_admin():
    """Team Administration Interface"""
    
    # Load current team assignments
    teams = load_team_assignments()
    pm_assignments = load_pm_assignments()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Administration - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .admin-card { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <div class="container-fluid mt-4">
            <div class="row">
                <!-- Header -->
                <div class="col-12 mb-4">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h2><i class="fas fa-users-cog me-2"></i>Team Administration</h2>
                            <p class="text-muted">Manage driver assignments, PM mappings, and team configurations</p>
                        </div>
                        <div>
                            <a href="/" class="btn btn-outline-secondary me-2">
                                <i class="fas fa-arrow-left me-1"></i>Dashboard
                            </a>
                            <button class="btn btn-success" onclick="saveAllChanges()">
                                <i class="fas fa-save me-1"></i>Save All Changes
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="col-12 mb-4">
                    <div class="card admin-card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0"><i class="fas fa-bolt me-2"></i>Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row g-3">
                                <div class="col-md-3">
                                    <button class="btn btn-outline-primary w-100" onclick="addNewDriver()">
                                        <i class="fas fa-user-plus me-2"></i>Add Driver
                                    </button>
                                </div>
                                <div class="col-md-3">
                                    <button class="btn btn-outline-info w-100" onclick="bulkAssignPM()">
                                        <i class="fas fa-users me-2"></i>Bulk Assign PM
                                    </button>
                                </div>
                                <div class="col-md-3">
                                    <button class="btn btn-outline-warning w-100" onclick="importFromTimecard()">
                                        <i class="fas fa-file-import me-2"></i>Import Timecard
                                    </button>
                                </div>
                                <div class="col-md-3">
                                    <button class="btn btn-outline-success w-100" onclick="exportTeamData()">
                                        <i class="fas fa-download me-2"></i>Export Data
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- PM Assignments -->
                <div class="col-md-6 mb-4">
                    <div class="card admin-card">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0"><i class="fas fa-user-tie me-2"></i>PM Assignments</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Job Pattern</th>
                                            <th>PM Assigned</th>
                                            <th>Division</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="pm-assignments">
                                        <tr>
                                            <td><input type="text" class="form-control form-control-sm" value="2023-032*" id="job-pattern-1"></td>
                                            <td>
                                                <select class="form-select form-select-sm" id="pm-select-1">
                                                    <option value="John Anderson">John Anderson</option>
                                                    <option value="Maria Rodriguez">Maria Rodriguez</option>
                                                    <option value="David Wilson">David Wilson</option>
                                                </select>
                                            </td>
                                            <td><span class="badge bg-primary">DFW</span></td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-danger" onclick="removePMRule(1)">
                                                    <i class="fas fa-times"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                                <button class="btn btn-sm btn-outline-primary" onclick="addPMRule()">
                                    <i class="fas fa-plus me-1"></i>Add Rule
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Driver Management -->
                <div class="col-md-6 mb-4">
                    <div class="card admin-card">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0"><i class="fas fa-users me-2"></i>Driver Management</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <input type="text" class="form-control" placeholder="Search drivers..." id="driver-search">
                            </div>
                            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                                <table class="table table-sm">
                                    <thead class="sticky-top bg-light">
                                        <tr>
                                            <th>Name</th>
                                            <th>ID</th>
                                            <th>Current Job</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody id="driver-list">
                                        <!-- Driver data will be loaded here -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Job Zone Configuration -->
                <div class="col-12">
                    <div class="card admin-card">
                        <div class="card-header bg-warning text-dark">
                            <h5 class="mb-0"><i class="fas fa-map-marked-alt me-2"></i>Job Zone Configuration</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-8">
                                    <div class="table-responsive">
                                        <table class="table table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Job Number</th>
                                                    <th>Assigned Drivers</th>
                                                    <th>PM</th>
                                                    <th>Division</th>
                                                    <th>Working Hours</th>
                                                    <th>Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody id="job-zone-config">
                                                <!-- Job zones will be loaded here -->
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card">
                                        <div class="card-header">
                                            <h6 class="mb-0">Edit Selected Job</h6>
                                        </div>
                                        <div class="card-body">
                                            <div class="mb-3">
                                                <label class="form-label">Job Number</label>
                                                <input type="text" class="form-control" id="edit-job-number" readonly>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">PM Assignment</label>
                                                <select class="form-select" id="edit-job-pm">
                                                    <option value="John Anderson">John Anderson (DFW)</option>
                                                    <option value="Maria Rodriguez">Maria Rodriguez (Houston)</option>
                                                    <option value="David Wilson">David Wilson (West Texas)</option>
                                                </select>
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">Start Time</label>
                                                <input type="time" class="form-control" id="edit-start-time" value="07:00">
                                            </div>
                                            <div class="mb-3">
                                                <label class="form-label">End Time</label>
                                                <input type="time" class="form-control" id="edit-end-time" value="17:00">
                                            </div>
                                            <button class="btn btn-primary w-100" onclick="updateJobConfig()">
                                                <i class="fas fa-save me-1"></i>Update Job
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function addNewDriver() {
                const name = prompt("Enter driver name:");
                const empId = prompt("Enter employee ID:");
                if (name && empId) {
                    // Add driver logic
                    alert('Driver added: ' + name);
                }
            }
            
            function bulkAssignPM() {
                const pm = prompt("Select PM (John Anderson, Maria Rodriguez, David Wilson):");
                if (pm) {
                    alert('Bulk PM assignment: ' + pm);
                }
            }
            
            function importFromTimecard() {
                alert('Import timecard data functionality');
            }
            
            function exportTeamData() {
                window.location.href = '/admin/teams/export';
            }
            
            function addPMRule() {
                const tbody = document.getElementById('pm-assignments');
                const newRow = `
                    <tr>
                        <td><input type="text" class="form-control form-control-sm" placeholder="Job Pattern"></td>
                        <td>
                            <select class="form-select form-select-sm">
                                <option value="John Anderson">John Anderson</option>
                                <option value="Maria Rodriguez">Maria Rodriguez</option>
                                <option value="David Wilson">David Wilson</option>
                            </select>
                        </td>
                        <td><span class="badge bg-secondary">Auto</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger" onclick="this.closest('tr').remove()">
                                <i class="fas fa-times"></i>
                            </button>
                        </td>
                    </tr>
                `;
                tbody.insertAdjacentHTML('beforeend', newRow);
            }
            
            function removePMRule(id) {
                if (confirm('Remove this PM assignment rule?')) {
                    document.getElementById('pm-assignments').rows[id-1].remove();
                }
            }
            
            function updateJobConfig() {
                const jobNumber = document.getElementById('edit-job-number').value;
                const pm = document.getElementById('edit-job-pm').value;
                const startTime = document.getElementById('edit-start-time').value;
                const endTime = document.getElementById('edit-end-time').value;
                
                alert(`Updated ${jobNumber}: PM=${pm}, Hours=${startTime}-${endTime}`);
            }
            
            function saveAllChanges() {
                if (confirm('Save all team configuration changes?')) {
                    // Save logic here
                    alert('All changes saved successfully!');
                }
            }
            
            // Load initial data
            document.addEventListener('DOMContentLoaded', function() {
                // Load driver list, job zones, etc.
            });
        </script>
    </body>
    </html>
    ''')

def load_team_assignments():
    """Load team assignments from data files"""
    return {}

def load_pm_assignments():
    """Load PM assignment rules"""
    return {}

@team_admin_bp.route('/admin/teams/export')
def export_team_data():
    """Export team configuration data"""
    return jsonify({'status': 'success', 'message': 'Export functionality'})