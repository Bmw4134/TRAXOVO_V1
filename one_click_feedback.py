"""
TRAXOVO One-Click Feedback Collector
Simple, fast feedback collection system for user experience improvement
"""

import os
import json
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

def save_feedback(feedback_data):
    """Save feedback to JSON file for analysis"""
    feedback_file = 'user_feedback.json'
    
    # Load existing feedback
    feedback_list = []
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r') as f:
                feedback_list = json.loads(f.read())
        except Exception as e:
            print(f"Error loading feedback file: {e}")
            feedback_list = []
    
    # Add new feedback
    feedback_entry = {
        'id': len(feedback_list) + 1,
        'user_id': current_user.id if current_user.is_authenticated else 'anonymous',
        'username': current_user.username if current_user.is_authenticated else 'anonymous',
        'timestamp': datetime.now().isoformat(),
        'feedback_type': feedback_data.get('type', 'general'),
        'rating': feedback_data.get('rating'),
        'message': feedback_data.get('message', ''),
        'page_url': feedback_data.get('page_url', ''),
        'browser_info': feedback_data.get('browser_info', ''),
        'feature_used': feedback_data.get('feature_used', ''),
        'status': 'new'
    }
    
    feedback_list.append(feedback_entry)
    
    # Save updated feedback
    try:
        with open(feedback_file, 'w') as f:
            f.write(json.dumps(feedback_list, indent=2))
        return True
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return False

def get_feedback_analytics():
    """Get feedback analytics for dashboard"""
    feedback_file = 'user_feedback.json'
    
    if not os.path.exists(feedback_file):
        return {
            'total_feedback': 0,
            'average_rating': 0,
            'rating_distribution': {},
            'recent_feedback': [],
            'feedback_by_type': {}
        }
    
    try:
        with open(feedback_file, 'r') as f:
            feedback_list = json.loads(f.read())
        
        if not feedback_list:
            return {
                'total_feedback': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'recent_feedback': [],
                'feedback_by_type': {}
            }
        
        # Calculate analytics
        total_feedback = len(feedback_list)
        ratings = [f['rating'] for f in feedback_list if f.get('rating')]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Rating distribution
        rating_distribution = {}
        for rating in ratings:
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        # Recent feedback (last 10)
        recent_feedback = sorted(feedback_list, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        # Feedback by type
        feedback_by_type = {}
        for feedback in feedback_list:
            feedback_type = feedback.get('feedback_type', 'general')
            feedback_by_type[feedback_type] = feedback_by_type.get(feedback_type, 0) + 1
        
        return {
            'total_feedback': total_feedback,
            'average_rating': round(average_rating, 1),
            'rating_distribution': rating_distribution,
            'recent_feedback': recent_feedback,
            'feedback_by_type': feedback_by_type
        }
        
    except Exception as e:
        print(f"Error analyzing feedback: {e}")
        return {
            'total_feedback': 0,
            'average_rating': 0,
            'rating_distribution': {},
            'recent_feedback': [],
            'feedback_by_type': {}
        }

# Route handlers for feedback system
@login_required
def feedback_collector():
    """Main feedback collector page"""
    return render_template('feedback_collector.html')

def submit_feedback():
    """Handle feedback submission"""
    if request.method == 'POST':
        feedback_data = request.get_json()
        
        if not feedback_data:
            return jsonify({'success': False, 'message': 'No feedback data received'})
        
        success = save_feedback(feedback_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Thank you for your feedback! We appreciate your input.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save feedback. Please try again.'
            })

@login_required
def feedback_analytics():
    """Feedback analytics dashboard"""
    if not current_user.has_access('admin'):
        return redirect(url_for('dashboard'))
    
    analytics = get_feedback_analytics()
    return render_template('feedback_analytics.html', analytics=analytics)

def quick_feedback():
    """Quick feedback submission via AJAX"""
    if request.method == 'POST':
        data = request.get_json()
        
        feedback_data = {
            'type': 'quick',
            'rating': data.get('rating'),
            'message': data.get('message', ''),
            'page_url': data.get('page_url', ''),
            'feature_used': data.get('feature_used', '')
        }
        
        success = save_feedback(feedback_data)
        
        return jsonify({
            'success': success,
            'message': 'Feedback saved!' if success else 'Error saving feedback'
        })

def get_feedback_widget_data():
    """Get data for feedback widget display"""
    analytics = get_feedback_analytics()
    return jsonify({
        'total_feedback': analytics['total_feedback'],
        'average_rating': analytics['average_rating'],
        'recent_count': len(analytics['recent_feedback'])
    })