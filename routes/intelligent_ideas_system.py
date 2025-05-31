"""
TRAXOVO Intelligent Ideas Management System
AI-powered idea collection, consolidation, and development planning
"""

from flask import Blueprint, render_template, jsonify, request
import json
import os
from datetime import datetime
import openai
import logging

intelligent_ideas_bp = Blueprint('intelligent_ideas', __name__, url_prefix='/ideas')

# Initialize OpenAI for intelligent idea processing
openai.api_key = os.environ.get('OPENAI_API_KEY')

@intelligent_ideas_bp.route('/')
def ideas_dashboard():
    """Intelligent Ideas Management Dashboard"""
    
    ideas = load_all_ideas()
    consolidated_ideas = get_consolidated_ideas()
    development_pipeline = get_development_pipeline()
    
    return render_template('intelligent_ideas_dashboard.html',
                         ideas=ideas,
                         consolidated_ideas=consolidated_ideas,
                         development_pipeline=development_pipeline,
                         page_title="Intelligent Ideas Hub")

@intelligent_ideas_bp.route('/api/submit-idea', methods=['POST'])
def api_submit_idea():
    """Submit new idea with AI processing"""
    
    try:
        data = request.get_json()
        idea_text = data.get('idea_text', '')
        submitter = data.get('submitter', 'Anonymous')
        
        if not idea_text:
            return jsonify({
                'success': False,
                'message': 'Idea text required'
            }), 400
        
        # AI-powered idea analysis
        ai_analysis = analyze_idea_with_ai(idea_text)
        
        # Create idea object
        idea = {
            'id': generate_idea_id(),
            'text': idea_text,
            'submitter': submitter,
            'timestamp': datetime.now().isoformat(),
            'ai_analysis': ai_analysis,
            'status': 'pending_review',
            'votes': 0,
            'similar_ideas': find_similar_ideas(idea_text),
            'development_estimate': ai_analysis.get('development_estimate', 'Unknown')
        }
        
        # Save idea
        save_idea(idea)
        
        # Check for consolidation opportunities
        consolidation_result = check_consolidation_opportunities(idea)
        
        return jsonify({
            'success': True,
            'idea_id': idea['id'],
            'ai_analysis': ai_analysis,
            'consolidation_opportunities': consolidation_result,
            'message': 'Idea submitted and analyzed successfully'
        })
        
    except Exception as e:
        logging.error(f"Error submitting idea: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@intelligent_ideas_bp.route('/api/vote-idea', methods=['POST'])
def api_vote_idea():
    """Vote on an idea"""
    
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        vote_type = data.get('vote_type', 'up')  # up or down
        
        result = update_idea_votes(idea_id, vote_type)
        
        return jsonify({
            'success': True,
            'new_vote_count': result['votes'],
            'message': f'Vote {vote_type} recorded'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@intelligent_ideas_bp.route('/api/consolidate-ideas', methods=['POST'])
def api_consolidate_ideas():
    """AI-powered idea consolidation"""
    
    try:
        data = request.get_json()
        idea_ids = data.get('idea_ids', [])
        
        if len(idea_ids) < 2:
            return jsonify({
                'success': False,
                'message': 'At least 2 ideas required for consolidation'
            }), 400
        
        # Load ideas
        ideas = [load_idea(idea_id) for idea_id in idea_ids]
        
        # AI-powered consolidation
        consolidated_idea = consolidate_ideas_with_ai(ideas)
        
        # Save consolidated idea
        save_consolidated_idea(consolidated_idea, idea_ids)
        
        return jsonify({
            'success': True,
            'consolidated_idea': consolidated_idea,
            'message': 'Ideas consolidated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@intelligent_ideas_bp.route('/api/generate-development-plan', methods=['POST'])
def api_generate_development_plan():
    """Generate AI-powered development plan"""
    
    try:
        data = request.get_json()
        idea_id = data.get('idea_id')
        
        idea = load_idea(idea_id)
        if not idea:
            return jsonify({
                'success': False,
                'message': 'Idea not found'
            }), 404
        
        # Generate comprehensive development plan
        development_plan = generate_development_plan_with_ai(idea)
        
        # Update idea with development plan
        idea['development_plan'] = development_plan
        idea['status'] = 'development_planned'
        save_idea(idea)
        
        return jsonify({
            'success': True,
            'development_plan': development_plan,
            'message': 'Development plan generated'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_idea_with_ai(idea_text):
    """Use AI to analyze and categorize ideas"""
    
    if not openai.api_key:
        return {
            'category': 'General',
            'priority': 'Medium',
            'feasibility': 'Unknown',
            'development_estimate': '2-4 weeks'
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert product manager analyzing feature ideas for TRAXOVO, an enterprise fleet management platform. Analyze the idea and respond with JSON containing: category, priority, feasibility, development_estimate, benefits, and potential_challenges."
                },
                {
                    "role": "user",
                    "content": f"Analyze this feature idea: {idea_text}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"AI analysis error: {e}")
        return {
            'category': 'General',
            'priority': 'Medium',
            'feasibility': 'Requires Analysis',
            'development_estimate': '2-4 weeks'
        }

def find_similar_ideas(idea_text):
    """Find similar existing ideas"""
    
    all_ideas = load_all_ideas()
    similar_ideas = []
    
    # Simple keyword matching for now
    idea_keywords = set(idea_text.lower().split())
    
    for existing_idea in all_ideas:
        existing_keywords = set(existing_idea['text'].lower().split())
        similarity = len(idea_keywords.intersection(existing_keywords)) / len(idea_keywords.union(existing_keywords))
        
        if similarity > 0.3:  # 30% similarity threshold
            similar_ideas.append({
                'id': existing_idea['id'],
                'text': existing_idea['text'][:100] + '...',
                'similarity': round(similarity * 100, 1)
            })
    
    return similar_ideas[:5]  # Top 5 similar ideas

def consolidate_ideas_with_ai(ideas):
    """Use AI to consolidate multiple similar ideas"""
    
    if not openai.api_key:
        return {
            'consolidated_text': f"Consolidated idea from {len(ideas)} suggestions",
            'key_features': ['Feature 1', 'Feature 2'],
            'priority': 'High'
        }
    
    try:
        ideas_text = "\n".join([f"{i+1}. {idea['text']}" for i, idea in enumerate(ideas)])
        
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": "You are consolidating multiple similar feature ideas into one comprehensive suggestion. Respond with JSON containing: consolidated_text, key_features (array), priority, and combined_benefits."
                },
                {
                    "role": "user",
                    "content": f"Consolidate these similar ideas:\n{ideas_text}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"AI consolidation error: {e}")
        return {
            'consolidated_text': f"Consolidated idea from {len(ideas)} suggestions",
            'key_features': ['Combined functionality'],
            'priority': 'Medium'
        }

def generate_development_plan_with_ai(idea):
    """Generate comprehensive development plan"""
    
    if not openai.api_key:
        return {
            'phases': ['Planning', 'Development', 'Testing', 'Deployment'],
            'timeline': '4-6 weeks',
            'resources_needed': ['Developer', 'Tester'],
            'technical_requirements': ['Basic implementation']
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": "Create a detailed development plan for TRAXOVO fleet management features. Respond with JSON containing: phases (array), timeline, resources_needed, technical_requirements, risk_factors, and success_metrics."
                },
                {
                    "role": "user",
                    "content": f"Create development plan for: {idea['text']}\nAI Analysis: {json.dumps(idea['ai_analysis'])}"
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Development plan error: {e}")
        return {
            'phases': ['Analysis', 'Development', 'Testing', 'Release'],
            'timeline': '4-6 weeks',
            'resources_needed': ['Development Team'],
            'technical_requirements': ['Implementation required']
        }

def load_all_ideas():
    """Load all ideas from storage"""
    
    ideas_dir = 'ideas_storage'
    os.makedirs(ideas_dir, exist_ok=True)
    
    all_ideas = []
    ideas_file = os.path.join(ideas_dir, 'ideas.json')
    
    if os.path.exists(ideas_file):
        try:
            with open(ideas_file, 'r') as f:
                all_ideas = json.load(f)
        except:
            all_ideas = []
    
    return sorted(all_ideas, key=lambda x: x.get('votes', 0), reverse=True)

def save_idea(idea):
    """Save idea to storage"""
    
    ideas_dir = 'ideas_storage'
    os.makedirs(ideas_dir, exist_ok=True)
    
    ideas_file = os.path.join(ideas_dir, 'ideas.json')
    
    all_ideas = load_all_ideas()
    
    # Update existing or add new
    existing_index = next((i for i, existing in enumerate(all_ideas) if existing['id'] == idea['id']), None)
    
    if existing_index is not None:
        all_ideas[existing_index] = idea
    else:
        all_ideas.append(idea)
    
    with open(ideas_file, 'w') as f:
        json.dump(all_ideas, f, indent=2)

def load_idea(idea_id):
    """Load specific idea"""
    
    all_ideas = load_all_ideas()
    return next((idea for idea in all_ideas if idea['id'] == idea_id), None)

def generate_idea_id():
    """Generate unique idea ID"""
    
    return f"idea_{int(datetime.now().timestamp())}"

def check_consolidation_opportunities(new_idea):
    """Check if new idea can be consolidated with existing ones"""
    
    similar_ideas = new_idea.get('similar_ideas', [])
    
    if len(similar_ideas) >= 2:
        return {
            'should_consolidate': True,
            'similar_count': len(similar_ideas),
            'recommendation': 'Consider consolidating with similar ideas'
        }
    
    return {
        'should_consolidate': False,
        'similar_count': len(similar_ideas),
        'recommendation': 'Unique idea - no consolidation needed'
    }

def update_idea_votes(idea_id, vote_type):
    """Update idea votes"""
    
    idea = load_idea(idea_id)
    if not idea:
        raise ValueError("Idea not found")
    
    if vote_type == 'up':
        idea['votes'] = idea.get('votes', 0) + 1
    elif vote_type == 'down':
        idea['votes'] = max(0, idea.get('votes', 0) - 1)
    
    save_idea(idea)
    return idea

def get_consolidated_ideas():
    """Get all consolidated ideas"""
    
    consolidated_file = 'ideas_storage/consolidated_ideas.json'
    
    if os.path.exists(consolidated_file):
        try:
            with open(consolidated_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    return []

def save_consolidated_idea(consolidated_idea, original_idea_ids):
    """Save consolidated idea"""
    
    consolidated_ideas = get_consolidated_ideas()
    
    new_consolidated = {
        'id': generate_idea_id(),
        'consolidated_idea': consolidated_idea,
        'original_idea_ids': original_idea_ids,
        'created_at': datetime.now().isoformat(),
        'status': 'consolidated'
    }
    
    consolidated_ideas.append(new_consolidated)
    
    consolidated_file = 'ideas_storage/consolidated_ideas.json'
    os.makedirs('ideas_storage', exist_ok=True)
    
    with open(consolidated_file, 'w') as f:
        json.dump(consolidated_ideas, f, indent=2)

def get_development_pipeline():
    """Get development pipeline status"""
    
    all_ideas = load_all_ideas()
    
    pipeline = {
        'pending_review': [],
        'development_planned': [],
        'in_development': [],
        'testing': [],
        'deployed': []
    }
    
    for idea in all_ideas:
        status = idea.get('status', 'pending_review')
        if status in pipeline:
            pipeline[status].append(idea)
    
    return pipeline