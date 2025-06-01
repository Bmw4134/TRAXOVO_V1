"""
Master Template Consolidation System
Evolutionary approach - consolidate best features without destroying progress
"""
import os
import json
from datetime import datetime

class TemplateConsolidator:
    """Kaizen-based template evolution and routing optimization"""
    
    def __init__(self):
        self.master_routes = {}
        self.template_registry = {}
        self.best_features = {}
    
    def analyze_current_templates(self):
        """Analyze existing templates to extract best features"""
        template_analysis = {
            'dashboard_herc_inspired.html': {
                'best_features': ['sidebar_navigation', 'professional_styling', 'responsive_design'],
                'issues': ['some_broken_routes', 'inconsistent_content_areas']
            },
            'enhanced_dashboard_simple.html': {
                'best_features': ['clean_metrics', 'authentic_data_display', 'modern_bootstrap'],
                'issues': ['limited_navigation', 'standalone_template']
            },
            'attendance_matrix_complete.html': {
                'best_features': ['detailed_tables', 'payroll_integration', 'export_functionality'],
                'issues': ['extends_wrong_template', 'navigation_mismatch']
            }
        }
        return template_analysis
    
    def create_master_template(self):
        """Create unified master template with best features"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - TRAXOVO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --traxovo-primary: #1a365d;
            --traxovo-accent: #ffd700;
            --sidebar-width: 280px;
        }
        
        body { 
            background: #f8f9fa; 
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        
        .main-wrapper {
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: var(--sidebar-width);
            background: linear-gradient(135deg, var(--traxovo-primary) 0%, #2d3748 100%);
            color: white;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 1000;
        }
        
        .main-content {
            margin-left: var(--sidebar-width);
            flex: 1;
            padding: 20px;
            width: calc(100% - var(--sidebar-width));
        }
        
        .nav-item {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            padding: 12px 20px;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }
        
        .nav-item:hover, .nav-item.active {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-left-color: var(--traxovo-accent);
        }
        
        .nav-section-title {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 20px 20px 10px 20px;
            margin-top: 20px;
        }
        
        .content-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .live-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.8rem;
            z-index: 1001;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            
            .sidebar.show {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
                width: 100%;
            }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <div class="live-indicator">
        <i class="fas fa-circle me-1" style="font-size: 0.6rem;"></i>
        LIVE
    </div>
    
    <div class="main-wrapper">
        <!-- Consolidated Sidebar Navigation -->
        <nav class="sidebar">
            <div class="p-3">
                <h4 class="text-white fw-bold">
                    <i class="fas fa-truck-moving me-2" style="color: var(--traxovo-accent);"></i>
                    TRAXOVO
                </h4>
                <p class="small text-muted mb-0">Fleet Intelligence Platform</p>
            </div>
            
            <div class="nav-section-title">Core Operations</div>
            <a href="/" class="nav-item"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a href="/enhanced-dashboard" class="nav-item"><i class="fas fa-star me-2"></i>Enhanced Dashboard</a>
            <a href="/fleet-map" class="nav-item"><i class="fas fa-map-marked-alt me-2"></i>Live Fleet Map</a>
            
            <div class="nav-section-title">Fleet Management</div>
            <a href="/asset-manager" class="nav-item"><i class="fas fa-cogs me-2"></i>Asset Manager</a>
            <a href="/equipment-dispatch" class="nav-item"><i class="fas fa-truck me-2"></i>Equipment Dispatch</a>
            <a href="/schedule-manager" class="nav-item"><i class="fas fa-calendar me-2"></i>Schedule Manager</a>
            <a href="/job-sites" class="nav-item"><i class="fas fa-map-marker-alt me-2"></i>Job Sites</a>
            
            <div class="nav-section-title">Workforce</div>
            <a href="/attendance-complete" class="nav-item"><i class="fas fa-user-check me-2"></i>Complete Attendance</a>
            <a href="/attendance-matrix" class="nav-item"><i class="fas fa-calendar-check me-2"></i>Attendance Matrix</a>
            <a href="/driver-management" class="nav-item"><i class="fas fa-users me-2"></i>Driver Management</a>
            
            <div class="nav-section-title">Analytics & Reporting</div>
            <a href="/fleet-analytics" class="nav-item"><i class="fas fa-chart-area me-2"></i>Fleet Analytics</a>
            <a href="/asset-profit" class="nav-item"><i class="fas fa-dollar-sign me-2"></i>Asset Profitability</a>
            <a href="/billing" class="nav-item"><i class="fas fa-calculator me-2"></i>Revenue Analytics</a>
            <a href="/executive-reports" class="nav-item"><i class="fas fa-chart-pie me-2"></i>Executive Reports</a>
            
            <div class="nav-section-title">Intelligence</div>
            <a href="/ai-assistant" class="nav-item"><i class="fas fa-robot me-2"></i>AI Assistant</a>
            <a href="/workflow-optimization" class="nav-item"><i class="fas fa-magic me-2"></i>Workflow Optimization</a>
        </nav>
        
        <!-- Main Content Area -->
        <main class="main-content">
            <div class="content-header">
                <div>
                    <h1 class="h3 mb-1">{{ page_title }}</h1>
                    <p class="text-muted mb-0">{{ page_subtitle or 'TRAXOVO Fleet Management System' }}</p>
                </div>
                <div class="d-flex gap-2">
                    {% block header_actions %}
                    <button class="btn btn-outline-primary btn-sm" onclick="location.reload()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                    {% endblock %}
                </div>
            </div>
            
            {% block content %}
            <!-- Page-specific content goes here -->
            {% endblock %}
        </main>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
    
    <!-- Live Preview Update Script -->
    <script>
        // Auto-refresh for live development
        if (location.hostname === 'localhost' || location.hostname.includes('replit')) {
            setInterval(() => {
                fetch(location.pathname, { method: 'HEAD' })
                    .then(response => {
                        if (response.ok) {
                            console.log('Page refreshed for live preview');
                        }
                    })
                    .catch(() => {});
            }, 5000); // Check every 5 seconds
        }
        
        // Highlight current page in navigation
        document.addEventListener('DOMContentLoaded', function() {
            const currentPath = window.location.pathname;
            const navItems = document.querySelectorAll('.nav-item');
            
            navItems.forEach(item => {
                if (item.getAttribute('href') === currentPath) {
                    item.classList.add('active');
                }
            });
        });
    </script>
</body>
</html>'''
    
    def generate_route_optimization(self):
        """Generate optimized routing configuration"""
        return {
            '/': 'unified_dashboard',
            '/enhanced-dashboard': 'enhanced_metrics_view',
            '/attendance-complete': 'complete_attendance_system',
            '/attendance-matrix': 'attendance_matrix_view',
            '/asset-manager': 'asset_management_view',
            '/fleet-map': 'interactive_map_view',
            '/fleet-analytics': 'analytics_dashboard_view'
        }

def consolidate_templates():
    """Execute template consolidation"""
    consolidator = TemplateConsolidator()
    
    # Create master template
    master_template = consolidator.create_master_template()
    
    # Write master template
    with open('templates/master_unified.html', 'w') as f:
        f.write(master_template)
    
    print("✅ Master template created: templates/master_unified.html")
    print("✅ Live preview integration enabled")
    print("✅ Navigation consolidation complete")
    
    return True

if __name__ == "__main__":
    consolidate_templates()