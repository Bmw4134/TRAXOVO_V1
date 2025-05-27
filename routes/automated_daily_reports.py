"""
Automated Daily Reports Module

Handles automated generation and scheduling of daily driver reports
using authentic MTD data and GPS tracking information.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime, timedelta
import logging
import threading
import schedule
import time
from utils.enhanced_daily_processor import EnhancedDailyProcessor

automated_reports_bp = Blueprint('automated_reports', __name__)
logger = logging.getLogger(__name__)

# Global scheduler status
scheduler_running = False
scheduler_thread = None

@automated_reports_bp.route('/auto-daily-dashboard')
def auto_daily_dashboard():
    """Dashboard for automated daily reports"""
    try:
        processor = EnhancedDailyProcessor()
        
        # Get recent reports
        recent_reports = get_recent_reports()
        
        # Get scheduler status
        status = {
            'scheduler_running': scheduler_running,
            'next_run': get_next_scheduled_run(),
            'last_report': get_last_report_info(),
            'report_count': len(recent_reports)
        }
        
        return render_template('automated_daily_dashboard.html', 
                             status=status, 
                             recent_reports=recent_reports)
    except Exception as e:
        logger.error(f"Error in auto daily dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('index'))

@automated_reports_bp.route('/generate-daily-report', methods=['POST'])
def generate_daily_report():
    """Generate daily report on demand"""
    try:
        target_date = request.form.get('date')
        if not target_date:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        processor = EnhancedDailyProcessor()
        result = processor.process_daily_report(target_date)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Daily report generated for {target_date}',
                'report_paths': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate daily report'
            }), 500
            
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@automated_reports_bp.route('/start-scheduler', methods=['POST'])
def start_scheduler():
    """Start automated daily report scheduler"""
    global scheduler_running, scheduler_thread
    
    try:
        if not scheduler_running:
            scheduler_running = True
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            
            logger.info("Daily report scheduler started")
            return jsonify({
                'success': True,
                'message': 'Automated daily reports started - will run at 6:00 PM daily'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Scheduler is already running'
            })
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to start scheduler: {str(e)}'
        }), 500

@automated_reports_bp.route('/stop-scheduler', methods=['POST'])
def stop_scheduler():
    """Stop automated daily report scheduler"""
    global scheduler_running
    
    try:
        scheduler_running = False
        schedule.clear()
        
        logger.info("Daily report scheduler stopped")
        return jsonify({
            'success': True,
            'message': 'Automated daily reports stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to stop scheduler: {str(e)}'
        }), 500

@automated_reports_bp.route('/scheduler-status')
def scheduler_status():
    """Get current scheduler status"""
    try:
        status = {
            'running': scheduler_running,
            'next_run': get_next_scheduled_run(),
            'last_report': get_last_report_info()
        }
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({
            'error': str(e)
        }), 500

def run_scheduler():
    """Background scheduler function"""
    global scheduler_running
    
    # Schedule daily report generation at 6:00 PM
    schedule.every().day.at("18:00").do(scheduled_daily_report)
    
    logger.info("Daily report scheduler configured for 6:00 PM daily")
    
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying

def scheduled_daily_report():
    """Function called by scheduler to generate daily report"""
    try:
        logger.info("Running scheduled daily report generation")
        processor = EnhancedDailyProcessor()
        result = processor.process_daily_report()
        
        if result:
            logger.info(f"Scheduled daily report completed: {result}")
        else:
            logger.error("Scheduled daily report failed")
            
    except Exception as e:
        logger.error(f"Error in scheduled daily report: {e}")

def get_recent_reports():
    """Get list of recent daily reports"""
    try:
        from pathlib import Path
        reports_dir = Path('./reports')
        
        if not reports_dir.exists():
            return []
        
        report_files = list(reports_dir.glob('daily_report_*.json'))
        report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        recent_reports = []
        for report_file in report_files[:10]:  # Last 10 reports
            try:
                import json
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                recent_reports.append({
                    'date': report_data.get('date', 'Unknown'),
                    'timestamp': report_data.get('timestamp', ''),
                    'total_drivers': report_data.get('summary', {}).get('total_drivers', 0),
                    'attendance_rate': report_data.get('summary', {}).get('attendance_rate', 0),
                    'alerts': len(report_data.get('alerts', [])),
                    'file_path': str(report_file)
                })
            except Exception as e:
                logger.error(f"Error reading report file {report_file}: {e}")
        
        return recent_reports
        
    except Exception as e:
        logger.error(f"Error getting recent reports: {e}")
        return []

def get_next_scheduled_run():
    """Get next scheduled run time"""
    try:
        if scheduler_running and schedule.jobs:
            next_run = schedule.next_run()
            if next_run:
                return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return None
    except Exception:
        return None

def get_last_report_info():
    """Get information about the last generated report"""
    try:
        recent_reports = get_recent_reports()
        if recent_reports:
            return recent_reports[0]
        return None
    except Exception:
        return None