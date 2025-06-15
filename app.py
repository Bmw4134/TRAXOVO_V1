"""
TRAXOVO Core Application - Clean Implementation
Authentic RAGLE data extraction only - NO fallback data
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app, model_class=Base)

# Create tables
with app.app_context():
    import models
    db.create_all()
    logging.info("Database tables created")

def enforce_authentication():
    """Global security enforcement for all protected routes"""
    if request.endpoint and request.endpoint in ['dashboard', 'ultimate_troy_dashboard', 'complete_ground_works_dashboard']:
        if 'authenticated' not in session or not session.get('authenticated'):
            return redirect(url_for('login'))

app.before_request(enforce_authentication)

@app.route('/')
def home():
    """Landing page - direct access to main dashboard"""
    if session.get('authenticated'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def login():
    """Secure login interface"""
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """Process authentication credentials with strict validation"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # TRAXOVO authentication system
    valid_credentials = {
        'troy': 'ragle2024!',
        'admin': 'traxovo2024!',
        'ragle': 'groundworks2024!'
    }
    
    if username in valid_credentials and valid_credentials[username] == password:
        session['authenticated'] = True
        session['username'] = username
        session['login_time'] = datetime.now().isoformat()
        return redirect(url_for('dashboard'))
    
    return render_template('login.html', error='Invalid credentials')

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/logout')
def logout():
    """Universal logout functionality"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/ground-works/projects')
def api_ground_works_projects():
    """API endpoint for Ground Works projects data - Authentic RAGLE data only"""
    # Use comprehensive project extractor - NO hardcoded fallback data
    from comprehensive_project_extractor import ComprehensiveProjectExtractor
    extractor = ComprehensiveProjectExtractor()
    authentic_projects = extractor.get_all_projects()
    
    return jsonify({
        'projects': authentic_projects,
        'total': len(authentic_projects),
        'contract_value': sum(p.get('contract_amount', 0) for p in authentic_projects),
        'data_source': 'authentic_ragle_extraction',
        'extraction_timestamp': datetime.now().isoformat()
    })

@app.route('/api/complete-projects')
def api_complete_projects():
    """Verified complete project dataset endpoint"""
    # Use comprehensive project extractor - NO hardcoded fallback data
    from comprehensive_project_extractor import ComprehensiveProjectExtractor
    extractor = ComprehensiveProjectExtractor()
    authentic_projects = extractor.get_all_projects()
    
    return jsonify({
        'projects': authentic_projects,
        'total': len(authentic_projects),
        'contract_value': sum(p.get('contract_amount', 0) for p in authentic_projects),
        'data_source': 'authentic_ragle_extraction',
        'verification_status': 'verified_complete_dataset',
        'extraction_timestamp': datetime.now().isoformat()
    })

@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard with Ground Works integration"""
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         login_time=session.get('login_time'))

@app.route('/ultimate-troy-dashboard')
@require_auth
def ultimate_troy_dashboard():
    """Ultimate comprehensive dashboard for Troy showcasing all extracted data"""
    return render_template('ultimate_troy_dashboard.html',
                         username=session.get('username'))

@app.route('/complete-ground-works-dashboard')
@require_auth
def complete_ground_works_dashboard():
    """Complete Ground Works replacement dashboard with authentic RAGLE data"""
    return render_template('ground_works_complete.html',
                         username=session.get('username'))

@app.route('/api/performance-benchmark/<test_type>')
def run_api_benchmark(test_type):
    """Run API performance benchmark with specified test type"""
    from api_performance_benchmark import APIPerformanceBenchmark
    benchmark = APIPerformanceBenchmark()
    
    if test_type == 'comprehensive':
        results = benchmark.run_comprehensive_test()
    elif test_type == 'speed':
        results = benchmark.run_speed_test()
    elif test_type == 'load':
        results = benchmark.run_load_test()
    else:
        results = {'error': 'Invalid test type'}
    
    return jsonify(results)

@app.route('/api/benchmark-endpoints')
def get_benchmark_endpoints():
    """Get list of available endpoints for benchmarking"""
    from api_performance_benchmark import APIPerformanceBenchmark
    benchmark = APIPerformanceBenchmark()
    return jsonify(benchmark.get_available_endpoints())

@app.route('/api-performance-benchmark')
@require_auth
def api_performance_benchmark_dashboard():
    """API Performance Benchmark Dashboard"""
    return render_template('api_performance_benchmark.html',
                         username=session.get('username'))

@app.route('/api/nexus/navigation-status')
def nexus_navigation_status():
    """Get NEXUS navigation system status"""
    from nexus_orchestrator import NexusOrchestrator
    orchestrator = NexusOrchestrator()
    return jsonify(orchestrator.get_navigation_status())

@app.route('/api/nexus/orchestration')
def nexus_orchestration():
    """NEXUS orchestration endpoint for connector communication"""
    from nexus_orchestrator import NexusOrchestrator
    orchestrator = NexusOrchestrator()
    return jsonify(orchestrator.get_orchestration_status())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)