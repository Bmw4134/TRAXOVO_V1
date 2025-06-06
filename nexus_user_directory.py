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
    """Display formatted user credentials for NEXUS COMMAND"""
    
    users = get_all_nexus_users()
    
    print("NEXUS COMMAND USER DIRECTORY")
    print("=" * 60)
    
    print("\nEXECUTIVE USERS:")
    print("-" * 40)
    for username, details in users['executive_users'].items():
        print(f"{details['name']:12} | {username:10} | {details['password']:15}")
    
    print("\nADMINISTRATIVE USERS:")
    print("-" * 40)
    for username, details in users['administrative_users'].items():
        print(f"{details['name']:12} | {username:10} | {details['password']:15}")
    
    print("\nWATSON SUPREME INTELLIGENCE:")
    print("-" * 40)
    for username, details in users['watson_supreme'].items():
        print(f"{details['name']:25} | {username:10} | {details['password']:25}")
    
    print("\nPLATFORM ACCESS:")
    print("URL: Your Replit app URL (automatically available)")
    print("Interface: NEXUS COMMAND Intelligence Platform")
    print("Authentication: Username/Password login system")
    
    return users

if __name__ == "__main__":
    display_user_credentials()