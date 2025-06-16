
"""
TRAXOVO Nexus Data Integration System
Automatically discovers and integrates real data from multiple sources
"""

import os
import json
import sqlite3
import csv
from datetime import datetime, timedelta
import glob
import logging
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TRAXOVODataIntegrator:
    def __init__(self):
        self.data_sources = []
        self.processed_data = {}
        self.database_path = 'instance/watson.db'
        self.data_cache_dir = 'data_cache'
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.data_cache_dir, exist_ok=True)
        os.makedirs('instance', exist_ok=True)
        
    def discover_data_sources(self):
        """Automatically discover all data files in the project"""
        data_patterns = [
            '*.json', '*.csv', '*.xlsx', '*.xls', '*.xml', '*.tsv',
            '**/*.json', '**/*.csv', '**/*.xlsx', '**/*.xls', '**/*.xml'
        ]
        
        discovered_files = []
        for pattern in data_patterns:
            files = glob.glob(pattern, recursive=True)
            discovered_files.extend(files)
            
        # Filter out system files and focus on data files
        data_files = []
        for file in discovered_files:
            if not any(exclude in file.lower() for exclude in [
                'node_modules', '.git', '__pycache__', '.deployment_cache',
                'static/js', 'static/css', 'templates', '.config'
            ]):
                data_files.append(file)
                
        self.data_sources = data_files
        logger.info(f"Discovered {len(data_files)} potential data sources")
        return data_files
        
    def analyze_file_structure(self, file_path):
        """Analyze the structure of a data file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            file_size = os.path.getsize(file_path)
            
            analysis = {
                'file_path': file_path,
                'file_size': file_size,
                'file_type': file_ext,
                'records_count': 0,
                'columns': [],
                'sample_data': None,
                'data_types': {},
                'key_fields': []
            }
            
            if file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    analysis['records_count'] = len(data)
                    if data:
                        analysis['columns'] = list(data[0].keys()) if isinstance(data[0], dict) else []
                        analysis['sample_data'] = data[:3]
                elif isinstance(data, dict):
                    analysis['records_count'] = len(data.get('assets', data.get('data', data.get('records', []))))
                    if 'assets' in data:
                        analysis['columns'] = list(data['assets'][0].keys()) if data['assets'] else []
                        analysis['sample_data'] = data['assets'][:3]
                        analysis['key_fields'] = ['id', 'asset_id', 'device_id', 'serial_number']
                        
            elif file_ext == '.csv':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
                    reader = csv.DictReader(csvfile)
                    columns = reader.fieldnames if reader.fieldnames else []
                    sample_data = []
                    row_count = 0
                    for row in reader:
                        if row_count < 3:
                            sample_data.append(row)
                        row_count += 1
                        if row_count >= 1000:  # Limit analysis to 1000 rows
                            break
                    
                    analysis['records_count'] = row_count
                    analysis['columns'] = columns
                    analysis['sample_data'] = sample_data
                
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return None
            
    def process_asset_data(self, file_path, analysis):
        """Process asset/equipment data files"""
        try:
            if 'gauge' in file_path.lower() or 'asset' in file_path.lower():
                logger.info(f"Processing asset data from {file_path}")
                
                if analysis['file_type'] == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    assets = data if isinstance(data, list) else data.get('assets', [])
                    
                    processed_assets = []
                    for asset in assets:
                        processed_asset = {
                            'asset_id': asset.get('id', asset.get('asset_id', asset.get('deviceId', 'unknown'))),
                            'name': asset.get('name', asset.get('deviceName', 'Unknown Asset')),
                            'type': asset.get('type', asset.get('deviceType', 'Equipment')),
                            'status': asset.get('status', asset.get('state', 'active')),
                            'location': asset.get('location', asset.get('site', 'Unknown')),
                            'last_update': asset.get('lastUpdate', asset.get('timestamp', datetime.now().isoformat())),
                            'serial_number': asset.get('serialNumber', asset.get('serial', 'N/A')),
                            'model': asset.get('model', asset.get('deviceModel', 'N/A')),
                            'manufacturer': asset.get('manufacturer', asset.get('make', 'N/A')),
                            'raw_data': json.dumps(asset)
                        }
                        processed_assets.append(processed_asset)
                        
                    self.processed_data['assets'] = processed_assets
                    logger.info(f"Processed {len(processed_assets)} assets")
                    
                    # Cache the processed data
                    with open(f'{self.data_cache_dir}/assets.json', 'w') as f:
                        json.dump(processed_assets, f, indent=2)
                        
                    return processed_assets
                    
        except Exception as e:
            logger.error(f"Error processing asset data: {e}")
            return []
            
    def process_attendance_data(self, file_path, analysis):
        """Process attendance/personnel data"""
        try:
            if any(keyword in file_path.lower() for keyword in ['attendance', 'personnel', 'employee', 'worker']):
                logger.info(f"Processing attendance data from {file_path}")
                
                attendance_records = []
                
                # Process CSV files only for deployment optimization
                if analysis['file_type'] == '.csv':
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            record = {
                                'employee_id': row.get('employee_id', row.get('id', row.get('worker_id', 'unknown'))),
                                'name': row.get('name', row.get('employee_name', 'Unknown')),
                                'clock_in': row.get('clock_in', row.get('start_time', None)),
                                'clock_out': row.get('clock_out', row.get('end_time', None)),
                                'date': row.get('date', row.get('work_date', str(datetime.now().date()))),
                                'hours_worked': row.get('hours_worked', row.get('total_hours', 0)),
                                'location': row.get('location', row.get('site', 'Main Office')),
                                'department': row.get('department', 'Operations')
                            }
                            attendance_records.append(record)
                    
                self.processed_data['attendance'] = attendance_records
                logger.info(f"Processed {len(attendance_records)} attendance records")
                
                # Cache the data
                with open(f'{self.data_cache_dir}/attendance.json', 'w') as f:
                    json.dump(attendance_records, f, indent=2)
                    
                return attendance_records
                
        except Exception as e:
            logger.error(f"Error processing attendance data: {e}")
            return []
            
    def process_billing_data(self, file_path, analysis):
        """Process billing/financial data"""
        try:
            if any(keyword in file_path.lower() for keyword in ['billing', 'invoice', 'financial', 'cost', 'revenue']):
                logger.info(f"Processing billing data from {file_path}")
                
                billing_records = []
                
                # Process CSV files only for deployment optimization
                if analysis['file_type'] == '.csv':
                    with open(file_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            record = {
                                'invoice_id': row.get('invoice_id', row.get('id', f"INV-{len(billing_records)+1}")),
                                'asset_id': row.get('asset_id', row.get('equipment_id', 'unknown')),
                                'customer': row.get('customer', row.get('client', 'Unknown Client')),
                                'amount': float(row.get('amount', row.get('total', row.get('cost', 0)))),
                                'date': row.get('date', row.get('invoice_date', str(datetime.now().date()))),
                                'status': row.get('status', 'active'),
                                'description': row.get('description', row.get('service', 'Equipment Rental'))
                            }
                            billing_records.append(record)
                    
                self.processed_data['billing'] = billing_records
                logger.info(f"Processed {len(billing_records)} billing records")
                
                # Cache the data
                with open(f'{self.data_cache_dir}/billing.json', 'w') as f:
                    json.dump(billing_records, f, indent=2)
                    
                return billing_records
                
        except Exception as e:
            logger.error(f"Error processing billing data: {e}")
            return []
            
    def process_geofence_data(self, file_path, analysis):
        """Process geofence/location data"""
        try:
            if any(keyword in file_path.lower() for keyword in ['geofence', 'location', 'gps', 'coordinate', 'zone']):
                logger.info(f"Processing geofence data from {file_path}")
                
                if analysis['file_type'] == '.json':
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    locations = data if isinstance(data, list) else data.get('locations', data.get('zones', []))
                    
                    geofence_records = []
                    for location in locations:
                        record = {
                            'zone_id': location.get('id', location.get('zone_id', f"ZONE-{len(geofence_records)+1}")),
                            'name': location.get('name', location.get('zone_name', 'Unknown Zone')),
                            'latitude': location.get('latitude', location.get('lat', 0)),
                            'longitude': location.get('longitude', location.get('lng', location.get('lon', 0))),
                            'radius': location.get('radius', 100),
                            'type': location.get('type', 'work_zone'),
                            'status': location.get('status', 'active'),
                            'description': location.get('description', 'Work Zone')
                        }
                        geofence_records.append(record)
                        
                    self.processed_data['geofences'] = geofence_records
                    logger.info(f"Processed {len(geofence_records)} geofence records")
                    
                    # Cache the data
                    with open(f'{self.data_cache_dir}/geofences.json', 'w') as f:
                        json.dump(geofence_records, f, indent=2)
                        
                    return geofence_records
                    
        except Exception as e:
            logger.error(f"Error processing geofence data: {e}")
            return []
            
    def setup_database_tables(self):
        """Create database tables for real data"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Assets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT UNIQUE,
                    name TEXT,
                    type TEXT,
                    status TEXT,
                    location TEXT,
                    last_update TEXT,
                    serial_number TEXT,
                    model TEXT,
                    manufacturer TEXT,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT,
                    name TEXT,
                    clock_in TEXT,
                    clock_out TEXT,
                    date TEXT,
                    hours_worked REAL,
                    location TEXT,
                    department TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Billing table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS billing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT UNIQUE,
                    asset_id TEXT,
                    customer TEXT,
                    amount REAL,
                    date TEXT,
                    status TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Geofences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS geofences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id TEXT UNIQUE,
                    name TEXT,
                    latitude REAL,
                    longitude REAL,
                    radius REAL,
                    type TEXT,
                    status TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            
    def populate_database(self):
        """Populate database with processed data"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Insert assets
            if 'assets' in self.processed_data:
                for asset in self.processed_data['assets']:
                    cursor.execute('''
                        INSERT OR REPLACE INTO assets 
                        (asset_id, name, type, status, location, last_update, serial_number, model, manufacturer, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        asset['asset_id'], asset['name'], asset['type'], asset['status'],
                        asset['location'], asset['last_update'], asset['serial_number'],
                        asset['model'], asset['manufacturer'], asset['raw_data']
                    ))
                    
            # Insert attendance records
            if 'attendance' in self.processed_data:
                for record in self.processed_data['attendance']:
                    cursor.execute('''
                        INSERT INTO attendance 
                        (employee_id, name, clock_in, clock_out, date, hours_worked, location, department)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record['employee_id'], record['name'], record['clock_in'], record['clock_out'],
                        str(record['date']), record['hours_worked'], record['location'], record['department']
                    ))
                    
            # Insert billing records
            if 'billing' in self.processed_data:
                for record in self.processed_data['billing']:
                    cursor.execute('''
                        INSERT OR REPLACE INTO billing 
                        (invoice_id, asset_id, customer, amount, date, status, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record['invoice_id'], record['asset_id'], record['customer'], record['amount'],
                        str(record['date']), record['status'], record['description']
                    ))
                    
            # Insert geofence records
            if 'geofences' in self.processed_data:
                for record in self.processed_data['geofences']:
                    cursor.execute('''
                        INSERT OR REPLACE INTO geofences 
                        (zone_id, name, latitude, longitude, radius, type, status, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record['zone_id'], record['name'], record['latitude'], record['longitude'],
                        record['radius'], record['type'], record['status'], record['description']
                    ))
                    
            conn.commit()
            conn.close()
            logger.info("Database populated with real data")
            
        except Exception as e:
            logger.error(f"Error populating database: {e}")
            
    def generate_integration_report(self):
        """Generate a comprehensive integration report"""
        report = {
            'integration_timestamp': datetime.now().isoformat(),
            'total_files_processed': len(self.data_sources),
            'data_summary': {},
            'file_details': []
        }
        
        for data_type, records in self.processed_data.items():
            report['data_summary'][data_type] = {
                'record_count': len(records),
                'last_updated': datetime.now().isoformat()
            }
            
        # Save report
        with open(f'{self.data_cache_dir}/integration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return report
        
    def run_full_integration(self):
        """Run the complete data integration process"""
        logger.info("Starting TRAXOVO Nexus Data Integration")
        
        # Discover all data sources
        data_files = self.discover_data_sources()
        
        # Setup database
        self.setup_database_tables()
        
        # Process each data file
        for file_path in data_files:
            logger.info(f"Analyzing file: {file_path}")
            analysis = self.analyze_file_structure(file_path)
            
            if analysis:
                # Process based on content type
                self.process_asset_data(file_path, analysis)
                self.process_attendance_data(file_path, analysis)
                self.process_billing_data(file_path, analysis)
                self.process_geofence_data(file_path, analysis)
                
        # Populate database with processed data
        self.populate_database()
        
        # Generate integration report
        report = self.generate_integration_report()
        
        logger.info("Data integration completed successfully")
        logger.info(f"Integration Summary: {report['data_summary']}")
        
        return report

if __name__ == "__main__":
    integrator = TRAXOVODataIntegrator()
    report = integrator.run_full_integration()
    print(f"Integration completed. Report saved to data_cache/integration_report.json")
