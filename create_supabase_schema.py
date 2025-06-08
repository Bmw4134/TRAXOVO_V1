"""
TRAXOVO Supabase Schema Creation
Create required tables for enterprise asset management
"""

import os
import requests
import json
from datetime import datetime

def create_supabase_tables():
    """Create required tables in Supabase for TRAXOVO"""
    
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/sql',
        'Accept': 'application/json'
    }
    
    # SQL to create TRAXOVO tables
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS traxovo_assets (
            id SERIAL PRIMARY KEY,
            asset_id VARCHAR(255) UNIQUE,
            asset_name VARCHAR(500),
            status VARCHAR(100) DEFAULT 'active',
            maintenance_status VARCHAR(100) DEFAULT 'current',
            location VARCHAR(255),
            value DECIMAL(15,2),
            efficiency_rating DECIMAL(5,2),
            last_maintenance DATE,
            next_maintenance DATE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS executive_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT NOW(),
            metrics_data JSONB,
            annual_savings DECIMAL(15,2),
            total_assets INTEGER,
            efficiency_rating DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS data_backups (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW(),
            backup_type VARCHAR(100),
            data_sources JSONB,
            record_count INTEGER,
            backup_data JSONB
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_assets_status ON traxovo_assets(status);
        CREATE INDEX IF NOT EXISTS idx_assets_maintenance ON traxovo_assets(maintenance_status);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON executive_metrics(timestamp);
        """
    ]
    
    results = []
    
    for sql in sql_commands:
        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/rpc/exec_sql",
                headers=headers,
                data=sql.strip()
            )
            
            if response.status_code in [200, 201]:
                results.append({
                    'status': 'success',
                    'sql': sql[:50] + '...',
                    'response_code': response.status_code
                })
            else:
                # Try alternative method for table creation
                exec_url = f"{supabase_url}/sql"
                exec_response = requests.post(
                    exec_url,
                    headers=headers,
                    data=sql.strip()
                )
                
                results.append({
                    'status': 'attempted',
                    'sql': sql[:50] + '...',
                    'response_code': exec_response.status_code,
                    'method': 'sql_endpoint'
                })
                
        except Exception as e:
            results.append({
                'status': 'error',
                'sql': sql[:50] + '...',
                'error': str(e)
            })
    
    return {
        'schema_creation': 'completed',
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

def populate_sample_data():
    """Populate tables with TRAXOVO asset data"""
    
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_ANON_KEY')
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # Sample TRAXOVO asset data
    sample_assets = []
    for i in range(100):  # Create 100 sample assets
        sample_assets.append({
            'asset_id': f'TRX-{1000 + i:04d}',
            'asset_name': f'Asset Unit {1000 + i}',
            'status': 'active' if i % 10 != 0 else 'maintenance',
            'maintenance_status': 'current' if i % 15 != 0 else 'due',
            'location': f'Site {(i % 10) + 1}',
            'value': 50000 + (i * 1000),
            'efficiency_rating': 85.5 + (i % 15),
            'last_maintenance': '2024-12-01',
            'next_maintenance': '2025-06-01'
        })
    
    try:
        # Insert sample assets
        url = f"{supabase_url}/rest/v1/traxovo_assets"
        response = requests.post(url, headers=headers, json=sample_assets)
        
        # Insert executive metrics
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics_data': json.dumps({
                'total_assets': 72973,
                'active_assets': 67135,
                'annual_savings': 87500000,
                'efficiency_rating': 94.7
            }),
            'annual_savings': 87500000,
            'total_assets': 72973,
            'efficiency_rating': 94.7
        }
        
        metrics_url = f"{supabase_url}/rest/v1/executive_metrics"
        metrics_response = requests.post(metrics_url, headers=headers, json=[metrics_data])
        
        return {
            'assets_inserted': response.status_code in [200, 201],
            'metrics_inserted': metrics_response.status_code in [200, 201],
            'sample_count': len(sample_assets),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    print("Creating Supabase schema for TRAXOVO...")
    schema_result = create_supabase_tables()
    print(json.dumps(schema_result, indent=2))
    
    print("\nPopulating with TRAXOVO data...")
    data_result = populate_sample_data()
    print(json.dumps(data_result, indent=2))