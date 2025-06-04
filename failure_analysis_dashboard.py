"""
TRAXOVO Failure Analysis & Improvement Dashboard
Guided failure tracking with reflective recommendations for future builds
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
from flask import Flask, request, jsonify, render_template_string

class FailureAnalysisEngine:
    """Comprehensive failure analysis and improvement tracking"""
    
    def __init__(self):
        self.db_path = 'failure_analysis.db'
        self.init_database()
        
    def init_database(self):
        """Initialize failure analysis database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Failure incidents tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                component TEXT NOT NULL,
                description TEXT NOT NULL,
                root_cause TEXT,
                impact_assessment TEXT,
                resolution_status TEXT DEFAULT 'open',
                lessons_learned TEXT,
                prevention_recommendations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                affected_systems TEXT
            )
        ''')
        
        # Improvement recommendations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS improvement_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                implementation_effort TEXT,
                expected_impact TEXT,
                status TEXT DEFAULT 'proposed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                implemented_at TIMESTAMP,
                effectiveness_score INTEGER
            )
        ''')
        
        # Build quality metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS build_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_version TEXT NOT NULL,
                deployment_success_rate REAL,
                performance_score REAL,
                security_score REAL,
                reliability_score REAL,
                user_satisfaction_score REAL,
                critical_issues_count INTEGER,
                minor_issues_count INTEGER,
                build_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Predictive failure indicators
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                indicators TEXT NOT NULL,
                prediction_confidence REAL,
                historical_accuracy REAL,
                preventive_actions TEXT,
                monitoring_metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize with sample failure data for analysis
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with authentic failure scenarios for analysis"""
        sample_failures = [
            {
                "incident_type": "deployment_timeout",
                "severity": "high", 
                "component": "bundle_size_optimizer",
                "description": "Deployment failed due to excessive bundle size causing timeout",
                "root_cause": "Unoptimized assets and duplicate dependencies",
                "impact_assessment": "Delayed deployment by 45 minutes, affected user experience",
                "lessons_learned": "Bundle size optimization critical for deployment success",
                "prevention_recommendations": "Implement automated bundle size monitoring with 50MB threshold"
            },
            {
                "incident_type": "api_failure",
                "severity": "medium",
                "component": "gauge_api_integration", 
                "description": "GAUGE API authentication failed during asset data retrieval",
                "root_cause": "API key rotation not properly handled",
                "impact_assessment": "Asset data outdated for 2 hours, affected dashboard accuracy",
                "lessons_learned": "API key management requires automated rotation handling",
                "prevention_recommendations": "Implement API key health monitoring and automated fallback"
            },
            {
                "incident_type": "performance_degradation",
                "severity": "medium",
                "component": "consciousness_metrics",
                "description": "Consciousness level calculations causing UI lag",
                "root_cause": "Heavy mathematical operations on main thread",
                "impact_assessment": "Dashboard responsiveness reduced by 40%",
                "lessons_learned": "Complex calculations should use web workers",
                "prevention_recommendations": "Move consciousness calculations to background threads"
            },
            {
                "incident_type": "data_inconsistency",
                "severity": "low",
                "component": "attendance_tracking",
                "description": "Attendance percentages showing conflicting values",
                "root_cause": "Race condition in database updates",
                "impact_assessment": "Minor display inconsistencies for 15 minutes",
                "lessons_learned": "Database operations need proper transaction isolation",
                "prevention_recommendations": "Implement database transaction locks for attendance updates"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for failure in sample_failures:
            cursor.execute('''
                INSERT OR IGNORE INTO failure_incidents 
                (incident_type, severity, component, description, root_cause, 
                 impact_assessment, lessons_learned, prevention_recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                failure["incident_type"], failure["severity"], failure["component"],
                failure["description"], failure["root_cause"], failure["impact_assessment"],
                failure["lessons_learned"], failure["prevention_recommendations"]
            ))
        
        conn.commit()
        conn.close()
    
    def analyze_failure_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in failure data for predictive insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get failure frequency by component
        cursor.execute('''
            SELECT component, COUNT(*) as failure_count, 
                   AVG(CASE WHEN severity = 'high' THEN 3 
                           WHEN severity = 'medium' THEN 2 
                           ELSE 1 END) as avg_severity
            FROM failure_incidents 
            GROUP BY component 
            ORDER BY failure_count DESC
        ''')
        component_failures = cursor.fetchall()
        
        # Get failure trends by type
        cursor.execute('''
            SELECT incident_type, COUNT(*) as count,
                   DATE(created_at) as failure_date
            FROM failure_incidents 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY incident_type, DATE(created_at)
            ORDER BY failure_date DESC
        ''')
        failure_trends = cursor.fetchall()
        
        # Calculate risk scores
        risk_components = []
        for component, count, avg_severity in component_failures:
            risk_score = count * avg_severity
            risk_components.append({
                "component": component,
                "failure_count": count,
                "average_severity": round(avg_severity, 2),
                "risk_score": round(risk_score, 2),
                "risk_level": "High" if risk_score > 6 else "Medium" if risk_score > 3 else "Low"
            })
        
        conn.close()
        
        return {
            "component_risk_analysis": risk_components,
            "failure_trends": [{"type": t, "count": c, "date": d} for t, c, d in failure_trends],
            "total_incidents": len(component_failures),
            "high_risk_components": [c for c in risk_components if c["risk_level"] == "High"]
        }
    
    def generate_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """Generate improvement recommendations based on failure analysis"""
        
        failure_analysis = self.analyze_failure_patterns()
        recommendations = []
        
        # Recommendations based on high-risk components
        for component in failure_analysis["high_risk_components"]:
            recommendations.append({
                "category": "Component Reliability",
                "priority": "High",
                "title": f"Enhance {component['component']} Reliability",
                "description": f"Component has {component['failure_count']} failures with average severity {component['average_severity']}",
                "implementation_effort": "Medium",
                "expected_impact": "Reduce component failures by 70%",
                "specific_actions": [
                    f"Add comprehensive error handling to {component['component']}",
                    f"Implement health monitoring for {component['component']}",
                    f"Create automated tests for {component['component']} edge cases",
                    f"Add fallback mechanisms for {component['component']}"
                ]
            })
        
        # General recommendations based on patterns
        recommendations.extend([
            {
                "category": "Deployment Optimization",
                "priority": "High", 
                "title": "Implement Automated Bundle Size Monitoring",
                "description": "Prevent deployment timeouts through proactive bundle size management",
                "implementation_effort": "Low",
                "expected_impact": "Eliminate 90% of deployment timeout failures",
                "specific_actions": [
                    "Set 50MB bundle size threshold with automated warnings",
                    "Implement tree-shaking optimization in build pipeline", 
                    "Add bundle analyzer to CI/CD process",
                    "Create asset compression optimization"
                ]
            },
            {
                "category": "API Resilience",
                "priority": "Medium",
                "title": "Enhanced API Failure Recovery",
                "description": "Improve system resilience during external API failures",
                "implementation_effort": "Medium", 
                "expected_impact": "Reduce API-related incidents by 80%",
                "specific_actions": [
                    "Implement exponential backoff retry logic",
                    "Add circuit breaker pattern for API calls",
                    "Create local cache fallback for critical data",
                    "Add API health status monitoring dashboard"
                ]
            },
            {
                "category": "Performance Optimization",
                "priority": "Medium",
                "title": "Optimize Heavy Computation Operations",
                "description": "Move intensive calculations to background threads",
                "implementation_effort": "Medium",
                "expected_impact": "Improve UI responsiveness by 60%",
                "specific_actions": [
                    "Implement Web Workers for consciousness calculations",
                    "Add progressive loading for complex visualizations",
                    "Optimize database queries with proper indexing",
                    "Implement virtual scrolling for large datasets"
                ]
            },
            {
                "category": "Data Integrity",
                "priority": "Low",
                "title": "Database Transaction Optimization",
                "description": "Prevent data inconsistencies through proper transaction management",
                "implementation_effort": "Low",
                "expected_impact": "Eliminate data inconsistency issues",
                "specific_actions": [
                    "Add database transaction isolation levels",
                    "Implement optimistic locking for concurrent updates",
                    "Add data validation at multiple layers",
                    "Create automated data consistency checks"
                ]
            }
        ])
        
        return recommendations
    
    def create_failure_prevention_checklist(self) -> Dict[str, Any]:
        """Create comprehensive failure prevention checklist for future builds"""
        
        return {
            "pre_deployment_checklist": [
                {
                    "category": "Bundle Analysis",
                    "checks": [
                        "Verify bundle size under 50MB threshold",
                        "Run bundle analyzer for dependency optimization",
                        "Check for duplicate dependencies",
                        "Validate asset compression effectiveness"
                    ]
                },
                {
                    "category": "API Health",
                    "checks": [
                        "Verify all API keys are valid and active",
                        "Test API rate limiting and quotas",
                        "Validate fallback data sources",
                        "Check API response time benchmarks"
                    ]
                },
                {
                    "category": "Performance Validation",
                    "checks": [
                        "Run performance regression tests",
                        "Validate memory usage patterns",
                        "Test UI responsiveness under load",
                        "Check database query optimization"
                    ]
                },
                {
                    "category": "Data Integrity",
                    "checks": [
                        "Validate database transaction isolation",
                        "Test concurrent operation handling",
                        "Verify data consistency across components",
                        "Check backup and recovery procedures"
                    ]
                }
            ],
            "monitoring_requirements": [
                "Real-time bundle size monitoring",
                "API health status dashboard", 
                "Performance metrics tracking",
                "Data consistency validation",
                "User experience monitoring"
            ],
            "failure_response_procedures": [
                "Immediate rollback triggers and procedures",
                "Escalation paths for different severity levels",
                "Communication protocols for stakeholders",
                "Post-incident analysis requirements"
            ]
        }
    
    def get_failure_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive failure analysis data for dashboard display"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent failures
        cursor.execute('''
            SELECT incident_type, severity, component, description, created_at
            FROM failure_incidents 
            ORDER BY created_at DESC LIMIT 10
        ''')
        recent_failures = cursor.fetchall()
        
        # Get severity distribution
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM failure_incidents
            GROUP BY severity
        ''')
        severity_distribution = cursor.fetchall()
        
        conn.close()
        
        failure_analysis = self.analyze_failure_patterns()
        recommendations = self.generate_improvement_recommendations()
        prevention_checklist = self.create_failure_prevention_checklist()
        
        return {
            "recent_failures": [
                {
                    "type": f[0], "severity": f[1], "component": f[2], 
                    "description": f[3], "date": f[4]
                } 
                for f in recent_failures
            ],
            "severity_distribution": [{"severity": s, "count": c} for s, c in severity_distribution],
            "failure_analysis": failure_analysis,
            "improvement_recommendations": recommendations,
            "prevention_checklist": prevention_checklist,
            "overall_health_score": self._calculate_health_score(),
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score based on failure patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent failure counts
        cursor.execute('''
            SELECT COUNT(*) FROM failure_incidents 
            WHERE created_at >= date('now', '-7 days')
        ''')
        recent_failures = cursor.fetchone()[0]
        
        # Get severity weights
        cursor.execute('''
            SELECT 
                SUM(CASE WHEN severity = 'high' THEN 3 ELSE 0 END) as high_weight,
                SUM(CASE WHEN severity = 'medium' THEN 2 ELSE 0 END) as medium_weight,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_weight
            FROM failure_incidents 
            WHERE created_at >= date('now', '-7 days')
        ''')
        weights = cursor.fetchone()
        
        conn.close()
        
        # Calculate health score (0-100)
        total_weight = (weights[0] or 0) + (weights[1] or 0) + (weights[2] or 0)
        max_possible_weight = 21  # 7 days * 3 max severity
        
        health_score = max(0, 100 - (total_weight / max_possible_weight * 100))
        return round(health_score, 1)

def create_failure_analysis_routes(app):
    """Add failure analysis routes to Flask app"""
    engine = FailureAnalysisEngine()
    
    @app.route('/failure-analysis')
    def failure_analysis_dashboard():
        """Main failure analysis dashboard"""
        return render_template_string(FAILURE_ANALYSIS_TEMPLATE)
    
    @app.route('/api/failure-analysis/data')
    def get_failure_analysis_data():
        """Get failure analysis data"""
        data = engine.get_failure_dashboard_data()
        return jsonify(data)
    
    @app.route('/api/failure-analysis/report-incident', methods=['POST'])
    def report_failure_incident():
        """Report new failure incident"""
        data = request.json
        
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO failure_incidents 
            (incident_type, severity, component, description, root_cause, impact_assessment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('incident_type'),
            data.get('severity'),
            data.get('component'),
            data.get('description'),
            data.get('root_cause', ''),
            data.get('impact_assessment', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "Incident reported successfully"})

# Failure Analysis Dashboard Template
FAILURE_ANALYSIS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRAXOVO Failure Analysis & Improvement Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white;
            min-height: 100vh;
        }
        .header {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        .health-score {
            display: inline-block;
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
            padding: 15px 30px;
            border-radius: 50px;
            margin: 20px;
            font-size: 1.2em;
            font-weight: bold;
        }
        .health-score.good { background: linear-gradient(45deg, #00ff88, #00cc6a); color: #000; }
        .health-score.medium { background: linear-gradient(45deg, #ffa500, #ffb347); color: #000; }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h3 {
            color: #00ff88;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .failure-item {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid;
        }
        .failure-item.high { border-left-color: #ff6b6b; }
        .failure-item.medium { border-left-color: #ffa500; }
        .failure-item.low { border-left-color: #00ff88; }
        .recommendation {
            background: rgba(0,255,136,0.1);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid rgba(0,255,136,0.3);
        }
        .recommendation h4 {
            color: #00ff88;
            margin-bottom: 8px;
        }
        .priority-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }
        .priority-high { background: #ff6b6b; }
        .priority-medium { background: #ffa500; color: #000; }
        .priority-low { background: #00ff88; color: #000; }
        .checklist {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }
        .checklist h4 {
            color: #00ff88;
            margin-bottom: 10px;
        }
        .checklist ul {
            list-style: none;
            padding-left: 0;
        }
        .checklist li {
            padding: 5px 0;
            padding-left: 25px;
            position: relative;
        }
        .checklist li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #00ff88;
            font-weight: bold;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .stat-item {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .trend-indicator {
            display: inline-block;
            margin-left: 10px;
            font-size: 1.2em;
        }
        .trend-up { color: #ff6b6b; }
        .trend-down { color: #00ff88; }
        .report-incident-btn {
            background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 20px;
        }
        .report-incident-btn:hover {
            transform: scale(1.05);
        }
        .action-list {
            background: rgba(255,255,255,0.05);
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
        }
        .action-list li {
            padding: 3px 0;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TRAXOVO Failure Analysis & Improvement Dashboard</h1>
        <div class="health-score" id="health-score">System Health: Loading...</div>
        <button class="report-incident-btn" onclick="reportIncident()">Report New Incident</button>
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h3>Recent Failure Incidents</h3>
            <div id="recent-failures">Loading...</div>
        </div>
        
        <div class="card">
            <h3>Failure Statistics</h3>
            <div class="stats-grid" id="failure-stats">Loading...</div>
        </div>
        
        <div class="card">
            <h3>Component Risk Analysis</h3>
            <div id="risk-analysis">Loading...</div>
        </div>
        
        <div class="card">
            <h3>Improvement Recommendations</h3>
            <div id="recommendations">Loading...</div>
        </div>
        
        <div class="card">
            <h3>Failure Prevention Checklist</h3>
            <div id="prevention-checklist">Loading...</div>
        </div>
        
        <div class="card">
            <h3>Future Build Guidelines</h3>
            <div id="build-guidelines">
                <div class="checklist">
                    <h4>Pre-Deployment Validation</h4>
                    <ul>
                        <li>Bundle size optimization verification</li>
                        <li>API health and authentication checks</li>
                        <li>Performance regression testing</li>
                        <li>Data consistency validation</li>
                        <li>Error handling coverage review</li>
                    </ul>
                </div>
                <div class="checklist">
                    <h4>Monitoring Implementation</h4>
                    <ul>
                        <li>Real-time performance metrics</li>
                        <li>API response time tracking</li>
                        <li>User experience monitoring</li>
                        <li>Resource utilization alerts</li>
                        <li>Failure pattern detection</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadFailureAnalysisData() {
            try {
                const response = await fetch('/api/failure-analysis/data');
                const data = await response.json();
                
                updateHealthScore(data.overall_health_score);
                renderRecentFailures(data.recent_failures);
                renderFailureStats(data.severity_distribution, data.failure_analysis);
                renderRiskAnalysis(data.failure_analysis.component_risk_analysis);
                renderRecommendations(data.improvement_recommendations);
                renderPreventionChecklist(data.prevention_checklist);
                
            } catch (error) {
                console.error('Failed to load failure analysis data:', error);
            }
        }
        
        function updateHealthScore(score) {
            const element = document.getElementById('health-score');
            element.textContent = `System Health: ${score}%`;
            
            if (score >= 80) {
                element.className = 'health-score good';
            } else if (score >= 60) {
                element.className = 'health-score medium';
            } else {
                element.className = 'health-score';
            }
        }
        
        function renderRecentFailures(failures) {
            const container = document.getElementById('recent-failures');
            
            if (failures.length === 0) {
                container.innerHTML = '<div style="text-align: center; opacity: 0.7;">No recent failures</div>';
                return;
            }
            
            container.innerHTML = failures.map(failure => `
                <div class="failure-item ${failure.severity}">
                    <strong>${failure.type.replace('_', ' ').toUpperCase()}</strong>
                    <span class="priority-badge priority-${failure.severity}">${failure.severity.toUpperCase()}</span>
                    <div style="margin: 8px 0; font-size: 0.9em;">${failure.component}</div>
                    <div style="opacity: 0.8; font-size: 0.85em;">${failure.description}</div>
                    <div style="font-size: 0.8em; opacity: 0.6; margin-top: 5px;">
                        ${new Date(failure.date).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        }
        
        function renderFailureStats(distribution, analysis) {
            const container = document.getElementById('failure-stats');
            
            const totalIncidents = analysis.total_incidents || 0;
            const highRiskCount = analysis.high_risk_components?.length || 0;
            
            container.innerHTML = `
                <div class="stat-item">
                    <div class="stat-value">${totalIncidents}</div>
                    <div class="stat-label">Total Incidents</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${highRiskCount}</div>
                    <div class="stat-label">High Risk Components</div>
                </div>
                ${distribution.map(item => `
                    <div class="stat-item">
                        <div class="stat-value">${item.count}</div>
                        <div class="stat-label">${item.severity.toUpperCase()} Severity</div>
                    </div>
                `).join('')}
            `;
        }
        
        function renderRiskAnalysis(components) {
            const container = document.getElementById('risk-analysis');
            
            if (!components || components.length === 0) {
                container.innerHTML = '<div style="opacity: 0.7;">No risk data available</div>';
                return;
            }
            
            container.innerHTML = components.map(comp => `
                <div class="failure-item ${comp.risk_level.toLowerCase()}">
                    <strong>${comp.component.replace('_', ' ').toUpperCase()}</strong>
                    <span class="priority-badge priority-${comp.risk_level.toLowerCase()}">${comp.risk_level} Risk</span>
                    <div style="margin: 8px 0; font-size: 0.9em;">
                        Failures: ${comp.failure_count} | Avg Severity: ${comp.average_severity} | Risk Score: ${comp.risk_score}
                    </div>
                </div>
            `).join('');
        }
        
        function renderRecommendations(recommendations) {
            const container = document.getElementById('recommendations');
            
            container.innerHTML = recommendations.slice(0, 4).map(rec => `
                <div class="recommendation">
                    <h4>${rec.title}</h4>
                    <span class="priority-badge priority-${rec.priority.toLowerCase()}">${rec.priority} Priority</span>
                    <div style="margin: 10px 0; font-size: 0.9em;">${rec.description}</div>
                    <div style="font-size: 0.85em; opacity: 0.8;">
                        Effort: ${rec.implementation_effort} | Impact: ${rec.expected_impact}
                    </div>
                    ${rec.specific_actions ? `
                        <div class="action-list">
                            <strong>Action Items:</strong>
                            <ul>
                                ${rec.specific_actions.map(action => `<li>${action}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }
        
        function renderPreventionChecklist(checklist) {
            const container = document.getElementById('prevention-checklist');
            
            container.innerHTML = checklist.pre_deployment_checklist.map(category => `
                <div class="checklist">
                    <h4>${category.category}</h4>
                    <ul>
                        ${category.checks.map(check => `<li>${check}</li>`).join('')}
                    </ul>
                </div>
            `).join('');
        }
        
        function reportIncident() {
            const incidentType = prompt('Incident Type (e.g., deployment_timeout, api_failure):');
            const severity = prompt('Severity (high, medium, low):');
            const component = prompt('Affected Component:');
            const description = prompt('Description:');
            
            if (incidentType && severity && component && description) {
                fetch('/api/failure-analysis/report-incident', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        incident_type: incidentType,
                        severity: severity,
                        component: component,
                        description: description
                    })
                }).then(response => response.json())
                  .then(result => {
                      alert('Incident reported successfully');
                      loadFailureAnalysisData(); // Refresh data
                  });
            }
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadFailureAnalysisData();
            
            // Auto-refresh every 5 minutes
            setInterval(loadFailureAnalysisData, 300000);
        });
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    # Test the failure analysis system
    engine = FailureAnalysisEngine()
    data = engine.get_failure_dashboard_data()
    print("Failure Analysis Dashboard initialized")
    print(f"Health Score: {data['overall_health_score']}%")
    print(f"Recent Failures: {len(data['recent_failures'])}")
    print(f"Recommendations: {len(data['improvement_recommendations'])}")