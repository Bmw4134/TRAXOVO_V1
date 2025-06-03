"""
Dynamic Driver-to-Asset Tracking System
Automated logging of all driver changes throughout the year for fringe benefit reporting
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
import requests
from sqlalchemy import create_engine, text

driver_tracking_bp = Blueprint('driver_tracking', __name__)

class DriverAssetTrackingSystem:
    """Comprehensive driver-to-asset assignment tracking with automated logging"""
    
    def __init__(self):
        self.load_authentic_data()
        self.initialize_tracking_database()
        
    def load_authentic_data(self):
        """Load authentic driver and asset data from your systems"""
        self.current_assignments = self._load_current_driver_assignments()
        self.asset_fleet = self._load_asset_fleet_from_billing()
        self.driver_roster = self._load_driver_roster()
        self.assignment_history = self._load_assignment_history()
        
    def initialize_tracking_database(self):
        """Initialize the tracking database tables"""
        try:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                engine = create_engine(db_url)
                
                # Create driver assignment tracking table
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS driver_asset_assignments (
                    id SERIAL PRIMARY KEY,
                    driver_id VARCHAR(50) NOT NULL,
                    driver_name VARCHAR(100) NOT NULL,
                    asset_id VARCHAR(50) NOT NULL,
                    asset_name VARCHAR(100) NOT NULL,
                    assignment_date DATE NOT NULL,
                    end_date DATE,
                    assignment_type VARCHAR(20) NOT NULL, -- 'primary', 'temporary', 'backup'
                    hours_logged DECIMAL(8,2) DEFAULT 0.0,
                    mileage_logged DECIMAL(10,2) DEFAULT 0.0,
                    fuel_consumption DECIMAL(8,2) DEFAULT 0.0,
                    project_assignment VARCHAR(100),
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(50) DEFAULT 'manual', -- 'gauge_api', 'manual', 'timecard_import'
                    notes TEXT,
                    UNIQUE(driver_id, asset_id, assignment_date)
                );
                
                CREATE INDEX IF NOT EXISTS idx_driver_asset_date 
                ON driver_asset_assignments(driver_id, asset_id, assignment_date);
                
                CREATE INDEX IF NOT EXISTS idx_assignment_date 
                ON driver_asset_assignments(assignment_date);
                """
                
                with engine.connect() as conn:
                    conn.execute(text(create_table_sql))
                    conn.commit()
                    
        except Exception as e:
            print(f"Error initializing tracking database: {e}")
            
    def _load_current_driver_assignments(self):
        """Load current driver assignments from Gauge API and timecard data"""
        assignments = []
        
        try:
            # Get from Gauge API first
            api_url = os.environ.get('GAUGE_API_URL')
            api_key = os.environ.get('GAUGE_API_KEY')
            
            if api_url and api_key:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                
                # Get current asset assignments
                assignments_endpoint = f"{api_url}/assignments/current"
                response = requests.get(assignments_endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        for assignment in data:
                            assignments.append({
                                'driver_id': assignment.get('driver_id'),
                                'driver_name': assignment.get('driver_name'),
                                'asset_id': assignment.get('asset_id'),
                                'asset_name': assignment.get('asset_name'),
                                'assignment_date': assignment.get('start_date', datetime.now().strftime('%Y-%m-%d')),
                                'assignment_type': 'primary',
                                'project': assignment.get('project'),
                                'status': 'active',
                                'source': 'gauge_api'
                            })
                            
        except Exception as e:
            print(f"Error loading from Gauge API: {e}")
            
        # Supplement with timecard data analysis
        timecard_assignments = self._extract_assignments_from_timecards()
        assignments.extend(timecard_assignments)
        
        return assignments
        
    def _extract_assignments_from_timecards(self):
        """Extract driver-asset assignments from timecard files"""
        assignments = []
        
        # Check for timecard files
        timecard_sources = ['uploads', 'attendance_data', '.']
        
        for source_dir in timecard_sources:
            if os.path.exists(source_dir):
                for file in os.listdir(source_dir):
                    if file.endswith(('.xlsx', '.xls')) and any(keyword in file.lower() for keyword in ['timecard', 'ground', 'works', 'time']):
                        try:
                            file_path = os.path.join(source_dir, file)
                            df = pd.read_excel(file_path)
                            
                            # Look for driver and equipment columns
                            driver_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['driver', 'operator', 'employee', 'name'])]
                            equipment_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['equipment', 'asset', 'unit', 'machine'])]
                            date_cols = [col for col in df.columns if any(keyword in str(col).lower() for keyword in ['date', 'day'])]
                            
                            if driver_cols and equipment_cols:
                                for _, row in df.iterrows():
                                    driver_name = str(row[driver_cols[0]]) if pd.notna(row[driver_cols[0]]) else None
                                    equipment_name = str(row[equipment_cols[0]]) if pd.notna(row[equipment_cols[0]]) else None
                                    work_date = row[date_cols[0]] if date_cols and pd.notna(row[date_cols[0]]) else datetime.now()
                                    
                                    if driver_name and equipment_name and driver_name.strip() and equipment_name.strip():
                                        assignments.append({
                                            'driver_id': self._generate_driver_id(driver_name),
                                            'driver_name': driver_name.strip(),
                                            'asset_id': self._generate_asset_id(equipment_name),
                                            'asset_name': equipment_name.strip(),
                                            'assignment_date': work_date.strftime('%Y-%m-%d') if hasattr(work_date, 'strftime') else str(work_date)[:10],
                                            'assignment_type': 'primary',
                                            'project': 'From Timecard',
                                            'status': 'active',
                                            'source': 'timecard_import'
                                        })
                                        
                        except Exception as e:
                            print(f"Error processing timecard file {file}: {e}")
                            
        return assignments
        
    def _generate_driver_id(self, driver_name):
        """Generate consistent driver ID from name"""
        # Simple ID generation - in production, this would map to employee IDs
        name_parts = driver_name.strip().split()
        if len(name_parts) >= 2:
            return f"DRV-{name_parts[0][:2]}{name_parts[-1][:2]}".upper()
        else:
            return f"DRV-{name_parts[0][:4]}".upper()
            
    def _generate_asset_id(self, asset_name):
        """Generate consistent asset ID from name"""
        # Clean up asset name and create ID
        clean_name = asset_name.strip().upper()
        return f"AST-{clean_name[:6]}"
        
    def _load_asset_fleet_from_billing(self):
        """Load asset fleet from billing files"""
        assets = []
        
        try:
            billing_files = [
                "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm",
                "RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm"
            ]
            
            for file_name in billing_files:
                if os.path.exists(file_name):
                    try:
                        excel_file = pd.ExcelFile(file_name)
                        
                        for sheet_name in excel_file.sheet_names:
                            df = pd.read_excel(file_name, sheet_name=sheet_name)
                            
                            # Process equipment data
                            for _, row in df.iterrows():
                                equipment_cols = [col for col in df.columns if any(indicator in str(col).lower() for indicator in ['equipment', 'asset', 'unit', 'machine'])]
                                
                                if equipment_cols:
                                    asset_name = str(row[equipment_cols[0]]) if pd.notna(row[equipment_cols[0]]) else None
                                    if asset_name and asset_name.strip():
                                        assets.append({
                                            'asset_id': self._generate_asset_id(asset_name),
                                            'asset_name': asset_name.strip(),
                                            'asset_type': self._classify_asset_type(asset_name),
                                            'billable': True,
                                            'source_file': file_name
                                        })
                                        
                    except Exception as e:
                        print(f"Error reading asset data from {file_name}: {e}")
                        
        except Exception as e:
            print(f"Error loading asset fleet: {e}")
            
        # Remove duplicates
        unique_assets = []
        seen_ids = set()
        for asset in assets:
            if asset['asset_id'] not in seen_ids:
                unique_assets.append(asset)
                seen_ids.add(asset['asset_id'])
                
        return unique_assets
        
    def _classify_asset_type(self, asset_name):
        """Classify asset type for fringe benefit categorization"""
        name_lower = asset_name.lower()
        
        if any(keyword in name_lower for keyword in ['truck', 'pickup', 'vehicle']):
            return 'Vehicle'
        elif any(keyword in name_lower for keyword in ['excavator', 'digger']):
            return 'Heavy Equipment'
        elif any(keyword in name_lower for keyword in ['dozer', 'bulldozer']):
            return 'Heavy Equipment'
        elif any(keyword in name_lower for keyword in ['trailer', 'haul']):
            return 'Trailer'
        else:
            return 'Equipment'
            
    def _load_driver_roster(self):
        """Load driver roster from various sources"""
        drivers = []
        
        # Extract unique drivers from current assignments
        driver_names = set()
        for assignment in self.current_assignments:
            if assignment['driver_name']:
                driver_names.add(assignment['driver_name'])
                
        for driver_name in driver_names:
            drivers.append({
                'driver_id': self._generate_driver_id(driver_name),
                'driver_name': driver_name,
                'status': 'active',
                'hire_date': None,  # Would come from HR system
                'license_type': 'CDL',  # Default assumption
                'fringe_eligible': True
            })
            
        return drivers
        
    def _load_assignment_history(self):
        """Load historical assignment data from database"""
        history = []
        
        try:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                engine = create_engine(db_url)
                
                query = """
                SELECT * FROM driver_asset_assignments 
                ORDER BY assignment_date DESC, created_timestamp DESC
                LIMIT 1000
                """
                
                with engine.connect() as conn:
                    result = conn.execute(text(query))
                    for row in result:
                        history.append(dict(row._mapping))
                        
        except Exception as e:
            print(f"Error loading assignment history: {e}")
            
        return history
        
    def log_driver_assignment(self, driver_id, driver_name, asset_id, asset_name, assignment_date, assignment_type='primary', project=None, hours=0.0, mileage=0.0, source='manual'):
        """Log a new driver assignment to the tracking database"""
        try:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                engine = create_engine(db_url)
                
                # End any existing assignments for this driver on this date
                end_existing_sql = """
                UPDATE driver_asset_assignments 
                SET end_date = %s, updated_timestamp = CURRENT_TIMESTAMP
                WHERE driver_id = %s AND assignment_date = %s AND end_date IS NULL
                """
                
                # Insert new assignment
                insert_sql = """
                INSERT INTO driver_asset_assignments 
                (driver_id, driver_name, asset_id, asset_name, assignment_date, assignment_type, 
                 hours_logged, mileage_logged, project_assignment, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (driver_id, asset_id, assignment_date) 
                DO UPDATE SET 
                    hours_logged = EXCLUDED.hours_logged,
                    mileage_logged = EXCLUDED.mileage_logged,
                    updated_timestamp = CURRENT_TIMESTAMP
                """
                
                with engine.connect() as conn:
                    # End existing assignments
                    conn.execute(text(end_existing_sql), (assignment_date, driver_id, assignment_date))
                    
                    # Insert new assignment
                    conn.execute(text(insert_sql), (
                        driver_id, driver_name, asset_id, asset_name, assignment_date,
                        assignment_type, hours, mileage, project, source
                    ))
                    
                    conn.commit()
                    
                return {'success': True, 'message': 'Assignment logged successfully'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def bulk_import_assignments(self, file_path):
        """Bulk import driver assignments from uploaded file"""
        try:
            df = pd.read_excel(file_path)
            imported_count = 0
            
            for _, row in df.iterrows():
                # Map columns to our fields
                driver_name = str(row.get('Driver Name', row.get('Operator', ''))) if pd.notna(row.get('Driver Name', row.get('Operator', ''))) else None
                asset_name = str(row.get('Equipment', row.get('Asset', ''))) if pd.notna(row.get('Equipment', row.get('Asset', ''))) else None
                work_date = row.get('Date', datetime.now())
                hours = float(row.get('Hours', 0)) if pd.notna(row.get('Hours', 0)) else 0.0
                
                if driver_name and asset_name:
                    result = self.log_driver_assignment(
                        driver_id=self._generate_driver_id(driver_name),
                        driver_name=driver_name,
                        asset_id=self._generate_asset_id(asset_name),
                        asset_name=asset_name,
                        assignment_date=work_date.strftime('%Y-%m-%d') if hasattr(work_date, 'strftime') else str(work_date)[:10],
                        hours=hours,
                        source='bulk_import'
                    )
                    
                    if result['success']:
                        imported_count += 1
                        
            return {'success': True, 'imported_count': imported_count}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def generate_fringe_benefit_report(self, start_date, end_date):
        """Generate fringe benefit report for specified date range"""
        try:
            db_url = os.environ.get('DATABASE_URL')
            if db_url:
                engine = create_engine(db_url)
                
                query = """
                SELECT 
                    driver_id,
                    driver_name,
                    asset_id,
                    asset_name,
                    assignment_date,
                    assignment_type,
                    hours_logged,
                    mileage_logged,
                    project_assignment
                FROM driver_asset_assignments 
                WHERE assignment_date BETWEEN %s AND %s
                ORDER BY driver_name, assignment_date
                """
                
                with engine.connect() as conn:
                    result = conn.execute(text(query), (start_date, end_date))
                    data = [dict(row._mapping) for row in result]
                    
                # Group by driver for summary
                driver_summary = {}
                for record in data:
                    driver = record['driver_name']
                    if driver not in driver_summary:
                        driver_summary[driver] = {
                            'total_hours': 0,
                            'total_mileage': 0,
                            'vehicles_used': set(),
                            'assignment_days': 0
                        }
                    
                    driver_summary[driver]['total_hours'] += record['hours_logged'] or 0
                    driver_summary[driver]['total_mileage'] += record['mileage_logged'] or 0
                    driver_summary[driver]['vehicles_used'].add(record['asset_name'])
                    driver_summary[driver]['assignment_days'] += 1
                    
                # Convert sets to lists for JSON serialization
                for driver in driver_summary:
                    driver_summary[driver]['vehicles_used'] = list(driver_summary[driver]['vehicles_used'])
                    
                return {
                    'success': True,
                    'report_data': data,
                    'driver_summary': driver_summary,
                    'period': f"{start_date} to {end_date}",
                    'total_records': len(data)
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def get_tracking_dashboard_data(self):
        """Get comprehensive tracking dashboard data"""
        return {
            'current_assignments': self.current_assignments,
            'asset_fleet': self.asset_fleet,
            'driver_roster': self.driver_roster,
            'assignment_history': self.assignment_history[:50],  # Recent history
            'summary_metrics': {
                'total_drivers': len(self.driver_roster),
                'total_assets': len(self.asset_fleet),
                'active_assignments': len([a for a in self.current_assignments if a['status'] == 'active']),
                'historical_records': len(self.assignment_history)
            }
        }

# Global instance
tracking_system = DriverAssetTrackingSystem()

@driver_tracking_bp.route('/driver-asset-tracking')
def driver_asset_tracking_dashboard():
    """Driver Asset Tracking Dashboard"""
    dashboard_data = tracking_system.get_tracking_dashboard_data()
    return render_template('driver_asset_tracking.html', data=dashboard_data)

@driver_tracking_bp.route('/api/log-assignment', methods=['POST'])
def api_log_assignment():
    """API endpoint to log driver assignments"""
    try:
        request_data = request.get_json()
        
        result = tracking_system.log_driver_assignment(
            driver_id=request_data.get('driver_id'),
            driver_name=request_data.get('driver_name'),
            asset_id=request_data.get('asset_id'),
            asset_name=request_data.get('asset_name'),
            assignment_date=request_data.get('assignment_date'),
            assignment_type=request_data.get('assignment_type', 'primary'),
            project=request_data.get('project'),
            hours=float(request_data.get('hours', 0)),
            mileage=float(request_data.get('mileage', 0))
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@driver_tracking_bp.route('/api/fringe-benefit-report', methods=['POST'])
def api_fringe_benefit_report():
    """API endpoint to generate fringe benefit reports"""
    try:
        request_data = request.get_json()
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        
        result = tracking_system.generate_fringe_benefit_report(start_date, end_date)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_tracking_system():
    """Get the tracking system instance"""
    return tracking_system