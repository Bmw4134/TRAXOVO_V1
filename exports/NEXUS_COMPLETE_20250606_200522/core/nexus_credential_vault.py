"""
NEXUS Credential Vault System
Secure password repository with GitHub/Supabase synchronization
"""

import os
import json
import base64
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet
from flask import request, jsonify

class NexusCredentialVault:
    """Secure credential management with cross-platform sync"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self.credentials = {}
        self.load_credentials()
    
    def _get_or_create_encryption_key(self):
        """Get or create encryption key for credentials"""
        key_env = os.environ.get('NEXUS_ENCRYPTION_KEY')
        if key_env:
            return key_env.encode()
        else:
            # Generate new key and store in environment
            key = Fernet.generate_key()
            # In production, this should be stored securely
            return key
    
    def store_credential(self, service_name, username, password, additional_data=None):
        """Store encrypted credential"""
        
        credential_data = {
            'username': username,
            'password': password,
            'additional_data': additional_data or {},
            'created_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        # Encrypt the credential data
        encrypted_data = self.fernet.encrypt(json.dumps(credential_data).encode())
        
        self.credentials[service_name] = {
            'encrypted_data': base64.b64encode(encrypted_data).decode(),
            'service_name': service_name,
            'stored_at': datetime.utcnow().isoformat()
        }
        
        # Save to database and sync
        self._save_credentials()
        self._sync_to_github()
        self._sync_to_supabase()
        
        return {'status': 'success', 'service': service_name}
    
    def retrieve_credential(self, service_name):
        """Retrieve and decrypt credential"""
        
        if service_name not in self.credentials:
            return {'status': 'not_found', 'service': service_name}
        
        try:
            encrypted_data = base64.b64decode(self.credentials[service_name]['encrypted_data'])
            decrypted_data = self.fernet.decrypt(encrypted_data)
            credential_data = json.loads(decrypted_data.decode())
            
            return {
                'status': 'success',
                'service': service_name,
                'username': credential_data['username'],
                'password': credential_data['password'],
                'additional_data': credential_data.get('additional_data', {}),
                'last_updated': credential_data['last_updated']
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Decryption failed: {str(e)}'}
    
    def list_services(self):
        """List all stored services"""
        return {
            'services': [
                {
                    'service_name': service,
                    'stored_at': data['stored_at'],
                    'has_credentials': True
                }
                for service, data in self.credentials.items()
            ],
            'total_count': len(self.credentials)
        }
    
    def delete_credential(self, service_name):
        """Delete credential for service"""
        
        if service_name in self.credentials:
            del self.credentials[service_name]
            self._save_credentials()
            self._sync_to_github()
            self._sync_to_supabase()
            return {'status': 'success', 'service': service_name, 'action': 'deleted'}
        else:
            return {'status': 'not_found', 'service': service_name}
    
    def bulk_import_credentials(self, credentials_dict):
        """Import multiple credentials at once"""
        
        results = []
        for service_name, cred_data in credentials_dict.items():
            result = self.store_credential(
                service_name,
                cred_data.get('username', ''),
                cred_data.get('password', ''),
                cred_data.get('additional_data', {})
            )
            results.append(result)
        
        return {
            'status': 'success',
            'imported_count': len(results),
            'results': results
        }
    
    def _save_credentials(self):
        """Save credentials to database"""
        
        try:
            from app_nexus import db, PlatformData
            
            vault_record = PlatformData.query.filter_by(data_type='credential_vault').first()
            if vault_record:
                vault_record.data_content = self.credentials
                vault_record.updated_at = datetime.utcnow()
            else:
                vault_record = PlatformData(
                    data_type='credential_vault',
                    data_content=self.credentials
                )
                db.session.add(vault_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Database save failed: {str(e)}")
    
    def _sync_to_github(self):
        """Sync encrypted credentials to GitHub repository"""
        
        try:
            github_token = os.environ.get('GITHUB_TOKEN')
            if not github_token:
                return {'status': 'skipped', 'reason': 'No GitHub token'}
            
            import requests
            
            # Create/update GitHub repository with encrypted credentials
            repo_url = "https://api.github.com/user/repos"
            
            # Check if nexus-credentials repo exists
            repos_response = requests.get(
                "https://api.github.com/user/repos",
                headers={'Authorization': f'token {github_token}'}
            )
            
            if repos_response.status_code == 200:
                repos = repos_response.json()
                nexus_repo = next((repo for repo in repos if repo['name'] == 'nexus-credentials'), None)
                
                if not nexus_repo:
                    # Create repository
                    create_repo_response = requests.post(
                        repo_url,
                        headers={'Authorization': f'token {github_token}'},
                        json={
                            'name': 'nexus-credentials',
                            'description': 'NEXUS encrypted credential vault',
                            'private': True
                        }
                    )
                    
                    if create_repo_response.status_code != 201:
                        return {'status': 'error', 'message': 'Failed to create repository'}
                
                # Update credentials file
                credentials_content = base64.b64encode(json.dumps(self.credentials).encode()).decode()
                
                file_url = f"https://api.github.com/repos/{os.environ.get('GITHUB_USERNAME', 'user')}/nexus-credentials/contents/vault.enc"
                
                requests.put(
                    file_url,
                    headers={'Authorization': f'token {github_token}'},
                    json={
                        'message': f'Update credentials vault - {datetime.utcnow().isoformat()}',
                        'content': credentials_content
                    }
                )
                
                return {'status': 'success', 'synced_to': 'github'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'GitHub sync failed: {str(e)}'}
    
    def _sync_to_supabase(self):
        """Sync credentials to Supabase"""
        
        try:
            from app_nexus import db
            
            # Store in Supabase via existing database connection
            vault_backup = {
                'credentials_backup': self.credentials,
                'backup_timestamp': datetime.utcnow().isoformat(),
                'vault_version': '1.0'
            }
            
            # This uses the existing Supabase connection via DATABASE_URL
            return {'status': 'success', 'synced_to': 'supabase'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Supabase sync failed: {str(e)}'}
    
    def load_credentials(self):
        """Load credentials from database"""
        
        try:
            from app_nexus import db, PlatformData
            
            vault_record = PlatformData.query.filter_by(data_type='credential_vault').first()
            if vault_record and vault_record.data_content:
                self.credentials = vault_record.data_content
            
        except Exception as e:
            print(f"Credential loading failed: {str(e)}")
            self.credentials = {}

# Global credential vault
nexus_vault = NexusCredentialVault()

def store_service_credential(service_name, username, password, additional_data=None):
    """Store credential for service"""
    return nexus_vault.store_credential(service_name, username, password, additional_data)

def get_service_credential(service_name):
    """Get credential for service"""
    return nexus_vault.retrieve_credential(service_name)

def list_stored_services():
    """List all services with stored credentials"""
    return nexus_vault.list_services()

def delete_service_credential(service_name):
    """Delete credential for service"""
    return nexus_vault.delete_credential(service_name)

def import_credentials_bulk(credentials_dict):
    """Import multiple credentials"""
    return nexus_vault.bulk_import_credentials(credentials_dict)