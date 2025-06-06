"""
TRAXOVO AI Regression Fixer
Integrates with custom ChatGPT model to automatically fix regression issues
"""

import os
import json
import requests
from datetime import datetime
from app import db
from models_clean import PlatformData
from regression_analysis import RegressionAnalyzer

class AIRegressionFixer:
    """AI-powered system to detect and fix regressions automatically"""
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.custom_model_endpoint = os.environ.get('CUSTOM_CHATGPT_ENDPOINT')
        self.analyzer = RegressionAnalyzer()
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured - needed for AI regression fixing")
    
    def analyze_and_fix_regressions(self):
        """Main method to analyze current state and fix any regressions"""
        
        # Step 1: Run comprehensive regression analysis
        analysis_report = self.analyzer.generate_regression_report()
        
        # Step 2: If issues found, consult AI for fixes
        if self._has_critical_issues(analysis_report):
            ai_recommendations = self._get_ai_fix_recommendations(analysis_report)
            
            # Step 3: Apply AI-recommended fixes
            fix_results = self._apply_ai_fixes(ai_recommendations)
            
            # Step 4: Re-analyze to verify fixes
            post_fix_analysis = self.analyzer.generate_regression_report()
            
            return {
                'initial_analysis': analysis_report,
                'ai_recommendations': ai_recommendations,
                'fix_results': fix_results,
                'post_fix_analysis': post_fix_analysis,
                'regression_fixed': self._regression_successfully_fixed(analysis_report, post_fix_analysis)
            }
        else:
            return {
                'status': 'no_regressions_detected',
                'analysis': analysis_report
            }
    
    def _has_critical_issues(self, analysis_report):
        """Check if analysis report contains critical issues"""
        critical_issues = analysis_report['executive_summary']['critical_issues']
        health_score = analysis_report['executive_summary']['health_score']
        deployment_score = analysis_report['executive_summary']['deployment_score']
        
        return critical_issues > 0 or health_score < 70 or deployment_score < 80
    
    def _get_ai_fix_recommendations(self, analysis_report):
        """Get AI recommendations for fixing regressions"""
        
        prompt = f"""
You are an expert TRAXOVO platform engineer. Analyze this regression report and provide specific code fixes.

REGRESSION ANALYSIS:
{json.dumps(analysis_report, indent=2)}

CURRENT CODEBASE CONTEXT:
- Flask application with PostgreSQL database
- Authentication system with multiple user accounts
- Executive dashboard with real-time data
- API endpoints for platform status, market data, executive metrics
- Data connectors for Robinhood, Coinbase, GAUGE API, OpenAI

REQUIREMENTS:
1. Maintain all existing functionality
2. Fix any regression issues identified
3. Ensure deployment readiness
4. Use authentic data sources, not hardcoded values
5. Preserve authentication and security

Provide specific fixes in JSON format:
{{
    "fixes": [
        {{
            "issue": "description of issue",
            "file": "filename to modify",
            "action": "create|modify|delete",
            "code": "exact code to implement",
            "explanation": "why this fixes the issue"
        }}
    ],
    "deployment_optimizations": [
        {{
            "optimization": "description",
            "implementation": "how to implement"
        }}
    ],
    "regression_prevention": [
        {{
            "prevention": "description",
            "implementation": "how to implement"
        }}
    ]
}}
"""
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert TRAXOVO platform engineer specializing in regression analysis and automated fixes. Always provide specific, actionable code solutions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = json.loads(result['choices'][0]['message']['content'])
                return ai_response
            else:
                return {"error": f"OpenAI API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"AI consultation failed: {str(e)}"}
    
    def _apply_ai_fixes(self, ai_recommendations):
        """Apply the AI-recommended fixes"""
        
        if "error" in ai_recommendations:
            return {"status": "failed", "error": ai_recommendations["error"]}
        
        fix_results = []
        
        try:
            # Apply each fix recommended by AI
            for fix in ai_recommendations.get('fixes', []):
                result = self._apply_single_fix(fix)
                fix_results.append(result)
            
            # Apply deployment optimizations
            for optimization in ai_recommendations.get('deployment_optimizations', []):
                result = self._apply_optimization(optimization)
                fix_results.append(result)
            
            # Store regression prevention measures
            self._store_prevention_measures(ai_recommendations.get('regression_prevention', []))
            
            return {"status": "success", "fixes_applied": fix_results}
            
        except Exception as e:
            return {"status": "failed", "error": f"Fix application failed: {str(e)}"}
    
    def _apply_single_fix(self, fix):
        """Apply a single fix recommended by AI"""
        
        try:
            file_path = fix['file']
            action = fix['action']
            code = fix['code']
            
            if action == 'create':
                with open(file_path, 'w') as f:
                    f.write(code)
                return {"fix": fix['issue'], "status": "created", "file": file_path}
            
            elif action == 'modify':
                # For modifications, we'll append or replace specific sections
                # This is a simplified implementation - in production you'd want more sophisticated patching
                with open(file_path, 'a') as f:
                    f.write(f"\n\n# AI Fix for: {fix['issue']}\n")
                    f.write(code)
                return {"fix": fix['issue'], "status": "modified", "file": file_path}
            
            elif action == 'delete':
                if os.path.exists(file_path):
                    os.remove(file_path)
                return {"fix": fix['issue'], "status": "deleted", "file": file_path}
            
        except Exception as e:
            return {"fix": fix['issue'], "status": "failed", "error": str(e)}
    
    def _apply_optimization(self, optimization):
        """Apply deployment optimization"""
        
        # Store optimization recommendations in database for review
        try:
            opt_record = PlatformData.query.filter_by(data_type='optimizations').first()
            if opt_record:
                existing_opts = opt_record.data_content.get('optimizations', [])
                existing_opts.append(optimization)
                opt_record.data_content = {'optimizations': existing_opts}
                opt_record.updated_at = datetime.utcnow()
            else:
                opt_record = PlatformData(
                    data_type='optimizations',
                    data_content={'optimizations': [optimization]}
                )
                db.session.add(opt_record)
            
            db.session.commit()
            return {"optimization": optimization['optimization'], "status": "stored"}
            
        except Exception as e:
            return {"optimization": optimization['optimization'], "status": "failed", "error": str(e)}
    
    def _store_prevention_measures(self, prevention_measures):
        """Store regression prevention measures"""
        
        try:
            prevention_record = PlatformData.query.filter_by(data_type='regression_prevention').first()
            if prevention_record:
                prevention_record.data_content = {'measures': prevention_measures}
                prevention_record.updated_at = datetime.utcnow()
            else:
                prevention_record = PlatformData(
                    data_type='regression_prevention',
                    data_content={'measures': prevention_measures}
                )
                db.session.add(prevention_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to store prevention measures: {e}")
    
    def _regression_successfully_fixed(self, before_analysis, after_analysis):
        """Compare before and after analysis to determine if regression was fixed"""
        
        before_health = before_analysis['executive_summary']['health_score']
        after_health = after_analysis['executive_summary']['health_score']
        
        before_deployment = before_analysis['executive_summary']['deployment_score']
        after_deployment = after_analysis['executive_summary']['deployment_score']
        
        before_critical = before_analysis['executive_summary']['critical_issues']
        after_critical = after_analysis['executive_summary']['critical_issues']
        
        # Consider regression fixed if:
        # 1. Health score improved by at least 10 points
        # 2. Deployment score improved by at least 10 points  
        # 3. Critical issues reduced
        
        health_improved = after_health > before_health + 10
        deployment_improved = after_deployment > before_deployment + 10
        critical_reduced = after_critical < before_critical
        
        return health_improved and deployment_improved and critical_reduced
    
    def continuous_monitoring(self):
        """Set up continuous monitoring to catch regressions early"""
        
        monitoring_config = {
            'health_check_interval': 300,  # 5 minutes
            'auto_fix_enabled': True,
            'alert_thresholds': {
                'health_score_min': 70,
                'deployment_score_min': 80,
                'max_critical_issues': 2
            }
        }
        
        # Store monitoring configuration
        try:
            monitor_record = PlatformData.query.filter_by(data_type='monitoring_config').first()
            if monitor_record:
                monitor_record.data_content = monitoring_config
                monitor_record.updated_at = datetime.utcnow()
            else:
                monitor_record = PlatformData(
                    data_type='monitoring_config',
                    data_content=monitoring_config
                )
                db.session.add(monitor_record)
            
            db.session.commit()
            return {"status": "monitoring_configured", "config": monitoring_config}
            
        except Exception as e:
            return {"status": "monitoring_failed", "error": str(e)}

def run_ai_regression_fix():
    """Main function to run AI-powered regression fixing"""
    
    try:
        fixer = AIRegressionFixer()
        results = fixer.analyze_and_fix_regressions()
        
        # Also set up continuous monitoring
        monitoring_result = fixer.continuous_monitoring()
        results['monitoring'] = monitoring_result
        
        return results
        
    except Exception as e:
        return {"status": "failed", "error": f"AI regression fixer failed: {str(e)}"}

def get_regression_status():
    """Get current regression status and AI recommendations"""
    
    try:
        # Get latest regression analysis
        analysis_record = PlatformData.query.filter_by(data_type='regression_analysis').first()
        
        # Get AI fix history
        fix_history = PlatformData.query.filter_by(data_type='ai_fix_history').first()
        
        # Get prevention measures
        prevention_record = PlatformData.query.filter_by(data_type='regression_prevention').first()
        
        return {
            'latest_analysis': analysis_record.data_content if analysis_record else None,
            'fix_history': fix_history.data_content if fix_history else None,
            'prevention_measures': prevention_record.data_content if prevention_record else None,
            'monitoring_active': True
        }
        
    except Exception as e:
        return {"error": f"Failed to get regression status: {str(e)}"}