"""
Personalized Dashboard Customization Module
User-specific dashboard layouts with authentic Fort Worth data integration
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, session
import logging

dashboard_customization_bp = Blueprint('dashboard_customization', __name__)

class DashboardCustomizationEngine:
    """Personalized dashboard customization engine"""
    
    def __init__(self):
        self.db_path = 'dashboard_customization.db'
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize dashboard customization database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # User dashboard preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_dashboards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    dashboard_name TEXT NOT NULL,
                    layout_config TEXT NOT NULL,
                    widget_preferences TEXT NOT NULL,
                    data_filters TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_default BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Widget configurations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS widget_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    widget_type TEXT NOT NULL,
                    widget_name TEXT NOT NULL,
                    data_source TEXT NOT NULL,
                    default_settings TEXT NOT NULL,
                    available_filters TEXT,
                    fort_worth_data_integration BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # User widget instances table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_widgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    dashboard_id INTEGER NOT NULL,
                    widget_type TEXT NOT NULL,
                    position_x INTEGER NOT NULL,
                    position_y INTEGER NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    custom_settings TEXT,
                    is_visible BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (dashboard_id) REFERENCES user_dashboards (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Initialize default widgets
            self._initialize_default_widgets()
            
        except Exception as e:
            logging.error(f"Dashboard customization database initialization error: {e}")
    
    def _initialize_default_widgets(self):
        """Initialize default widget configurations with Fort Worth data"""
        
        default_widgets = [
            {
                'widget_type': 'fleet_overview',
                'widget_name': 'Fleet Overview',
                'data_source': '/api/fort-worth-assets',
                'default_settings': json.dumps({
                    'show_active_count': True,
                    'show_utilization': True,
                    'show_gps_coverage': True,
                    'refresh_interval': 30
                }),
                'available_filters': json.dumps([
                    'asset_type', 'location', 'status', 'driver_assigned'
                ])
            },
            {
                'widget_type': 'attendance_summary',
                'widget_name': 'Driver Attendance',
                'data_source': '/api/attendance-data',
                'default_settings': json.dumps({
                    'show_on_time_rate': True,
                    'show_late_count': True,
                    'show_absent_count': True,
                    'display_mode': 'compact'
                }),
                'available_filters': json.dumps([
                    'date_range', 'division', 'asset_type'
                ])
            },
            {
                'widget_type': 'revenue_metrics',
                'widget_name': 'Revenue Analytics',
                'data_source': '/api/revenue-data',
                'default_settings': json.dumps({
                    'show_ytd_revenue': True,
                    'show_monthly_trend': True,
                    'show_growth_rate': True,
                    'currency_format': 'USD'
                }),
                'available_filters': json.dumps([
                    'time_period', 'revenue_type', 'client_category'
                ])
            },
            {
                'widget_type': 'predictive_alerts',
                'widget_name': 'Maintenance Alerts',
                'data_source': '/api/predictive-analysis',
                'default_settings': json.dumps({
                    'show_critical_only': False,
                    'alert_threshold': 0.25,
                    'auto_refresh': True,
                    'sound_alerts': False
                }),
                'available_filters': json.dumps([
                    'risk_level', 'asset_category', 'maintenance_type'
                ])
            },
            {
                'widget_type': 'cost_optimization',
                'widget_name': 'Cost Savings',
                'data_source': '/api/lifecycle-analysis',
                'default_settings': json.dumps({
                    'show_potential_savings': True,
                    'show_roi_metrics': True,
                    'highlight_opportunities': True
                }),
                'available_filters': json.dumps([
                    'optimization_category', 'time_horizon', 'investment_level'
                ])
            },
            {
                'widget_type': 'market_intelligence',
                'widget_name': 'Texas Market Intel',
                'data_source': '/api/market-research',
                'default_settings': json.dumps({
                    'show_market_share': True,
                    'show_competitor_analysis': True,
                    'show_growth_trends': True,
                    'focus_region': 'fort_worth'
                }),
                'available_filters': json.dumps([
                    'market_segment', 'competitor_focus', 'time_range'
                ])
            },
            {
                'widget_type': 'quantum_consciousness',
                'widget_name': 'QQ Intelligence',
                'data_source': '/api/quantum-consciousness',
                'default_settings': json.dumps({
                    'show_thought_vectors': True,
                    'show_consciousness_level': True,
                    'animation_enabled': True,
                    'processing_indicators': True
                }),
                'available_filters': json.dumps([
                    'consciousness_mode', 'vector_visualization', 'update_frequency'
                ])
            }
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for widget in default_widgets:
                cursor.execute('''
                    INSERT OR IGNORE INTO widget_configs 
                    (widget_type, widget_name, data_source, default_settings, available_filters)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    widget['widget_type'],
                    widget['widget_name'],
                    widget['data_source'],
                    widget['default_settings'],
                    widget['available_filters']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Error initializing default widgets: {e}")
    
    def create_custom_dashboard(self, user_id, dashboard_name, layout_config, widget_preferences):
        """Create a custom dashboard for user"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_dashboards 
                (user_id, dashboard_name, layout_config, widget_preferences, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                dashboard_name,
                json.dumps(layout_config),
                json.dumps(widget_preferences),
                datetime.now().isoformat()
            ))
            
            dashboard_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'dashboard_id': dashboard_id,
                'message': f'Custom dashboard "{dashboard_name}" created successfully'
            }
            
        except Exception as e:
            logging.error(f"Error creating custom dashboard: {e}")
            return {
                'success': False,
                'error': 'Failed to create custom dashboard'
            }
    
    def get_user_dashboards(self, user_id):
        """Get all dashboards for a user"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, dashboard_name, layout_config, widget_preferences, 
                       created_at, updated_at, is_default
                FROM user_dashboards 
                WHERE user_id = ?
                ORDER BY is_default DESC, updated_at DESC
            ''', (user_id,))
            
            dashboards = []
            for row in cursor.fetchall():
                dashboards.append({
                    'id': row[0],
                    'name': row[1],
                    'layout_config': json.loads(row[2]),
                    'widget_preferences': json.loads(row[3]),
                    'created_at': row[4],
                    'updated_at': row[5],
                    'is_default': bool(row[6])
                })
            
            conn.close()
            return dashboards
            
        except Exception as e:
            logging.error(f"Error getting user dashboards: {e}")
            return []
    
    def update_dashboard_layout(self, dashboard_id, user_id, layout_config, widget_positions):
        """Update dashboard layout and widget positions"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update dashboard layout
            cursor.execute('''
                UPDATE user_dashboards 
                SET layout_config = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            ''', (
                json.dumps(layout_config),
                datetime.now().isoformat(),
                dashboard_id,
                user_id
            ))
            
            # Update widget positions
            for widget in widget_positions:
                cursor.execute('''
                    UPDATE user_widgets
                    SET position_x = ?, position_y = ?, width = ?, height = ?
                    WHERE dashboard_id = ? AND widget_type = ?
                ''', (
                    widget['x'],
                    widget['y'],
                    widget['width'],
                    widget['height'],
                    dashboard_id,
                    widget['type']
                ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Dashboard layout updated successfully'
            }
            
        except Exception as e:
            logging.error(f"Error updating dashboard layout: {e}")
            return {
                'success': False,
                'error': 'Failed to update dashboard layout'
            }
    
    def get_available_widgets(self):
        """Get all available widgets for customization"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT widget_type, widget_name, data_source, 
                       default_settings, available_filters
                FROM widget_configs
            ''')
            
            widgets = []
            for row in cursor.fetchall():
                widgets.append({
                    'type': row[0],
                    'name': row[1],
                    'data_source': row[2],
                    'default_settings': json.loads(row[3]),
                    'available_filters': json.loads(row[4])
                })
            
            conn.close()
            return widgets
            
        except Exception as e:
            logging.error(f"Error getting available widgets: {e}")
            return []
    
    def save_widget_preferences(self, user_id, dashboard_id, widget_type, preferences):
        """Save user preferences for a specific widget"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_widgets
                (user_id, dashboard_id, widget_type, position_x, position_y, 
                 width, height, custom_settings, is_visible)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                dashboard_id,
                widget_type,
                preferences.get('x', 0),
                preferences.get('y', 0),
                preferences.get('width', 4),
                preferences.get('height', 3),
                json.dumps(preferences.get('settings', {})),
                preferences.get('visible', True)
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Widget preferences saved successfully'
            }
            
        except Exception as e:
            logging.error(f"Error saving widget preferences: {e}")
            return {
                'success': False,
                'error': 'Failed to save widget preferences'
            }

# Initialize customization engine
customization_engine = DashboardCustomizationEngine()

@dashboard_customization_bp.route('/api/dashboard/create', methods=['POST'])
def create_dashboard():
    """Create a new custom dashboard"""
    try:
        data = request.json
        user_id = session.get('user', 'demo_user')
        
        result = customization_engine.create_custom_dashboard(
            user_id=user_id,
            dashboard_name=data.get('name'),
            layout_config=data.get('layout', {}),
            widget_preferences=data.get('widgets', [])
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Dashboard creation error: {e}")
        return jsonify({'success': False, 'error': 'Failed to create dashboard'}), 500

@dashboard_customization_bp.route('/api/dashboard/list')
def list_dashboards():
    """Get user's dashboards"""
    try:
        user_id = session.get('user', 'demo_user')
        dashboards = customization_engine.get_user_dashboards(user_id)
        
        return jsonify({
            'dashboards': dashboards,
            'total_count': len(dashboards)
        })
        
    except Exception as e:
        logging.error(f"Dashboard listing error: {e}")
        return jsonify({'error': 'Failed to load dashboards'}), 500

@dashboard_customization_bp.route('/api/dashboard/widgets')
def available_widgets():
    """Get available widgets for customization"""
    try:
        widgets = customization_engine.get_available_widgets()
        
        return jsonify({
            'widgets': widgets,
            'categories': [
                'fleet_management',
                'financial_analytics', 
                'maintenance_intelligence',
                'market_research',
                'quantum_processing'
            ]
        })
        
    except Exception as e:
        logging.error(f"Widget listing error: {e}")
        return jsonify({'error': 'Failed to load widgets'}), 500

@dashboard_customization_bp.route('/api/dashboard/<int:dashboard_id>/layout', methods=['PUT'])
def update_layout(dashboard_id):
    """Update dashboard layout"""
    try:
        data = request.json
        user_id = session.get('user', 'demo_user')
        
        result = customization_engine.update_dashboard_layout(
            dashboard_id=dashboard_id,
            user_id=user_id,
            layout_config=data.get('layout', {}),
            widget_positions=data.get('widgets', [])
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Layout update error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update layout'}), 500

@dashboard_customization_bp.route('/api/dashboard/widget/preferences', methods=['POST'])
def save_widget_preferences():
    """Save widget preferences"""
    try:
        data = request.json
        user_id = session.get('user', 'demo_user')
        
        result = customization_engine.save_widget_preferences(
            user_id=user_id,
            dashboard_id=data.get('dashboard_id'),
            widget_type=data.get('widget_type'),
            preferences=data.get('preferences', {})
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Widget preferences error: {e}")
        return jsonify({'success': False, 'error': 'Failed to save preferences'}), 500

def get_dashboard_customization_engine():
    """Get dashboard customization engine instance"""
    return customization_engine