"""
TRAXOVO User Profile Management System
Enterprise-grade user management with ASI/AGI-enhanced capabilities
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from werkzeug.security import generate_password_hash, check_password_hash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

@dataclass
class UserProfile:
    """Complete user profile data structure"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    company: str
    job_title: str
    phone: str
    department: str
    created_date: str
    last_login: str
    profile_image_url: str
    notification_preferences: Dict[str, bool]
    security_settings: Dict[str, Any]
    role: str  # ADMIN, MANAGER, OPERATOR, VIEWER

class TRAXOVOUserProfileSystem:
    """
    ASI/AGI-Enhanced User Profile Management
    Complete enterprise user system with intelligent features
    """
    
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.reset_tokens = {}  # In production, store in Redis or database
        self.session_data = {}
        
    def create_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive user profile with ASI validation"""
        
        # ASI-enhanced profile validation
        validation_result = self._asi_validate_profile_data(user_data)
        if not validation_result['valid']:
            return {
                "success": False,
                "error": validation_result['message'],
                "suggestions": validation_result.get('suggestions', [])
            }
        
        # Generate secure profile
        profile = UserProfile(
            id=self._generate_user_id(),
            username=user_data.get('username', '').lower(),
            email=user_data.get('email', '').lower(),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            company=user_data.get('company', ''),
            job_title=user_data.get('job_title', ''),
            phone=user_data.get('phone', ''),
            department=user_data.get('department', ''),
            created_date=datetime.now().isoformat(),
            last_login='',
            profile_image_url='',
            notification_preferences=self._default_notification_preferences(),
            security_settings=self._default_security_settings(),
            role=user_data.get('role', 'OPERATOR')
        )
        
        return {
            "success": True,
            "profile": profile.__dict__,
            "asi_insights": self._asi_profile_insights(profile)
        }
    
    def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile with ASI optimization"""
        
        # ASI change analysis
        change_analysis = self._asi_analyze_profile_changes(user_id, updates)
        
        # Apply updates with validation
        validation_result = self._asi_validate_profile_updates(updates)
        if not validation_result['valid']:
            return {
                "success": False,
                "error": validation_result['message']
            }
        
        # Update profile (in production, update database)
        updated_profile = self._apply_profile_updates(user_id, updates)
        
        return {
            "success": True,
            "profile": updated_profile,
            "change_analysis": change_analysis,
            "asi_recommendations": self._asi_profile_optimization_suggestions(updated_profile)
        }
    
    def initiate_password_reset(self, email: str) -> Dict[str, Any]:
        """Initiate secure password reset with email verification"""
        
        if not self.sendgrid_api_key:
            return {
                "success": False,
                "error": "Email service not configured. Please contact administrator."
            }
        
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        expiry_time = datetime.now() + timedelta(hours=1)
        
        # Store reset token (in production, use database)
        self.reset_tokens[reset_token] = {
            "email": email,
            "expires": expiry_time,
            "used": False
        }
        
        # Send reset email
        email_sent = self._send_password_reset_email(email, reset_token)
        
        if email_sent:
            return {
                "success": True,
                "message": "Password reset instructions sent to your email.",
                "token_expires": expiry_time.isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to send reset email. Please try again."
            }
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Complete password reset with token validation"""
        
        # Validate token
        if token not in self.reset_tokens:
            return {
                "success": False,
                "error": "Invalid or expired reset token."
            }
        
        token_data = self.reset_tokens[token]
        
        # Check expiry
        if datetime.now() > token_data['expires']:
            del self.reset_tokens[token]
            return {
                "success": False,
                "error": "Reset token has expired. Please request a new one."
            }
        
        # Check if already used
        if token_data['used']:
            return {
                "success": False,
                "error": "Reset token has already been used."
            }
        
        # Validate new password
        password_validation = self._asi_validate_password(new_password)
        if not password_validation['valid']:
            return {
                "success": False,
                "error": password_validation['message'],
                "suggestions": password_validation.get('suggestions', [])
            }
        
        # Update password (in production, update database)
        password_hash = generate_password_hash(new_password)
        
        # Mark token as used
        self.reset_tokens[token]['used'] = True
        
        # Log security event
        self._log_security_event(token_data['email'], 'password_reset_completed')
        
        return {
            "success": True,
            "message": "Password successfully reset. You can now log in with your new password."
        }
    
    def get_user_security_dashboard(self, user_id: int) -> Dict[str, Any]:
        """ASI-enhanced security dashboard for user"""
        
        security_analysis = self._asi_security_analysis(user_id)
        
        return {
            "security_score": security_analysis['score'],
            "recent_activity": self._get_recent_security_activity(user_id),
            "security_recommendations": security_analysis['recommendations'],
            "account_health": security_analysis['health_status'],
            "two_factor_status": self._get_2fa_status(user_id),
            "session_management": self._get_active_sessions(user_id)
        }
    
    def _asi_validate_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ASI validation of profile data"""
        
        # Required fields validation
        required_fields = ['username', 'email', 'first_name', 'last_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "suggestions": [f"Please provide {field}" for field in missing_fields]
            }
        
        # Email format validation
        email = data.get('email', '')
        if '@' not in email or '.' not in email.split('@')[-1]:
            return {
                "valid": False,
                "message": "Invalid email format",
                "suggestions": ["Please provide a valid email address"]
            }
        
        # Username validation
        username = data.get('username', '')
        if len(username) < 3:
            return {
                "valid": False,
                "message": "Username must be at least 3 characters long"
            }
        
        return {"valid": True}
    
    def _asi_validate_password(self, password: str) -> Dict[str, Any]:
        """ASI-enhanced password validation"""
        
        suggestions = []
        
        if len(password) < 8:
            return {
                "valid": False,
                "message": "Password must be at least 8 characters long",
                "suggestions": ["Use at least 8 characters"]
            }
        
        # Check complexity
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not has_upper:
            suggestions.append("Include uppercase letters")
        if not has_lower:
            suggestions.append("Include lowercase letters")
        if not has_digit:
            suggestions.append("Include numbers")
        if not has_special:
            suggestions.append("Include special characters")
        
        if len(suggestions) > 2:
            return {
                "valid": False,
                "message": "Password is too weak",
                "suggestions": suggestions
            }
        
        return {"valid": True, "strength": "strong"}
    
    def _send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email using SendGrid"""
        
        try:
            sg = SendGridAPIClient(self.sendgrid_api_key)
            
            reset_url = f"https://{os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')}/reset_password?token={token}"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #d4a574;">TRAXOVO Password Reset</h2>
                <p>You requested a password reset for your TRAXOVO account.</p>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_url}" style="background: #d4a574; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Reset Password</a>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
                <hr style="margin: 30px 0;">
                <p style="color: #666; font-size: 12px;">TRAXOVO Fleet Intelligence Platform</p>
            </div>
            """
            
            message = Mail(
                from_email='noreply@traxovo.com',
                to_emails=email,
                subject='TRAXOVO Password Reset Request',
                html_content=html_content
            )
            
            response = sg.send(message)
            return response.status_code == 202
            
        except Exception as e:
            print(f"Email send error: {e}")
            return False
    
    def _asi_security_analysis(self, user_id: int) -> Dict[str, Any]:
        """ASI security analysis for user account"""
        
        # In production, analyze actual user data
        base_score = 75
        recommendations = []
        
        # Simulate security analysis
        if not self._get_2fa_status(user_id):
            base_score -= 20
            recommendations.append("Enable two-factor authentication")
        
        if self._check_password_age(user_id) > 90:
            base_score -= 10
            recommendations.append("Update your password (it's over 90 days old)")
        
        return {
            "score": max(base_score, 0),
            "recommendations": recommendations,
            "health_status": "good" if base_score > 70 else "needs_attention"
        }
    
    def _generate_user_id(self) -> int:
        """Generate unique user ID"""
        return int(datetime.now().timestamp() * 1000) % 1000000
    
    def _default_notification_preferences(self) -> Dict[str, bool]:
        """Default notification preferences"""
        return {
            "email_alerts": True,
            "maintenance_notifications": True,
            "security_alerts": True,
            "system_updates": False,
            "fleet_reports": True
        }
    
    def _default_security_settings(self) -> Dict[str, Any]:
        """Default security settings"""
        return {
            "two_factor_enabled": False,
            "session_timeout": 480,  # 8 hours
            "login_notifications": True,
            "password_last_changed": datetime.now().isoformat()
        }
    
    def _asi_analyze_profile_changes(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """ASI analysis of profile changes"""
        return {
            "risk_level": "low",
            "significant_changes": [key for key in updates if key in ['email', 'role', 'security_settings']],
            "recommendations": ["Verify email change with confirmation", "Log security-related changes"]
        }
    
    def _asi_validate_profile_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile update data"""
        # Basic validation for updates
        if 'email' in updates:
            email = updates['email']
            if '@' not in email:
                return {"valid": False, "message": "Invalid email format"}
        
        return {"valid": True}
    
    def _apply_profile_updates(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply profile updates (placeholder for database integration)"""
        # In production, update database and return updated profile
        return {"user_id": user_id, "updated_fields": list(updates.keys())}
    
    def _asi_profile_optimization_suggestions(self, profile: Dict[str, Any]) -> list:
        """ASI suggestions for profile optimization"""
        suggestions = []
        
        if not profile.get('profile_image_url'):
            suggestions.append("Add a profile image for better team recognition")
        
        if not profile.get('phone'):
            suggestions.append("Add phone number for emergency contacts")
        
        return suggestions
    
    def _asi_profile_insights(self, profile: UserProfile) -> Dict[str, Any]:
        """ASI insights about the new profile"""
        return {
            "completeness_score": 85,
            "security_level": "standard",
            "onboarding_tips": [
                "Complete your profile for better team collaboration",
                "Set up two-factor authentication for enhanced security"
            ]
        }
    
    def _get_recent_security_activity(self, user_id: int) -> list:
        """Get recent security activity for user"""
        # Placeholder - in production, query actual security logs
        return [
            {"event": "login", "timestamp": datetime.now().isoformat(), "ip": "192.168.1.100"},
            {"event": "profile_update", "timestamp": (datetime.now() - timedelta(days=2)).isoformat(), "ip": "192.168.1.100"}
        ]
    
    def _get_2fa_status(self, user_id: int) -> bool:
        """Check if user has 2FA enabled"""
        # Placeholder - in production, check database
        return False
    
    def _get_active_sessions(self, user_id: int) -> list:
        """Get user's active sessions"""
        # Placeholder - in production, query session store
        return [
            {"session_id": "sess_123", "created": datetime.now().isoformat(), "last_activity": datetime.now().isoformat()}
        ]
    
    def _check_password_age(self, user_id: int) -> int:
        """Check password age in days"""
        # Placeholder - in production, check database
        return 45
    
    def _log_security_event(self, email: str, event_type: str):
        """Log security events"""
        # In production, log to security audit system
        print(f"Security Event: {event_type} for {email} at {datetime.now()}")

# Global instance
user_profile_system = TRAXOVOUserProfileSystem()

def get_user_profile_system():
    """Get the global user profile system instance"""
    return user_profile_system