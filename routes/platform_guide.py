"""
TRAXOVO Platform Navigation Guide and Walkthrough System
"""

from flask import Blueprint, render_template, jsonify

platform_guide_bp = Blueprint('platform_guide', __name__)

def get_platform_navigation():
    """Complete TRAXOVO platform navigation structure"""
    return {
        'core_modules': {
            'Executive Dashboard': {
                'route': '/enhanced-dashboard',
                'purpose': 'High-level fleet overview with KPIs',
                'key_features': ['Cost savings analysis', 'ROI metrics', 'Fleet utilization', 'Executive drill-downs'],
                'use_case': 'Daily executive review and strategic decision making'
            },
            'Fleet Map': {
                'route': '/fleet-map',
                'purpose': 'Real-time GPS tracking and asset visualization',
                'key_features': ['701 asset tracking', 'Geofence monitoring', 'Asset trails', 'Status filtering'],
                'use_case': 'Operational dispatch and asset location management'
            },
            'Attendance Matrix': {
                'route': '/attendance-matrix',
                'purpose': 'Workforce tracking and productivity analysis',
                'key_features': ['Driver status', 'Time tracking', 'GPS validation', 'Compliance monitoring'],
                'use_case': 'HR management and payroll verification'
            }
        },
        'financial_modules': {
            'Billing Consolidation': {
                'route': '/billing-consolidation',
                'purpose': 'Unified view of all Foundation billing data',
                'key_features': ['Duplicate detection', 'Multi-file processing', 'Export capabilities', 'Data validation'],
                'use_case': 'Financial reconciliation and executive reporting'
            },
            'Cost Savings Simulator': {
                'route': '/cost-simulator',
                'purpose': 'Rental vs ownership analysis',
                'key_features': ['ROI calculations', 'Break-even analysis', 'Equipment-specific scenarios', 'Fleet optimization'],
                'use_case': 'Equipment acquisition and disposal decisions'
            },
            'Revenue Analytics': {
                'route': '/billing',
                'purpose': 'Revenue performance and profitability',
                'key_features': ['Project profitability', 'Equipment revenue', 'Trend analysis', 'Performance metrics'],
                'use_case': 'Financial performance monitoring'
            }
        },
        'operational_modules': {
            'Asset Manager': {
                'route': '/asset-manager',
                'purpose': 'Equipment lifecycle and maintenance',
                'key_features': ['Asset tracking', 'Maintenance scheduling', 'Utilization analysis', 'Performance metrics'],
                'use_case': 'Equipment management and optimization'
            },
            'Project Accountability': {
                'route': '/project-accountability',
                'purpose': 'Project-based asset allocation',
                'key_features': ['Project tracking', 'Asset assignment', 'Cost allocation', 'Performance monitoring'],
                'use_case': 'Project management and cost control'
            }
        },
        'intelligence_modules': {
            'Predictive Analytics': {
                'route': '/predictive-dashboard',
                'purpose': 'AI-powered insights and forecasting',
                'key_features': ['Maintenance prediction', 'Usage forecasting', 'Performance trends', 'Risk analysis'],
                'use_case': 'Proactive fleet management'
            },
            'Executive Reports': {
                'route': '/executive-reports',
                'purpose': 'Comprehensive reporting suite',
                'key_features': ['Custom reports', 'Automated generation', 'Data export', 'Trend analysis'],
                'use_case': 'Stakeholder communication and compliance'
            }
        }
    }

def get_workflow_guides():
    """Step-by-step workflow guides for common tasks"""
    return {
        'daily_operations': {
            'title': 'Daily Operations Workflow',
            'steps': [
                {'step': 1, 'action': 'Start at Executive Dashboard', 'route': '/enhanced-dashboard', 'purpose': 'Review overnight alerts and KPIs'},
                {'step': 2, 'action': 'Check Fleet Map', 'route': '/fleet-map', 'purpose': 'Verify asset locations and operational status'},
                {'step': 3, 'action': 'Review Attendance Matrix', 'route': '/attendance-matrix', 'purpose': 'Confirm workforce deployment'},
                {'step': 4, 'action': 'Monitor Active Projects', 'route': '/project-accountability', 'purpose': 'Track project progress and resource allocation'}
            ]
        },
        'weekly_financial_review': {
            'title': 'Weekly Financial Review',
            'steps': [
                {'step': 1, 'action': 'Process Billing Data', 'route': '/billing-consolidation', 'purpose': 'Consolidate all Foundation billing files'},
                {'step': 2, 'action': 'Export Financial Reports', 'route': '/api/executive-report', 'purpose': 'Generate executive summary'},
                {'step': 3, 'action': 'Review Cost Savings', 'route': '/cost-simulator', 'purpose': 'Analyze equipment ROI and optimization opportunities'},
                {'step': 4, 'action': 'Update Revenue Analytics', 'route': '/billing', 'purpose': 'Track financial performance trends'}
            ]
        },
        'equipment_decision_workflow': {
            'title': 'Equipment Acquisition/Disposal Decision',
            'steps': [
                {'step': 1, 'action': 'Analyze Current Fleet', 'route': '/asset-manager', 'purpose': 'Review current equipment utilization'},
                {'step': 2, 'action': 'Run Cost Simulation', 'route': '/cost-simulator', 'purpose': 'Compare rental vs purchase scenarios'},
                {'step': 3, 'action': 'Check Predictive Analytics', 'route': '/predictive-dashboard', 'purpose': 'Review maintenance and usage forecasts'},
                {'step': 4, 'action': 'Generate Executive Report', 'route': '/api/executive-report', 'purpose': 'Document decision rationale'}
            ]
        }
    }

@platform_guide_bp.route('/platform-guide')
def platform_guide():
    """TRAXOVO Platform Navigation Guide"""
    navigation = get_platform_navigation()
    workflows = get_workflow_guides()
    
    context = {
        'page_title': 'TRAXOVO Platform Guide',
        'navigation': navigation,
        'workflows': workflows,
        'total_modules': sum(len(modules) for modules in navigation.values()),
        'quick_links': [
            {'name': 'Executive Dashboard', 'route': '/enhanced-dashboard', 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Fleet Map', 'route': '/fleet-map', 'icon': 'fas fa-map-marked-alt'},
            {'name': 'Billing Consolidation', 'route': '/billing-consolidation', 'icon': 'fas fa-database'},
            {'name': 'Cost Simulator', 'route': '/cost-simulator', 'icon': 'fas fa-calculator'}
        ]
    }
    
    return render_template('platform_guide.html', **context)

@platform_guide_bp.route('/api/navigation-help')
def navigation_help():
    """API endpoint for navigation assistance"""
    return jsonify({
        'platform_structure': get_platform_navigation(),
        'workflow_guides': get_workflow_guides(),
        'help_resources': {
            'data_export': 'Use /api/billing-export for comprehensive financial data',
            'executive_reporting': 'Use /api/executive-report for leadership summaries',
            'real_time_updates': 'Fleet map updates every 15 seconds in real-time mode',
            'data_integrity': 'All data sourced from authentic Foundation billing files'
        }
    })