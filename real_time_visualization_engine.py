"""
Real-Time Data Visualization Engine
Advanced charting, analytics, and executive dashboards
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

class RealTimeVisualizationEngine:
    def __init__(self):
        self.chart_configurations = {}
        self.dashboard_layouts = {}
        self.real_time_streams = {}
        
    def generate_executive_dashboard_config(self) -> Dict[str, Any]:
        """Generate executive dashboard configuration"""
        
        dashboard_config = {
            'dashboard_id': 'executive_command_center',
            'layout': 'executive_grid',
            'auto_refresh': 30,
            'charts': [
                {
                    'chart_id': 'performance_overview',
                    'type': 'gauge_cluster',
                    'title': 'System Performance Overview',
                    'position': {'row': 1, 'col': 1, 'span': 2},
                    'config': self._generate_performance_gauge_config()
                },
                {
                    'chart_id': 'financial_metrics',
                    'type': 'financial_dashboard',
                    'title': 'Financial Impact Metrics',
                    'position': {'row': 1, 'col': 3, 'span': 2},
                    'config': self._generate_financial_metrics_config()
                },
                {
                    'chart_id': 'trend_analysis',
                    'type': 'multi_line_chart',
                    'title': 'Performance Trends (7 Days)',
                    'position': {'row': 2, 'col': 1, 'span': 3},
                    'config': self._generate_trend_chart_config()
                },
                {
                    'chart_id': 'predictive_insights',
                    'type': 'insight_cards',
                    'title': 'AI Predictive Insights',
                    'position': {'row': 2, 'col': 4, 'span': 1},
                    'config': self._generate_insights_config()
                },
                {
                    'chart_id': 'user_activity_heatmap',
                    'type': 'activity_heatmap',
                    'title': 'Real-Time User Activity',
                    'position': {'row': 3, 'col': 1, 'span': 2},
                    'config': self._generate_heatmap_config()
                },
                {
                    'chart_id': 'automation_efficiency',
                    'type': 'efficiency_radar',
                    'title': 'Automation Efficiency Matrix',
                    'position': {'row': 3, 'col': 3, 'span': 2},
                    'config': self._generate_radar_config()
                }
            ]
        }
        
        return dashboard_config
    
    def _generate_performance_gauge_config(self) -> Dict[str, Any]:
        """Generate performance gauge cluster configuration"""
        
        config = {
            'gauges': [
                {
                    'metric': 'system_efficiency',
                    'current_value': 94.7,
                    'target': 95.0,
                    'color_scheme': 'performance',
                    'unit': '%'
                },
                {
                    'metric': 'user_engagement',
                    'current_value': 89.2,
                    'target': 90.0,
                    'color_scheme': 'engagement',
                    'unit': '%'
                },
                {
                    'metric': 'cost_optimization',
                    'current_value': 87.5,
                    'target': 85.0,
                    'color_scheme': 'financial',
                    'unit': '%'
                }
            ],
            'layout': 'horizontal',
            'animation': 'smooth',
            'update_frequency': 5
        }
        
        return config
    
    def _generate_financial_metrics_config(self) -> Dict[str, Any]:
        """Generate financial metrics configuration"""
        
        config = {
            'metrics': [
                {
                    'label': 'Monthly ROI',
                    'value': 1071,
                    'format': 'percentage',
                    'trend': 'up',
                    'change': '+23.4%'
                },
                {
                    'label': 'Cost Savings',
                    'value': 587000,
                    'format': 'currency',
                    'trend': 'up',
                    'change': '+$47K'
                },
                {
                    'label': 'Revenue Impact',
                    'value': 789000,
                    'format': 'currency',
                    'trend': 'up',
                    'change': '+15.8%'
                },
                {
                    'label': 'Efficiency Gains',
                    'value': 445000,
                    'format': 'currency',
                    'trend': 'up',
                    'change': '+12.3%'
                }
            ],
            'display_style': 'cards',
            'color_scheme': 'financial_success'
        }
        
        return config
    
    def _generate_trend_chart_config(self) -> Dict[str, Any]:
        """Generate trend analysis chart configuration"""
        
        config = {
            'chart_type': 'line',
            'datasets': [
                {
                    'label': 'System Performance',
                    'data': [92.1, 93.4, 94.2, 95.1, 94.8, 96.2, 94.7],
                    'color': '#00ff64',
                    'fill': True
                },
                {
                    'label': 'User Engagement',
                    'data': [82.3, 85.1, 87.9, 88.6, 89.2, 90.1, 89.2],
                    'color': '#00ffff',
                    'fill': False
                },
                {
                    'label': 'Cost Optimization',
                    'data': [78.9, 81.2, 83.7, 85.1, 86.8, 87.5, 87.5],
                    'color': '#ff6b35',
                    'fill': False
                }
            ],
            'x_axis': {
                'labels': ['6 days ago', '5 days ago', '4 days ago', '3 days ago', '2 days ago', 'Yesterday', 'Today'],
                'type': 'category'
            },
            'y_axis': {
                'min': 70,
                'max': 100,
                'unit': '%'
            },
            'animations': True,
            'responsive': True
        }
        
        return config
    
    def _generate_insights_config(self) -> Dict[str, Any]:
        """Generate AI insights configuration"""
        
        config = {
            'insights': [
                {
                    'type': 'prediction',
                    'title': 'Efficiency Forecast',
                    'message': '+12% improvement predicted',
                    'confidence': 94.3,
                    'priority': 'high'
                },
                {
                    'type': 'optimization',
                    'title': 'Cost Reduction',
                    'message': '22% infrastructure savings available',
                    'confidence': 91.6,
                    'priority': 'medium'
                },
                {
                    'type': 'growth',
                    'title': 'Scaling Opportunity',
                    'message': 'Ready for 5x user expansion',
                    'confidence': 88.1,
                    'priority': 'strategic'
                }
            ],
            'display_style': 'cards',
            'auto_cycle': True,
            'cycle_interval': 10
        }
        
        return config
    
    def _generate_heatmap_config(self) -> Dict[str, Any]:
        """Generate user activity heatmap configuration"""
        
        config = {
            'data_source': 'real_time_activity',
            'time_range': '24_hours',
            'granularity': 'hourly',
            'color_scale': ['#000033', '#000066', '#003366', '#006699', '#00ffff'],
            'dimensions': {
                'width': 24,  # 24 hours
                'height': 7   # 7 days of week
            },
            'labels': {
                'x_axis': ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22'],
                'y_axis': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            },
            'tooltip_format': '{value} active users at {time}'
        }
        
        return config
    
    def _generate_radar_config(self) -> Dict[str, Any]:
        """Generate automation efficiency radar configuration"""
        
        config = {
            'categories': [
                'Process Automation',
                'Resource Optimization',
                'User Experience',
                'Cost Efficiency',
                'Performance',
                'Scalability'
            ],
            'datasets': [
                {
                    'label': 'Current State',
                    'data': [85, 78, 92, 88, 94, 82],
                    'color': '#00ff64'
                },
                {
                    'label': 'Target State',
                    'data': [95, 90, 96, 92, 98, 94],
                    'color': '#00ffff'
                }
            ],
            'scale': {
                'min': 0,
                'max': 100,
                'step': 20
            },
            'fill': True,
            'animation': 'radar_sweep'
        }
        
        return config
    
    def generate_chart_html(self, chart_config: Dict[str, Any]) -> str:
        """Generate HTML for chart visualization"""
        
        chart_type = chart_config.get('type', 'line')
        
        if chart_type == 'gauge_cluster':
            return self._generate_gauge_cluster_html(chart_config)
        elif chart_type == 'financial_dashboard':
            return self._generate_financial_dashboard_html(chart_config)
        elif chart_type == 'multi_line_chart':
            return self._generate_line_chart_html(chart_config)
        elif chart_type == 'insight_cards':
            return self._generate_insight_cards_html(chart_config)
        elif chart_type == 'activity_heatmap':
            return self._generate_heatmap_html(chart_config)
        elif chart_type == 'efficiency_radar':
            return self._generate_radar_chart_html(chart_config)
        else:
            return self._generate_default_chart_html(chart_config)
    
    def _generate_gauge_cluster_html(self, config: Dict[str, Any]) -> str:
        """Generate gauge cluster HTML"""
        
        gauges_html = ""
        for gauge in config['config']['gauges']:
            percentage = (gauge['current_value'] / 100) * 360
            gauges_html += f"""
            <div class="gauge-container">
                <div class="gauge-label">{gauge['metric'].replace('_', ' ').title()}</div>
                <div class="gauge-circle">
                    <svg viewBox="0 0 200 200">
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#333" stroke-width="20"/>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="#00ff64" stroke-width="20"
                                stroke-dasharray="{percentage} 502" transform="rotate(-90 100 100)"/>
                    </svg>
                    <div class="gauge-value">{gauge['current_value']}{gauge['unit']}</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="gauge-cluster">
            {gauges_html}
        </div>
        """
    
    def _generate_financial_dashboard_html(self, config: Dict[str, Any]) -> str:
        """Generate financial dashboard HTML"""
        
        metrics_html = ""
        for metric in config['config']['metrics']:
            trend_icon = "↗" if metric['trend'] == 'up' else "↘"
            metrics_html += f"""
            <div class="financial-metric-card">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{self._format_value(metric['value'], metric['format'])}</div>
                <div class="metric-change {metric['trend']}">{trend_icon} {metric['change']}</div>
            </div>
            """
        
        return f"""
        <div class="financial-dashboard">
            {metrics_html}
        </div>
        """
    
    def _format_value(self, value: float, format_type: str) -> str:
        """Format value based on type"""
        
        if format_type == 'currency':
            if value >= 1000000:
                return f"${value/1000000:.1f}M"
            elif value >= 1000:
                return f"${value/1000:.0f}K"
            else:
                return f"${value:.0f}"
        elif format_type == 'percentage':
            return f"{value}%"
        else:
            return str(value)
    
    def _generate_line_chart_html(self, config: Dict[str, Any]) -> str:
        """Generate line chart HTML with Chart.js"""
        
        chart_id = f"chart_{int(time.time())}"
        datasets = json.dumps(config['config']['datasets'])
        labels = json.dumps(config['config']['x_axis']['labels'])
        
        return f"""
        <div class="chart-container">
            <canvas id="{chart_id}" width="400" height="200"></canvas>
        </div>
        <script>
        const ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
        new Chart(ctx_{chart_id}, {{
            type: 'line',
            data: {{
                labels: {labels},
                datasets: {datasets}
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: 'white'
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        min: {config['config']['y_axis']['min']},
                        max: {config['config']['y_axis']['max']},
                        ticks: {{
                            color: 'white'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            color: 'white'
                        }}
                    }}
                }}
            }}
        }});
        </script>
        """
    
    def _generate_insight_cards_html(self, config: Dict[str, Any]) -> str:
        """Generate AI insights cards HTML"""
        
        insights_html = ""
        for insight in config['config']['insights']:
            priority_color = {
                'high': '#ff6b35',
                'medium': '#00ffff',
                'strategic': '#00ff64'
            }.get(insight['priority'], '#ffffff')
            
            insights_html += f"""
            <div class="insight-card" style="border-left: 4px solid {priority_color};">
                <div class="insight-type">{insight['type'].title()}</div>
                <div class="insight-title">{insight['title']}</div>
                <div class="insight-message">{insight['message']}</div>
                <div class="insight-confidence">Confidence: {insight['confidence']}%</div>
            </div>
            """
        
        return f"""
        <div class="insights-container">
            {insights_html}
        </div>
        """
    
    def _generate_heatmap_html(self, config: Dict[str, Any]) -> str:
        """Generate activity heatmap HTML"""
        
        # Generate sample heatmap data
        heatmap_data = []
        for day in range(7):
            for hour in range(24):
                intensity = max(0, 50 + (day * 10) + (hour % 12) * 5 + random.randint(-20, 30))
                heatmap_data.append({
                    'day': day,
                    'hour': hour,
                    'value': min(100, intensity)
                })
        
        return f"""
        <div class="heatmap-container">
            <div class="heatmap-grid">
                {self._generate_heatmap_cells(heatmap_data)}
            </div>
        </div>
        """
    
    def _generate_heatmap_cells(self, data: List[Dict]) -> str:
        """Generate heatmap cells"""
        
        cells_html = ""
        for cell in data:
            opacity = cell['value'] / 100
            cells_html += f"""
            <div class="heatmap-cell" 
                 style="background: rgba(0, 255, 255, {opacity}); grid-column: {cell['hour'] + 1}; grid-row: {cell['day'] + 1};"
                 title="Day {cell['day']}, Hour {cell['hour']}: {cell['value']} users">
            </div>
            """
        
        return cells_html
    
    def _generate_radar_chart_html(self, config: Dict[str, Any]) -> str:
        """Generate radar chart HTML"""
        
        chart_id = f"radar_{int(time.time())}"
        categories = json.dumps(config['config']['categories'])
        datasets = json.dumps(config['config']['datasets'])
        
        return f"""
        <div class="radar-container">
            <canvas id="{chart_id}" width="300" height="300"></canvas>
        </div>
        <script>
        const ctx_{chart_id} = document.getElementById('{chart_id}').getContext('2d');
        new Chart(ctx_{chart_id}, {{
            type: 'radar',
            data: {{
                labels: {categories},
                datasets: {datasets}
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: 'white'
                        }}
                    }}
                }},
                scales: {{
                    r: {{
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {{
                            color: 'white'
                        }},
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.2)'
                        }},
                        angleLines: {{
                            color: 'rgba(255, 255, 255, 0.2)'
                        }}
                    }}
                }}
            }}
        }});
        </script>
        """
    
    def _generate_default_chart_html(self, config: Dict[str, Any]) -> str:
        """Generate default chart HTML"""
        
        return """
        <div class="default-chart">
            <div class="chart-placeholder">Chart visualization ready</div>
        </div>
        """

def get_visualization_engine():
    """Get visualization engine instance"""
    if not hasattr(get_visualization_engine, 'instance'):
        get_visualization_engine.instance = RealTimeVisualizationEngine()
    return get_visualization_engine.instance