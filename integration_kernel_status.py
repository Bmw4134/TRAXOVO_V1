"""
NEXUS Integration Kernel Status
Real-time monitoring and validation of external system connections
"""

import os
import requests
from datetime import datetime

class IntegrationKernel:
    """Core integration status monitoring and validation system"""
    
    def __init__(self):
        self.status = {"diagnostics_complete": True, "kernel_active": True}
        self.required_connections = {
            "openai": {
                "env_var": "OPENAI_API_KEY",
                "test_endpoint": "https://api.openai.com/v1/models",
                "status": "unknown",
                "priority": "critical"
            },
            "sendgrid": {
                "env_var": "SENDGRID_API_KEY", 
                "test_endpoint": "https://api.sendgrid.com/v3/user/profile",
                "status": "unknown",
                "priority": "high"
            },
            "github": {
                "env_var": "GITHUB_TOKEN",
                "test_endpoint": "https://api.github.com/user",
                "status": "unknown", 
                "priority": "medium"
            },
            "trello": {
                "env_vars": ["TRELLO_API_KEY", "TRELLO_TOKEN"],
                "test_endpoint": "https://api.trello.com/1/members/me",
                "status": "unknown",
                "priority": "medium"
            },
            "twilio": {
                "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
                "test_endpoint": "https://api.twilio.com/2010-04-01/Accounts",
                "status": "unknown",
                "priority": "medium"
            },
            "microsoft_graph": {
                "env_vars": ["MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET"],
                "test_endpoint": "https://graph.microsoft.com/v1.0",
                "status": "unknown",
                "priority": "high"
            }
        }
    
    def run_full_diagnostics(self):
        """Execute comprehensive integration diagnostics"""
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "connections": {},
            "missing_secrets": [],
            "setup_required": [],
            "ready_connections": [],
            "authorization_checklist": []
        }
        
        for service, config in self.required_connections.items():
            result = self._test_connection(service, config)
            diagnostics["connections"][service] = result
            
            if result["status"] == "missing_credentials":
                diagnostics["missing_secrets"].extend(result["missing_vars"])
                diagnostics["setup_required"].append({
                    "service": service,
                    "action": "credential_input",
                    "priority": config["priority"],
                    "vars_needed": result["missing_vars"]
                })
            elif result["status"] == "needs_authorization":
                diagnostics["authorization_checklist"].append({
                    "service": service,
                    "action": "oauth_authorization", 
                    "priority": config["priority"],
                    "auth_url": result.get("auth_url")
                })
            elif result["status"] == "ready":
                diagnostics["ready_connections"].append(service)
        
        # Generate precise checklist
        diagnostics["manual_actions_required"] = self._generate_checklist(diagnostics)
        
        return diagnostics
    
    def _test_connection(self, service, config):
        """Test individual service connection"""
        result = {"service": service, "timestamp": datetime.utcnow().isoformat()}
        
        # Check for required environment variables
        if "env_var" in config:
            missing_vars = []
            if not os.environ.get(config["env_var"]):
                missing_vars.append(config["env_var"])
        else:
            missing_vars = []
            for var in config.get("env_vars", []):
                if not os.environ.get(var):
                    missing_vars.append(var)
        
        if missing_vars:
            result.update({
                "status": "missing_credentials",
                "missing_vars": missing_vars,
                "setup_type": "credential_input"
            })
            return result
        
        # Test API connection if credentials exist
        try:
            if service == "openai":
                headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"}
                response = requests.get(config["test_endpoint"], headers=headers, timeout=10)
                result["status"] = "ready" if response.status_code == 200 else "error"
                
            elif service == "sendgrid":
                headers = {"Authorization": f"Bearer {os.environ.get('SENDGRID_API_KEY')}"}
                response = requests.get(config["test_endpoint"], headers=headers, timeout=10)
                result["status"] = "ready" if response.status_code == 200 else "error"
                
            elif service == "github":
                headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN')}"}
                response = requests.get(config["test_endpoint"], headers=headers, timeout=10)
                result["status"] = "ready" if response.status_code == 200 else "error"
                
            elif service == "trello":
                api_key = os.environ.get("TRELLO_API_KEY")
                token = os.environ.get("TRELLO_TOKEN")
                url = f"{config['test_endpoint']}?key={api_key}&token={token}"
                response = requests.get(url, timeout=10)
                result["status"] = "ready" if response.status_code == 200 else "error"
                
            elif service == "twilio":
                from base64 import b64encode
                sid = os.environ.get("TWILIO_ACCOUNT_SID")
                token = os.environ.get("TWILIO_AUTH_TOKEN")
                auth_string = b64encode(f"{sid}:{token}".encode()).decode()
                headers = {"Authorization": f"Basic {auth_string}"}
                response = requests.get(f"{config['test_endpoint']}/{sid}.json", headers=headers, timeout=10)
                result["status"] = "ready" if response.status_code == 200 else "error"
                
            elif service == "microsoft_graph":
                # Microsoft Graph requires OAuth flow
                result["status"] = "needs_authorization"
                result["auth_url"] = "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps"
                
        except Exception as e:
            result.update({
                "status": "error",
                "error": str(e),
                "setup_type": "troubleshooting_required"
            })
        
        return result
    
    def _generate_checklist(self, diagnostics):
        """Generate precise manual action checklist"""
        checklist = []
        
        # Critical missing credentials
        critical_missing = [item for item in diagnostics["setup_required"] if item["priority"] == "critical"]
        if critical_missing:
            checklist.append({
                "priority": "CRITICAL",
                "action": "Add OpenAI API Key to Replit Secrets",
                "steps": [
                    "Navigate to Replit Secrets panel",
                    "Add key: OPENAI_API_KEY", 
                    "Get value from: https://platform.openai.com/api-keys"
                ]
            })
        
        # High priority integrations
        high_priority = [item for item in diagnostics["setup_required"] if item["priority"] == "high"]
        for item in high_priority:
            if item["service"] == "sendgrid":
                checklist.append({
                    "priority": "HIGH", 
                    "action": "Configure SendGrid for email automation",
                    "steps": [
                        "Get API key from: https://app.sendgrid.com/settings/api_keys",
                        "Add to Replit Secrets: SENDGRID_API_KEY"
                    ]
                })
            elif item["service"] == "microsoft_graph":
                checklist.append({
                    "priority": "HIGH",
                    "action": "Setup Microsoft Graph OAuth for OneDrive",
                    "steps": [
                        "Register app at: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps",
                        "Add redirect URI: {your_replit_url}/auth/microsoft/callback",
                        "Add to Secrets: MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET"
                    ]
                })
        
        # Medium priority integrations
        medium_priority = [item for item in diagnostics["setup_required"] if item["priority"] == "medium"]
        for item in medium_priority:
            if item["service"] == "github":
                checklist.append({
                    "priority": "MEDIUM",
                    "action": "GitHub integration for code automation",
                    "steps": [
                        "Create token at: https://github.com/settings/tokens",
                        "Select scopes: repo, workflow",
                        "Add to Secrets: GITHUB_TOKEN"
                    ]
                })
            elif item["service"] == "trello":
                checklist.append({
                    "priority": "MEDIUM", 
                    "action": "Trello integration for project management",
                    "steps": [
                        "Get API key from: https://trello.com/app-key",
                        "Generate token with read/write permissions",
                        "Add to Secrets: TRELLO_API_KEY, TRELLO_TOKEN"
                    ]
                })
            elif item["service"] == "twilio":
                checklist.append({
                    "priority": "MEDIUM",
                    "action": "Twilio SMS integration",
                    "steps": [
                        "Get credentials from: https://console.twilio.com/",
                        "Add to Secrets: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER"
                    ]
                })
        
        return checklist

# Initialize integration kernel
integration = IntegrationKernel()
integration.kernel = {"status": True}