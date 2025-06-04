"""
QQ Quantum API Drift & Optimization Model
Self-auditing intelligent backend process for API call analysis and optimization
Analyzes all API pull behaviors across TRAXOVO suite for efficiency and drift detection
"""

import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QQApiCallSignature:
    """API call signature for drift detection"""
    
    def __init__(self, method: str, url: str, payload: Dict, headers: Dict = None):
        self.method = method
        self.url = url
        self.payload = payload
        self.headers = headers or {}
        self.signature = self._generate_signature()
        self.timestamp = time.time()
    
    def _generate_signature(self) -> str:
        """Generate unique signature for API call"""
        signature_data = {
            'method': self.method,
            'url': self.url,
            'payload': self.payload,
            'relevant_headers': {k: v for k, v in self.headers.items() 
                               if k.lower() in ['content-type', 'authorization']}
        }
        signature_string = json.dumps(signature_data, sort_keys=True)
        return sha256(signature_string.encode()).hexdigest()

class QQApiDriftOptimizer:
    """
    QQ Quantum API Drift & Optimization Model
    Self-auditing system for API call analysis and optimization
    """
    
    def __init__(self, db_path: str = "qq_api_drift_analysis.db"):
        self.db_path = db_path
        self.api_call_log = []
        self.endpoint_registry = defaultdict(list)
        self.duplicate_signatures = defaultdict(list)
        self.drift_alerts = []
        self.optimization_suggestions = []
        self._initialize_database()
        self._start_background_analysis()
    
    def _initialize_database(self):
        """Initialize SQLite database for API call tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signature TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                payload TEXT,
                headers TEXT,
                response_status INTEGER,
                response_time REAL,
                response_size INTEGER,
                timestamp REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Drift analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drift_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                drift_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                suggestions TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Optimization recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                optimization_type TEXT NOT NULL,
                current_calls_per_hour INTEGER,
                recommended_calls_per_hour INTEGER,
                potential_savings_percent REAL,
                implementation_priority TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_api_call(self, method: str, url: str, payload: Dict = None, 
                     headers: Dict = None, response_status: int = None,
                     response_time: float = None, response_size: int = None):
        """Log API call for drift analysis"""
        
        # Create signature
        signature_obj = QQApiCallSignature(method, url, payload or {}, headers or {})
        
        # Store in memory for real-time analysis
        call_entry = {
            'signature': signature_obj.signature,
            'method': method,
            'url': url,
            'payload': payload,
            'headers': headers,
            'response_status': response_status,
            'response_time': response_time,
            'response_size': response_size,
            'timestamp': signature_obj.timestamp
        }
        
        self.api_call_log.append(call_entry)
        self.endpoint_registry[url].append(call_entry)
        
        # Track duplicates
        self.duplicate_signatures[signature_obj.signature].append(call_entry)
        
        # Store in database
        self._store_call_in_database(call_entry)
        
        # Trigger real-time analysis
        self._analyze_call_patterns()
        
        logger.info(f"QQ API Call Logged: {method} {url} - Signature: {signature_obj.signature[:8]}...")
    
    def _store_call_in_database(self, call_entry: Dict):
        """Store API call in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_calls 
            (signature, method, url, payload, headers, response_status, 
             response_time, response_size, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_entry['signature'],
            call_entry['method'],
            call_entry['url'],
            json.dumps(call_entry['payload']) if call_entry['payload'] else None,
            json.dumps(call_entry['headers']) if call_entry['headers'] else None,
            call_entry['response_status'],
            call_entry['response_time'],
            call_entry['response_size'],
            call_entry['timestamp']
        ))
        
        conn.commit()
        conn.close()
    
    def _analyze_call_patterns(self):
        """Analyze API call patterns for optimization opportunities"""
        
        # Find duplicate calls
        duplicates = self.find_duplicate_calls()
        
        # Analyze frequency patterns
        frequency_analysis = self.analyze_call_frequency()
        
        # Detect payload drift
        drift_analysis = self.detect_payload_drift()
        
        # Generate optimization suggestions
        self._generate_optimization_suggestions(duplicates, frequency_analysis)
    
    def find_duplicate_calls(self) -> Dict[str, List[Dict]]:
        """Find duplicate API calls within time windows"""
        duplicates = {}
        
        for signature, calls in self.duplicate_signatures.items():
            if len(calls) > 1:
                # Check if duplicates are within short time window (potential inefficiency)
                recent_calls = [call for call in calls 
                              if time.time() - call['timestamp'] < 300]  # 5 minutes
                
                if len(recent_calls) > 2:  # More than 2 identical calls in 5 minutes
                    duplicates[signature] = recent_calls
        
        return duplicates
    
    def analyze_call_frequency(self) -> Dict[str, Dict]:
        """Analyze API call frequency patterns"""
        frequency_analysis = {}
        
        for endpoint, calls in self.endpoint_registry.items():
            if len(calls) < 3:
                continue
                
            # Calculate calls per hour
            recent_calls = [call for call in calls 
                          if time.time() - call['timestamp'] < 3600]  # Last hour
            
            calls_per_hour = len(recent_calls)
            
            # Calculate average response time
            response_times = [call['response_time'] for call in recent_calls 
                            if call['response_time'] is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Detect high-frequency endpoints
            frequency_analysis[endpoint] = {
                'calls_per_hour': calls_per_hour,
                'avg_response_time': avg_response_time,
                'total_calls': len(calls),
                'is_high_frequency': calls_per_hour > 60,  # More than 1 call per minute
                'is_slow': avg_response_time > 2.0  # Slower than 2 seconds
            }
        
        return frequency_analysis
    
    def detect_payload_drift(self) -> List[Dict]:
        """Detect payload structure drift in API responses"""
        drift_alerts = []
        
        for endpoint, calls in self.endpoint_registry.items():
            if len(calls) < 10:  # Need sufficient data
                continue
            
            # Analyze payload structure changes
            recent_payloads = [call['payload'] for call in calls[-10:] 
                             if call['payload'] is not None]
            
            if len(recent_payloads) < 5:
                continue
            
            # Simple drift detection: check for consistent field presence
            field_consistency = self._check_field_consistency(recent_payloads)
            
            if field_consistency['drift_detected']:
                drift_alert = {
                    'endpoint': endpoint,
                    'drift_type': 'payload_structure',
                    'severity': 'medium',
                    'description': f"Field consistency issues detected: {field_consistency['issues']}",
                    'timestamp': time.time()
                }
                drift_alerts.append(drift_alert)
                self._store_drift_analysis(drift_alert)
        
        return drift_alerts
    
    def _check_field_consistency(self, payloads: List[Dict]) -> Dict:
        """Check field consistency across payloads"""
        if not payloads:
            return {'drift_detected': False, 'issues': []}
        
        # Get all unique fields across payloads
        all_fields = set()
        for payload in payloads:
            if isinstance(payload, dict):
                all_fields.update(payload.keys())
        
        # Check field presence consistency
        field_presence = {}
        for field in all_fields:
            presence_count = sum(1 for payload in payloads 
                               if isinstance(payload, dict) and field in payload)
            field_presence[field] = presence_count / len(payloads)
        
        # Detect inconsistent fields (present in less than 80% of calls)
        inconsistent_fields = [field for field, presence in field_presence.items() 
                             if presence < 0.8]
        
        return {
            'drift_detected': len(inconsistent_fields) > 0,
            'issues': inconsistent_fields,
            'field_presence': field_presence
        }
    
    def _generate_optimization_suggestions(self, duplicates: Dict, frequency_analysis: Dict):
        """Generate optimization suggestions based on analysis"""
        suggestions = []
        
        # Duplicate call optimization
        for signature, calls in duplicates.items():
            suggestion = {
                'type': 'duplicate_elimination',
                'endpoint': calls[0]['url'],
                'description': f"Found {len(calls)} duplicate calls in 5 minutes",
                'suggestion': "Implement caching or request deduplication",
                'potential_savings': f"{(len(calls) - 1) / len(calls) * 100:.1f}% reduction in calls",
                'priority': 'high' if len(calls) > 5 else 'medium'
            }
            suggestions.append(suggestion)
        
        # High-frequency endpoint optimization
        for endpoint, analysis in frequency_analysis.items():
            if analysis['is_high_frequency']:
                suggestion = {
                    'type': 'frequency_optimization',
                    'endpoint': endpoint,
                    'description': f"High frequency: {analysis['calls_per_hour']} calls/hour",
                    'suggestion': "Consider WebSocket connection or bulk endpoint",
                    'potential_savings': "30-50% reduction in HTTP overhead",
                    'priority': 'high' if analysis['calls_per_hour'] > 120 else 'medium'
                }
                suggestions.append(suggestion)
        
        # Store suggestions in database
        for suggestion in suggestions:
            self._store_optimization_recommendation(suggestion)
        
        self.optimization_suggestions.extend(suggestions)
    
    def _store_drift_analysis(self, drift_alert: Dict):
        """Store drift analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO drift_analysis (endpoint, drift_type, severity, description)
            VALUES (?, ?, ?, ?)
        ''', (
            drift_alert['endpoint'],
            drift_alert['drift_type'],
            drift_alert['severity'],
            drift_alert['description']
        ))
        
        conn.commit()
        conn.close()
    
    def _store_optimization_recommendation(self, suggestion: Dict):
        """Store optimization recommendation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO optimization_recommendations 
            (endpoint, optimization_type, potential_savings_percent, implementation_priority)
            VALUES (?, ?, ?, ?)
        ''', (
            suggestion['endpoint'],
            suggestion['type'],
            50.0,  # Default potential savings
            suggestion['priority']
        ))
        
        conn.commit()
        conn.close()
    
    def _start_background_analysis(self):
        """Start background thread for continuous analysis"""
        def analysis_worker():
            while True:
                time.sleep(60)  # Run analysis every minute
                try:
                    self._cleanup_old_logs()
                    self._generate_periodic_report()
                except Exception as e:
                    logger.error(f"Background analysis error: {e}")
        
        analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
        analysis_thread.start()
        logger.info("QQ API Drift Optimizer: Background analysis started")
    
    def _cleanup_old_logs(self):
        """Clean up old log entries to prevent memory bloat"""
        cutoff_time = time.time() - (24 * 3600)  # 24 hours ago
        
        # Remove from memory
        self.api_call_log = [call for call in self.api_call_log 
                           if call['timestamp'] > cutoff_time]
        
        # Clean up endpoint registry
        for endpoint in list(self.endpoint_registry.keys()):
            self.endpoint_registry[endpoint] = [
                call for call in self.endpoint_registry[endpoint]
                if call['timestamp'] > cutoff_time
            ]
            if not self.endpoint_registry[endpoint]:
                del self.endpoint_registry[endpoint]
    
    def _generate_periodic_report(self):
        """Generate periodic optimization report"""
        if len(self.api_call_log) < 10:
            return
        
        report = {
            'total_calls_last_hour': len([call for call in self.api_call_log 
                                        if time.time() - call['timestamp'] < 3600]),
            'unique_endpoints': len(self.endpoint_registry),
            'duplicate_signatures': len([sig for sig, calls in self.duplicate_signatures.items() 
                                       if len(calls) > 1]),
            'optimization_opportunities': len(self.optimization_suggestions),
            'timestamp': time.time()
        }
        
        logger.info(f"QQ API Drift Report: {report}")
    
    def get_optimization_dashboard_data(self) -> Dict[str, Any]:
        """Get data for optimization dashboard"""
        
        # Recent activity (last hour)
        recent_calls = [call for call in self.api_call_log 
                       if time.time() - call['timestamp'] < 3600]
        
        # Top endpoints by frequency
        endpoint_frequency = {}
        for call in recent_calls:
            endpoint_frequency[call['url']] = endpoint_frequency.get(call['url'], 0) + 1
        
        top_endpoints = sorted(endpoint_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Current optimization suggestions
        high_priority_suggestions = [s for s in self.optimization_suggestions 
                                   if s.get('priority') == 'high']
        
        return {
            'summary': {
                'total_calls_last_hour': len(recent_calls),
                'unique_endpoints': len(self.endpoint_registry),
                'duplicate_calls_detected': len([sig for sig, calls in self.duplicate_signatures.items() 
                                               if len(calls) > 1]),
                'optimization_suggestions': len(self.optimization_suggestions),
                'high_priority_suggestions': len(high_priority_suggestions)
            },
            'top_endpoints': top_endpoints,
            'optimization_suggestions': high_priority_suggestions[:5],
            'drift_alerts': self.drift_alerts[-5:],  # Last 5 alerts
            'last_updated': datetime.now().isoformat()
        }

# Global instance
_qq_api_optimizer = None

def get_qq_api_optimizer() -> QQApiDriftOptimizer:
    """Get global QQ API Drift Optimizer instance"""
    global _qq_api_optimizer
    if _qq_api_optimizer is None:
        _qq_api_optimizer = QQApiDriftOptimizer()
    return _qq_api_optimizer

def log_api_call(method: str, url: str, payload: Dict = None, 
                 headers: Dict = None, response_status: int = None,
                 response_time: float = None, response_size: int = None):
    """Convenience function to log API calls"""
    optimizer = get_qq_api_optimizer()
    optimizer.log_api_call(method, url, payload, headers, response_status, response_time, response_size)

def get_optimization_dashboard_data() -> Dict[str, Any]:
    """Get optimization dashboard data"""
    optimizer = get_qq_api_optimizer()
    return optimizer.get_optimization_dashboard_data()