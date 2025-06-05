"""
Infinity Email Intelligence Bundle
Advanced email automation and processing system for TRAXOVO
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import smtplib
import email
from email.header import decode_header
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailMessage:
    """Email message structure"""
    id: str
    sender: str
    subject: str
    body: str
    received_time: datetime
    priority: str
    classification: str
    processed: bool = False
    response_sent: bool = False

class EmailAutoScan:
    """Email auto-scanning with queue management"""
    
    def __init__(self):
        self.db_path = "email_intelligence.db"
        self.queues = {
            'urgent': [],
            'delayed': [],
            'weekly': []
        }
        self.init_database()
        logger.info("[EMAIL AUTOSCAN] Email AutoScan initialized")
    
    def init_database(self):
        """Initialize email intelligence database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                sender TEXT,
                subject TEXT,
                body TEXT,
                received_time TIMESTAMP,
                priority TEXT,
                classification TEXT,
                processed BOOLEAN DEFAULT FALSE,
                response_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_automation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                action_type TEXT,
                action_details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("[EMAIL AUTOSCAN] Database initialized")
    
    def scan_emails(self, email_config: Dict) -> List[EmailMessage]:
        """Scan emails from configured email account"""
        try:
            # Connect to email server
            if email_config.get('provider') == 'imap':
                return self._scan_imap_emails(email_config)
            elif email_config.get('provider') == 'outlook':
                return self._scan_outlook_emails(email_config)
            elif email_config.get('provider') == 'gmail':
                return self._scan_gmail_emails(email_config)
            else:
                logger.warning("[EMAIL AUTOSCAN] Unknown email provider")
                return []
        except Exception as e:
            logger.error(f"[EMAIL AUTOSCAN] Error scanning emails: {e}")
            return []
    
    def _scan_imap_emails(self, config: Dict) -> List[EmailMessage]:
        """Scan emails using IMAP"""
        messages = []
        try:
            mail = imaplib.IMAP4_SSL(config['server'], config.get('port', 993))
            mail.login(config['username'], config['password'])
            mail.select('inbox')
            
            # Search for unread emails from today
            today = datetime.now().strftime("%d-%b-%Y")
            status, messages_ids = mail.search(None, f'(UNSEEN SINCE "{today}")')
            
            for msg_id in messages_ids[0].split():
                status, msg_data = mail.fetch(msg_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract email details
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                sender = email_message["From"]
                body = self._extract_body(email_message)
                
                # Create EmailMessage object
                email_obj = EmailMessage(
                    id=msg_id.decode(),
                    sender=sender,
                    subject=subject,
                    body=body,
                    received_time=datetime.now(),
                    priority="normal",
                    classification="unprocessed"
                )
                
                messages.append(email_obj)
            
            mail.close()
            mail.logout()
            logger.info(f"[EMAIL AUTOSCAN] Scanned {len(messages)} new emails")
            
        except Exception as e:
            logger.error(f"[EMAIL AUTOSCAN] IMAP scan error: {e}")
        
        return messages
    
    def _extract_body(self, email_message) -> str:
        """Extract email body text"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        return body
    
    def queue_email(self, email_msg: EmailMessage, queue_type: str):
        """Add email to processing queue"""
        self.queues[queue_type].append(email_msg)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO emails 
            (id, sender, subject, body, received_time, priority, classification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (email_msg.id, email_msg.sender, email_msg.subject, 
              email_msg.body, email_msg.received_time, 
              email_msg.priority, email_msg.classification))
        conn.commit()
        conn.close()
        
        logger.info(f"[EMAIL AUTOSCAN] Email queued in {queue_type}: {email_msg.subject}")

class CreditApplicationHandler:
    """Automated credit application processing"""
    
    def __init__(self):
        self.templates = self._load_response_templates()
        logger.info("[CREDIT HANDLER] Credit Application Handler initialized")
    
    def _load_response_templates(self) -> Dict:
        """Load response templates for credit applications"""
        return {
            'approval_request': '''
            Thank you for your credit application inquiry. We have received your request 
            and are processing it through our automated system.
            
            Based on initial review, we can offer the following terms:
            - Credit Limit: ${credit_limit}
            - Interest Rate: {interest_rate}%
            - Payment Terms: {payment_terms}
            
            Please reply with "ACCEPT" to proceed or "MODIFY" to discuss terms.
            
            Best regards,
            TRAXOVO Credit Processing Team
            ''',
            'document_request': '''
            To complete your credit application, please provide:
            
            1. Business License
            2. Financial Statements (last 2 years)
            3. Bank References
            4. Trade References
            
            Upload documents to: {upload_link}
            
            Best regards,
            TRAXOVO Credit Processing Team
            ''',
            'status_update': '''
            Your credit application status has been updated:
            
            Application ID: {app_id}
            Status: {status}
            Next Steps: {next_steps}
            
            Contact us if you have questions.
            
            Best regards,
            TRAXOVO Credit Processing Team
            '''
        }
    
    def process_credit_application(self, email_msg: EmailMessage) -> Dict:
        """Process credit application email"""
        try:
            # Extract application details from email
            app_details = self._extract_application_details(email_msg.body)
            
            # Auto-fill application form
            filled_form = self._auto_fill_application(app_details)
            
            # Generate response
            response = self._generate_response(app_details, filled_form)
            
            logger.info(f"[CREDIT HANDLER] Processed credit application from {email_msg.sender}")
            
            return {
                'success': True,
                'application_details': app_details,
                'filled_form': filled_form,
                'response': response
            }
            
        except Exception as e:
            logger.error(f"[CREDIT HANDLER] Error processing application: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_application_details(self, email_body: str) -> Dict:
        """Extract credit application details from email"""
        details = {}
        
        # Extract company name
        company_match = re.search(r'company[:\s]+([^\n\r]+)', email_body, re.IGNORECASE)
        if company_match:
            details['company_name'] = company_match.group(1).strip()
        
        # Extract credit amount
        amount_match = re.search(r'\$?([\d,]+)', email_body)
        if amount_match:
            details['requested_amount'] = amount_match.group(1).replace(',', '')
        
        # Extract contact information
        phone_match = re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4})', email_body)
        if phone_match:
            details['phone'] = phone_match.group(1)
        
        return details
    
    def _auto_fill_application(self, details: Dict) -> Dict:
        """Auto-fill credit application form"""
        return {
            'company_name': details.get('company_name', ''),
            'requested_amount': details.get('requested_amount', ''),
            'contact_phone': details.get('phone', ''),
            'application_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'pending_review'
        }
    
    def _generate_response(self, details: Dict, form: Dict) -> str:
        """Generate automated response"""
        if 'requested_amount' in details:
            amount = int(details['requested_amount'])
            if amount < 50000:
                credit_limit = amount * 1.2
                interest_rate = 8.5
                payment_terms = "Net 30"
            else:
                credit_limit = amount
                interest_rate = 6.5
                payment_terms = "Net 45"
            
            return self.templates['approval_request'].format(
                credit_limit=f"{credit_limit:,.0f}",
                interest_rate=interest_rate,
                payment_terms=payment_terms
            )
        else:
            return self.templates['document_request'].format(
                upload_link="https://traxovo.com/upload"
            )

class PriorityClassifierModel:
    """AI-powered email priority classification"""
    
    def __init__(self):
        self.priority_keywords = {
            'urgent': ['urgent', 'emergency', 'asap', 'immediate', 'critical', 'breakdown'],
            'high': ['important', 'priority', 'deadline', 'time-sensitive'],
            'normal': ['request', 'inquiry', 'question', 'information'],
            'low': ['newsletter', 'update', 'notification', 'fyi']
        }
        logger.info("[PRIORITY CLASSIFIER] Priority Classifier Model initialized")
    
    def classify_priority(self, email_msg: EmailMessage) -> str:
        """Classify email priority based on content"""
        content = f"{email_msg.subject} {email_msg.body}".lower()
        
        # Check for urgent keywords
        for keyword in self.priority_keywords['urgent']:
            if keyword in content:
                return 'urgent'
        
        # Check for high priority keywords
        for keyword in self.priority_keywords['high']:
            if keyword in content:
                return 'high'
        
        # Check for low priority keywords
        for keyword in self.priority_keywords['low']:
            if keyword in content:
                return 'low'
        
        return 'normal'
    
    def classify_type(self, email_msg: EmailMessage) -> str:
        """Classify email type"""
        content = f"{email_msg.subject} {email_msg.body}".lower()
        
        if any(word in content for word in ['credit', 'loan', 'financing']):
            return 'credit_application'
        elif any(word in content for word in ['vendor', 'supplier', 'purchase']):
            return 'vendor_inquiry'
        elif any(word in content for word in ['equipment', 'rental', 'lease']):
            return 'equipment_request'
        elif any(word in content for word in ['invoice', 'payment', 'billing']):
            return 'financial'
        else:
            return 'general'

class VendorRecordMatcher:
    """Vendor record matching and management"""
    
    def __init__(self):
        self.vendor_db_path = "vendor_records.db"
        self.init_vendor_database()
        logger.info("[VENDOR MATCHER] Vendor Record Matcher initialized")
    
    def init_vendor_database(self):
        """Initialize vendor database"""
        conn = sqlite3.connect(self.vendor_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                contact_email TEXT,
                phone TEXT,
                address TEXT,
                vendor_type TEXT,
                credit_status TEXT,
                last_contact TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample vendor data
        sample_vendors = [
            ('ABC Equipment Rental', 'contact@abcequipment.com', '555-0101', '123 Main St', 'equipment', 'approved'),
            ('XYZ Construction Supply', 'sales@xyzsupply.com', '555-0102', '456 Oak Ave', 'materials', 'pending'),
            ('Heavy Machinery Co', 'info@heavymachinery.com', '555-0103', '789 Industrial Blvd', 'equipment', 'approved')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO vendors 
            (company_name, contact_email, phone, address, vendor_type, credit_status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_vendors)
        
        conn.commit()
        conn.close()
    
    def match_vendor(self, email_msg: EmailMessage) -> Optional[Dict]:
        """Match email sender to vendor record"""
        conn = sqlite3.connect(self.vendor_db_path)
        cursor = conn.cursor()
        
        # Try exact email match first
        cursor.execute('SELECT * FROM vendors WHERE contact_email = ?', (email_msg.sender,))
        result = cursor.fetchone()
        
        if not result:
            # Try domain match
            domain = email_msg.sender.split('@')[-1] if '@' in email_msg.sender else ''
            cursor.execute('SELECT * FROM vendors WHERE contact_email LIKE ?', (f'%{domain}%',))
            result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'company_name': result[1],
                'contact_email': result[2],
                'phone': result[3],
                'address': result[4],
                'vendor_type': result[5],
                'credit_status': result[6],
                'last_contact': result[7]
            }
        
        return None
    
    def update_vendor_contact(self, vendor_id: int):
        """Update last contact time for vendor"""
        conn = sqlite3.connect(self.vendor_db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE vendors SET last_contact = ? WHERE id = ?', 
                      (datetime.now(), vendor_id))
        conn.commit()
        conn.close()

class InfinityEmailIntelligence:
    """Main email intelligence coordination system"""
    
    def __init__(self):
        self.auto_scan = EmailAutoScan()
        self.credit_handler = CreditApplicationHandler()
        self.priority_classifier = PriorityClassifierModel()
        self.vendor_matcher = VendorRecordMatcher()
        self.session_log = []
        logger.info("[EMAIL INTELLIGENCE] Infinity Email Intelligence Bundle initialized")
    
    def process_email_batch(self, email_config: Dict) -> Dict:
        """Process a batch of emails"""
        try:
            # Scan for new emails
            emails = self.auto_scan.scan_emails(email_config)
            
            processed_count = 0
            automation_sessions = []
            
            for email_msg in emails:
                session = self._process_single_email(email_msg)
                automation_sessions.append(session)
                if session['processed']:
                    processed_count += 1
            
            # Generate daily summary
            summary = self._generate_daily_summary(automation_sessions)
            
            return {
                'success': True,
                'emails_scanned': len(emails),
                'emails_processed': processed_count,
                'automation_sessions': automation_sessions,
                'daily_summary': summary
            }
            
        except Exception as e:
            logger.error(f"[EMAIL INTELLIGENCE] Error processing email batch: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_single_email(self, email_msg: EmailMessage) -> Dict:
        """Process a single email message"""
        session = {
            'email_id': email_msg.id,
            'timestamp': datetime.now().isoformat(),
            'processed': False,
            'actions': []
        }
        
        try:
            # Classify priority and type
            priority = self.priority_classifier.classify_priority(email_msg)
            classification = self.priority_classifier.classify_type(email_msg)
            
            email_msg.priority = priority
            email_msg.classification = classification
            
            session['actions'].append(f"Classified as {priority} priority, type: {classification}")
            
            # Match to vendor if applicable
            vendor = self.vendor_matcher.match_vendor(email_msg)
            if vendor:
                session['actions'].append(f"Matched to vendor: {vendor['company_name']}")
                self.vendor_matcher.update_vendor_contact(vendor['id'])
            
            # Handle specific email types
            if classification == 'credit_application':
                result = self.credit_handler.process_credit_application(email_msg)
                if result['success']:
                    session['actions'].append("Credit application processed and response generated")
                    session['response_generated'] = True
            
            # Queue email based on priority
            if priority == 'urgent':
                self.auto_scan.queue_email(email_msg, 'urgent')
            elif priority in ['high', 'normal']:
                self.auto_scan.queue_email(email_msg, 'delayed')
            else:
                self.auto_scan.queue_email(email_msg, 'weekly')
            
            session['processed'] = True
            session['queue'] = priority
            
        except Exception as e:
            session['error'] = str(e)
            logger.error(f"[EMAIL INTELLIGENCE] Error processing email {email_msg.id}: {e}")
        
        return session
    
    def _generate_daily_summary(self, sessions: List[Dict]) -> Dict:
        """Generate daily automation summary"""
        total_processed = len([s for s in sessions if s['processed']])
        
        priority_counts = {'urgent': 0, 'high': 0, 'normal': 0, 'low': 0}
        for session in sessions:
            if 'queue' in session:
                priority_counts[session['queue']] += 1
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_emails': len(sessions),
            'processed_emails': total_processed,
            'priority_breakdown': priority_counts,
            'automation_success_rate': f"{(total_processed/len(sessions)*100):.1f}%" if sessions else "0%"
        }
    
    def get_watson_integration_data(self) -> Dict:
        """Get data for Watson Command Console integration"""
        conn = sqlite3.connect(self.auto_scan.db_path)
        cursor = conn.cursor()
        
        # Get recent email stats
        cursor.execute('''
            SELECT priority, COUNT(*) as count 
            FROM emails 
            WHERE DATE(created_at) = DATE('now') 
            GROUP BY priority
        ''')
        priority_stats = dict(cursor.fetchall())
        
        # Get processing stats
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed
            FROM emails 
            WHERE DATE(created_at) = DATE('now')
        ''')
        stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'system_status': 'OPERATIONAL',
            'daily_stats': {
                'total_emails': stats[0] if stats else 0,
                'processed_emails': stats[1] if stats else 0,
                'priority_breakdown': priority_stats
            },
            'queues': {
                'urgent': len(self.auto_scan.queues['urgent']),
                'delayed': len(self.auto_scan.queues['delayed']),
                'weekly': len(self.auto_scan.queues['weekly'])
            },
            'last_scan': datetime.now().isoformat()
        }

# Global instance
email_intelligence = InfinityEmailIntelligence()

def get_email_intelligence():
    """Get global email intelligence instance"""
    return email_intelligence

def process_daily_emails(email_config: Dict) -> Dict:
    """Process daily email batch"""
    return email_intelligence.process_email_batch(email_config)

def get_email_dashboard_data() -> Dict:
    """Get email dashboard data for Watson Console"""
    return email_intelligence.get_watson_integration_data()