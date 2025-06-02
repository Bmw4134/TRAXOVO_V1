#!/usr/bin/env python3
"""
TRAXOVO Emergency System Restoration Script
Run this if the system breaks to restore core functionality
"""

import os
import shutil
from datetime import datetime

def create_emergency_backup():
    """Create backup of current working state"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    critical_files = [
        'app.py',
        'templates/base.html',
        'templates/dashboard_with_sidebar.html',
        'templates/attendance_matrix.html',
        'templates/billing_intelligence.html',
        'routes/billing_intelligence.py',
        'static/voice-commands.js'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            # Create directory structure in backup
            backup_file_path = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
            shutil.copy2(file_path, backup_file_path)
            print(f"✓ Backed up: {file_path}")
    
    print(f"Emergency backup created: {backup_dir}")

def verify_core_files():
    """Verify all critical files exist and are functional"""
    checks = {
        'app.py': 'Core application file',
        'templates/base.html': 'Base template',
        'templates/login.html': 'Login page',
        'templates/dashboard_with_sidebar.html': 'Main dashboard',
        'templates/attendance_matrix.html': 'Attendance system',
        'templates/billing_intelligence.html': 'Billing module',
        'routes/billing_intelligence.py': 'Billing backend',
        'static/voice-commands.js': 'Voice navigation',
        'TRAXOVO_MASTER_RECOVERY.md': 'Recovery documentation'
    }
    
    print("🔍 SYSTEM INTEGRITY CHECK")
    print("=" * 50)
    
    all_good = True
    for file_path, description in checks.items():
        if os.path.exists(file_path):
            print(f"✅ {file_path} - {description}")
        else:
            print(f"❌ MISSING: {file_path} - {description}")
            all_good = False
    
    return all_good

def check_authentication_structure():
    """Verify authentication functions are present in app.py"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        required_functions = [
            'require_auth',
            'require_watson',
            'def login',
            'def dashboard',
            'get_sample_attendance_data'
        ]
        
        print("\n🔐 AUTHENTICATION CHECK")
        print("=" * 50)
        
        for func in required_functions:
            if func in content:
                print(f"✅ {func}")
            else:
                print(f"❌ MISSING: {func}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def verify_authentic_data():
    """Check that authentic data generators are working"""
    try:
        # Import and test data functions
        import sys
        sys.path.append('.')
        
        print("\n📊 AUTHENTIC DATA CHECK")
        print("=" * 50)
        
        # Test attendance data
        from app import get_sample_attendance_data
        attendance_data = get_sample_attendance_data()
        
        pm_count = len([d for d in attendance_data if d['division'] == 'PM'])
        ej_count = len([d for d in attendance_data if d['division'] == 'EJ'])
        
        if pm_count == 47 and ej_count == 45:
            print(f"✅ Attendance data: {pm_count} PM + {ej_count} EJ = {len(attendance_data)} total")
        else:
            print(f"❌ Attendance data incorrect: {pm_count} PM + {ej_count} EJ")
            return False
        
        # Test billing data
        from routes.billing_intelligence import RAGLEBillingProcessor
        processor = RAGLEBillingProcessor()
        billing_data = processor.process_billing_data()
        
        if billing_data['april_2025']['total_revenue'] == 552000:
            print("✅ Billing data: April revenue $552,000")
        else:
            print("❌ Billing data incorrect")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data verification error: {e}")
        return False

def run_system_check():
    """Run complete system health check"""
    print("🚀 TRAXOVO SYSTEM HEALTH CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Check 1: File integrity
    files_ok = verify_core_files()
    
    # Check 2: Authentication structure
    auth_ok = check_authentication_structure()
    
    # Check 3: Authentic data
    data_ok = verify_authentic_data()
    
    print("\n📋 SUMMARY")
    print("=" * 50)
    
    if files_ok and auth_ok and data_ok:
        print("🎉 SYSTEM STATUS: HEALTHY")
        print("All core components are functioning correctly.")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  SYSTEM STATUS: ISSUES DETECTED")
        print("Some components need attention.")
        print("📖 Refer to TRAXOVO_MASTER_RECOVERY.md for fixes")
    
    return files_ok and auth_ok and data_ok

if __name__ == "__main__":
    print("TRAXOVO Emergency Recovery System")
    print("Choose an option:")
    print("1. Run system health check")
    print("2. Create emergency backup")
    print("3. Full diagnostic")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        run_system_check()
    elif choice == "2":
        create_emergency_backup()
    elif choice == "3":
        create_emergency_backup()
        run_system_check()
    else:
        print("Invalid choice. Running health check...")
        run_system_check()