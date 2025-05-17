#!/usr/bin/env python

"""
SYSTEMSMITH: Fleet Management System
"""

import logging
import os
import traceback
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import LoginManager, current_user, login_required
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24))

# Set up database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Database initialization
from db import init_app
init_app(app)

# Import models after db initialization
from models import Asset, Driver, User, AssetDriverMapping, db

# Import blueprints
try:
    from routes.drivers import asset_drivers_bp
    app.register_blueprint(asset_drivers_bp)
    logging.info("Registered asset_drivers blueprint")
except ImportError:
    logging.error("Failed to register asset_drivers blueprint")

try:
    from routes.maintenance import maintenance_bp
    app.register_blueprint(maintenance_bp)
    logging.info("Registered maintenance blueprint") 
except ImportError as e:
    logging.error(f"Failed to register maintenance blueprint: {e}")

try:
    from routes.reports import reports_bp
    app.register_blueprint(reports_bp)
    logging.info("Registered reports blueprint")
except ImportError:
    logging.error("Failed to register reports blueprint")

try:
    from routes.alerts import alerts_bp
    app.register_blueprint(alerts_bp)
    logging.info("Registered alerts blueprint")
except ImportError:
    logging.error("Failed to register alerts blueprint")

@login_manager.user_loader
def load_user(user_id):
    """Load user from database"""
    try:
        return User.query.get(int(user_id))
    except:
        return None

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            from flask_login import login_user
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
                
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    from flask_login import logout_user
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    
    # Get assets data (from DB or fallback to JSON file)
    from gauge_api import get_asset_data
    assets = get_asset_data(use_db=True)
    
    # Count assets by category
    asset_counts = {}
    active_assets = 0
    total_assets = len(assets)
    
    for asset in assets:
        category = asset.get('category', 'Uncategorized')
        asset_counts[category] = asset_counts.get(category, 0) + 1
        
        # Count active assets
        if asset.get('active', False):
            active_assets += 1
    
    # Get alerts
    try:
        from models import Alert
        critical_alerts = Alert.query.filter_by(severity='critical', resolved=False).count()
        warning_alerts = Alert.query.filter_by(severity='warning', resolved=False).count()
        info_alerts = Alert.query.filter_by(severity='info', resolved=False).count()
    except:
        critical_alerts = 0
        warning_alerts = 0
        info_alerts = 0
    
    return render_template('dashboard.html', 
                          asset_counts=asset_counts,
                          active_assets=active_assets,
                          total_assets=total_assets,
                          critical_alerts=critical_alerts,
                          warning_alerts=warning_alerts,
                          info_alerts=info_alerts)

@app.route('/assets')
@login_required
def assets():
    """Assets list"""
    from gauge_api import get_asset_data
    
    assets_data = get_asset_data(use_db=True)
    
    # Get categories for filtering
    categories = set()
    for asset in assets_data:
        categories.add(asset.get('category', 'Uncategorized'))
    
    return render_template('assets.html', assets=assets_data, categories=sorted(categories))

@app.route('/asset/<asset_id>')
@login_required
def asset_detail(asset_id):
    """Asset detail page"""
    from gauge_api import get_asset_data
    
    assets_data = get_asset_data(use_db=True)
    
    # Find the asset
    asset = None
    for a in assets_data:
        if a.get('asset_identifier') == asset_id:
            asset = a
            break
    
    if not asset:
        flash('Asset not found', 'danger')
        return redirect(url_for('assets'))
    
    # Get driver assignments
    try:
        from models import AssetDriverMapping
        assignments = (AssetDriverMapping.query
                      .filter_by(asset_id=asset_id)
                      .order_by(AssetDriverMapping.start_date.desc())
                      .all())
    except:
        assignments = []
    
    return render_template('asset_detail.html', asset=asset, assignments=assignments)

@app.route('/ocr_tool', methods=['GET', 'POST'])
@login_required
def ocr_tool():
    """OCR processing tool"""
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        # Check file extension
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'tif', 'tiff'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
            
        if not allowed_file(file.filename):
            flash('File type not supported. Please upload PDF, JPG, PNG, or TIFF files.', 'danger')
            return redirect(request.url)
            
        # Create the uploads directory if it doesn't exist
        uploads_dir = Path('uploads')
        uploads_dir.mkdir(exist_ok=True)
        
        # Create the extracted_data directory if it doesn't exist
        extracted_dir = Path('extracted_data')
        extracted_dir.mkdir(exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(uploads_dir, filename)
        file.save(file_path)
        
        try:
            # Process the file with OCR
            from utils.ocr_processor import OCRProcessor
            ocr = OCRProcessor()
            result = ocr.process_file(file_path)
            
            # Save extracted text to file
            text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
            text_path = os.path.join(extracted_dir, text_filename)
            
            with open(text_path, 'w') as f:
                f.write(result.get('text', 'No text extracted'))
            
            # Return success with extracted text
            return render_template('ocr_tool.html', 
                                  extracted_text=result.get('text', 'No text extracted'),
                                  original_filename=filename,
                                  text_filename=text_filename)
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('ocr_tool.html')

@app.route('/download_extracted_text/<filename>')
@login_required
def download_extracted_text(filename):
    """Download extracted text from OCR processing"""
    extracted_dir = Path('extracted_data')
    
    # Ensure directory exists
    extracted_dir.mkdir(exist_ok=True)
    
    return send_from_directory(extracted_dir, filename, as_attachment=True)

@app.route('/pm_allocation', methods=['GET', 'POST'])
@login_required
def pm_allocation_processor():
    """Handle PM allocation file upload and processing"""
    import os
    import shutil
    import traceback
    from datetime import datetime
    from pathlib import Path
    from werkzeug.utils import secure_filename
    
    # Define directories
    uploads_dir = Path('uploads')
    uploads_dir.mkdir(exist_ok=True)
    
    exports_dir = Path('exports')
    exports_dir.mkdir(exist_ok=True)
    
    recent_reports = []
    
    # Check for existing reports
    try:
        # Get all files in the exports directory
        export_files = sorted(
            [f for f in exports_dir.glob('pm_allocation_*.xlsx')],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )[:10]  # Get the 10 most recent files
        
        for file in export_files:
            report_name = file.name.replace('pm_allocation_', '').replace('.xlsx', '')
            report_name = ' '.join(word.capitalize() for word in report_name.split('_'))
            created_time = datetime.fromtimestamp(os.path.getmtime(file))
            
            recent_reports.append({
                'name': report_name,
                'filename': file.name,
                'created_at': created_time
            })
    except Exception:
        # If there's an error, we'll just show an empty list
        traceback.print_exc()
        recent_reports = []

    # Handle POST request for file upload
    if request.method == 'POST':
        # Check if the required files are in the request
        if 'original_file' not in request.files or 'updated_file' not in request.files:
            flash('Both original and updated files are required', 'danger')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
        
        original_file = request.files['original_file']
        updated_file = request.files['updated_file']
        
        # Check if files were selected
        if original_file.filename == '' or updated_file.filename == '':
            flash('Both original and updated files must be selected', 'danger')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
        
        region = request.form.get('region', 'ALL')
        
        # Check file extensions
        allowed_extensions = {'xlsx', 'xlsm', 'xls'}
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
        
        if not allowed_file(original_file.filename) or not allowed_file(updated_file.filename):
            flash('Files must be Excel workbooks (.xlsx, .xlsm, .xls)', 'danger')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
        
        try:
            # Save the uploaded files
            original_filename = secure_filename(original_file.filename)
            updated_filename = secure_filename(updated_file.filename)
            
            original_path = os.path.join(uploads_dir, original_filename)
            updated_path = os.path.join(uploads_dir, updated_filename)
            
            original_file.save(original_path)
            updated_file.save(updated_path)
            
            # Import the processing function
            from utils.pm_processor import process_pm_allocation
            
            # Process the files
            result = process_pm_allocation(
                original_path=original_path,
                updated_path=updated_path,
                region=region
            )
            
            if result and 'success' in result and result['success']:
                # Format for display
                def format_currency(value):
                    try:
                        return f"${float(value):,.2f}"
                    except (ValueError, TypeError):
                        return "N/A"
                
                # Process the changes for display
                changes = []
                for change in result.get('changes', []):
                    formatted_change = {
                        'row': change.get('row', 'N/A'),
                        'asset_id': change.get('asset_id', 'N/A'),
                        'description': change.get('description', 'N/A'),
                        'original_value': format_currency(change.get('original_value')),
                        'updated_value': format_currency(change.get('updated_value')),
                        'difference': format_currency(change.get('difference', 0))
                    }
                    changes.append(formatted_change)
                
                # Prepare the report data
                report_data = {
                    'original_filename': original_filename,
                    'updated_filename': updated_filename,
                    'total_lines': result.get('total_lines', 0),
                    'changed_lines': result.get('changed_lines', 0),
                    'new_lines': result.get('new_lines', 0),
                    'unchanged_lines': result.get('unchanged_lines', 0),
                    'report_filename': result.get('report_filename', ''),
                    'csv_export_path': result.get('csv_export_path', ''),
                    'changes': changes
                }
                
                # Return the template with the processing results
                return render_template('pm_allocation.html', 
                                      recent_reports=recent_reports,
                                      report_data=report_data)
            else:
                # If processing failed
                error_message = result.get('error', 'Unknown error occurred during processing')
                flash(f'Processing failed: {error_message}', 'danger')
                return render_template('pm_allocation.html', recent_reports=recent_reports)
                
        except Exception as e:
            # Clean up the uploaded files if there's an error
            traceback.print_exc()
            flash(f'Error processing files: {str(e)}', 'danger')
            return render_template('pm_allocation.html', recent_reports=recent_reports)
    
    # GET request - show the upload form
    return render_template('pm_allocation.html', recent_reports=recent_reports)

@app.route('/view_pm_report/<filename>')
@login_required
def view_pm_report(filename):
    """View a PM allocation reconciliation report"""
    # Sanitize filename
    filename = secure_filename(filename)
    
    # Set the directory
    exports_dir = Path('exports')
    
    try:
        import pandas as pd
        from openpyxl import load_workbook
        
        # Load the Excel file
        file_path = os.path.join(exports_dir, filename)
        df = pd.read_excel(file_path)
        
        # Convert to HTML table
        table_html = df.to_html(classes='table table-striped table-hover table-responsive', index=False)
        
        return render_template('view_report.html', 
                              title=f'PM Report: {filename}',
                              table_html=table_html,
                              filename=filename)
    except Exception as e:
        flash(f'Error viewing report: {str(e)}', 'danger')
        return redirect(url_for('pm_allocation_processor'))

@app.route('/download_pm_report/<filename>')
@login_required
def download_pm_report(filename):
    """Download a PM allocation reconciliation report"""
    # Sanitize filename
    filename = secure_filename(filename)
    
    # Set the directory
    exports_dir = Path('exports')
    
    # Ensure directory exists
    exports_dir.mkdir(exist_ok=True)
    
    return send_from_directory(exports_dir, filename, as_attachment=True)

@app.route('/download_export/<path:export_path>')
@login_required
def download_export(export_path):
    """Download an export file"""
    # Get the directory and filename from the path
    path = Path(export_path)
    directory = path.parent
    filename = path.name
    
    # Sanitize filename
    filename = secure_filename(filename)
    
    # Ensure directory exists
    directory.mkdir(exist_ok=True, parents=True)
    
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/auto_process_pm_allocation', methods=['POST'])
@login_required
def auto_process_pm_allocation():
    """Automatically find and process PM allocation files"""
    import os
    import traceback
    from datetime import datetime
    from pathlib import Path
    from utils.pm_processor import find_allocation_files, process_pm_allocation
    
    # Path for exports
    exports_dir = Path('exports')
    exports_dir.mkdir(exist_ok=True)
    
    # Find allocation files
    original_file, updated_file = find_allocation_files()
    
    # If files were found
    if original_file and updated_file:
        try:
            # Process the files
            result = process_pm_allocation(
                original_path=original_file,
                updated_path=updated_file,
                region='ALL'  # Process all regions by default
            )
            
            if result and result.get('success'):
                original_filename = os.path.basename(original_file)
                updated_filename = os.path.basename(updated_file)
                
                # Format for display
                def format_currency(value):
                    try:
                        return f"${float(value):,.2f}"
                    except (ValueError, TypeError):
                        return "N/A"
                
                # Process the changes for display
                changes = []
                for change in result.get('changes', []):
                    formatted_change = {
                        'row': change.get('row', 'N/A'),
                        'asset_id': change.get('asset_id', 'N/A'),
                        'description': change.get('description', 'N/A'),
                        'original_value': format_currency(change.get('original_value')),
                        'updated_value': format_currency(change.get('updated_value')),
                        'difference': format_currency(change.get('difference', 0))
                    }
                    changes.append(formatted_change)
                
                # Check for existing reports to display
                recent_reports = []
                try:
                    # Get all files in the exports directory
                    export_files = sorted(
                        [f for f in exports_dir.glob('pm_allocation_*.xlsx')],
                        key=lambda x: os.path.getmtime(x),
                        reverse=True
                    )[:10]  # Get the 10 most recent files
                    
                    for file in export_files:
                        report_name = file.name.replace('pm_allocation_', '').replace('.xlsx', '')
                        report_name = ' '.join(word.capitalize() for word in report_name.split('_'))
                        created_time = datetime.fromtimestamp(os.path.getmtime(file))
                        
                        recent_reports.append({
                            'name': report_name,
                            'filename': file.name,
                            'created_at': created_time
                        })
                except Exception:
                    traceback.print_exc()
                    recent_reports = []
                
                # Prepare the report data
                report_data = {
                    'original_filename': original_filename,
                    'updated_filename': updated_filename,
                    'total_lines': result.get('total_lines', 0),
                    'changed_lines': result.get('changed_lines', 0),
                    'new_lines': result.get('new_lines', 0),
                    'unchanged_lines': result.get('unchanged_lines', 0),
                    'report_filename': result.get('report_filename', ''),
                    'csv_export_path': result.get('csv_export_path', ''),
                    'changes': changes
                }
                
                # Add success message
                flash(f'Successfully processed files: {original_filename} and {updated_filename}', 'success')
                
                # Return the template with processing results
                return render_template('pm_allocation.html',
                                      recent_reports=recent_reports,
                                      report_data=report_data)
            else:
                # If processing failed
                error_message = result.get('error', 'Unknown error occurred during processing')
                flash(f'Auto-processing failed: {error_message}', 'danger')
        except Exception as e:
            # Log the error
            traceback.print_exc()
            flash(f'Error during auto-processing: {str(e)}', 'danger')
    else:
        # If no files were found
        flash('Could not find suitable PM allocation files in the attached_assets folder. Please upload files manually.', 'warning')
    
    # Redirect back to the PM allocation page
    return redirect(url_for('pm_allocation_processor'))

@app.route('/daily_report')
@login_required
def daily_report():
    """Generate daily driver report"""
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_day_name = yesterday.strftime('%A')
    yesterday_month = yesterday.strftime('%B')
    yesterday_day = yesterday.strftime('%d').lstrip('0')
    
    # Check if there are existing files from yesterday
    real_data_found = False
    
    # Attached assets directory
    assets_dir = Path('attached_assets')
    
    for filename in os.listdir(assets_dir):
        if "DAILY LATE START" in filename and yesterday.strftime('%m.%d.%Y') in filename:
            real_data_found = True
            break
            
    # Process and generate the report
    data_files = []
    ls_ee_data = []
    noj_data = []
    
    if real_data_found:
        # Read real data
        pass  # Placeholder - actual implementation
    else:
        # Use sample data
        ls_ee_data = [
            ['JARED RUHRUP', '2024-019', 'Tarrant VA Bridge Rehab', 'PT-237', '240441', 'Miramontes Jr, Juan C', '', 'Arrived', 'Departed', '2024-023', '7:00 AM', '5:30 PM', 'Late', 'Left Early', '7:11 AM', '4:55 PM', '7:54:00', '0'],
            ['LUIS A. MORALES', '2023-035', 'Harris VA Bridge Rehabs', 'PT-160', '440455', 'Saldierna Jr, Armando', '', 'Arrived', 'Departed', '2023-035', '7:00 AM', '5:30 PM', 'Late', 'Left Early', '8:32 AM', '4:44 PM', '2:48:00', '0'],
            ['VARIOUS', 'TEXDIST', 'Texas District Office', 'PT-241', '210050', 'Garcia, Mark E XL', '', 'Arrived', 'Departed', '2025-004', '8:00 AM', '5:00 PM', 'Late', 'Left Early', '8:50 AM', '4:33 PM', '7:09:00', '0'],
            ['VARIOUS', 'TRAFFIC WALNUT HILL YARD', 'TRAFFIC WALNUT HILL YARD', 'PT-173', '240494', 'Hernandez, Juan B', '', 'Arrived', 'Departed', '2024-004', '7:00 AM', '5:30 PM', 'Late', 'Left Early', '7:04 AM', '5:12 PM', '1:58:00', '0']
        ]
        
        noj_data = [
            ['*N/A', 'N.O.J.Y.', 'NOT ON DHISTORY REPORT', 'ET-41', '240801', 'Hampton, Justin D', '', '', 'NOJY', 'NOJY', 'NOJY', '12:00 AM', '0', ''],
            ['*N/A', 'N.O.J.Y.', 'NOT ON DHISTORY REPORT', 'PT-19S', 'FIGBRY', 'Figueroa, Bryan', '', '', 'NOJY', 'NOJY', 'NOJY', '12:00 AM', '1', '']
        ]
    
    # Render template with data
    return render_template('daily_report.html',
                          yesterday=yesterday,
                          yesterday_day_name=yesterday_day_name,
                          yesterday_month=yesterday_month,
                          yesterday_day=yesterday_day,
                          ls_ee_data=ls_ee_data,
                          noj_data=noj_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
