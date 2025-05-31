"""
Intelligent Responsive Layout Detector
Automatically detects device capabilities and optimizes layout accordingly
"""

from flask import Blueprint, render_template, jsonify, request, session
import json
from datetime import datetime

responsive_detector_bp = Blueprint('responsive_detector', __name__)

class IntelligentLayoutEngine:
    """Detects device capabilities and optimizes layout intelligently"""
    
    def __init__(self):
        self.device_profiles = self._initialize_device_profiles()
        self.layout_optimizations = self._initialize_layout_optimizations()
    
    def _initialize_device_profiles(self):
        """Device capability profiles for intelligent detection"""
        return {
            "mobile_phone": {
                "screen_width": {"min": 0, "max": 767},
                "touch_capable": True,
                "bandwidth_typical": "medium",
                "interaction_pattern": "touch_primary",
                "layout_priority": ["navigation", "primary_content", "actions", "secondary_content"],
                "optimizations": ["simplified_nav", "touch_targets", "reduced_content", "priority_loading"]
            },
            
            "tablet": {
                "screen_width": {"min": 768, "max": 1024},
                "touch_capable": True,
                "bandwidth_typical": "high",
                "interaction_pattern": "touch_and_keyboard",
                "layout_priority": ["navigation", "primary_content", "secondary_content", "actions"],
                "optimizations": ["adaptive_sidebar", "touch_targets", "dual_column", "full_content"]
            },
            
            "desktop": {
                "screen_width": {"min": 1025, "max": 9999},
                "touch_capable": False,
                "bandwidth_typical": "high",
                "interaction_pattern": "mouse_keyboard",
                "layout_priority": ["navigation", "primary_content", "secondary_content", "tertiary_content"],
                "optimizations": ["full_sidebar", "hover_states", "multi_column", "rich_content"]
            },
            
            "large_desktop": {
                "screen_width": {"min": 1400, "max": 9999},
                "touch_capable": False,
                "bandwidth_typical": "high",
                "interaction_pattern": "mouse_keyboard_advanced",
                "layout_priority": ["navigation", "primary_content", "secondary_content", "tertiary_content", "analytics"],
                "optimizations": ["expanded_sidebar", "dashboard_widgets", "multi_panel", "advanced_features"]
            }
        }
    
    def _initialize_layout_optimizations(self):
        """Layout optimization strategies per device type"""
        return {
            "mobile_phone": {
                "navigation": {
                    "type": "hamburger_menu",
                    "position": "top_left",
                    "behavior": "overlay",
                    "animation": "slide_right"
                },
                "content": {
                    "columns": 1,
                    "card_layout": "stacked",
                    "spacing": "compact",
                    "font_size": "16px"
                },
                "interactions": {
                    "touch_targets": "44px_minimum",
                    "swipe_gestures": True,
                    "tap_feedback": True,
                    "scroll_optimization": True
                }
            },
            
            "tablet": {
                "navigation": {
                    "type": "collapsible_sidebar",
                    "position": "left",
                    "behavior": "push_content",
                    "animation": "slide_left"
                },
                "content": {
                    "columns": 2,
                    "card_layout": "grid",
                    "spacing": "comfortable",
                    "font_size": "15px"
                },
                "interactions": {
                    "touch_targets": "40px_minimum",
                    "swipe_gestures": True,
                    "hover_simulation": True,
                    "pinch_zoom": True
                }
            },
            
            "desktop": {
                "navigation": {
                    "type": "persistent_sidebar",
                    "position": "left",
                    "behavior": "fixed",
                    "animation": "none"
                },
                "content": {
                    "columns": 3,
                    "card_layout": "masonry",
                    "spacing": "generous",
                    "font_size": "14px"
                },
                "interactions": {
                    "hover_states": True,
                    "keyboard_navigation": True,
                    "context_menus": True,
                    "drag_drop": True
                }
            }
        }
    
    def detect_device_profile(self, user_agent, screen_width, touch_capable=None):
        """Intelligently detect device profile from available data"""
        
        # Analyze user agent for device hints
        device_hints = self._analyze_user_agent(user_agent)
        
        # Determine device category based on screen width
        device_category = self._categorize_by_screen_width(screen_width)
        
        # Enhance detection with user agent analysis
        if device_hints.get('mobile') and screen_width < 768:
            device_category = "mobile_phone"
        elif device_hints.get('tablet') and 768 <= screen_width <= 1024:
            device_category = "tablet"
        elif screen_width >= 1400:
            device_category = "large_desktop"
        
        profile = self.device_profiles.get(device_category, self.device_profiles["desktop"])
        
        # Add detected capabilities
        profile["detected"] = {
            "user_agent_hints": device_hints,
            "screen_width": screen_width,
            "touch_capable": touch_capable,
            "detection_confidence": self._calculate_confidence(device_hints, screen_width),
            "timestamp": datetime.now().isoformat()
        }
        
        return device_category, profile
    
    def _analyze_user_agent(self, user_agent):
        """Extract device information from user agent string"""
        if not user_agent:
            return {}
        
        user_agent_lower = user_agent.lower()
        hints = {
            'mobile': any(keyword in user_agent_lower for keyword in ['mobile', 'android', 'iphone', 'ipod']),
            'tablet': any(keyword in user_agent_lower for keyword in ['tablet', 'ipad']),
            'desktop': any(keyword in user_agent_lower for keyword in ['windows', 'macintosh', 'linux']),
            'touch': any(keyword in user_agent_lower for keyword in ['touch', 'mobile', 'android', 'iphone', 'ipad']),
            'webkit': 'webkit' in user_agent_lower,
            'chrome': 'chrome' in user_agent_lower,
            'firefox': 'firefox' in user_agent_lower,
            'safari': 'safari' in user_agent_lower
        }
        
        return hints
    
    def _categorize_by_screen_width(self, screen_width):
        """Categorize device by screen width"""
        if screen_width < 768:
            return "mobile_phone"
        elif screen_width < 1025:
            return "tablet"
        elif screen_width < 1400:
            return "desktop"
        else:
            return "large_desktop"
    
    def _calculate_confidence(self, device_hints, screen_width):
        """Calculate detection confidence score"""
        confidence = 0.7  # Base confidence
        
        # Boost confidence with consistent hints
        if device_hints.get('mobile') and screen_width < 768:
            confidence += 0.2
        elif device_hints.get('tablet') and 768 <= screen_width <= 1024:
            confidence += 0.2
        elif device_hints.get('desktop') and screen_width > 1024:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def get_layout_optimization(self, device_category):
        """Get optimized layout configuration for device"""
        return self.layout_optimizations.get(device_category, self.layout_optimizations["desktop"])
    
    def generate_responsive_css(self, device_category, profile):
        """Generate device-specific CSS optimizations"""
        optimization = self.get_layout_optimization(device_category)
        
        css_rules = []
        
        # Navigation optimizations
        nav_config = optimization["navigation"]
        if nav_config["type"] == "hamburger_menu":
            css_rules.append("""
                .sidebar { transform: translateX(-100%); transition: transform 0.3s ease; }
                .sidebar.show { transform: translateX(0); }
                .navbar-toggler { display: block; }
            """)
        
        # Content optimizations
        content_config = optimization["content"]
        css_rules.append(f"""
            .content-grid {{ 
                grid-template-columns: repeat({content_config['columns']}, 1fr);
                gap: {content_config['spacing'] == 'compact' and '0.5rem' or '1rem'};
            }}
            body {{ font-size: {content_config['font_size']}; }}
        """)
        
        # Interaction optimizations
        interaction_config = optimization["interactions"]
        if interaction_config.get("touch_targets"):
            touch_size = interaction_config["touch_targets"].replace("px_minimum", "px")
            css_rules.append(f"""
                .btn, .nav-link, .clickable {{ 
                    min-height: {touch_size}; 
                    min-width: {touch_size}; 
                }}
            """)
        
        return "\n".join(css_rules)

# Global layout engine
layout_engine = IntelligentLayoutEngine()

@responsive_detector_bp.route('/api/detect-layout')
def detect_layout():
    """API endpoint for intelligent layout detection"""
    user_agent = request.headers.get('User-Agent', '')
    screen_width = request.args.get('width', type=int, default=1024)
    touch_capable = request.args.get('touch', type=bool)
    
    device_category, profile = layout_engine.detect_device_profile(
        user_agent, screen_width, touch_capable
    )
    
    optimization = layout_engine.get_layout_optimization(device_category)
    css_rules = layout_engine.generate_responsive_css(device_category, profile)
    
    # Store detection in session for persistent optimization
    session['device_profile'] = {
        'category': device_category,
        'profile': profile,
        'optimization': optimization,
        'last_detection': datetime.now().isoformat()
    }
    
    return jsonify({
        'device_category': device_category,
        'profile': profile,
        'optimization': optimization,
        'css_rules': css_rules,
        'detection_confidence': profile.get('detected', {}).get('detection_confidence', 0.7)
    })

@responsive_detector_bp.route('/api/layout-status')
def layout_status():
    """Get current layout optimization status"""
    device_profile = session.get('device_profile', {})
    
    return jsonify({
        'active': bool(device_profile),
        'device_category': device_profile.get('category', 'unknown'),
        'optimization_active': True,
        'last_detection': device_profile.get('last_detection'),
        'features': {
            'intelligent_detection': True,
            'adaptive_layout': True,
            'touch_optimization': True,
            'performance_tuning': True
        }
    })

@responsive_detector_bp.route('/responsive-demo')
def responsive_demo():
    """Responsive layout demonstration page"""
    return render_template('responsive_demo.html',
                         page_title="Intelligent Responsive Layout",
                         page_subtitle="Automatic device detection and layout optimization")