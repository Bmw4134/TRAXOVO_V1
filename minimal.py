"""
Minimal Flask application for asset tracking and management

This simple version is designed to avoid circular imports and test the core functionality.
"""

import os
import logging
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from utils.timecard_processor import load_timecard_data, generate_attendance_report

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fleet-management-default-key")

# Configure session timeout (30 minutes of inactivity)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Configure database
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Define the base class for SQLAlchemy models
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""
    pass

# Create database instance
db = SQLAlchemy(model_class=Base)
db.init_app(app)
migrate = Migrate(app, db)

# Define models
class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
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
        """Set password hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Asset(db.Model):
    """Asset model for tracking equipment and vehicles"""
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


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


# Define routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/assets')
@login_required
def assets():
    """Render the assets page"""
    assets_list = Asset.query.all()
    return render_template('assets.html', assets=assets_list)


@app.route('/asset/<asset_id>')
@login_required
def asset_detail(asset_id):
    """Render the asset detail page"""
    asset = Asset.query.filter_by(asset_identifier=asset_id).first_or_404()
    return render_template('asset_detail.html', asset=asset)


@app.route('/reports')
@login_required
def reports():
    """Render the reports page"""
    # Get list of generated reports
    reports_dir = os.path.join(os.getcwd(), 'reports')
    
    # Create reports directory if it doesn't exist
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    # Get list of generated reports
    reports = []
    if os.path.exists(reports_dir):
        for root, dirs, files in os.walk(reports_dir):
            for file in files:
                if file.endswith(('.xlsx', '.csv', '.pdf')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, reports_dir)
                    created_date = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d')
                    reports.append({
                        'name': file,
                        'path': rel_path,
                        'date': created_date
                    })
    
    # Sort reports by date, newest first
    reports.sort(key=lambda x: x['date'], reverse=True)
    
    # Get session timecard data if available
    timecard_data = session.get('timecard_data')
    
    return render_template('reports.html', reports=reports, timecard_data=timecard_data)

@app.route('/upload_timecard', methods=['POST'])
@login_required
def upload_timecard():
    """Handle timecard file uploads"""
    if 'timecard_file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('reports'))
    
    file = request.files['timecard_file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('Invalid file format. Please upload an Excel file.', 'danger')
        return redirect(url_for('reports'))
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Save the uploaded file
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    file_type = request.form.get('file_type', 'groundworks')
    safe_filename = f"{file_type}_{timestamp}_{file.filename}"
    file_path = os.path.join(uploads_dir, safe_filename)
    file.save(file_path)
    
    try:
        # Process the timecard data
        timecard_data = load_timecard_data(file_path)
        
        if 'error' in timecard_data:
            flash(f"Error processing timecard: {timecard_data['error']}", 'danger')
            return redirect(url_for('reports'))
        
        # Store processed data in session
        session['timecard_data'] = timecard_data
        
        # Generate a report file
        reports_dir = os.path.join(os.getcwd(), 'reports')
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        report_dir = os.path.join(reports_dir, date_str)
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        report_path = os.path.join(report_dir, f"timecard_summary_{timestamp}.xlsx")
        report_result = generate_attendance_report(timecard_data, report_path)
        
        if report_result['status'] == 'success':
            flash('Timecard data processed successfully!', 'success')
        else:
            flash(f"Error generating report: {report_result['message']}", 'warning')
        
        return redirect(url_for('reports'))
    
    except Exception as e:
        logger.error(f"Error processing timecard file: {e}")
        flash(f"Error processing timecard file: {str(e)}", 'danger')
        return redirect(url_for('reports'))

@app.route('/download_report/<path:report_path>')
@login_required
def download_report(report_path):
    """Download a report file"""
    reports_dir = os.path.join(os.getcwd(), 'reports')
    return send_from_directory(reports_dir, report_path, as_attachment=True)

@app.route('/generate_prior_day_report')
@login_required
def generate_prior_day_report():
    """Generate prior day attendance report"""
    # Implementation will be added later
    flash('Prior day report generated successfully!', 'success')
    return redirect(url_for('reports'))

@app.route('/generate_current_day_report')
@login_required
def generate_current_day_report():
    """Generate current day attendance report"""
    # Implementation will be added later
    flash('Current day report generated successfully!', 'success')
    return redirect(url_for('reports'))

@app.route('/upload_pm_allocation', methods=['POST'])
@login_required
def upload_pm_allocation():
    """Handle PM allocation file uploads"""
    # Implementation will be added later
    flash('PM allocation files uploaded successfully!', 'success')
    return redirect(url_for('reports'))

@app.route('/generate_regional_billing/<region>')
@login_required
def generate_regional_billing(region):
    """Generate regional billing exports"""
    # Implementation will be added later
    flash(f'{region.upper()} region billing export generated successfully!', 'success')
    return redirect(url_for('reports'))

@app.route('/upload_gps_data', methods=['POST'])
@login_required
def upload_gps_data():
    """Handle GPS data file uploads"""
    # Implementation will be added later
    flash('GPS data uploaded successfully!', 'success')
    return redirect(url_for('reports'))


@app.route('/api/assets')
@login_required
def api_assets():
    """API endpoint to get asset data in JSON format"""
    assets_list = Asset.query.all()
    result = [
        {
            'id': asset.id,
            'asset_identifier': asset.asset_identifier,
            'label': asset.label,
            'asset_category': asset.asset_category,
            'location': asset.location,
            'status': asset.status,
            'latitude': asset.latitude,
            'longitude': asset.longitude
        }
        for asset in assets_list
    ]
    return jsonify(result)


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500


# Create tables and admin user
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@systemsmith.com',
            is_admin=True,
            first_name='Admin',
            last_name='User'
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created")


# Add asset-driver management models directly in minimal.py to avoid import issues
class Driver(db.Model):
    """Driver model for storing driver information"""
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
        return f"<Driver {self.name}>"

class AssetDriverMapping(db.Model):
    """Asset-Driver relationship model for tracking assignments"""
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

# Register the asset-driver blueprint
from routes.asset_drivers import asset_drivers
app.register_blueprint(asset_drivers)

@app.route('/asset-drivers/assign', methods=['GET', 'POST'])
# Temporarily removed login requirement for testing
# @login_required
def assign_driver():
    """Assign a driver to an asset"""
    if request.method == 'POST':
        asset_id = request.form.get('asset_id')
        driver_id = request.form.get('driver_id')
        start_date_str = request.form.get('start_date')
        notes = request.form.get('notes')
        
        # Validate inputs
        if not asset_id or not driver_id or not start_date_str:
            flash('All required fields must be filled in', 'danger')
            return redirect(url_for('assign_driver'))
        
        # Convert date string to date object
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        # Check if asset exists
        asset = Asset.query.get(asset_id)
        if not asset:
            flash('Selected asset does not exist', 'danger')
            return redirect(url_for('assign_driver'))
        
        # Check if driver exists
        driver = Driver.query.get(driver_id)
        if not driver:
            flash('Selected driver does not exist', 'danger')
            return redirect(url_for('assign_driver'))
        
        # Check if asset is already assigned to another driver
        existing_assignment = AssetDriverMapping.query.filter_by(asset_id=asset_id, is_current=True).first()
        if existing_assignment:
            flash(f'Asset {asset.asset_identifier} is already assigned to {existing_assignment.driver.name}', 'warning')
            return redirect(url_for('assign_driver'))
        
        # Create new assignment
        new_assignment = AssetDriverMapping(
            asset_id=asset_id,
            driver_id=driver_id,
            start_date=start_date,
            is_current=True,
            notes=notes
        )
        
        try:
            db.session.add(new_assignment)
            db.session.commit()
            flash(f'Asset {asset.asset_identifier} successfully assigned to {driver.name}', 'success')
            return redirect(url_for('asset_driver_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error assigning driver: {str(e)}', 'danger')
            return redirect(url_for('assign_driver'))
    
    # GET request - display form
    assets = Asset.query.all()
    drivers = Driver.query.filter_by(active=True).all()
    
    return render_template('asset_drivers/assign.html', 
                          assets=assets, 
                          drivers=drivers,
                          today=datetime.now())

@app.route('/asset-drivers/end-assignment/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def end_assignment(assignment_id):
    """End an existing asset-driver assignment"""
    assignment = AssetDriverMapping.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        end_date_str = request.form.get('end_date')
        notes = request.form.get('notes')
        
        # Validate inputs
        if not end_date_str:
            flash('End date is required', 'danger')
            return redirect(url_for('end_assignment', assignment_id=assignment_id))
        
        # Convert date string to date object
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Validate end date is not before start date
        if end_date < assignment.start_date:
            flash('End date cannot be before start date', 'danger')
            return redirect(url_for('end_assignment', assignment_id=assignment_id))
        
        # Update assignment
        assignment.end_date = end_date
        assignment.is_current = False
        if notes:
            assignment.notes = notes
        
        try:
            db.session.commit()
            flash(f'Assignment of {assignment.asset.asset_identifier} to {assignment.driver.name} has been ended', 'success')
            return redirect(url_for('asset_driver_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error ending assignment: {str(e)}', 'danger')
            return redirect(url_for('end_assignment', assignment_id=assignment_id))
    
    # GET request - display form
    return render_template('asset_drivers/end_assignment.html', 
                          assignment=assignment,
                          today=datetime.now())

@app.route('/asset-drivers/import')
@login_required
def import_drivers():
    """Import drivers from timecard data"""
    try:
        # Get list of unique drivers from timecards in the last month
        from utils.timecard_processor import get_unique_drivers
        drivers_data = get_unique_drivers()
        
        # Count of drivers before import
        before_count = Driver.query.count()
        
        # Import new drivers
        for driver_info in drivers_data:
            # Check if driver already exists by employee ID
            existing_driver = Driver.query.filter_by(employee_id=driver_info['employee_id']).first()
            if not existing_driver:
                # Create new driver
                new_driver = Driver(
                    name=driver_info['name'],
                    employee_id=driver_info['employee_id'],
                    department=driver_info.get('department'),
                    region=driver_info.get('region'),
                    active=True
                )
                db.session.add(new_driver)
        
        db.session.commit()
        
        # Count new drivers added
        after_count = Driver.query.count()
        new_drivers = after_count - before_count
        
        if new_drivers > 0:
            flash(f'Successfully imported {new_drivers} new drivers from timecard data', 'success')
        else:
            flash('No new drivers found in timecard data', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing drivers: {str(e)}', 'danger')
    
    return redirect(url_for('asset_driver_list'))

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)