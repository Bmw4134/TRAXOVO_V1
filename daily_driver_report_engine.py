#!/usr/bin/env python3
"""
TRAXOVO Daily Driver Report Engine
Comprehensive driver attendance, performance, and fleet utilization system
Uses authentic data with advanced deduplication and tech stack integration
"""

import pandas as pd
import numpy as np
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailyDriverReportEngine:
    def __init__(self):
        self.database_file = 'traxovo_driver_reports.db'
        self.data_sources = {
            'activity_detail': 'attached_assets/ActivityDetail (4)_1749454854416.csv',
            'daily_usage': 'attached_assets/DailyUsage_1749454857635.csv',
            'driving_history': 'attached_assets/DrivingHistory (2)_1749454860929.csv',
            'driver_scorecard': 'attached_assets/DriverScorecard YTD_1749454628117.pdf',
            'late_start_report': 'attached_assets/DAILY LATE START-EARLY END & NOJ REPORT_05.14.2025_1749451649446.xlsx',
            'speeding_report': 'attached_assets/SpeedingReport (1)_1749454624967.csv',
            'assets_time_onsite': 'attached_assets/AssetsTimeOnSite (2)_1749454865159.csv'
        }
        self.processed_data = {}
        self.dedupe_cache = set()
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize SQLite database for driver reports with deduplication"""
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Create tables with proper indexing for deduplication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_driver_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hash TEXT UNIQUE NOT NULL,
                driver_id TEXT NOT NULL,
                report_date DATE NOT NULL,
                vehicle_id TEXT,
                hours_worked REAL DEFAULT 0,
                miles_driven INTEGER DEFAULT 0,
                fuel_consumed REAL DEFAULT 0,
                equipment_used TEXT,
                start_time TEXT,
                end_time TEXT,
                locations_visited TEXT,
                safety_incidents INTEGER DEFAULT 0,
                speed_violations INTEGER DEFAULT 0,
                utilization_rate REAL DEFAULT 0,
                performance_score REAL DEFAULT 0,
                attendance_status TEXT DEFAULT 'present',
                late_start_minutes INTEGER DEFAULT 0,
                early_end_minutes INTEGER DEFAULT 0,
                break_time_minutes INTEGER DEFAULT 0,
                overtime_hours REAL DEFAULT 0,
                project_assignments TEXT,
                notes TEXT,
                processed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source_file TEXT,
                data_quality_score REAL DEFAULT 1.0,
                UNIQUE(driver_id, report_date, vehicle_id, data_hash)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS driver_attendance_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hash TEXT UNIQUE NOT NULL,
                driver_id TEXT NOT NULL,
                attendance_date DATE NOT NULL,
                clock_in_time TEXT,
                clock_out_time TEXT,
                total_hours REAL,
                scheduled_hours REAL,
                overtime_hours REAL,
                break_hours REAL,
                location TEXT,
                equipment_assignments TEXT,
                supervisor TEXT,
                attendance_type TEXT DEFAULT 'regular',
                status TEXT DEFAULT 'present',
                processed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(driver_id, attendance_date, data_hash)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment_utilization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hash TEXT UNIQUE NOT NULL,
                equipment_id TEXT NOT NULL,
                driver_id TEXT,
                utilization_date DATE NOT NULL,
                hours_operated REAL DEFAULT 0,
                fuel_consumed REAL DEFAULT 0,
                maintenance_alerts INTEGER DEFAULT 0,
                efficiency_rating REAL DEFAULT 0,
                project_code TEXT,
                location TEXT,
                processed_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(equipment_id, utilization_date, driver_id, data_hash)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_driver_reports_date ON daily_driver_reports(report_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_driver_reports_driver ON daily_driver_reports(driver_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON driver_attendance_matrix(attendance_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_equipment_date ON equipment_utilization(utilization_date)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized with deduplication support")
    
    def generate_data_hash(self, data_dict: Dict) -> str:
        """Generate hash for deduplication using tech stack"""
        # Remove timestamp fields for consistent hashing
        clean_data = {k: v for k, v in data_dict.items() 
                     if 'timestamp' not in k.lower() and 'processed' not in k.lower()}
        
        # Sort keys for consistent hashing
        sorted_data = json.dumps(clean_data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def safe_csv_read(self, file_path: str) -> pd.DataFrame:
        """Safely read CSV with multiple encoding attempts"""
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return pd.DataFrame()
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, low_memory=False, 
                               on_bad_lines='skip', sep=None, engine='python')
                if not df.empty:
                    logger.info(f"Successfully read {file_path} with {encoding} encoding: {len(df)} records")
                    return df
            except Exception as e:
                continue
        
        logger.error(f"Failed to read {file_path} with any encoding")
        return pd.DataFrame()
    
    def process_activity_detail(self) -> Dict[str, Any]:
        """Process ActivityDetail for driver attendance and performance"""
        df = self.safe_csv_read(self.data_sources['activity_detail'])
        if df.empty:
            return {'status': 'no_data', 'records_processed': 0}
        
        processed_records = 0
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        # Process activity records with deduplication
        for index, row in df.iterrows():
            try:
                # Extract driver and activity information
                activity_data = {
                    'driver_id': str(row.get('Driver', row.get('Operator', f'DRIVER_{index}')))[:20],
                    'report_date': datetime.now().date(),
                    'vehicle_id': str(row.get('Vehicle', row.get('Equipment', '')))[:20],
                    'activity_type': str(row.get('Activity', row.get('Task', 'General Work'))),
                    'location': str(row.get('Location', row.get('Site', 'Unknown')))[:50],
                    'hours_worked': float(row.get('Hours', row.get('Duration', 0)) or 0),
                    'source_file': 'ActivityDetail'
                }
                
                # Generate hash for deduplication
                data_hash = self.generate_data_hash(activity_data)
                
                if data_hash not in self.dedupe_cache:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO daily_driver_reports 
                            (data_hash, driver_id, report_date, vehicle_id, hours_worked, 
                             locations_visited, source_file, equipment_used)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (data_hash, activity_data['driver_id'], activity_data['report_date'],
                              activity_data['vehicle_id'], activity_data['hours_worked'],
                              activity_data['location'], activity_data['source_file'],
                              activity_data['activity_type']))
                        
                        self.dedupe_cache.add(data_hash)
                        processed_records += 1
                    except sqlite3.IntegrityError:
                        # Record already exists, skip
                        pass
                        
            except Exception as e:
                logger.warning(f"Error processing activity record {index}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return {
            'status': 'success',
            'records_processed': processed_records,
            'total_records': len(df),
            'deduplication_ratio': f"{(len(df) - processed_records) / len(df) * 100:.1f}%" if len(df) > 0 else "0%"
        }
    
    def process_daily_usage(self) -> Dict[str, Any]:
        """Process DailyUsage for equipment utilization and driver performance"""
        df = self.safe_csv_read(self.data_sources['daily_usage'])
        if df.empty:
            return {'status': 'no_data', 'records_processed': 0}
        
        processed_records = 0
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        for index, row in df.iterrows():
            try:
                # Extract usage data
                usage_data = {
                    'equipment_id': str(row.get('Equipment', row.get('Asset', f'EQUIP_{index}')))[:20],
                    'driver_id': str(row.get('Operator', row.get('Driver', 'UNKNOWN')))[:20],
                    'utilization_date': datetime.now().date(),
                    'hours_operated': float(row.get('Hours', row.get('Runtime', 0)) or 0),
                    'fuel_consumed': float(row.get('Fuel', row.get('FuelUsed', 0)) or 0),
                    'efficiency_rating': min(float(row.get('Efficiency', 85) or 85), 100) / 100,
                    'location': str(row.get('Location', row.get('Site', 'Unknown')))[:50],
                    'project_code': str(row.get('Project', row.get('Job', '')))[:20]
                }
                
                data_hash = self.generate_data_hash(usage_data)
                
                if data_hash not in self.dedupe_cache:
                    try:
                        cursor.execute('''
                            INSERT OR IGNORE INTO equipment_utilization 
                            (data_hash, equipment_id, driver_id, utilization_date, 
                             hours_operated, fuel_consumed, efficiency_rating, location, project_code)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (data_hash, usage_data['equipment_id'], usage_data['driver_id'],
                              usage_data['utilization_date'], usage_data['hours_operated'],
                              usage_data['fuel_consumed'], usage_data['efficiency_rating'],
                              usage_data['location'], usage_data['project_code']))
                        
                        self.dedupe_cache.add(data_hash)
                        processed_records += 1
                    except sqlite3.IntegrityError:
                        pass
                        
            except Exception as e:
                logger.warning(f"Error processing usage record {index}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return {
            'status': 'success',
            'records_processed': processed_records,
            'total_records': len(df),
            'deduplication_ratio': f"{(len(df) - processed_records) / len(df) * 100:.1f}%" if len(df) > 0 else "0%"
        }
    
    def process_driving_history(self) -> Dict[str, Any]:
        """Process DrivingHistory for driver performance metrics"""
        df = self.safe_csv_read(self.data_sources['driving_history'])
        if df.empty:
            return {'status': 'no_data', 'records_processed': 0}
        
        processed_records = 0
        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        
        for index, row in df.iterrows():
            try:
                # Extract driving performance data
                driving_data = {
                    'driver_id': str(row.get('Driver', row.get('DriverID', f'DRIVER_{index}')))[:20],
                    'report_date': datetime.now().date(),
                    'miles_driven': int(row.get('Miles', row.get('Distance', 0)) or 0),
                    'speed_violations': int(row.get('SpeedViolations', row.get('Violations', 0)) or 0),
                    'safety_incidents': int(row.get('Incidents', row.get('SafetyEvents', 0)) or 0),
                    'fuel_efficiency': float(row.get('MPG', row.get('FuelEfficiency', 0)) or 0),
                    'performance_score': min(float(row.get('Score', 85) or 85), 100)
                }
                
                data_hash = self.generate_data_hash(driving_data)
                
                if data_hash not in self.dedupe_cache:
                    try:
                        cursor.execute('''
                            UPDATE daily_driver_reports 
                            SET miles_driven = ?, speed_violations = ?, safety_incidents = ?, 
                                performance_score = ?, fuel_consumed = ?
                            WHERE driver_id = ? AND report_date = ? AND data_hash != ?
                        ''', (driving_data['miles_driven'], driving_data['speed_violations'],
                              driving_data['safety_incidents'], driving_data['performance_score'],
                              driving_data['fuel_efficiency'], driving_data['driver_id'],
                              driving_data['report_date'], data_hash))
                        
                        if cursor.rowcount == 0:
                            # Insert new record if no existing record to update
                            cursor.execute('''
                                INSERT OR IGNORE INTO daily_driver_reports 
                                (data_hash, driver_id, report_date, miles_driven, speed_violations, 
                                 safety_incidents, performance_score, fuel_consumed, source_file)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (data_hash, driving_data['driver_id'], driving_data['report_date'],
                                  driving_data['miles_driven'], driving_data['speed_violations'],
                                  driving_data['safety_incidents'], driving_data['performance_score'],
                                  driving_data['fuel_efficiency'], 'DrivingHistory'))
                        
                        self.dedupe_cache.add(data_hash)
                        processed_records += 1
                    except sqlite3.IntegrityError:
                        pass
                        
            except Exception as e:
                logger.warning(f"Error processing driving record {index}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return {
            'status': 'success',
            'records_processed': processed_records,
            'total_records': len(df),
            'deduplication_ratio': f"{(len(df) - processed_records) / len(df) * 100:.1f}%" if len(df) > 0 else "0%"
        }
    
    def generate_daily_driver_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive daily driver report with deduplication"""
        if not target_date:
            target_date = datetime.now().date()
        else:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Process all data sources
        activity_result = self.process_activity_detail()
        usage_result = self.process_daily_usage()
        driving_result = self.process_driving_history()
        
        # Generate consolidated report
        conn = sqlite3.connect(self.database_file)
        
        # Get driver performance summary
        driver_summary = pd.read_sql_query('''
            SELECT 
                driver_id,
                COUNT(*) as total_reports,
                SUM(hours_worked) as total_hours,
                SUM(miles_driven) as total_miles,
                AVG(performance_score) as avg_performance,
                SUM(safety_incidents) as total_incidents,
                SUM(speed_violations) as total_violations,
                MAX(processed_timestamp) as last_updated
            FROM daily_driver_reports 
            WHERE report_date = ?
            GROUP BY driver_id
            ORDER BY total_hours DESC
        ''', conn, params=[target_date])
        
        # Get equipment utilization summary
        equipment_summary = pd.read_sql_query('''
            SELECT 
                equipment_id,
                driver_id,
                SUM(hours_operated) as total_hours,
                SUM(fuel_consumed) as total_fuel,
                AVG(efficiency_rating) as avg_efficiency,
                COUNT(*) as utilization_records
            FROM equipment_utilization 
            WHERE utilization_date = ?
            GROUP BY equipment_id, driver_id
            ORDER BY total_hours DESC
        ''', conn, params=[target_date])
        
        conn.close()
        
        # Calculate key metrics
        total_drivers = len(driver_summary)
        total_hours = driver_summary['total_hours'].sum() if not driver_summary.empty else 0
        total_miles = driver_summary['total_miles'].sum() if not driver_summary.empty else 0
        avg_performance = driver_summary['avg_performance'].mean() if not driver_summary.empty else 0
        total_incidents = driver_summary['total_incidents'].sum() if not driver_summary.empty else 0
        
        return {
            'report_date': str(target_date),
            'generation_timestamp': datetime.now().isoformat(),
            'data_processing_summary': {
                'activity_detail': activity_result,
                'daily_usage': usage_result,
                'driving_history': driving_result
            },
            'driver_performance_summary': {
                'total_active_drivers': total_drivers,
                'total_hours_worked': round(total_hours, 2),
                'total_miles_driven': int(total_miles),
                'average_performance_score': round(avg_performance, 1),
                'total_safety_incidents': int(total_incidents),
                'drivers': driver_summary.to_dict('records') if not driver_summary.empty else []
            },
            'equipment_utilization_summary': {
                'total_equipment_used': len(equipment_summary),
                'equipment_details': equipment_summary.to_dict('records') if not equipment_summary.empty else []
            },
            'data_quality_metrics': {
                'total_records_processed': (activity_result.get('records_processed', 0) + 
                                          usage_result.get('records_processed', 0) + 
                                          driving_result.get('records_processed', 0)),
                'deduplication_cache_size': len(self.dedupe_cache),
                'data_sources_processed': len([r for r in [activity_result, usage_result, driving_result] 
                                             if r.get('status') == 'success'])
            }
        }
    
    def get_attendance_matrix(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate attendance matrix for date range"""
        conn = sqlite3.connect(self.database_file)
        
        attendance_data = pd.read_sql_query('''
            SELECT 
                driver_id,
                report_date,
                SUM(hours_worked) as daily_hours,
                COUNT(*) as activity_count,
                MAX(performance_score) as daily_performance,
                SUM(CASE WHEN safety_incidents > 0 THEN 1 ELSE 0 END) as incident_flag
            FROM daily_driver_reports 
            WHERE report_date BETWEEN ? AND ?
            GROUP BY driver_id, report_date
            ORDER BY driver_id, report_date
        ''', conn, params=[start_date, end_date])
        
        conn.close()
        
        # Create matrix format
        if not attendance_data.empty:
            matrix = attendance_data.pivot(index='driver_id', columns='report_date', values='daily_hours')
            matrix = matrix.fillna(0)
            
            return {
                'attendance_matrix': matrix.to_dict(),
                'summary': {
                    'total_drivers': len(matrix),
                    'date_range': f"{start_date} to {end_date}",
                    'average_daily_hours': attendance_data['daily_hours'].mean(),
                    'total_work_days': len(matrix.columns),
                    'attendance_rate': f"{(matrix > 0).sum().sum() / (len(matrix) * len(matrix.columns)) * 100:.1f}%"
                }
            }
        
        return {'attendance_matrix': {}, 'summary': {'total_drivers': 0}}

def main():
    """Run daily driver report generation"""
    engine = DailyDriverReportEngine()
    
    print("TRAXOVO Daily Driver Report Engine")
    print("=" * 50)
    print("Processing authentic fleet data with deduplication...")
    
    # Generate today's report
    report = engine.generate_daily_driver_report()
    
    print(f"\nDaily Driver Report for {report['report_date']}")
    print("-" * 40)
    
    # Display summary
    summary = report['driver_performance_summary']
    print(f"Active Drivers: {summary['total_active_drivers']}")
    print(f"Total Hours: {summary['total_hours_worked']}")
    print(f"Total Miles: {summary['total_miles_driven']:,}")
    print(f"Avg Performance: {summary['average_performance_score']}/100")
    print(f"Safety Incidents: {summary['total_safety_incidents']}")
    
    # Display data quality
    quality = report['data_quality_metrics']
    print(f"\nData Quality Metrics:")
    print(f"Records Processed: {quality['total_records_processed']:,}")
    print(f"Deduplication Cache: {quality['deduplication_cache_size']:,} hashes")
    print(f"Data Sources: {quality['data_sources_processed']}/3 processed")
    
    # Save full report
    with open('daily_driver_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nFull report saved to: daily_driver_report.json")
    
    return report

if __name__ == "__main__":
    main()