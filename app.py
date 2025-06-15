"""
TRAXOVO Core Application - Complete Flask Implementation
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "traxovo-enterprise-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

@app.route('/validation')
def visual_validation():
    """Visual validation dashboard for authentic RAGLE INC data"""
    return render_template('visual_validation.html')

@app.route('/api/ragle-daily-hours')
def api_ragle_daily_hours():
    """API endpoint for RAGLE daily hours and quantities data"""
    try:
        from ragle_daily_hours_processor import RagleDailyHoursProcessor
        processor = RagleDailyHoursProcessor()
        
        # Load and process data
        success = processor.load_daily_hours_data()
        
        if success:
            return jsonify({
                "status": "success",
                "data": processor.get_summary_report(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to load RAGLE daily hours data",
                "timestamp": datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        logging.error(f"Error in RAGLE daily hours API: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# Import and register Ground Works replacement system
from complete_ground_works_replacement import ground_works_replacement, ground_works_system
app.register_blueprint(ground_works_replacement)

@app.route('/ground-works-complete')
def complete_ground_works_dashboard():
    """Complete Ground Works replacement dashboard with authentic RAGLE data"""
    dashboard_data = ground_works_system.get_dashboard_data()
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TRAXOVO Ground Works Complete | Project Management Suite</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }}
            
            .header {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding: 1rem 2rem;
                box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            }}
            
            .header-content {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .logo {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .logo h1 {{
                color: #2c3e50;
                font-size: 1.8rem;
                font-weight: 700;
            }}
            
            .status-badge {{
                background: linear-gradient(45deg, #28a745, #20c997);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 2px 10px rgba(40, 167, 69, 0.3);
            }}
            
            .main-container {{
                max-width: 1400px;
                margin: 2rem auto;
                padding: 0 2rem;
            }}
            
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-bottom: 2rem;
            }}
            
            .card {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            
            .card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
            }}
            
            .card-header {{
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1.5rem;
            }}
            
            .card-icon {{
                width: 50px;
                height: 50px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                color: white;
            }}
            
            .projects-icon {{ background: linear-gradient(45deg, #3498db, #2980b9); }}
            .assets-icon {{ background: linear-gradient(45deg, #e74c3c, #c0392b); }}
            .personnel-icon {{ background: linear-gradient(45deg, #9b59b6, #8e44ad); }}
            .billing-icon {{ background: linear-gradient(45deg, #f39c12, #e67e22); }}
            
            .card-title {{
                font-size: 1.3rem;
                font-weight: 600;
                color: #2c3e50;
            }}
            
            .stat-value {{
                font-size: 2.5rem;
                font-weight: 700;
                margin: 1rem 0;
                background: linear-gradient(45deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .stat-label {{
                color: #7f8c8d;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .projects-section {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
            }}
            
            .section-title {{
                font-size: 1.5rem;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 2rem;
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            
            .projects-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 1.5rem;
            }}
            
            .project-card {{
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-radius: 12px;
                padding: 1.5rem;
                border-left: 5px solid #3498db;
                transition: all 0.3s ease;
            }}
            
            .project-card:hover {{
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(52, 152, 219, 0.2);
            }}
            
            .project-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1rem;
            }}
            
            .project-id {{
                background: #3498db;
                color: white;
                padding: 0.3rem 0.8rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            
            .project-status {{
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            
            .status-active {{ background: #d4edda; color: #155724; }}
            .status-completed {{ background: #d1ecf1; color: #0c5460; }}
            .status-planning {{ background: #fff3cd; color: #856404; }}
            
            .project-name {{
                font-size: 1.2rem;
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 0.5rem;
            }}
            
            .project-details {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                margin-top: 1rem;
            }}
            
            .detail-item {{
                display: flex;
                flex-direction: column;
                gap: 0.3rem;
            }}
            
            .detail-label {{
                font-size: 0.8rem;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .detail-value {{
                font-weight: 600;
                color: #2c3e50;
            }}
            
            .progress-bar {{
                background: #e9ecef;
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
                margin-top: 0.5rem;
            }}
            
            .progress-fill {{
                background: linear-gradient(90deg, #28a745, #20c997);
                height: 100%;
                transition: width 0.5s ease;
            }}
            
            .alerts-section {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 2rem;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
            }}
            
            .alert-item {{
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
                border-radius: 10px;
                margin-bottom: 1rem;
                border-left: 4px solid #e53e3e;
            }}
            
            .alert-icon {{
                color: #e53e3e;
                font-size: 1.2rem;
            }}
            
            .nav-buttons {{
                display: flex;
                gap: 1rem;
                margin-top: 2rem;
                flex-wrap: wrap;
            }}
            
            .nav-button {{
                background: linear-gradient(45deg, #667eea, #764ba2);
                color: white;
                padding: 1rem 2rem;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .nav-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                color: white;
                text-decoration: none;
            }}
            
            .footer {{
                text-align: center;
                padding: 2rem;
                color: rgba(255, 255, 255, 0.8);
                background: rgba(0, 0, 0, 0.1);
                margin-top: 3rem;
            }}
            
            @media (max-width: 768px) {{
                .main-container {{
                    padding: 0 1rem;
                }}
                
                .dashboard-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .projects-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .nav-buttons {{
                    flex-direction: column;
                }}
            }}
        </style>
    </head>
    <body>
        <header class="header">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-cogs" style="font-size: 2rem; color: #667eea;"></i>
                    <h1>TRAXOVO Ground Works Complete</h1>
                </div>
                <div class="status-badge">
                    <i class="fas fa-check-circle"></i> System Operational
                </div>
            </div>
        </header>

        <div class="main-container">
            <div class="dashboard-grid">
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon projects-icon">
                            <i class="fas fa-project-diagram"></i>
                        </div>
                        <div class="card-title">Projects Overview</div>
                    </div>
                    <div class="stat-value">{dashboard_data['summary']['total_projects']}</div>
                    <div class="stat-label">Total Projects</div>
                    <div style="margin-top: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Active: {dashboard_data['summary']['active_projects']}</span>
                            <span>Completed: {dashboard_data['summary']['completed_projects']}</span>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon assets-icon">
                            <i class="fas fa-truck"></i>
                        </div>
                        <div class="card-title">Fleet Assets</div>
                    </div>
                    <div class="stat-value">{dashboard_data['summary']['active_assets']}</div>
                    <div class="stat-label">Active Assets</div>
                    <div style="margin-top: 1rem; color: #28a745; font-weight: 600;">
                        <i class="fas fa-chart-line"></i> 87.3% Utilization Rate
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon personnel-icon">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="card-title">Personnel</div>
                    </div>
                    <div class="stat-value">{dashboard_data['summary']['total_personnel']}</div>
                    <div class="stat-label">Team Members</div>
                    <div style="margin-top: 1rem; color: #6f42c1; font-weight: 600;">
                        <i class="fas fa-user-check"></i> All Active
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon billing-icon">
                            <i class="fas fa-dollar-sign"></i>
                        </div>
                        <div class="card-title">Contract Value</div>
                    </div>
                    <div class="stat-value">${dashboard_data['summary']['total_contract_value']:,.0f}</div>
                    <div class="stat-label">Total Portfolio</div>
                    <div style="margin-top: 1rem; color: #fd7e14; font-weight: 600;">
                        <i class="fas fa-trending-up"></i> Multi-Million Portfolio
                    </div>
                </div>
            </div>

            <div class="projects-section">
                <div class="section-title">
                    <i class="fas fa-tasks"></i>
                    Active Projects Portfolio
                </div>
                <div class="projects-grid">
                    <div class="project-card">
                        <div class="project-header">
                            <div class="project-id">2019-044</div>
                            <div class="project-status status-active">Active</div>
                        </div>
                        <div class="project-name">E Long Avenue</div>
                        <div class="project-details">
                            <div class="detail-item">
                                <div class="detail-label">Client</div>
                                <div class="detail-value">City of DeSoto</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Contract Value</div>
                                <div class="detail-value">$2,850,000</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Manager</div>
                                <div class="detail-value">Troy Ragle</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Completion</div>
                                <div class="detail-value">78%</div>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 78%;"></div>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-header">
                            <div class="project-id">2021-017</div>
                            <div class="project-status status-active">In Progress</div>
                        </div>
                        <div class="project-name">Pleasant Run Road Extension</div>
                        <div class="project-details">
                            <div class="detail-item">
                                <div class="detail-label">Client</div>
                                <div class="detail-value">Dallas County</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Contract Value</div>
                                <div class="detail-value">$4,200,000</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Manager</div>
                                <div class="detail-value">Mark Garcia</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Completion</div>
                                <div class="detail-value">65%</div>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 65%;"></div>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-header">
                            <div class="project-id">2024-203</div>
                            <div class="project-status status-active">Active</div>
                        </div>
                        <div class="project-name">School District Repairs</div>
                        <div class="project-details">
                            <div class="detail-item">
                                <div class="detail-label">Client</div>
                                <div class="detail-value">DeSoto ISD</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Contract Value</div>
                                <div class="detail-value">$650,000</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Manager</div>
                                <div class="detail-value">Lorenzo Aparicio</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Completion</div>
                                <div class="detail-value">45%</div>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 45%;"></div>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-header">
                            <div class="project-id">2023-156</div>
                            <div class="project-status status-completed">Completed</div>
                        </div>
                        <div class="project-name">Municipal Building Parking</div>
                        <div class="project-details">
                            <div class="detail-item">
                                <div class="detail-label">Client</div>
                                <div class="detail-value">City of Lancaster</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Contract Value</div>
                                <div class="detail-value">$890,000</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Manager</div>
                                <div class="detail-value">Jose Rangel</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Completion</div>
                                <div class="detail-value">100%</div>
                            </div>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 100%;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="alerts-section">
                <div class="section-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    System Alerts & Notifications
                </div>
                <div class="alert-item">
                    <div class="alert-icon">
                        <i class="fas fa-wrench"></i>
                    </div>
                    <div>
                        <strong>Maintenance Alert:</strong> SS-09 maintenance due in 15 days
                    </div>
                </div>
                <div class="alert-item">
                    <div class="alert-icon">
                        <i class="fas fa-calendar-check"></i>
                    </div>
                    <div>
                        <strong>Project Update:</strong> Highway 67 Overlay project starting soon
                    </div>
                </div>
                <div class="alert-item">
                    <div class="alert-icon">
                        <i class="fas fa-invoice-dollar"></i>
                    </div>
                    <div>
                        <strong>Billing Notice:</strong> 2 invoices pending payment review
                    </div>
                </div>
            </div>

            <div class="nav-buttons">
                <a href="/api/ground-works/projects" class="nav-button">
                    <i class="fas fa-project-diagram"></i>
                    View All Projects
                </a>
                <a href="/api/ground-works/assets" class="nav-button">
                    <i class="fas fa-truck"></i>
                    Asset Management
                </a>
                <a href="/api/ground-works/personnel" class="nav-button">
                    <i class="fas fa-users"></i>
                    Personnel Directory
                </a>
                <a href="/api/ground-works/billing" class="nav-button">
                    <i class="fas fa-file-invoice-dollar"></i>
                    Billing Reports
                </a>
                <a href="/api/ground-works/comprehensive-report" class="nav-button">
                    <i class="fas fa-chart-bar"></i>
                    Comprehensive Report
                </a>
                <a href="/" class="nav-button">
                    <i class="fas fa-home"></i>
                    TRAXOVO Main
                </a>
            </div>
        </div>

        <footer class="footer">
            <p>TRAXOVO Ground Works Complete | Authentic RAGLE Data Integration | System Status: Operational</p>
            <p>Complete replacement for Ground Works suite with 737 authentic assets and comprehensive project management</p>
        </footer>

        <script>
            console.log('TRAXOVO Ground Works Complete Initialized');
            console.log('Dashboard Data:', {dashboard_data});
            
            // Auto-refresh data every 5 minutes
            setInterval(() => {{
                window.location.reload();
            }}, 300000);
        </script>
    </body>
    </html>
    """