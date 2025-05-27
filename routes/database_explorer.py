"""
Database Explorer - Direct database access for TRAXORA
View and query your fleet data tables without writing code
"""

from flask import Blueprint, render_template, request, jsonify
import logging
from app import db
import pandas as pd
from sqlalchemy import text, inspect
from datetime import datetime

database_explorer_bp = Blueprint('database_explorer', __name__)
logger = logging.getLogger(__name__)

@database_explorer_bp.route('/')
def database_dashboard():
    """Main database explorer dashboard"""
    try:
        # Get all table names
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Get table info
        table_info = []
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_info.append({
                    'name': table,
                    'count': count,
                    'description': get_table_description(table)
                })
            except Exception as e:
                table_info.append({
                    'name': table,
                    'count': 'Error',
                    'description': str(e)
                })
        
        return render_template('database_explorer/dashboard.html', 
                             tables=table_info,
                             total_tables=len(tables))
    
    except Exception as e:
        logger.error(f"Database explorer error: {e}")
        return render_template('database_explorer/dashboard.html', 
                             tables=[],
                             error=str(e))

@database_explorer_bp.route('/table/<table_name>')
def view_table(table_name):
    """View data from a specific table"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        # Get table data
        query = text(f"SELECT * FROM {table_name} LIMIT {per_page} OFFSET {offset}")
        result = db.session.execute(query)
        
        # Convert to list of dictionaries
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        total_count = db.session.execute(count_query).scalar()
        
        # Get table schema
        inspector = inspect(db.engine)
        schema = inspector.get_columns(table_name)
        
        return render_template('database_explorer/table_view.html',
                             table_name=table_name,
                             columns=columns,
                             rows=rows,
                             schema=schema,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             has_next=offset + per_page < total_count,
                             has_prev=page > 1)
    
    except Exception as e:
        logger.error(f"Error viewing table {table_name}: {e}")
        return render_template('database_explorer/table_view.html',
                             table_name=table_name,
                             error=str(e))

@database_explorer_bp.route('/query', methods=['GET', 'POST'])
def custom_query():
    """Execute custom SQL queries"""
    if request.method == 'POST':
        try:
            query = request.form.get('query', '').strip()
            
            if not query:
                return jsonify({'error': 'Query cannot be empty'})
            
            # Safety check - only allow SELECT statements
            if not query.upper().startswith('SELECT'):
                return jsonify({'error': 'Only SELECT queries are allowed'})
            
            result = db.session.execute(text(query))
            
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                return jsonify({
                    'success': True,
                    'columns': columns,
                    'rows': rows,
                    'count': len(rows)
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Query executed successfully'
                })
                
        except Exception as e:
            logger.error(f"Query error: {e}")
            return jsonify({'error': str(e)})
    
    return render_template('database_explorer/query.html')

@database_explorer_bp.route('/export/<table_name>')
def export_table(table_name):
    """Export table data to CSV"""
    try:
        query = text(f"SELECT * FROM {table_name}")
        df = pd.read_sql(query, db.engine)
        
        # Create CSV response
        csv_data = df.to_csv(index=False)
        
        from flask import Response
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={table_name}_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'error': str(e)})

def get_table_description(table_name):
    """Get a friendly description for table names"""
    descriptions = {
        'assets': 'Fleet vehicles and equipment tracking',
        'drivers': 'Driver information and credentials',
        'attendance_records': 'Daily attendance tracking data',
        'job_sites': 'Work location and project sites',
        'gps_data': 'Vehicle location and movement data',
        'users': 'System users and authentication',
        'reports': 'Generated reports and analytics'
    }
    return descriptions.get(table_name, 'Database table')