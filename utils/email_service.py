"""
Email Service Module

This module provides email sending functionality using SendGrid.
"""
import os
import base64
import logging
import sys
from typing import List, Optional, Dict, Any, Union

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)

# Set up logging
logger = logging.getLogger(__name__)

# Get environment variables
def get_sendgrid_api_key():
    """Get SendGrid API key from environment, with validation and debugging"""
    api_key = os.environ.get("SENDGRID_API_KEY")
    
    if not api_key:
        logger.warning("SENDGRID_API_KEY environment variable is not set")
        return None
        
    # Remove any spaces or newlines that might have been introduced
    api_key = api_key.strip().replace(" ", "").replace("\n", "").replace("\r", "")
    
    # Basic validation - ensure key starts with SG.
    if not api_key.startswith("SG."):
        logger.warning("SendGrid API key appears to be invalid (doesn't start with SG.)")
        return None
        
    logger.info(f"SendGrid API key is configured (length: {len(api_key)})")
    return api_key

SENDGRID_API_KEY = get_sendgrid_api_key()
FROM_EMAIL = os.environ.get("FROM_EMAIL", "bwatson@ragleinc.com")

def send_email(
    subject: str,
    html_content: str,
    recipients: List[str],
    cc: List[str] = [],
    bcc: List[str] = [],
    attachments: List[Dict[str, str]] = [],
    reply_to: str = ""
) -> Dict[str, Any]:
    """
    Send email using SendGrid.

    Args:
        subject (str): Subject of the email.
        html_content (str): HTML body.
        recipients (List[str]): Recipient emails.
        cc (List[str]): Optional. CC recipients.
        bcc (List[str]): Optional. BCC recipients.
        attachments (List[dict]): Optional. Attachments with file_path, file_name, mime_type.
        reply_to (str): Optional reply-to email.

    Returns:
        dict: status and error (if any).
    """
    try:
        # First, we need a valid API key
        api_key = get_sendgrid_api_key()
        if not api_key:
            return {
                "status": "error", 
                "error": "SendGrid API key not properly configured. Please check your environment variables."
            }
        
        # Create message
        from_email = Email(FROM_EMAIL)
        
        # Validate recipients
        if not recipients or not isinstance(recipients, list) or len(recipients) == 0:
            return {"status": "error", "error": "No recipients specified"}
        
        # Remove any empty emails from recipients
        recipients = [email for email in recipients if email and email.strip()]
        if len(recipients) == 0:
            return {"status": "error", "error": "No valid recipients specified"}
            
        to_emails = [To(email.strip()) for email in recipients]
        content = Content("text/html", html_content)
        message = Mail(from_email, to_emails[0], subject, content)
        
        # Add additional recipients if more than one
        if len(to_emails) > 1:
            for to_email in to_emails[1:]:
                message.add_to(to_email)
        
        # Add CC recipients if provided
        if cc and isinstance(cc, list) and len(cc) > 0:
            for email in cc:
                if email and email.strip():  # Skip empty strings
                    message.add_cc(Email(email.strip()))
        
        # Add BCC recipients if provided
        if bcc and isinstance(bcc, list) and len(bcc) > 0:
            for email in bcc:
                if email and email.strip():  # Skip empty strings
                    message.add_bcc(Email(email.strip()))
        
        # Add reply-to if provided
        if reply_to and reply_to.strip():
            message.reply_to = Email(reply_to.strip())
        
        # Add attachments if provided
        if attachments:
            for att in attachments:
                try:
                    if not os.path.exists(att["file_path"]):
                        logger.warning(f"Attachment file not found: {att['file_path']}")
                        continue
                        
                    with open(att["file_path"], "rb") as f:
                        data = f.read()
                    
                    encoded = base64.b64encode(data).decode()
                    attachment = Attachment()
                    attachment.file_content = FileContent(encoded)
                    attachment.file_type = FileType(att["mime_type"])
                    attachment.file_name = FileName(att["file_name"])
                    attachment.disposition = Disposition("attachment")
                    message.add_attachment(attachment)
                except Exception as e:
                    logger.error(f"Error adding attachment: {e}")
                    # Continue with email even if attachment fails
                    logger.info("Continuing with email despite attachment error")
        
        # Send email with debug information
        try:
            sg = SendGridAPIClient(api_key)
            logger.info(f"Attempting to send email to {recipients} with subject: {subject}")
            res = sg.send(message)
            
            logger.info(f"Email sent successfully. Status code: {res.status_code}")
            return {"status": "success", "code": res.status_code}
        except Exception as send_error:
            logger.error(f"SendGrid API error: {str(send_error)}")
            return {"status": "error", "error": f"SendGrid API error: {str(send_error)}"}
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {"status": "error", "error": str(e)}

def send_report_email(
    subject: str,
    report_content: str,
    recipients: List[str],
    cc: List[str] = [],
    bcc: List[str] = [],
    report_date: str = "",
    report_data: dict = {},
    excel_path: str = "",
    pdf_path: str = "",
    include_user: bool = True
) -> Dict[str, Any]:
    """
    Send a report email with attachments.

    Args:
        subject (str): Email subject
        report_content (str): HTML content for the email body
        recipients (List[str]): List of recipient email addresses
        cc (List[str], optional): CC recipients. Defaults to None.
        bcc (List[str], optional): BCC recipients. Defaults to None.
        report_date (str, optional): Report date. Defaults to None.
        report_data (dict, optional): Report data for templating. Defaults to None.
        excel_path (str, optional): Path to Excel attachment. Defaults to None.
        pdf_path (str, optional): Path to PDF attachment. Defaults to None.
        include_user (bool, optional): Whether to include user info. Defaults to True.

    Returns:
        Dict[str, Any]: Result of send operation
    """
    try:
        # Build attachments
        attachments = []
        
        if excel_path and os.path.exists(excel_path):
            attachments.append({
                "file_path": excel_path,
                "file_name": f"DailyDriverReport_{report_date}.xlsx" if report_date else "DailyDriverReport.xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            })
        
        if pdf_path and os.path.exists(pdf_path):
            attachments.append({
                "file_path": pdf_path,
                "file_name": f"DailyDriverReport_{report_date}.pdf" if report_date else "DailyDriverReport.pdf",
                "mime_type": "application/pdf"
            })
        
        # Send email
        result = send_email(
            subject=subject,
            html_content=report_content,
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            attachments=attachments
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error sending report email: {e}")
        return {"status": "error", "error": str(e)}