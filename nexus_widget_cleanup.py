#!/usr/bin/env python3
"""
NEXUS Widget Cleanup - Remove duplicates and ensure single navigation
"""

from flask import Flask, request, jsonify
import re

def cleanup_duplicate_widgets(html_content):
    """Clean up duplicate NEXUS widgets in HTML content"""
    
    # Remove multiple instances of nexus-unified-nav (keep only first)
    nav_pattern = r'<div id="nexus-unified-nav".*?</div>\s*</div>'
    nav_matches = re.findall(nav_pattern, html_content, re.DOTALL)
    
    if len(nav_matches) > 1:
        # Keep first, remove others
        for i in range(1, len(nav_matches)):
            html_content = html_content.replace(nav_matches[i], '', 1)
    
    # Remove multiple floating widgets
    floating_pattern = r'<div id="nexus-floating-nav".*?</div>\s*</div>'
    floating_matches = re.findall(floating_pattern, html_content, re.DOTALL)
    
    if len(floating_matches) > 1:
        for i in range(1, len(floating_matches)):
            html_content = html_content.replace(floating_matches[i], '', 1)
    
    # Remove old assistant widgets
    assistant_patterns = [
        r'<div[^>]*class="[^"]*assistant[^"]*"[^>]*>.*?</div>',
        r'<div[^>]*id="[^"]*assistant[^"]*"[^>]*>.*?</div>',
        r'<div[^>]*class="[^"]*chat[^"]*"[^>]*>.*?</div>'
    ]
    
    for pattern in assistant_patterns:
        html_content = re.sub(pattern, '', html_content, flags=re.DOTALL)
    
    return html_content

def inject_unified_navigation(html_content, current_path="/"):
    """Inject unified navigation if not present"""
    
    if 'nexus-unified-nav' in html_content:
        return html_content
    
    navigation_html = f'''
<div id="nexus-unified-nav" style="position: fixed; top: 0; left: 0; right: 0; height: 60px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-bottom: 2px solid #00ff88; z-index: 10000; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; font-family: 'SF Mono', Monaco, monospace; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);">
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="font-size: 18px; font-weight: bold; color: #00ff88; cursor: pointer;" onclick="window.location.href='/'">NEXUS</div>
        <div style="padding: 4px 8px; background: #00ff88; color: #000; border-radius: 3px; font-size: 11px; font-weight: bold;">OPERATIONAL</div>
    </div>
    <div style="display: flex; align-items: center; gap: 20px;">
        <a href="/admin-direct" style="color: #00ff88; text-decoration: none; font-weight: bold; padding: 8px 12px; border: 1px solid #00ff88; border-radius: 4px; transition: all 0.2s;">ADMIN</a>
        <a href="/nexus-dashboard" style="color: #ffffff; text-decoration: none; font-weight: bold; padding: 8px 12px; border: 1px solid #ffffff; border-radius: 4px; transition: all 0.2s;">DASHBOARD</a>
        <a href="/executive-dashboard" style="color: #ffa502; text-decoration: none; font-weight: bold; padding: 8px 12px; border: 1px solid #ffa502; border-radius: 4px; transition: all 0.2s;">EXECUTIVE</a>
        <a href="/upload" style="color: #3742fa; text-decoration: none; font-weight: bold; padding: 8px 12px; border: 1px solid #3742fa; border-radius: 4px; transition: all 0.2s;">UPLOAD</a>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="background: rgba(255, 255, 255, 0.1); color: #ffffff; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; border: 1px solid rgba(255, 255, 255, 0.2);">⌘K Navigate</div>
        <div style="color: #ffffff; font-size: 12px; opacity: 0.8;">{current_path}</div>
        <div style="background: #ff4757; color: #ffffff; padding: 6px 10px; border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: bold;" onclick="window.location.href='/admin-direct'">🚨 ADMIN</div>
    </div>
</div>

<div id="nexus-floating-nav" style="position: fixed; bottom: 20px; left: 20px; z-index: 15000; display: flex; flex-direction: column; gap: 10px;">
    <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 15px rgba(0, 255, 136, 0.3); color: #000; font-weight: bold; font-size: 18px;" onclick="toggleFloatingMenu()">N</div>
    <div id="nexus-floating-menu" style="display: none; flex-direction: column; gap: 8px; margin-bottom: 10px;">
        <div onclick="window.location.href='/admin-direct'" style="width: 50px; height: 50px; background: #ff4757; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; font-weight: bold; font-size: 12px;">A</div>
        <div onclick="window.location.href='/nexus-dashboard'" style="width: 50px; height: 50px; background: #3742fa; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; font-weight: bold; font-size: 12px;">D</div>
        <div onclick="window.location.href='/executive-dashboard'" style="width: 50px; height: 50px; background: #ffa502; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; font-weight: bold; font-size: 12px;">E</div>
        <div onclick="window.location.href='/'" style="width: 50px; height: 50px; background: #2f3542; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #fff; font-weight: bold; font-size: 12px;">H</div>
    </div>
</div>

<script>
let floatingMenuOpen = false;
function toggleFloatingMenu() {{
    const menu = document.getElementById('nexus-floating-menu');
    const button = document.querySelector('#nexus-floating-nav > div:first-child');
    if (floatingMenuOpen) {{
        menu.style.display = 'none';
        button.style.transform = 'rotate(0deg)';
        floatingMenuOpen = false;
    }} else {{
        menu.style.display = 'flex';
        button.style.transform = 'rotate(45deg)';
        floatingMenuOpen = true;
    }}
}}
document.addEventListener('keydown', function(e) {{
    if (e.ctrlKey && e.shiftKey && e.key === 'A') {{ e.preventDefault(); window.location.href = '/admin-direct'; }}
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {{ e.preventDefault(); window.location.href = '/nexus-dashboard'; }}
    if (e.ctrlKey && e.shiftKey && e.key === 'H') {{ e.preventDefault(); window.location.href = '/'; }}
}});
if (document.body) {{ document.body.style.marginTop = '60px'; }}
</script>
'''
    
    # Inject after opening body tag
    if '<body>' in html_content:
        html_content = html_content.replace('<body>', f'<body>{navigation_html}', 1)
    elif '<body' in html_content:
        # Handle body tag with attributes
        body_match = re.search(r'<body[^>]*>', html_content)
        if body_match:
            body_tag = body_match.group(0)
            html_content = html_content.replace(body_tag, f'{body_tag}{navigation_html}', 1)
    
    return html_content

if __name__ == "__main__":
    print("NEXUS Widget Cleanup module ready")