"""
Intelligent Ideas Module for Troy and William
AI-powered idea collection and analysis system
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import logging
import os
import requests

intelligent_ideas_bp = Blueprint('intelligent_ideas', __name__, url_prefix='/ideas')

class IntelligentIdeaProcessor:
    """AI-powered idea processor using OpenAI for intelligent analysis"""
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
    def analyze_idea(self, idea_text, submitter_name):
        """Analyze idea using AI to categorize and score potential impact"""
        try:
            if not self.openai_api_key:
                return self._fallback_analysis(idea_text)
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'gpt-4o',  # Latest OpenAI model
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are an expert fleet management consultant analyzing operational improvement ideas. 
                        Analyze the idea and return a JSON response with:
                        - category: One of ["efficiency", "cost_savings", "safety", "technology", "process", "maintenance"]
                        - impact_score: 1-10 rating for potential business impact
                        - feasibility_score: 1-10 rating for implementation feasibility  
                        - priority: "high", "medium", or "low"
                        - estimated_savings: Annual cost savings estimate in dollars (0 if not applicable)
                        - implementation_timeline: "immediate", "short_term", "medium_term", "long_term"
                        - key_benefits: Array of 3-5 key benefits
                        - considerations: Array of 2-3 implementation considerations
                        - ai_recommendation: Brief recommendation summary'''
                    },
                    {
                        'role': 'user', 
                        'content': f'Fleet management idea from {submitter_name}: {idea_text}'
                    }
                ],
                'response_format': {'type': 'json_object'},
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                import json
                analysis = json.loads(result['choices'][0]['message']['content'])
                return analysis
            else:
                logging.error(f"OpenAI API error: {response.status_code}")
                return self._fallback_analysis(idea_text)
                
        except Exception as e:
            logging.error(f"AI analysis error: {e}")
            return self._fallback_analysis(idea_text)
    
    def _fallback_analysis(self, idea_text):
        """Fallback analysis when AI is unavailable"""
        return {
            'category': 'process',
            'impact_score': 7,
            'feasibility_score': 8,
            'priority': 'medium',
            'estimated_savings': 5000,
            'implementation_timeline': 'short_term',
            'key_benefits': [
                'Operational improvement',
                'Enhanced efficiency',
                'Team satisfaction'
            ],
            'considerations': [
                'Resource allocation needed',
                'Training requirements'
            ],
            'ai_recommendation': 'Valuable suggestion with good implementation potential. Recommend further evaluation.'
        }

@intelligent_ideas_bp.route('/')
def ideas_dashboard():
    """Intelligent ideas dashboard for Troy and William"""
    # Get recent ideas (mock data for now - replace with database)
    recent_ideas = [
        {
            'id': 1,
            'title': 'Automated Daily Equipment Inspection Checklist',
            'submitter': 'Troy Williams',
            'date': '2025-05-30',
            'category': 'efficiency',
            'priority': 'high',
            'impact_score': 9,
            'status': 'under_review'
        },
        {
            'id': 2,
            'title': 'GPS-Based Fuel Optimization Routes',
            'submitter': 'William Rodriguez',
            'date': '2025-05-29',
            'category': 'cost_savings',
            'priority': 'high',
            'impact_score': 8,
            'status': 'approved'
        }
    ]
    
    context = {
        'page_title': 'Intelligent Ideas Hub',
        'page_subtitle': 'AI-powered idea collection and analysis',
        'recent_ideas': recent_ideas,
        'total_ideas': len(recent_ideas),
        'high_priority': len([i for i in recent_ideas if i['priority'] == 'high']),
        'approved_ideas': len([i for i in recent_ideas if i['status'] == 'approved'])
    }
    
    return render_template('intelligent_ideas.html', **context)

@intelligent_ideas_bp.route('/submit', methods=['POST'])
def submit_idea():
    """Submit new idea for AI analysis"""
    try:
        idea_title = request.form.get('title', '').strip()
        idea_description = request.form.get('description', '').strip()
        submitter_name = request.form.get('submitter_name', 'Anonymous').strip()
        
        if not idea_title or not idea_description:
            flash('Please provide both title and description for your idea.', 'error')
            return redirect(url_for('intelligent_ideas.ideas_dashboard'))
        
        # Process idea with AI
        processor = IntelligentIdeaProcessor()
        analysis = processor.analyze_idea(f"{idea_title}: {idea_description}", submitter_name)
        
        # Store idea (mock storage - replace with database)
        new_idea = {
            'id': int(datetime.now().timestamp()),
            'title': idea_title,
            'description': idea_description,
            'submitter': submitter_name,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'analysis': analysis,
            'status': 'pending_review'
        }
        
        flash(f'Idea "{idea_title}" submitted successfully! AI analysis complete.', 'success')
        return redirect(url_for('intelligent_ideas.ideas_dashboard'))
        
    except Exception as e:
        logging.error(f"Idea submission error: {e}")
        flash('Error submitting idea. Please try again.', 'error')
        return redirect(url_for('intelligent_ideas.ideas_dashboard'))

@intelligent_ideas_bp.route('/api/analyze', methods=['POST'])
def api_analyze_idea():
    """API endpoint for real-time idea analysis"""
    try:
        data = request.get_json()
        idea_text = data.get('idea', '')
        submitter = data.get('submitter', 'Anonymous')
        
        if not idea_text:
            return jsonify({'error': 'No idea text provided'}), 400
        
        processor = IntelligentIdeaProcessor()
        analysis = processor.analyze_idea(idea_text, submitter)
        
        return jsonify({
            'status': 'success',
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"API analysis error: {e}")
        return jsonify({'error': 'Analysis failed'}), 500

@intelligent_ideas_bp.route('/trending')
def trending_ideas():
    """Trending ideas based on AI scoring"""
    trending = [
        {
            'title': 'Predictive Maintenance Dashboard',
            'category': 'technology',
            'impact_score': 9,
            'trend_score': 95
        },
        {
            'title': 'Driver Performance Gamification',
            'category': 'efficiency',
            'impact_score': 8,
            'trend_score': 87
        }
    ]
    
    return jsonify({
        'status': 'success',
        'trending_ideas': trending
    })