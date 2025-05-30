"""
Direct SQL execution for Supabase data operations
"""

import os
import psycopg2
import logging

logger = logging.getLogger(__name__)

def execute_sql_query(sql_query: str):
    """Execute SQL query directly on Supabase database"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return []
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        
        # Check if it's a SELECT query
        if sql_query.strip().upper().startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.commit()
            result = []
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return []