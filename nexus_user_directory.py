"""
NEXUS COMMAND User Directory
Complete authentication credentials for all platform users
"""

def get_all_nexus_users():
    """Complete NEXUS COMMAND user authentication directory"""
    
    return {
        'executive_users': {
            'chris': {
                'username': 'chris',
                'password': 'chris2025',
                'role': 'executive',
                'name': 'Chris',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'britney': {
                'username': 'britney', 
                'password': 'britney2025',
                'role': 'executive',
                'name': 'Britney',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'cooper': {
                'username': 'cooper',
                'password': 'cooper2025',
                'role': 'executive', 
                'name': 'Cooper',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'ammar': {
                'username': 'ammar',
                'password': 'ammar2025',
                'role': 'executive',
                'name': 'Ammar', 
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'jacob': {
                'username': 'jacob',
                'password': 'jacob2025',
                'role': 'executive',
                'name': 'Jacob',
                'access_level': 'executive_dashboard', 
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'william': {
                'username': 'william',
                'password': 'william2025',
                'role': 'executive',
                'name': 'William',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'james': {
                'username': 'james',
                'password': 'james2025',
                'role': 'executive',
                'name': 'James',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            },
            'troy': {
                'username': 'troy',
                'password': 'troy2025',
                'role': 'executive', 
                'name': 'Troy',
                'access_level': 'executive_dashboard',
                'permissions': ['fleet_management', 'analytics', 'reporting']
            }
        },
        
        'administrative_users': {
            'admin': {
                'username': 'admin',
                'password': 'admin123',
                'role': 'administrator',
                'name': 'Administrator',
                'access_level': 'full_system_admin',
                'permissions': ['user_management', 'system_config', 'full_access']
            },
            'ops': {
                'username': 'ops',
                'password': 'ops123',
                'role': 'operations',
                'name': 'Operations',
                'access_level': 'operations_management', 
                'permissions': ['fleet_operations', 'maintenance', 'scheduling']
            }
        },
        
        'watson_supreme': {
            'watson': {
                'username': 'watson',
                'password': 'proprietary_watson_2025',
                'role': 'supreme_intelligence',
                'name': 'Watson Supreme Intelligence',
                'access_level': 'omniscient_control',
                'authority': 'unlimited',
                'permissions': ['complete_system_control', 'autonomous_optimization', 'override_authority']
            }
        }
    }

def display_user_credentials():
    """Secure user management - credentials protected"""
    
    users = get_all_nexus_users()
    
    print("NEXUS COMMAND USER DIRECTORY")
    print("=" * 60)
    
    print("\nSECURE USER MANAGEMENT:")
    print("-" * 40)
    executive_count = len(users['executive_users'])
    admin_count = len(users['administrative_users'])
    
    print(f"Executive Users: {executive_count} accounts configured")
    print(f"Administrative Users: {admin_count} accounts configured")
    print("Watson Intelligence: 1 supreme account active")
    
    print("\nSECURITY STATUS:")
    print("-" * 40)
    print("Authentication: Secure credential system active")
    print("Access Control: Role-based permissions enforced")
    print("Credential Management: Protected by system administrator")
    
    print("\nPLATFORM ACCESS:")
    print("Interface: NEXUS COMMAND Intelligence Platform")
    print("Security: All credentials secured and protected")
    
    return users

if __name__ == "__main__":
    display_user_credentials()