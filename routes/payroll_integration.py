"""
Payroll Integration Module
Links timecard data with Excel payroll processing and quantity review
"""
from flask import Blueprint, render_template_string, request, jsonify
import pandas as pd
from datetime import datetime

payroll_bp = Blueprint('payroll_integration', __name__)

@payroll_bp.route('/payroll-review')
def payroll_dashboard():
    """Payroll review with timecard validation"""
    
    # Load timecard data for payroll processing
    tc_df = pd.read_excel('RAG-SEL TIMECARDS - APRIL 2025.xlsx')
    
    # Process payroll summary by employee
    payroll_summary = process_payroll_data(tc_df)
    
    # Get billing allocations for cross-reference
    billing_files = [
        'EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx'
    ]
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Payroll Integration - TRAXOVO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .page-header {
                background: white;
                padding: 2rem 0;
                margin-bottom: 2rem;
                border-bottom: 1px solid #dee2e6;
            }
            .payroll-card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
        </style>
    </head>
    <body>
        <div class="page-header">
            <div class="container">
                <h1 class="fw-bold mb-2">
                    <i class="fas fa-calculator me-2 text-primary"></i>Payroll Integration
                </h1>
                <p class="text-muted">Timecard validation and payroll processing</p>
            </div>
        </div>
        
        <div class="container">
            <!-- Payroll Summary -->
            <div class="row g-4 mb-4">
                <div class="col-lg-3">
                    <div class="payroll-card p-3 text-center">
                        <div class="fs-3 fw-bold text-primary">{{ payroll_summary.total_employees }}</div>
                        <div>Employees</div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="payroll-card p-3 text-center">
                        <div class="fs-3 fw-bold text-success">{{ "%.1f"|format(payroll_summary.total_hours) }}</div>
                        <div>Total Hours</div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="payroll-card p-3 text-center">
                        <div class="fs-3 fw-bold text-info">{{ payroll_summary.unique_jobs }}</div>
                        <div>Active Jobs</div>
                    </div>
                </div>
                <div class="col-lg-3">
                    <div class="payroll-card p-3 text-center">
                        <div class="fs-3 fw-bold text-warning">${{ "{:,.0f}"|format(payroll_summary.total_cost) }}</div>
                        <div>Labor Cost</div>
                    </div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="row">
                <div class="col-12">
                    <div class="payroll-card p-4">
                        <h4 class="mb-3">Payroll Actions</h4>
                        <div class="row g-3">
                            <div class="col-md-4">
                                <button class="btn btn-primary w-100">
                                    <i class="fas fa-file-excel me-2"></i>Export Payroll Excel
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-success w-100">
                                    <i class="fas fa-check-circle me-2"></i>Validate Timecards
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-info w-100">
                                    <i class="fas fa-chart-bar me-2"></i>Quantity Review
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', payroll_summary=payroll_summary)

def process_payroll_data(timecard_df):
    """Process timecard data for payroll summary"""
    
    # Calculate payroll metrics
    total_employees = timecard_df['sort_key_no'].nunique()
    total_hours = timecard_df['hours'].sum()
    unique_jobs = timecard_df['job_no'].nunique()
    
    # Estimate labor cost (placeholder calculation)
    avg_hourly_rate = 25  # Base rate estimation
    total_cost = total_hours * avg_hourly_rate
    
    return {
        'total_employees': total_employees,
        'total_hours': total_hours,
        'unique_jobs': unique_jobs,
        'total_cost': total_cost,
        'period': 'April 2025'
    }