"""
Email Service Module

This module provides email sending functionality using SendGrid.
"""
import os
import base64
import logging
from typing import List, Optional, Dict, Any, Union

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content,
    Attachment, FileContent, FileName, FileType, Disposition
)

# Set up logging
logger = logging.getLogger(__name__)

# Get environment variables
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
if SENDGRID_API_KEY:
    # Remove any spaces in the API key that might have been introduced
    SENDGRID_API_KEY = SENDGRID_API_KEY.replace(" ", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "bwatson@ragleinc.com")

# Debug info
if not SENDGRID_API_KEY:
    logger.warning("SENDGRID_API_KEY environment variable is not set")
else:
    logger.info("SendGrid API key is configured (length: {})".format(len(SENDGRID_API_KEY)))

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
        if not SENDGRID_API_KEY:
            logger.error("SendGrid API key not found in environment variables")
            return {"status": "error", "error": "SendGrid API key not configured"}
        
        # Create message
        from_email = Email(FROM_EMAIL)
        to_emails = [To(email) for email in recipients]
        content = Content("text/html", html_content)
        message = Mail(from_email, to_emails, subject, content)
        
        # Add CC recipients if provided
        if cc and isinstance(cc, list) and len(cc) > 0:
            for email in cc:
                if email:  # Skip empty strings
                    message.add_cc(Email(email))
        
        # Add BCC recipients if provided
        if bcc and isinstance(bcc, list) and len(bcc) > 0:
            for email in bcc:
                if email:  # Skip empty strings
                    message.add_bcc(Email(email))
        
        # Add reply-to if provided
        if reply_to:
            message.reply_to = Email(reply_to)
        
        # Add attachments if provided
        if attachments:
            for att in attachments:
                try:
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
                    return {"status": "error", "error": f"Attachment error: {str(e)}"}
        
        # Send email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        res = sg.send(message)
        
        logger.info(f"Email sent. Status code: {res.status_code}")
        return {"status": "success", "code": res.status_code}
    
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