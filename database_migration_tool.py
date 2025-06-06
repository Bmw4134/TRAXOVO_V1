
"""
Database Migration Tool - Offload Large Data to Connected Database
Moves large files and cached data from filesystem to PostgreSQL database
"""

import os
import json
import sqlite3
import psycopg2
import gzip
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional

class DatabaseMigrationTool:
    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        self.migration_log = []
        self.setup_migration_tables()
        
    def setup_migration_tables(self):
        """Create tables for migrated data"""
        if not self.db_url:
            print("No DATABASE_URL configured")
            return
            
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Large files storage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS large_file_storage (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    compressed_data BYTEA,
                    original_size INTEGER,
                    compressed_size INTEGER,
                    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            ''')
            
            # Cache data storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_storage (
                    cache_key TEXT PRIMARY KEY,
                    cache_data JSONB,
                    cache_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            # Archive data storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archive_storage (
                    id SERIAL PRIMARY KEY,
                    archive_name TEXT NOT NULL,
                    archive_data JSONB,
                    archive_type TEXT,
                    source_path TEXT,
                    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("Migration tables created successfully")
            
        except Exception as e:
            print(f"Error setting up migration tables: {e}")
    
    def migrate_large_json_files(self):
        """Migrate large JSON files to database"""
        large_files = [
            'GAUGE API PULL 1045AM_05.15.2025.json',
            'TRAXOVO_DNA_Complete_20250605_162308.json',
            'TRAXOVO_Comprehensive_Audit_20250603_184020.json',
            'deployment_optimization.json',
            'mobile_optimization_cache.json'
        ]
        
        migrated_count = 0
        space_saved = 0
        
        for filename in large_files:
            if os.path.exists(filename):
                try:
                    # Read and compress file
                    with open(filename, 'r') as f:
                        data = json.load(f)
                    
                    original_size = os.path.getsize(filename)
                    compressed_data = gzip.compress(json.dumps(data).encode('utf-8'))
                    
                    # Store in database
                    conn = psycopg2.connect(self.db_url)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO large_file_storage 
                        (filename, file_type, compressed_data, original_size, compressed_size, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (filename) DO UPDATE SET
                        compressed_data = EXCLUDED.compressed_data,
                        compressed_size = EXCLUDED.compressed_size,
                        upload_timestamp = CURRENT_TIMESTAMP
                    ''', (
                        filename,
                        'json',
                        compressed_data,
                        original_size,
                        len(compressed_data),
                        json.dumps({'source': 'migration', 'compression_ratio': len(compressed_data) / original_size})
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    # Archive original file
                    os.rename(filename, f"archived_{filename}")
                    
                    migrated_count += 1
                    space_saved += original_size
                    
                    self.migration_log.append({
                        'file': filename,
                        'original_size': original_size,
                        'compressed_size': len(compressed_data),
                        'compression_ratio': len(compressed_data) / original_size,
                        'status': 'migrated'
                    })
                    
                except Exception as e:
                    print(f"Error migrating {filename}: {e}")
        
        print(f"Migrated {migrated_count} large files, saved {space_saved} bytes")
        return migrated_count, space_saved
    
    def migrate_sqlite_databases(self):
        """Migrate SQLite databases to PostgreSQL"""
        db_files = [
            'authentic_fleet_data.db',
            'automation_requests.db',
            'automation_tasks.db',
            'dashboard_customization.db',
            'failure_analysis.db',
            'learning_progress.db',
            'master_brain.db'
        ]
        
        migrated_dbs = 0
        
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    # Read SQLite data
                    sqlite_conn = sqlite3.connect(db_file)
                    sqlite_conn.row_factory = sqlite3.Row
                    
                    # Get all tables
                    cursor = sqlite_conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    db_data = {}
                    for table in tables:
                        table_name = table[0]
                        cursor.execute(f"SELECT * FROM {table_name}")
                        rows = cursor.fetchall()
                        db_data[table_name] = [dict(row) for row in rows]
                    
                    sqlite_conn.close()
                    
                    # Store in PostgreSQL
                    conn = psycopg2.connect(self.db_url)
                    pg_cursor = conn.cursor()
                    
                    pg_cursor.execute('''
                        INSERT INTO archive_storage 
                        (archive_name, archive_data, archive_type, source_path)
                        VALUES (%s, %s, %s, %s)
                    ''', (
                        db_file.replace('.db', ''),
                        json.dumps(db_data),
                        'sqlite_migration',
                        db_file
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    # Archive original file
                    os.rename(db_file, f"archived_{db_file}")
                    migrated_dbs += 1
                    
                except Exception as e:
                    print(f"Error migrating {db_file}: {e}")
        
        print(f"Migrated {migrated_dbs} SQLite databases to PostgreSQL")
        return migrated_dbs
    
    def migrate_cache_files(self):
        """Migrate cache and temporary files"""
        cache_patterns = [
            'mobile_diagnostic_optimization.json',
            'deployment_status.json',
            'optimization_verification.json',
            'goal_tracker.json'
        ]
        
        migrated_cache = 0
        
        for cache_file in cache_patterns:
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    conn = psycopg2.connect(self.db_url)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO cache_storage 
                        (cache_key, cache_data, cache_type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (cache_key) DO UPDATE SET
                        cache_data = EXCLUDED.cache_data,
                        created_at = CURRENT_TIMESTAMP
                    ''', (
                        cache_file.replace('.json', ''),
                        json.dumps(cache_data),
                        'file_cache'
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    os.remove(cache_file)
                    migrated_cache += 1
                    
                except Exception as e:
                    print(f"Error migrating cache {cache_file}: {e}")
        
        print(f"Migrated {migrated_cache} cache files")
        return migrated_cache
    
    def migrate_archived_modules(self):
        """Archive the archived_modules directory"""
        archived_dir = 'archived_modules'
        if os.path.exists(archived_dir):
            try:
                # Create a manifest of all archived files
                manifest = []
                total_size = 0
                
                for root, dirs, files in os.walk(archived_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        
                        manifest.append({
                            'path': file_path,
                            'size': file_size,
                            'modified': os.path.getmtime(file_path)
                        })
                
                # Store manifest in database
                conn = psycopg2.connect(self.db_url)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO archive_storage 
                    (archive_name, archive_data, archive_type, source_path)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    'archived_modules_manifest',
                    json.dumps({
                        'manifest': manifest,
                        'total_files': len(manifest),
                        'total_size': total_size,
                        'archived_at': datetime.now().isoformat()
                    }),
                    'directory_archive',
                    archived_dir
                ))
                
                conn.commit()
                conn.close()
                
                print(f"Archived manifest for {len(manifest)} files ({total_size} bytes)")
                return True
                
            except Exception as e:
                print(f"Error archiving modules: {e}")
                return False
    
    def retrieve_file_from_database(self, filename: str) -> Optional[Dict]:
        """Retrieve a migrated file from database"""
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
                return {
                    'data': json.loads(decompressed_data.decode('utf-8')),
                    'original_size': original_size,
                    'metadata': metadata
                }
            
        except Exception as e:
            print(f"Error retrieving {filename}: {e}")
        
        return None
    
    def run_full_migration(self):
        """Run complete migration process"""
        print("Starting database migration...")
        
        # Migrate large JSON files
        json_count, json_space = self.migrate_large_json_files()
        
        # Migrate SQLite databases
        db_count = self.migrate_sqlite_databases()
        
        # Migrate cache files
        cache_count = self.migrate_cache_files()
        
        # Archive modules directory
        self.migrate_archived_modules()
        
        # Generate migration report
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'files_migrated': json_count,
            'space_saved_bytes': json_space,
            'databases_migrated': db_count,
            'cache_files_migrated': cache_count,
            'migration_log': self.migration_log
        }
        
        # Store migration report
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cache_storage 
                (cache_key, cache_data, cache_type)
                VALUES (%s, %s, %s)
            ''', (
                'migration_report',
                json.dumps(report),
                'migration_log'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error storing migration report: {e}")
        
        print("\nMigration Summary:")
        print(f"- {json_count} large files migrated")
        print(f"- {json_space} bytes saved")
        print(f"- {db_count} SQLite databases migrated")
        print(f"- {cache_count} cache files migrated")
        print("Migration complete!")
        
        return report

# Global instance
migration_tool = DatabaseMigrationTool()

if __name__ == "__main__":
    # Run migration
    migration_tool.run_full_migration()
