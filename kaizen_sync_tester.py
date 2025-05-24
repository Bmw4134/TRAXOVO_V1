# kaizen_sync_tester.py (Auto-Patch Mode)

import os
import re
from bs4 import BeautifulSoup

ROUTES_FILE = "routes/enhanced_weekly_report.py"
TEMPLATE_FILE = "templates/enhanced_weekly_report/dashboard.html"
BUTTON_LABEL = "Compare Processing Methods"
ROUTE_ENDPOINT = "/compare_processing_methods"
BUTTON_HTML = f'<a href="{ROUTE_ENDPOINT}" class="btn btn-success" style="margin-top: 20px;">🔍 {BUTTON_LABEL}</a>'


def check_route():
    print("🔍 Checking backend route...")
    if not os.path.exists(ROUTES_FILE):
        print("❌ Route file not found")
        return False
    with open(ROUTES_FILE, 'r') as f:
        content = f.read()
        if ROUTE_ENDPOINT in content:
            print("✅ Route is defined in backend")
            return True
        else:
            print("🚨 Route not found")
            return False


def check_and_patch_button():
    print("🔍 Checking UI button in dashboard...")
    if not os.path.exists(TEMPLATE_FILE):
        print("❌ Dashboard HTML not found")
        return False
    with open(TEMPLATE_FILE, 'r+') as f:
        html = f.read()
        
        # First check if button already exists
        if BUTTON_LABEL in html:
            print("✅ Button exists in UI")
            return True
        else:
            print("🚨 Button missing — applying patch...")
            
            # Find a suitable insertion point - the row with demo buttons
            match = re.search(r'<div class="row">\s*<div class="col-md-\d+">\s*<a href=.*?View May 18-24 Automated Report.*?</a>', html)
            if match:
                # Insert after the closing </div> tag following this match
                insertion_point = html.find('</div>', match.end()) + 6
                new_html = html[:insertion_point] + '\n                    <div class="col-md-6">\n                        <a href="/compare_processing_methods" class="btn btn-success w-100 mb-2">\n                            <i class="bi bi-bar-chart"></i> Compare Processing Methods\n                        </a>\n                    </div>\n' + html[insertion_point:]
                
                # Write the updated HTML back to the file
                f.seek(0)
                f.write(new_html)
                f.truncate()
                print("✅ Button injected into UI at demo button row")
                return True
            else:
                print("❌ Could not find suitable insertion point. Manual update needed.")
                return False


def run_tests():
    print("\n📦 Running Kaizen Sync Tests + Auto-Patch")
    route_ok = check_route()
    button_ok = check_and_patch_button()
    if route_ok and button_ok:
        print("\n🟩 All systems in sync and patched.")
    else:
        print("\n🟥 Desync detected. Further manual review may be needed.")


if __name__ == "__main__":
    run_tests()