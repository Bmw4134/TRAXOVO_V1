"""
Email Service Module

This module handles email delivery for the attendance reports
using SendGrid as the email service provider.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/email_service.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Load SendGrid API key from environment
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

def get_user_email_config(user_id=None):
    """
    Get user's email configuration
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Email configuration
    """
    # Create config directory if it doesn't exist
    config_dir = 'config'
    os.makedirs(config_dir, exist_ok=True)
    
    # Default configuration
    default_config = {
        'recipients': 'team@ragleinc.com',
        'cc': '',
        'bcc': '',
        'subject_prefix': 'Daily Driver Report',
        'include_pdf': True,
        'include_excel': True
    }
    
    # User-specific configuration path
    config_path = os.path.join(config_dir, f"email_config_{user_id or 'default'}.json")
    
    # Load existing configuration if available
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                
            # Merge with default config to ensure all fields are present
            for key in default_config:
                if key not in user_config:
                    user_config[key] = default_config[key]
                    
            return user_config
        
        except Exception as e:
            logger.error(f"Error loading email configuration: {e}")
            return default_config
    
    # Save default configuration if not exists
    try:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    except Exception as e:
        logger.error(f"Error saving default email configuration: {e}")
        return default_config

def save_user_email_config(config, user_id=None):
    """
    Save user's email configuration
    
    Args:
        config (dict): Email configuration
        user_id (str): User ID
        
    Returns:
        bool: Success status
    """
    # Create config directory if it doesn't exist
    config_dir = 'config'
    os.makedirs(config_dir, exist_ok=True)
    
    # User-specific configuration path
    config_path = os.path.join(config_dir, f"email_config_{user_id or 'default'}.json")
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Saved email configuration for user {user_id or 'default'}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving email configuration: {e}")
        return False

def send_email(to_emails, subject, html_content, cc_emails=None, bcc_emails=None, attachments=None):
    """
    Send an email using SendGrid
    
    Args:
        to_emails (str or list): Recipient email address(es)
        subject (str): Email subject
        html_content (str): Email content in HTML format
        cc_emails (str or list): CC email address(es)
        bcc_emails (str or list): BCC email address(es)
        attachments (list): List of attachment dictionaries
        
    Returns:
        dict: Email delivery status
    """
    # Check if SendGrid API key is available
    if not SENDGRID_API_KEY:
        error_msg = "SendGrid API key not found in environment variables. Cannot send email."
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }
    
    try:
        # Prepare recipient list
        if isinstance(to_emails, str):
            to_emails = [email.strip() for email in to_emails.split(',') if email.strip()]
        
        # Prepare CC list
        if cc_emails:
            if isinstance(cc_emails, str):
                cc_emails = [email.strip() for email in cc_emails.split(',') if email.strip()]
        else:
            cc_emails = []
        
        # Prepare BCC list
        if bcc_emails:
            if isinstance(bcc_emails, str):
                bcc_emails = [email.strip() for email in bcc_emails.split(',') if email.strip()]
        else:
            bcc_emails = []
        
        # Check if we have any recipients
        if not to_emails:
            logger.warning("No recipients specified, email not sent")
            return {
                'success': False,
                'message': "No recipients specified"
            }
        
        # Initialize SendGrid client
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Set up from email
        from_email = Email("telematics@ragleinc.com", "Ragle Fleet Telematics")
        
        # Create personalization for each recipient
        personalization_list = []
        for to_email in to_emails:
            mail = Mail(
                from_email=from_email,
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Add CC recipients if any
            for cc_email in cc_emails:
                mail.cc = To(cc_email)
            
            # Add BCC recipients if any
            for bcc_email in bcc_emails:
                mail.bcc = To(bcc_email)
            
            # Add attachments if any
            if attachments:
                for attachment_data in attachments:
                    attachment = Attachment()
                    
                    if 'content' in attachment_data:
                        # Base64 content
                        attachment.file_content = FileContent(attachment_data['content'])
                    elif 'path' in attachment_data:
                        # File path
                        with open(attachment_data['path'], 'rb') as f:
                            content = f.read()
                            attachment.file_content = FileContent(content)
                    else:
                        continue
                    
                    # Set attachment properties
                    attachment.file_name = FileName(attachment_data.get('filename', 'attachment'))
                    attachment.file_type = FileType(attachment_data.get('type', 'application/octet-stream'))
                    attachment.disposition = Disposition(attachment_data.get('disposition', 'attachment'))
                    
                    mail.attachment = attachment
            
            personalization_list.append(mail)
        
        # Send emails
        responses = []
        for mail in personalization_list:
            response = sg.send(mail)
            responses.append({
                'status_code': response.status_code,
                'body': response.body.decode() if response.body else None,
                'headers': dict(response.headers)
            })
        
        logger.info(f"Sent email to {len(to_emails)} recipients with subject: {subject}")
        return {
            'success': True,
            'responses': responses
        }
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': str(e)
        }

def email_daily_report(date_str, email_config=None, user_id=None):
    """
    Email the daily driver report for a specific date
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        email_config (dict): Email configuration
        user_id (str): User ID
        
    Returns:
        dict: Email delivery status
    """
    try:
        # Get email configuration if not provided
        if not email_config:
            email_config = get_user_email_config(user_id)
        
        # Load report data
        report_path = f"exports/daily_reports/daily_report_{date_str}.json"
        
        if not os.path.exists(report_path):
            logger.error(f"Report not found for {date_str}")
            return {
                'success': False,
                'message': f"Report not found for {date_str}"
            }
        
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Parse date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Prepare email subject
        subject = f"{email_config.get('subject_prefix', 'Daily Driver Report')} - {formatted_date}"
        
        # Build email content
        html_content = generate_email_html(report_data, date_str)
        
        # Prepare attachments
        attachments = []
        
        # Add PDF attachment if enabled and available
        if email_config.get('include_pdf', True) and report_data.get('files', {}).get('pdf_exists', False):
            pdf_path = os.path.join('exports', report_data['files']['pdf_path'])
            
            if os.path.exists(pdf_path):
                attachments.append({
                    'path': pdf_path,
                    'filename': f"daily_report_{date_str}.pdf",
                    'type': 'application/pdf',
                    'disposition': 'attachment'
                })
        
        # Add Excel attachment if enabled and available
        if email_config.get('include_excel', True) and report_data.get('files', {}).get('excel_exists', False):
            excel_path = os.path.join('exports', report_data['files']['excel_path'])
            
            if os.path.exists(excel_path):
                attachments.append({
                    'path': excel_path,
                    'filename': f"daily_report_{date_str}.xlsx",
                    'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'disposition': 'attachment'
                })
        
        # Send email
        result = send_email(
            to_emails=email_config.get('recipients', ''),
            subject=subject,
            html_content=html_content,
            cc_emails=email_config.get('cc', ''),
            bcc_emails=email_config.get('bcc', ''),
            attachments=attachments
        )
        
        if result.get('success', False):
            logger.info(f"Successfully sent daily report email for {date_str}")
        else:
            logger.error(f"Failed to send daily report email for {date_str}: {result.get('message', 'Unknown error')}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error emailing daily report for {date_str}: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': str(e)
        }

def generate_email_html(report_data, date_str):
    """
    Generate HTML content for the daily report email
    
    Args:
        report_data (dict): Report data
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        str: HTML content
    """
    # Parse date
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%A, %B %d, %Y')
    
    # Extract summary counts
    total_drivers = report_data['summary']['total_drivers']
    on_time_drivers = report_data['summary']['on_time_drivers']
    late_drivers = report_data['summary']['late_drivers']
    early_end_drivers = report_data['summary']['early_end_drivers']
    not_on_job_drivers = report_data['summary']['not_on_job_drivers']
    
    # Calculate success rate
    success_rate = (on_time_drivers / total_drivers * 100) if total_drivers > 0 else 0
    
    # Generate summary HTML
    summary_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr style="background-color: #f2f2f2;">
            <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Metric</th>
            <th style="text-align: right; padding: 8px; border: 1px solid #ddd;">Count</th>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Total Drivers</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{total_drivers}</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">On Time</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{on_time_drivers}</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Late Arrivals</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{late_drivers}</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Early Departures</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{early_end_drivers}</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Not On Job</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{not_on_job_drivers}</td>
        </tr>
        <tr>
            <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">Success Rate</td>
            <td style="text-align: right; padding: 8px; border: 1px solid #ddd;">{success_rate:.1f}%</td>
        </tr>
    </table>
    """
    
    # Generate issue tables if there are issues
    issue_tables = ""
    
    # Late drivers table
    if late_drivers > 0 and 'late_drivers' in report_data:
        late_table = """
        <h3 style="color: #ff9900;">Late Arrivals</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Scheduled Start</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Actual Start</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Minutes Late</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
            </tr>
        """
        
        for driver in report_data['late_drivers']:
            late_table += f"""
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('name', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('scheduled_start', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('arrival', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('minutes_late', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('job_site', 'N/A')}</td>
            </tr>
            """
        
        late_table += "</table>"
        issue_tables += late_table
    
    # Early end drivers table
    if early_end_drivers > 0 and 'early_end_drivers' in report_data:
        early_table = """
        <h3 style="color: #3399ff;">Early Departures</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Scheduled End</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Actual End</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Minutes Early</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
            </tr>
        """
        
        for driver in report_data['early_end_drivers']:
            early_table += f"""
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('name', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('scheduled_end', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('departure', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('minutes_early', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('job_site', 'N/A')}</td>
            </tr>
            """
        
        early_table += "</table>"
        issue_tables += early_table
    
    # Not on job drivers table
    if not_on_job_drivers > 0 and 'not_on_job_drivers' in report_data:
        noj_table = """
        <h3 style="color: #ff3333;">Not On Job</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Driver</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Asset</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Job Site</th>
                <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">Reason</th>
            </tr>
        """
        
        for driver in report_data['not_on_job_drivers']:
            noj_table += f"""
            <tr>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('name', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('asset', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('job_site', 'N/A')}</td>
                <td style="text-align: left; padding: 8px; border: 1px solid #ddd;">{driver.get('status_reason', 'Unknown')}</td>
            </tr>
            """
        
        noj_table += "</table>"
        issue_tables += noj_table
    
    # Build complete HTML
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #0056b3; margin-bottom: 20px; }}
                h2 {{ color: #0056b3; margin-top: 30px; margin-bottom: 10px; }}
                h3 {{ margin-top: 20px; margin-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .summary {{ margin-bottom: 30px; }}
                .note {{ color: #666; font-style: italic; }}
            </style>
        </head>
        <body>
            <h1>Daily Driver Report - {formatted_date}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                {summary_html}
            </div>
            
            {issue_tables}
            
            <div class="note">
                <p>This report is generated automatically by the TRAXORA Fleet Management System.</p>
                <p>For questions or assistance, please contact the Fleet Management team.</p>
            </div>
        </body>
    </html>
    """
    
    return html_content