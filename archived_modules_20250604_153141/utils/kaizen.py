"""
Kaizen Utility Functions

This module provides utility functions for the Kaizen system self-improvement module.
It calculates system health metrics, generates improvement suggestions, and
tracks the implementation of those suggestions.
"""

import os
import json
import time
import math
import logging
from datetime import datetime, timedelta
import random  # Used only for initial demo purposes

# Set up logging
logger = logging.getLogger(__name__)

# Constants
HEALTH_SCORE_FILE = 'data/health_scores.json'
SUGGESTIONS_FILE = 'data/improvement_suggestions.json'
MAPPINGS_FILE = 'data/employee_asset_mappings.json'

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def calculate_system_health(assets=None, file_path=None):
    """
    Calculate system health metrics based on asset data

    Args:
        assets (list): List of asset dictionaries
        file_path (str, optional): Path to save the health score

    Returns:
        dict: Health score data
    """
    # If no assets provided, try to load from file
    if not assets and not file_path:
        try:
            from utils import load_data
            assets = load_data('data/processed_data.json')
        except Exception as e:
            logger.error(f"Failed to load asset data: {e}")
            assets = []

    # Calculate data completeness
    data_completeness = calculate_data_completeness(assets)
    
    # Calculate file match rate
    file_match_rate = calculate_file_match_rate(assets)
    
    # Calculate asset assignment accuracy
    asset_assignment_accuracy = calculate_asset_assignment_accuracy(assets)
    
    # Calculate overall health score (weighted average)
    weights = {
        'data_completeness': 0.3,
        'file_match_rate': 0.4,
        'asset_assignment_accuracy': 0.3
    }
    
    overall_health_score = (
        data_completeness['score'] * weights['data_completeness'] +
        file_match_rate['score'] * weights['file_match_rate'] +
        asset_assignment_accuracy['score'] * weights['asset_assignment_accuracy']
    )
    
    # Prepare health score data
    health_score = {
        'timestamp': datetime.now().isoformat(),
        'overall_health_score': overall_health_score,
        'data_completeness': data_completeness,
        'file_match_rate': file_match_rate,
        'asset_assignment_accuracy': asset_assignment_accuracy
    }
    
    # Save health score to file
    save_path = file_path or HEALTH_SCORE_FILE
    save_health_score(health_score, save_path)
    
    # Generate improvement suggestions based on health score
    generate_suggestions_from_health(health_score)
    
    return health_score

def calculate_data_completeness(assets):
    """
    Calculate data completeness score

    Args:
        assets (list): List of asset dictionaries

    Returns:
        dict: Data completeness score and details
    """
    if not assets:
        return {
            'score': 0,
            'message': 'No asset data available.',
            'details': {
                'fields_with_data': 0,
                'total_fields': 0,
                'assets_with_employee': 0,
                'assets_with_location': 0,
                'assets_with_hours': 0,
                'total_assets': 0
            }
        }
    
    # Key fields to check
    key_fields = [
        'AssetIdentifier', 'Label', 'AssetCategory', 'AssetMake', 'AssetModel',
        'Location', 'District', 'Engine1Hours', 'Odometer'
    ]
    
    total_assets = len(assets)
    field_completeness = {}
    
    # Count assets with key data
    assets_with_employee = 0
    assets_with_location = 0
    assets_with_hours = 0
    
    # Check completeness for each field
    for field in key_fields:
        field_completeness[field] = 0
    
    for asset in assets:
        # Check each field
        for field in key_fields:
            if asset.get(field):
                field_completeness[field] += 1
        
        # Check special cases
        # Employee assignment (check if name in label or special field)
        label = asset.get('Label', '')
        if isinstance(label, str) and ('(' in label or ')' in label):
            assets_with_employee += 1
        
        # Location data
        if asset.get('Location'):
            assets_with_location += 1
        
        # Engine hours or odometer
        if asset.get('Engine1Hours') or asset.get('Odometer'):
            assets_with_hours += 1
    
    # Calculate average completeness
    total_field_checks = total_assets * len(key_fields)
    fields_with_data = sum(field_completeness.values())
    
    if total_field_checks > 0:
        completeness_pct = (fields_with_data / total_field_checks) * 100
    else:
        completeness_pct = 0
    
    # Adjust score based on special case completeness
    employee_pct = (assets_with_employee / total_assets) * 100 if total_assets > 0 else 0
    location_pct = (assets_with_location / total_assets) * 100 if total_assets > 0 else 0
    hours_pct = (assets_with_hours / total_assets) * 100 if total_assets > 0 else 0
    
    # Final score (weighted)
    score = (
        completeness_pct * 0.6 +
        employee_pct * 0.15 +
        location_pct * 0.15 +
        hours_pct * 0.1
    )
    
    # Create message based on score
    if score >= 90:
        message = "Excellent data completeness. Most assets have all required data."
    elif score >= 75:
        message = "Good data completeness, but some fields could be improved."
    elif score >= 60:
        message = "Moderate data completeness. Several key fields are missing data."
    else:
        message = "Poor data completeness. Critical data is missing for many assets."
    
    return {
        'score': score,
        'message': message,
        'details': {
            'fields_with_data': fields_with_data,
            'total_fields': total_field_checks,
            'assets_with_employee': assets_with_employee,
            'assets_with_location': assets_with_location,
            'assets_with_hours': assets_with_hours,
            'total_assets': total_assets
        }
    }

def calculate_file_match_rate(assets):
    """
    Calculate file match rate score

    Args:
        assets (list): List of asset dictionaries

    Returns:
        dict: File match rate score and details
    """
    # In a production scenario, this would calculate matches between
    # various data files (GPS data, billing data, job records, etc.)
    
    # For demo purposes, we'll simulate match rates
    if not assets:
        return {
            'score': 0,
            'message': 'No asset data available to calculate match rates.',
            'details': {
                'matched_records': 0,
                'total_records': 0,
                'billable_assets_matched': 0,
                'total_billable_assets': 0,
                'gps_records_matched': 0,
                'total_gps_records': 0,
                'cross_file_consistency_score': 0
            }
        }
    
    total_assets = len(assets)
    
    # Simulate match rates based on asset data quality
    # Higher quality data would likely have better match rates
    
    # Base rate influenced by asset data completeness
    completeness = sum(1 for a in assets if a.get('AssetIdentifier') and a.get('Label')) / total_assets if total_assets > 0 else 0
    
    # Simulate various match metrics
    total_records = total_assets * 3  # Each asset might appear in multiple files
    matched_records = int(total_records * (0.7 + (completeness * 0.2)))
    
    billable_assets = int(total_assets * 0.8)  # Assume 80% of assets are billable
    billable_matched = int(billable_assets * (0.75 + (completeness * 0.15)))
    
    gps_records = total_assets  # Assume each asset has a GPS record
    gps_matched = int(gps_records * (0.85 + (completeness * 0.1)))
    
    # Cross-file consistency (higher when match rates are higher)
    cross_file_score = 65 + (matched_records / total_records) * 25 if total_records > 0 else 60
    
    # Overall match rate score
    if total_records > 0:
        match_rate = (matched_records / total_records) * 100
    else:
        match_rate = 0
    
    # Adjust with weighted factors
    score = (
        match_rate * 0.5 +
        (billable_matched / billable_assets) * 100 * 0.3 if billable_assets > 0 else 0 +
        (gps_matched / gps_records) * 100 * 0.2 if gps_records > 0 else 0
    )
    
    # Create message based on score
    if score >= 90:
        message = "Excellent file match rate. Assets are consistently identified across systems."
    elif score >= 75:
        message = "Good match rate, but some asset records are inconsistent between files."
    elif score >= 60:
        message = "Moderate match rate. Several assets have mismatched or missing records."
    else:
        message = "Poor match rate. Many assets cannot be reconciled across different files."
    
    return {
        'score': score,
        'message': message,
        'details': {
            'matched_records': matched_records,
            'total_records': total_records,
            'billable_assets_matched': billable_matched,
            'total_billable_assets': billable_assets,
            'gps_records_matched': gps_matched,
            'total_gps_records': gps_records,
            'cross_file_consistency_score': cross_file_score
        }
    }

def calculate_asset_assignment_accuracy(assets):
    """
    Calculate asset assignment accuracy score

    Args:
        assets (list): List of asset dictionaries

    Returns:
        dict: Asset assignment accuracy score and details
    """
    # In production, this would use the actual asset-employee mapping accuracy
    # based on matched files, employee names, and assignment records
    
    if not assets:
        return {
            'score': 0,
            'message': 'No asset data available to calculate assignment accuracy.',
            'details': {
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'total_mappings': 0,
                'conflicting_assignments': 0
            }
        }
    
    employee_assets = []
    for asset in assets:
        label = asset.get('Label', '')
        if isinstance(label, str) and ('(' in label and ')' in label):
            # Extract employee name from label
            employee_name = label.split('(')[1].split(')')[0].strip()
            if employee_name and not any(x in employee_name.lower() for x in ['sold', 'open', 'shop']):
                employee_assets.append({
                    'asset_id': asset.get('AssetIdentifier'),
                    'asset_label': label,
                    'employee_name': employee_name
                })
    
    # Count mappings by confidence
    total_mappings = len(employee_assets)
    
    # In demo mode, simulate confidence levels
    # In production, this would use actual match confidence from the employee mapper
    high_confidence = int(total_mappings * 0.6)
    medium_confidence = int(total_mappings * 0.25)
    low_confidence = total_mappings - high_confidence - medium_confidence
    
    # Simulate conflicting assignments
    conflicting_assignments = int(total_mappings * 0.05)
    
    # Calculate score
    if len(assets) > 0:
        assignment_pct = total_mappings / len(assets) * 100
    else:
        assignment_pct = 0
    
    # Final score based on assignment percentage and confidence
    if total_mappings > 0:
        confidence_factor = (high_confidence * 1.0 + medium_confidence * 0.6 + low_confidence * 0.3) / total_mappings
    else:
        confidence_factor = 0
    
    # Adjust score based on data coverage and confidence
    score = assignment_pct * 0.7 + confidence_factor * 100 * 0.3
    if conflicting_assignments > 0:
        penalty = (conflicting_assignments / total_mappings) * 20 if total_mappings > 0 else 0
        score = max(0, score - penalty)
    
    # Create message based on score
    if score >= 90:
        message = "Excellent asset assignment tracking. Almost all assets are correctly mapped to employees."
    elif score >= 75:
        message = "Good assignment accuracy, but some employee mappings could be improved."
    elif score >= 60:
        message = "Moderate assignment accuracy. Several assets lack clear employee assignments."
    else:
        message = "Poor assignment accuracy. Many assets cannot be confidently mapped to employees."
    
    return {
        'score': score,
        'message': message,
        'details': {
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'total_mappings': total_mappings,
            'conflicting_assignments': conflicting_assignments
        }
    }

def save_health_score(health_score, file_path=None):
    """
    Save health score to file and maintain history

    Args:
        health_score (dict): Health score data
        file_path (str, optional): Path to save the health score

    Returns:
        bool: True if saved successfully, False otherwise
    """
    save_path = file_path or HEALTH_SCORE_FILE
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Load existing data if any
        history = []
        if os.path.exists(save_path):
            with open(save_path, 'r') as f:
                history = json.load(f)
        
        # Ensure history is a list
        if not isinstance(history, list):
            history = []
        
        # Add current score to history (keep last 30 days)
        history.append(health_score)
        history = history[-30:]
        
        # Save updated history
        with open(save_path, 'w') as f:
            json.dump(history, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save health score: {e}")
        return False

def get_latest_health_score():
    """
    Get the latest health score

    Returns:
        dict: Latest health score or default empty score
    """
    try:
        if os.path.exists(HEALTH_SCORE_FILE):
            with open(HEALTH_SCORE_FILE, 'r') as f:
                history = json.load(f)
                if history and isinstance(history, list):
                    return history[-1]
        
        # If no history or error, calculate a new score
        return calculate_system_health()
    except Exception as e:
        logger.error(f"Failed to get latest health score: {e}")
        
        # Return default empty score
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': 65,
            'data_completeness': {
                'score': 70,
                'message': 'No previous data available.',
                'details': {
                    'fields_with_data': 0,
                    'total_fields': 0,
                    'assets_with_employee': 0,
                    'assets_with_location': 0,
                    'assets_with_hours': 0,
                    'total_assets': 0
                }
            },
            'file_match_rate': {
                'score': 60,
                'message': 'No previous data available.',
                'details': {
                    'matched_records': 0,
                    'total_records': 0,
                    'billable_assets_matched': 0,
                    'total_billable_assets': 0,
                    'gps_records_matched': 0,
                    'total_gps_records': 0,
                    'cross_file_consistency_score': 0
                }
            },
            'asset_assignment_accuracy': {
                'score': 65,
                'message': 'No previous data available.',
                'details': {
                    'high_confidence': 0,
                    'medium_confidence': 0,
                    'low_confidence': 0,
                    'total_mappings': 0,
                    'conflicting_assignments': 0
                }
            }
        }

def generate_suggestions_from_health(health_score):
    """
    Generate improvement suggestions based on health score

    Args:
        health_score (dict): Health score data

    Returns:
        list: Generated improvement suggestions
    """
    suggestions = []
    
    # Data completeness suggestions
    if health_score['data_completeness']['score'] < 90:
        completeness = health_score['data_completeness']
        details = completeness['details']
        
        # Missing employee assignments
        if details['assets_with_employee'] / details['total_assets'] < 0.8 if details['total_assets'] > 0 else True:
            suggestions.append({
                'id': int(time.time() * 1000),
                'title': 'Improve Employee Assignment Tracking',
                'description': 'Several assets are missing employee assignments. Update asset labels to include employee names in parentheses.',
                'category': 'Data Completeness',
                'priority': 'High' if completeness['score'] < 70 else 'Medium',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
        
        # Missing location data
        if details['assets_with_location'] / details['total_assets'] < 0.9 if details['total_assets'] > 0 else True:
            suggestions.append({
                'id': int(time.time() * 1000) + 1,
                'title': 'Update Missing Location Data',
                'description': 'Location information is missing for some assets. Ensure all assets have a valid location assigned.',
                'category': 'Data Completeness',
                'priority': 'Medium',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
    
    # File match rate suggestions
    if health_score['file_match_rate']['score'] < 85:
        match_rate = health_score['file_match_rate']
        details = match_rate['details']
        
        # Improve asset ID consistency
        if details['matched_records'] / details['total_records'] < 0.85 if details['total_records'] > 0 else True:
            suggestions.append({
                'id': int(time.time() * 1000) + 2,
                'title': 'Standardize Asset Identifiers',
                'description': 'Asset IDs are inconsistent across files. Implement a standard format for asset identifiers in all systems.',
                'category': 'File Integration',
                'priority': 'High' if match_rate['score'] < 70 else 'Medium',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
        
        # Improve billing match
        if details['billable_assets_matched'] / details['total_billable_assets'] < 0.9 if details['total_billable_assets'] > 0 else True:
            suggestions.append({
                'id': int(time.time() * 1000) + 3,
                'title': 'Reconcile Billing Records',
                'description': 'Some billable assets cannot be matched to their billing records. Review and update billing data.',
                'category': 'Billing',
                'priority': 'High',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
    
    # Asset assignment suggestions
    if health_score['asset_assignment_accuracy']['score'] < 80:
        assignment = health_score['asset_assignment_accuracy']
        details = assignment['details']
        
        # Low confidence mappings
        if details['low_confidence'] > 5:
            suggestions.append({
                'id': int(time.time() * 1000) + 4,
                'title': 'Improve Low-Confidence Mappings',
                'description': f"There are {details['low_confidence']} asset-employee mappings with low confidence. Manually verify and correct these assignments.",
                'category': 'Asset Assignment',
                'priority': 'Medium',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
        
        # Conflicting assignments
        if details['conflicting_assignments'] > 0:
            suggestions.append({
                'id': int(time.time() * 1000) + 5,
                'title': 'Resolve Conflicting Asset Assignments',
                'description': f"Found {details['conflicting_assignments']} assets with conflicting employee assignments. Review and update records.",
                'category': 'Asset Assignment',
                'priority': 'High',
                'date_created': datetime.now().isoformat(),
                'implemented': False,
                'implemented_at': None
            })
    
    # General suggestions
    suggestions.append({
        'id': int(time.time() * 1000) + 6,
        'title': 'Schedule Regular Data Audits',
        'description': 'Implement weekly data audits to proactively identify and fix data quality issues.',
        'category': 'Process Improvement',
        'priority': 'Medium',
        'date_created': datetime.now().isoformat(),
        'implemented': False,
        'implemented_at': None
    })
    
    # Save the updated suggestions
    save_improvement_suggestions(suggestions)
    
    return suggestions

def save_improvement_suggestions(new_suggestions):
    """
    Save improvement suggestions to file

    Args:
        new_suggestions (list): New improvement suggestions

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(SUGGESTIONS_FILE), exist_ok=True)
        
        # Load existing suggestions if any
        existing_suggestions = []
        if os.path.exists(SUGGESTIONS_FILE):
            with open(SUGGESTIONS_FILE, 'r') as f:
                existing_suggestions = json.load(f)
        
        # Ensure existing_suggestions is a list
        if not isinstance(existing_suggestions, list):
            existing_suggestions = []
        
        # Get existing IDs to avoid duplicates
        existing_ids = {s['id'] for s in existing_suggestions}
        
        # Add new suggestions that don't already exist
        for suggestion in new_suggestions:
            if suggestion['id'] not in existing_ids:
                existing_suggestions.append(suggestion)
                existing_ids.add(suggestion['id'])
        
        # Save updated suggestions
        with open(SUGGESTIONS_FILE, 'w') as f:
            json.dump(existing_suggestions, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save improvement suggestions: {e}")
        return False

def get_improvement_suggestions(limit=100, implemented=False):
    """
    Get improvement suggestions

    Args:
        limit (int): Maximum number of suggestions to return
        implemented (bool): Whether to return implemented or pending suggestions

    Returns:
        list: Improvement suggestions
    """
    try:
        if os.path.exists(SUGGESTIONS_FILE):
            with open(SUGGESTIONS_FILE, 'r') as f:
                suggestions = json.load(f)
            
            # Filter by implementation status
            filtered = [s for s in suggestions if s.get('implemented', False) == implemented]
            
            # Sort by priority and date
            priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
            sorted_suggestions = sorted(
                filtered,
                key=lambda s: (
                    priority_order.get(s.get('priority'), 3),
                    s.get('date_created', ''), 
                    s.get('id', 0)
                )
            )
            
            return sorted_suggestions[:limit]
        
        # If file doesn't exist or error, generate some default suggestions
        if not implemented:
            # Only generate defaults for pending suggestions
            health_score = get_latest_health_score()
            return generate_suggestions_from_health(health_score)[:limit]
        
        return []
    except Exception as e:
        logger.error(f"Failed to get improvement suggestions: {e}")
        return []

def mark_suggestion_implemented(suggestion_id):
    """
    Mark a suggestion as implemented

    Args:
        suggestion_id (int): Suggestion ID

    Returns:
        bool: True if marked successfully, False otherwise
    """
    try:
        if os.path.exists(SUGGESTIONS_FILE):
            with open(SUGGESTIONS_FILE, 'r') as f:
                suggestions = json.load(f)
            
            # Find and update the suggestion
            for suggestion in suggestions:
                if suggestion.get('id') == suggestion_id:
                    suggestion['implemented'] = True
                    suggestion['implemented_at'] = datetime.now().isoformat()
                    
                    # Save updated suggestions
                    with open(SUGGESTIONS_FILE, 'w') as f:
                        json.dump(suggestions, f, indent=2)
                    
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Failed to mark suggestion as implemented: {e}")
        return False

def get_asset_employee_mappings(confidence='all', limit=100):
    """
    Get asset-employee mappings

    Args:
        confidence (str): 'all', 'high', 'medium', or 'low'
        limit (int): Maximum number of mappings to return

    Returns:
        list: Asset-employee mappings
    """
    try:
        # Check if we have real mappings from the smart matcher
        if os.path.exists(MAPPINGS_FILE):
            with open(MAPPINGS_FILE, 'r') as f:
                mappings = json.load(f)
            
            # Filter by confidence level
            if confidence != 'all':
                confidence_thresholds = {
                    'high': 0.8,
                    'medium': 0.5,
                    'low': 0.0
                }
                
                if confidence == 'high':
                    filtered = [m for m in mappings if m.get('confidence', 0) >= confidence_thresholds['high']]
                elif confidence == 'medium':
                    filtered = [m for m in mappings if confidence_thresholds['medium'] <= m.get('confidence', 0) < confidence_thresholds['high']]
                elif confidence == 'low':
                    filtered = [m for m in mappings if m.get('confidence', 0) < confidence_thresholds['medium']]
                else:
                    filtered = mappings
            else:
                filtered = mappings
            
            # Sort by confidence (descending)
            sorted_mappings = sorted(
                filtered,
                key=lambda m: m.get('confidence', 0),
                reverse=True
            )
            
            return sorted_mappings[:limit]
        
        # If no real mappings, generate sample ones
        return generate_sample_mappings(limit)
    except Exception as e:
        logger.error(f"Failed to get asset-employee mappings: {e}")
        return generate_sample_mappings(limit)

def generate_sample_mappings(limit=100):
    """
    Generate sample asset-employee mappings for demo purposes

    Args:
        limit (int): Maximum number of mappings to return

    Returns:
        list: Sample asset-employee mappings
    """
    # Sample asset types and prefixes
    asset_types = [
        {'prefix': 'PT', 'description': 'Pickup Truck'},
        {'prefix': 'DT', 'description': 'Dump Truck'},
        {'prefix': 'EX', 'description': 'Excavator'},
        {'prefix': 'BH', 'description': 'Backhoe'},
        {'prefix': 'LB', 'description': 'Loader Backhoe'},
        {'prefix': 'SS', 'description': 'Skid Steer'},
        {'prefix': 'D', 'description': 'Dozer'},
        {'prefix': 'LP', 'description': 'Light Plant'},
        {'prefix': 'WL', 'description': 'Wheel Loader'}
    ]
    
    # Sample employee names
    first_names = ['John', 'Robert', 'Michael', 'David', 'James', 'Mary', 'Patricia', 'Linda', 'Elizabeth', 'Susan', 
                   'Jose', 'Carlos', 'Juan', 'Maria', 'Luis', 'Alejandro', 'Miguel', 'Jorge', 'Pedro', 'Rosa']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                  'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
    
    # Generate random mappings
    mappings = []
    for i in range(min(100, limit)):
        # Generate asset ID
        asset_type = random.choice(asset_types)
        asset_num = random.randint(1, 50)
        asset_id = f"{asset_type['prefix']}-{asset_num:02d}"
        
        # Generate employee name
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        employee_name = f"{first_name} {last_name}"
        
        # Generate confidence level (weighted toward high)
        confidence_roll = random.random()
        if confidence_roll < 0.6:  # 60% chance of high confidence
            confidence = round(random.uniform(0.8, 0.98), 2)
        elif confidence_roll < 0.85:  # 25% chance of medium confidence
            confidence = round(random.uniform(0.5, 0.79), 2)
        else:  # 15% chance of low confidence
            confidence = round(random.uniform(0.1, 0.49), 2)
        
        # Match pattern (how the match was determined)
        match_patterns = ['Label Pattern', 'Billing Record', 'GPS Analysis', 'Timesheet', 'Manual Assignment']
        match_pattern = random.choice(match_patterns)
        
        # Last verified
        days_ago = random.randint(0, 30)
        last_verified = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        mappings.append({
            'asset_id': asset_id,
            'asset_type': asset_type['description'],
            'employee_name': employee_name,
            'confidence': confidence,
            'match_pattern': match_pattern,
            'last_verified': last_verified,
            'history': []
        })
    
    # Sort by confidence (descending)
    sorted_mappings = sorted(mappings, key=lambda m: m['confidence'], reverse=True)
    
    return sorted_mappings[:limit]