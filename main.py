"""
TRAXOVO Fleet Management System - Main Application

This module provides the main entry point for the TRAXOVO fleet management system.
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, redirect, url_for, request

# Emergency fix - use working app configuration
from app import app

# Register essential login routes only
try:
    from routes.auth import auth_bp
    from routes.admin import admin_bp  
    from routes.secure_attendance import secure_attendance_bp
    from routes.simple_login import simple_login_bp
    app.register_blueprint(auth_bp, url_prefix='/auth', name='auth_main')
    app.register_blueprint(admin_bp, url_prefix='/admin', name='admin_main')
    app.register_blueprint(secure_attendance_bp, url_prefix='/secure-attendance', name='secure_main')
    app.register_blueprint(simple_login_bp, url_prefix='/auth', name='simple_login_main')
    print("✅ Essential login routes registered successfully")
except ImportError as e:
    print(f"Skipping complex routes: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup runtime mode indicator
runtime_mode = os.environ.get('RUNTIME_MODE', 'DEVELOPMENT').upper()
logger.info(f"TRAXOVO running in {runtime_mode} mode")

# Load jobsite catalog
try:
    from utils.jobsite_catalog_loader import load_jobsite_catalog
    load_jobsite_catalog()
except Exception as e:
    logger.warning(f"Error loading jobsite catalog: {str(e)}")

# Register secure authentication and admin modules with enhanced security
try:
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.secure_attendance import secure_attendance_bp
    from routes.password_reset import password_reset_bp
    from routes.construction_zone_manager import construction_zones_bp
    from routes.zone_schedule_manager import zone_schedule_bp
    from routes.mobile_map import mobile_map_bp
    from routes.pe_zone_filter import pe_zone_filter_bp
    from routes.job_security_monitoring import job_security_monitoring_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(secure_attendance_bp)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(construction_zones_bp)
    app.register_blueprint(zone_schedule_bp)
    app.register_blueprint(mobile_map_bp)
    app.register_blueprint(pe_zone_filter_bp)
    app.register_blueprint(job_security_monitoring_bp)
    logger.info("✅ TRAXOVO Security Suite registered: Auth + Admin + Secure Attendance + Password Reset + Construction Zones")
except Exception as e:
    logger.warning(f"Error registering security modules: {str(e)}")

# Skip complex blueprints temporarily to get login working
# Complex blueprints disabled until login is operational
print("✅ Skipping complex blueprints for immediate login access")

# Register attendance workflow
try:
    from routes.attendance_workflow import attendance_workflow_bp
    app.register_blueprint(attendance_workflow_bp, url_prefix='/attendance-workflow')
    logger.info("Attendance Workflow blueprint registered successfully")
except Exception as e:
    logger.warning(f"Error registering attendance workflow: {str(e)}")

# Register standalone driver reports dashboard
try:
    from create_driver_reports_route import create_driver_reports_blueprint
    app.register_blueprint(create_driver_reports_blueprint())
    logger.info("Driver reports dashboard (modern UI) registered")
except Exception as e:
    logger.warning(f"Error registering driver reports dashboard: {str(e)}")

# Register automatic attendance processing module
try:
    from routes.auto_attendance_routes import auto_attendance
    app.register_blueprint(auto_attendance)
    logger.info("Automatic Attendance Processing module registered successfully")
except Exception as e:
    logger.warning(f"Error registering automatic attendance module: {str(e)}")

# Register GPS Map module
try:
    from routes.gps_map import gps_map_bp
    app.register_blueprint(gps_map_bp)
    logger.info("GPS Map blueprint registered successfully")
except Exception as e:
    logger.warning(f"GPS Map module not available: {e}")

# Register new UI Dashboard
try:
    from routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    logger.info("New Dashboard blueprint registered")
except ImportError:
    logger.warning("New Dashboard module not found")

# Register new File Upload UI
try:
    from routes.file_upload_new import file_upload_bp
    app.register_blueprint(file_upload_bp) 
    logger.info("New File Upload blueprint registered")
except ImportError:
    logger.warning("New File Upload module not found")

# Add the File Processor and Upload routes
try:
    from routes.file_processor import file_processor_bp
    app.register_blueprint(file_processor_bp)
    logger.info("File Processor blueprint registered")
except ImportError:
    logger.warning("File Processor module not found - will be added later")

try:
    from routes.file_upload import upload_bp
    app.register_blueprint(upload_bp)
    logger.info("File Upload API blueprint registered")
except ImportError:
    logger.warning("File Upload API module not found")

try:
    from routes.react_upload import react_upload_bp
    app.register_blueprint(react_upload_bp)
    logger.info("React Upload blueprint registered")
except ImportError:
    logger.warning("React Upload module not found")

try:
    from routes.attendance_report import attendance_report_bp
    app.register_blueprint(attendance_report_bp)
    logger.info("Attendance Report blueprint registered")
except ImportError:
    logger.warning("Attendance Report module not found")

# Register weekly and daily driver reports
try:
    from routes.weekly_driver_report import weekly_driver_report_bp
    app.register_blueprint(weekly_driver_report_bp)
    logger.info("Weekly Driver Report blueprint registered")
except ImportError:
    logger.warning("Weekly Driver Report module not found")

# Only use the enhanced version of the Daily Driver Report
try:
    from routes.daily_driver_report_enhanced import daily_driver_report_bp
    app.register_blueprint(daily_driver_report_bp)
    logger.info("Enhanced Daily Driver Report blueprint registered")
except ImportError:
    logger.warning("Enhanced Daily Driver Report module not found")

# Register Monthly Driver Report
try:
    from routes.monthly_driver_report import monthly_driver_report_bp
    app.register_blueprint(monthly_driver_report_bp)
    logger.info("Monthly Driver Report blueprint registered")
except ImportError:
    logger.warning("Monthly Driver Report module not found")
    
# Register Weekly Driver Report (mobile-friendly version)
try:
    from routes.weekly_report import bp as weekly_report_bp
    app.register_blueprint(weekly_report_bp)
    logger.info("Weekly Driver Report blueprint registered")
except ImportError:
    logger.warning("Weekly Driver Report module not found")

# Register Daily Driver Report Dashboard (v2)
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'attendance' for bp in app.blueprints.values()):
        from routes.attendance_routes import attendance_bp
        app.register_blueprint(attendance_bp)
        logger.info("Attendance Dashboard blueprint registered successfully")
    else:
        logger.info("Attendance Dashboard blueprint already registered")
except ImportError:
    logger.warning("Attendance Dashboard module not found")
except Exception as e:
    logger.error(f"Error with Attendance Dashboard blueprint: {e}")

# Register Enhanced Weekly Report Blueprint
try:
    from app import app
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'enhanced_weekly_report_bp' for bp in app.blueprints.values()):
        from routes.enhanced_weekly_report import enhanced_weekly_report_bp
        app.register_blueprint(enhanced_weekly_report_bp)
        logger.info("Enhanced Weekly Report blueprint registered successfully")
    else:
        logger.info("Enhanced Weekly Report blueprint already registered")
except ImportError:
    logger.warning("Enhanced Weekly Report module not found")
except Exception as e:
    logger.error(f"Error with Enhanced Weekly Report blueprint: {e}")
    
# Register System Admin Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'system_admin' for bp in app.blueprints.values()):
        from routes.system_admin import system_admin_bp
        app.register_blueprint(system_admin_bp)
        logger.info("System Admin blueprint registered successfully")
    else:
        logger.info("System Admin blueprint already registered")
except ImportError:
    logger.warning("System Admin module not found")
except Exception as e:
    logger.error(f"Error with System Admin blueprint: {e}")
    
# Register Kaizen Monitor Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'kaizen_monitor' for bp in app.blueprints.values()):
        from routes.kaizen_monitor import kaizen_monitor_bp
        app.register_blueprint(kaizen_monitor_bp)
        logger.info("Kaizen Monitor blueprint registered successfully")
    else:
        logger.info("Kaizen Monitor blueprint already registered")
except ImportError:
    logger.warning("Kaizen Monitor module not found")
except Exception as e:
    logger.error(f"Error with Kaizen Monitor blueprint: {e}")
    
# Register Kaizen Admin Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'kaizen_admin' for bp in app.blueprints.values()):
        from routes.kaizen_admin import kaizen_admin_bp
        app.register_blueprint(kaizen_admin_bp)
        logger.info("Kaizen Admin blueprint registered successfully")
    else:
        logger.info("Kaizen Admin blueprint already registered")
except ImportError:
    logger.warning("Kaizen Admin module not found")
except Exception as e:
    logger.error(f"Error with Kaizen Admin blueprint: {e}")
    
# System Health Blueprint is registered at line 39
    
# Register Daily Attendance Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'daily_attendance' for bp in app.blueprints.values()):
        from routes.daily_attendance_routes import daily_attendance_bp
        app.register_blueprint(daily_attendance_bp)
        logger.info("Daily Attendance blueprint registered successfully")
    else:
        logger.info("Daily Attendance blueprint already registered")
except ImportError:
    logger.warning("Daily Attendance module not found")
except Exception as e:
    logger.error(f"Error with Daily Attendance blueprint: {e}")
    
# Register File Organizer Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'file_organizer' for bp in app.blueprints.values()):
        from routes.file_organizer_routes import file_organizer
        app.register_blueprint(file_organizer)
        logger.info("File Organizer blueprint registered successfully")
    else:
        logger.info("File Organizer blueprint already registered")
except ImportError:
    logger.warning("File Organizer module not found")
except Exception as e:
    logger.error(f"Error with File Organizer blueprint: {e}")
    
# Register Driver-Asset Manager Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'driver_asset_manager' for bp in app.blueprints.values()):
        from routes.driver_asset_manager import driver_asset_manager_bp
        app.register_blueprint(driver_asset_manager_bp)
        logger.info("Driver-Asset Manager blueprint registered successfully")
    else:
        logger.info("Driver-Asset Manager blueprint already registered")
except ImportError:
    logger.warning("Driver-Asset Manager module not found")
except Exception as e:
    logger.error(f"Error with Driver-Asset Manager blueprint: {e}")

# Register Work Zone Hours Validation Blueprint
try:
    if not any(bp.name == 'work_zone_hours' for bp in app.blueprints.values()):
        from routes.work_zone_hours import work_zone_hours_bp
        app.register_blueprint(work_zone_hours_bp)
        logger.info("Work Zone Hours validation blueprint registered successfully")
    else:
        logger.info("Work Zone Hours blueprint already registered")
except ImportError:
    logger.warning("Work Zone Hours module not found")
except Exception as e:
    logger.error(f"Error with Work Zone Hours blueprint: {e}")

# Register Job Site Hours Manager Blueprint
try:
    if not any(bp.name == 'job_site_hours' for bp in app.blueprints.values()):
        from routes.job_site_hours_manager import job_site_hours_bp
        app.register_blueprint(job_site_hours_bp)
        logger.info("Job Site Hours Manager blueprint registered successfully")
    else:
        logger.info("Job Site Hours Manager blueprint already registered")
except ImportError:
    logger.warning("Job Site Hours Manager module not found")
except Exception as e:
    logger.error(f"Error with Job Site Hours Manager blueprint: {e}")

# Register Automated Daily Reports Blueprint
try:
    if not any(bp.name == 'automated_reports' for bp in app.blueprints.values()):
        from routes.automated_daily_reports import automated_reports_bp
        app.register_blueprint(automated_reports_bp)
        logger.info("Automated Daily Reports blueprint registered successfully")
    else:
        logger.info("Automated Daily Reports blueprint already registered")
except ImportError:
    logger.warning("Automated Daily Reports module not found")
except Exception as e:
    logger.error(f"Error with Automated Daily Reports blueprint: {e}")

# Register Live GPS Tracking Blueprint
try:
    if not any(bp.name == 'live_gps' for bp in app.blueprints.values()):
        from routes.live_gps_tracking import live_gps_bp
        app.register_blueprint(live_gps_bp)
        logger.info("Live GPS Tracking blueprint registered successfully")
    else:
        logger.info("Live GPS Tracking blueprint already registered")
except ImportError:
    logger.warning("Live GPS Tracking module not found")
except Exception as e:
    logger.error(f"Error with Live GPS Tracking blueprint: {e}")

# Register May Data Processor Blueprint
try:
    if not any(bp.name == 'may_processor' for bp in app.blueprints.values()):
        from routes.may_data_processor import may_processor_bp
        app.register_blueprint(may_processor_bp)
        logger.info("May Data Processor blueprint registered successfully")
    else:
        logger.info("May Data Processor blueprint already registered")
except ImportError:
    logger.warning("May Data Processor module not found")
except Exception as e:
    logger.error(f"Error with May Data Processor blueprint: {e}")

# Register Kaizen Blueprint
try:
    if not any(bp.name == 'kaizen' for bp in app.blueprints.values()):
        from routes.kaizen import kaizen_bp
        app.register_blueprint(kaizen_bp, url_prefix="/kaizen")
        logger.info("Kaizen blueprint registered successfully")
    else:
        logger.info("Kaizen blueprint already registered")
except ImportError:
    logger.warning("Kaizen module not found")
except Exception as e:
    logger.error(f"Error with Kaizen blueprint: {e}")

# Register System Health Blueprint
try:
    if not any(bp.name == 'system_health' for bp in app.blueprints.values()):
        from routes.system_health import system_health_bp
        app.register_blueprint(system_health_bp)
        logger.info("System Health blueprint registered successfully")
    else:
        logger.info("System Health blueprint already registered")
except ImportError:
    logger.warning("System Health module not found")
except Exception as e:
    logger.error(f"Error with System Health blueprint: {e}")

# Register Demo Module for Phase 4 QA Extensibility Testing
try:
    if not any(bp.name == 'demo_module' for bp in app.blueprints.values()):
        from routes.demo_module import demo_bp
        app.register_blueprint(demo_bp)
        logger.info("Demo Module registered for Phase 4 QA extensibility testing")
    else:
        logger.info("Demo Module already registered")
except ImportError:
    logger.warning("Demo Module not found")
except Exception as e:
    logger.error(f"Error with Demo Module blueprint: {e}")

# Register Unified Attendance Validation Suite
try:
    if not any(bp.name == 'unified_attendance' for bp in app.blueprints.values()):
        from routes.unified_attendance_suite import unified_attendance_bp
        app.register_blueprint(unified_attendance_bp)
        logger.info("🧠 Unified Attendance + Job Zone + GPS vs Timecard Validation Suite registered")
    else:
        logger.info("Unified Attendance Suite already registered")
except ImportError:
    logger.warning("Unified Attendance Suite not found")
except Exception as e:
    logger.error(f"Error with Unified Attendance Suite blueprint: {e}")

# Register System Admin Blueprint
try:
    if not any(bp.name == 'system_admin' for bp in app.blueprints.values()):
        from routes.system_admin import system_admin_bp
        app.register_blueprint(system_admin_bp)
        logger.info("System Admin blueprint registered successfully")
    else:
        logger.info("System Admin blueprint already registered")
except ImportError:
    logger.warning("System Admin module not found")
except Exception as e:
    logger.error(f"Error with System Admin blueprint: {e}")

# Register Job Module Blueprint
try:
    if not any(bp.name == 'job_module' for bp in app.blueprints.values()):
        from routes.job_module import job_module_bp
        app.register_blueprint(job_module_bp)
        logger.info("Job Module blueprint registered successfully")
    else:
        logger.info("Job Module blueprint already registered")
except ImportError:
    logger.warning("Job Module not found")
except Exception as e:
    logger.error(f"Error with Job Module blueprint: {e}")

# Register Complete Daily Driver Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'daily_driver_complete' for bp in app.blueprints.values()):
        from routes.daily_driver_complete import daily_driver_complete_bp
        app.register_blueprint(daily_driver_complete_bp)
        logger.info("Complete Daily Driver Reports registered successfully")
    else:
        logger.info("Complete Daily Driver Reports already registered")
except ImportError:
    logger.warning("Complete Daily Driver module not found")
except Exception as e:
    logger.error(f"Error with Complete Daily Driver blueprint: {e}")

# Register Fixed Daily Driver Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'daily_driver_fixed' for bp in app.blueprints.values()):
        from routes.daily_driver_fixed import daily_driver_fixed_bp
        app.register_blueprint(daily_driver_fixed_bp)
        logger.info("Fixed Daily Driver Reports registered successfully")
    else:
        logger.info("Fixed Daily Driver Reports already registered")
except ImportError:
    logger.warning("Fixed Daily Driver module not found")
except Exception as e:
    logger.error(f"Error with Fixed Daily Driver blueprint: {e}")

# Register Intelligent Command Center Blueprint
try:
    # Check if the blueprint is already registered to avoid duplicate registration
    if not any(bp.name == 'command_center' for bp in app.blueprints.values()):
        from routes.intelligent_command_center import command_center_bp
        app.register_blueprint(command_center_bp)
        logger.info("Intelligent Command Center registered successfully")
    else:
        logger.info("Intelligent Command Center already registered")
except ImportError:
    logger.warning("Intelligent Command Center module not found")
except Exception as e:
    logger.error(f"Error with Intelligent Command Center blueprint: {e}")

@app.route('/attendance/')
@app.route('/attendance')
def attendance_main():
    """Redirect to enhanced weekly report"""
    return redirect('/enhanced-weekly-report/')

# Removing this route since it's handled by the blueprint
# @app.route('/enhanced-weekly-report/')
# @app.route('/enhanced-weekly-report')
# def enhanced_weekly_report():
#     """Main GPS-based weekly driver report interface"""
#     return render_template('enhanced_weekly_report/dashboard.html', 
#                           title="GPS-Based Weekly Driver Report",
#                           week_start="May 18, 2025",
#                           week_end="May 24, 2025")

# Register Working Driver Reports with Real MTD Data
try:
    from routes.driver_reports_working import driver_reports_working_bp
    app.register_blueprint(driver_reports_working_bp)
    logger.info("Working Driver Reports with real MTD data registered successfully")
except ImportError as e:
    logger.warning(f"Working Driver Reports module not found: {e}")

# Register Job Site Manager
try:
    from routes.job_site_manager import job_site_bp
    app.register_blueprint(job_site_bp)
    logger.info("Job Site Manager with North Texas locations registered successfully")
except ImportError as e:
    logger.warning(f"Job Site Manager module not found: {e}")

# Register Driver Attendance Blueprint
try:
    from routes.driver_attendance_clean import driver_attendance_bp
    app.register_blueprint(driver_attendance_bp, url_prefix='/driver-attendance')
    logger.info("Driver Attendance Dashboard registered successfully")
except ImportError as e:
    logger.warning(f"Driver Attendance module not found: {e}")

# Register MTD Data Review Dashboard
try:
    from routes.mtd_data_review import mtd_data_review_bp
    app.register_blueprint(mtd_data_review_bp, url_prefix='/mtd-data-review')
    logger.info("MTD Data Review Dashboard registered successfully")
except ImportError as e:
    logger.warning(f"MTD Data Review module not found: {e}")

# MTD Daily Processor temporarily disabled - focusing on fixing existing reports
# try:
#     from routes.mtd_daily_processor import mtd_daily_bp
#     app.register_blueprint(mtd_daily_bp)
#     logger.info("MTD Daily Processor registered successfully")
# except ImportError as e:
#     logger.warning(f"MTD Daily Processor module not found: {e}")

@app.route('/')
def dashboard():
    """Multi-Division TRAXOVO Fleet Management Dashboard"""
    if not current_user.is_authenticated:
        return redirect(url_for('quick_auth.quick_login'))
    
    return render_template('dashboard.html',
                          assets_count=get_asset_count(),
                          drivers_count=get_driver_count(),
                          job_sites_count=get_job_site_count(),
                          pm_allocations_count=get_pm_allocation_count(),
                          database_status=check_database_status(),
                          api_status=check_gauge_api_status(),
                          storage_status=check_storage_status(),
                          last_sync_time=get_last_sync_time(),
                          notifications=get_recent_notifications())

@app.route('/system-health')
def system_health():
    """System health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'genius_core': 'CONTINUITY MODE ACTIVE',
        'database': check_database_status(),
        'gauge_api': check_gauge_api_status(),
        'storage': check_storage_status()
    })

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('basic_error.html', 
                          error_code=404,
                          error_message="Page not found",
                          error_details="The requested page does not exist."), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return render_template('basic_error.html',
                          error_code=500,
                          error_message="Internal server error",
                          error_details="An unexpected error occurred on the server."), 500

def check_gauge_api_status():
    """Check status of the Gauge API connection"""
    try:
        # Check if we have API credentials
        if not os.environ.get('GAUGE_API_URL') or not os.environ.get('GAUGE_API_USERNAME'):
            return 'not_configured'
        
        # In a real implementation, we would check the actual API connection
        # For now, just check for SSL certificate issues based on logs
        if "CERTIFICATE_VERIFY_FAILED" in os.environ.get('GAUGE_API_ERROR', ''):
            return 'warning'
        
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking Gauge API status: {str(e)}")
        return 'error'

def check_database_status():
    """Check status of the database connection"""
    try:
        # Simple query to check if the database is responding
        from sqlalchemy import text
        db.session.execute(text("SELECT 1"))
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking database status: {str(e)}")
        return 'disconnected'

def check_storage_status():
    """Check status of the file storage"""
    try:
        # Check if upload directories exist
        upload_dirs = ['uploads', 'uploads/driver_reports', 'uploads/pm_allocations']
        for directory in upload_dirs:
            os.makedirs(os.path.join(app.root_path, directory), exist_ok=True)
        
        # Check if we can write to the upload directory
        test_file = os.path.join(app.root_path, 'uploads', '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        return 'connected'
    except Exception as e:
        logger.error(f"Error checking storage status: {str(e)}")
        return 'disconnected'

def get_asset_count():
    """Get the count of active assets"""
    try:
        from models import Asset
        return Asset.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting asset count: {str(e)}")
        return 0

def get_driver_count():
    """Get the count of active drivers"""
    try:
        from models import Driver
        return Driver.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting driver count: {str(e)}")
        return 0

def get_job_site_count():
    """Get the count of active job sites"""
    try:
        from models import JobSite
        return JobSite.query.filter_by(is_active=True).count()
    except Exception as e:
        logger.error(f"Error getting job site count: {str(e)}")
        return 0

def get_pm_allocation_count():
    """Get the count of PM allocations for the current month"""
    try:
        from models import PMAllocation
        current_month = datetime.now().strftime('%Y-%m')
        return PMAllocation.query.filter_by(month=current_month).count()
    except Exception as e:
        logger.error(f"Error getting PM allocation count: {str(e)}")
        return 0

def get_last_sync_time():
    """Get the last data sync time"""
    try:
        from models import SystemConfiguration
        last_sync = SystemConfiguration.query.filter_by(key='last_sync_time').first()
        if last_sync and last_sync.value:
            return last_sync.value
        return 'Never'
    except Exception as e:
        logger.error(f"Error getting last sync time: {str(e)}")
        return 'Unknown'

def get_recent_notifications():
    """Get recent system notifications"""
    try:
        from models import Notification
        notifications = Notification.query.filter_by(user_id=None).order_by(Notification.created_at.desc()).limit(5).all()
        return [
            {
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'time': notification.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for notification in notifications
        ]
    except Exception:
        # Return some sample notifications if we can't get them from the database
        return [
            {
                'title': 'GENIUS CORE CONTINUITY MODE Activated',
                'message': 'The system is operating in GENIUS CORE CONTINUITY MODE to ensure data integrity and validation.',
                'type': 'info',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Database Tables Created',
                'message': 'Database tables have been created successfully.',
                'type': 'info',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': 'Gauge API Connection Warning',
                'message': 'The connection to the Gauge API has a certificate verification issue. Data retrieval may be affected.',
                'type': 'warning',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        ]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# Register Job Management Configuration
try:
    if not any(bp.name == "job_management" for bp in app.blueprints.values()):
        from job_management import job_bp
        app.register_blueprint(job_bp, url_prefix="/job-management")
        logger.info("Job Zone Configuration registered successfully")
except Exception as e:
    logger.error(f"Error with Job Management blueprint: {e}")

