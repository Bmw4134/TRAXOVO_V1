from flask import Flask, send_file, request, session, redirect, url_for, jsonify
import os
import json
import subprocess
import threading

app = Flask(__name__, static_folder='public')
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

# Store for users (in production this would be in a database)
users = {
    'troy': {'password': 'troy2025', 'role': 'exec', 'name': 'Troy'},
    'william': {'password': 'william2025', 'role': 'exec', 'name': 'William'},
    'admin': {'password': 'admin123', 'role': 'admin', 'name': 'Administrator'},
    'ops': {'password': 'ops123', 'role': 'ops', 'name': 'Operations'}
}

# Proprietary Watson access - separate from general users
watson_access = {
    'watson': {'password': 'proprietary_watson_2025', 'owner': True, 'name': 'Watson Command Console'}
}

def start_node_server():
    """Start AGI mesh server in background"""
    try:
        subprocess.Popen(["node", "agi_evolution/sovereign_coordinator.js"], 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"AGI mesh startup: {e}")

# Start AGI systems
threading.Thread(target=start_node_server, daemon=True).start()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')
    return send_file('public/index.html')

@app.route('/login')
def login_page():
    return send_file('public/login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check proprietary Watson access first
    if username in watson_access and watson_access[username]['password'] == password:
        session['user'] = {
            'username': username,
            'role': 'watson_owner',
            'name': watson_access[username]['name'],
            'watson_access': True
        }
        return redirect('/watson-command-console')
    
    # Check regular users
    if username in users and users[username]['password'] == password:
        session['user'] = {
            'username': username,
            'role': users[username]['role'],
            'name': users[username]['name']
        }
        # Redirect to organization selector for all authenticated users
        return redirect(f'/organization-selector?user={users[username]["name"]}')
    
    return redirect('/login?error=invalid')

@app.route('/organization-selector')
def organization_selector():
    if 'user' not in session:
        return redirect('/login')
    return send_file('public/organization_selector.html')

@app.route('/dashboard')
def executive_dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    # Get organization from query parameter
    org = request.args.get('org', 'default')
    session['selected_organization'] = org
    
    return send_file('public/post_login_reveal/executive_dashboard.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/mesh-graph')
def mesh_graph():
    return json.dumps({
        'agents': [
            {'id': 'agent_0', 'status': 'active'},
            {'id': 'agent_1', 'status': 'active'},
            {'id': 'agent_2', 'status': 'active'},
            {'id': 'agent_3', 'status': 'active'},
            {'id': 'agent_4', 'status': 'active'}
        ],
        'mesh_health': 'Operational',
        'alliance_routing': 'active'
    })

@app.route('/api/dashboard-fingerprints')
def dashboard_fingerprints():
    return jsonify({
        'telemetry_entries': '10,000+',
        'fingerprint_sync': 'verified',
        'last_update': '2025-06-05T12:52:00Z',
        'status': 'operational'
    })

@app.route('/globe-tracker')
def globe_tracker():
    if 'user' not in session:
        return redirect('/login')
    return send_file('infinity_visual_tracker/index.html')

@app.route('/mobile-fleet-map')
def mobile_fleet_map():
    if 'user' not in session:
        return redirect('/login')
    return send_file('mobile_fleet_map/index.html')

@app.route('/watson-command-console')
def watson_command_console():
    if 'user' not in session or not session['user'].get('watson_access'):
        return redirect('/login?error=unauthorized')
    return send_file('public/watson_command_console.html')

@app.route('/watson_email_ops')
def watson_email_ops():
    if 'user' not in session or not session['user'].get('watson_access'):
        return redirect('/login?error=unauthorized')
    return send_file('templates/watson_email_ops.html')

@app.route('/kaizen_dashboard')
def kaizen_dashboard():
    if 'user' not in session:
        return redirect('/login')
    return send_file('templates/kaizen_dashboard.html')

@app.route('/api/voice/start_session', methods=['POST'])
def start_voice_session():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from watson_voice_integration import start_voice_session
    user_id = session['user']['username']
    language = request.json.get('language', 'en-US') if request.json else 'en-US'
    
    result = start_voice_session(user_id, language)
    return jsonify(result)

@app.route('/api/voice/process_command', methods=['POST'])
def process_voice_command():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from watson_voice_integration import process_voice_command
    user_id = session['user']['username']
    
    # Simulate audio data processing
    audio_data = request.data or b'watson analyze system performance'
    
    result = process_voice_command(audio_data, user_id)
    return jsonify(result)

@app.route('/api/voice/stop_session', methods=['POST'])
def stop_voice_session():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from watson_voice_integration import stop_voice_session
    result = stop_voice_session()
    return jsonify(result)

@app.route('/api/voice/analytics')
def voice_analytics():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from watson_voice_integration import get_voice_analytics
    result = get_voice_analytics()
    return jsonify(result)

@app.route('/api/trillion_scale/execute', methods=['POST'])
def execute_trillion_simulation():
    if 'user' not in session or not session['user'].get('watson_access'):
        return jsonify({'error': 'Unauthorized - Watson access required'}), 401
    
    from trillion_scale_simulator import execute_trillion_scale_test
    result = execute_trillion_scale_test()
    return jsonify(result)

@app.route('/api/trillion_scale/metrics')
def get_simulation_metrics():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    from trillion_scale_simulator import get_simulation_metrics
    simulation_id = request.args.get('simulation_id')
    result = get_simulation_metrics(simulation_id)
    return jsonify(result)

# Serve static files with error handling
@app.route('/<path:filename>')
def serve_static(filename):
    try:
        return send_file(f'public/{filename}')
    except FileNotFoundError:
        # Return 404 for missing static files like favicon.ico, apple-touch-icon.png
        return '', 404

@app.errorhandler(404)
def not_found(error):
    return '', 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)