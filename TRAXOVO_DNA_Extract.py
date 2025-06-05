#!/usr/bin/env python3
"""
TRAXOVO DNA Extractor
Captures all working technology components for integration into any stack
"""

import os
import json
import shutil
from datetime import datetime

class TRAXOVODNAExtractor:
    """Extract complete working technology DNA for remix integration"""
    
    def __init__(self):
        self.extract_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.dna_package = {
            'core_files': [],
            'database_schema': [],
            'api_integrations': [],
            'automation_workflows': [],
            'environment_config': {},
            'deployment_config': {},
            'integration_points': []
        }
    
    def extract_core_automation_engine(self):
        """Extract the real automation engine that processes authentic data"""
        automation_dna = {
            'file': 'automation_engine.py',
            'capabilities': [
                'processes_authentic_attendance_data_from_uploads',
                'generates_real_reports_with_timestamps',
                'executes_background_tasks_with_scheduling',
                'integrates_with_gauge_api_for_live_tracking',
                'handles_excel_csv_file_processing',
                'maps_fort_worth_gps_coordinates_to_zones'
            ],
            'critical_methods': {
                'execute_manual_task': 'processes real uploaded files and returns execution results',
                'create_attendance_automation': 'sets up scheduled processing of timecard files',
                'get_automation_status': 'returns actual file counts and processing status',
                'fetch_gauge_api_data': 'connects to live asset tracking API',
                'determine_fort_worth_zone': 'maps GPS coordinates to job zones'
            },
            'data_flow': {
                'input': 'uploads/ directory with Excel/CSV timecard files',
                'processing': 'pandas dataframe transformation with real employee data',
                'output': 'reports_processed/ directory with timestamped CSV reports'
            }
        }
        self.dna_package['automation_workflows'].append(automation_dna)
        
    def extract_database_schema(self):
        """Extract database schema for authentic data storage"""
        schema_dna = {
            'file': 'models.py',
            'tables': {
                'automation_tasks': 'stores real task execution history',
                'asset_locations': 'stores authentic GPS coordinates from GAUGE API',
                'attendance_records': 'stores processed timecard data',
                'users': 'authentication and session management'
            },
            'relationships': {
                'tasks_to_executions': 'one_to_many tracking of automation runs',
                'assets_to_locations': 'historical location tracking',
                'users_to_sessions': 'secure authentication state'
            },
            'indexes': [
                'asset_locations.timestamp for time-series queries',
                'attendance_records.date for date range filtering',
                'automation_tasks.status for active task monitoring'
            ]
        }
        self.dna_package['database_schema'].append(schema_dna)
        
    def extract_api_integrations(self):
        """Extract GAUGE API integration for live asset tracking"""
        api_dna = {
            'file': 'authentic_fleet_data_processor.py',
            'integrations': {
                'gauge_api': {
                    'purpose': 'live_asset_location_tracking',
                    'authentication': 'bearer_token_in_GAUGE_API_KEY',
                    'endpoints': [
                        'GET /assets/locations - fetch current asset positions',
                        'GET /assets/history - retrieve location history'
                    ],
                    'data_processing': 'maps_gps_to_fort_worth_zones',
                    'update_frequency': 'every_5_minutes_via_scheduler'
                }
            },
            'environment_variables': {
                'GAUGE_API_KEY': 'required_for_live_tracking',
                'GAUGE_API_URL': 'api_endpoint_base_url'
            }
        }
        self.dna_package['api_integrations'].append(api_dna)
        
    def extract_file_processing_workflow(self):
        """Extract authentic file processing capabilities"""
        file_processing_dna = {
            'supported_formats': ['xlsx', 'csv'],
            'input_directory': 'uploads/',
            'output_directory': 'reports_processed/',
            'processing_pipeline': [
                'scan_uploads_directory_for_new_files',
                'read_excel_or_csv_with_pandas',
                'validate_timecard_data_columns',
                'transform_employee_hours_data',
                'calculate_total_hours_and_overtime',
                'generate_timestamped_report_file',
                'move_processed_file_to_archive'
            ],
            'data_validation': {
                'required_columns': ['employee_id', 'date', 'time_in', 'time_out'],
                'data_types': 'datetime for timestamps, decimal for hours',
                'integrity_checks': 'validate_employee_ids_against_database'
            }
        }
        self.dna_package['automation_workflows'].append(file_processing_dna)
        
    def extract_deployment_configuration(self):
        """Extract production deployment requirements"""
        deployment_dna = {
            'runtime': 'python3.11',
            'web_framework': 'flask_with_gunicorn',
            'database': 'postgresql_with_sqlalchemy',
            'build_command': 'pip install -r requirements.txt',
            'run_command': 'gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app',
            'required_dependencies': [
                'Flask==3.0.0',
                'Flask-SQLAlchemy==3.1.1',
                'gunicorn==21.2.0',
                'psycopg2-binary==2.9.9',
                'pandas==2.1.4',
                'requests==2.31.0',
                'openpyxl==3.1.2',
                'schedule==1.2.0'
            ],
            'environment_setup': {
                'DATABASE_URL': 'postgresql connection string',
                'SESSION_SECRET': 'secure session key',
                'GAUGE_API_KEY': 'for live asset tracking',
                'GAUGE_API_URL': 'api endpoint'
            },
            'directory_structure': {
                'uploads/': 'create on startup for file input',
                'reports_processed/': 'create on startup for output',
                'static/': 'voice UI assets',
                'templates/': 'if using template rendering'
            }
        }
        self.dna_package['deployment_config'] = deployment_dna
        
    def extract_integration_points(self):
        """Extract key integration points for any technology stack"""
        integration_dna = {
            'rest_api_endpoints': {
                '/automate-task': 'POST - execute automation with authentic data',
                '/automation-status': 'GET - view real execution results',
                '/attendance-matrix': 'GET - access processed timecard data',
                '/location-tracking': 'GET - view live asset locations',
                '/setup-attendance-automation': 'POST - configure scheduled processing'
            },
            'data_exchange_formats': {
                'input': 'multipart/form-data for file uploads, JSON for API calls',
                'output': 'JSON responses with execution results and record counts',
                'reports': 'CSV files with timestamps in reports_processed directory'
            },
            'authentication_integration': {
                'session_management': 'flask sessions with DATABASE_URL',
                'user_model': 'SQLAlchemy User model with authentication methods',
                'security': 'SESSION_SECRET environment variable required'
            },
            'external_service_integration': {
                'email_notifications': 'optional SENDGRID_API_KEY for report delivery',
                'ai_processing': 'optional OPENAI_API_KEY for enhanced analysis',
                'asset_tracking': 'required GAUGE_API_KEY for live location data'
            }
        }
        self.dna_package['integration_points'].append(integration_dna)
        
    def generate_remix_instructions(self):
        """Generate complete instructions for technology remix"""
        instructions = {
            'technology_transfer_steps': [
                '1. Extract automation_engine.py for core task execution logic',
                '2. Implement database schema from models.py for authentic data storage',
                '3. Configure GAUGE API integration for live asset tracking',
                '4. Set up file processing pipeline for uploads and reports directories',
                '5. Configure environment variables for external service connections',
                '6. Implement REST API endpoints for automation control',
                '7. Test with authentic timecard files and GAUGE API credentials'
            ],
            'critical_preservation_requirements': [
                'maintain_authentic_data_processing_not_mock_data',
                'preserve_gauge_api_integration_for_live_tracking',
                'keep_file_based_workflow_uploads_to_reports',
                'maintain_fort_worth_gps_zone_mapping',
                'preserve_background_task_scheduling',
                'keep_database_schema_for_authentic_data'
            ],
            'validation_checklist': [
                'uploads directory accepts Excel/CSV files',
                'reports_processed directory generates timestamped outputs',
                'GAUGE API returns live asset location data',
                'database stores authentic attendance records',
                'automation status shows real execution counts',
                'scheduled tasks run in background threads'
            ]
        }
        return instructions
        
    def create_complete_dna_package(self):
        """Create complete DNA package for technology transfer"""
        print(f"Extracting TRAXOVO DNA package at {self.extract_timestamp}")
        
        # Extract all components
        self.extract_core_automation_engine()
        self.extract_database_schema()
        self.extract_api_integrations()
        self.extract_file_processing_workflow()
        self.extract_deployment_configuration()
        self.extract_integration_points()
        
        # Generate remix instructions
        remix_instructions = self.generate_remix_instructions()
        self.dna_package['remix_instructions'] = remix_instructions
        
        # Add metadata
        self.dna_package['metadata'] = {
            'extraction_timestamp': self.extract_timestamp,
            'source_platform': 'replit_flask_postgresql',
            'target_compatibility': 'any_web_framework_with_database',
            'data_integrity_level': 'authentic_production_data_only',
            'automation_capability': 'real_task_execution_with_scheduling'
        }
        
        # Save DNA package
        dna_filename = f'TRAXOVO_DNA_Complete_{self.extract_timestamp}.json'
        with open(dna_filename, 'w') as f:
            json.dump(self.dna_package, f, indent=2)
            
        print(f"DNA package saved as {dna_filename}")
        print("Technology transfer package ready for any stack integration")
        
        return self.dna_package

if __name__ == "__main__":
    extractor = TRAXOVODNAExtractor()
    dna_package = extractor.create_complete_dna_package()
    
    print("\nDNA Extraction Summary:")
    print(f"Core Files: {len(dna_package['core_files'])}")
    print(f"Database Tables: {len(dna_package['database_schema'])}")
    print(f"API Integrations: {len(dna_package['api_integrations'])}")
    print(f"Automation Workflows: {len(dna_package['automation_workflows'])}")
    print(f"Integration Points: {len(dna_package['integration_points'])}")
    print("\nReady for technology remix and cohesive integration.")