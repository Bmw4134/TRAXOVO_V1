from flask import Flask, render_template_string
import json
import re

app = Flask(__name__)
app.secret_key = "traxovo_authentic"

@app.route('/')
def dashboard():
    # Load authentic GPS assets (active IMEI devices only)
    with open('data/gauge_2025-05-15.json', 'r') as f:
        all_assets = json.load(f)
    
    gps_assets = [a for a in all_assets if a.get('IMEI') and a.get('IMEI') != '' and a.get('Active') == True]
    total_assets = len(gps_assets)  # 562
    
    # Company classification (GPS assets only)
    unified_count = len([a for a in gps_assets if a.get('AssetIdentifier', '').endswith('U')])
    select_count = len([a for a in gps_assets if a.get('AssetIdentifier', '').endswith('S')])
    ragle_count = total_assets - unified_count - select_count
    
    # Job sites from GPS assets
    active_sites = len(set([a.get('Location', '') for a in gps_assets if a.get('Location', '') and a.get('Location', '') not in ['', 'Unknown']]))
    
    # Driver data from MTD
    with open('DrivingHistory (19).csv', 'r') as f:
        content = f.read()
    drivers = re.findall(r'#(\d+) - ([A-Z\s\.]+)', content)
    total_drivers = len(drivers)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>TRAXOVO Fleet Command</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
            .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 15px; margin-bottom: 1rem; }
            .metric-number { font-size: 3rem; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <h1 class="text-center mb-5">TRAXOVO Texas Fleet Operations</h1>
            
            <div class="row g-4">
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-number">{{ total_assets }}</div>
                        <div>GPS Assets Active</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-number">{{ total_drivers }}</div>
                        <div>Active Drivers</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-number">{{ active_sites }}</div>
                        <div>Job Sites</div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <div class="metric-number">3</div>
                        <div>Companies</div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-5">
                <div class="col-md-6">
                    <div class="card p-4">
                        <h4>Company Distribution</h4>
                        <p>Ragle Inc: {{ ragle_count }} assets</p>
                        <p>Select Maintenance: {{ select_count }} assets</p>
                        <p>Unified Specialties: {{ unified_count }} assets</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card p-4">
                        <h4>Verified Drivers</h4>
                        {% for emp_id, name in drivers %}
                        <p>Employee #{{ emp_id }}: {{ name }}</p>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', total_assets=total_assets, total_drivers=total_drivers, active_sites=active_sites,
        ragle_count=ragle_count, select_count=select_count, unified_count=unified_count, drivers=drivers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)