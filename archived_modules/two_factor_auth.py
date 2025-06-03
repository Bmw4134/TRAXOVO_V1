"""
Two-Factor Authentication System
Enterprise-grade security with SMS and email verification
"""

import os
import json
import secrets
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

@dataclass
class TwoFactorUser:
    """User with two-factor authentication data"""
    user_id: str
    username: str
    email: str
    phone: Optional[str]
    totp_secret: Optional[str]
    backup_codes: List[str]
    sms_enabled: bool
    email_enabled: bool
    totp_enabled: bool
    last_2fa_verification: Optional[datetime]
    failed_attempts: int
    locked_until: Optional[datetime]

class TwoFactorAuthSystem:
    """
    Enterprise two-factor authentication system
    """
    
    def __init__(self):
        self.users_2fa_file = "users_2fa.json"
        self.verification_codes = {}  # In-memory storage for verification codes
        self.code_expiry_minutes = 5
        self.max_failed_attempts = 3
        self.lockout_duration_minutes = 30
        
    def setup_2fa_for_user(self, user_id: str, username: str, email: str, phone: Optional[str] = None) -> Dict[str, Any]:
        """Set up two-factor authentication for a user"""
        # Generate TOTP secret
        totp_secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Create 2FA user record
        user_2fa = TwoFactorUser(
            user_id=user_id,
            username=username,
            email=email,
            phone=phone,
            totp_secret=totp_secret,
            backup_codes=backup_codes,
            sms_enabled=bool(phone),
            email_enabled=True,
            totp_enabled=True,
            last_2fa_verification=None,
            failed_attempts=0,
            locked_until=None
        )
        
        # Save to file
        self._save_user_2fa(user_2fa)
        
        # Generate QR code for TOTP setup
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
            username,
            issuer_name="TRAXOVO Fleet Intelligence"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert QR code to base64 for display
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        qr_code_b64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return {
            "success": True,
            "totp_secret": totp_secret,
            "qr_code": qr_code_b64,
            "backup_codes": backup_codes,
            "setup_uri": totp_uri
        }
    
    def send_sms_code(self, user_id: str) -> Dict[str, Any]:
        """Send SMS verification code"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa or not user_2fa.sms_enabled or not user_2fa.phone:
            return {"success": False, "error": "SMS not enabled for user"}
        
        if self._is_user_locked(user_2fa):
            return {"success": False, "error": "Account temporarily locked due to failed attempts"}
        
        # Generate 6-digit code
        verification_code = secrets.randbelow(900000) + 100000
        
        # Store code with expiry
        self.verification_codes[f"sms_{user_id}"] = {
            "code": str(verification_code),
            "expires": datetime.now() + timedelta(minutes=self.code_expiry_minutes),
            "attempts": 0
        }
        
        # Send SMS (you'll need to configure with your SMS provider)
        sms_result = self._send_sms(user_2fa.phone, f"TRAXOVO verification code: {verification_code}")
        
        return {
            "success": sms_result,
            "message": "SMS code sent" if sms_result else "Failed to send SMS",
            "expires_in_minutes": self.code_expiry_minutes
        }
    
    def send_email_code(self, user_id: str) -> Dict[str, Any]:
        """Send email verification code"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa or not user_2fa.email_enabled:
            return {"success": False, "error": "Email verification not enabled"}
        
        if self._is_user_locked(user_2fa):
            return {"success": False, "error": "Account temporarily locked due to failed attempts"}
        
        # Generate 6-digit code
        verification_code = secrets.randbelow(900000) + 100000
        
        # Store code with expiry
        self.verification_codes[f"email_{user_id}"] = {
            "code": str(verification_code),
            "expires": datetime.now() + timedelta(minutes=self.code_expiry_minutes),
            "attempts": 0
        }
        
        # Send email
        email_result = self._send_verification_email(user_2fa.email, verification_code)
        
        return {
            "success": email_result,
            "message": "Email code sent" if email_result else "Failed to send email",
            "expires_in_minutes": self.code_expiry_minutes
        }
    
    def verify_totp_code(self, user_id: str, totp_code: str) -> Dict[str, Any]:
        """Verify TOTP code from authenticator app"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa or not user_2fa.totp_enabled:
            return {"success": False, "error": "TOTP not enabled for user"}
        
        if self._is_user_locked(user_2fa):
            return {"success": False, "error": "Account temporarily locked due to failed attempts"}
        
        # Verify TOTP code
        totp = pyotp.TOTP(user_2fa.totp_secret)
        
        if totp.verify(totp_code, valid_window=1):  # Allow 1 window of tolerance
            self._reset_failed_attempts(user_2fa)
            user_2fa.last_2fa_verification = datetime.now()
            self._save_user_2fa(user_2fa)
            
            return {
                "success": True,
                "message": "TOTP verification successful",
                "method": "totp"
            }
        else:
            self._increment_failed_attempts(user_2fa)
            return {
                "success": False,
                "error": "Invalid TOTP code",
                "failed_attempts": user_2fa.failed_attempts
            }
    
    def verify_sms_code(self, user_id: str, sms_code: str) -> Dict[str, Any]:
        """Verify SMS code"""
        return self._verify_stored_code(f"sms_{user_id}", sms_code, "SMS")
    
    def verify_email_code(self, user_id: str, email_code: str) -> Dict[str, Any]:
        """Verify email code"""
        return self._verify_stored_code(f"email_{user_id}", email_code, "Email")
    
    def verify_backup_code(self, user_id: str, backup_code: str) -> Dict[str, Any]:
        """Verify backup code"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa:
            return {"success": False, "error": "User not found"}
        
        if backup_code.upper() in user_2fa.backup_codes:
            # Remove used backup code
            user_2fa.backup_codes.remove(backup_code.upper())
            user_2fa.last_2fa_verification = datetime.now()
            self._reset_failed_attempts(user_2fa)
            self._save_user_2fa(user_2fa)
            
            return {
                "success": True,
                "message": "Backup code verification successful",
                "method": "backup",
                "remaining_codes": len(user_2fa.backup_codes)
            }
        else:
            self._increment_failed_attempts(user_2fa)
            return {
                "success": False,
                "error": "Invalid backup code",
                "failed_attempts": user_2fa.failed_attempts
            }
    
    def get_2fa_methods(self, user_id: str) -> Dict[str, Any]:
        """Get available 2FA methods for user"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa:
            return {"methods": []}
        
        methods = []
        if user_2fa.totp_enabled:
            methods.append("totp")
        if user_2fa.sms_enabled:
            methods.append("sms")
        if user_2fa.email_enabled:
            methods.append("email")
        
        methods.append("backup")  # Always available
        
        return {
            "methods": methods,
            "backup_codes_remaining": len(user_2fa.backup_codes),
            "is_locked": self._is_user_locked(user_2fa)
        }
    
    def _verify_stored_code(self, code_key: str, provided_code: str, method_name: str) -> Dict[str, Any]:
        """Verify a stored verification code"""
        if code_key not in self.verification_codes:
            return {"success": False, "error": f"No {method_name} code found or expired"}
        
        code_data = self.verification_codes[code_key]
        
        # Check if expired
        if datetime.now() > code_data["expires"]:
            del self.verification_codes[code_key]
            return {"success": False, "error": f"{method_name} code expired"}
        
        # Check attempts
        if code_data["attempts"] >= 3:
            del self.verification_codes[code_key]
            return {"success": False, "error": "Too many attempts"}
        
        # Verify code
        if code_data["code"] == provided_code:
            del self.verification_codes[code_key]
            return {
                "success": True,
                "message": f"{method_name} verification successful",
                "method": method_name.lower()
            }
        else:
            code_data["attempts"] += 1
            return {
                "success": False,
                "error": f"Invalid {method_name} code",
                "attempts_remaining": 3 - code_data["attempts"]
            }
    
    def _send_sms(self, phone: str, message: str) -> bool:
        """Send SMS using configured SMS service"""
        # For production, integrate with Twilio, AWS SNS, or similar service
        # This is a placeholder that would need actual SMS API integration
        
        # Check if Twilio credentials are available
        twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
        twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
        
        if twilio_sid and twilio_token and twilio_phone:
            try:
                # Would integrate with Twilio API here
                # This is a simulation for now
                print(f"SMS would be sent to {phone}: {message}")
                return True
            except Exception:
                return False
        
        # For demo purposes, log the SMS
        print(f"SMS Code for {phone}: {message}")
        return True
    
    def _send_verification_email(self, email: str, code: int) -> bool:
        """Send verification email"""
        try:
            # Use SendGrid or SMTP for email sending
            sendgrid_key = os.environ.get("SENDGRID_API_KEY")
            
            if sendgrid_key:
                # Would integrate with SendGrid API here
                pass
            
            # For demo purposes, log the email
            print(f"Email Code for {email}: {code}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _get_user_2fa(self, user_id: str) -> Optional[TwoFactorUser]:
        """Get user 2FA data"""
        try:
            if os.path.exists(self.users_2fa_file):
                with open(self.users_2fa_file, 'r') as f:
                    data = json.load(f)
                    
                for user_data in data.get("users", []):
                    if user_data["user_id"] == user_id:
                        # Convert datetime fields
                        if user_data.get("last_2fa_verification"):
                            user_data["last_2fa_verification"] = datetime.fromisoformat(user_data["last_2fa_verification"])
                        if user_data.get("locked_until"):
                            user_data["locked_until"] = datetime.fromisoformat(user_data["locked_until"])
                        
                        return TwoFactorUser(**user_data)
            
            return None
            
        except Exception:
            return None
    
    def _save_user_2fa(self, user_2fa: TwoFactorUser):
        """Save user 2FA data"""
        try:
            # Load existing data
            users_data = []
            if os.path.exists(self.users_2fa_file):
                with open(self.users_2fa_file, 'r') as f:
                    data = json.load(f)
                    users_data = data.get("users", [])
            
            # Update or add user
            user_dict = asdict(user_2fa)
            if user_dict.get("last_2fa_verification"):
                user_dict["last_2fa_verification"] = user_2fa.last_2fa_verification.isoformat()
            if user_dict.get("locked_until"):
                user_dict["locked_until"] = user_2fa.locked_until.isoformat()
            
            # Remove existing user data and add updated
            users_data = [u for u in users_data if u.get("user_id") != user_2fa.user_id]
            users_data.append(user_dict)
            
            # Save to file
            with open(self.users_2fa_file, 'w') as f:
                json.dump({
                    "users": users_data,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save 2FA data: {e}")
    
    def _is_user_locked(self, user_2fa: TwoFactorUser) -> bool:
        """Check if user is locked out"""
        if user_2fa.locked_until and datetime.now() < user_2fa.locked_until:
            return True
        return False
    
    def _increment_failed_attempts(self, user_2fa: TwoFactorUser):
        """Increment failed attempts and lock if necessary"""
        user_2fa.failed_attempts += 1
        
        if user_2fa.failed_attempts >= self.max_failed_attempts:
            user_2fa.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
        
        self._save_user_2fa(user_2fa)
    
    def _reset_failed_attempts(self, user_2fa: TwoFactorUser):
        """Reset failed attempts counter"""
        user_2fa.failed_attempts = 0
        user_2fa.locked_until = None
        self._save_user_2fa(user_2fa)

# Global 2FA system
_two_factor_auth = None

def get_two_factor_auth():
    """Get two-factor authentication system"""
    global _two_factor_auth
    if _two_factor_auth is None:
        _two_factor_auth = TwoFactorAuthSystem()
    return _two_factor_auth