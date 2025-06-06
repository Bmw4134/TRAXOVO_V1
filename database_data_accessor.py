
"""
Database Data Accessor - Access migrated data from PostgreSQL
Provides easy access to files and data moved to the database
"""

import os
import json
import psycopg2
import gzip
from typing import Dict, List, Any, Optional

class DatabaseDataAccessor:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
    
    def get_large_file(self, filename: str) -> Optional[Dict]:
        """Get a large file that was migrated to database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT compressed_data, original_size, metadata 
                FROM large_file_storage 
                WHERE filename = %s
            ''', (filename,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                compressed_data, original_size, metadata = result
                decompressed_data = gzip.decompress(compressed_data)
                return json.loads(decompressed_data.decode('utf-8'))
            
        except Exception as e:
            print(f"Error accessing {filename}: {e}")
        
        return None
    
    def get_cache_data(self, cache_key: str) -> Optional[Dict]:
        """Get cached data from database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cache_data 
                FROM cache_storage 
                WHERE cache_key = %s
            ''', (cache_key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]  # JSONB data
            
        except Exception as e:
            print(f"Error accessing cache {cache_key}: {e}")
        
        return None
    
    def get_archived_database(self, db_name: str) -> Optional[Dict]:
        """Get archived SQLite database data"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT archive_data 
                FROM archive_storage 
                WHERE archive_name = %s AND archive_type = 'sqlite_migration'
            ''', (db_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]  # JSONB data
            
        except Exception as e:
            print(f"Error accessing database {db_name}: {e}")
        
        return None
    
    def list_migrated_files(self) -> List[Dict]:
        """List all migrated files"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, original_size, compressed_size, upload_timestamp
                FROM large_file_storage
                ORDER BY upload_timestamp DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'filename': row[0],
                    'original_size': row[1],
                    'compressed_size': row[2],
                    'upload_timestamp': row[3].isoformat() if row[3] else None,
                    'compression_ratio': row[2] / row[1] if row[1] > 0 else 0
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

# Global accessor instance
db_accessor = DatabaseDataAccessor()

# Helper functions for existing code compatibility
def get_gauge_api_data():
    """Get GAUGE API data from database"""
    return db_accessor.get_large_file('GAUGE API PULL 1045AM_05.15.2025.json')

def get_traxovo_dna():
    """Get TRAXOVO DNA data from database"""
    return db_accessor.get_large_file('TRAXOVO_DNA_Complete_20250605_162308.json')

def get_deployment_optimization():
    """Get deployment optimization data from database"""
    return db_accessor.get_cache_data('deployment_optimization')
