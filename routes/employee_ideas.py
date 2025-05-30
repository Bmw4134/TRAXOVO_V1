"""
Employee Ideas and Feedback System
Collect employee suggestions and feature requests across all TRAXOVO modules
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session
import hashlib

employee_ideas_bp = Blueprint('employee_ideas', __name__)

def save_employee_idea(idea_data):
    """Save employee idea to persistent storage"""
    ideas_file = 'data_cache/employee_ideas.json'
    
    # Load existing ideas
    ideas = []
    if os.path.exists(ideas_file):
        try:
            with open(ideas_file, 'r') as f:
                ideas = json.load(f)
        except:
            ideas = []
    
    # Add new idea
    idea_data['id'] = hashlib.md5(f"{idea_data['title']}_{idea_data['timestamp']}".encode()).hexdigest()[:8]
    idea_data['status'] = 'submitted'
    idea_data['admin_response'] = ''
    ideas.append(idea_data)
    
    # Keep last 500 ideas
    ideas = ideas[-500:]
    
    # Save back to file
    try:
        os.makedirs('data_cache', exist_ok=True)
        with open(ideas_file, 'w') as f:
            json.dump(ideas, f, indent=2)
    except Exception as e:
        print(f"Error saving idea: {e}")
    
    return idea_data

def get_employee_ideas():
    """Get all employee ideas"""
    ideas_file = 'data_cache/employee_ideas.json'
    if os.path.exists(ideas_file):
        try:
            with open(ideas_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def categorize_ideas():
    """Categorize ideas by module and priority"""
    ideas = get_employee_ideas()
    categories = {
        'fleet_management': [],
        'billing_finance': [],
        'attendance_workforce': [],
        'reporting_analytics': [],
        'ui_ux': [],
        'general': []
    }
    
    priority_counts = {'high': 0, 'medium': 0, 'low': 0}
    
    for idea in ideas:
        category = idea.get('category', 'general')
        if category in categories:
            categories[category].append(idea)
        else:
            categories['general'].append(idea)
        
        priority = idea.get('priority', 'medium')
        if priority in priority_counts:
            priority_counts[priority] += 1
    
    return categories, priority_counts

@employee_ideas_bp.route('/employee-ideas')
def employee_ideas_portal():
    """Employee ideas submission portal"""
    categories, priority_counts = categorize_ideas()
    recent_ideas = get_employee_ideas()[-10:]  # Last 10 ideas
    
    context = {
        'page_title': 'Employee Ideas Portal',
        'categories': categories,
        'priority_counts': priority_counts,
        'recent_ideas': recent_ideas,
        'total_ideas': len(get_employee_ideas()),
        'employee_name': session.get('employee_name', ''),
        'traxovo_modules': [
            'Executive Dashboard',
            'Fleet Map & GPS Tracking',
            'Billing & Financial Analysis',
            'Attendance & Workforce',
            'Asset Management',
            'Predictive Analytics',
            'Project Accountability',
            'Cost Savings Tools',
            'Reporting & Export',
            'User Interface & Navigation'
        ]
    }
    
    return render_template('employee_ideas_portal.html', **context)

@employee_ideas_bp.route('/admin/ideas-dashboard')
def admin_ideas_dashboard():
    """Admin dashboard for reviewing employee ideas"""
    categories, priority_counts = categorize_ideas()
    all_ideas = get_employee_ideas()
    
    # Sort by timestamp (newest first)
    all_ideas.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Categorize by status
    status_counts = {'submitted': 0, 'under_review': 0, 'implemented': 0, 'rejected': 0}
    for idea in all_ideas:
        status = idea.get('status', 'submitted')
        if status in status_counts:
            status_counts[status] += 1
    
    context = {
        'page_title': 'Employee Ideas Management',
        'all_ideas': all_ideas,
        'categories': categories,
        'priority_counts': priority_counts,
        'status_counts': status_counts,
        'total_ideas': len(all_ideas),
        'high_priority_ideas': [idea for idea in all_ideas if idea.get('priority') == 'high']
    }
    
    return render_template('admin_ideas_dashboard.html', **context)

@employee_ideas_bp.route('/api/submit-idea', methods=['POST'])
def submit_idea():
    """API to submit employee idea"""
    data = request.get_json()
    
    required_fields = ['title', 'description', 'category']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create idea record
    idea_data = {
        'title': data['title'].strip(),
        'description': data['description'].strip(),
        'category': data['category'],
        'priority': data.get('priority', 'medium'),
        'module': data.get('module', ''),
        'employee_name': data.get('employee_name', '').strip(),
        'employee_email': data.get('employee_email', '').strip(),
        'expected_benefit': data.get('expected_benefit', '').strip(),
        'implementation_effort': data.get('implementation_effort', 'medium'),
        'timestamp': datetime.now().isoformat(),
        'ip_address': request.remote_addr
    }
    
    # Save idea
    saved_idea = save_employee_idea(idea_data)
    
    # Store employee name in session for future submissions
    if idea_data['employee_name']:
        session['employee_name'] = idea_data['employee_name']
    
    return jsonify({
        'success': True,
        'idea': saved_idea,
        'message': 'Your idea has been submitted successfully!'
    })

@employee_ideas_bp.route('/api/update-idea-status', methods=['POST'])
def update_idea_status():
    """API to update idea status (admin only)"""
    data = request.get_json()
    
    idea_id = data.get('idea_id')
    new_status = data.get('status')
    admin_response = data.get('admin_response', '')
    
    if not idea_id or not new_status:
        return jsonify({'error': 'Missing idea ID or status'}), 400
    
    # Load and update ideas
    ideas = get_employee_ideas()
    updated = False
    
    for idea in ideas:
        if idea.get('id') == idea_id:
            idea['status'] = new_status
            idea['admin_response'] = admin_response
            idea['admin_updated'] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        # Save updated ideas
        try:
            with open('data_cache/employee_ideas.json', 'w') as f:
                json.dump(ideas, f, indent=2)
            return jsonify({'success': True, 'message': 'Idea status updated'})
        except Exception as e:
            return jsonify({'error': f'Failed to save update: {e}'}), 500
    else:
        return jsonify({'error': 'Idea not found'}), 404

@employee_ideas_bp.route('/api/ideas-analytics')
def ideas_analytics():
    """Analytics API for employee ideas"""
    ideas = get_employee_ideas()
    categories, priority_counts = categorize_ideas()
    
    # Monthly submission trends
    monthly_stats = {}
    for idea in ideas:
        timestamp = idea.get('timestamp', '')
        if timestamp:
            try:
                month_key = timestamp[:7]  # YYYY-MM format
                monthly_stats[month_key] = monthly_stats.get(month_key, 0) + 1
            except:
                pass
    
    # Employee participation
    employee_stats = {}
    for idea in ideas:
        employee = idea.get('employee_name', 'Anonymous')
        employee_stats[employee] = employee_stats.get(employee, 0) + 1
    
    # Top requested modules
    module_requests = {}
    for idea in ideas:
        module = idea.get('module', 'General')
        module_requests[module] = module_requests.get(module, 0) + 1
    
    return jsonify({
        'total_ideas': len(ideas),
        'categories': {k: len(v) for k, v in categories.items()},
        'priority_counts': priority_counts,
        'monthly_trends': monthly_stats,
        'employee_participation': employee_stats,
        'module_requests': module_requests,
        'recent_submissions': len([i for i in ideas if i.get('timestamp', '') > (datetime.now().replace(day=1)).isoformat()])
    })