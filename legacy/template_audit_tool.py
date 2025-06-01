
import os
import re
import inspect
from flask import Flask
from admin.routes import admin_bp
from attendance.routes import attendance_bp

app = Flask(__name__)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(attendance_bp, url_prefix='/attendance')

# Collect all available templates
TEMPLATE_DIR = 'templates'
all_templates = set()
for root, dirs, files in os.walk(TEMPLATE_DIR):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file).replace('\\', '/').replace(TEMPLATE_DIR + '/', '')
            all_templates.add(path)

# Collect all referenced templates from routes
used_templates = set()

for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        try:
            view_func = app.view_functions[rule.endpoint]
            src = re.findall(r'render_template\((.*?)\)', inspect.getsource(view_func))
            for match in src:
                path_match = re.findall(r'["\']([^"\']+\.html)["\']', match)
                used_templates.update(path_match)
        except Exception:
            continue

# Audit
unused = sorted(all_templates - used_templates)
used = sorted(used_templates & all_templates)
missing = sorted(used_templates - all_templates)

with open("/mnt/data/template_audit_report.md", "w") as f:
    f.write("# 🧾 Template Audit Report\n\n")
    f.write("## ✅ Used Templates\n")
    for t in used:
        f.write(f"- {t}\n")

    f.write("\n## ❌ Unused Templates (Safe to Review)\n")
    for t in unused:
        f.write(f"- {t}\n")

    f.write("\n## ⚠️ Missing Templates (Used but Not Found)\n")
    for t in missing:
        f.write(f"- {t}\n")
