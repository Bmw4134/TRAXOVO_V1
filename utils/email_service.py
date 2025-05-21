"""
Email Service

This module handles sending emails with daily driver reports and attachments
using SendGrid API.
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId, Email, To, Content
)
import base64
import mimetypes

# Set up logging
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('logs/email_service.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# Default recipients
DEFAULT_RECIPIENTS = [
    'bm.watson34@gmail.com', 
    'bwatson@ragleinc.com'
]

def send_daily_report_email(date_str, recipients=None):
    """
    Send daily driver report email with attachments
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        recipients (list): List of email addresses to send to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Use default recipients if none provided
        if not recipients:
            recipients = DEFAULT_RECIPIENTS
            
        # Format date for display
        display_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%B %d, %Y')
        
        # Check if report files exist
        report_dir = Path('reports/daily_drivers')
        json_file = report_dir / f'daily_report_{date_str}.json'
        excel_file = report_dir / f'daily_report_{date_str}.xlsx'
        
        if not json_file.exists() or not excel_file.exists():
            logger.error(f"Report files not found for {date_str}")
            return False
            
        # Load report data
        with open(json_file, 'r') as f:
            report_data = json.load(f)
            
        # Create email summary
        summary = report_data.get('summary', {})
        total = summary.get('total', 0)
        late = summary.get('late', 0)
        early_end = summary.get('early_end', 0)
        not_on_job = summary.get('not_on_job', 0)
        on_time = summary.get('on_time', 0)
        
        late_pct = (late / total) * 100 if total > 0 else 0
        early_end_pct = (early_end / total) * 100 if total > 0 else 0
        not_on_job_pct = (not_on_job / total) * 100 if total > 0 else 0
        on_time_pct = (on_time / total) * 100 if total > 0 else 0
        
        # Create email content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .late {{ color: #cc0000; }}
                .early-end {{ color: #ff9900; }}
                .not-on-job {{ color: #cc0000; }}
                .on-time {{ color: #008000; }}
                .summary {{ font-weight: bold; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Daily Driver Report: {display_date}</h2>
                
                <div class="summary">
                    <p>Total Drivers: {total}</p>
                    <p class="late">Late: {late} ({late_pct:.1f}%)</p>
                    <p class="early-end">Early End: {early_end} ({early_end_pct:.1f}%)</p>
                    <p class="not-on-job">Not On Job: {not_on_job} ({not_on_job_pct:.1f}%)</p>
                    <p class="on-time">On Time: {on_time} ({on_time_pct:.1f}%)</p>
                </div>
                
                <p>Please see the attached Excel file for the detailed report.</p>
                
                <p>This is an automated email from the TRAXORA Daily Driver Report system.</p>
            </div>
        </body>
        </html>
        """
        
        # Create message
        message = Mail(
            from_email=Email('traxora-reports@ragleinc.com', 'TRAXORA Reports'),
            subject=f'Daily Driver Report: {display_date}',
            html_content=Content('text/html', html_content)
        )
        
        # Add recipients
        for recipient in recipients:
            message.add_to(To(recipient))
            
        # Attach Excel file
        with open(excel_file, 'rb') as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
            attachment = Attachment()
            attachment.file_content = FileContent(encoded)
            attachment.file_type = FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            attachment.file_name = FileName(f'Daily_Driver_Report_{date_str}.xlsx')
            attachment.disposition = Disposition('attachment')
            attachment.content_id = ContentId('Excel Report')
            message.add_attachment(attachment)
        
        # Send email
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Email sent successfully for {date_str} to {', '.join(recipients)}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.body}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def validate_email_recipients(recipients_str):
    """
    Validate and parse email recipients from a comma-separated string
    
    Args:
        recipients_str (str): Comma-separated list of email addresses
        
    Returns:
        list: List of valid email addresses
    """
    if not recipients_str:
        return []
        
    # Split by comma and strip whitespace
    candidates = [email.strip() for email in recipients_str.split(',')]
    
    # Basic validation (could be enhanced with regex or email_validator)
    valid_emails = []
    for email in candidates:
        if '@' in email and '.' in email.split('@')[1]:
            valid_emails.append(email)
        else:
            logger.warning(f"Invalid email address: {email}")
    
    return valid_emails