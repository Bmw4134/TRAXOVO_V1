"""
TRAXOVO AGI-Enhanced Idea Box - Intelligent Feature Request System
AI-powered idea analysis, prioritization, and development planning
"""

import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
import logging

# Import OpenAI for AGI analysis
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
except ImportError:
    openai_client = None

logger = logging.getLogger(__name__)

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

def analyze_idea_with_agi(idea):
    """Analyze idea using AGI for intelligent categorization and prioritization"""
    if not openai_client:
        return {
            'category': idea.get('category', 'feature'),
            'priority': idea.get('priority', 'medium'),
            'feasibility': 'medium',
            'development_estimate': '2-4 weeks',
            'traxovo_alignment': 'high',
            'implementation_notes': 'Standard feature implementation'
        }
    
    try:
        traxovo_context = """
        TRAXOVO is a fleet management platform with:
        - 717 assets (614 active, 103 inactive) via GAUGE API
        - Equipment billing and invoicing 
        - Driver attendance tracking
        - Asset utilization analytics
        - Real-time fleet monitoring
        - Mobile-optimized interface
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an AI product analyst for TRAXOVO fleet management. 
                    
                    Context: {traxovo_context}
                    
                    Analyze feature ideas and respond with JSON containing:
                    - category: (ui_improvement, analytics, automation, integration, mobile, security, billing)
                    - priority: (critical, high, medium, low)
                    - feasibility: (high, medium, low)
                    - development_estimate: realistic timeframe
                    - traxovo_alignment: how well it fits existing platform
                    - implementation_notes: specific technical considerations
                    - similar_existing_features: any overlap with current capabilities"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this feature idea:\nTitle: {idea['title']}\nDescription: {idea['description']}"
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        
        analysis = json.loads(response.choices[0].message.content)
        return analysis
        
    except Exception as e:
        logger.error(f"AGI idea analysis failed: {e}")
        return {
            'category': 'feature',
            'priority': 'medium',
            'feasibility': 'medium',
            'development_estimate': '2-4 weeks',
            'traxovo_alignment': 'medium',
            'implementation_notes': f'Analysis unavailable: {str(e)}'
        }

def save_idea(idea):
    """Save a new idea with AGI analysis"""
    ideas = load_ideas()
    idea['id'] = len(ideas) + 1
    idea['submitted_at'] = datetime.now().isoformat()
    idea['status'] = 'submitted'
    idea['votes'] = 0
    idea['comments'] = []
    
    # Add AGI analysis
    idea['agi_analysis'] = analyze_idea_with_agi(idea)
    
    # Check for similar ideas
    idea['similar_ideas'] = find_similar_ideas(idea, ideas)
    
    ideas.append(idea)
    
    with open(f'{IDEAS_DIR}/ideas.json', 'w') as f:
        json.dump(ideas, f, indent=2)
    
    return idea['id']

def find_similar_ideas(new_idea, existing_ideas):
    """Find similar ideas using text analysis"""
    similar = []
    new_text = f"{new_idea['title']} {new_idea['description']}".lower()
    
    for existing in existing_ideas:
        existing_text = f"{existing['title']} {existing['description']}".lower()
        
        # Simple similarity check - could be enhanced with more sophisticated NLP
        common_words = set(new_text.split()) & set(existing_text.split())
        if len(common_words) >= 3:  # At least 3 common words
            similar.append({
                'id': existing['id'],
                'title': existing['title'],
                'similarity_score': len(common_words)
            })
    
    return similar[:3]  # Return top 3 similar ideas

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