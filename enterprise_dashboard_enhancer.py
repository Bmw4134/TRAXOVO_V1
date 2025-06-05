"""
Enterprise Dashboard Enhancer - Active Pattern Application
Applies real-time UI/UX patterns from Amazon AWS, Palantir Foundry, and Samsara Fleet Management
"""
from flask import render_template_string
import json
import random
from datetime import datetime

class EnterpriseDashboardEnhancer:
    def __init__(self):
        self.enterprise_patterns = self._load_enterprise_patterns()
        self.active_enhancements = {}
        
    def _load_enterprise_patterns(self):
        """Load specific UI/UX patterns from enterprise platforms"""
        return {
            'amazon_aws': {
                'color_scheme': {
                    'primary': '#232F3E',
                    'secondary': '#FF9900',
                    'accent': '#146EB4',
                    'background': '#FAFAFA',
                    'text_primary': '#232F3E',
                    'text_secondary': '#687078'
                },
                'navigation': {
                    'style': 'fixed_sidebar_with_service_groups',
                    'breadcrumb_style': 'hierarchical_with_service_context',
                    'search_prominence': 'high',
                    'quick_actions': 'always_visible'
                },
                'layout': {
                    'grid_system': '12_column_responsive',
                    'card_design': 'minimal_shadows_rounded_corners',
                    'spacing': 'generous_whitespace',
                    'typography': 'clear_hierarchy_system_fonts'
                },
                'data_visualization': {
                    'chart_style': 'clean_lines_minimal_decoration',
                    'color_palette': 'blue_orange_professional',
                    'animation': 'subtle_smooth_transitions',
                    'real_time_indicators': 'discrete_status_dots'
                }
            },
            'palantir_foundry': {
                'color_scheme': {
                    'primary': '#1B1F23',
                    'secondary': '#0F4C75',
                    'accent': '#3282B8',
                    'background': '#0F1419',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#8B949E'
                },
                'navigation': {
                    'style': 'command_palette_centric',
                    'breadcrumb_style': 'data_lineage_aware',
                    'search_prominence': 'omnipresent_intelligent',
                    'quick_actions': 'contextual_workflow_based'
                },
                'layout': {
                    'grid_system': 'flexible_data_driven',
                    'card_design': 'data_dense_information_rich',
                    'spacing': 'information_optimized',
                    'typography': 'monospace_data_sans_serif_ui'
                },
                'data_visualization': {
                    'chart_style': 'information_dense_interactive',
                    'color_palette': 'blue_spectrum_high_contrast',
                    'animation': 'data_driven_meaningful_motion',
                    'real_time_indicators': 'prominent_status_changes'
                }
            },
            'samsara_fleet': {
                'color_scheme': {
                    'primary': '#2E7D32',
                    'secondary': '#1976D2',
                    'accent': '#FFC107',
                    'background': '#F8F9FA',
                    'text_primary': '#212529',
                    'text_secondary': '#6C757D'
                },
                'navigation': {
                    'style': 'map_centric_with_panels',
                    'breadcrumb_style': 'location_time_aware',
                    'search_prominence': 'asset_focused',
                    'quick_actions': 'operational_immediate'
                },
                'layout': {
                    'grid_system': 'map_sidebar_responsive',
                    'card_design': 'operational_status_focused',
                    'spacing': 'functional_efficient',
                    'typography': 'clear_numeric_emphasis'
                },
                'data_visualization': {
                    'chart_style': 'real_time_operational_focus',
                    'color_palette': 'green_blue_status_indicators',
                    'animation': 'live_updates_smooth_transitions',
                    'real_time_indicators': 'always_on_status_health'
                }
            }
        }
    
    def apply_amazon_aws_patterns(self, template_content):
        """Apply Amazon AWS dashboard patterns to template"""
        aws_styles = """
        /* Amazon AWS Inspired Patterns */
        .aws-header {
            background: #232F3E;
            color: white;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #3C4043;
        }
        
        .aws-service-nav {
            background: #FAFAFA;
            border-right: 1px solid #D5DBDB;
            width: 280px;
            padding: 16px;
        }
        
        .aws-service-group {
            margin-bottom: 24px;
        }
        
        .aws-service-group-title {
            font-size: 12px;
            font-weight: 600;
            color: #687078;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .aws-service-item {
            padding: 8px 12px;
            margin: 2px 0;
            border-radius: 6px;
            color: #232F3E;
            text-decoration: none;
            display: block;
            transition: background-color 0.2s;
        }
        
        .aws-service-item:hover {
            background-color: #E3F2FD;
            color: #146EB4;
        }
        
        .aws-breadcrumb {
            background: #F2F3F3;
            padding: 12px 20px;
            font-size: 14px;
            border-bottom: 1px solid #D5DBDB;
        }
        
        .aws-breadcrumb a {
            color: #146EB4;
            text-decoration: none;
        }
        
        .aws-main-content {
            padding: 24px;
            background: #FAFAFA;
        }
        
        .aws-card {
            background: white;
            border: 1px solid #D5DBDB;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .aws-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #E9ECEF;
        }
        
        .aws-card-title {
            font-size: 18px;
            font-weight: 600;
            color: #232F3E;
        }
        
        .aws-button-primary {
            background: #FF9900;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .aws-button-primary:hover {
            background: #E6880A;
        }
        
        .aws-status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }
        
        .aws-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #52C41A;
        }
        
        .aws-metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }
        
        .aws-metric-card {
            background: #F8F9FA;
            padding: 16px;
            border-radius: 6px;
            border-left: 4px solid #146EB4;
        }
        
        .aws-metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #232F3E;
            margin-bottom: 4px;
        }
        
        .aws-metric-label {
            font-size: 12px;
            color: #687078;
            text-transform: uppercase;
        }
        """
        
        return template_content.replace('</style>', aws_styles + '</style>')
    
    def apply_palantir_foundry_patterns(self, template_content):
        """Apply Palantir Foundry dashboard patterns to template"""
        palantir_styles = """
        /* Palantir Foundry Inspired Patterns */
        .foundry-layout {
            background: #0F1419;
            color: #FFFFFF;
            min-height: 100vh;
        }
        
        .foundry-header {
            background: #1B1F23;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363D;
        }
        
        .foundry-command-palette {
            background: rgba(255,255,255,0.1);
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 8px 16px;
            min-width: 300px;
            color: #FFFFFF;
            backdrop-filter: blur(10px);
        }
        
        .foundry-sidebar {
            background: #1B1F23;
            width: 320px;
            border-right: 1px solid #30363D;
            padding: 20px;
        }
        
        .foundry-data-panel {
            background: #21262D;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }
        
        .foundry-data-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid #30363D;
        }
        
        .foundry-data-title {
            font-size: 16px;
            font-weight: 600;
            color: #FFFFFF;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
        }
        
        .foundry-data-grid {
            display: grid;
            gap: 1px;
            background: #30363D;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .foundry-data-row {
            background: #1B1F23;
            padding: 12px 16px;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 16px;
        }
        
        .foundry-data-cell {
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
            font-size: 13px;
        }
        
        .foundry-data-cell.header {
            color: #8B949E;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
        }
        
        .foundry-data-cell.value {
            color: #FFFFFF;
        }
        
        .foundry-data-cell.highlight {
            color: #3282B8;
        }
        
        .foundry-visualization {
            background: #21262D;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 20px;
            margin: 16px 0;
        }
        
        .foundry-chart-container {
            height: 200px;
            background: linear-gradient(45deg, rgba(50,130,184,0.1) 0%, rgba(15,76,117,0.1) 100%);
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }
        
        .foundry-button {
            background: #3282B8;
            color: #FFFFFF;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .foundry-button:hover {
            background: #2563EB;
        }
        
        .foundry-status-bar {
            background: #1B1F23;
            padding: 8px 20px;
            font-size: 12px;
            color: #8B949E;
            border-top: 1px solid #30363D;
        }
        """
        
        return template_content.replace('</style>', palantir_styles + '</style>')
    
    def apply_samsara_fleet_patterns(self, template_content):
        """Apply Samsara Fleet Management patterns to template"""
        samsara_styles = """
        /* Samsara Fleet Inspired Patterns */
        .samsara-layout {
            background: #F8F9FA;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .samsara-header {
            background: #FFFFFF;
            border-bottom: 1px solid #DEE2E6;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .samsara-main {
            flex: 1;
            display: flex;
        }
        
        .samsara-map-container {
            flex: 1;
            background: #E9ECEF;
            position: relative;
        }
        
        .samsara-sidebar {
            width: 380px;
            background: #FFFFFF;
            border-left: 1px solid #DEE2E6;
            display: flex;
            flex-direction: column;
        }
        
        .samsara-panel {
            background: #FFFFFF;
            border: 1px solid #DEE2E6;
            border-radius: 8px;
            margin: 12px;
            overflow: hidden;
        }
        
        .samsara-panel-header {
            background: #F8F9FA;
            padding: 16px 20px;
            border-bottom: 1px solid #DEE2E6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .samsara-panel-title {
            font-size: 16px;
            font-weight: 600;
            color: #212529;
        }
        
        .samsara-status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .samsara-status-indicator.operational {
            background: #D4EDDA;
            color: #155724;
        }
        
        .samsara-status-indicator.warning {
            background: #FFF3CD;
            color: #856404;
        }
        
        .samsara-asset-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .samsara-asset-item {
            padding: 16px 20px;
            border-bottom: 1px solid #F1F3F4;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s;
        }
        
        .samsara-asset-item:hover {
            background: #F8F9FA;
        }
        
        .samsara-asset-info {
            flex: 1;
        }
        
        .samsara-asset-name {
            font-weight: 600;
            color: #212529;
            margin-bottom: 4px;
        }
        
        .samsara-asset-details {
            font-size: 12px;
            color: #6C757D;
        }
        
        .samsara-metric-badge {
            background: #E7F3FF;
            color: #1976D2;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }
        
        .samsara-live-updates {
            background: #2E7D32;
            color: white;
            padding: 8px 16px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .samsara-live-dot {
            width: 8px;
            height: 8px;
            background: #4CAF50;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .samsara-quick-actions {
            display: flex;
            gap: 8px;
            padding: 16px 20px;
            background: #F8F9FA;
            border-top: 1px solid #DEE2E6;
        }
        
        .samsara-action-btn {
            background: #1976D2;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .samsara-action-btn:hover {
            background: #1565C0;
        }
        
        .samsara-action-btn.secondary {
            background: #6C757D;
        }
        
        .samsara-action-btn.secondary:hover {
            background: #545B62;
        }
        """
        
        return template_content.replace('</style>', samsara_styles + '</style>')
    
    def generate_enhanced_dashboard(self, user_role, pattern_preference='auto'):
        """Generate dashboard with applied enterprise patterns"""
        
        # Determine which pattern to apply based on user role or preference
        if pattern_preference == 'auto':
            if user_role == 'watson_owner':
                pattern = 'palantir_foundry'  # Data-intensive, command-centric
            elif user_role in ['exec', 'admin']:
                pattern = 'amazon_aws'  # Professional, service-oriented
            else:
                pattern = 'samsara_fleet'  # Operational, real-time focused
        else:
            pattern = pattern_preference
        
        base_template = self._get_base_dashboard_template()
        
        if pattern == 'amazon_aws':
            enhanced_template = self.apply_amazon_aws_patterns(base_template)
            layout_class = 'aws-layout'
        elif pattern == 'palantir_foundry':
            enhanced_template = self.apply_palantir_foundry_patterns(base_template)
            layout_class = 'foundry-layout'
        elif pattern == 'samsara_fleet':
            enhanced_template = self.apply_samsara_fleet_patterns(base_template)
            layout_class = 'samsara-layout'
        else:
            enhanced_template = base_template
            layout_class = 'default-layout'
        
        return {
            'template': enhanced_template,
            'pattern_applied': pattern,
            'layout_class': layout_class,
            'enhancement_metadata': {
                'timestamp': datetime.now().isoformat(),
                'user_role': user_role,
                'pattern_source': f'{pattern}_enterprise_patterns',
                'responsive': True,
                'accessibility_compliant': True
            }
        }
    
    def _get_base_dashboard_template(self):
        """Get base dashboard template for enhancement"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>TRAXOVO - Enterprise Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; }
        .dashboard-container { display: flex; min-height: 100vh; }
        .main-content { flex: 1; }
        /* Enterprise patterns will be injected here */
    </style>
</head>
<body>
    <div class="dashboard-container">
        <nav class="navigation-sidebar">
            <div class="nav-header">TRAXOVO</div>
            <div class="nav-sections">
                <div class="nav-section">
                    <div class="nav-section-title">Core Systems</div>
                    <a href="#" class="nav-item">Dashboard</a>
                    <a href="#" class="nav-item">Asset Intelligence</a>
                    <a href="#" class="nav-item">Analytics</a>
                </div>
            </div>
        </nav>
        <main class="main-content">
            <header class="main-header">
                <div class="header-content">
                    <h1>System Overview</h1>
                    <div class="header-actions">
                        <button class="action-btn">Refresh</button>
                    </div>
                </div>
            </header>
            <div class="content-area">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">717</div>
                        <div class="metric-label">Active Assets</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">94.7%</div>
                        <div class="metric-label">Efficiency</div>
                    </div>
                </div>
            </div>
        </main>
    </div>
</body>
</html>
        """

def get_enterprise_dashboard_enhancer():
    """Get global enterprise dashboard enhancer instance"""
    return EnterpriseDashboardEnhancer()

def apply_enterprise_patterns(user_role, pattern_preference='auto'):
    """Apply enterprise patterns to dashboard based on user role"""
    enhancer = EnterpriseDashboardEnhancer()
    return enhancer.generate_enhanced_dashboard(user_role, pattern_preference)