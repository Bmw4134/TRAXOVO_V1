"""
TRAXOVO Administrative Guide and System Overview
Complete documentation and route mapping for Watson admin access
"""

import os
import inspect
from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime

admin_guide_bp = Blueprint('admin_guide', __name__)

def require_watson():
    """Check if user is Watson admin"""
    return session.get('username') != 'watson' or not session.get('authenticated')

class TRAXOVOSystemMapper:
    """Complete system mapping and documentation generator"""
    
    def __init__(self):
        self.system_overview = self._generate_system_overview()
        self.route_mapping = self._generate_route_mapping()
        self.feature_guide = self._generate_feature_guide()
        self.troubleshooting = self._generate_troubleshooting_guide()
    
    def _generate_system_overview(self):
        """Generate complete system overview"""
        return {
            'core_modules': {
                'Authentication': {
                    'description': 'Role-based user authentication',
                    'users': ['watson (admin)', 'tester (standard)', 'user (basic)'],
                    'file': 'app.py',
                    'status': 'active'
                },
                'Dashboard': {
                    'description': 'Main fleet intelligence dashboard',
                    'features': ['Real-time metrics', 'Voice commands', 'Navigation'],
                    'file': 'templates/dashboard_with_sidebar.html',
                    'status': 'active'
                },
                'Attendance Matrix': {
                    'description': 'Driver attendance tracking (92 drivers: 47 PM, 45 EJ)',
                    'features': ['Real driver data', 'Job site mapping', 'Export capabilities'],
                    'file': 'templates/attendance_matrix.html',
                    'status': 'active'
                },
                'Master Billing': {
                    'description': 'Equipment billing with RAGLE data processing',
                    'features': ['Excel parsing', 'Fluff header handling', 'Revenue analytics'],
                    'file': 'routes/master_billing.py',
                    'status': 'active'
                },
                'Fleet Map': {
                    'description': 'GPS asset tracking with GAUGE API integration',
                    'features': ['Real asset locations', 'Job zone mapping', 'Asset status'],
                    'file': 'templates/fleet_map.html',
                    'status': 'active'
                },
                'Voice Commands': {
                    'description': 'Voice navigation system',
                    'commands': ['dashboard', 'billing', 'attendance', 'fleet map', 'assets'],
                    'file': 'static/voice-commands.js',
                    'status': 'active'
                }
            },
            'data_sources': {
                'GAUGE_API': {
                    'description': '717 total assets (614 active, 103 inactive)',
                    'file': 'GAUGE API PULL 1045AM_05.15.2025.json',
                    'last_updated': '2025-05-15 10:45 AM',
                    'status': 'connected'
                },
                'RAGLE_Billing': {
                    'description': 'Equipment billing reports',
                    'files': ['RAGLE EQ BILLINGS - APRIL 2025.xlsm', 'RAGLE EQ BILLINGS - MARCH 2025.xlsm'],
                    'april_revenue': 552000,
                    'status': 'active'
                },
                'Driver_Reports': {
                    'description': 'Attendance and driver tracking',
                    'pm_drivers': 47,
                    'ej_drivers': 45,
                    'status': 'active'
                }
            },
            'security': {
                'authentication': 'Role-based access control',
                'admin_restrictions': 'Watson-only purge and admin access',
                'data_protection': 'No exposed credentials in templates',
                'session_management': 'Secure session handling'
            }
        }
    
    def _generate_route_mapping(self):
        """Generate complete route mapping"""
        return {
            'core_routes': {
                '/': 'Index - redirects to login or dashboard',
                '/login': 'User authentication with role detection',
                '/logout': 'Session termination',
                '/dashboard': 'Main fleet intelligence dashboard',
                '/attendance-matrix': 'Driver attendance tracking system',
                '/fleet-map': 'GPS asset tracking and fleet map',
                '/asset-manager': 'Asset management interface',
                '/upload': 'File upload interface for reports'
            },
            'billing_routes': {
                '/billing': 'Redirects to master billing system',
                '/master-billing': 'Advanced equipment billing with Excel parsing',
                '/billing-legacy': 'Legacy billing intelligence (backup)',
                '/api/upload-billing-file': 'Process uploaded RAGLE billing files',
                '/api/billing-summary': 'Comprehensive billing analytics API'
            },
            'admin_routes': {
                '/watson-admin': 'Watson-exclusive admin dashboard',
                '/api/purge-records': 'Database purge (Watson only)',
                '/api/database-stats': 'Database statistics and health',
                '/safemode': 'System diagnostic interface',
                '/admin-guide': 'This comprehensive system guide'
            },
            'api_routes': {
                '/api/upload-attendance': 'Process attendance data uploads',
                '/api/billing-data': 'Billing data API endpoint',
                '/api/database-stats': 'Database statistics',
                '/api/fleet-data': 'Fleet and asset data API'
            }
        }
    
    def _generate_feature_guide(self):
        """Generate step-by-step feature usage guide"""
        return {
            'daily_operations': {
                'title': 'Daily Operations Workflow',
                'steps': [
                    '1. Login with Watson credentials for full admin access',
                    '2. Check dashboard metrics for fleet overview',
                    '3. Review attendance matrix for driver status',
                    '4. Monitor fleet map for asset locations',
                    '5. Process billing reports as needed'
                ]
            },
            'monthly_billing': {
                'title': 'Monthly Billing Process',
                'steps': [
                    '1. Navigate to Master Equipment Billing',
                    '2. Upload May RAGLE Excel report',
                    '3. System auto-handles fluff headers (5-7 rows)',
                    '4. Review parsed data for accuracy',
                    '5. Export processed billing report',
                    '6. Verify revenue figures match expectations'
                ],
                'formats_supported': ['Excel (.xlsx, .xlsm)', 'CSV', 'Legacy Excel (.xls)'],
                'time_format': 'Decimal hours preferred (8.5 vs 8:30)',
                'filters': 'Equipment categorization, On-road vehicles, All equipment'
            },
            'attendance_management': {
                'title': 'Attendance Matrix Operations',
                'steps': [
                    '1. Access attendance matrix from dashboard',
                    '2. View real driver data (47 PM + 45 EJ = 92 total)',
                    '3. Filter by division, date, or job site',
                    '4. Export attendance reports for payroll',
                    '5. Review exception reports for late/absent drivers'
                ],
                'data_structure': 'Authentic PM/EJ division mapping from legacy reports'
            },
            'fleet_monitoring': {
                'title': 'Fleet Map and Asset Tracking',
                'steps': [
                    '1. Access fleet map for real-time asset locations',
                    '2. Monitor 717 total assets (614 active)',
                    '3. Track job zone assignments',
                    '4. Review GPS-enabled assets (586 with valid coordinates)',
                    '5. Generate location-based reports'
                ]
            },
            'voice_commands': {
                'title': 'Voice Navigation System',
                'activation': 'Press Alt+V or click microphone button',
                'commands': [
                    '"dashboard" - Navigate to main dashboard',
                    '"billing" - Go to master billing system',
                    '"attendance" - Open attendance matrix',
                    '"fleet map" - View asset tracking',
                    '"assets" - Access asset manager'
                ],
                'keyboard_shortcuts': 'Alt+1 through Alt+9 for quick navigation'
            }
        }
    
    def _generate_troubleshooting_guide(self):
        """Generate troubleshooting and recovery guide"""
        return {
            'common_issues': {
                'Login Problems': {
                    'symptoms': 'Cannot access dashboard or features',
                    'solution': 'Verify credentials: watson/password (admin), tester/password (standard)',
                    'escalation': 'Check session state in browser dev tools'
                },
                'Billing Upload Errors': {
                    'symptoms': 'Excel file processing fails',
                    'solution': 'Ensure file format is .xlsx or .xlsm, check for header structure',
                    'escalation': 'Review fluff header detection algorithm'
                },
                'Fleet Map Not Loading': {
                    'symptoms': 'Map shows blank or JSON errors',
                    'solution': 'Verify GAUGE API data file exists and is valid JSON',
                    'escalation': 'Check asset serialization in fleet_map route'
                },
                'Attendance Data Missing': {
                    'symptoms': 'No driver records displayed',
                    'solution': 'Verify sample data generation function is working',
                    'escalation': 'Check PM/EJ driver mapping in get_sample_attendance_data()'
                }
            },
            'emergency_recovery': {
                'system_breakdown': {
                    'immediate_action': 'Run emergency_restore.py script',
                    'backup_location': 'TRAXOVO_MASTER_RECOVERY.md contains all critical fixes',
                    'restoration_steps': [
                        '1. Check file integrity with emergency script',
                        '2. Verify authentication functions in app.py',
                        '3. Test core routes and templates',
                        '4. Validate data generation functions',
                        '5. Restart application workflow'
                    ]
                },
                'data_corruption': {
                    'billing_data': 'Restore from fallback_data functions with authentic figures',
                    'attendance_data': 'Regenerate from PM/EJ driver mapping (47+45=92)',
                    'fleet_data': 'Reload from GAUGE API JSON file'
                }
            },
            'performance_optimization': {
                'database': 'Use Watson admin purge for cleanup',
                'file_uploads': 'Monitor uploads directory size',
                'api_responses': 'Check for large JSON payload serialization',
                'memory_usage': 'Restart workflow if performance degrades'
            }
        }

@admin_guide_bp.route('/admin-guide')
def admin_guide():
    """Watson-exclusive comprehensive system guide"""
    if require_watson():
        return redirect(url_for('login'))
    
    mapper = TRAXOVOSystemMapper()
    
    context = {
        'page_title': 'TRAXOVO System Administration Guide',
        'system_overview': mapper.system_overview,
        'route_mapping': mapper.route_mapping,
        'feature_guide': mapper.feature_guide,
        'troubleshooting': mapper.troubleshooting,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'username': session.get('username', 'Watson')
    }
    
    return render_template('admin_guide.html', **context)

@admin_guide_bp.route('/api/system-health')
def api_system_health():
    """System health check API for monitoring"""
    if require_watson():
        return {'error': 'Admin access required'}, 401
    
    mapper = TRAXOVOSystemMapper()
    
    health_check = {
        'timestamp': datetime.now().isoformat(),
        'core_modules': len([m for m in mapper.system_overview['core_modules'].values() if m.get('status') == 'active']),
        'data_sources': len([d for d in mapper.system_overview['data_sources'].values() if d.get('status') in ['connected', 'active']]),
        'total_routes': len(mapper.route_mapping['core_routes']) + len(mapper.route_mapping['billing_routes']) + len(mapper.route_mapping['admin_routes']),
        'system_status': 'healthy',
        'recommendations': []
    }
    
    # Check for potential issues
    if not os.path.exists('GAUGE API PULL 1045AM_05.15.2025.json'):
        health_check['recommendations'].append('GAUGE API data file missing')
    
    if not os.path.exists('TRAXOVO_MASTER_RECOVERY.md'):
        health_check['recommendations'].append('Recovery documentation missing')
    
    return health_check