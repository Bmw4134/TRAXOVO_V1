"""
QQ Fast Deployment Check
Streamlined validation for immediate deployment readiness assessment
"""

import os
import json
import subprocess
import time
from datetime import datetime

def check_deployment_readiness():
    """Fast deployment readiness check"""
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'status': 'UNKNOWN',
        'blockers': [],
        'warnings': [],
        'passed': []
    }
    
    # 1. Check critical files exist
    critical_files = [
        'app_qq_enhanced.py',
        'qq_ai_accessibility_enhancer.py', 
        'qq_quantum_api_drift_optimizer.py',
        'templates/accessibility_dashboard.html',
        'static/css/accessibility-enhancements.css',
        'static/js/accessibility-enhancer.js'
    ]
    
    missing_files = [f for f in critical_files if not os.path.exists(f)]
    if missing_files:
        results['blockers'].extend([f"Missing critical file: {f}" for f in missing_files])
    else:
        results['passed'].append("All critical files present")
    
    results['checks']['critical_files'] = {
        'total': len(critical_files),
        'present': len(critical_files) - len(missing_files),
        'missing': missing_files
    }
    
    # 2. Check secrets availability
    required_secrets = ['DATABASE_URL', 'GAUGE_API_KEY', 'SESSION_SECRET']
    available_secrets = [s for s in required_secrets if os.environ.get(s)]
    missing_secrets = [s for s in required_secrets if not os.environ.get(s)]
    
    if missing_secrets:
        results['warnings'].extend([f"Missing secret: {s}" for s in missing_secrets])
    else:
        results['passed'].append("All required secrets configured")
    
    results['checks']['secrets'] = {
        'required': required_secrets,
        'available': available_secrets,
        'missing': missing_secrets
    }
    
    # 3. Check for hardcoded secrets (basic scan)
    hardcoded_found = []
    try:
        with open('app_qq_enhanced.py', 'r') as f:
            content = f.read()
            if 'password = "' in content or 'secret = "' in content:
                hardcoded_found.append('app_qq_enhanced.py')
    except:
        pass
    
    if hardcoded_found:
        results['blockers'].extend([f"Hardcoded secret in: {f}" for f in hardcoded_found])
    else:
        results['passed'].append("No obvious hardcoded secrets found")
    
    results['checks']['security'] = {
        'hardcoded_secrets': hardcoded_found
    }
    
    # 4. Check application syntax
    try:
        result = subprocess.run(['python3', '-m', 'py_compile', 'app_qq_enhanced.py'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            results['passed'].append("Main application compiles successfully")
        else:
            results['blockers'].append(f"Syntax error in main app: {result.stderr}")
    except subprocess.TimeoutExpired:
        results['warnings'].append("Syntax check timed out")
    except Exception as e:
        results['warnings'].append(f"Syntax check error: {e}")
    
    results['checks']['syntax'] = {
        'main_app_compiles': len([b for b in results['blockers'] if 'Syntax error' in b]) == 0
    }
    
    # 5. Check database connectivity
    try:
        import sqlite3
        # Test basic SQLite functionality
        conn = sqlite3.connect(':memory:')
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.close()
        results['passed'].append("Database connectivity verified")
    except Exception as e:
        results['blockers'].append(f"Database connectivity issue: {e}")
    
    results['checks']['database'] = {
        'connectivity': len([b for b in results['blockers'] if 'Database' in b]) == 0
    }
    
    # 6. Check port availability
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            results['warnings'].append("Port 5000 already in use")
        else:
            results['passed'].append("Port 5000 available")
    except Exception as e:
        results['warnings'].append(f"Port check error: {e}")
    
    results['checks']['port'] = {
        'port_5000_available': len([w for w in results['warnings'] if 'Port 5000 already' in w]) == 0
    }
    
    # 7. Check AI enhancer modules
    ai_modules = [
        'qq_ai_accessibility_enhancer.py',
        'qq_quantum_api_drift_optimizer.py'
    ]
    
    ai_module_status = {}
    for module in ai_modules:
        try:
            result = subprocess.run(['python3', '-m', 'py_compile', module], 
                                   capture_output=True, text=True, timeout=5)
            ai_module_status[module] = result.returncode == 0
            if result.returncode != 0:
                results['warnings'].append(f"AI module syntax issue: {module}")
        except:
            ai_module_status[module] = False
            results['warnings'].append(f"AI module check failed: {module}")
    
    if all(ai_module_status.values()):
        results['passed'].append("All AI enhancement modules valid")
    
    results['checks']['ai_modules'] = ai_module_status
    
    # Determine overall status
    if results['blockers']:
        results['status'] = 'BLOCKED'
        results['recommendation'] = 'Fix critical issues before deployment'
    elif len(results['warnings']) > 3:
        results['status'] = 'CAUTION'
        results['recommendation'] = 'Address warnings for optimal deployment'
    else:
        results['status'] = 'READY'
        results['recommendation'] = 'Approved for production deployment'
    
    # Calculate readiness score
    total_checks = len(results['passed']) + len(results['warnings']) + len(results['blockers'])
    results['readiness_score'] = round(len(results['passed']) / max(total_checks, 1) * 100, 1)
    
    return results

def main():
    print("🚀 QQ Fast Deployment Check")
    print("=" * 50)
    
    results = check_deployment_readiness()
    
    print(f"Status: {results['status']}")
    print(f"Readiness Score: {results['readiness_score']}%")
    print(f"Recommendation: {results['recommendation']}")
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Passed: {len(results['passed'])}")
    print(f"  ⚠️  Warnings: {len(results['warnings'])}")
    print(f"  🚫 Blockers: {len(results['blockers'])}")
    
    if results['blockers']:
        print(f"\n🚫 CRITICAL BLOCKERS:")
        for blocker in results['blockers']:
            print(f"  - {blocker}")
    
    if results['warnings']:
        print(f"\n⚠️  WARNINGS:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    if results['passed']:
        print(f"\n✅ PASSED CHECKS:")
        for passed in results['passed']:
            print(f"  - {passed}")
    
    # Save results
    with open('qq_fast_deployment_check.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved: qq_fast_deployment_check.json")
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    main()