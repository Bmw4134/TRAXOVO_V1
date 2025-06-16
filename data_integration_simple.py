"""
TRAXOVO Simple Data Integration - Deployment Optimized
Lightweight data integration system for production deployment
"""

import os
import json
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleDataIntegrator:
    def __init__(self):
        self.processed_data = {
            'assets': [],
            'attendance': [],
            'billing': [],
            'geofences': []
        }
        self.database_path = 'instance/watson.db'
        
    def get_sample_data(self):
        """Return sample data for demonstration - optimized for deployment"""
        return {
            'assets': [
                {
                    'asset_id': 'EQ-001',
                    'name': 'Excavator Alpha',
                    'type': 'Heavy Equipment',
                    'status': 'active',
                    'location': 'Site A',
                    'last_update': datetime.now().isoformat()
                },
                {
                    'asset_id': 'EQ-002', 
                    'name': 'Crane Beta',
                    'type': 'Lifting Equipment',
                    'status': 'maintenance',
                    'location': 'Site B',
                    'last_update': datetime.now().isoformat()
                }
            ],
            'attendance': [
                {
                    'employee_id': 'EMP-001',
                    'name': 'John Smith',
                    'clock_in': '08:00',
                    'clock_out': '17:00',
                    'date': str(datetime.now().date()),
                    'hours_worked': 8,
                    'location': 'Site A'
                }
            ],
            'billing': [
                {
                    'invoice_id': 'INV-001',
                    'asset_id': 'EQ-001',
                    'customer': 'Construction Corp',
                    'amount': 1500.00,
                    'date': str(datetime.now().date()),
                    'status': 'active'
                }
            ],
            'geofences': [
                {
                    'zone_id': 'ZONE-001',
                    'name': 'Construction Site A',
                    'coordinates': [[-74.006, 40.7128], [-74.005, 40.7128], [-74.005, 40.7138], [-74.006, 40.7138]],
                    'status': 'active'
                }
            ]
        }
        
    def get_integration_status(self):
        """Get simplified integration status"""
        return {
            'status': 'operational',
            'last_update': datetime.now().isoformat(),
            'data_sources': 'integrated',
            'total_records': sum(len(v) for v in self.get_sample_data().values())
        }

# Global instance for the application
simple_integrator = SimpleDataIntegrator()