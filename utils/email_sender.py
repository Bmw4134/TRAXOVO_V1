"""
Email Sending Utility

This module handles sending email reports through SendGrid.
"""
import os
import logging
import traceback
import base64
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, FileContent, 
    FileName, FileType, Disposition, ContentId
)

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get API key from environment variables
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'fleet-reports@systemsmith.com')
DEFAULT_RECIPIENTS = [
    'william.rather@systemsmith.com'  # Default recipient for testing
]
BCC_RECIPIENTS = [
    'admin@systemsmith.com',
    'archives@systemsmith.com'
]

def send_email(subject, html_content, recipients=None, from_email=None, bcc_recipients=None, attachment_path=None):
    """
    Send an email using SendGrid API
    
    Args:
        subject (str): Email subject
        html_content (str): Email content in HTML format
        recipients (list, optional): List of recipient email addresses. Defaults to DEFAULT_RECIPIENTS.
        from_email (str, optional): Sender email address. Defaults to DEFAULT_FROM_EMAIL.
        bcc_recipients (list, optional): List of BCC recipients. Defaults to BCC_RECIPIENTS.
        attachment_path (str, optional): Path to file to attach to the email.
    
    Returns:
        tuple: (success, message)
    """
    if not SENDGRID_API_KEY:
        error_msg = "SendGrid API key not found in environment variables"
        logger.error(error_msg)
        
        # Save email to file instead as a fallback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        email_file = f'data/unsent_emails/email_{timestamp}.html'
        
        os.makedirs('data/unsent_emails', exist_ok=True)
        
        with open(email_file, 'w') as f:
            f.write(f"Subject: {subject}\n\n")
            f.write(html_content)
        
        logger.info(f"Email saved to file: {email_file}")
        return (False, f"{error_msg} - Email saved to file: {email_file}")
    
    from_email = from_email or DEFAULT_FROM_EMAIL
    recipients = recipients or DEFAULT_RECIPIENTS
    bcc_recipients = bcc_recipients or BCC_RECIPIENTS
    
    # Convert plain text to HTML if needed
    if not html_content.strip().startswith('<'):
        # Convert line breaks to <br> tags
        html_content = html_content.replace('\n', '<br>')
        html_content = f"<pre>{html_content}</pre>"
    
    try:
        message = Mail(
            from_email=Email(from_email),
            subject=subject
        )
        
        # Add recipients
        for recipient in recipients:
            message.add_to(To(recipient))
        
        # Add BCC recipients
        for bcc in bcc_recipients:
            message.add_bcc(bcc)
        
        # Add content
        message.add_content(Content("text/html", html_content))
        
        # Send email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        # Check response
        if response.status_code in (200, 201, 202):
            success_msg = f"Email sent successfully to {', '.join(recipients)}"
            logger.info(success_msg)
            return (True, success_msg)
        else:
            error_msg = f"Failed to send email. Status code: {response.status_code}"
            logger.error(error_msg)
            return (False, error_msg)
            
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        logger.error(error_msg)
        logger.debug(traceback.format_exc())
        
        # Save email to file as a fallback
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        email_file = f'data/unsent_emails/email_{timestamp}.html'
        
        os.makedirs('data/unsent_emails', exist_ok=True)
        
        with open(email_file, 'w') as f:
            f.write(f"Subject: {subject}\n\n")
            f.write(html_content)
        
        logger.info(f"Email saved to file: {email_file}")
        return (False, f"{error_msg} - Email saved to file: {email_file}")

def send_report_email(subject, report_content, recipients=None):
    """
    Send a report email
    
    Args:
        subject (str): Email subject
        report_content (str): Report content in text format
        recipients (list, optional): List of recipient email addresses. Defaults to DEFAULT_RECIPIENTS.
    
    Returns:
        tuple: (success, message)
    """
    # Format the plain text report as HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333; }}
            pre {{ background-color: #f8f8f8; padding: 10px; border-radius: 5px; white-space: pre-wrap; }}
            .header {{ background-color: #283478; color: white; padding: 10px; }}
            .footer {{ background-color: #f1f1f1; padding: 10px; font-size: 12px; color: #666; text-align: center; }}
            .flagged {{ color: #a94442; }}
            .summary {{ margin: 15px 0; padding: 15px; background-color: #f9f9f9; border-left: 5px solid #283478; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{subject}</h2>
        </div>
        <div class="content">
            <pre>{report_content}</pre>
        </div>
        <div class="footer">
            <p>This is an automated report from the SYSTEMSMITH FLEET INTELLIGENCE SYSTEM.</p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(subject, html_content, recipients)

# Testing function
if __name__ == "__main__":
    # Test email sending
    success, message = send_report_email(
        subject="TEST REPORT: Fleet Intelligence System",
        report_content="This is a test report.\n\nAll systems operational.",
        recipients=["test@example.com"]
    )
    
    print(f"Email sending {'succeeded' if success else 'failed'}: {message}")