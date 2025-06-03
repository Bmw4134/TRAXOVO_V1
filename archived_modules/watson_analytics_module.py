"""
Watson Analytics Module - User Behavior Intelligence & System Optimization
Captures comprehensive user interactions and provides strategic intelligence
"""

import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, session, jsonify, render_template
from collections import defaultdict, deque
import sqlite3
import threading

class WatsonAnalyticsEngine:
    """Advanced analytics engine for user behavior and system optimization"""
    
    def __init__(self):
        self.interaction_log = deque(maxlen=10000)
        self.user_sessions = defaultdict(dict)
        self.performance_metrics = defaultdict(list)
        self.db_lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent analytics storage"""
        with sqlite3.connect('watson_analytics.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    action TEXT,
                    page TEXT,
                    data TEXT,
                    performance_ms INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS system_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    context TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS excellence_activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    user_id TEXT,
                    activation_type TEXT,
                    results TEXT,
                    export_generated BOOLEAN
                )
            ''')
    
    def log_interaction(self, user_id, action, page, data=None, performance_ms=None):
        """Log user interaction with comprehensive context"""
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id or 'anonymous',
            'session_id': session.get('session_id', 'unknown'),
            'action': action,
            'page': page,
            'data': json.dumps(data) if data else None,
            'performance_ms': performance_ms,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        self.interaction_log.append(interaction)
        
        # Store in database for persistence
        with self.db_lock:
            with sqlite3.connect('watson_analytics.db') as conn:
                conn.execute('''
                    INSERT INTO user_interactions 
                    (timestamp, user_id, session_id, action, page, data, performance_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction['timestamp'],
                    interaction['user_id'],
                    interaction['session_id'],
                    interaction['action'],
                    interaction['page'],
                    interaction['data'],
                    interaction['performance_ms']
                ))
    
    def log_excellence_activation(self, user_id, activation_type, results, export_generated=False):
        """Log Excellence Mode activations with results"""
        with self.db_lock:
            with sqlite3.connect('watson_analytics.db') as conn:
                conn.execute('''
                    INSERT INTO excellence_activations 
                    (timestamp, user_id, activation_type, results, export_generated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    user_id or 'anonymous',
                    activation_type,
                    json.dumps(results),
                    export_generated
                ))
    
    def get_user_analytics(self, user_id):
        """Get comprehensive analytics for specific user"""
        with sqlite3.connect('watson_analytics.db') as conn:
            cursor = conn.cursor()
            
            # Get user interactions
            cursor.execute('''
                SELECT action, page, COUNT(*) as count, 
                       AVG(performance_ms) as avg_performance
                FROM user_interactions 
                WHERE user_id = ? AND timestamp > datetime('now', '-7 days')
                GROUP BY action, page
                ORDER BY count DESC
            ''', (user_id,))
            interactions = cursor.fetchall()
            
            # Get excellence activations
            cursor.execute('''
                SELECT activation_type, COUNT(*) as count,
                       AVG(json_extract(results, '$.asi_level')) as avg_asi_level
                FROM excellence_activations
                WHERE user_id = ? AND timestamp > datetime('now', '-7 days')
                GROUP BY activation_type
            ''', (user_id,))
            excellence_stats = cursor.fetchall()
            
            return {
                'interactions': interactions,
                'excellence_stats': excellence_stats,
                'total_sessions': len(set([i['session_id'] for i in self.interaction_log if i['user_id'] == user_id]))
            }
    
    def get_system_insights(self):
        """Generate comprehensive system insights"""
        with sqlite3.connect('watson_analytics.db') as conn:
            cursor = conn.cursor()
            
            # Most popular pages
            cursor.execute('''
                SELECT page, COUNT(*) as visits
                FROM user_interactions
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY page
                ORDER BY visits DESC
                LIMIT 10
            ''')
            popular_pages = cursor.fetchall()
            
            # Performance metrics
            cursor.execute('''
                SELECT page, AVG(performance_ms) as avg_ms
                FROM user_interactions
                WHERE performance_ms IS NOT NULL 
                AND timestamp > datetime('now', '-24 hours')
                GROUP BY page
                ORDER BY avg_ms DESC
            ''')
            performance_data = cursor.fetchall()
            
            # Excellence mode usage
            cursor.execute('''
                SELECT COUNT(*) as activations,
                       AVG(json_extract(results, '$.asi_level')) as avg_performance
                FROM excellence_activations
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            excellence_usage = cursor.fetchone()
            
            return {
                'popular_pages': popular_pages,
                'performance_data': performance_data,
                'excellence_usage': excellence_usage,
                'total_interactions_24h': len([i for i in self.interaction_log 
                                             if datetime.fromisoformat(i['timestamp']) > datetime.now() - timedelta(hours=24)])
            }
    
    def get_watson_specific_insights(self):
        """Generate insights specifically for Watson user"""
        watson_analytics = self.get_user_analytics('watson')
        
        # Calculate Watson's efficiency metrics
        recent_interactions = [i for i in self.interaction_log 
                             if i['user_id'] == 'watson' and 
                             datetime.fromisoformat(i['timestamp']) > datetime.now() - timedelta(hours=24)]
        
        efficiency_score = len(recent_interactions) * 0.1  # Base efficiency
        
        # Bonus for excellence mode usage
        excellence_count = len([i for i in recent_interactions if 'excellence' in i['action'].lower()])
        efficiency_score += excellence_count * 2.5
        
        # Bonus for dashboard usage
        dashboard_time = len([i for i in recent_interactions if 'dashboard' in i['page'].lower()])
        efficiency_score += dashboard_time * 1.2
        
        return {
            'efficiency_score': min(100, efficiency_score),
            'recent_interactions': len(recent_interactions),
            'excellence_activations': excellence_count,
            'dashboard_utilization': dashboard_time,
            'watson_analytics': watson_analytics
        }

# Global analytics engine instance
watson_analytics = WatsonAnalyticsEngine()

# Blueprint for Watson analytics routes
watson_blueprint = Blueprint('watson_analytics', __name__)

@watson_blueprint.route('/watson_dashboard')
def watson_dashboard():
    """Watson's personalized analytics dashboard"""
    insights = watson_analytics.get_watson_specific_insights()
    system_insights = watson_analytics.get_system_insights()
    
    return render_template('watson_dashboard.html', 
                         insights=insights, 
                         system_insights=system_insights)

@watson_blueprint.route('/api/watson_analytics')
def api_watson_analytics():
    """API endpoint for Watson analytics data"""
    return jsonify(watson_analytics.get_watson_specific_insights())

@watson_blueprint.route('/api/log_interaction', methods=['POST'])
def log_interaction():
    """Log user interaction via API"""
    data = request.get_json()
    
    watson_analytics.log_interaction(
        user_id=data.get('user_id'),
        action=data.get('action'),
        page=data.get('page'),
        data=data.get('data'),
        performance_ms=data.get('performance_ms')
    )
    
    return jsonify({'status': 'logged'})

@watson_blueprint.route('/api/excellence_analytics')
def excellence_analytics():
    """Get excellence mode analytics"""
    with sqlite3.connect('watson_analytics.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total_activations,
                   AVG(json_extract(results, '$.asi_level')) as avg_asi_level,
                   AVG(json_extract(results, '$.performance_boost')) as avg_boost,
                   COUNT(CASE WHEN export_generated = 1 THEN 1 END) as exports_generated
            FROM excellence_activations
            WHERE timestamp > datetime('now', '-30 days')
        ''')
        
        stats = cursor.fetchone()
        
        return jsonify({
            'total_activations': stats[0] or 0,
            'avg_asi_level': stats[1] or 0,
            'avg_performance_boost': stats[2] or 0,
            'exports_generated': stats[3] or 0
        })

def integrate_watson_analytics(app):
    """Integrate Watson analytics into the main application"""
    
    # Register the blueprint
    app.register_blueprint(watson_blueprint, url_prefix='/watson')
    
    # Add middleware to automatically log page visits
    @app.before_request
    def log_page_visit():
        if request.endpoint and not request.endpoint.startswith('static'):
            user_id = session.get('user_id', 'anonymous')
            watson_analytics.log_interaction(
                user_id=user_id,
                action='page_visit',
                page=request.endpoint or request.path,
                data={'method': request.method}
            )
    
    # Add Watson-specific routes to main app
    @app.route('/watson_insights')
    def watson_insights():
        """Quick Watson insights page"""
        insights = watson_analytics.get_watson_specific_insights()
        return jsonify(insights)
    
    return watson_analytics

# Export the analytics engine for use in other modules
__all__ = ['watson_analytics', 'integrate_watson_analytics', 'WatsonAnalyticsEngine']