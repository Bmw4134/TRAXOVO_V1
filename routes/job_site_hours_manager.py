"""
Job Site Hours Manager

Allows supervisors to configure and modify working hours for different job sites.
Integrates with authentic job site data from MTD files and supports flexible scheduling.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import json
import logging
from datetime import datetime, time
from pathlib import Path
from collections import defaultdict

job_site_hours_bp = Blueprint('job_site_hours', __name__)
logger = logging.getLogger(__name__)

# Default working hours configuration
DEFAULT_HOURS = {
    'start_time': '07:00',
    'end_time': '15:30',
    'break_start': '12:00',
    'break_end': '12:30',
    'overtime_threshold': 8.0,
    'weekend_rate': 1.5,
    'holiday_rate': 2.0
}

@job_site_hours_bp.route('/job-hours-manager')
def job_hours_dashboard():
    """Main dashboard for managing job site working hours"""
    try:
        # Load job site data from MTD files
        job_sites = load_job_sites_from_mtd()
        
        # Load current hours configuration
        hours_config = load_hours_configuration()
        
        # Get job site statistics
        site_stats = get_job_site_statistics()
        
        return render_template('job_site_hours_manager.html',
                             job_sites=job_sites,
                             hours_config=hours_config,
                             site_stats=site_stats,
                             default_hours=DEFAULT_HOURS)
        
    except Exception as e:
        logger.error(f"Error in job hours dashboard: {e}")
        flash('Error loading job site hours dashboard', 'error')
        return redirect(url_for('index'))

@job_site_hours_bp.route('/update-site-hours', methods=['POST'])
def update_site_hours():
    """Update working hours for a specific job site"""
    try:
        data = request.get_json()
        site_name = data.get('site_name')
        hours_config = data.get('hours_config')
        
        if not site_name or not hours_config:
            return jsonify({
                'success': False,
                'message': 'Missing site name or hours configuration'
            }), 400
        
        # Validate hours configuration
        validation_result = validate_hours_config(hours_config)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'message': f'Invalid configuration: {validation_result["error"]}'
            }), 400
        
        # Save updated configuration
        success = save_site_hours_config(site_name, hours_config)
        
        if success:
            logger.info(f"Updated hours for job site: {site_name}")
            return jsonify({
                'success': True,
                'message': f'Hours updated for {site_name}',
                'site_name': site_name,
                'config': hours_config
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating site hours: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@job_site_hours_bp.route('/get-site-hours/<site_name>')
def get_site_hours(site_name):
    """Get current hours configuration for a specific job site"""
    try:
        hours_config = load_hours_configuration()
        site_config = hours_config.get(site_name, DEFAULT_HOURS.copy())
        
        return jsonify({
            'success': True,
            'site_name': site_name,
            'config': site_config
        })
        
    except Exception as e:
        logger.error(f"Error getting site hours for {site_name}: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@job_site_hours_bp.route('/bulk-update-hours', methods=['POST'])
def bulk_update_hours():
    """Update hours for multiple job sites at once"""
    try:
        data = request.get_json()
        updates = data.get('updates', [])
        
        if not updates:
            return jsonify({
                'success': False,
                'message': 'No updates provided'
            }), 400
        
        results = []
        errors = []
        
        for update in updates:
            site_name = update.get('site_name')
            hours_config = update.get('hours_config')
            
            if not site_name or not hours_config:
                errors.append(f"Missing data for site: {site_name}")
                continue
            
            # Validate configuration
            validation_result = validate_hours_config(hours_config)
            if not validation_result['valid']:
                errors.append(f"{site_name}: {validation_result['error']}")
                continue
            
            # Save configuration
            success = save_site_hours_config(site_name, hours_config)
            if success:
                results.append(site_name)
            else:
                errors.append(f"Failed to save: {site_name}")
        
        return jsonify({
            'success': len(errors) == 0,
            'updated_sites': results,
            'errors': errors,
            'message': f'Updated {len(results)} sites' + (f', {len(errors)} errors' if errors else '')
        })
        
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@job_site_hours_bp.route('/copy-hours-template', methods=['POST'])
def copy_hours_template():
    """Copy hours configuration from one site to others"""
    try:
        data = request.get_json()
        source_site = data.get('source_site')
        target_sites = data.get('target_sites', [])
        
        if not source_site or not target_sites:
            return jsonify({
                'success': False,
                'message': 'Missing source site or target sites'
            }), 400
        
        # Get source configuration
        hours_config = load_hours_configuration()
        source_config = hours_config.get(source_site)
        
        if not source_config:
            return jsonify({
                'success': False,
                'message': f'No configuration found for {source_site}'
            }), 400
        
        # Apply to target sites
        updated_sites = []
        errors = []
        
        for target_site in target_sites:
            success = save_site_hours_config(target_site, source_config.copy())
            if success:
                updated_sites.append(target_site)
            else:
                errors.append(target_site)
        
        return jsonify({
            'success': len(errors) == 0,
            'updated_sites': updated_sites,
            'errors': errors,
            'message': f'Copied configuration to {len(updated_sites)} sites'
        })
        
    except Exception as e:
        logger.error(f"Error copying hours template: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@job_site_hours_bp.route('/reset-site-hours', methods=['POST'])
def reset_site_hours():
    """Reset job site hours to default configuration"""
    try:
        data = request.get_json()
        site_name = data.get('site_name')
        
        if not site_name:
            return jsonify({
                'success': False,
                'message': 'Site name required'
            }), 400
        
        success = save_site_hours_config(site_name, DEFAULT_HOURS.copy())
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Reset {site_name} to default hours',
                'config': DEFAULT_HOURS
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to reset configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resetting site hours: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

def load_job_sites_from_mtd():
    """Load authentic job sites from MTD data"""
    try:
        # Look for MTD files
        data_dir = Path('./data')
        temp_extract_dir = Path('./temp_extract')
        
        mtd_files = []
        for directory in [data_dir, temp_extract_dir]:
            if directory.exists():
                mtd_files.extend(list(directory.glob('*MTD*.json')))
        
        if not mtd_files:
            logger.warning("No MTD files found for job site loading")
            return []
        
        # Use the most recent MTD file
        latest_mtd = max(mtd_files, key=lambda x: x.stat().st_mtime)
        
        with open(latest_mtd, 'r') as f:
            mtd_data = json.load(f)
        
        # Extract unique job sites
        job_sites = set()
        
        # From daily records
        for date_records in mtd_data.get('daily_records', {}).values():
            for record in date_records:
                site = record.get('job_site')
                if site and site != 'Unknown':
                    job_sites.add(site)
        
        # From locations list
        for location in mtd_data.get('locations', []):
            if location and location != 'Unknown':
                job_sites.add(location)
        
        # Convert to sorted list with additional metadata
        job_sites_list = []
        for site in sorted(job_sites):
            job_sites_list.append({
                'name': site,
                'division': determine_division(site),
                'active': True,
                'driver_count': count_drivers_for_site(mtd_data, site)
            })
        
        logger.info(f"Loaded {len(job_sites_list)} job sites from MTD data")
        return job_sites_list
        
    except Exception as e:
        logger.error(f"Error loading job sites from MTD: {e}")
        return []

def determine_division(site_name):
    """Determine division based on job site name patterns"""
    site_upper = site_name.upper()
    
    if any(pattern in site_upper for pattern in ['HOU', 'HOUSTON', 'HARRIS']):
        return 'Houston'
    elif any(pattern in site_upper for pattern in ['WT', 'WEST', 'ODESSA', 'MIDLAND']):
        return 'West Texas'
    else:
        return 'DFW'

def count_drivers_for_site(mtd_data, site_name):
    """Count unique drivers assigned to a job site"""
    try:
        drivers = set()
        for date_records in mtd_data.get('daily_records', {}).values():
            for record in date_records:
                if record.get('job_site') == site_name:
                    driver = record.get('name')
                    if driver:
                        drivers.add(driver)
        return len(drivers)
    except Exception:
        return 0

def load_hours_configuration():
    """Load job site hours configuration from file"""
    try:
        config_file = Path('./config/job_site_hours.json')
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            return {}
            
    except Exception as e:
        logger.error(f"Error loading hours configuration: {e}")
        return {}

def save_site_hours_config(site_name, hours_config):
    """Save hours configuration for a specific job site"""
    try:
        config_dir = Path('./config')
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / 'job_site_hours.json'
        
        # Load existing configuration
        if config_file.exists():
            with open(config_file, 'r') as f:
                all_config = json.load(f)
        else:
            all_config = {}
        
        # Update configuration for this site
        all_config[site_name] = hours_config
        
        # Save updated configuration
        with open(config_file, 'w') as f:
            json.dump(all_config, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving site hours config: {e}")
        return False

def validate_hours_config(hours_config):
    """Validate hours configuration"""
    try:
        required_fields = ['start_time', 'end_time']
        
        for field in required_fields:
            if field not in hours_config:
                return {'valid': False, 'error': f'Missing {field}'}
        
        # Validate time format
        for time_field in ['start_time', 'end_time', 'break_start', 'break_end']:
            if time_field in hours_config:
                time_value = hours_config[time_field]
                if time_value and not validate_time_format(time_value):
                    return {'valid': False, 'error': f'Invalid time format for {time_field}'}
        
        # Validate start < end
        start_time = parse_time(hours_config['start_time'])
        end_time = parse_time(hours_config['end_time'])
        
        if start_time >= end_time:
            return {'valid': False, 'error': 'Start time must be before end time'}
        
        return {'valid': True}
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}

def validate_time_format(time_str):
    """Validate time string format (HH:MM)"""
    try:
        if not time_str:
            return True  # Optional fields can be empty
        
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        
        hour, minute = int(parts[0]), int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
        
    except Exception:
        return False

def parse_time(time_str):
    """Parse time string to minutes since midnight"""
    try:
        parts = time_str.split(':')
        hour, minute = int(parts[0]), int(parts[1])
        return hour * 60 + minute
    except Exception:
        return 0

def get_job_site_statistics():
    """Get statistics about job site usage"""
    try:
        # This would normally pull from your database
        # For now, return basic stats structure
        return {
            'total_sites': 0,
            'active_sites': 0,
            'configured_sites': 0,
            'drivers_across_sites': 0
        }
    except Exception:
        return {
            'total_sites': 0,
            'active_sites': 0,
            'configured_sites': 0,
            'drivers_across_sites': 0
        }