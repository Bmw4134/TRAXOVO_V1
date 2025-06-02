# TRAXOVO DEPLOYMENT MASTER DIRECTIVE
## Universal Flask Dashboard Recovery & Deployment Protocol

### EMERGENCY RECOVERY SEQUENCE
```bash
# 1. IMMEDIATE STABILIZATION
git status  # Check current state
cp -r . ../backup_$(date +%Y%m%d_%H%M%S)  # Emergency backup

# 2. CORE RESTORATION
python emergency_restore.py  # Automated recovery
flask db upgrade  # Database sync
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app  # Start server
```

### AUTHENTICATION FOUNDATION
**Core Login System (app.py)**
```python
# SESSION MANAGEMENT
app.secret_key = os.environ.get("SESSION_SECRET")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

# AUTHENTICATION FUNCTION
def require_auth():
    return 'username' not in session

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if (username == 'watson' and password == 'password') or \
           (username == 'admin' and password == 'password') or \
           (username == 'tester' and password == 'password'):
            session['username'] = username
            session['user_role'] = 'admin' if username in ['watson', 'admin'] else 'user'
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')
```

### BLUEPRINT ARCHITECTURE
**Master Blueprint Registration Pattern**
```python
# Import all blueprints
from routes.billing import billing_bp
from routes.master_billing import master_billing_bp
from routes.admin_guide import admin_guide_bp
from routes.ai_intelligence import ai_intelligence_bp

# Register in correct order
app.register_blueprint(billing_bp)
app.register_blueprint(master_billing_bp)
app.register_blueprint(admin_guide_bp)
app.register_blueprint(ai_intelligence_bp)
```

### DASHBOARD FOUNDATION
**Universal Dashboard Template Structure**
```html
<!-- templates/dashboard_with_sidebar.html -->
<div class="sidebar-nav">
    <a href="/dashboard" class="nav-link active">Dashboard</a>
    <a href="/attendance-matrix" class="nav-link">Attendance</a>
    <a href="/fleet-map" class="nav-link">Fleet Map</a>
    <a href="/asset-manager" class="nav-link">Assets</a>
    <a href="/billing" class="nav-link">Billing Intelligence</a>
    <a href="/ai-intelligence" class="nav-link">AI Intelligence Center</a>
    <a href="/upload" class="nav-link">Upload</a>
    <a href="/safemode" class="nav-link">SafeMode</a>
    <a href="/logout" class="nav-link text-danger">Logout</a>
</div>
```

### ROUTE PROTECTION PATTERN
```python
@app.route('/protected-route')
def protected_route():
    if require_auth():
        return redirect(url_for('login'))
    # Route logic here
    return render_template('template.html')
```

### ERROR HANDLING FOUNDATION
```python
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
```

### DATABASE INTEGRATION
```python
# models.py foundation
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Database initialization
with app.app_context():
    import models
    db.create_all()
```

### DEPLOYMENT CHECKLIST
- [ ] Authentication routes working (watson/password)
- [ ] Database connection established
- [ ] All blueprints registered
- [ ] Static files serving
- [ ] Templates rendering
- [ ] Error handlers active
- [ ] Session management working
- [ ] Gunicorn server stable

### BROKEN DASHBOARD RECOVERY STEPS
1. **Backup Current State**: `cp -r . ../emergency_backup`
2. **Apply Core Structure**: Copy authentication system from this directive
3. **Register Blueprints**: Follow blueprint registration pattern
4. **Fix Templates**: Ensure base.html and dashboard structure exists
5. **Database Sync**: Run `flask db upgrade` if using migrations
6. **Test Authentication**: Verify watson/password login works
7. **Deploy**: Use `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`

### REPLICATION PROTOCOL
To replicate TRAXOVO success to broken dashboard:
1. Copy entire `app.py` authentication system
2. Copy `templates/base.html` and `templates/login.html`
3. Copy `templates/dashboard_with_sidebar.html` structure
4. Apply blueprint registration pattern
5. Implement route protection using `require_auth()`
6. Test with watson/password credentials

This directive provides universal recovery for any Flask dashboard using the proven TRAXOVO architecture.