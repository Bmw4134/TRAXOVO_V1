"""
TRAXOVO User Credentials Reference
Current active user accounts with authentication details
"""

def get_all_user_credentials():
    """Get complete list of user credentials for system access"""
    
    return {
        'executive_users': {
            'troy': {
                'username': 'troy',
                'password': 'troy2025',
                'role': 'exec',
                'name': 'Troy',
                'access_level': 'executive_dashboard'
            },
            'william': {
                'username': 'william', 
                'password': 'william2025',
                'role': 'exec',
                'name': 'William',
                'access_level': 'executive_dashboard'
            },
            'james': {
                'username': 'james',
                'password': 'james2025', 
                'role': 'exec',
                'name': 'James',
                'access_level': 'executive_dashboard'
            },
            'chris': {
                'username': 'chris',
                'password': 'chris2025',
                'role': 'exec', 
                'name': 'Chris',
                'access_level': 'executive_dashboard'
            }
        },
        
        'administrative_users': {
            'admin': {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'name': 'Administrator', 
                'access_level': 'full_system_admin'
            },
            'ops': {
                'username': 'ops',
                'password': 'ops123',
                'role': 'ops',
                'name': 'Operations',
                'access_level': 'operations_management'
            }
        },
        
        'watson_exclusive': {
            'watson': {
                'username': 'watson',
                'password': 'proprietary_watson_2025',
                'role': 'dev_admin_master',
                'name': 'Watson Dev Admin Master',
                'access_level': 'complete_system_control',
                'watson_access': True,
                'admin_access': True,
                'full_system_control': True,
                'simulation_engine_access': True,
                'exclusive_owner': True
            }
        }
    }

def validate_user_credentials(username, password):
    """Validate user credentials against the authentication store"""
    
    all_users = get_all_user_credentials()
    
    # Check executive users
    for user_type, users in all_users.items():
        if username in users:
            user_data = users[username]
            if user_data['password'] == password:
                return {
                    'valid': True,
                    'user_data': user_data,
                    'user_type': user_type
                }
    
    return {
        'valid': False,
        'error': 'Invalid username or password'
    }

def get_user_access_summary():
    """Get summary of user access levels and capabilities"""
    
    return {
        'James Login Credentials': {
            'Username': 'james',
            'Password': 'james2025',
            'Role': 'Executive',
            'Access': 'Full executive dashboard access'
        },
        
        'Chris Login Credentials': {
            'Username': 'chris', 
            'Password': 'chris2025',
            'Role': 'Executive',
            'Access': 'Full executive dashboard access'
        },
        
        'Validation Process': {
            'Login URL': '/login',
            'Dashboard Access': 'Automatic redirect after successful login',
            'Session Management': 'Persistent login until logout',
            'Security': 'Role-based access control implemented'
        },
        
        'Testing Instructions': [
            '1. Navigate to the login page',
            '2. Enter username and password',
            '3. Verify successful authentication',
            '4. Confirm dashboard access and role permissions',
            '5. Test navigation between different system modules'
        ]
    }

if __name__ == "__main__":
    # Display user credentials
    credentials = get_user_access_summary()
    
    print("TRAXOVO User Authentication Summary")
    print("=" * 50)
    
    for section, data in credentials.items():
        print(f"\n{section}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        elif isinstance(data, list):
            for item in data:
                print(f"  - {item}")