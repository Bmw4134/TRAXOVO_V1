#!/usr/bin/env python3
"""
Syncfusion-Enhanced Watson Intelligence Platform
Professional UI components with advanced dashboard features
"""

from flask import Flask, render_template, render_template_string, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus_watson_supreme_production")

# User credentials
USERS = {
    'watson': {'password': 'Btpp@1513', 'name': 'Watson Supreme Intelligence', 'role': 'admin'},
    'demo': {'password': 'demo123', 'name': 'Demo User', 'role': 'user'}
}

def get_dashboard_data():
    """Get comprehensive dashboard data for Syncfusion components"""
    current_time = datetime.now()
    
    # Fleet performance data for charts
    fleet_performance = [
        {'Date': (current_time - timedelta(days=6)).strftime('%Y-%m-%d'), 'Efficiency': 95.2, 'Utilization': 87.2, 'CostSavings': 45230},
        {'Date': (current_time - timedelta(days=5)).strftime('%Y-%m-%d'), 'Efficiency': 96.1, 'Utilization': 88.5, 'CostSavings': 48120},
        {'Date': (current_time - timedelta(days=4)).strftime('%Y-%m-%d'), 'Efficiency': 97.3, 'Utilization': 89.2, 'CostSavings': 51340},
        {'Date': (current_time - timedelta(days=3)).strftime('%Y-%m-%d'), 'Efficiency': 96.8, 'Utilization': 88.8, 'CostSavings': 49870},
        {'Date': (current_time - timedelta(days=2)).strftime('%Y-%m-%d'), 'Efficiency': 97.1, 'Utilization': 89.1, 'CostSavings': 52110},
        {'Date': (current_time - timedelta(days=1)).strftime('%Y-%m-%d'), 'Efficiency': 97.3, 'Utilization': 89.0, 'CostSavings': 50890},
        {'Date': current_time.strftime('%Y-%m-%d'), 'Efficiency': 97.3, 'Utilization': 89.2, 'CostSavings': 52340}
    ]
    
    # Asset data for grids
    asset_data = [
        {'ID': 'EX-001', 'Type': 'Excavator', 'Status': 'Operational', 'Utilization': 94.2, 'Location': 'Zone A', 'LastMaintenance': '2024-05-15'},
        {'ID': 'DZ-003', 'Type': 'Dozer', 'Status': 'Operational', 'Utilization': 87.5, 'Location': 'Zone B', 'LastMaintenance': '2024-05-10'},
        {'ID': 'LD-005', 'Type': 'Loader', 'Status': 'Maintenance', 'Utilization': 0.0, 'Location': 'Shop', 'LastMaintenance': '2024-06-01'},
        {'ID': 'GR-002', 'Type': 'Grader', 'Status': 'Operational', 'Utilization': 91.3, 'Location': 'Zone C', 'LastMaintenance': '2024-05-20'},
        {'ID': 'TR-008', 'Type': 'Truck', 'Status': 'Critical', 'Utilization': 23.1, 'Location': 'Zone A', 'LastMaintenance': '2024-04-30'},
        {'ID': 'CR-001', 'Type': 'Crane', 'Status': 'Operational', 'Utilization': 88.7, 'Location': 'Zone D', 'LastMaintenance': '2024-05-25'}
    ]
    
    # KPI data for gauges and cards
    kpi_data = {
        'fleet_efficiency': 97.3,
        'quantum_coherence': 98.7,
        'system_uptime': 99.94,
        'cost_savings_ytd': 347320,
        'total_assets': 47,
        'operational_assets': 43,
        'maintenance_assets': 3,
        'critical_assets': 1,
        'daily_revenue': 52340,
        'monthly_projected': 1570200,
        'roi_percentage': 24.8
    }
    
    return {
        'fleet_performance': fleet_performance,
        'asset_data': asset_data,
        'kpi_data': kpi_data,
        'timestamp': current_time.isoformat()
    }

@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').lower()
    password = request.form.get('password', '')
    
    if username in USERS and USERS[username]['password'] == password:
        session['user'] = {
            'username': username, 
            'name': USERS[username]['name'],
            'role': USERS[username]['role']
        }
        return redirect('/dashboard')
    
    flash('Invalid credentials')
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    user = session['user']
    dashboard_data = get_dashboard_data()
    
    return render_template_string(SYNCFUSION_DASHBOARD_TEMPLATE, 
                                user=user, 
                                dashboard_data=dashboard_data,
                                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# API Endpoints for Syncfusion components
@app.route('/api/dashboard-data')
def api_dashboard_data():
    return jsonify(get_dashboard_data())

@app.route('/api/fleet-performance')
def api_fleet_performance():
    data = get_dashboard_data()
    return jsonify(data['fleet_performance'])

@app.route('/api/asset-grid')
def api_asset_grid():
    data = get_dashboard_data()
    return jsonify(data['asset_data'])

@app.route('/api/kpi-metrics')
def api_kpi_metrics():
    data = get_dashboard_data()
    return jsonify(data['kpi_data'])

# Export endpoints
@app.route('/api/export/syncfusion-config')
def export_syncfusion_config():
    """Export Syncfusion dashboard configuration"""
    config = {
        'charts': {
            'line_chart': {
                'primaryXAxis': {'valueType': 'Category'},
                'primaryYAxis': {'labelFormat': '{value}%'},
                'series': [
                    {'dataSource': '/api/fleet-performance', 'xName': 'Date', 'yName': 'Efficiency', 'name': 'Fleet Efficiency'}
                ]
            },
            'column_chart': {
                'primaryXAxis': {'valueType': 'Category'},
                'primaryYAxis': {'labelFormat': '${value}K'},
                'series': [
                    {'dataSource': '/api/fleet-performance', 'xName': 'Date', 'yName': 'CostSavings', 'name': 'Cost Savings'}
                ]
            }
        },
        'grids': {
            'asset_grid': {
                'dataSource': '/api/asset-grid',
                'columns': [
                    {'field': 'ID', 'headerText': 'Asset ID', 'width': 100},
                    {'field': 'Type', 'headerText': 'Type', 'width': 120},
                    {'field': 'Status', 'headerText': 'Status', 'width': 100},
                    {'field': 'Utilization', 'headerText': 'Utilization %', 'width': 120}
                ]
            }
        },
        'gauges': {
            'efficiency_gauge': {
                'minimum': 0,
                'maximum': 100,
                'value': 97.3,
                'ranges': [
                    {'start': 0, 'end': 70, 'color': '#ff4444'},
                    {'start': 70, 'end': 90, 'color': '#ffaa00'},
                    {'start': 90, 'end': 100, 'color': '#00ff44'}
                ]
            }
        }
    }
    
    response = app.response_class(
        response=json.dumps(config, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=syncfusion_watson_config.json'}
    )
    return response

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'operational',
        'quantum_coherence': '98.7%',
        'fleet_efficiency': '97.3%',
        'cost_optimization': '$347,320',
        'syncfusion_integration': 'active',
        'timestamp': datetime.now().isoformat()
    })

# Template definitions
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Nexus Watson - Syncfusion Enhanced</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); margin: 0; padding: 100px 0; }
        .login-container { max-width: 400px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.3); }
        .login-header { text-align: center; margin-bottom: 30px; }
        .login-header h1 { color: #333; margin: 0; font-size: 28px; font-weight: 600; }
        .login-header p { color: #666; margin: 5px 0 0 0; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        .form-group input { width: 100%; padding: 12px 16px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 16px; box-sizing: border-box; transition: border-color 0.3s; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .login-btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .login-btn:hover { transform: translateY(-1px); }
        .demo-info { text-align: center; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; color: #666; font-size: 13px; }
        .syncfusion-badge { position: absolute; top: 20px; right: 20px; background: #ff6b35; color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="syncfusion-badge">Syncfusion Enhanced</div>
    <div class="login-container">
        <div class="login-header">
            <h1>NEXUS WATSON</h1>
            <p>Intelligence Platform with Advanced UI Components</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div style="padding: 12px; margin-bottom: 20px; background: #f8d7da; color: #721c24; border-radius: 8px; border: 1px solid #f5c6cb;">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login">
            <div class="form-group">
                <input type="text" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <input type="password" name="password" placeholder="Password" required>
            </div>
            <button type="submit" class="login-btn">Access Intelligence Platform</button>
        </form>
        
        <div class="demo-info">
            <strong>Demo Credentials:</strong><br>
            Admin: watson / Btpp@1513<br>
            User: demo / demo123
        </div>
    </div>
</body>
</html>
'''

SYNCFUSION_DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Watson Command Center - Syncfusion Enhanced</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.syncfusion.com/ej2/20.4.38/material.css" rel="stylesheet">
    <script src="https://cdn.syncfusion.com/ej2/20.4.38/dist/ej2.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1a1a2e, #0f3460); color: white; margin: 0; padding: 0; }
        .dashboard-container { padding: 20px; max-width: 1400px; margin: 0 auto; }
        .header { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 12px; margin-bottom: 20px; backdrop-filter: blur(10px); }
        .header h1 { color: #00ffff; text-shadow: 0 0 10px #00ffff; margin: 0; font-size: 2.5em; text-align: center; }
        .header-info { text-align: center; margin-top: 10px; opacity: 0.8; }
        .logout-btn { position: absolute; top: 20px; right: 20px; background: rgba(255,0,0,0.2); border: 1px solid rgba(255,0,0,0.5); color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; transition: all 0.3s; }
        .logout-btn:hover { background: rgba(255,0,0,0.4); }
        
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .kpi-card { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 12px; border: 1px solid rgba(0,255,255,0.3); text-align: center; backdrop-filter: blur(10px); }
        .kpi-value { font-size: 2.5em; font-weight: bold; color: #00ffff; margin-bottom: 5px; }
        .kpi-label { color: #ccc; font-size: 0.9em; }
        .kpi-change { font-size: 0.8em; margin-top: 5px; }
        .kpi-positive { color: #4ade80; }
        .kpi-negative { color: #f87171; }
        
        .charts-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-container { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
        .chart-title { color: #00ffff; font-size: 1.2em; margin-bottom: 15px; text-align: center; }
        
        .grid-section { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1); }
        .grid-title { color: #00ffff; font-size: 1.2em; margin-bottom: 15px; }
        
        .export-section { background: linear-gradient(135deg, #667eea, #764ba2); padding: 25px; border-radius: 12px; }
        .export-title { color: white; font-size: 1.3em; margin-bottom: 15px; }
        .export-buttons { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }
        .export-btn { background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 12px 20px; border-radius: 8px; text-decoration: none; text-align: center; transition: all 0.3s; display: block; }
        .export-btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-1px); }
        
        .syncfusion-badge { position: fixed; bottom: 20px; right: 20px; background: #ff6b35; color: white; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; z-index: 1000; }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .charts-section { grid-template-columns: 1fr; }
            .kpi-grid { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
            .export-buttons { grid-template-columns: 1fr; }
        }
        
        /* Syncfusion component overrides for dark theme */
        .e-chart { background: transparent !important; }
        .e-grid { background: rgba(255,255,255,0.05) !important; }
        .e-grid .e-content { background: transparent !important; }
        .e-grid .e-headercontent { background: rgba(0,255,255,0.1) !important; }
        .e-grid .e-headercelldiv { color: #00ffff !important; }
        .e-grid .e-rowcell { color: white !important; border-color: rgba(255,255,255,0.1) !important; }
    </style>
</head>
<body>
    <div class="syncfusion-badge">Powered by Syncfusion</div>
    <a href="/logout" class="logout-btn">Logout</a>
    
    <div class="dashboard-container">
        <div class="header">
            <h1>WATSON COMMAND CENTER</h1>
            <div class="header-info">
                <p>Welcome, {{ user.name }} ({{ user.role }}) | {{ current_time }}</p>
                <p>Advanced Analytics with Syncfusion UI Components</p>
            </div>
        </div>
        
        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">{{ "%.1f"|format(dashboard_data.kpi_data.fleet_efficiency) }}%</div>
                <div class="kpi-label">Fleet Efficiency</div>
                <div class="kpi-change kpi-positive">+2.1% from last month</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{{ dashboard_data.kpi_data.total_assets }}</div>
                <div class="kpi-label">Total Assets</div>
                <div class="kpi-change kpi-positive">{{ dashboard_data.kpi_data.operational_assets }} operational</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">${{ "{:,.0f}".format(dashboard_data.kpi_data.cost_savings_ytd/1000) }}K</div>
                <div class="kpi-label">Cost Savings YTD</div>
                <div class="kpi-change kpi-positive">+15.3% from target</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{{ "%.1f"|format(dashboard_data.kpi_data.quantum_coherence) }}%</div>
                <div class="kpi-label">Quantum Coherence</div>
                <div class="kpi-change kpi-positive">Optimal performance</div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Fleet Efficiency Trend</div>
                <div id="efficiency-chart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Cost Savings Analysis</div>
                <div id="savings-chart"></div>
            </div>
        </div>
        
        <!-- Asset Grid -->
        <div class="grid-section">
            <div class="grid-title">Asset Management Grid</div>
            <div id="asset-grid"></div>
        </div>
        
        <!-- Export Section -->
        <div class="export-section">
            <div class="export-title">Intelligence Export Hub</div>
            <p style="opacity: 0.8; margin: 0;">Export data and configurations for dashboard integration</p>
            
            <div class="export-buttons">
                <a href="/api/dashboard-data" class="export-btn">📊 Dashboard Data (JSON)</a>
                <a href="/api/export/syncfusion-config" class="export-btn">⚙️ Syncfusion Config</a>
                <a href="/api/fleet-performance" class="export-btn">📈 Performance Data</a>
                <a href="/api/asset-grid" class="export-btn">🏗️ Asset Data</a>
                <button onclick="copyApiUrl()" class="export-btn">📋 Copy API Endpoint</button>
                <button onclick="exportToPDF()" class="export-btn">📄 Export Dashboard PDF</button>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Syncfusion components
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            initializeGrid();
        });
        
        function initializeCharts() {
            // Fleet Efficiency Line Chart
            var efficiencyChart = new ej.charts.Chart({
                primaryXAxis: { valueType: 'Category', labelStyle: { color: '#ffffff' } },
                primaryYAxis: { 
                    labelFormat: '{value}%', 
                    labelStyle: { color: '#ffffff' },
                    minimum: 90,
                    maximum: 100
                },
                series: [{
                    dataSource: {{ dashboard_data.fleet_performance | tojsonfilter }},
                    xName: 'Date',
                    yName: 'Efficiency',
                    name: 'Fleet Efficiency',
                    type: 'Line',
                    marker: { visible: true, width: 6, height: 6 },
                    fill: '#00ffff'
                }],
                background: 'transparent',
                legendSettings: { textStyle: { color: '#ffffff' } },
                tooltip: { enable: true }
            });
            efficiencyChart.appendTo('#efficiency-chart');
            
            // Cost Savings Column Chart
            var savingsChart = new ej.charts.Chart({
                primaryXAxis: { valueType: 'Category', labelStyle: { color: '#ffffff' } },
                primaryYAxis: { 
                    labelFormat: '${value}K', 
                    labelStyle: { color: '#ffffff' }
                },
                series: [{
                    dataSource: {{ dashboard_data.fleet_performance | tojsonfilter }},
                    xName: 'Date',
                    yName: 'CostSavings',
                    name: 'Cost Savings',
                    type: 'Column',
                    fill: '#667eea'
                }],
                background: 'transparent',
                legendSettings: { textStyle: { color: '#ffffff' } },
                tooltip: { enable: true }
            });
            savingsChart.appendTo('#savings-chart');
        }
        
        function initializeGrid() {
            var grid = new ej.grids.Grid({
                dataSource: {{ dashboard_data.asset_data | tojsonfilter }},
                columns: [
                    { field: 'ID', headerText: 'Asset ID', width: 100 },
                    { field: 'Type', headerText: 'Type', width: 120 },
                    { field: 'Status', headerText: 'Status', width: 100, template: statusTemplate },
                    { field: 'Utilization', headerText: 'Utilization %', width: 120, format: 'N1' },
                    { field: 'Location', headerText: 'Location', width: 100 },
                    { field: 'LastMaintenance', headerText: 'Last Maintenance', width: 140, type: 'date', format: 'dd/MM/yyyy' }
                ],
                allowPaging: true,
                pageSettings: { pageSize: 10 },
                allowSorting: true,
                allowFiltering: true,
                filterSettings: { type: 'Excel' }
            });
            grid.appendTo('#asset-grid');
        }
        
        function statusTemplate(args) {
            var statusClass = args.Status === 'Operational' ? 'kpi-positive' : 
                             args.Status === 'Critical' ? 'kpi-negative' : 'kpi-warning';
            return '<span class="' + statusClass + '">' + args.Status + '</span>';
        }
        
        function copyApiUrl() {
            navigator.clipboard.writeText(window.location.origin + '/api/dashboard-data');
            showNotification('API URL copied to clipboard!');
        }
        
        function exportToPDF() {
            // Implement PDF export functionality
            showNotification('PDF export feature coming soon!');
        }
        
        function showNotification(message) {
            var notification = document.createElement('div');
            notification.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #4ade80; color: white; padding: 12px 24px; border-radius: 8px; z-index: 10000; font-weight: 600;';
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(function() {
                document.body.removeChild(notification);
            }, 3000);
        }
        
        // Auto-refresh data every 5 minutes
        setInterval(function() {
            location.reload();
        }, 300000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)