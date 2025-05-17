"""
Email Engine for TRAXORA

This module handles all email automation capabilities including:
- Report scheduling and delivery
- Alert notifications
- Timecard discrepancy notifications
- Daily attendance summaries
"""
import os
import logging
from datetime import datetime, timedelta
import schedule
import threading
import time
from flask import render_template
from flask_mail import Mail, Message
from app import create_app

# Initialize Flask app and mail
app = create_app()
mail = Mail(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email configuration
DEFAULT_SENDER = 'reports@traxora.com'
REPORT_RECIPIENTS = {}  # Will be populated from database

def send_email(subject, recipients, template, **kwargs):
    """
    Send an email using the provided template and context variables
    
    Args:
        subject (str): Email subject
        recipients (list): List of email addresses
        template (str): Template file path
        **kwargs: Context variables for the template
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        with app.app_context():
            msg = Message(
                subject=subject,
                sender=DEFAULT_SENDER,
                recipients=recipients
            )
            
            # Render HTML and text versions
            msg.html = render_template(f'emails/{template}.html', **kwargs)
            msg.body = render_template(f'emails/{template}.txt', **kwargs)
            
            # Send the email
            mail.send(msg)
            
            logger.info(f"Email sent: {subject} to {', '.join(recipients)}")
            return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def attach_report_file(msg, report_path, report_name=None):
    """
    Attach a report file to an email message
    
    Args:
        msg (Message): Email message object
        report_path (str): Path to the report file
        report_name (str, optional): Custom name for the attachment
        
    Returns:
        bool: True if file was attached successfully, False otherwise
    """
    try:
        if not report_name:
            report_name = os.path.basename(report_path)
            
        with open(report_path, 'rb') as f:
            msg.attach(
                report_name,
                'application/octet-stream',
                f.read()
            )
        return True
    except Exception as e:
        logger.error(f"Failed to attach report file: {str(e)}")
        return False

def load_report_recipients():
    """
    Load report recipients from the database
    
    This function populates the REPORT_RECIPIENTS dictionary with
    email addresses for different report types from the database.
    """
    from models import ReportSubscription, User, Organization
    
    with app.app_context():
        subscriptions = ReportSubscription.query.filter_by(active=True).all()
        
        # Group by report type
        for subscription in subscriptions:
            report_type = subscription.report_type
            
            if report_type not in REPORT_RECIPIENTS:
                REPORT_RECIPIENTS[report_type] = []
                
            # Add email if it's not already in the list
            if subscription.email and subscription.email not in REPORT_RECIPIENTS[report_type]:
                REPORT_RECIPIENTS[report_type].append(subscription.email)
            
            # Add user email if available
            if subscription.user_id:
                user = User.query.get(subscription.user_id)
                if user and user.email and user.email not in REPORT_RECIPIENTS[report_type]:
                    REPORT_RECIPIENTS[report_type].append(user.email)

# Report generation functions
def generate_daily_attendance_report():
    """Generate and email the daily attendance report"""
    from utils.report_generator import create_attendance_report
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_path = create_attendance_report(report_date)
    
    if not report_path:
        logger.error(f"Failed to generate attendance report for {report_date}")
        return False
    
    recipients = REPORT_RECIPIENTS.get('daily_attendance', [])
    if not recipients:
        logger.warning("No recipients configured for daily attendance report")
        return False
    
    subject = f"TRAXORA Daily Attendance Report - {report_date}"
    
    with app.app_context():
        msg = Message(
            subject=subject,
            sender=DEFAULT_SENDER,
            recipients=recipients
        )
        
        msg.html = render_template(
            'emails/daily_attendance_report.html',
            report_date=report_date
        )
        
        msg.body = f"Daily Attendance Report for {report_date} is attached."
        
        attach_report_file(msg, report_path)
        mail.send(msg)
    
    logger.info(f"Daily attendance report sent to {len(recipients)} recipients")
    return True

def generate_job_zone_hours_report():
    """Generate and email the job zone hours report"""
    from utils.report_generator import create_job_zone_hours_report
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_path = create_job_zone_hours_report(report_date)
    
    if not report_path:
        logger.error(f"Failed to generate job zone hours report for {report_date}")
        return False
    
    recipients = REPORT_RECIPIENTS.get('job_zone_hours', [])
    if not recipients:
        logger.warning("No recipients configured for job zone hours report")
        return False
    
    subject = f"TRAXORA Job Zone Hours Report - {report_date}"
    
    with app.app_context():
        msg = Message(
            subject=subject,
            sender=DEFAULT_SENDER,
            recipients=recipients
        )
        
        msg.html = render_template(
            'emails/job_zone_hours_report.html',
            report_date=report_date
        )
        
        msg.body = f"Job Zone Hours Report for {report_date} is attached."
        
        attach_report_file(msg, report_path)
        mail.send(msg)
    
    logger.info(f"Job zone hours report sent to {len(recipients)} recipients")
    return True

def generate_pm_billing_report():
    """Generate and email the PM billing report"""
    from utils.report_generator import create_pm_billing_report
    
    # Get the previous month for the report
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    month_str = last_month.strftime("%B %Y")
    
    report_path = create_pm_billing_report(last_month)
    
    if not report_path:
        logger.error(f"Failed to generate PM billing report for {month_str}")
        return False
    
    recipients = REPORT_RECIPIENTS.get('pm_billing', [])
    if not recipients:
        logger.warning("No recipients configured for PM billing report")
        return False
    
    subject = f"TRAXORA PM Billing Report - {month_str}"
    
    with app.app_context():
        msg = Message(
            subject=subject,
            sender=DEFAULT_SENDER,
            recipients=recipients
        )
        
        msg.html = render_template(
            'emails/pm_billing_report.html',
            month=month_str
        )
        
        msg.body = f"PM Billing Report for {month_str} is attached."
        
        attach_report_file(msg, report_path)
        mail.send(msg)
    
    logger.info(f"PM billing report sent to {len(recipients)} recipients")
    return True

# Schedule configuration
def configure_scheduled_reports():
    """Configure all scheduled reports"""
    # Daily attendance report at 6:00 AM
    schedule.every().day.at("06:00").do(generate_daily_attendance_report)
    
    # Weekly job zone hours report on Monday at 7:00 AM
    schedule.every().monday.at("07:00").do(generate_job_zone_hours_report)
    
    # Monthly PM billing report on the 1st of each month at 8:00 AM
    schedule.every().month.at("08:00").do(generate_pm_billing_report)
    
    logger.info("Scheduled reports configured")

# Scheduler thread
def run_scheduler():
    """Run the scheduler in a background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def start_scheduler():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Thread will exit when the main thread exits
    scheduler_thread.start()
    logger.info("Email scheduler started")

def init_email_engine():
    """Initialize the email engine"""
    # Load report recipients
    load_report_recipients()
    
    # Configure scheduled reports
    configure_scheduled_reports()
    
    # Start the scheduler
    start_scheduler()
    
    logger.info("Email engine initialized")