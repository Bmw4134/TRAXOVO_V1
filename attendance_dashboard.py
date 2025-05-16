"""
Attendance Dashboard Module

This module provides routes and functionality for displaying attendance trend data
extracted from the MTD reports. It uses SQLite database for storage and retrieval.
"""

from flask import Blueprint, render_template, request, jsonify
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create blueprint
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect('extracted_data/attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

@attendance_bp.route('/')
def attendance_dashboard():
    """Display attendance dashboard page"""
    try:
        conn = get_db_connection()
        
        # Get summary statistics
        cursor = conn.cursor()
        
        # Get late start counts
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE status_type='LATE_START'")
        late_start_count = cursor.fetchone()[0]
        
        # Get early end counts
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE status_type='EARLY_END'")
        early_end_count = cursor.fetchone()[0]
        
        # Get not on job counts
        cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE status_type='NOT_ON_JOB'")
        not_on_job_count = cursor.fetchone()[0]
        
        # Get total driver count
        cursor.execute("SELECT COUNT(DISTINCT driver_id) FROM attendance_records")
        driver_count = cursor.fetchone()[0]
        
        # Get job site count
        cursor.execute("SELECT COUNT(DISTINCT job_site_id) FROM attendance_records")
        job_site_count = cursor.fetchone()[0]
        
        # Get date range of data
        cursor.execute("SELECT MIN(report_date) as start_date, MAX(report_date) as end_date FROM attendance_records")
        date_range = cursor.fetchone()
        
        # Get top drivers with issues
        cursor.execute("""
            SELECT d.name, d.employee_id, 
                   COUNT(CASE WHEN ar.status_type='LATE_START' THEN 1 ELSE NULL END) as late_starts,
                   COUNT(CASE WHEN ar.status_type='EARLY_END' THEN 1 ELSE NULL END) as early_ends,
                   COUNT(CASE WHEN ar.status_type='NOT_ON_JOB' THEN 1 ELSE NULL END) as not_on_job,
                   COUNT(*) as total
            FROM attendance_records ar
            JOIN drivers d ON ar.driver_id = d.id
            GROUP BY ar.driver_id
            ORDER BY total DESC
            LIMIT 10
        """)
        problem_drivers = cursor.fetchall()
        
        # Get top job sites with issues
        cursor.execute("""
            SELECT js.name, js.job_number,
                   COUNT(CASE WHEN ar.status_type='LATE_START' THEN 1 ELSE NULL END) as late_starts,
                   COUNT(CASE WHEN ar.status_type='EARLY_END' THEN 1 ELSE NULL END) as early_ends,
                   COUNT(CASE WHEN ar.status_type='NOT_ON_JOB' THEN 1 ELSE NULL END) as not_on_job,
                   COUNT(*) as total
            FROM attendance_records ar
            JOIN job_sites js ON ar.job_site_id = js.id
            GROUP BY ar.job_site_id
            ORDER BY total DESC
            LIMIT 10
        """)
        problem_job_sites = cursor.fetchall()
        
        conn.close()
        
        # Prepare data for template
        summary = {
            'late_start_count': late_start_count,
            'early_end_count': early_end_count,
            'not_on_job_count': not_on_job_count,
            'total_incidents': late_start_count + early_end_count + not_on_job_count,
            'driver_count': driver_count,
            'job_site_count': job_site_count,
            'start_date': date_range['start_date'] if date_range else None,
            'end_date': date_range['end_date'] if date_range else None
        }
        
        return render_template(
            'attendance/dashboard.html',
            summary=summary,
            problem_drivers=problem_drivers,
            problem_job_sites=problem_job_sites
        )
    
    except Exception as e:
        logger.error(f"Error rendering attendance dashboard: {e}")
        # Create a basic template with error message if no data available
        return render_template(
            'attendance/dashboard.html',
            summary={
                'late_start_count': 0,
                'early_end_count': 0,
                'not_on_job_count': 0,
                'total_incidents': 0,
                'driver_count': 0,
                'job_site_count': 0,
                'start_date': None,
                'end_date': None
            },
            problem_drivers=[],
            problem_job_sites=[],
            error=str(e)
        )

@attendance_bp.route('/charts/daily')
def daily_chart_data():
    """Get daily attendance data for charts"""
    try:
        conn = get_db_connection()
        
        # Query for daily incidents
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                report_date,
                COUNT(CASE WHEN status_type='LATE_START' THEN 1 ELSE NULL END) as late_starts,
                COUNT(CASE WHEN status_type='EARLY_END' THEN 1 ELSE NULL END) as early_ends,
                COUNT(CASE WHEN status_type='NOT_ON_JOB' THEN 1 ELSE NULL END) as not_on_job
            FROM attendance_records
            GROUP BY report_date
            ORDER BY report_date
        """)
        
        daily_data = cursor.fetchall()
        conn.close()
        
        # Format data for charts
        dates = []
        late_starts = []
        early_ends = []
        not_on_job = []
        
        for day in daily_data:
            dates.append(day['report_date'])
            late_starts.append(day['late_starts'])
            early_ends.append(day['early_ends'])
            not_on_job.append(day['not_on_job'])
        
        return jsonify({
            'dates': dates,
            'late_starts': late_starts,
            'early_ends': early_ends,
            'not_on_job': not_on_job
        })
    
    except Exception as e:
        logger.error(f"Error getting daily chart data: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@attendance_bp.route('/driver/<int:driver_id>')
def driver_detail(driver_id):
    """Display driver detail page with attendance history"""
    try:
        conn = get_db_connection()
        
        # Get driver info
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = cursor.fetchone()
        
        if not driver:
            conn.close()
            return render_template('attendance/error.html', message="Driver not found"), 404
        
        # Get driver's attendance history
        cursor.execute("""
            SELECT ar.*, js.name as job_site_name, js.job_number,
                  CASE 
                      WHEN ar.status_type = 'LATE_START' THEN ar.minutes_late
                      WHEN ar.status_type = 'EARLY_END' THEN ar.minutes_early
                      ELSE 0
                  END as minutes
            FROM attendance_records ar
            JOIN job_sites js ON ar.job_site_id = js.id
            WHERE ar.driver_id = ?
            ORDER BY ar.report_date DESC
        """, (driver_id,))
        
        history = cursor.fetchall()
        
        # Get summary stats for this driver
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status_type='LATE_START' THEN 1 ELSE NULL END) as late_starts,
                COUNT(CASE WHEN status_type='EARLY_END' THEN 1 ELSE NULL END) as early_ends,
                COUNT(CASE WHEN status_type='NOT_ON_JOB' THEN 1 ELSE NULL END) as not_on_job,
                COUNT(*) as total_incidents,
                AVG(CASE WHEN status_type='LATE_START' THEN minutes_late ELSE NULL END) as avg_minutes_late,
                AVG(CASE WHEN status_type='EARLY_END' THEN minutes_early ELSE NULL END) as avg_minutes_early
            FROM attendance_records
            WHERE driver_id = ?
        """, (driver_id,))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return render_template(
            'attendance/driver_detail.html',
            driver=driver,
            history=history,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error rendering driver detail: {e}")
        return render_template('attendance/error.html', message=f"Error: {e}"), 500

@attendance_bp.route('/job_site/<int:job_site_id>')
def job_site_detail(job_site_id):
    """Display job site detail page with attendance history"""
    try:
        conn = get_db_connection()
        
        # Get job site info
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_sites WHERE id = ?", (job_site_id,))
        job_site = cursor.fetchone()
        
        if not job_site:
            conn.close()
            return render_template('attendance/error.html', message="Job site not found"), 404
        
        # Get attendance issues at this job site
        cursor.execute("""
            SELECT ar.*, d.name as driver_name, d.employee_id
            FROM attendance_records ar
            JOIN drivers d ON ar.driver_id = d.id
            WHERE ar.job_site_id = ?
            ORDER BY ar.report_date DESC
        """, (job_site_id,))
        
        history = cursor.fetchall()
        
        # Get summary stats for this job site
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status_type='LATE_START' THEN 1 ELSE NULL END) as late_starts,
                COUNT(CASE WHEN status_type='EARLY_END' THEN 1 ELSE NULL END) as early_ends,
                COUNT(CASE WHEN status_type='NOT_ON_JOB' THEN 1 ELSE NULL END) as not_on_job,
                COUNT(*) as total_incidents,
                COUNT(DISTINCT driver_id) as unique_drivers
            FROM attendance_records
            WHERE job_site_id = ?
        """, (job_site_id,))
        
        stats = cursor.fetchone()
        
        conn.close()
        
        return render_template(
            'attendance/job_site_detail.html',
            job_site=job_site,
            history=history,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Error rendering job site detail: {e}")
        return render_template('attendance/error.html', message=f"Error: {e}"), 500

@attendance_bp.route('/process_mtd_data', methods=['GET', 'POST'])
def process_mtd_data():
    """Process MTD data from uploaded files"""
    if request.method == 'POST':
        try:
            # Import the extract_mtd_data module and run it
            from extract_mtd_data import process_mtd_reports
            
            result = process_mtd_reports()
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'MTD data processed successfully',
                    'results': result['results']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f"Error processing MTD data: {result.get('message', 'Unknown error')}"
                })
        
        except Exception as e:
            logger.error(f"Error processing MTD data: {e}")
            return jsonify({
                'success': False,
                'message': f"Error: {e}"
            })
    
    return render_template('attendance/process_mtd.html')