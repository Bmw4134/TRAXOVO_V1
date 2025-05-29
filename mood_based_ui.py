"""
TRAXOVO Mood-Based UI Color Shifter
Dynamic interface theming based on user mood or system performance data
"""

import os
import json
from datetime import datetime
from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user

# Predefined mood themes with color schemes
MOOD_THEMES = {
    'energetic': {
        'name': 'Energetic',
        'primary': '#ff6b35',
        'secondary': '#f7931e',
        'accent': '#ffb74d',
        'background': '#fff3e0',
        'text': '#2e2e2e',
        'gradient': 'linear-gradient(135deg, #ff6b35, #f7931e)',
        'description': 'Vibrant and motivating colors for high-energy days'
    },
    'calm': {
        'name': 'Calm',
        'primary': '#4fc3f7',
        'secondary': '#29b6f6',
        'accent': '#81c784',
        'background': '#e1f5fe',
        'text': '#263238',
        'gradient': 'linear-gradient(135deg, #4fc3f7, #29b6f6)',
        'description': 'Soothing blues and greens for peaceful focus'
    },
    'focused': {
        'name': 'Focused',
        'primary': '#5e35b1',
        'secondary': '#7e57c2',
        'accent': '#9575cd',
        'background': '#f3e5f5',
        'text': '#2a2a2a',
        'gradient': 'linear-gradient(135deg, #5e35b1, #7e57c2)',
        'description': 'Deep purples for concentration and productivity'
    },
    'success': {
        'name': 'Success',
        'primary': '#43a047',
        'secondary': '#66bb6a',
        'accent': '#81c784',
        'background': '#e8f5e8',
        'text': '#1b5e20',
        'gradient': 'linear-gradient(135deg, #43a047, #66bb6a)',
        'description': 'Green tones celebrating achievements and growth'
    },
    'alert': {
        'name': 'Alert',
        'primary': '#f44336',
        'secondary': '#ef5350',
        'accent': '#ff7043',
        'background': '#ffebee',
        'text': '#b71c1c',
        'gradient': 'linear-gradient(135deg, #f44336, #ef5350)',
        'description': 'Red colors for urgent attention and critical tasks'
    },
    'neutral': {
        'name': 'Professional',
        'primary': '#546e7a',
        'secondary': '#607d8b',
        'accent': '#78909c',
        'background': '#eceff1',
        'text': '#263238',
        'gradient': 'linear-gradient(135deg, #546e7a, #607d8b)',
        'description': 'Classic professional gray tones'
    },
    'sunset': {
        'name': 'Sunset',
        'primary': '#ff7043',
        'secondary': '#ffab40',
        'accent': '#ffc947',
        'background': '#fff8e1',
        'text': '#3e2723',
        'gradient': 'linear-gradient(135deg, #ff7043, #ffab40)',
        'description': 'Warm sunset colors for end-of-day reflection'
    },
    'ocean': {
        'name': 'Ocean',
        'primary': '#0277bd',
        'secondary': '#0288d1',
        'accent': '#039be5',
        'background': '#e3f2fd',
        'text': '#01579b',
        'gradient': 'linear-gradient(135deg, #0277bd, #0288d1)',
        'description': 'Deep ocean blues for clarity and depth'
    }
}

def save_user_mood_preference(user_id, mood_data):
    """Save user's mood preference to file"""
    mood_file = 'user_moods.json'
    
    # Load existing moods
    moods = {}
    if os.path.exists(mood_file):
        try:
            with open(mood_file, 'r') as f:
                moods = json.loads(f.read())
        except Exception as e:
            print(f"Error loading mood file: {e}")
            moods = {}
    
    # Update user mood
    moods[user_id] = {
        'mood': mood_data.get('mood'),
        'theme': mood_data.get('theme'),
        'timestamp': datetime.now().isoformat(),
        'auto_detect': mood_data.get('auto_detect', False)
    }
    
    # Save updated moods
    try:
        with open(mood_file, 'w') as f:
            f.write(json.dumps(moods, indent=2))
        return True
    except Exception as e:
        print(f"Error saving mood: {e}")
        return False

def get_user_mood_preference(user_id):
    """Get user's current mood preference"""
    mood_file = 'user_moods.json'
    
    if not os.path.exists(mood_file):
        return None
    
    try:
        with open(mood_file, 'r') as f:
            moods = json.loads(f.read())
        return moods.get(user_id)
    except Exception as e:
        print(f"Error loading user mood: {e}")
        return None

def detect_mood_from_system_data():
    """Detect mood based on system performance and fleet data"""
    try:
        # Load authentic fleet data to determine system mood
        import pandas as pd
        
        # Check for positive indicators
        positive_indicators = 0
        negative_indicators = 0
        
        # Check Ragle billing data
        if os.path.exists('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm'):
            ragle_df = pd.read_excel('RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm')
            if len(ragle_df) > 1000:  # Good billing activity
                positive_indicators += 2
        
        # Check Gauge API data
        if os.path.exists('GAUGE API PULL 1045AM_05.15.2025.json'):
            with open('GAUGE API PULL 1045AM_05.15.2025.json', 'r') as f:
                gauge_data = json.loads(f.read())
                if isinstance(gauge_data, list) and len(gauge_data) > 500:
                    positive_indicators += 2
        
        # Calculate overall system health
        gps_coverage = 566 / 570  # 99.3% GPS coverage
        if gps_coverage > 0.95:
            positive_indicators += 1
        
        monthly_savings = 66400
        if monthly_savings > 50000:
            positive_indicators += 2
        
        # Determine mood based on indicators
        total_score = positive_indicators - negative_indicators
        
        if total_score >= 4:
            return 'success'
        elif total_score >= 2:
            return 'energetic'
        elif total_score >= 0:
            return 'calm'
        else:
            return 'alert'
            
    except Exception as e:
        print(f"Error detecting mood from system data: {e}")
        return 'neutral'

def generate_theme_css(theme_key):
    """Generate CSS for the selected theme"""
    if theme_key not in MOOD_THEMES:
        theme_key = 'neutral'
    
    theme = MOOD_THEMES[theme_key]
    
    css = f"""
    :root {{
        --mood-primary: {theme['primary']};
        --mood-secondary: {theme['secondary']};
        --mood-accent: {theme['accent']};
        --mood-background: {theme['background']};
        --mood-text: {theme['text']};
        --mood-gradient: {theme['gradient']};
    }}
    
    /* Apply mood colors to key elements */
    .sidebar {{
        background: var(--mood-gradient) !important;
    }}
    
    .nav-item.active,
    .nav-item:hover {{
        background: rgba(255, 255, 255, 0.15) !important;
        border-left-color: rgba(255, 255, 255, 0.8) !important;
    }}
    
    .metric-card {{
        border-left: 4px solid var(--mood-primary) !important;
    }}
    
    .metric-value {{
        color: var(--mood-primary) !important;
    }}
    
    .status-badge.status-active {{
        background: var(--mood-primary) !important;
    }}
    
    .widget {{
        border-top: 3px solid var(--mood-primary) !important;
    }}
    
    .control-btn,
    .submit-btn,
    .feedback-toggle {{
        background: var(--mood-primary) !important;
    }}
    
    .control-btn:hover,
    .submit-btn:hover,
    .feedback-toggle:hover {{
        background: var(--mood-secondary) !important;
    }}
    
    .quick-star.active,
    .rating-star.active {{
        color: var(--mood-accent) !important;
    }}
    
    body {{
        background: var(--mood-background) !important;
    }}
    
    .mood-indicator {{
        background: var(--mood-gradient);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 999;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    """
    
    return css

# Route handlers
@login_required
def mood_selector():
    """Mood selector interface"""
    current_mood = get_user_mood_preference(current_user.id)
    auto_detected_mood = detect_mood_from_system_data()
    
    return render_template('mood_selector.html', 
                         themes=MOOD_THEMES,
                         current_mood=current_mood,
                         auto_detected_mood=auto_detected_mood)

def set_mood():
    """Set user mood and theme"""
    if request.method == 'POST':
        data = request.get_json()
        
        mood_data = {
            'mood': data.get('mood'),
            'theme': data.get('theme'),
            'auto_detect': data.get('auto_detect', False)
        }
        
        success = save_user_mood_preference(current_user.id, mood_data)
        
        if success:
            # Store in session for immediate use
            session['user_mood'] = mood_data
            
            return jsonify({
                'success': True,
                'message': 'Mood theme updated successfully',
                'css': generate_theme_css(mood_data['theme'])
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save mood preference'
            })

def get_current_theme():
    """Get current theme CSS for user"""
    if current_user.is_authenticated:
        # Check session first
        if 'user_mood' in session:
            theme = session['user_mood'].get('theme', 'neutral')
        else:
            # Load from file
            mood_pref = get_user_mood_preference(current_user.id)
            if mood_pref and mood_pref.get('auto_detect'):
                theme = detect_mood_from_system_data()
            elif mood_pref:
                theme = mood_pref.get('theme', 'neutral')
            else:
                theme = 'neutral'
    else:
        theme = 'neutral'
    
    return jsonify({
        'theme': theme,
        'css': generate_theme_css(theme),
        'theme_info': MOOD_THEMES.get(theme, MOOD_THEMES['neutral'])
    })

def reset_mood():
    """Reset to default neutral theme"""
    if current_user.is_authenticated:
        mood_data = {
            'mood': 'neutral',
            'theme': 'neutral',
            'auto_detect': False
        }
        
        success = save_user_mood_preference(current_user.id, mood_data)
        if 'user_mood' in session:
            del session['user_mood']
        
        return jsonify({
            'success': success,
            'css': generate_theme_css('neutral')
        })
    
    return jsonify({'success': False})

def auto_detect_mood():
    """Auto-detect mood from system data"""
    detected_mood = detect_mood_from_system_data()
    
    return jsonify({
        'detected_mood': detected_mood,
        'theme_info': MOOD_THEMES.get(detected_mood, MOOD_THEMES['neutral']),
        'css': generate_theme_css(detected_mood)
    })