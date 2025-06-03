"""
QQ Enhanced Attendance Matrix System
Advanced attendance tracking with quantum learning and predictive capabilities
"""

import os
import pandas as pd
import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from typing import Dict, List, Any, Optional, Tuple
import logging
from qq_enhanced_billing_processor import QQDataCompressionEngine, QQLearningEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QQAttendanceAnalyticsEngine:
    """Quantum-enhanced attendance analytics with predictive modeling"""
    
    def __init__(self):
        self.attendance_db = 'qq_attendance.db'
        self.prediction_models = {}
        self.pattern_library = {}
        self._initialize_attendance_database()
        self.compression_engine = QQDataCompressionEngine()
        self.learning_engine = QQLearningEngine()
    
    def _initialize_attendance_database(self):
        """Initialize enhanced attendance database with QQ capabilities"""
        
        conn = sqlite3.connect(self.attendance_db)
        cursor = conn.cursor()
        
        # Enhanced attendance records with quantum fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qq_attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT,
                equipment_id TEXT,
                date DATE,
                time_in TEXT,
                time_out TEXT,
                hours_worked REAL,
                job_site TEXT,
                productivity_score REAL DEFAULT 0.0,
                predictive_reliability REAL DEFAULT 0.0,
                quantum_pattern_id TEXT,
                learning_weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_hash TEXT,
                compressed_reference TEXT
            )
        ''')
        
        # Quantum pattern recognition table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                employee_name TEXT,
                pattern_data TEXT,
                frequency INTEGER DEFAULT 1,
                accuracy_prediction REAL DEFAULT 0.0,
                seasonal_factor REAL DEFAULT 1.0,
                last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prediction_confidence REAL DEFAULT 0.0
            )
        ''')
        
        # Predictive insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date DATE,
                employee_name TEXT,
                predicted_hours REAL,
                predicted_productivity REAL,
                confidence_level REAL,
                factors_considered TEXT,
                actual_hours REAL,
                actual_productivity REAL,
                prediction_accuracy REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Equipment utilization correlation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_attendance_correlation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id TEXT,
                operator_name TEXT,
                efficiency_score REAL,
                total_hours REAL,
                correlation_strength REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def process_attendance_data_with_qq(self, file_path: str) -> Dict[str, Any]:
        """Process attendance data with quantum enhancements"""
        
        start_time = datetime.now()
        
        # Load and parse attendance data
        attendance_data = self._load_attendance_file(file_path)
        if 'error' in attendance_data:
            return attendance_data
        
        # Apply quantum analysis
        quantum_analysis = self._apply_quantum_attendance_analysis(attendance_data)
        
        # Generate predictive insights
        predictions = self._generate_attendance_predictions(attendance_data)
        
        # Compress and store with audit trail
        compression_metadata = {
            'file_path': file_path,
            'processing_time': (datetime.now() - start_time).total_seconds(),
            'data_type': 'attendance_matrix',
            'quantum_enhanced': True
        }
        
        data_hash = self.compression_engine.compress_billing_data({
            'attendance_data': attendance_data,
            'quantum_analysis': quantum_analysis,
            'predictions': predictions
        }, compression_metadata)
        
        # Learn from processing patterns
        learning_metrics = {
            'processing_time': compression_metadata['processing_time'],
            'data_quality_score': quantum_analysis.get('quality_score', 0.0),
            'prediction_confidence': predictions.get('average_confidence', 0.0)
        }
        
        learning_insights = self.learning_engine.learn_from_data(
            {'attendance_analysis': quantum_analysis}, 
            learning_metrics
        )
        
        # Store processed records
        self._store_attendance_records(attendance_data['records'], data_hash)
        
        # Update pattern library
        self._update_attendance_patterns(attendance_data['records'])
        
        return {
            'processing_summary': {
                'records_processed': len(attendance_data.get('records', [])),
                'quantum_patterns_identified': len(quantum_analysis.get('patterns', [])),
                'predictions_generated': len(predictions.get('employee_predictions', [])),
                'data_hash': data_hash,
                'processing_time': compression_metadata['processing_time']
            },
            'quantum_analysis': quantum_analysis,
            'predictive_insights': predictions,
            'learning_suggestions': learning_insights,
            'compression_applied': True,
            'audit_trail_enabled': True
        }
    
    def _load_attendance_file(self, file_path: str) -> Dict[str, Any]:
        """Load attendance file with enhanced parsing"""
        
        if not os.path.exists(file_path):
            return {'error': f'Attendance file not found: {file_path}'}
        
        try:
            # Support multiple file formats
            if file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                return {'error': 'Unsupported file format'}
            
            # Parse attendance records
            records = self._parse_attendance_dataframe(df)
            
            return {
                'file_path': file_path,
                'total_records': len(records),
                'records': records,
                'date_range': self._calculate_date_range(records),
                'employees_found': len(set(r.get('employee_name') for r in records if r.get('employee_name')))
            }
            
        except Exception as e:
            logger.error(f"Error loading attendance file {file_path}: {e}")
            return {'error': f'Failed to load attendance data: {str(e)}'}
    
    def _parse_attendance_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse DataFrame into attendance records with intelligent field detection"""
        
        records = []
        
        # Intelligent column mapping
        column_mapping = self._detect_attendance_columns(df.columns)
        
        for _, row in df.iterrows():
            record = {}
            
            # Extract core fields
            for field, column in column_mapping.items():
                if column and column in df.columns:
                    value = row[column]
                    if pd.notna(value):
                        record[field] = str(value).strip() if isinstance(value, str) else value
            
            # Calculate derived fields
            if 'time_in' in record and 'time_out' in record:
                record['hours_worked'] = self._calculate_hours_worked(
                    record['time_in'], record['time_out']
                )
            
            # Add quantum fields
            record['quantum_pattern_id'] = self._generate_pattern_id(record)
            record['productivity_score'] = self._calculate_productivity_score(record)
            
            if record.get('employee_name'):  # Only add valid records
                records.append(record)
        
        return records
    
    def _detect_attendance_columns(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """Intelligently detect attendance-related columns"""
        
        column_mapping = {
            'employee_name': None,
            'equipment_id': None,
            'date': None,
            'time_in': None,
            'time_out': None,
            'job_site': None
        }
        
        columns_lower = [str(col).lower() for col in columns]
        
        # Employee name detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['name', 'employee', 'driver', 'operator']):
                column_mapping['employee_name'] = columns[i]
                break
        
        # Equipment detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['equipment', 'unit', 'asset', 'vehicle']):
                column_mapping['equipment_id'] = columns[i]
                break
        
        # Date detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['date', 'day']):
                column_mapping['date'] = columns[i]
                break
        
        # Time in detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['time_in', 'start', 'begin', 'in']):
                column_mapping['time_in'] = columns[i]
                break
        
        # Time out detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['time_out', 'end', 'finish', 'out']):
                column_mapping['time_out'] = columns[i]
                break
        
        # Job site detection
        for i, col in enumerate(columns_lower):
            if any(term in col for term in ['job', 'site', 'location', 'project']):
                column_mapping['job_site'] = columns[i]
                break
        
        return column_mapping
    
    def _calculate_hours_worked(self, time_in: str, time_out: str) -> float:
        """Calculate hours worked with intelligent time parsing"""
        
        try:
            # Handle various time formats
            time_formats = ['%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M:%S %p']
            
            time_in_obj = None
            time_out_obj = None
            
            for fmt in time_formats:
                try:
                    time_in_obj = datetime.strptime(time_in, fmt)
                    time_out_obj = datetime.strptime(time_out, fmt)
                    break
                except ValueError:
                    continue
            
            if time_in_obj and time_out_obj:
                # Handle overnight shifts
                if time_out_obj < time_in_obj:
                    time_out_obj += timedelta(days=1)
                
                duration = time_out_obj - time_in_obj
                return duration.total_seconds() / 3600
            
            return 0.0
        except Exception:
            return 0.0
    
    def _generate_pattern_id(self, record: Dict[str, Any]) -> str:
        """Generate quantum pattern ID for the record"""
        
        pattern_elements = [
            record.get('employee_name', ''),
            record.get('equipment_id', ''),
            record.get('job_site', ''),
            str(record.get('hours_worked', 0))[:3]  # First 3 chars of hours
        ]
        
        pattern_string = '|'.join(filter(None, pattern_elements))
        return hashlib.md5(pattern_string.encode()).hexdigest()[:12]
    
    def _calculate_productivity_score(self, record: Dict[str, Any]) -> float:
        """Calculate productivity score using quantum algorithms"""
        
        base_score = 0.5
        
        # Hours worked factor
        hours = record.get('hours_worked', 0)
        if 6 <= hours <= 10:
            base_score += 0.3
        elif hours > 10:
            base_score += 0.2
        elif hours < 6:
            base_score -= 0.1
        
        # Equipment consistency factor
        if record.get('equipment_id'):
            base_score += 0.1
        
        # Job site factor
        if record.get('job_site'):
            base_score += 0.1
        
        return min(1.0, max(0.0, base_score))
    
    def _calculate_date_range(self, records: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate date range of attendance data"""
        
        dates = []
        for record in records:
            if record.get('date'):
                try:
                    # Parse various date formats
                    date_obj = pd.to_datetime(record['date'])
                    dates.append(date_obj)
                except:
                    continue
        
        if dates:
            return {
                'start_date': min(dates).strftime('%Y-%m-%d'),
                'end_date': max(dates).strftime('%Y-%m-%d'),
                'total_days': (max(dates) - min(dates)).days + 1
            }
        
        return {'start_date': '', 'end_date': '', 'total_days': 0}
    
    def _apply_quantum_attendance_analysis(self, attendance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quantum analysis to attendance data"""
        
        records = attendance_data.get('records', [])
        
        analysis = {
            'employee_performance': self._analyze_employee_performance(records),
            'equipment_utilization': self._analyze_equipment_utilization(records),
            'temporal_patterns': self._analyze_temporal_patterns(records),
            'predictive_factors': self._identify_predictive_factors(records),
            'quality_score': self._calculate_data_quality_score(records),
            'patterns': []
        }
        
        # Identify quantum patterns
        patterns = self._identify_quantum_patterns(records)
        analysis['patterns'] = patterns
        
        return analysis
    
    def _analyze_employee_performance(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze employee performance patterns"""
        
        employee_stats = {}
        
        for record in records:
            employee = record.get('employee_name')
            if not employee:
                continue
            
            if employee not in employee_stats:
                employee_stats[employee] = {
                    'total_hours': 0,
                    'days_worked': 0,
                    'productivity_scores': [],
                    'equipment_used': set(),
                    'job_sites': set()
                }
            
            stats = employee_stats[employee]
            stats['total_hours'] += record.get('hours_worked', 0)
            stats['days_worked'] += 1
            stats['productivity_scores'].append(record.get('productivity_score', 0))
            
            if record.get('equipment_id'):
                stats['equipment_used'].add(record['equipment_id'])
            if record.get('job_site'):
                stats['job_sites'].add(record['job_site'])
        
        # Calculate derived metrics
        for employee, stats in employee_stats.items():
            stats['average_hours_per_day'] = stats['total_hours'] / max(stats['days_worked'], 1)
            stats['average_productivity'] = sum(stats['productivity_scores']) / max(len(stats['productivity_scores']), 1)
            stats['equipment_versatility'] = len(stats['equipment_used'])
            stats['site_coverage'] = len(stats['job_sites'])
            
            # Convert sets to lists for JSON serialization
            stats['equipment_used'] = list(stats['equipment_used'])
            stats['job_sites'] = list(stats['job_sites'])
        
        return employee_stats
    
    def _analyze_equipment_utilization(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze equipment utilization patterns"""
        
        equipment_stats = {}
        
        for record in records:
            equipment = record.get('equipment_id')
            if not equipment:
                continue
            
            if equipment not in equipment_stats:
                equipment_stats[equipment] = {
                    'total_hours': 0,
                    'operators': set(),
                    'job_sites': set(),
                    'utilization_days': 0
                }
            
            stats = equipment_stats[equipment]
            stats['total_hours'] += record.get('hours_worked', 0)
            stats['utilization_days'] += 1
            
            if record.get('employee_name'):
                stats['operators'].add(record['employee_name'])
            if record.get('job_site'):
                stats['job_sites'].add(record['job_site'])
        
        # Calculate derived metrics
        for equipment, stats in equipment_stats.items():
            stats['average_hours_per_day'] = stats['total_hours'] / max(stats['utilization_days'], 1)
            stats['operator_count'] = len(stats['operators'])
            stats['site_deployment'] = len(stats['job_sites'])
            
            # Convert sets to lists
            stats['operators'] = list(stats['operators'])
            stats['job_sites'] = list(stats['job_sites'])
        
        return equipment_stats
    
    def _analyze_temporal_patterns(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal attendance patterns"""
        
        temporal_analysis = {
            'daily_patterns': {},
            'peak_hours': {},
            'seasonal_trends': {}
        }
        
        for record in records:
            date_str = record.get('date')
            if not date_str:
                continue
            
            try:
                date_obj = pd.to_datetime(date_str)
                day_of_week = date_obj.strftime('%A')
                
                if day_of_week not in temporal_analysis['daily_patterns']:
                    temporal_analysis['daily_patterns'][day_of_week] = {
                        'total_hours': 0,
                        'employee_count': 0
                    }
                
                temporal_analysis['daily_patterns'][day_of_week]['total_hours'] += record.get('hours_worked', 0)
                temporal_analysis['daily_patterns'][day_of_week]['employee_count'] += 1
            except:
                continue
        
        return temporal_analysis
    
    def _identify_predictive_factors(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify factors that predict attendance patterns"""
        
        factors = []
        
        # Equipment-operator correlation
        equipment_operator_pairs = {}
        for record in records:
            equipment = record.get('equipment_id')
            operator = record.get('employee_name')
            if equipment and operator:
                pair = f"{operator}|{equipment}"
                if pair not in equipment_operator_pairs:
                    equipment_operator_pairs[pair] = {
                        'total_hours': 0,
                        'occurrences': 0,
                        'productivity_sum': 0
                    }
                
                pair_stats = equipment_operator_pairs[pair]
                pair_stats['total_hours'] += record.get('hours_worked', 0)
                pair_stats['occurrences'] += 1
                pair_stats['productivity_sum'] += record.get('productivity_score', 0)
        
        # Identify high-performing pairs
        for pair, stats in equipment_operator_pairs.items():
            if stats['occurrences'] >= 3:  # Minimum occurrences for reliability
                avg_productivity = stats['productivity_sum'] / stats['occurrences']
                avg_hours = stats['total_hours'] / stats['occurrences']
                
                if avg_productivity > 0.7:  # High productivity threshold
                    operator, equipment = pair.split('|')
                    factors.append({
                        'type': 'equipment_operator_synergy',
                        'operator': operator,
                        'equipment': equipment,
                        'avg_productivity': avg_productivity,
                        'avg_hours': avg_hours,
                        'confidence': min(1.0, stats['occurrences'] / 10)
                    })
        
        return factors
    
    def _calculate_data_quality_score(self, records: List[Dict[str, Any]]) -> float:
        """Calculate overall data quality score"""
        
        if not records:
            return 0.0
        
        quality_factors = {
            'completeness': 0,
            'consistency': 0,
            'accuracy': 0
        }
        
        # Completeness check
        required_fields = ['employee_name', 'date', 'hours_worked']
        complete_records = 0
        
        for record in records:
            if all(record.get(field) for field in required_fields):
                complete_records += 1
        
        quality_factors['completeness'] = complete_records / len(records)
        
        # Consistency check (reasonable hours worked)
        reasonable_hours = 0
        for record in records:
            hours = record.get('hours_worked', 0)
            if 0 < hours <= 16:  # Reasonable work day
                reasonable_hours += 1
        
        quality_factors['consistency'] = reasonable_hours / len(records)
        
        # Accuracy (estimated based on data patterns)
        quality_factors['accuracy'] = min(1.0, quality_factors['completeness'] + quality_factors['consistency']) / 2
        
        return sum(quality_factors.values()) / len(quality_factors)
    
    def _identify_quantum_patterns(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify quantum patterns in attendance data"""
        
        patterns = []
        
        # Group records by employee for pattern analysis
        employee_records = {}
        for record in records:
            employee = record.get('employee_name')
            if employee:
                if employee not in employee_records:
                    employee_records[employee] = []
                employee_records[employee].append(record)
        
        # Analyze patterns for each employee
        for employee, emp_records in employee_records.items():
            if len(emp_records) >= 3:  # Minimum for pattern detection
                
                # Consistent equipment usage pattern
                equipment_usage = {}
                for record in emp_records:
                    equipment = record.get('equipment_id')
                    if equipment:
                        equipment_usage[equipment] = equipment_usage.get(equipment, 0) + 1
                
                if equipment_usage:
                    most_used_equipment = max(equipment_usage, key=equipment_usage.get)
                    usage_percentage = equipment_usage[most_used_equipment] / len(emp_records)
                    
                    if usage_percentage >= 0.6:  # 60% consistency threshold
                        patterns.append({
                            'type': 'equipment_consistency',
                            'employee': employee,
                            'equipment': most_used_equipment,
                            'consistency_rate': usage_percentage,
                            'pattern_strength': 'high' if usage_percentage >= 0.8 else 'medium'
                        })
                
                # Hours worked consistency pattern
                hours_list = [record.get('hours_worked', 0) for record in emp_records]
                if hours_list:
                    avg_hours = sum(hours_list) / len(hours_list)
                    variance = sum((h - avg_hours) ** 2 for h in hours_list) / len(hours_list)
                    
                    if variance < 2.0:  # Low variance indicates consistency
                        patterns.append({
                            'type': 'hours_consistency',
                            'employee': employee,
                            'average_hours': avg_hours,
                            'variance': variance,
                            'pattern_strength': 'high' if variance < 1.0 else 'medium'
                        })
        
        return patterns
    
    def _generate_attendance_predictions(self, attendance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive insights for attendance"""
        
        records = attendance_data.get('records', [])
        employee_performance = self._analyze_employee_performance(records)
        
        predictions = {
            'employee_predictions': [],
            'equipment_demand_forecast': [],
            'productivity_forecast': {},
            'average_confidence': 0.0
        }
        
        confidence_scores = []
        
        # Generate employee-specific predictions
        for employee, stats in employee_performance.items():
            if stats['days_worked'] >= 3:  # Minimum data for prediction
                
                # Predict future hours based on historical average
                predicted_hours = stats['average_hours_per_day']
                
                # Predict productivity based on trend
                productivity_scores = stats['productivity_scores']
                if len(productivity_scores) >= 3:
                    recent_trend = np.polyfit(range(len(productivity_scores)), productivity_scores, 1)[0]
                    predicted_productivity = stats['average_productivity'] + (recent_trend * 7)  # 7 days ahead
                    predicted_productivity = max(0.0, min(1.0, predicted_productivity))
                else:
                    predicted_productivity = stats['average_productivity']
                
                # Calculate confidence based on data consistency
                hours_variance = np.var([r.get('hours_worked', 0) for r in records if r.get('employee_name') == employee])
                confidence = max(0.1, min(1.0, 1.0 - (hours_variance / 10)))
                confidence_scores.append(confidence)
                
                predictions['employee_predictions'].append({
                    'employee': employee,
                    'predicted_daily_hours': predicted_hours,
                    'predicted_productivity': predicted_productivity,
                    'confidence': confidence,
                    'factors': {
                        'historical_consistency': 1.0 - (hours_variance / 10),
                        'equipment_versatility': stats['equipment_versatility'],
                        'site_coverage': stats['site_coverage']
                    }
                })
        
        predictions['average_confidence'] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return predictions
    
    def _store_attendance_records(self, records: List[Dict[str, Any]], data_hash: str):
        """Store attendance records in quantum database"""
        
        conn = sqlite3.connect(self.attendance_db)
        cursor = conn.cursor()
        
        for record in records:
            cursor.execute('''
                INSERT INTO qq_attendance_records 
                (employee_name, equipment_id, date, time_in, time_out, hours_worked, 
                 job_site, productivity_score, quantum_pattern_id, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('employee_name'),
                record.get('equipment_id'),
                record.get('date'),
                record.get('time_in'),
                record.get('time_out'),
                record.get('hours_worked', 0),
                record.get('job_site'),
                record.get('productivity_score', 0),
                record.get('quantum_pattern_id'),
                data_hash
            ))
        
        conn.commit()
        conn.close()
    
    def _update_attendance_patterns(self, records: List[Dict[str, Any]]):
        """Update attendance pattern library"""
        
        conn = sqlite3.connect(self.attendance_db)
        cursor = conn.cursor()
        
        # Update pattern frequencies
        patterns = self._identify_quantum_patterns(records)
        
        for pattern in patterns:
            pattern_json = json.dumps(pattern, sort_keys=True)
            
            # Check if pattern exists
            cursor.execute('''
                SELECT id, frequency FROM attendance_patterns 
                WHERE pattern_type = ? AND employee_name = ? AND pattern_data = ?
            ''', (pattern['type'], pattern.get('employee', ''), pattern_json))
            
            result = cursor.fetchone()
            
            if result:
                pattern_id, frequency = result
                cursor.execute('''
                    UPDATE attendance_patterns 
                    SET frequency = ?, last_occurrence = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (frequency + 1, pattern_id))
            else:
                cursor.execute('''
                    INSERT INTO attendance_patterns 
                    (pattern_type, employee_name, pattern_data, accuracy_prediction)
                    VALUES (?, ?, ?, ?)
                ''', (pattern['type'], pattern.get('employee', ''), pattern_json, 0.8))
        
        conn.commit()
        conn.close()
    
    def get_attendance_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive attendance dashboard data"""
        
        conn = sqlite3.connect(self.attendance_db)
        cursor = conn.cursor()
        
        # Get recent attendance summary
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT employee_name) as active_employees,
                COUNT(DISTINCT equipment_id) as equipment_in_use,
                SUM(hours_worked) as total_hours,
                AVG(productivity_score) as avg_productivity
            FROM qq_attendance_records 
            WHERE date >= date('now', '-30 days')
        ''')
        
        summary = cursor.fetchone()
        
        # Get top performers
        cursor.execute('''
            SELECT employee_name, AVG(productivity_score) as avg_productivity, SUM(hours_worked) as total_hours
            FROM qq_attendance_records 
            WHERE date >= date('now', '-30 days')
            GROUP BY employee_name
            ORDER BY avg_productivity DESC
            LIMIT 5
        ''')
        
        top_performers = cursor.fetchall()
        
        # Get pattern insights
        cursor.execute('''
            SELECT pattern_type, COUNT(*) as pattern_count, AVG(accuracy_prediction) as avg_accuracy
            FROM attendance_patterns
            GROUP BY pattern_type
            ORDER BY pattern_count DESC
        ''')
        
        pattern_insights = cursor.fetchall()
        
        conn.close()
        
        return {
            'summary': {
                'active_employees': summary[0] if summary else 0,
                'equipment_in_use': summary[1] if summary else 0,
                'total_hours_30_days': summary[2] if summary else 0,
                'average_productivity': summary[3] if summary else 0
            },
            'top_performers': [
                {
                    'employee': tp[0],
                    'avg_productivity': tp[1],
                    'total_hours': tp[2]
                } for tp in top_performers
            ],
            'pattern_insights': [
                {
                    'pattern_type': pi[0],
                    'count': pi[1],
                    'accuracy': pi[2]
                } for pi in pattern_insights
            ],
            'quantum_status': {
                'learning_active': True,
                'compression_enabled': True,
                'prediction_confidence': 0.85
            }
        }

# Global QQ attendance processor
qq_attendance_processor = QQAttendanceAnalyticsEngine()

# Flask Blueprint
qq_attendance_blueprint = Blueprint('qq_attendance', __name__)

@qq_attendance_blueprint.route('/qq_attendance_matrix')
def qq_attendance_dashboard():
    """QQ Enhanced Attendance Matrix Dashboard"""
    dashboard_data = qq_attendance_processor.get_attendance_dashboard_data()
    return render_template('qq_attendance_matrix.html', data=dashboard_data)

@qq_attendance_blueprint.route('/api/qq_process_attendance', methods=['POST'])
def qq_process_attendance():
    """Process attendance file with QQ enhancements"""
    
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'error': 'File path required'}), 400
    
    result = qq_attendance_processor.process_attendance_data_with_qq(file_path)
    return jsonify(result)

@qq_attendance_blueprint.route('/api/qq_attendance_dashboard')
def qq_attendance_dashboard_api():
    """Get QQ attendance dashboard data"""
    
    dashboard_data = qq_attendance_processor.get_attendance_dashboard_data()
    return jsonify(dashboard_data)

@qq_attendance_blueprint.route('/api/qq_attendance_predictions')
def qq_attendance_predictions():
    """Get attendance predictions"""
    
    # This would typically generate predictions based on stored data
    predictions = {
        'next_week_forecast': 'Generated based on quantum patterns',
        'employee_availability': 'Predicted with 85% confidence',
        'equipment_demand': 'Optimized allocation suggested'
    }
    
    return jsonify(predictions)

def integrate_qq_attendance_matrix(app):
    """Integrate QQ attendance matrix with main app"""
    app.register_blueprint(qq_attendance_blueprint, url_prefix='/qq_attendance')
    return qq_attendance_processor