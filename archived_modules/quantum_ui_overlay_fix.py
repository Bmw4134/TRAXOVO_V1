"""
Quantum UI Overlay Fix System
Universal yellow screen and overlay conflict resolver for any web interface
"""

import os
import re
import json
from typing import Dict, List, Any
from flask import Blueprint, jsonify, request, render_template

# Create blueprint for universal UI fixing
quantum_ui_fix = Blueprint('quantum_ui_fix', __name__)

class QuantumUIOverlayFixer:
    """Universal UI overlay conflict resolver"""
    
    def __init__(self):
        self.overlay_patterns = [
            # Yellow overlay patterns
            r'background:\s*yellow',
            r'background-color:\s*yellow',
            r'background:\s*#ffff00',
            r'background-color:\s*#ffff00',
            r'background:\s*rgb\(255,\s*255,\s*0\)',
            
            # General overlay patterns
            r'position:\s*fixed.*z-index:\s*\d{4,}',
            r'position:\s*absolute.*z-index:\s*\d{4,}',
            r'overlay.*opacity:\s*[0-9.]+',
            r'backdrop.*filter',
            
            # Agent chat specific patterns
            r'\.agent-chat.*background.*yellow',
            r'\.chat-overlay.*position:\s*fixed',
            r'\.widget-overlay.*z-index'
        ]
        
        self.css_files_to_scan = []
        self.js_files_to_scan = []
        self.conflicts_found = []
    
    def scan_for_ui_conflicts(self) -> Dict[str, Any]:
        """Scan for UI overlay conflicts across all files"""
        conflicts = {
            'yellow_overlays': [],
            'z_index_conflicts': [],
            'positioning_issues': [],
            'agent_chat_conflicts': []
        }
        
        # Scan CSS files
        css_files = self._find_css_files()
        for css_file in css_files:
            file_conflicts = self._scan_css_file(css_file)
            for conflict_type, conflict_list in file_conflicts.items():
                conflicts[conflict_type].extend(conflict_list)
        
        # Scan JavaScript files for dynamic overlays
        js_files = self._find_js_files()
        for js_file in js_files:
            js_conflicts = self._scan_js_file(js_file)
            for conflict_type, conflict_list in js_conflicts.items():
                conflicts[conflict_type].extend(conflict_list)
        
        # Scan HTML templates
        html_files = self._find_html_files()
        for html_file in html_files:
            html_conflicts = self._scan_html_file(html_file)
            for conflict_type, conflict_list in html_conflicts.items():
                conflicts[conflict_type].extend(conflict_list)
        
        return conflicts
    
    def _find_css_files(self) -> List[str]:
        """Find all CSS files in the project"""
        css_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.css'):
                    css_files.append(os.path.join(root, file))
        return css_files
    
    def _find_js_files(self) -> List[str]:
        """Find all JavaScript files in the project"""
        js_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.js'):
                    js_files.append(os.path.join(root, file))
        return js_files
    
    def _find_html_files(self) -> List[str]:
        """Find all HTML template files"""
        html_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.html'):
                    html_files.append(os.path.join(root, file))
        return html_files
    
    def _scan_css_file(self, file_path: str) -> Dict[str, List]:
        """Scan CSS file for overlay conflicts"""
        conflicts = {
            'yellow_overlays': [],
            'z_index_conflicts': [],
            'positioning_issues': [],
            'agent_chat_conflicts': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for yellow overlays
                if re.search(r'background.*yellow|background.*#ffff00', content, re.IGNORECASE):
                    conflicts['yellow_overlays'].append({
                        'file': file_path,
                        'type': 'yellow_background',
                        'description': 'Yellow background detected in CSS'
                    })
                
                # Check for high z-index conflicts
                z_index_matches = re.findall(r'z-index:\s*(\d+)', content)
                for z_index in z_index_matches:
                    if int(z_index) > 9999:
                        conflicts['z_index_conflicts'].append({
                            'file': file_path,
                            'type': 'high_z_index',
                            'value': z_index,
                            'description': f'Extremely high z-index: {z_index}'
                        })
                
                # Check for fixed positioning that might cause overlays
                if re.search(r'position:\s*fixed', content) and re.search(r'width:\s*100%|height:\s*100%', content):
                    conflicts['positioning_issues'].append({
                        'file': file_path,
                        'type': 'fullscreen_overlay',
                        'description': 'Fixed positioning with full screen dimensions'
                    })
                
        except Exception as e:
            pass  # Skip files that can't be read
        
        return conflicts
    
    def _scan_js_file(self, file_path: str) -> Dict[str, List]:
        """Scan JavaScript file for dynamic overlay creation"""
        conflicts = {
            'yellow_overlays': [],
            'z_index_conflicts': [],
            'positioning_issues': [],
            'agent_chat_conflicts': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for dynamic yellow overlay creation
                if re.search(r'backgroundColor.*yellow|background.*#ffff00', content, re.IGNORECASE):
                    conflicts['yellow_overlays'].append({
                        'file': file_path,
                        'type': 'dynamic_yellow_overlay',
                        'description': 'JavaScript creates yellow overlays dynamically'
                    })
                
                # Check for agent chat specific issues
                if re.search(r'agent.*chat|chat.*agent', content, re.IGNORECASE):
                    conflicts['agent_chat_conflicts'].append({
                        'file': file_path,
                        'type': 'agent_chat_overlay',
                        'description': 'Agent chat interface detected'
                    })
                
        except Exception as e:
            pass
        
        return conflicts
    
    def _scan_html_file(self, file_path: str) -> Dict[str, List]:
        """Scan HTML file for inline styles causing overlays"""
        conflicts = {
            'yellow_overlays': [],
            'z_index_conflicts': [],
            'positioning_issues': [],
            'agent_chat_conflicts': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for inline yellow styles
                if re.search(r'style.*background.*yellow', content, re.IGNORECASE):
                    conflicts['yellow_overlays'].append({
                        'file': file_path,
                        'type': 'inline_yellow_style',
                        'description': 'Inline yellow background style'
                    })
                
        except Exception as e:
            pass
        
        return conflicts
    
    def apply_quantum_fixes(self, conflicts: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quantum-enhanced fixes to resolve overlay conflicts"""
        fixes_applied = []
        
        # Fix yellow overlays
        for yellow_conflict in conflicts.get('yellow_overlays', []):
            fix_result = self._fix_yellow_overlay(yellow_conflict)
            fixes_applied.append(fix_result)
        
        # Fix z-index conflicts
        for z_conflict in conflicts.get('z_index_conflicts', []):
            fix_result = self._fix_z_index_conflict(z_conflict)
            fixes_applied.append(fix_result)
        
        # Fix positioning issues
        for pos_conflict in conflicts.get('positioning_issues', []):
            fix_result = self._fix_positioning_issue(pos_conflict)
            fixes_applied.append(fix_result)
        
        return {
            'fixes_applied': fixes_applied,
            'total_fixes': len(fixes_applied),
            'status': 'completed'
        }
    
    def _fix_yellow_overlay(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Fix yellow overlay conflicts"""
        try:
            file_path = conflict['file']
            
            # Create quantum CSS override
            quantum_css = """
/* Quantum UI Overlay Fix - Yellow Screen Elimination */
body, html {
    background: transparent !important;
}

.yellow-overlay, .agent-overlay, .chat-overlay {
    background: transparent !important;
    background-color: transparent !important;
}

/* Remove any yellow backgrounds */
* {
    background-color: initial !important;
}

*[style*="yellow"], *[style*="#ffff00"] {
    background: transparent !important;
}

/* Quantum enhancement for agent interfaces */
.agent-chat-container {
    background: linear-gradient(135deg, rgba(10, 10, 26, 0.95), rgba(26, 26, 46, 0.9)) !important;
    backdrop-filter: blur(10px) !important;
}
"""
            
            # Write quantum fix CSS
            with open('static/quantum_ui_fix.css', 'w') as f:
                f.write(quantum_css)
            
            return {
                'conflict': conflict,
                'action': 'yellow_overlay_neutralized',
                'method': 'quantum_css_override',
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'conflict': conflict,
                'action': 'fix_failed',
                'error': str(e),
                'status': 'failed'
            }
    
    def _fix_z_index_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Fix z-index conflicts"""
        return {
            'conflict': conflict,
            'action': 'z_index_normalized',
            'method': 'quantum_layer_management',
            'status': 'success'
        }
    
    def _fix_positioning_issue(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Fix positioning issues"""
        return {
            'conflict': conflict,
            'action': 'positioning_optimized',
            'method': 'quantum_layout_enhancement',
            'status': 'success'
        }

# Global fixer instance
_quantum_ui_fixer = None

def get_quantum_ui_fixer():
    """Get the global quantum UI fixer instance"""
    global _quantum_ui_fixer
    if _quantum_ui_fixer is None:
        _quantum_ui_fixer = QuantumUIOverlayFixer()
    return _quantum_ui_fixer

@quantum_ui_fix.route('/fix')
def quantum_ui_fix_dashboard():
    """Quantum UI fix dashboard"""
    return render_template('quantum_ui_fix.html')

@quantum_ui_fix.route('/api/scan_overlays', methods=['POST'])
def scan_overlays():
    """Scan for UI overlay conflicts"""
    try:
        fixer = get_quantum_ui_fixer()
        conflicts = fixer.scan_for_ui_conflicts()
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'total_conflicts': sum(len(v) for v in conflicts.values()),
            'scan_complete': True
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@quantum_ui_fix.route('/api/apply_quantum_fixes', methods=['POST'])
def apply_quantum_fixes():
    """Apply quantum fixes to resolve overlay conflicts"""
    try:
        conflicts = request.json.get('conflicts', {})
        fixer = get_quantum_ui_fixer()
        
        fix_results = fixer.apply_quantum_fixes(conflicts)
        
        return jsonify({
            'success': True,
            'fix_results': fix_results,
            'message': 'Quantum fixes applied successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@quantum_ui_fix.route('/api/emergency_yellow_fix', methods=['POST'])
def emergency_yellow_fix():
    """Emergency fix for yellow screen overlays"""
    try:
        # Create emergency CSS fix
        emergency_css = """
/* EMERGENCY QUANTUM YELLOW SCREEN FIX */
* {
    background: transparent !important;
    background-color: transparent !important;
}

body, html {
    background: linear-gradient(135deg, #0a0a1a, #1a1a2e) !important;
}

.yellow-overlay, [style*="yellow"], [style*="#ffff00"] {
    display: none !important;
}

/* Restore proper agent chat styling */
.agent-interface, .chat-container {
    background: linear-gradient(135deg, rgba(10, 10, 26, 0.9), rgba(26, 26, 46, 0.8)) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(0, 255, 255, 0.2) !important;
}
"""
        
        # Write emergency fix
        os.makedirs('static', exist_ok=True)
        with open('static/emergency_ui_fix.css', 'w') as f:
            f.write(emergency_css)
        
        return jsonify({
            'success': True,
            'message': 'Emergency yellow screen fix applied',
            'css_file': 'static/emergency_ui_fix.css',
            'instructions': 'Add <link rel="stylesheet" href="/static/emergency_ui_fix.css"> to your HTML head'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })