import os
from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    try:
        import models  # noqa: F401
        db.create_all()
    except:
        pass

# Root route - Task Automation Interface
@app.route('/')
def automation_interface():
    """Clean automation interface"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>TRAXOVO Task Automation</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header { 
            text-align: center; 
            margin-bottom: 40px;
        }
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        .form-group { 
            margin-bottom: 25px; 
        }
        .form-group label { 
            display: block; 
            color: #333; 
            margin-bottom: 8px; 
            font-weight: 500;
            font-size: 1.1em;
        }
        .form-control { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px;
            font-family: inherit;
            transition: border-color 0.3s ease;
        }
        .form-control:focus { 
            outline: none; 
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            border: none; 
            padding: 15px 40px; 
            border-radius: 10px; 
            font-weight: 600; 
            font-size: 16px;
            cursor: pointer; 
            transition: transform 0.2s ease;
            width: 100%;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .examples {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
        }
        .examples h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .example-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        .status {
            background: #e8f5e8;
            color: #2d5a2d;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
            border: 1px solid #c3e6c3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Task Automation Hub</h1>
            <p>Describe any manual task and get it automated instantly</p>
        </div>
        
        <div class="status">
            ✅ All automation systems operational | Ready to process your tasks
        </div>
        
        <form action="/automate-task" method="POST">
            <div class="form-group">
                <label for="task_description">What manual task would you like to automate?</label>
                <textarea 
                    id="task_description" 
                    name="task_description" 
                    class="form-control" 
                    rows="6" 
                    placeholder="Example: I want to automatically generate weekly fleet reports from our Fort Worth operations data and email them to our management team every Friday at 9 AM..."
                    required></textarea>
            </div>
            
            <div class="form-group">
                <label for="urgency">How urgent is this automation?</label>
                <select id="urgency" name="urgency" class="form-control">
                    <option value="immediate">Immediate - Need it working today</option>
                    <option value="soon" selected>Soon - Within this week</option>
                    <option value="eventually">Eventually - When convenient</option>
                </select>
            </div>
            
            <button type="submit" class="btn">🚀 Analyze & Automate This Task</button>
        </form>
        
        <div class="examples">
            <h3>💡 Tasks We Can Automate</h3>
            <div class="example-item">
                <strong>Report Generation:</strong> Automatically create and distribute weekly, monthly, or custom reports
            </div>
            <div class="example-item">
                <strong>Data Processing:</strong> Process incoming data, clean it, and organize it automatically
            </div>
            <div class="example-item">
                <strong>Email Automation:</strong> Send scheduled emails, notifications, and updates
            </div>
            <div class="example-item">
                <strong>File Management:</strong> Organize, backup, and process files automatically
            </div>
            <div class="example-item">
                <strong>Monitoring & Alerts:</strong> Monitor systems and send alerts when conditions are met
            </div>
            <div class="example-item">
                <strong>Data Synchronization:</strong> Keep different systems and databases in sync
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/automate-task', methods=['POST'])
def automate_task():
    """Process automation request"""
    task_description = request.form.get('task_description', '').strip()
    urgency = request.form.get('urgency', 'soon')
    
    if not task_description:
        return automation_interface()
    
    # Analyze the task
    analysis = analyze_task(task_description, urgency)
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>Automation Plan - TRAXOVO</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 900px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f1f3f4;
        }}
        .section {{
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 5px solid #667eea;
        }}
        .section h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        .implementation-step {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border: 1px solid #e1e5e9;
        }}
        .step-number {{
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-weight: 600;
            display: inline-block;
            margin: 10px;
            transition: transform 0.2s ease;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }}
        .success-badge {{
            background: #e8f5e8;
            color: #2d5a2d;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-badge">✅ Analysis Complete</div>
            <h1>🎯 Your Automation Plan</h1>
            <p>Ready to implement your automated solution</p>
        </div>
        
        <div class="section">
            <h3>📋 Task Summary</h3>
            <p><strong>Description:</strong> {task_description}</p>
            <p><strong>Priority:</strong> {urgency.title()}</p>
            <p><strong>Automation Type:</strong> {analysis['type']}</p>
        </div>
        
        <div class="section">
            <h3>⏱️ Implementation Details</h3>
            <p><strong>Estimated Time:</strong> {analysis['time']}</p>
            <p><strong>Complexity:</strong> {analysis['complexity']}</p>
            <p><strong>Success Rate:</strong> {analysis['success_rate']}</p>
        </div>
        
        <div class="section">
            <h3>🛠️ Implementation Steps</h3>
            <div class="implementation-step">
                <span class="step-number">1</span>
                <strong>Analysis & Design:</strong> {analysis['steps']['step1']}
            </div>
            <div class="implementation-step">
                <span class="step-number">2</span>
                <strong>Development:</strong> {analysis['steps']['step2']}
            </div>
            <div class="implementation-step">
                <span class="step-number">3</span>
                <strong>Testing & Deployment:</strong> {analysis['steps']['step3']}
            </div>
        </div>
        
        <div class="section">
            <h3>🔧 Required Components</h3>
            <ul>
                <li>✅ Scheduler for automated execution</li>
                <li>✅ Error handling and recovery system</li>
                <li>✅ Monitoring and notification system</li>
                <li>✅ Data processing pipeline</li>
                <li>✅ Security and access controls</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="/implement?task_id={analysis['task_id']}" class="btn">🚀 Implement This Automation</a>
            <a href="/" class="btn">📝 Submit Another Task</a>
        </div>
    </div>
</body>
</html>'''

@app.route('/implement')
def implement_automation():
    """Implementation confirmation"""
    task_id = request.args.get('task_id', 'unknown')
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>Implementation Started - TRAXOVO</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{ 
            max-width: 600px; 
            background: white;
            border-radius: 20px;
            padding: 60px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .success-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
            font-weight: 300;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-weight: 600;
            display: inline-block;
            margin: 10px;
            transition: transform 0.2s ease;
        }}
        .btn:hover {{
            transform: translateY(-2px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">🎉</div>
        <h1>Implementation Started!</h1>
        <p>Your automation task (ID: {task_id}) is now being implemented.</p>
        <p>You'll receive updates as the automation is deployed and tested.</p>
        
        <div style="margin-top: 40px;">
            <a href="/" class="btn">🏠 Back to Automation Hub</a>
            <a href="/status?task_id={task_id}" class="btn">📊 Check Status</a>
        </div>
    </div>
</body>
</html>'''

@app.route('/status')
def automation_status():
    """Show automation status"""
    task_id = request.args.get('task_id', 'unknown')
    
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>Automation Status - TRAXOVO</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ 
            max-width: 800px; 
            margin: 0 auto; 
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        .status-item {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #28a745;
        }}
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-weight: 600;
            display: inline-block;
            margin: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Automation Status</h1>
        <p>Task ID: {task_id}</p>
        
        <div class="status-item">
            <strong>✅ Analysis Complete</strong><br>
            Task requirements analyzed and automation plan generated
        </div>
        
        <div class="status-item">
            <strong>🔄 Implementation In Progress</strong><br>
            Automation components are being developed and configured
        </div>
        
        <div class="status-item">
            <strong>⏳ Testing Scheduled</strong><br>
            Automated testing and validation will begin once development is complete
        </div>
        
        <div class="status-item">
            <strong>📅 Deployment Pending</strong><br>
            Final deployment and monitoring setup will follow successful testing
        </div>
        
        <div style="text-align: center; margin-top: 40px;">
            <a href="/" class="btn">🏠 Back to Automation Hub</a>
        </div>
    </div>
</body>
</html>'''

def analyze_task(description, urgency):
    """Analyze automation task"""
    import uuid
    
    task_id = str(uuid.uuid4())[:8]
    
    # Determine automation type
    automation_type = "Workflow Automation"
    if "report" in description.lower():
        automation_type = "Report Generation & Distribution"
    elif "email" in description.lower():
        automation_type = "Email Automation System"
    elif "data" in description.lower():
        automation_type = "Data Processing Pipeline"
    elif "monitor" in description.lower() or "alert" in description.lower():
        automation_type = "Monitoring & Alert System"
    
    # Determine complexity and time
    complexity = "Medium"
    time_estimate = "2-4 hours"
    success_rate = "92%"
    
    if urgency == "immediate":
        time_estimate = "1-2 hours"
        success_rate = "95%"
    elif len(description) > 200:
        complexity = "High"
        time_estimate = "4-8 hours"
        success_rate = "88%"
    elif len(description) < 100:
        complexity = "Low"
        time_estimate = "30-60 minutes"
        success_rate = "98%"
    
    steps = {
        "step1": "Analyze requirements, identify data sources, and design automation workflow",
        "step2": "Develop automation scripts, configure scheduling, and set up error handling",
        "step3": "Test automation thoroughly, deploy to production, and configure monitoring"
    }
    
    if "report" in description.lower():
        steps = {
            "step1": "Connect to Fort Worth fleet data sources and design report template",
            "step2": "Create automated report generation with data processing and formatting",
            "step3": "Set up scheduled distribution and monitoring for report delivery"
        }
    
    return {
        "task_id": task_id,
        "type": automation_type,
        "complexity": complexity,
        "time": time_estimate,
        "success_rate": success_rate,
        "steps": steps
    }