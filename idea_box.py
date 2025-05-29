"""
TRAXOVO Idea Box - Feature Request System
Allows organization members to submit feature requests and suggestions
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

# Create blueprint
idea_box_bp = Blueprint('idea_box', __name__)

# Ensure ideas directory exists
IDEAS_DIR = 'ideas'
if not os.path.exists(IDEAS_DIR):
    os.makedirs(IDEAS_DIR)

def load_ideas():
    """Load all submitted ideas"""
    ideas = []
    if os.path.exists(f'{IDEAS_DIR}/ideas.json'):
        with open(f'{IDEAS_DIR}/ideas.json', 'r') as f:
            ideas = json.load(f)
    return sorted(ideas, key=lambda x: x['submitted_at'], reverse=True)

def save_idea(idea):
    """Save a new idea"""
    ideas = load_ideas()
    idea['id'] = len(ideas) + 1
    idea['submitted_at'] = datetime.now().isoformat()
    idea['status'] = 'submitted'
    idea['votes'] = 0
    idea['comments'] = []
    ideas.append(idea)
    
    with open(f'{IDEAS_DIR}/ideas.json', 'w') as f:
        json.dump(ideas, f, indent=2)
    
    return idea['id']

@idea_box_bp.route('/idea-box')
@login_required
def idea_box():
    """Display the idea submission and viewing interface"""
    ideas = load_ideas()
    return render_template('idea_box.html', ideas=ideas)

@idea_box_bp.route('/submit-idea', methods=['POST'])
@login_required
def submit_idea():
    """Submit a new feature idea"""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'feature')
        priority = request.form.get('priority', 'medium')
        
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('idea_box.idea_box'))
        
        idea = {
            'title': title,
            'description': description,
            'category': category,
            'priority': priority,
            'submitter': getattr(current_user, 'email', 'Anonymous'),
            'submitter_name': getattr(current_user, 'first_name', 'Anonymous User')
        }
        
        idea_id = save_idea(idea)
        flash(f'Idea #{idea_id} submitted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error submitting idea: {str(e)}', 'error')
    
    return redirect(url_for('idea_box.idea_box'))

@idea_box_bp.route('/vote-idea/<int:idea_id>', methods=['POST'])
@login_required
def vote_idea(idea_id):
    """Vote for an idea"""
    try:
        ideas = load_ideas()
        for idea in ideas:
            if idea['id'] == idea_id:
                idea['votes'] += 1
                break
        
        with open(f'{IDEAS_DIR}/ideas.json', 'w') as f:
            json.dump(ideas, f, indent=2)
        
        return jsonify({'success': True, 'votes': idea['votes']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@idea_box_bp.route('/api/ideas-summary')
@login_required
def ideas_summary():
    """Get summary statistics for ideas"""
    ideas = load_ideas()
    
    summary = {
        'total_ideas': len(ideas),
        'pending_ideas': len([i for i in ideas if i['status'] == 'submitted']),
        'implemented_ideas': len([i for i in ideas if i['status'] == 'implemented']),
        'top_categories': {}
    }
    
    # Count categories
    for idea in ideas:
        category = idea.get('category', 'other')
        summary['top_categories'][category] = summary['top_categories'].get(category, 0) + 1
    
    return jsonify(summary)

def register_idea_box(app):
    """Register the idea box blueprint"""
    app.register_blueprint(idea_box_bp)