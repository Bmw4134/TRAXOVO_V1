"""
Email Sending Utility

This module handles sending email reports through SendGrid.
"""
import logging
import os
from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId

# Configure logging
logger = logging.getLogger(__name__)

# Email configuration constants
DEFAULT_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@traxora.app')
BCC_RECIPIENTS = [email.strip() for email in os.environ.get('SENDGRID_BCC_EMAILS', '').split(',') if email.strip()]
DEFAULT_RECIPIENTS = [email.strip() for email in os.environ.get('SENDGRID_DEFAULT_RECIPIENTS', '').split(',') if email.strip()]

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
    if recipients is None:
        recipients = DEFAULT_RECIPIENTS
    
    if from_email is None:
        from_email = DEFAULT_FROM_EMAIL
        
    if bcc_recipients is None:
        bcc_recipients = BCC_RECIPIENTS
    
    # Check if we have at least one recipient
    if not recipients and not bcc_recipients:
        logger.error("No recipients specified for email")
        return False, "No recipients specified"
    
    # Build the email message
    message = Mail(
        from_email=from_email,
        to_emails=recipients,
        subject=subject,
        html_content=html_content
    )
    
    # Add BCC recipients
    for bcc in bcc_recipients:
        message.add_bcc(bcc)
    
    # Add attachment if provided
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, 'rb') as f:
                file_content = f.read()
                
            encoded_file = FileContent(file_content)
            file_name = FileName(os.path.basename(attachment_path))
            file_type = FileType(get_file_type(attachment_path))
            disposition = Disposition('attachment')
            content_id = ContentId('attachment_1')
            
            attachment = Attachment(
                encoded_file, file_name, file_type, disposition, content_id
            )
            message.add_attachment(attachment)
        except Exception as e:
            logger.error(f"Error adding attachment: {e}")
    
    try:
        # Attempt to send the email
        sg_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sg_api_key:
            logger.error("SendGrid API key not found in environment variables")
            return False, "SendGrid API key not configured"
        
        sg = SendGridAPIClient(sg_api_key)
        response = sg.send(message)
        
        # Log the response
        status_code = response.status_code
        logger.info(f"Email sent with status code: {status_code}")
        
        if status_code >= 200 and status_code < 300:
            return True, f"Email sent successfully ({status_code})"
        else:
            return False, f"Failed to send email, status code: {status_code}"
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False, f"Error sending email: {str(e)}"

def get_file_type(file_path):
    """
    Get the MIME type of a file based on its extension
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: MIME type string
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    mime_types = {
        '.pdf': 'application/pdf',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif'
    }
    
    return mime_types.get(file_extension, 'application/octet-stream')

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
    # Create HTML version of the report
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #0056b3; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>{subject}</h1>
            <div>{report_content}</div>
            <p style="margin-top: 20px; font-size: 12px; color: #666;">
                This email was automatically generated by the TRAXORA Fleet Management System.
                Please do not reply to this email.
            </p>
        </body>
    </html>
    """
    
    return send_email(subject, html_content, recipients)