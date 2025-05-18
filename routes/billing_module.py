"""
Billing Module Blueprint

This module handles all billing-related functionality including:
- PM allocation reconciliation
- Monthly billing reports
- Invoice generation
- Payment tracking
"""

import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import re

from flask import (Blueprint, current_app, flash, jsonify, redirect,
                  render_template, request, send_from_directory, url_for, session)
from flask_login import current_user, login_required
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize blueprint
billing_module_bp = Blueprint('billing_module', __name__, url_prefix='/billing')

# Ensure data directories exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
BILLING_DATA_DIR = DATA_DIR / "billing"
BILLING_DATA_DIR.mkdir(exist_ok=True)
INVOICE_DIR = Path("exports") / "invoices"
INVOICE_DIR.mkdir(exist_ok=True, parents=True)

# Sample data for demonstration
def get_sample_pm_allocations():
    """Get sample PM allocation data for demonstration"""
    return [
        {
            "id": 1,
            "asset_id": "EQ1001",
            "description": "CAT 320 Excavator",
            "department": "Construction",
            "original_amount": 2500.00,
            "updated_amount": 2750.00,
            "difference": 250.00,
            "percentage_change": 10.0,
            "job_number": "2024-025",
            "month": "April 2025",
            "notes": "Additional parts required"
        },
        {
            "id": 2,
            "asset_id": "EQ1002",
            "description": "John Deere Loader",
            "department": "Construction",
            "original_amount": 1800.00,
            "updated_amount": 1800.00,
            "difference": 0.00,
            "percentage_change": 0.0,
            "job_number": "2024-019",
            "month": "April 2025",
            "notes": ""
        },
        {
            "id": 3,
            "asset_id": "EQ1003",
            "description": "Komatsu Dozer",
            "department": "Construction",
            "original_amount": 3200.00,
            "updated_amount": 2950.00,
            "difference": -250.00,
            "percentage_change": -7.8,
            "job_number": "2024-030",
            "month": "April 2025",
            "notes": "Reduced service scope"
        },
        {
            "id": 4,
            "asset_id": "EQ1004",
            "description": "Ford F350",
            "department": "Transportation",
            "original_amount": 850.00,
            "updated_amount": 920.00,
            "difference": 70.00,
            "percentage_change": 8.2,
            "job_number": "2023-034",
            "month": "April 2025",
            "notes": "Additional labor"
        },
        {
            "id": 5,
            "asset_id": "EQ1005",
            "description": "Bobcat Skid Steer",
            "department": "Construction",
            "original_amount": 1200.00,
            "updated_amount": 1200.00,
            "difference": 0.00,
            "percentage_change": 0.0,
            "job_number": "2023-032",
            "month": "April 2025",
            "notes": ""
        }
    ]

def get_sample_invoices():
    """Get sample invoice data for demonstration"""
    return [
        {
            "id": 1001,
            "invoice_number": "INV-25-0428",
            "job_number": "2024-025",
            "date": "2025-04-28",
            "customer": "Ragle Construction",
            "amount": 10450.00,
            "status": "Paid",
            "payment_date": "2025-05-15",
            "payment_method": "ACH Transfer",
            "payment_reference": "ACH-78901",
            "notes": ""
        },
        {
            "id": 1002,
            "invoice_number": "INV-25-0429",
            "job_number": "2024-019",
            "date": "2025-04-28",
            "customer": "WTX Construction",
            "amount": 7850.00,
            "status": "Unpaid",
            "payment_date": None,
            "payment_method": None,
            "payment_reference": None,
            "notes": "Due date: 2025-05-28"
        },
        {
            "id": 1003,
            "invoice_number": "INV-25-0430",
            "job_number": "2024-030",
            "date": "2025-04-28",
            "customer": "Ragle Construction",
            "amount": 5670.00,
            "status": "Partial",
            "payment_date": "2025-05-10",
            "payment_method": "Check",
            "payment_reference": "Check #4567",
            "notes": "Balance due: $2,000.00"
        },
        {
            "id": 1004,
            "invoice_number": "INV-25-0431",
            "job_number": "2023-034",
            "date": "2025-04-29",
            "customer": "ESCO Services",
            "amount": 3240.00,
            "status": "Paid",
            "payment_date": "2025-05-12",
            "payment_method": "Credit Card",
            "payment_reference": "VISA-5678",
            "notes": ""
        },
        {
            "id": 1005,
            "invoice_number": "INV-25-0432",
            "job_number": "2023-032",
            "date": "2025-04-29",
            "customer": "Warren CAT",
            "amount": 9120.00,
            "status": "Unpaid",
            "payment_date": None,
            "payment_method": None,
            "payment_reference": None,
            "notes": "Due date: 2025-05-29"
        }
    ]

def get_monthly_summary():
    """Get monthly billing summary data"""
    return {
        "total_invoiced": 36330.00,
        "total_paid": 15690.00,
        "total_due": 20640.00,
        "invoice_count": 5,
        "paid_count": 2,
        "partial_count": 1,
        "unpaid_count": 2,
        "by_customer": [
            {"customer": "Ragle Construction", "amount": 16120.00, "paid": 9670.00, "due": 6450.00},
            {"customer": "WTX Construction", "amount": 7850.00, "paid": 0.00, "due": 7850.00},
            {"customer": "ESCO Services", "amount": 3240.00, "paid": 3240.00, "due": 0.00},
            {"customer": "Warren CAT", "amount": 9120.00, "paid": 0.00, "due": 9120.00}
        ],
        "by_job": [
            {"job_number": "2024-025", "amount": 10450.00, "paid": 10450.00, "due": 0.00},
            {"job_number": "2024-019", "amount": 7850.00, "paid": 0.00, "due": 7850.00},
            {"job_number": "2024-030", "amount": 5670.00, "paid": 3670.00, "due": 2000.00},
            {"job_number": "2023-034", "amount": 3240.00, "paid": 3240.00, "due": 0.00},
            {"job_number": "2023-032", "amount": 9120.00, "paid": 0.00, "due": 9120.00}
        ]
    }

def process_pm_allocation_file(file_path, original=True):
    """
    Process PM allocation file and extract relevant data
    
    Args:
        file_path (str): Path to the Excel file
        original (bool): Whether this is the original or updated file
        
    Returns:
        dict: Extracted data with asset IDs as keys
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Basic validation - check for required columns
        required_cols = ["Asset ID", "Description", "Amount"]
        for col in required_cols:
            if col not in df.columns:
                # Try to find columns with similar names
                for actual_col in df.columns:
                    if col.lower() in actual_col.lower():
                        # Rename the column
                        df.rename(columns={actual_col: col}, inplace=True)
                        break
                else:
                    # Column not found
                    logger.error(f"Required column '{col}' not found in file: {file_path}")
                    return None
        
        # Extract data
        result = {}
        for _, row in df.iterrows():
            asset_id = str(row["Asset ID"]).strip()
            if not asset_id or pd.isna(asset_id):
                continue
                
            # Get amount, ensuring it's a float
            amount = row["Amount"]
            if isinstance(amount, str):
                # Remove currency symbols and commas
                amount = re.sub(r'[^\d.-]', '', amount)
                amount = float(amount)
            
            result[asset_id] = {
                "asset_id": asset_id,
                "description": str(row["Description"]).strip(),
                "amount": float(amount),
                "file_type": "original" if original else "updated"
            }
            
        return result
    except Exception as e:
        logger.error(f"Error processing PM allocation file: {e}")
        return None

def compare_allocation_files(original_file, updated_file):
    """
    Compare original and updated PM allocation files
    
    Args:
        original_file (str): Path to the original file
        updated_file (str): Path to the updated file
        
    Returns:
        dict: Comparison results
    """
    # Process files
    original_data = process_pm_allocation_file(original_file, original=True)
    updated_data = process_pm_allocation_file(updated_file, original=False)
    
    if not original_data or not updated_data:
        return None
    
    # Compare data
    results = {
        "allocations": [],
        "summary": {
            "total_assets": 0,
            "changed_assets": 0,
            "increased_count": 0,
            "decreased_count": 0,
            "unchanged_count": 0,
            "total_original": 0.0,
            "total_updated": 0.0,
            "total_difference": 0.0,
            "total_increase": 0.0,
            "total_decrease": 0.0
        }
    }
    
    # Process all assets from both files
    all_assets = set(original_data.keys()) | set(updated_data.keys())
    
    for asset_id in all_assets:
        original_info = original_data.get(asset_id, {"amount": 0.0})
        updated_info = updated_data.get(asset_id, {"amount": 0.0})
        
        original_amount = original_info.get("amount", 0.0)
        updated_amount = updated_info.get("amount", 0.0)
        difference = updated_amount - original_amount
        
        if original_amount > 0:
            percentage_change = (difference / original_amount) * 100
        else:
            percentage_change = 0.0 if difference == 0 else 100.0
        
        allocation = {
            "asset_id": asset_id,
            "description": updated_info.get("description") or original_info.get("description", ""),
            "original_amount": original_amount,
            "updated_amount": updated_amount,
            "difference": difference,
            "percentage_change": percentage_change,
            "status": "added" if asset_id not in original_data else ("removed" if asset_id not in updated_data else 
                     "unchanged" if difference == 0 else "increased" if difference > 0 else "decreased")
        }
        
        results["allocations"].append(allocation)
        
        # Update summary
        results["summary"]["total_assets"] += 1
        results["summary"]["total_original"] += original_amount
        results["summary"]["total_updated"] += updated_amount
        results["summary"]["total_difference"] += difference
        
        if difference > 0:
            results["summary"]["increased_count"] += 1
            results["summary"]["total_increase"] += difference
            results["summary"]["changed_assets"] += 1
        elif difference < 0:
            results["summary"]["decreased_count"] += 1
            results["summary"]["total_decrease"] += abs(difference)
            results["summary"]["changed_assets"] += 1
        else:
            results["summary"]["unchanged_count"] += 1
    
    # Sort allocations by difference (largest absolute difference first)
    results["allocations"].sort(key=lambda x: abs(x["difference"]), reverse=True)
    
    return results

# Routes
@billing_module_bp.route('/')
@login_required
def index():
    """Billing module home page"""
    monthly_summary = get_monthly_summary()
    return render_template('billing/index.html', summary=monthly_summary)

@billing_module_bp.route('/pm_allocation')
@login_required
def pm_allocation():
    """PM allocation page"""
    allocations = get_sample_pm_allocations()
    return render_template('billing/pm_allocation.html', allocations=allocations)

@billing_module_bp.route('/pm_allocation/upload', methods=['GET', 'POST'])
@login_required
def pm_allocation_upload():
    """Handle PM allocation file upload and processing"""
    if request.method == 'POST':
        # Check if the post request has the file parts
        if 'original_file' not in request.files or 'updated_file' not in request.files:
            flash('Both original and updated files are required', 'danger')
            return redirect(request.url)
        
        original_file = request.files['original_file']
        updated_file = request.files['updated_file']
        
        # If the user does not select a file, the browser submits an empty file without a filename
        if original_file.filename == '' or updated_file.filename == '':
            flash('Both original and updated files are required', 'danger')
            return redirect(request.url)
        
        # Check file extensions
        allowed_extensions = {'xlsx', 'xls'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
        
        if not allowed_file(original_file.filename) or not allowed_file(updated_file.filename):
            flash('Only Excel files (.xlsx, .xls) are allowed', 'danger')
            return redirect(request.url)
        
        try:
            # Create upload directory if it doesn't exist
            upload_dir = Path('uploads')
            upload_dir.mkdir(exist_ok=True)
            
            # Save the uploaded files
            original_path = upload_dir / f"original_{original_file.filename}"
            updated_path = upload_dir / f"updated_{updated_file.filename}"
            
            original_file.save(original_path)
            updated_file.save(updated_path)
            
            # Process the files
            results = compare_allocation_files(original_path, updated_path)
            
            if not results:
                flash('Error processing the files. Please check the format and try again.', 'danger')
                return redirect(request.url)
            
            # Save results
            results_file = f"pm_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path = BILLING_DATA_DIR / results_file
            
            with open(results_path, 'w') as f:
                json.dump(results, f)
            
            # Log activity
            try:
                from utils.activity_logger import log_pm_process
                log_pm_process(
                    original_file=original_file.filename,
                    updated_file=updated_file.filename,
                    changes_count=results["summary"]["changed_assets"],
                    success=True
                )
            except ImportError:
                # Activity logger not available
                pass
            
            # Redirect to results page
            return redirect(url_for('billing_module.pm_allocation_results', results_file=results_file))
        
        except Exception as e:
            flash(f'Error processing files: {str(e)}', 'danger')
            
            # Log error
            try:
                from utils.activity_logger import log_pm_process
                log_pm_process(
                    original_file=original_file.filename,
                    updated_file=updated_file.filename,
                    success=False,
                    error=str(e)
                )
            except ImportError:
                # Activity logger not available
                pass
            
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('billing/pm_allocation_upload.html')

@billing_module_bp.route('/pm_allocation/results/<results_file>')
@login_required
def pm_allocation_results(results_file):
    """Display PM allocation comparison results"""
    try:
        results_path = BILLING_DATA_DIR / results_file
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        return render_template('billing/pm_allocation_results.html', 
                              results=results,
                              results_file=results_file)
    except Exception as e:
        flash(f'Error reading results file: {str(e)}', 'danger')
        return redirect(url_for('billing_module.pm_allocation'))

@billing_module_bp.route('/pm_allocation/export/<results_file>')
@login_required
def pm_allocation_export(results_file):
    """Export PM allocation results as CSV or Excel"""
    try:
        results_path = BILLING_DATA_DIR / results_file
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Get export format
        export_format = request.args.get('format', 'xlsx')
        
        # Create DataFrame from results
        df = pd.DataFrame(results["allocations"])
        
        # Format the columns
        df = df[["asset_id", "description", "original_amount", "updated_amount", 
                "difference", "percentage_change", "status"]]
        
        # Create export directory if it doesn't exist
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        
        # Generate export filename
        export_filename = f"pm_allocation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if export_format == 'xlsx':
            export_path = export_dir / f"{export_filename}.xlsx"
            df.to_excel(export_path, index=False, sheet_name="PM Allocation")
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:  # CSV
            export_path = export_dir / f"{export_filename}.csv"
            df.to_csv(export_path, index=False)
            mimetype = 'text/csv'
        
        # Log activity
        try:
            from utils.activity_logger import log_report_export
            log_report_export(report_type="pm_allocation", export_format=export_format)
        except ImportError:
            # Activity logger not available
            pass
        
        # Send file
        return send_from_directory(export_dir, export_path.name, mimetype=mimetype, as_attachment=True)
    
    except Exception as e:
        flash(f'Error exporting results: {str(e)}', 'danger')
        return redirect(url_for('billing_module.pm_allocation_results', results_file=results_file))

@billing_module_bp.route('/invoices')
@login_required
def invoices():
    """Invoices list page"""
    invoices_data = get_sample_invoices()
    return render_template('billing/invoices.html', invoices=invoices_data)

@billing_module_bp.route('/invoices/<invoice_id>')
@login_required
def invoice_detail(invoice_id):
    """Invoice detail page"""
    invoices_data = get_sample_invoices()
    
    # Find invoice by ID
    invoice = next((inv for inv in invoices_data if str(inv["id"]) == str(invoice_id)), None)
    
    if not invoice:
        flash('Invoice not found', 'danger')
        return redirect(url_for('billing_module.invoices'))
    
    # Get PM allocations for this invoice's job number
    allocations = get_sample_pm_allocations()
    job_allocations = [a for a in allocations if a["job_number"] == invoice["job_number"]]
    
    return render_template('billing/invoice_detail.html', 
                          invoice=invoice,
                          allocations=job_allocations)

@billing_module_bp.route('/invoices/generate', methods=['GET', 'POST'])
@login_required
def generate_invoice():
    """Generate a new invoice"""
    if request.method == 'POST':
        # Process form submission
        job_number = request.form.get('job_number')
        customer = request.form.get('customer')
        invoice_date = request.form.get('invoice_date')
        amount = request.form.get('amount')
        
        # Validate form data
        if not job_number or not customer or not invoice_date or not amount:
            flash('All fields are required', 'danger')
            return redirect(request.url)
        
        try:
            # Generate invoice number
            invoice_number = f"INV-25-{(len(get_sample_invoices()) + 1):04d}"
            
            # In a real implementation, this would create an invoice record
            # For demonstration, we'll just simulate success
            
            # Log activity
            try:
                from utils.activity_logger import log_invoice_generation
                log_invoice_generation(
                    invoice_number=invoice_number,
                    job_number=job_number,
                    amount=amount,
                    success=True
                )
            except (ImportError, NameError):
                # Activity logger not available
                pass
            
            flash(f'Invoice {invoice_number} generated successfully', 'success')
            return redirect(url_for('billing_module.invoices'))
        
        except Exception as e:
            flash(f'Error generating invoice: {str(e)}', 'danger')
            return redirect(request.url)
    
    # GET request - show form
    return render_template('billing/generate_invoice.html')

@billing_module_bp.route('/invoices/record_payment', methods=['POST'])
@login_required
def record_payment():
    """Record a payment for an invoice"""
    invoice_id = request.form.get('invoice_id')
    payment_amount = request.form.get('payment_amount')
    payment_method = request.form.get('payment_method')
    payment_reference = request.form.get('payment_reference')
    
    # Validate form data
    if not invoice_id or not payment_amount or not payment_method:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400
    
    # In a real implementation, this would update the invoice record
    # For demonstration, we'll just simulate success
    
    # Log activity
    try:
        from utils.activity_logger import log_payment_record
        log_payment_record(
            invoice_id=invoice_id,
            payment_amount=payment_amount,
            payment_method=payment_method,
            success=True
        )
    except (ImportError, NameError):
        # Activity logger not available
        pass
    
    return jsonify({
        "success": True,
        "message": "Payment recorded successfully"
    })

@billing_module_bp.route('/monthly_report')
@login_required
def monthly_report():
    """Monthly billing report page"""
    summary = get_monthly_summary()
    invoices_data = get_sample_invoices()
    
    # Get month parameter or use current month
    month = request.args.get('month')
    if not month:
        month = datetime.now().strftime("%B %Y")
    
    return render_template('billing/monthly_report.html', 
                          summary=summary,
                          invoices=invoices_data,
                          month=month)

@billing_module_bp.route('/export_monthly_report')
@login_required
def export_monthly_report():
    """Export monthly billing report"""
    # Get export format
    export_format = request.args.get('format', 'pdf')
    
    # Get month parameter or use current month
    month = request.args.get('month')
    if not month:
        month = datetime.now().strftime("%B %Y")
    
    # Generate filename based on month
    filename = f"billing_report_{month.replace(' ', '_')}"
    
    try:
        # Log activity
        try:
            from utils.activity_logger import log_report_export
            log_report_export(report_type="monthly_billing", export_format=export_format)
        except ImportError:
            # Activity logger not available
            pass
        
        if export_format == 'pdf':
            # Generate PDF report
            from utils.report_generator import generate_pdf_report
            
            # Get data
            summary = get_monthly_summary()
            invoices = get_sample_invoices()
            
            # Format data for report
            data = {
                "summary": summary,
                "invoices": invoices,
                "month": month
            }
            
            # Generate report
            report_path, preview_path = generate_pdf_report(
                report_type="monthly_billing",
                data=data,
                title=f"Monthly Billing Report - {month}"
            )
            
            # Return PDF
            return send_from_directory(os.path.dirname(report_path), os.path.basename(report_path))
        
        elif export_format == 'xlsx':
            # Generate Excel report
            export_dir = Path('exports')
            export_dir.mkdir(exist_ok=True)
            
            # Create Excel file
            export_path = export_dir / f"{filename}.xlsx"
            
            # Get data
            summary = get_monthly_summary()
            invoices = get_sample_invoices()
            
            # Create Excel writer
            writer = pd.ExcelWriter(export_path, engine='openpyxl')
            
            # Create summary sheet
            summary_df = pd.DataFrame([{
                "Total Invoiced": summary["total_invoiced"],
                "Total Paid": summary["total_paid"],
                "Total Due": summary["total_due"],
                "Invoice Count": summary["invoice_count"],
                "Paid Count": summary["paid_count"],
                "Partial Count": summary["partial_count"],
                "Unpaid Count": summary["unpaid_count"]
            }])
            
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Create customer breakdown sheet
            customer_df = pd.DataFrame(summary["by_customer"])
            customer_df.to_excel(writer, sheet_name="By Customer", index=False)
            
            # Create job breakdown sheet
            job_df = pd.DataFrame(summary["by_job"])
            job_df.to_excel(writer, sheet_name="By Job", index=False)
            
            # Create invoices sheet
            invoices_df = pd.DataFrame(invoices)
            invoices_df.to_excel(writer, sheet_name="Invoices", index=False)
            
            # Save Excel file
            writer.close()
            
            # Return Excel file
            return send_from_directory(export_dir, export_path.name)
        
        else:  # CSV
            # Generate CSV report
            export_dir = Path('exports')
            export_dir.mkdir(exist_ok=True)
            
            # Create CSV file
            export_path = export_dir / f"{filename}.csv"
            
            # Get invoices data
            invoices = get_sample_invoices()
            
            # Create DataFrame
            invoices_df = pd.DataFrame(invoices)
            
            # Save CSV file
            invoices_df.to_csv(export_path, index=False)
            
            # Return CSV file
            return send_from_directory(export_dir, export_path.name)
    
    except Exception as e:
        flash(f'Error exporting report: {str(e)}', 'danger')
        return redirect(url_for('billing_module.monthly_report'))

@billing_module_bp.route('/api/pm_allocations')
@login_required
def api_pm_allocations():
    """API endpoint to get PM allocation data"""
    allocations = get_sample_pm_allocations()
    
    # Filter by parameters
    job_number = request.args.get('job_number')
    month = request.args.get('month')
    
    if job_number:
        allocations = [a for a in allocations if a["job_number"] == job_number]
    if month:
        allocations = [a for a in allocations if a["month"] == month]
    
    return jsonify(allocations)

@billing_module_bp.route('/api/invoices')
@login_required
def api_invoices():
    """API endpoint to get invoice data"""
    invoices = get_sample_invoices()
    
    # Filter by parameters
    status = request.args.get('status')
    customer = request.args.get('customer')
    job_number = request.args.get('job_number')
    
    if status:
        invoices = [i for i in invoices if i["status"].lower() == status.lower()]
    if customer:
        invoices = [i for i in invoices if i["customer"] == customer]
    if job_number:
        invoices = [i for i in invoices if i["job_number"] == job_number]
    
    return jsonify(invoices)

@billing_module_bp.route('/api/monthly_summary')
@login_required
def api_monthly_summary():
    """API endpoint to get monthly summary data"""
    summary = get_monthly_summary()
    
    # Filter by parameters
    month = request.args.get('month')
    
    # In a real implementation, this would filter by month
    # For demonstration, we'll just return the sample data
    
    return jsonify(summary)

# Register blueprint function
def register_blueprint(app):
    app.register_blueprint(billing_module_bp)
    return app