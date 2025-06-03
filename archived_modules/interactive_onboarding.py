"""
TRAXOVO Interactive Onboarding Wizard
Step-by-step guided tour for new users to learn the fleet management system
"""

import os
import json
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user

# Onboarding steps configuration
ONBOARDING_STEPS = {
    'welcome': {
        'title': 'Welcome to TRAXOVO',
        'description': 'Your comprehensive fleet management solution',
        'content': 'TRAXOVO helps you manage 570 fleet assets, track $66,400 in monthly savings, and optimize operations across your entire fleet.',
        'action': 'Get Started',
        'next': 'dashboard_overview'
    },
    'dashboard_overview': {
        'title': 'Executive Dashboard',
        'description': 'Your fleet at a glance',
        'content': 'The main dashboard shows real-time fleet metrics, including 566 GPS-enabled assets, active drivers, and performance indicators.',
        'highlight': '.metric-card',
        'action': 'Continue',
        'next': 'asset_management'
    },
    'asset_management': {
        'title': 'Asset Management',
        'description': 'Track and manage your equipment',
        'content': 'Monitor individual assets including 180 pickup trucks, 32 excavators, and 13 air compressors. View utilization rates and maintenance schedules.',
        'highlight': '.asset-card',
        'action': 'Next',
        'next': 'cost_savings'
    },
    'cost_savings': {
        'title': 'Cost Intelligence',
        'description': 'Monitor your savings and efficiency',
        'content': 'Track monthly savings of $66,400 through rental reduction ($35,000), maintenance optimization ($13,340), and fuel intelligence ($14,260).',
        'highlight': '.savings-metric',
        'action': 'Continue',
        'next': 'customization'
    },
    'customization': {
        'title': 'Personalization Features',
        'description': 'Make TRAXOVO your own',
        'content': 'Customize your experience with widget dashboards, mood-based themes, and personalized layouts to match your workflow.',
        'highlight': '.widget-dashboard',
        'action': 'Explore',
        'next': 'feedback'
    },
    'feedback': {
        'title': 'Share Your Experience',
        'description': 'Help us improve TRAXOVO',
        'content': 'Use the feedback system to share suggestions, report issues, or rate features. Your input helps us enhance the platform.',
        'highlight': '.feedback-toggle',
        'action': 'Continue',
        'next': 'completion'
    },
    'completion': {
        'title': 'You\'re All Set!',
        'description': 'Welcome to efficient fleet management',
        'content': 'You\'re now ready to manage your fleet with TRAXOVO. Explore the features, customize your workspace, and optimize your operations.',
        'action': 'Start Managing',
        'next': None
    }
}

def save_onboarding_progress(user_id, step, completed=False):
    """Save user's onboarding progress"""
    progress_file = 'onboarding_progress.json'
    
    # Load existing progress
    progress = {}
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.loads(f.read())
        except Exception as e:
            print(f"Error loading onboarding progress: {e}")
            progress = {}
    
    # Update user progress
    if user_id not in progress:
        progress[user_id] = {
            'started': datetime.now().isoformat(),
            'steps_completed': [],
            'current_step': 'welcome',
            'completed': False
        }
    
    progress[user_id]['current_step'] = step
    progress[user_id]['last_activity'] = datetime.now().isoformat()
    
    if completed:
        progress[user_id]['completed'] = True
        progress[user_id]['completed_date'] = datetime.now().isoformat()
    
    if step not in progress[user_id]['steps_completed']:
        progress[user_id]['steps_completed'].append(step)
    
    # Save updated progress
    try:
        with open(progress_file, 'w') as f:
            f.write(json.dumps(progress, indent=2))
        return True
    except Exception as e:
        print(f"Error saving onboarding progress: {e}")
        return False

def get_onboarding_progress(user_id):
    """Get user's onboarding progress"""
    progress_file = 'onboarding_progress.json'
    
    if not os.path.exists(progress_file):
        return None
    
    try:
        with open(progress_file, 'r') as f:
            progress = json.loads(f.read())
        return progress.get(user_id)
    except Exception as e:
        print(f"Error loading onboarding progress: {e}")
        return None

def should_show_onboarding(user_id):
    """Check if user should see onboarding"""
    progress = get_onboarding_progress(user_id)
    
    if not progress:
        return True
    
    return not progress.get('completed', False)

def get_onboarding_analytics():
    """Get onboarding completion analytics"""
    progress_file = 'onboarding_progress.json'
    
    if not os.path.exists(progress_file):
        return {
            'total_users': 0,
            'completed_users': 0,
            'completion_rate': 0,
            'most_common_exit': 'welcome',
            'average_steps': 0
        }
    
    try:
        with open(progress_file, 'r') as f:
            progress = json.loads(f.read())
        
        total_users = len(progress)
        completed_users = sum(1 for p in progress.values() if p.get('completed', False))
        completion_rate = (completed_users / total_users * 100) if total_users > 0 else 0
        
        # Find most common exit point
        exit_points = {}
        total_steps = 0
        
        for user_progress in progress.values():
            current_step = user_progress.get('current_step', 'welcome')
            if not user_progress.get('completed', False):
                exit_points[current_step] = exit_points.get(current_step, 0) + 1
            
            total_steps += len(user_progress.get('steps_completed', []))
        
        most_common_exit = max(exit_points.items(), key=lambda x: x[1])[0] if exit_points else 'welcome'
        average_steps = total_steps / total_users if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'completed_users': completed_users,
            'completion_rate': round(completion_rate, 1),
            'most_common_exit': most_common_exit,
            'average_steps': round(average_steps, 1)
        }
        
    except Exception as e:
        print(f"Error analyzing onboarding data: {e}")
        return {
            'total_users': 0,
            'completed_users': 0,
            'completion_rate': 0,
            'most_common_exit': 'welcome',
            'average_steps': 0
        }

# Route handlers
@login_required
def onboarding_wizard():
    """Main onboarding wizard interface"""
    # Check if user should see onboarding
    if not should_show_onboarding(current_user.id):
        return redirect(url_for('dashboard'))
    
    # Get user's current progress
    progress = get_onboarding_progress(current_user.id)
    current_step = progress['current_step'] if progress else 'welcome'
    
    # Get step information
    step_info = ONBOARDING_STEPS.get(current_step, ONBOARDING_STEPS['welcome'])
    
    return render_template('onboarding_wizard.html', 
                         step=current_step,
                         step_info=step_info,
                         steps=ONBOARDING_STEPS,
                         progress=progress)

def update_onboarding_step():
    """Update user's onboarding step"""
    if request.method == 'POST':
        data = request.get_json()
        step = data.get('step')
        completed = data.get('completed', False)
        
        if step not in ONBOARDING_STEPS:
            return jsonify({'success': False, 'message': 'Invalid step'})
        
        success = save_onboarding_progress(current_user.id, step, completed)
        
        # Get next step info
        next_step = ONBOARDING_STEPS[step].get('next')
        next_step_info = ONBOARDING_STEPS.get(next_step) if next_step else None
        
        return jsonify({
            'success': success,
            'current_step': step,
            'next_step': next_step,
            'next_step_info': next_step_info,
            'completed': completed
        })

@login_required
def skip_onboarding():
    """Skip onboarding wizard"""
    save_onboarding_progress(current_user.id, 'completion', True)
    return jsonify({'success': True, 'redirectUrl': '/dashboard'})

@login_required
def restart_onboarding():
    """Restart onboarding from beginning"""
    save_onboarding_progress(current_user.id, 'welcome', False)
    return jsonify({'success': True, 'redirectUrl': '/onboarding'})

@login_required
def onboarding_analytics():
    """Onboarding analytics for administrators"""
    if not current_user.has_access('admin'):
        return redirect(url_for('dashboard'))
    
    analytics = get_onboarding_analytics()
    return render_template('onboarding_analytics.html', analytics=analytics)

def check_onboarding_status():
    """Check if current user needs onboarding"""
    if not current_user.is_authenticated:
        return jsonify({'needs_onboarding': False})
    
    needs_onboarding = should_show_onboarding(current_user.id)
    progress = get_onboarding_progress(current_user.id)
    
    return jsonify({
        'needs_onboarding': needs_onboarding,
        'current_step': progress['current_step'] if progress else 'welcome',
        'steps_completed': progress['steps_completed'] if progress else []
    })

def get_onboarding_tour_data():
    """Get tour data for guided tour overlay"""
    return jsonify({
        'steps': ONBOARDING_STEPS,
        'user_progress': get_onboarding_progress(current_user.id) if current_user.is_authenticated else None
    })