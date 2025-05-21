"""
Billing Module Controller

This module provides routes and functionality for the Billing module,
including PM allocation reconciliation, invoice management, and monthly reporting.
"""

import os
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Import activity logger
from utils.activity_logger import (
    log_navigation, log_document_upload, log_report_export, 
    log_pm_process, log_invoice_generation, log_payment_record
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
billing_module_bp = Blueprint('billing_module', __name__, url_prefix='/billing')

# Constants
UPLOAD_FOLDER = os.path.join('uploads', 'billing_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXPORTS_FOLDER = os.path.join('exports', 'billing_reports')
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

RESULTS_FOLDER = os.path.join('reconcile', 'pm_results')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Helper functions
def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_sample_invoices():
    """
    Get sample invoice data for demonstration
    In a real application, this would fetch from the database
    """
    today = datetime.now()
    invoices = []
    
    # Generate 15 sample invoices with varied dates and statuses
    customers = ['Ragle Construction', 'WTX Construction', 'ESCO Services', 'Warren CAT']
    statuses = ['Paid', 'Partial', 'Unpaid']
    status_weights = [0.5, 0.2, 0.3]  # 50% paid, 20% partial, 30% unpaid
    
    for i in range(1, 16):
        invoice_date = today - timedelta(days=random.randint(0, 60))
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        amount = round(random.uniform(2000, 15000), 2)
        
        invoice = {
            'id': str(i),
            'invoice_number': f'INV-2025-{i:04d}',
            'job_number': f'JOB-{random.randint(1000, 9999)}',
            'date': invoice_date.strftime('%Y-%m-%d'),
            'customer': random.choice(customers),
            'amount': amount,
            'status': status
        }
        
        if status == 'Paid':
            payment_date = invoice_date + timedelta(days=random.randint(5, 30))
            invoice['payment_date'] = payment_date.strftime('%Y-%m-%d')
        elif status == 'Partial':
            payment_date = invoice_date + timedelta(days=random.randint(5, 30))
            invoice['payment_date'] = payment_date.strftime('%Y-%m-%d')
            invoice['paid_amount'] = round(amount * random.uniform(0.3, 0.7), 2)
        
        invoices.append(invoice)
    
    return invoices

def get_sample_allocation_files():
    """
    Get list of PM allocation files for demonstration
    In a real application, this would scan a directory or query a database
    """
    files = [
        {
            'id': '1',
            'filename': 'EQMO. BILLING ALLOCATIONS - APRIL 2025 (TR-FINAL REVISIONS BY 05.15.2025).xlsx',
            'date_uploaded': '2025-05-15',
            'uploaded_by': 'John Admin',
            'status': 'Final',
            'file_type': 'Original',
            'region': 'DFW'
        },
        {
            'id': '2',
            'filename': '2024-025 EQMO. BILLING ALLOCATIONS - APRIL 2025 2024-025 allocated AJR.xlsx',
            'date_uploaded': '2025-05-14',
            'uploaded_by': 'Sarah Manager',
            'status': 'Updated',
            'file_type': 'Modified',
            'region': 'DFW'
        },
        {
            'id': '3',
            'filename': 'WTX EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx',
            'date_uploaded': '2025-05-13',
            'uploaded_by': 'Michael Analyst',
            'status': 'Original',
            'file_type': 'Original',
            'region': 'WTX'
        },
        {
            'id': '4',
            'filename': 'L. MORALES EQMO. BILLING ALLOCATIONS - APRIL 2025.xlsx',
            'date_uploaded': '2025-05-12',
            'uploaded_by': 'Lisa Supervisor',
            'status': 'Updated',
            'file_type': 'Modified',
            'region': 'HOU'
        }
    ]
    
    return files

def get_sample_allocation_results():
    """
    Get sample PM allocation reconciliation results
    In a real application, this would be generated from actual file comparison
    """
    return {
        'summary': {
            'total_assets': 42,
            'changed_assets': 15,
            'increased_count': 8,
            'decreased_count': 5,
            'unchanged_count': 27,
            'total_original': 134567.89,
            'total_updated': 139852.43,
            'total_increase': 6284.54,
            'total_decrease': 1000.00,
            'total_difference': 5284.54
        },
        'allocations': [
            {
                'asset_id': 'ASST-001',
                'description': 'Caterpillar D6 Dozer',
                'original_amount': 3245.67,
                'updated_amount': 3500.00,
                'difference': 254.33,
                'percentage_change': 7.84,
                'status': 'increased'
            },
            {
                'asset_id': 'ASST-002',
                'description': 'John Deere 310SL Backhoe',
                'original_amount': 2987.50,
                'updated_amount': 2987.50,
                'difference': 0.00,
                'percentage_change': 0.00,
                'status': 'unchanged'
            },
            {
                'asset_id': 'ASST-003',
                'description': 'Komatsu PC210 Excavator',
                'original_amount': 4500.00,
                'updated_amount': 4800.00,
                'difference': 300.00,
                'percentage_change': 6.67,
                'status': 'increased'
            },
            {
                'asset_id': 'ASST-004',
                'description': 'Cat 140M Motor Grader',
                'original_amount': 5200.00,
                'updated_amount': 5000.00,
                'difference': -200.00,
                'percentage_change': -3.85,
                'status': 'decreased'
            },
            {
                'asset_id': 'ASST-005',
                'description': 'Volvo A30F Articulated Hauler',
                'original_amount': 4750.00,
                'updated_amount': 5230.00,
                'difference': 480.00,
                'percentage_change': 10.11,
                'status': 'increased'
            },
            {
                'asset_id': 'ASST-006',
                'description': 'Bobcat S650 Skid Steer',
                'original_amount': 1800.00,
                'updated_amount': 1800.00,
                'difference': 0.00,
                'percentage_change': 0.00,
                'status': 'unchanged'
            },
            {
                'asset_id': 'ASST-007',
                'description': 'Case 580SN Backhoe Loader',
                'original_amount': 2700.00,
                'updated_amount': 2900.00,
                'difference': 200.00,
                'percentage_change': 7.41,
                'status': 'increased'
            },
            {
                'asset_id': 'ASST-008',
                'description': 'Wacker Neuson EZ38 Excavator',
                'original_amount': 3100.00,
                'updated_amount': 3100.00,
                'difference': 0.00,
                'percentage_change': 0.00,
                'status': 'unchanged'
            },
            {
                'asset_id': 'ASST-009',
                'description': 'Caterpillar 950M Wheel Loader',
                'original_amount': 4200.00,
                'updated_amount': 4000.00,
                'difference': -200.00,
                'percentage_change': -4.76,
                'status': 'decreased'
            },
            {
                'asset_id': 'ASST-010',
                'description': 'JLG 1055 Telehandler',
                'original_amount': 3800.00,
                'updated_amount': 4000.00,
                'difference': 200.00,
                'percentage_change': 5.26,
                'status': 'increased'
            },
            {
                'asset_id': 'ASST-011',
                'description': 'Multiquip MQ WhisperWatt Generator',
                'original_amount': 0.00,
                'updated_amount': 1500.00,
                'difference': 1500.00,
                'percentage_change': 100.00,
                'status': 'added'
            },
            {
                'asset_id': 'ASST-012',
                'description': 'Ingersoll Rand Air Compressor',
                'original_amount': 1200.00,
                'updated_amount': 0.00,
                'difference': -1200.00,
                'percentage_change': -100.00,
                'status': 'removed'
            }
        ]
    }

def get_sample_monthly_report():
    """
    Get sample monthly billing report data
    In a real application, this would be calculated from actual invoice and billing records
    """
    today = datetime.now()
    current_month = today.strftime('%B %Y')
    previous_month = (today.replace(day=1) - timedelta(days=1)).strftime('%B %Y')
    
    return {
        'current_month': current_month,
        'previous_month': previous_month,
        'total_invoiced': 142850.75,
        'total_paid': 98500.25,
        'total_outstanding': 44350.50,
        'payment_rate': 69.0,
        'average_days_to_payment': 23,
        'regions': [
            {
                'id': 'DFW',
                'name': 'Dallas-Fort Worth',
                'invoiced': 65420.50,
                'paid': 48750.25,
                'outstanding': 16670.25,
                'payment_rate': 74.5
            },
            {
                'id': 'HOU',
                'name': 'Houston',
                'invoiced': 52130.25,
                'paid': 35500.00,
                'outstanding': 16630.25,
                'payment_rate': 68.1
            },
            {
                'id': 'WTX',
                'name': 'West Texas',
                'invoiced': 25300.00,
                'paid': 14250.00,
                'outstanding': 11050.00,
                'payment_rate': 56.3
            }
        ],
        'customers': [
            {
                'id': '1',
                'name': 'Ragle Construction',
                'invoiced': 58420.25,
                'paid': 45750.25,
                'outstanding': 12670.00,
                'payment_rate': 78.3
            },
            {
                'id': '2',
                'name': 'WTX Construction',
                'invoiced': 32130.50,
                'paid': 22500.00,
                'outstanding': 9630.50,
                'payment_rate': 70.0
            },
            {
                'id': '3',
                'name': 'ESCO Services',
                'invoiced': 28300.00,
                'paid': 15250.00,
                'outstanding': 13050.00,
                'payment_rate': 53.9
            },
            {
                'id': '4',
                'name': 'Warren CAT',
                'invoiced': 24000.00,
                'paid': 15000.00,
                'outstanding': 9000.00,
                'payment_rate': 62.5
            }
        ],
        'monthly_trends': {
            'months': ['January', 'February', 'March', 'April', 'May'],
            'invoiced': [121500.50, 135420.75, 128930.25, 138250.50, 142850.75],
            'paid': [115425.50, 120420.75, 115930.25, 110250.50, 98500.25],
            'payment_rates': [95.0, 88.9, 89.9, 79.7, 69.0]
        }
    }

# Routes
@billing_module_bp.route('/')
@login_required
def index():
    """Billing module home page with dashboard"""
    log_navigation('billing_module.index')
    
    # Get summary data
    invoices = get_sample_invoices()
    allocation_files = get_sample_allocation_files()
    monthly_report = get_sample_monthly_report()
    
    return render_template('billing/index.html',
                          invoices=invoices[:5],  # Show only 5 recent invoices
                          allocation_files=allocation_files[:3],  # Show only 3 recent files
                          monthly_report=monthly_report)

@billing_module_bp.route('/invoices')
@login_required
def invoices():
    """List all invoices with filtering options"""
    log_navigation('billing_module.invoices')
    
    invoices = get_sample_invoices()
    
    # Handle filtering (in a real application)
    status = request.args.get('status')
    customer = request.args.get('customer')
    date_range = request.args.get('date_range')
    search = request.args.get('search', '').lower()
    
    # Apply filters (simplified for demonstration)
    if status:
        invoices = [i for i in invoices if i['status'] == status]
    
    if customer:
        invoices = [i for i in invoices if i['customer'] == customer]
    
    if search:
        invoices = [i for i in invoices if 
                   search in i['invoice_number'].lower() or 
                   search in i['job_number'].lower()]
    
    return render_template('billing/invoices.html', invoices=invoices)

@billing_module_bp.route('/invoice_detail/<invoice_id>')
@login_required
def invoice_detail(invoice_id):
    """Show invoice details and payment history"""
    log_navigation(f'billing_module.invoice_detail.{invoice_id}')
    
    # Find invoice in our sample data
    invoices = get_sample_invoices()
    invoice = next((i for i in invoices if i['id'] == invoice_id), None)
    
    if not invoice:
        flash('Invoice not found', 'danger')
        return redirect(url_for('billing_module.invoices'))
    
    # Generate payment history for this invoice
    payment_history = []
    
    if invoice['status'] in ['Paid', 'Partial']:
        # Add at least one payment
        payment_date = datetime.strptime(invoice.get('payment_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d')
        
        if invoice['status'] == 'Paid':
            payment_history.append({
                'id': f'PMT-{random.randint(1000, 9999)}',
                'date': payment_date.strftime('%Y-%m-%d'),
                'amount': invoice['amount'],
                'method': random.choice(['Check', 'ACH Transfer', 'Wire Transfer']),
                'reference': f'REF-{random.randint(10000, 99999)}',
                'notes': 'Payment received in full'
            })
        else:  # Partial
            paid_amount = invoice.get('paid_amount', round(invoice['amount'] * 0.5, 2))
            payment_history.append({
                'id': f'PMT-{random.randint(1000, 9999)}',
                'date': payment_date.strftime('%Y-%m-%d'),
                'amount': paid_amount,
                'method': random.choice(['Check', 'ACH Transfer', 'Wire Transfer']),
                'reference': f'REF-{random.randint(10000, 99999)}',
                'notes': 'Partial payment received'
            })
    
    return render_template('billing/invoice_detail.html', 
                          invoice=invoice,
                          payment_history=payment_history)

@billing_module_bp.route('/generate_invoice', methods=['GET', 'POST'])
@login_required
def generate_invoice():
    """Generate a new invoice"""
    log_navigation('billing_module.generate_invoice')
    
    if request.method == 'POST':
        # In a real application, this would create an actual invoice
        invoice_number = request.form.get('invoice_number')
        job_number = request.form.get('job_number')
        customer = request.form.get('customer')
        amount = float(request.form.get('amount', 0))
        date = request.form.get('date')
        
        # Log invoice generation
        log_invoice_generation(
            invoice_number=invoice_number,
            job_number=job_number,
            amount=amount
        )
        
        flash(f'Invoice {invoice_number} generated successfully', 'success')
        return redirect(url_for('billing_module.invoices'))
    
    # Generate a new invoice number
    next_invoice_number = f'INV-2025-{len(get_sample_invoices()) + 1:04d}'
    
    return render_template('billing/generate_invoice.html',
                          next_invoice_number=next_invoice_number,
                          today=datetime.now().strftime('%Y-%m-%d'))

@billing_module_bp.route('/record_payment', methods=['POST'])
@login_required
def record_payment():
    """Record a payment for an invoice"""
    # In a real application, this would update the database
    data = request.json
    
    invoice_id = data.get('invoice_id')
    payment_amount = float(data.get('payment_amount', 0))
    payment_method = data.get('payment_method')
    
    # Log payment record
    log_payment_record(
        invoice_id=invoice_id,
        payment_amount=payment_amount,
        payment_method=payment_method
    )
    
    # Return success response
    return jsonify({
        'success': True,
        'message': f'Payment of ${payment_amount:.2f} recorded successfully'
    })

@billing_module_bp.route('/pm_allocation')
@login_required
def pm_allocation():
    """List all PM allocation files"""
    log_navigation('billing_module.pm_allocation')
    
    allocation_files = get_sample_allocation_files()
    
    return render_template('billing/pm_allocation.html', 
                          allocation_files=allocation_files)

@billing_module_bp.route('/pm_allocation_upload', methods=['GET', 'POST'])
@login_required
def pm_allocation_upload():
    """Upload PM allocation files"""
    log_navigation('billing_module.pm_allocation_upload')
    
    if request.method == 'POST':
        if 'original_file' not in request.files or 'updated_file' not in request.files:
            flash('Both original and updated files are required', 'danger')
            return redirect(request.url)
        
        original_file = request.files['original_file']
        updated_file = request.files['updated_file']
        
        if original_file.filename == '' or updated_file.filename == '':
            flash('Both original and updated files are required', 'danger')
            return redirect(request.url)
        
        if (allowed_file(original_file.filename) and 
            allowed_file(updated_file.filename)):
            
            # Save files
            original_filename = secure_filename(original_file.filename)
            updated_filename = secure_filename(updated_file.filename)
            
            original_path = os.path.join(UPLOAD_FOLDER, original_filename)
            updated_path = os.path.join(UPLOAD_FOLDER, updated_filename)
            
            original_file.save(original_path)
            updated_file.save(updated_path)
            
            # Log upload
            log_document_upload(
                filename=original_filename,
                file_type='original_allocation',
                file_size=os.path.getsize(original_path)
            )
            
            log_document_upload(
                filename=updated_filename,
                file_type='updated_allocation',
                file_size=os.path.getsize(updated_path)
            )
            
            # Process files (in a real application, this would analyze the actual files)
            # For demonstration, we'll use sample data
            results = get_sample_allocation_results()
            
            # Save results to a file
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            results_filename = f'pm_allocation_results_{timestamp}.json'
            results_path = os.path.join(RESULTS_FOLDER, results_filename)
            
            with open(results_path, 'w') as f:
                json.dump(results, f)
            
            # Log PM processing
            log_pm_process(
                original_file=original_filename,
                updated_file=updated_filename,
                changes_count=results['summary']['changed_assets']
            )
            
            return redirect(url_for('billing_module.pm_allocation_results', 
                                   results_file=results_filename))
        else:
            flash(f'File type not allowed. Please upload {", ".join(ALLOWED_EXTENSIONS)} files.', 'danger')
    
    return render_template('billing/pm_allocation_upload.html')

@billing_module_bp.route('/pm_allocation_results')
@login_required
def pm_allocation_results():
    """Show PM allocation comparison results"""
    log_navigation('billing_module.pm_allocation_results')
    
    results_file = request.args.get('results_file')
    
    if not results_file:
        flash('No results file specified', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))
    
    results_path = os.path.join(RESULTS_FOLDER, results_file)
    
    if not os.path.exists(results_path):
        flash('Results file not found', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))
    
    # Load results from file
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
    except Exception as e:
        flash(f'Error loading results: {str(e)}', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))
    
    return render_template('billing/pm_allocation_results.html', 
                          results=results,
                          results_file=results_file)

@billing_module_bp.route('/pm_allocation_export')
@login_required
def pm_allocation_export():
    """Export PM allocation comparison results"""
    results_file = request.args.get('results_file')
    export_format = request.args.get('format', 'xlsx')
    
    if not results_file:
        flash('No results file specified', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))
    
    results_path = os.path.join(RESULTS_FOLDER, results_file)
    
    if not os.path.exists(results_path):
        flash('Results file not found', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))
    
    # Generate export filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    export_filename = f'pm_allocation_export_{timestamp}.{export_format}'
    export_path = os.path.join(EXPORTS_FOLDER, export_filename)
    
    # In a real application, this would generate a proper Excel or CSV file
    # For demonstration, we'll create a simple text file
    with open(export_path, 'w') as f:
        f.write(f"PM Allocation Export ({export_format})\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("This is a placeholder for the actual export content.")
    
    # Log export
    log_report_export(
        report_type='pm_allocation',
        export_format=export_format
    )
    
    return send_file(export_path, as_attachment=True, download_name=export_filename)

@billing_module_bp.route('/monthly_report')
@login_required
def monthly_report():
    """Show monthly billing report"""
    log_navigation('billing_module.monthly_report')
    
    report_data = get_sample_monthly_report()
    
    return render_template('billing/monthly_report.html', report=report_data)

@billing_module_bp.route('/export_monthly_report')
@login_required
def export_monthly_report():
    """Export monthly report"""
    export_format = request.args.get('format', 'xlsx')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    # Generate export filename
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    export_filename = f'monthly_billing_report_{month}_{timestamp}.{export_format}'
    export_path = os.path.join(EXPORTS_FOLDER, export_filename)
    
    # In a real application, this would generate a proper report file
    # For demonstration, we'll create a simple text file
    with open(export_path, 'w') as f:
        f.write(f"Monthly Billing Report - {month} ({export_format})\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("This is a placeholder for the actual report content.")
    
    # Log export
    log_report_export(
        report_type='monthly_billing',
        export_format=export_format
    )
    
    return send_file(export_path, as_attachment=True, download_name=export_filename)

# API endpoints for AJAX requests
@billing_module_bp.route('/api/invoice_status_chart')
@login_required
def invoice_status_chart():
    """Get invoice status data for charts"""
    invoices = get_sample_invoices()
    
    # Count invoices by status
    status_counts = {'Paid': 0, 'Partial': 0, 'Unpaid': 0}
    
    for invoice in invoices:
        status_counts[invoice['status']] += 1
    
    # Calculate totals by status
    status_totals = {'Paid': 0, 'Partial': 0, 'Unpaid': 0}
    
    for invoice in invoices:
        if invoice['status'] == 'Paid':
            status_totals['Paid'] += invoice['amount']
        elif invoice['status'] == 'Partial':
            status_totals['Partial'] += invoice['amount']
        else:
            status_totals['Unpaid'] += invoice['amount']
    
    return jsonify({
        'status_counts': status_counts,
        'status_totals': status_totals
    })

@billing_module_bp.route('/api/monthly_trends')
@login_required
def monthly_trends():
    """Get monthly trends data for charts"""
    report = get_sample_monthly_report()
    
    return jsonify(report['monthly_trends'])
@billing_module_bp.route('/')
def index():
    """Handler for /"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/index.html')
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/invoices')
def invoices():
    """Handler for /invoices"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/invoices.html')
    except Exception as e:
        logger.error(f"Error in invoices: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/invoice_detail/<invoice_id>')
def invoice_detail(invoice_id):
    """Handler for /invoice_detail/<invoice_id>"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/invoice_detail.html', invoice_id=invoice_id)
    except Exception as e:
        logger.error(f"Error in invoice_detail: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/generate_invoice')
def generate_invoice():
    """Handler for /generate_invoice"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/generate_invoice.html')
    except Exception as e:
        logger.error(f"Error in generate_invoice: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/record_payment')
def record_payment():
    """Handler for /record_payment"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/record_payment.html')
    except Exception as e:
        logger.error(f"Error in record_payment: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/pm_allocation')
def pm_allocation():
    """Handler for /pm_allocation"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/pm_allocation.html')
    except Exception as e:
        logger.error(f"Error in pm_allocation: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/pm_allocation_upload')
def pm_allocation_upload():
    """Handler for /pm_allocation_upload"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/pm_allocation_upload.html')
    except Exception as e:
        logger.error(f"Error in pm_allocation_upload: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/pm_allocation_results')
def pm_allocation_results():
    """Handler for /pm_allocation_results"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/pm_allocation_results.html')
    except Exception as e:
        logger.error(f"Error in pm_allocation_results: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/pm_allocation_export')
def pm_allocation_export():
    """Handler for /pm_allocation_export"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/pm_allocation_export.html')
    except Exception as e:
        logger.error(f"Error in pm_allocation_export: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/monthly_report')
def monthly_report():
    """Handler for /monthly_report"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/monthly_report.html')
    except Exception as e:
        logger.error(f"Error in monthly_report: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/export_monthly_report')
def export_monthly_report():
    """Handler for /export_monthly_report"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/export_monthly_report.html')
    except Exception as e:
        logger.error(f"Error in export_monthly_report: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/api/invoice_status_chart')
def api_invoice_status_chart():
    """Handler for /api/invoice_status_chart"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/api_invoice_status_chart.html')
    except Exception as e:
        logger.error(f"Error in api_invoice_status_chart: {e}")
        return render_template('error.html', error=str(e)), 500

@billing_module_bp.route('/api/monthly_trends')
def api_monthly_trends():
    """Handler for /api/monthly_trends"""
    try:
        # Add your route handler logic here
        return render_template('billing_module/api_monthly_trends.html')
    except Exception as e:
        logger.error(f"Error in api_monthly_trends: {e}")
        return render_template('error.html', error=str(e)), 500
