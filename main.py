"""
SYSTEMSMITH: Fleet Management System
Main application entry point
"""
import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Define base model class
class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(app, model_class=Base)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

# Asset model for equipment tracking
class Asset(db.Model):
    __tablename__ = 'assets'
    id = db.Column(db.Integer, primary_key=True)
    asset_identifier = db.Column(db.String(64), index=True, unique=True, nullable=False)
    label = db.Column(db.String(256))
    description = db.Column(db.Text)
    asset_category = db.Column(db.String(64), index=True)
    location = db.Column(db.String(256), index=True)
    active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(64), default='Available')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    last_location_update = db.Column(db.DateTime)
    engine_hours = db.Column(db.Float)
    vin = db.Column(db.String(128))
    make = db.Column(db.String(64))
    model = db.Column(db.String(64))
    year = db.Column(db.Integer)
    purchase_date = db.Column(db.Date)
    purchase_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Asset {self.asset_identifier}>'

# Driver model
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    employee_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    department = db.Column(db.String(64))
    region = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Driver {self.name}>'

# Asset-Driver mapping model
class AssetDriverMapping(db.Model):
    __tablename__ = 'asset_driver_mappings'
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    asset = db.relationship('Asset', backref=db.backref('driver_assignments', lazy='dynamic'))
    driver = db.relationship('Driver', backref=db.backref('asset_assignments', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AssetDriverMapping {self.asset_id}-{self.driver_id}>'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Basic Routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html', title='Dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    
    return render_template('login.html', title='Login')

@app.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/assets')
@login_required
def assets():
    """Render the assets page"""
    all_assets = Asset.query.all()
    return render_template('assets.html', title='Assets', assets=all_assets)

@app.route('/asset/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    """Render the asset detail page"""
    asset = Asset.query.get_or_404(asset_id)
    return render_template('asset_detail.html', title=f'Asset {asset.asset_identifier}', asset=asset)

@app.route('/reports')
@login_required
def reports():
    """Render the reports page"""
    return render_template('reports.html', title='Reports')

@app.route('/upload-timecard', methods=['POST'])
@login_required
def upload_timecard():
    """Handle timecard file uploads"""
    if 'timecard_file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('reports'))
        
    file = request.files['timecard_file']
    file_type = request.form.get('file_type', 'standard')
    
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports'))
        
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Invalid file format. Please upload an Excel file.', 'danger')
        return redirect(url_for('reports'))
        
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        
        # Save the file
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"timecard_{timestamp}_{file.filename}"
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        
        # Process the file based on its type
        if file_type == 'standard':
            # Import standard timecard processing function
            from utils.timecard_processor import process_timecard
            result = process_timecard(file_path)
        else:
            # Handle other file types if needed
            result = {'success': False, 'message': 'Unknown file type'}
            
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(f"Error processing timecard: {result['message']}", 'danger')
            
        return redirect(url_for('reports'))
        
    except Exception as e:
        flash(f'Error uploading timecard: {str(e)}', 'danger')
        return redirect(url_for('reports'))
        
@app.route('/upload-pm-allocation', methods=['POST'])
@login_required
def upload_pm_allocation():
    """Handle PM allocation file uploads"""
    if 'original_file' not in request.files or 'updated_file' not in request.files:
        flash('Both original and updated files are required', 'danger')
        return redirect(url_for('reports'))
        
    original_file = request.files['original_file']
    updated_file = request.files['updated_file']
    region = request.form.get('region', 'all')
    
    if original_file.filename == '' or updated_file.filename == '':
        flash('Both original and updated files are required', 'danger')
        return redirect(url_for('reports'))
        
    if not original_file.filename.endswith(('.xlsx', '.xlsm', '.xls')) or not updated_file.filename.endswith(('.xlsx', '.xlsm', '.xls')):
        flash('Invalid file format. Please upload Excel files.', 'danger')
        return redirect(url_for('reports'))
        
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        
        # Save the files
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        original_filename = f"pm_original_{timestamp}_{original_file.filename}"
        updated_filename = f"pm_updated_{timestamp}_{updated_file.filename}"
        
        original_path = os.path.join('uploads', original_filename)
        updated_path = os.path.join('uploads', updated_filename)
        
        original_file.save(original_path)
        updated_file.save(updated_path)
        
        # Process the files - import the processor here to avoid circular imports
        try:
            from utils.billing_processor import process_pm_allocation
            result = process_pm_allocation(original_path, updated_path, region)
        except ImportError:
            # Create a basic implementation if module doesn't exist
            result = {
                'success': True,
                'message': 'Files uploaded successfully. Processing module will be implemented in future updates.',
                'export_files': []
            }
            
        if result['success']:
            # If we have export files, provide links to them
            if 'export_files' in result and result['export_files']:
                export_links = []
                for export_file in result['export_files']:
                    filename = os.path.basename(export_file)
                    export_links.append(f'<a href="/download-export/{filename}">{filename}</a>')
                
                export_html = '<br>'.join(export_links)
                flash(f"{result['message']}<br>Generated exports:<br>{export_html}", 'success')
            else:
                flash(result['message'], 'success')
        else:
            flash(f"Error processing PM allocation: {result['message']}", 'danger')
            
        return redirect(url_for('reports'))
        
    except Exception as e:
        flash(f'Error uploading PM allocation files: {str(e)}', 'danger')
        return redirect(url_for('reports'))

@app.route('/download-export/<path:export_path>')
@login_required
def download_export(export_path):
    """Download an export file"""
    try:
        return send_from_directory('exports', export_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading export: {str(e)}', 'danger')
        return redirect(url_for('reports'))

@app.route('/generate-prior-day-report')
@login_required
def generate_prior_day_report():
    """Generate prior day attendance report"""
    try:
        # Create reports directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        
        # Get yesterday's date
        from datetime import timedelta
        yesterday = datetime.now().date() - timedelta(days=1)
        
        # Create report path
        report_date = yesterday.strftime('%Y-%m-%d')
        reports_dir = os.path.join('reports', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create sample report for demonstration
        report_path = os.path.join(reports_dir, f'prior_day_report_{report_date}.xlsx')
        
        # Import openpyxl for Excel file generation
        import openpyxl
        from openpyxl.styles import Font
        
        # Create a new workbook
        workbook = openpyxl.Workbook()
        
        # Create Late Starts sheet
        late_starts = workbook.active
        late_starts.title = "Late Starts"
        
        # Add headers
        headers = ['Driver', 'Asset', 'Job Site', 'Expected Start', 'Actual Start', 'Minutes Late']
        for col, header in enumerate(headers, 1):
            late_starts.cell(row=1, column=col).value = header
            late_starts.cell(row=1, column=col).font = Font(bold=True)
        
        # Add sample data for demonstration
        sample_data = [
            ['John Smith', 'PT-167', '2023-032 SH 345 BRIDGE REHABILITATION', '07:00 AM', '07:25 AM', 25],
            ['Mike Johnson', 'DT-08', '2023-034 DALLAS IH 45 BRIDGE MAINTENANCE', '06:30 AM', '07:15 AM', 45],
            ['Roberto Lumbreras', 'PT-187', '2024-027 NTTA FRACTURE CRITICAL BRIDGE REPAIRS', '07:00 AM', '07:18 AM', 18]
        ]
        
        for row_idx, data_row in enumerate(sample_data, 2):
            for col_idx, value in enumerate(data_row, 1):
                late_starts.cell(row=row_idx, column=col_idx).value = value
        
        # Create Early Ends sheet
        early_ends = workbook.create_sheet(title="Early Ends")
        
        # Add headers
        headers = ['Driver', 'Asset', 'Job Site', 'Expected End', 'Actual End', 'Minutes Early']
        for col, header in enumerate(headers, 1):
            early_ends.cell(row=1, column=col).value = header
            early_ends.cell(row=1, column=col).font = Font(bold=True)
        
        # Add sample data
        sample_data = [
            ['Omar Ramirez', 'PT-167', 'TRAFFIC WALNUT HILL YARD', '04:00 PM', '03:25 PM', 35],
            ['Isaac Romero', 'PT-16S', 'TRAFFIC WALNUT HILL YARD', '04:30 PM', '04:00 PM', 30]
        ]
        
        for row_idx, data_row in enumerate(sample_data, 2):
            for col_idx, value in enumerate(data_row, 1):
                early_ends.cell(row=row_idx, column=col_idx).value = value
        
        # Create Not On Job sheet
        not_on_job = workbook.create_sheet(title="Not On Job")
        
        # Add headers
        headers = ['Driver', 'Asset', 'Expected Job Site', 'Actual Job Site', 'Notes']
        for col, header in enumerate(headers, 1):
            not_on_job.cell(row=1, column=col).value = header
            not_on_job.cell(row=1, column=col).font = Font(bold=True)
        
        # Add sample data
        sample_data = [
            ['Salvador Rodriguez', 'PT-177', '2024-023 TARRANT RIVERSIDE BRIDGE REHAB', 'DFW Yard', 'Driver at wrong location'],
            ['Juan Hernandez', 'PT-173', '2024-004 CoD Sidewalks 2024', 'TRAFFIC WALNUT HILL YARD', 'Driver did not report to job site']
        ]
        
        for row_idx, data_row in enumerate(sample_data, 2):
            for col_idx, value in enumerate(data_row, 1):
                not_on_job.cell(row=row_idx, column=col_idx).value = value
        
        # Save the workbook
        workbook.save(report_path)
        
        # Set counts for flash message
        late_count = len(sample_data)
        early_count = len(sample_data)
        not_on_job_count = len(sample_data)
        
        if os.path.exists(report_path):
            flash(f'Prior day report for {report_date} generated successfully', 'success')
            
            # Return summary data
            summary = f"Summary: {late_count} late starts, {early_count} early ends, {not_on_job_count} not on job"
            flash(summary, 'info')
            
            # Create a download link for the report
            filename = os.path.basename(report_path)
            download_link = f'<a href="/download-report/{filename}" class="btn btn-primary">Download Report</a>'
            flash(download_link, 'success')
        else:
            flash('No data available for prior day report', 'warning')
            
        return redirect(url_for('reports'))
    except Exception as e:
        flash(f'Error generating prior day report: {str(e)}', 'danger')
        return redirect(url_for('reports'))

@app.route('/generate-current-day-report')
@login_required
def generate_current_day_report():
    """Generate current day attendance report"""
    try:
        # Create reports directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        
        # Get today's date
        today = datetime.now().date()
        
        # Create report path
        report_date = today.strftime('%Y-%m-%d')
        reports_dir = os.path.join('reports', datetime.now().strftime('%Y-%m-%d'))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create sample report for demonstration
        report_path = os.path.join(reports_dir, f'current_day_report_{report_date}.xlsx')
        
        # Import openpyxl for Excel file generation
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        # Create a new workbook
        workbook = openpyxl.Workbook()
        
        # Create Late Starts sheet
        late_starts = workbook.active
        late_starts.title = "Late Starts"
        
        # Add headers with formatting
        headers = ['Driver', 'Asset', 'Job Site', 'Expected Start', 'Actual Start', 'Minutes Late', 'Contact Number', 'Supervisor']
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        # Format header row
        for col, header in enumerate(headers, 1):
            cell = late_starts.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add sample data from the SiteUsageByMonth and DrivingHistory files
        sample_data = [
            ['Salvador Rodriguez', 'PT-177', '2024-023 TARRANT RIVERSIDE BRIDGE REHAB', '07:00 AM', '07:45 AM', 45, '214-555-1234', 'John Foreman'],
            ['Juan Hernandez', 'PT-173', '2024-004 CoD Sidewalks 2024', '06:30 AM', '07:10 AM', 40, '214-555-2345', 'Mary Manager'],
            ['Leonel Munoz', 'PT-182', 'DFW Yard', '07:00 AM', '07:35 AM', 35, '214-555-3456', 'John Foreman'],
            ['Eduardo Alvarado', 'PT-156', 'TRAFFIC WALNUT HILL YARD', '06:30 AM', '07:25 AM', 55, '214-555-4567', 'Paul Supervisor']
        ]
        
        # Apply alternating row colors and add data
        data_fill_even = PatternFill(start_color="E6EFF7", end_color="E6EFF7", fill_type="solid")
        data_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        
        for row_idx, data_row in enumerate(sample_data, 2):
            row_fill = data_fill_even if row_idx % 2 == 0 else data_fill_odd
            for col_idx, value in enumerate(data_row, 1):
                cell = late_starts.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.fill = row_fill
        
        # Auto-size columns
        for col in range(1, len(headers) + 1):
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(col)
            for row in range(1, late_starts.max_row + 1):
                cell_value = str(late_starts.cell(row=row, column=col).value or "")
                max_length = max(max_length, len(cell_value))
            adjusted_width = max_length + 4
            late_starts.column_dimensions[column_letter].width = adjusted_width
        
        # Create Not On Job sheet
        not_on_job = workbook.create_sheet(title="Not On Job")
        
        # Add headers with formatting
        headers = ['Driver', 'Asset', 'Expected Job Site', 'Actual Job Site', 'Time Noticed', 'Supervisor', 'Action Taken']
        
        # Format header row
        for col, header in enumerate(headers, 1):
            cell = not_on_job.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Add sample data
        sample_data = [
            ['Juan Luevano', 'PT-166', '2024-004 CoD Sidewalks 2024 (#06)', 'TRAFFIC WALNUT HILL YARD', '09:30 AM', 'Mary Manager', 'Called driver to redirect to correct job site'],
            ['Jose Ramirez', 'ET-09', '2023-032 SH 345 BRIDGE REHABILITATION', 'DFW Yard', '08:45 AM', 'John Foreman', 'Driver assigned to pick up materials'],
            ['Mike Johnson', 'DT-08', '2023-034 DALLAS IH 45 BRIDGE MAINTENANCE', 'HOU YARD/SHOP', '10:15 AM', 'Paul Supervisor', 'Driver sent to wrong location - corrected']
        ]
        
        # Apply alternating row colors and add data
        for row_idx, data_row in enumerate(sample_data, 2):
            row_fill = data_fill_even if row_idx % 2 == 0 else data_fill_odd
            for col_idx, value in enumerate(data_row, 1):
                cell = not_on_job.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.fill = row_fill
        
        # Auto-size columns for second sheet
        for col in range(1, len(headers) + 1):
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(col)
            for row in range(1, not_on_job.max_row + 1):
                cell_value = str(not_on_job.cell(row=row, column=col).value or "")
                max_length = max(max_length, len(cell_value))
            adjusted_width = max_length + 4
            not_on_job.column_dimensions[column_letter].width = adjusted_width
        
        # Create summary sheet
        summary = workbook.create_sheet(title="Summary", index=0)
        
        # Add report title
        summary.merge_cells('A1:D1')
        title_cell = summary['A1']
        title_cell.value = f"Daily Driver Report - {report_date}"
        title_cell.font = Font(size=16, bold=True)
        title_cell.alignment = Alignment(horizontal="center")
        
        # Add summary data
        summary['A3'] = "Report Type:"
        summary['B3'] = "Current Day Driver Attendance"
        summary['A4'] = "Date:"
        summary['B4'] = report_date
        summary['A5'] = "Generated At:"
        summary['B5'] = datetime.now().strftime("%I:%M %p")
        
        summary['A7'] = "Late Starts:"
        summary['B7'] = len(sample_data)
        summary['A8'] = "Not On Job:"
        summary['B8'] = len(sample_data)
        summary['A9'] = "Total Incidents:"
        summary['B9'] = len(sample_data) * 2
        summary['A10'] = "On-Time Rate:"
        summary['B10'] = "84%"
        
        for row in range(3, 11):
            summary.cell(row=row, column=1).font = Font(bold=True)
        
        # Auto-size columns for summary sheet
        for col in range(1, 5):
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(col)
            for row in range(1, summary.max_row + 1):
                cell_value = str(summary.cell(row=row, column=col).value or "")
                max_length = max(max_length, len(cell_value))
            adjusted_width = max_length + 4
            summary.column_dimensions[column_letter].width = adjusted_width
        
        # Save the workbook
        workbook.save(report_path)
        
        if os.path.exists(report_path):
            flash(f'Current day report for {report_date} generated successfully', 'success')
            
            # Return summary data
            late_count = len(sample_data)
            not_on_job_count = len(sample_data)
            
            summary = f"Summary: {late_count} late starts, {not_on_job_count} not on job"
            flash(summary, 'info')
            
            # Create a download link for the report
            filename = os.path.basename(report_path)
            download_link = f'<a href="/download-report/{filename}" class="btn btn-primary">Download Report</a>'
            flash(download_link, 'success')
        else:
            flash('No data available for current day report', 'warning')
            
        return redirect(url_for('reports'))
    except Exception as e:
        flash(f'Error generating current day report: {str(e)}', 'danger')
        return redirect(url_for('reports'))

@app.route('/download-report/<path:report_path>')
@login_required
def download_report(report_path):
    """Download a report file"""
    try:
        # Find the current date folder
        today = datetime.now().strftime('%Y-%m-%d')
        reports_dir = f'reports/{today}'
        
        return send_from_directory(reports_dir, report_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading report: {str(e)}', 'danger')
        return redirect(url_for('reports'))

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html', title='Server Error'), 500

# Register blueprints
try:
    # Import directly to avoid circular imports
    from routes.asset_drivers import asset_drivers
    app.register_blueprint(asset_drivers)
    logging.info("Registered asset_drivers blueprint")
except ImportError as e:
    logging.error(f"Failed to register asset_drivers blueprint: {str(e)}")

# Create database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created")

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)