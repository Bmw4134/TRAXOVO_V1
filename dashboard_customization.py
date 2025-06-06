"""
Personalized Dashboard Customization Toolkit
Advanced dashboard builder with drag-and-drop interface and custom widgets
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str
    title: str
    position: Dict[str, int]  # x, y, width, height
    config: Dict[str, Any]
    data_source: str
    refresh_interval: int
    visible: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class DashboardLayout:
    """Dashboard layout configuration"""
    layout_id: str
    user_id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    grid_config: Dict[str, Any]
    theme: str
    is_default: bool = False
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

class DashboardCustomizationEngine:
    """Advanced dashboard customization system"""
    
    def __init__(self):
        self.widget_templates = self._initialize_widget_templates()
        self.data_sources = self._initialize_data_sources()
        self.themes = self._initialize_themes()
        self.user_layouts = {}
        
    def _initialize_widget_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available widget templates"""
        
        templates = {
            'metrics_card': {
                'name': 'Metrics Card',
                'description': 'Display key performance metrics',
                'default_config': {
                    'metric_type': 'revenue',
                    'display_format': 'currency',
                    'show_trend': True,
                    'show_comparison': True,
                    'color_scheme': 'blue'
                },
                'data_requirements': ['value', 'trend', 'comparison'],
                'size_constraints': {'min_width': 2, 'min_height': 1}
            },
            'line_chart': {
                'name': 'Line Chart',
                'description': 'Time series data visualization',
                'default_config': {
                    'chart_type': 'line',
                    'time_range': '7_days',
                    'smooth_curves': True,
                    'show_points': True,
                    'fill_area': False
                },
                'data_requirements': ['time_series', 'labels'],
                'size_constraints': {'min_width': 3, 'min_height': 2}
            },
            'gauge_chart': {
                'name': 'Gauge Chart',
                'description': 'Progress and performance indicators',
                'default_config': {
                    'gauge_type': 'circular',
                    'min_value': 0,
                    'max_value': 100,
                    'target_value': 80,
                    'color_zones': True
                },
                'data_requirements': ['current_value', 'target_value'],
                'size_constraints': {'min_width': 2, 'min_height': 2}
            },
            'data_table': {
                'name': 'Data Table',
                'description': 'Tabular data display with sorting',
                'default_config': {
                    'show_pagination': True,
                    'items_per_page': 10,
                    'sortable_columns': True,
                    'searchable': True,
                    'exportable': True
                },
                'data_requirements': ['table_data', 'columns'],
                'size_constraints': {'min_width': 4, 'min_height': 3}
            },
            'activity_feed': {
                'name': 'Activity Feed',
                'description': 'Real-time activity and notifications',
                'default_config': {
                    'max_items': 20,
                    'auto_refresh': True,
                    'show_timestamps': True,
                    'filter_by_type': True,
                    'grouping': 'chronological'
                },
                'data_requirements': ['activities', 'timestamps'],
                'size_constraints': {'min_width': 3, 'min_height': 4}
            },
            'map_widget': {
                'name': 'Interactive Map',
                'description': 'Geographic data visualization',
                'default_config': {
                    'map_type': 'satellite',
                    'zoom_level': 10,
                    'show_markers': True,
                    'cluster_markers': True,
                    'show_routes': False
                },
                'data_requirements': ['coordinates', 'markers'],
                'size_constraints': {'min_width': 4, 'min_height': 3}
            },
            'pie_chart': {
                'name': 'Pie Chart',
                'description': 'Category distribution visualization',
                'default_config': {
                    'chart_type': 'pie',
                    'show_legend': True,
                    'show_percentages': True,
                    'donut_style': False,
                    'animation': True
                },
                'data_requirements': ['categories', 'values'],
                'size_constraints': {'min_width': 2, 'min_height': 2}
            },
            'weather_widget': {
                'name': 'Weather Display',
                'description': 'Current weather and forecast',
                'default_config': {
                    'location': 'auto',
                    'show_forecast': True,
                    'forecast_days': 5,
                    'units': 'fahrenheit',
                    'show_hourly': False
                },
                'data_requirements': ['weather_data', 'location'],
                'size_constraints': {'min_width': 2, 'min_height': 2}
            },
            'calendar_widget': {
                'name': 'Calendar',
                'description': 'Events and scheduling display',
                'default_config': {
                    'view_type': 'month',
                    'show_weekends': True,
                    'event_colors': True,
                    'mini_calendar': False,
                    'time_format': '12_hour'
                },
                'data_requirements': ['events', 'dates'],
                'size_constraints': {'min_width': 4, 'min_height': 3}
            },
            'custom_html': {
                'name': 'Custom HTML',
                'description': 'Custom HTML content widget',
                'default_config': {
                    'html_content': '<div>Custom content here</div>',
                    'allow_scripts': False,
                    'auto_height': True,
                    'border': True,
                    'padding': '15px'
                },
                'data_requirements': ['html_content'],
                'size_constraints': {'min_width': 2, 'min_height': 1}
            }
        }
        
        return templates
    
    def _initialize_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available data sources"""
        
        sources = {
            'business_intelligence': {
                'name': 'Business Intelligence',
                'description': 'Executive metrics and KPIs',
                'endpoints': [
                    '/api/business/intelligence',
                    '/api/business/roi-analysis',
                    '/api/predictive/forecasts'
                ],
                'refresh_rates': [30, 60, 300, 900]
            },
            'system_performance': {
                'name': 'System Performance',
                'description': 'Application performance metrics',
                'endpoints': [
                    '/api/optimization/report',
                    '/api/watson/evolution',
                    '/api/deployment/diagnostics'
                ],
                'refresh_rates': [10, 30, 60, 300]
            },
            'user_analytics': {
                'name': 'User Analytics',
                'description': 'User behavior and engagement',
                'endpoints': [
                    '/api/users/analytics',
                    '/api/sessions/activity',
                    '/api/engagement/metrics'
                ],
                'refresh_rates': [60, 300, 900, 1800]
            },
            'fleet_tracking': {
                'name': 'Fleet Tracking',
                'description': 'Asset location and status',
                'endpoints': [
                    '/api/fleet/positions',
                    '/api/assets/status',
                    '/api/routes/optimization'
                ],
                'refresh_rates': [5, 15, 30, 60]
            },
            'financial_data': {
                'name': 'Financial Data',
                'description': 'Revenue and cost analysis',
                'endpoints': [
                    '/api/financial/metrics',
                    '/api/costs/analysis',
                    '/api/revenue/tracking'
                ],
                'refresh_rates': [300, 900, 3600, 86400]
            },
            'external_api': {
                'name': 'External API',
                'description': 'Third-party data integration',
                'endpoints': ['custom'],
                'refresh_rates': [60, 300, 900, 3600]
            }
        }
        
        return sources
    
    def _initialize_themes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize dashboard themes"""
        
        themes = {
            'executive_dark': {
                'name': 'Executive Dark',
                'description': 'Professional dark theme for executives',
                'colors': {
                    'primary': '#1a1a1a',
                    'secondary': '#2d2d2d',
                    'accent': '#ffd700',
                    'text': '#ffffff',
                    'text_secondary': '#cccccc',
                    'border': '#444444',
                    'success': '#00ff64',
                    'warning': '#ff6b35',
                    'error': '#ff3333'
                },
                'fonts': {
                    'primary': 'Inter, sans-serif',
                    'heading': 'Inter, sans-serif',
                    'monospace': 'Monaco, monospace'
                }
            },
            'business_light': {
                'name': 'Business Light',
                'description': 'Clean light theme for business use',
                'colors': {
                    'primary': '#ffffff',
                    'secondary': '#f8f9fa',
                    'accent': '#007bff',
                    'text': '#333333',
                    'text_secondary': '#666666',
                    'border': '#dee2e6',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'error': '#dc3545'
                },
                'fonts': {
                    'primary': 'Segoe UI, sans-serif',
                    'heading': 'Segoe UI, sans-serif',
                    'monospace': 'Consolas, monospace'
                }
            },
            'performance_blue': {
                'name': 'Performance Blue',
                'description': 'High-contrast blue theme for analytics',
                'colors': {
                    'primary': '#0a1929',
                    'secondary': '#1e293b',
                    'accent': '#00ffff',
                    'text': '#ffffff',
                    'text_secondary': '#94a3b8',
                    'border': '#334155',
                    'success': '#10b981',
                    'warning': '#f59e0b',
                    'error': '#ef4444'
                },
                'fonts': {
                    'primary': 'Roboto, sans-serif',
                    'heading': 'Roboto, sans-serif',
                    'monospace': 'Fira Code, monospace'
                }
            },
            'minimal_green': {
                'name': 'Minimal Green',
                'description': 'Minimalist green theme for focus',
                'colors': {
                    'primary': '#f7fafc',
                    'secondary': '#edf2f7',
                    'accent': '#48bb78',
                    'text': '#2d3748',
                    'text_secondary': '#4a5568',
                    'border': '#e2e8f0',
                    'success': '#38a169',
                    'warning': '#ed8936',
                    'error': '#e53e3e'
                },
                'fonts': {
                    'primary': 'Source Sans Pro, sans-serif',
                    'heading': 'Source Sans Pro, sans-serif',
                    'monospace': 'Source Code Pro, monospace'
                }
            }
        }
        
        return themes
    
    def create_custom_dashboard(self, user_id: str, name: str, description: str = "") -> DashboardLayout:
        """Create a new custom dashboard layout"""
        
        layout_id = f"custom_{user_id}_{int(time.time())}"
        
        # Default grid configuration
        grid_config = {
            'columns': 12,
            'row_height': 60,
            'margin': [10, 10],
            'container_padding': [20, 20],
            'breakpoints': {
                'lg': 1200,
                'md': 996,
                'sm': 768,
                'xs': 480
            }
        }
        
        layout = DashboardLayout(
            layout_id=layout_id,
            user_id=user_id,
            name=name,
            description=description,
            widgets=[],
            grid_config=grid_config,
            theme='executive_dark'
        )
        
        self.user_layouts[layout_id] = layout
        return layout
    
    def add_widget_to_dashboard(self, layout_id: str, widget_type: str, position: Dict[str, int], config: Optional[Dict[str, Any]] = None) -> DashboardWidget:
        """Add a widget to a dashboard layout"""
        
        if layout_id not in self.user_layouts:
            raise ValueError(f"Dashboard layout {layout_id} not found")
        
        if widget_type not in self.widget_templates:
            raise ValueError(f"Widget type {widget_type} not supported")
        
        template = self.widget_templates[widget_type]
        widget_id = f"widget_{widget_type}_{int(time.time())}"
        
        # Merge default config with user config
        widget_config = template['default_config'].copy()
        if config:
            widget_config.update(config)
        
        # Validate position constraints
        min_width = template['size_constraints']['min_width']
        min_height = template['size_constraints']['min_height']
        
        if position['width'] < min_width:
            position['width'] = min_width
        if position['height'] < min_height:
            position['height'] = min_height
        
        widget = DashboardWidget(
            widget_id=widget_id,
            widget_type=widget_type,
            title=template['name'],
            position=position,
            config=widget_config,
            data_source='business_intelligence',
            refresh_interval=60
        )
        
        self.user_layouts[layout_id].widgets.append(widget)
        self.user_layouts[layout_id].updated_at = datetime.now().isoformat()
        
        return widget
    
    def update_widget_config(self, layout_id: str, widget_id: str, config_updates: Dict[str, Any]) -> bool:
        """Update widget configuration"""
        
        if layout_id not in self.user_layouts:
            return False
        
        layout = self.user_layouts[layout_id]
        
        for widget in layout.widgets:
            if widget.widget_id == widget_id:
                widget.config.update(config_updates)
                layout.updated_at = datetime.now().isoformat()
                return True
        
        return False
    
    def move_widget(self, layout_id: str, widget_id: str, new_position: Dict[str, int]) -> bool:
        """Move widget to new position"""
        
        if layout_id not in self.user_layouts:
            return False
        
        layout = self.user_layouts[layout_id]
        
        for widget in layout.widgets:
            if widget.widget_id == widget_id:
                widget.position.update(new_position)
                layout.updated_at = datetime.now().isoformat()
                return True
        
        return False
    
    def remove_widget(self, layout_id: str, widget_id: str) -> bool:
        """Remove widget from dashboard"""
        
        if layout_id not in self.user_layouts:
            return False
        
        layout = self.user_layouts[layout_id]
        
        for i, widget in enumerate(layout.widgets):
            if widget.widget_id == widget_id:
                del layout.widgets[i]
                layout.updated_at = datetime.now().isoformat()
                return True
        
        return False
    
    def change_theme(self, layout_id: str, theme_name: str) -> bool:
        """Change dashboard theme"""
        
        if layout_id not in self.user_layouts:
            return False
        
        if theme_name not in self.themes:
            return False
        
        self.user_layouts[layout_id].theme = theme_name
        self.user_layouts[layout_id].updated_at = datetime.now().isoformat()
        
        return True
    
    def get_dashboard_layout(self, layout_id: str) -> Optional[DashboardLayout]:
        """Get dashboard layout by ID"""
        
        return self.user_layouts.get(layout_id)
    
    def get_user_dashboards(self, user_id: str) -> List[DashboardLayout]:
        """Get all dashboards for a user"""
        
        return [layout for layout in self.user_layouts.values() if layout.user_id == user_id]
    
    def export_dashboard_config(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """Export dashboard configuration as JSON"""
        
        layout = self.user_layouts.get(layout_id)
        if not layout:
            return None
        
        return {
            'layout': asdict(layout),
            'widget_templates': {widget.widget_type: self.widget_templates[widget.widget_type] for widget in layout.widgets},
            'theme': self.themes[layout.theme],
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_dashboard_config(self, user_id: str, config_data: Dict[str, Any]) -> Optional[str]:
        """Import dashboard configuration from JSON"""
        
        try:
            layout_data = config_data['layout']
            
            # Create new layout ID for import
            new_layout_id = f"imported_{user_id}_{int(time.time())}"
            layout_data['layout_id'] = new_layout_id
            layout_data['user_id'] = user_id
            layout_data['created_at'] = datetime.now().isoformat()
            layout_data['updated_at'] = datetime.now().isoformat()
            
            # Convert widgets
            widgets = []
            for widget_data in layout_data['widgets']:
                widget = DashboardWidget(**widget_data)
                widgets.append(widget)
            
            layout_data['widgets'] = widgets
            layout = DashboardLayout(**layout_data)
            
            self.user_layouts[new_layout_id] = layout
            return new_layout_id
            
        except Exception as e:
            print(f"Error importing dashboard config: {e}")
            return None
    
    def generate_widget_html(self, widget: DashboardWidget, theme: Dict[str, Any]) -> str:
        """Generate HTML for a dashboard widget"""
        
        base_style = f"""
        background: {theme['colors']['secondary']};
        border: 1px solid {theme['colors']['border']};
        border-radius: 8px;
        padding: 15px;
        color: {theme['colors']['text']};
        font-family: {theme['fonts']['primary']};
        """
        
        widget_html = f"""
        <div class="dashboard-widget" 
             data-widget-id="{widget.widget_id}"
             data-widget-type="{widget.widget_type}"
             style="{base_style} grid-column: span {widget.position['width']}; grid-row: span {widget.position['height']};">
            
            <div class="widget-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid {theme['colors']['border']}; padding-bottom: 10px;">
                <h3 style="margin: 0; color: {theme['colors']['text']}; font-size: 16px; font-weight: 600;">{widget.title}</h3>
                <div class="widget-controls">
                    <button class="widget-edit-btn" style="background: none; border: none; color: {theme['colors']['text_secondary']}; cursor: pointer; margin-left: 5px;">⚙️</button>
                    <button class="widget-remove-btn" style="background: none; border: none; color: {theme['colors']['text_secondary']}; cursor: pointer; margin-left: 5px;">✕</button>
                </div>
            </div>
            
            <div class="widget-content" id="content_{widget.widget_id}">
                {self._generate_widget_content(widget)}
            </div>
        </div>
        """
        
        return widget_html
    
    def _generate_widget_content(self, widget: DashboardWidget) -> str:
        """Generate content for specific widget types"""
        
        if widget.widget_type == 'metrics_card':
            return f"""
            <div class="metrics-card-content">
                <div class="metric-value" style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">$47.5K</div>
                <div class="metric-label" style="color: #ccc; margin-bottom: 10px;">Monthly Revenue</div>
                <div class="metric-trend" style="color: #00ff64;">↗ +15.3%</div>
            </div>
            """
        
        elif widget.widget_type == 'line_chart':
            return f"""
            <div class="chart-container">
                <canvas id="chart_{widget.widget_id}" width="100%" height="200"></canvas>
            </div>
            <script>
                // Chart.js implementation would go here
                console.log('Line chart for widget {widget.widget_id}');
            </script>
            """
        
        elif widget.widget_type == 'gauge_chart':
            return f"""
            <div class="gauge-container" style="text-align: center;">
                <div class="gauge-circle" style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
                    <svg viewBox="0 0 120 120" style="width: 100%; height: 100%;">
                        <circle cx="60" cy="60" r="50" fill="none" stroke="#333" stroke-width="8"/>
                        <circle cx="60" cy="60" r="50" fill="none" stroke="#00ff64" stroke-width="8"
                                stroke-dasharray="188 314" transform="rotate(-90 60 60)"/>
                    </svg>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 18px; font-weight: bold;">75%</div>
                </div>
                <div style="margin-top: 10px; color: #ccc;">Performance Score</div>
            </div>
            """
        
        elif widget.widget_type == 'data_table':
            return f"""
            <div class="data-table-container">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid #444;">
                            <th style="text-align: left; padding: 8px; color: #ccc;">Metric</th>
                            <th style="text-align: right; padding: 8px; color: #ccc;">Value</th>
                            <th style="text-align: right; padding: 8px; color: #ccc;">Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 8px;">Revenue</td>
                            <td style="padding: 8px; text-align: right;">$47.5K</td>
                            <td style="padding: 8px; text-align: right; color: #00ff64;">+15.3%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px;">Users</td>
                            <td style="padding: 8px; text-align: right;">1,247</td>
                            <td style="padding: 8px; text-align: right; color: #00ff64;">+8.7%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
        
        elif widget.widget_type == 'activity_feed':
            return f"""
            <div class="activity-feed">
                <div class="activity-item" style="padding: 8px 0; border-bottom: 1px solid #333;">
                    <div style="font-size: 14px;">New user registration</div>
                    <div style="font-size: 12px; color: #ccc;">2 minutes ago</div>
                </div>
                <div class="activity-item" style="padding: 8px 0; border-bottom: 1px solid #333;">
                    <div style="font-size: 14px;">System optimization completed</div>
                    <div style="font-size: 12px; color: #ccc;">5 minutes ago</div>
                </div>
                <div class="activity-item" style="padding: 8px 0;">
                    <div style="font-size: 14px;">Performance improvement detected</div>
                    <div style="font-size: 12px; color: #ccc;">10 minutes ago</div>
                </div>
            </div>
            """
        
        else:
            return f"""
            <div class="widget-placeholder" style="text-align: center; padding: 20px; color: #ccc;">
                <div>Widget: {widget.widget_type}</div>
                <div style="font-size: 12px; margin-top: 10px;">Configuration options available</div>
            </div>
            """
    
    def get_available_widgets(self) -> Dict[str, Any]:
        """Get all available widget types and templates"""
        
        return {
            'categories': {
                'Analytics': ['metrics_card', 'line_chart', 'pie_chart', 'gauge_chart'],
                'Data': ['data_table', 'activity_feed'],
                'Maps': ['map_widget'],
                'Utilities': ['weather_widget', 'calendar_widget', 'custom_html']
            },
            'templates': self.widget_templates,
            'data_sources': self.data_sources,
            'themes': self.themes
        }

def get_dashboard_customization_engine():
    """Get dashboard customization engine instance"""
    if not hasattr(get_dashboard_customization_engine, 'instance'):
        get_dashboard_customization_engine.instance = DashboardCustomizationEngine()
    return get_dashboard_customization_engine.instance