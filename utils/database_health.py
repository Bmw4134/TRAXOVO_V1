"""
TRAXORA Fleet Management System - Database Health Check Utility

This module provides a comprehensive set of database health checks and diagnostics
to ensure proper database connectivity, schema integrity, and query performance.
"""

import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Tuple

from sqlalchemy import inspect, text, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper

logger = logging.getLogger(__name__)

class DatabaseHealthCheck:
    """
    Comprehensive database health check utility for the TRAXORA system.
    Validates database connection, schema integrity, and query performance.
    """
    
    def __init__(self, db, models_list=None):
        """
        Initialize the database health check utility.
        
        Args:
            db: SQLAlchemy database instance
            models_list: List of SQLAlchemy models to check
        """
        self.db = db
        self.models_list = models_list or []
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'connection_status': False,
            'schema_integrity': False,
            'model_column_mapping': {},
            'foreign_key_integrity': {},
            'query_performance': {},
            'errors': [],
            'warnings': [],
            'details': {}
        }
    
    def check_connection(self) -> bool:
        """
        Check database connection status.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Simple query to check database connectivity
            start_time = time.time()
            result = self.db.session.execute(text('SELECT 1')).fetchone()
            end_time = time.time()
            
            connection_successful = result is not None and result[0] == 1
            self.results['connection_status'] = connection_successful
            self.results['connection_time'] = end_time - start_time
            
            if connection_successful:
                logger.info(f"Database connection successful in {end_time - start_time:.4f} seconds")
            else:
                logger.error("Database connection failed")
                self.results['errors'].append("Database connection failed")
            
            return connection_successful
        
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.results['errors'].append(f"Database connection error: {str(e)}")
            self.results['connection_status'] = False
            return False
    
    def check_schema_integrity(self) -> bool:
        """
        Check schema integrity by validating that all models have corresponding tables.
        
        Returns:
            bool: True if schema integrity check passes, False otherwise
        """
        try:
            inspector = inspect(self.db.engine)
            tables_in_db = inspector.get_table_names()
            
            missing_tables = []
            for model in self.models_list:
                if hasattr(model, '__tablename__') and model.__tablename__ not in tables_in_db:
                    missing_tables.append(model.__tablename__)
            
            self.results['schema_integrity'] = len(missing_tables) == 0
            self.results['details']['tables_in_db'] = tables_in_db
            self.results['details']['missing_tables'] = missing_tables
            
            if missing_tables:
                logger.warning(f"Missing tables in database: {missing_tables}")
                self.results['warnings'].append(f"Missing tables in database: {missing_tables}")
            else:
                logger.info("Schema integrity check passed")
            
            return len(missing_tables) == 0
        
        except Exception as e:
            logger.error(f"Schema integrity check error: {str(e)}")
            self.results['errors'].append(f"Schema integrity check error: {str(e)}")
            self.results['schema_integrity'] = False
            return False
    
    def check_model_column_mapping(self) -> Dict[str, Dict[str, bool]]:
        """
        Check model column mappings by validating that all model attributes have
        corresponding database columns.
        
        Returns:
            Dict: Results of column mapping checks for each model
        """
        try:
            inspector = inspect(self.db.engine)
            mapping_results = {}
            
            for model in self.models_list:
                if not hasattr(model, '__tablename__'):
                    continue
                
                table_name = model.__tablename__
                columns_in_db = {col['name']: col for col in inspector.get_columns(table_name)}
                mapper = class_mapper(model)
                mapping_status = {}
                
                for column_prop in mapper.column_attrs:
                    # Get the actual column name in the database (handle 'name' overrides)
                    column = column_prop.columns[0]
                    db_column_name = column.name if not column.key or column.name == column.key else column.key
                    
                    # Check if column exists in database
                    db_column_exists = db_column_name in columns_in_db
                    mapping_status[column_prop.key] = {
                        'mapped_to': db_column_name,
                        'exists_in_db': db_column_exists
                    }
                    
                    if not db_column_exists:
                        warning = f"Model {model.__name__}.{column_prop.key} mapped to non-existent database column '{db_column_name}' in table '{table_name}'"
                        logger.warning(warning)
                        self.results['warnings'].append(warning)
                
                mapping_results[model.__name__] = mapping_status
            
            self.results['model_column_mapping'] = mapping_results
            return mapping_results
        
        except Exception as e:
            logger.error(f"Model column mapping check error: {str(e)}")
            self.results['errors'].append(f"Model column mapping check error: {str(e)}")
            return {}
    
    def check_foreign_key_integrity(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check foreign key integrity by validating referential integrity.
        
        Returns:
            Dict: Results of foreign key integrity checks
        """
        try:
            inspector = inspect(self.db.engine)
            fk_results = {}
            
            for model in self.models_list:
                if not hasattr(model, '__tablename__'):
                    continue
                
                table_name = model.__tablename__
                fk_constraints = inspector.get_foreign_keys(table_name)
                fk_status = []
                
                for fk in fk_constraints:
                    referred_table = fk.get('referred_table')
                    referred_columns = fk.get('referred_columns', [])
                    constrained_columns = fk.get('constrained_columns', [])
                    
                    # Check if referred table exists
                    if referred_table not in inspector.get_table_names():
                        error = f"Foreign key in {table_name} references non-existent table {referred_table}"
                        logger.error(error)
                        self.results['errors'].append(error)
                        fk_valid = False
                    else:
                        # Check if referred columns exist in referred table
                        referred_columns_in_db = {col['name'] for col in inspector.get_columns(referred_table)}
                        missing_columns = [col for col in referred_columns if col not in referred_columns_in_db]
                        
                        fk_valid = len(missing_columns) == 0
                        if not fk_valid:
                            error = f"Foreign key in {table_name} references non-existent columns {missing_columns} in table {referred_table}"
                            logger.error(error)
                            self.results['errors'].append(error)
                    
                    fk_status.append({
                        'table': table_name,
                        'columns': constrained_columns,
                        'referred_table': referred_table,
                        'referred_columns': referred_columns,
                        'valid': fk_valid
                    })
                
                fk_results[table_name] = fk_status
            
            self.results['foreign_key_integrity'] = fk_results
            return fk_results
        
        except Exception as e:
            logger.error(f"Foreign key integrity check error: {str(e)}")
            self.results['errors'].append(f"Foreign key integrity check error: {str(e)}")
            return {}
    
    def check_query_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Check query performance by measuring execution time of simple queries.
        
        Returns:
            Dict: Results of query performance checks
        """
        try:
            performance_results = {}
            
            for model in self.models_list:
                if not hasattr(model, '__tablename__'):
                    continue
                
                # Simple count query
                start_time = time.time()
                count = self.db.session.query(func.count(model.id)).scalar()
                end_time = time.time()
                count_time = end_time - start_time
                
                # Simple select query (first 10 records)
                start_time = time.time()
                _ = self.db.session.query(model).limit(10).all()
                end_time = time.time()
                select_time = end_time - start_time
                
                performance_results[model.__name__] = {
                    'count': count,
                    'count_query_time': count_time,
                    'select_query_time': select_time
                }
                
                # Log slow queries
                if count_time > 1.0:
                    warning = f"Slow count query for {model.__name__}: {count_time:.4f} seconds"
                    logger.warning(warning)
                    self.results['warnings'].append(warning)
                
                if select_time > 1.0:
                    warning = f"Slow select query for {model.__name__}: {select_time:.4f} seconds"
                    logger.warning(warning)
                    self.results['warnings'].append(warning)
            
            self.results['query_performance'] = performance_results
            return performance_results
        
        except Exception as e:
            logger.error(f"Query performance check error: {str(e)}")
            self.results['errors'].append(f"Query performance check error: {str(e)}")
            return {}
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        Run a comprehensive database health check.
        
        Returns:
            Dict: Complete results of all health checks
        """
        try:
            # Connection check must pass for other checks to execute
            if not self.check_connection():
                return self.results
            
            # Run schema integrity check
            self.check_schema_integrity()
            
            # Run model column mapping check
            self.check_model_column_mapping()
            
            # Run foreign key integrity check
            self.check_foreign_key_integrity()
            
            # Run query performance check
            self.check_query_performance()
            
            # Calculate overall health status
            self.results['overall_health'] = (
                self.results['connection_status'] and 
                self.results['schema_integrity'] and
                len(self.results['errors']) == 0
            )
            
            return self.results
        
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            self.results['errors'].append(f"Database health check failed: {str(e)}")
            self.results['traceback'] = traceback.format_exc()
            self.results['overall_health'] = False
            return self.results
    
    def generate_report(self, include_details=False) -> str:
        """
        Generate a formatted health check report.
        
        Args:
            include_details: Whether to include detailed results in the report
            
        Returns:
            str: Formatted health check report
        """
        report = [
            "=== TRAXORA DATABASE HEALTH CHECK REPORT ===",
            f"Timestamp: {self.results['timestamp']}",
            "",
            f"Connection Status: {'✓ OK' if self.results.get('connection_status', False) else '✘ FAILED'}",
            f"Schema Integrity: {'✓ OK' if self.results.get('schema_integrity', False) else '✘ FAILED'}",
            f"Overall Health: {'✓ OK' if self.results.get('overall_health', False) else '✘ FAILED'}",
            "",
            f"Errors: {len(self.results.get('errors', []))}",
            f"Warnings: {len(self.results.get('warnings', []))}",
            ""
        ]
        
        # Add errors and warnings
        if self.results.get('errors'):
            report.append("--- ERRORS ---")
            for error in self.results.get('errors', []):
                report.append(f"• {error}")
            report.append("")
        
        if self.results.get('warnings'):
            report.append("--- WARNINGS ---")
            for warning in self.results.get('warnings', []):
                report.append(f"• {warning}")
            report.append("")
        
        # Add detailed results if requested
        if include_details:
            if self.results.get('model_column_mapping'):
                report.append("--- MODEL COLUMN MAPPING ---")
                for model_name, mapping in self.results.get('model_column_mapping', {}).items():
                    report.append(f"Model: {model_name}")
                    mismatched_columns = [col for col, status in mapping.items() if not status.get('exists_in_db', True)]
                    if mismatched_columns:
                        report.append(f"  • Mismatched columns: {', '.join(mismatched_columns)}")
                report.append("")
            
            if self.results.get('query_performance'):
                report.append("--- QUERY PERFORMANCE ---")
                for model_name, perf in self.results.get('query_performance', {}).items():
                    report.append(f"Model: {model_name}")
                    report.append(f"  • Count: {perf.get('count', 0)} records")
                    report.append(f"  • Count query time: {perf.get('count_query_time', 0):.4f} seconds")
                    report.append(f"  • Select query time: {perf.get('select_query_time', 0):.4f} seconds")
                report.append("")
        
        return "\n".join(report)

def run_health_check(db, models_list=None) -> Tuple[Dict[str, Any], str]:
    """
    Run a database health check and generate a report.
    
    Args:
        db: SQLAlchemy database instance
        models_list: List of SQLAlchemy models to check
        
    Returns:
        Tuple: (health check results dict, formatted report string)
    """
    health_check = DatabaseHealthCheck(db, models_list)
    results = health_check.check_database_health()
    report = health_check.generate_report(include_details=True)
    
    return results, report