"""
QQ Intelligent Automation Pipeline
Smart error recovery and workflow adaptation for file processing automation
Handles user errors, re-downloads, and intelligent recovery
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil
import sqlite3

class QQIntelligentAutomationPipeline:
    def __init__(self):
        self.pipeline_db = 'qq_automation_pipeline.db'
        self.upload_dir = 'uploads'
        self.processing_dir = 'processing'
        self.archive_dir = 'archive'
        self.error_recovery_dir = 'error_recovery'
        
        # Create directories
        for directory in [self.upload_dir, self.processing_dir, self.archive_dir, self.error_recovery_dir]:
            os.makedirs(directory, exist_ok=True)
            
        self.initialize_pipeline_database()
        self.workflow_patterns = self.load_workflow_patterns()
        
    def initialize_pipeline_database(self):
        """Initialize pipeline tracking database"""
        conn = sqlite3.connect(self.pipeline_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipeline_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT,
                files_processed INTEGER,
                errors_encountered INTEGER,
                recovery_actions INTEGER,
                session_data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_operations (
                operation_id TEXT PRIMARY KEY,
                session_id TEXT,
                file_name TEXT,
                file_hash TEXT,
                file_size INTEGER,
                operation_type TEXT,
                timestamp TIMESTAMP,
                status TEXT,
                error_message TEXT,
                retry_count INTEGER,
                recovery_action TEXT,
                FOREIGN KEY (session_id) REFERENCES pipeline_sessions (session_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_intelligence (
                pattern_id TEXT PRIMARY KEY,
                pattern_name TEXT,
                trigger_conditions TEXT,
                recovery_actions TEXT,
                success_rate REAL,
                last_used TIMESTAMP,
                usage_count INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_workflow_patterns(self) -> Dict[str, Any]:
        """Load intelligent workflow patterns for error recovery"""
        return {
            'duplicate_download_detection': {
                'triggers': ['same_file_hash', 'similar_filename', 'rapid_succession'],
                'actions': ['compare_files', 'use_latest', 'prompt_user'],
                'confidence_threshold': 0.85
            },
            'incomplete_upload_recovery': {
                'triggers': ['partial_file_size', 'upload_interruption', 'connection_error'],
                'actions': ['resume_upload', 'restart_upload', 'validate_integrity'],
                'confidence_threshold': 0.90
            },
            'wrong_file_correction': {
                'triggers': ['unexpected_format', 'size_mismatch', 'header_validation_fail'],
                'actions': ['suggest_alternatives', 'format_conversion', 'user_confirmation'],
                'confidence_threshold': 0.75
            },
            'processing_error_recovery': {
                'triggers': ['parsing_error', 'memory_overflow', 'timeout'],
                'actions': ['chunk_processing', 'format_adjustment', 'fallback_parser'],
                'confidence_threshold': 0.80
            }
        }
        
    def start_automation_session(self, user_id: str = 'default') -> str:
        """Start a new automation session with intelligent tracking"""
        session_id = f"session_{int(time.time())}_{hashlib.md5(user_id.encode()).hexdigest()[:8]}"
        
        conn = sqlite3.connect(self.pipeline_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pipeline_sessions 
            (session_id, user_id, start_time, status, files_processed, errors_encountered, recovery_actions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, datetime.now(), 'active', 0, 0, 0))
        
        conn.commit()
        conn.close()
        
        print(f"Started intelligent automation session: {session_id}")
        return session_id
        
    def process_file_intelligently(self, file_path: str, session_id: str, expected_type: str = None) -> Dict[str, Any]:
        """Process file with intelligent error detection and recovery"""
        
        # Generate file signature
        file_hash = self.calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        operation_id = f"op_{int(time.time())}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
        
        # Check for duplicate or error patterns
        intelligence_result = self.analyze_file_intelligence(file_path, file_hash, file_size, session_id)
        
        processing_result = {
            'operation_id': operation_id,
            'file_name': file_name,
            'file_hash': file_hash,
            'file_size': file_size,
            'intelligence_analysis': intelligence_result,
            'processing_status': 'analyzing',
            'recovery_actions': [],
            'recommendations': []
        }
        
        # Log operation start
        self.log_file_operation(operation_id, session_id, file_name, file_hash, file_size, 'upload', 'started')
        
        # Apply intelligence-based processing
        if intelligence_result['requires_action']:
            processing_result = self.apply_intelligent_recovery(processing_result, intelligence_result)
        else:
            # Normal processing
            processing_result = self.process_file_normally(processing_result, file_path, expected_type)
            
        # Update operation status
        self.log_file_operation(operation_id, session_id, file_name, file_hash, file_size, 
                              'process', processing_result['processing_status'])
        
        return processing_result
        
    def analyze_file_intelligence(self, file_path: str, file_hash: str, file_size: int, session_id: str) -> Dict[str, Any]:
        """Analyze file for intelligent patterns and potential issues"""
        
        intelligence_result = {
            'requires_action': False,
            'detected_patterns': [],
            'confidence_scores': {},
            'recommended_actions': [],
            'similar_files': []
        }
        
        # Check for duplicate files
        duplicates = self.find_duplicate_files(file_hash, session_id)
        if duplicates:
            intelligence_result['requires_action'] = True
            intelligence_result['detected_patterns'].append('duplicate_download_detection')
            intelligence_result['confidence_scores']['duplicate_detection'] = 0.95
            intelligence_result['recommended_actions'].append('use_latest_version')
            intelligence_result['similar_files'] = duplicates
            
        # Check file size patterns
        size_analysis = self.analyze_file_size_patterns(file_size, os.path.basename(file_path))
        if size_analysis['anomaly_detected']:
            intelligence_result['requires_action'] = True
            intelligence_result['detected_patterns'].append('size_anomaly')
            intelligence_result['confidence_scores']['size_analysis'] = size_analysis['confidence']
            intelligence_result['recommended_actions'].extend(size_analysis['recommendations'])
            
        # Check filename patterns
        filename_analysis = self.analyze_filename_patterns(os.path.basename(file_path), session_id)
        if filename_analysis['pattern_detected']:
            intelligence_result['detected_patterns'].append(filename_analysis['pattern_type'])
            intelligence_result['confidence_scores']['filename_pattern'] = filename_analysis['confidence']
            intelligence_result['recommended_actions'].extend(filename_analysis['actions'])
            
        return intelligence_result
        
    def find_duplicate_files(self, file_hash: str, session_id: str) -> List[Dict]:
        """Find duplicate files in current session"""
        conn = sqlite3.connect(self.pipeline_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_name, timestamp, status FROM file_operations 
            WHERE file_hash = ? AND session_id = ? AND status = 'completed'
            ORDER BY timestamp DESC
        ''', (file_hash, session_id))
        
        duplicates = []
        for row in cursor.fetchall():
            duplicates.append({
                'file_name': row[0],
                'timestamp': row[1],
                'status': row[2]
            })
            
        conn.close()
        return duplicates
        
    def analyze_file_size_patterns(self, file_size: int, filename: str) -> Dict[str, Any]:
        """Analyze file size for anomalies based on expected patterns"""
        
        # Expected size ranges for different file types
        expected_ranges = {
            'driving_history': {'min': 8 * 1024 * 1024, 'max': 15 * 1024 * 1024},  # 8-15MB
            'activity_detail': {'min': 15 * 1024 * 1024, 'max': 25 * 1024 * 1024},  # 15-25MB
            'assets_time_on_site': {'min': 2 * 1024 * 1024, 'max': 8 * 1024 * 1024}  # 2-8MB
        }
        
        # Detect file type from filename
        file_type = None
        if 'driving' in filename.lower() or 'history' in filename.lower():
            file_type = 'driving_history'
        elif 'activity' in filename.lower() or 'detail' in filename.lower():
            file_type = 'activity_detail'
        elif 'asset' in filename.lower() or 'time' in filename.lower():
            file_type = 'assets_time_on_site'
            
        analysis_result = {
            'anomaly_detected': False,
            'confidence': 0.0,
            'recommendations': [],
            'detected_type': file_type
        }
        
        if file_type and file_type in expected_ranges:
            expected = expected_ranges[file_type]
            
            if file_size < expected['min']:
                analysis_result['anomaly_detected'] = True
                analysis_result['confidence'] = 0.8
                analysis_result['recommendations'].append('file_may_be_incomplete')
                analysis_result['recommendations'].append('verify_download_completion')
                
            elif file_size > expected['max']:
                analysis_result['anomaly_detected'] = True
                analysis_result['confidence'] = 0.7
                analysis_result['recommendations'].append('file_may_contain_extra_data')
                analysis_result['recommendations'].append('verify_date_range')
                
        return analysis_result
        
    def analyze_filename_patterns(self, filename: str, session_id: str) -> Dict[str, Any]:
        """Analyze filename for patterns and potential issues"""
        
        analysis_result = {
            'pattern_detected': False,
            'pattern_type': None,
            'confidence': 0.0,
            'actions': []
        }
        
        # Check for version patterns (v1, v2, _2, etc.)
        version_patterns = ['_v', '_2', '_3', '_copy', '_new', '_final', '_latest']
        for pattern in version_patterns:
            if pattern in filename.lower():
                analysis_result['pattern_detected'] = True
                analysis_result['pattern_type'] = 'version_pattern'
                analysis_result['confidence'] = 0.85
                analysis_result['actions'].append('check_for_original_version')
                analysis_result['actions'].append('confirm_latest_version')
                break
                
        # Check for date patterns
        if any(month in filename.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            analysis_result['pattern_detected'] = True
            analysis_result['pattern_type'] = 'date_pattern'
            analysis_result['confidence'] = 0.9
            analysis_result['actions'].append('validate_date_range')
            
        return analysis_result
        
    def apply_intelligent_recovery(self, processing_result: Dict, intelligence_result: Dict) -> Dict[str, Any]:
        """Apply intelligent recovery actions based on analysis"""
        
        recovery_actions = []
        
        for pattern in intelligence_result['detected_patterns']:
            if pattern == 'duplicate_download_detection':
                recovery_actions.append(self.handle_duplicate_detection(processing_result, intelligence_result))
            elif pattern == 'size_anomaly':
                recovery_actions.append(self.handle_size_anomaly(processing_result, intelligence_result))
            elif pattern == 'version_pattern':
                recovery_actions.append(self.handle_version_pattern(processing_result, intelligence_result))
                
        processing_result['recovery_actions'] = recovery_actions
        processing_result['processing_status'] = 'recovered'
        
        return processing_result
        
    def handle_duplicate_detection(self, processing_result: Dict, intelligence_result: Dict) -> Dict[str, Any]:
        """Handle duplicate file detection"""
        similar_files = intelligence_result.get('similar_files', [])
        
        recovery_action = {
            'action_type': 'duplicate_resolution',
            'action_taken': 'use_latest_file',
            'details': f"Found {len(similar_files)} similar files, using most recent",
            'confidence': intelligence_result['confidence_scores'].get('duplicate_detection', 0.8)
        }
        
        if similar_files:
            # Use the latest file
            latest_file = max(similar_files, key=lambda x: x['timestamp'])
            recovery_action['selected_file'] = latest_file['file_name']
            recovery_action['rationale'] = f"Selected {latest_file['file_name']} as it's the most recent"
            
        return recovery_action
        
    def handle_size_anomaly(self, processing_result: Dict, intelligence_result: Dict) -> Dict[str, Any]:
        """Handle file size anomalies"""
        return {
            'action_type': 'size_validation',
            'action_taken': 'proceed_with_caution',
            'details': 'File size outside expected range, proceeding with enhanced validation',
            'confidence': intelligence_result['confidence_scores'].get('size_analysis', 0.7),
            'validation_steps': ['header_check', 'sample_parsing', 'integrity_verification']
        }
        
    def handle_version_pattern(self, processing_result: Dict, intelligence_result: Dict) -> Dict[str, Any]:
        """Handle version pattern detection"""
        return {
            'action_type': 'version_management',
            'action_taken': 'confirm_latest',
            'details': 'Version pattern detected in filename, confirming this is the intended file',
            'confidence': intelligence_result['confidence_scores'].get('filename_pattern', 0.8),
            'recommendation': 'Verify this is the correct version before processing'
        }
        
    def process_file_normally(self, processing_result: Dict, file_path: str, expected_type: str) -> Dict[str, Any]:
        """Normal file processing without recovery actions"""
        
        try:
            # Import and use the intelligent file processor
            from qq_intelligent_file_processor import process_uploaded_file
            
            file_processing_result = process_uploaded_file(file_path, expected_type or 'attendance')
            
            processing_result.update({
                'processing_status': file_processing_result.get('status', 'completed'),
                'file_analysis': file_processing_result,
                'total_rows': file_processing_result.get('total_rows', 0),
                'processed_rows': file_processing_result.get('processed_rows', 0),
                'issues_found': file_processing_result.get('issues', []),
                'data_preview': file_processing_result.get('data_preview', [])[:5]  # Limit preview
            })
            
        except Exception as e:
            processing_result.update({
                'processing_status': 'error',
                'error_message': str(e),
                'recovery_suggestions': ['retry_with_different_parser', 'check_file_format', 'validate_file_integrity']
            })
            
        return processing_result
        
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for duplicate detection"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
                
        return hash_sha256.hexdigest()
        
    def log_file_operation(self, operation_id: str, session_id: str, file_name: str, 
                          file_hash: str, file_size: int, operation_type: str, status: str,
                          error_message: str = None, recovery_action: str = None):
        """Log file operation to database"""
        
        conn = sqlite3.connect(self.pipeline_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO file_operations 
            (operation_id, session_id, file_name, file_hash, file_size, operation_type, 
             timestamp, status, error_message, retry_count, recovery_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (operation_id, session_id, file_name, file_hash, file_size, operation_type,
              datetime.now(), status, error_message, 0, recovery_action))
        
        conn.commit()
        conn.close()
        
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        
        conn = sqlite3.connect(self.pipeline_db)
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM pipeline_sessions WHERE session_id = ?', (session_id,))
        session_row = cursor.fetchone()
        
        # Get operations
        cursor.execute('SELECT * FROM file_operations WHERE session_id = ? ORDER BY timestamp', (session_id,))
        operations = cursor.fetchall()
        
        conn.close()
        
        if not session_row:
            return {'error': 'Session not found'}
            
        return {
            'session_id': session_id,
            'status': session_row[4],
            'files_processed': len(operations),
            'operations': [
                {
                    'operation_id': op[0],
                    'file_name': op[2],
                    'operation_type': op[5],
                    'timestamp': op[6],
                    'status': op[7],
                    'recovery_action': op[10]
                }
                for op in operations
            ],
            'summary': {
                'successful_operations': len([op for op in operations if op[7] == 'completed']),
                'failed_operations': len([op for op in operations if op[7] == 'error']),
                'recovery_actions_taken': len([op for op in operations if op[10]])
            }
        }

# Global pipeline instance
qq_automation_pipeline = QQIntelligentAutomationPipeline()

def start_intelligent_session(user_id: str = 'default') -> str:
    """Start intelligent automation session"""
    return qq_automation_pipeline.start_automation_session(user_id)

def process_file_with_intelligence(file_path: str, session_id: str, expected_type: str = None) -> Dict[str, Any]:
    """Process file with intelligent error recovery"""
    return qq_automation_pipeline.process_file_intelligently(file_path, session_id, expected_type)