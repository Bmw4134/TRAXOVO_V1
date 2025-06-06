"""
TRAXOVO Regression Analysis System
Identify and prevent feature regression issues
"""

import os
import json
from datetime import datetime
from app import db
from models_clean import PlatformData

class RegressionAnalyzer:
    """Analyze and prevent regression issues in TRAXOVO platform"""
    
    def __init__(self):
        self.analysis_results = {}
        self.critical_features = [
            'authentication_system',
            'executive_dashboard',
            'data_connectors',
            'api_endpoints',
            'database_models',
            'deployment_config'
        ]
    
    def analyze_current_state(self):
        """Analyze current platform state"""
        self.analysis_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'platform_health': self._check_platform_health(),
            'feature_status': self._check_feature_status(),
            'deployment_readiness': self._check_deployment_readiness(),
            'data_integrity': self._check_data_integrity(),
            'regression_risks': self._identify_regression_risks()
        }
        
        # Store analysis in database
        self._store_analysis()
        return self.analysis_results
    
    def _check_platform_health(self):
        """Check overall platform health"""
        health_metrics = {
            'database_connected': self._test_database_connection(),
            'authentication_working': self._test_authentication(),
            'api_endpoints_functional': self._test_api_endpoints(),
            'templates_rendering': self._test_template_rendering()
        }
        
        health_score = sum(health_metrics.values()) / len(health_metrics) * 100
        return {
            'score': health_score,
            'metrics': health_metrics,
            'status': 'healthy' if health_score > 80 else 'degraded'
        }
    
    def _check_feature_status(self):
        """Check status of critical features"""
        feature_status = {}
        
        for feature in self.critical_features:
            feature_status[feature] = self._evaluate_feature(feature)
        
        return feature_status
    
    def _check_deployment_readiness(self):
        """Check deployment readiness"""
        readiness_checks = {
            'file_size_optimized': self._check_file_sizes(),
            'dependencies_clean': self._check_dependencies(),
            'config_valid': self._check_configuration(),
            'database_ready': self._check_database_schema()
        }
        
        readiness_score = sum(readiness_checks.values()) / len(readiness_checks) * 100
        return {
            'score': readiness_score,
            'checks': readiness_checks,
            'ready': readiness_score > 90
        }
    
    def _check_data_integrity(self):
        """Check data integrity and authentic sources"""
        integrity_status = {
            'database_data_valid': self._validate_database_data(),
            'api_connections_configured': self._check_api_configurations(),
            'no_hardcoded_data': self._check_for_hardcoded_data()
        }
        
        return integrity_status
    
    def _identify_regression_risks(self):
        """Identify potential regression risks"""
        risks = []
        
        # Check for common regression patterns
        if not self._test_database_connection():
            risks.append({
                'risk': 'Database connection failure',
                'severity': 'high',
                'impact': 'Complete platform failure'
            })
        
        if self._check_for_hardcoded_data():
            risks.append({
                'risk': 'Hardcoded data present',
                'severity': 'medium',
                'impact': 'Data integrity issues'
            })
        
        if not self._check_file_sizes():
            risks.append({
                'risk': 'Large file sizes',
                'severity': 'high',
                'impact': 'Deployment failures'
            })
        
        return risks
    
    def _test_database_connection(self):
        """Test database connection"""
        try:
            db.session.execute('SELECT 1')
            return True
        except Exception:
            return False
    
    def _test_authentication(self):
        """Test authentication system"""
        try:
            # Check if login route exists and returns 200
            from app import app
            with app.test_client() as client:
                response = client.get('/login')
                return response.status_code == 200
        except Exception:
            return False
    
    def _test_api_endpoints(self):
        """Test API endpoints"""
        try:
            from app import app
            with app.test_client() as client:
                # Test health endpoint
                response = client.get('/health')
                return response.status_code == 200
        except Exception:
            return False
    
    def _test_template_rendering(self):
        """Test template rendering"""
        try:
            from app import app
            with app.test_client() as client:
                response = client.get('/')
                return response.status_code == 200 and b'TRAXOVO' in response.data
        except Exception:
            return False
    
    def _evaluate_feature(self, feature):
        """Evaluate specific feature status"""
        feature_checks = {
            'authentication_system': self._test_authentication,
            'executive_dashboard': lambda: self._check_route_exists('/dashboard'),
            'data_connectors': lambda: os.path.exists('data_connectors.py'),
            'api_endpoints': self._test_api_endpoints,
            'database_models': lambda: os.path.exists('models_clean.py'),
            'deployment_config': lambda: os.path.exists('Dockerfile')
        }
        
        if feature in feature_checks:
            try:
                return feature_checks[feature]()
            except Exception:
                return False
        return False
    
    def _check_route_exists(self, route):
        """Check if route exists"""
        try:
            from app import app
            with app.test_client() as client:
                response = client.get(route, follow_redirects=True)
                return response.status_code in [200, 302]
        except Exception:
            return False
    
    def _check_file_sizes(self):
        """Check for large files that could cause deployment issues"""
        large_files = []
        max_size = 50 * 1024 * 1024  # 50MB limit
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if size > max_size:
                        large_files.append(filepath)
                except OSError:
                    continue
        
        return len(large_files) == 0
    
    def _check_dependencies(self):
        """Check dependencies are clean"""
        try:
            with open('requirements-production.txt', 'r') as f:
                deps = f.read().strip().split('\n')
                # Check for reasonable number of dependencies
                return len(deps) < 20 and all(dep.strip() for dep in deps)
        except FileNotFoundError:
            return False
    
    def _check_configuration(self):
        """Check configuration files"""
        required_files = ['app.py', 'models_clean.py', 'main.py']
        return all(os.path.exists(f) for f in required_files)
    
    def _check_database_schema(self):
        """Check database schema is ready"""
        try:
            from models_clean import PlatformData
            return PlatformData.query.count() >= 0
        except Exception:
            return False
    
    def _validate_database_data(self):
        """Validate database contains proper data"""
        try:
            from models_clean import PlatformData
            essential_data_types = ['executive_metrics', 'platform_status', 'market_data']
            
            for data_type in essential_data_types:
                record = PlatformData.query.filter_by(data_type=data_type).first()
                if not record:
                    return False
            return True
        except Exception:
            return False
    
    def _check_api_configurations(self):
        """Check API configurations"""
        api_keys = [
            'ROBINHOOD_ACCESS_TOKEN',
            'COINBASE_API_KEY', 
            'GAUGE_API_KEY',
            'OPENAI_API_KEY'
        ]
        
        configured_count = sum(1 for key in api_keys if os.environ.get(key))
        return configured_count > 0  # At least one API configured
    
    def _check_for_hardcoded_data(self):
        """Check for hardcoded data in source files"""
        # This should return False (no hardcoded data) for good integrity
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                # Look for patterns that suggest hardcoded data
                hardcoded_patterns = [
                    '"deployment_readiness": 96',
                    '"projected_roi": 300',
                    'platform_status = {'
                ]
                
                for pattern in hardcoded_patterns:
                    if pattern in content:
                        return True
                return False
        except Exception:
            return True
    
    def _store_analysis(self):
        """Store analysis results in database"""
        try:
            analysis_record = PlatformData.query.filter_by(data_type='regression_analysis').first()
            if analysis_record:
                analysis_record.data_content = self.analysis_results
                analysis_record.updated_at = datetime.utcnow()
            else:
                analysis_record = PlatformData(
                    data_type='regression_analysis',
                    data_content=self.analysis_results
                )
                db.session.add(analysis_record)
            
            db.session.commit()
        except Exception as e:
            print(f"Failed to store analysis: {e}")
    
    def generate_regression_report(self):
        """Generate comprehensive regression report"""
        analysis = self.analyze_current_state()
        
        report = {
            'executive_summary': self._generate_executive_summary(analysis),
            'detailed_findings': analysis,
            'recommendations': self._generate_recommendations(analysis),
            'action_items': self._generate_action_items(analysis)
        }
        
        return report
    
    def _generate_executive_summary(self, analysis):
        """Generate executive summary"""
        health_score = analysis['platform_health']['score']
        deployment_score = analysis['deployment_readiness']['score']
        
        if health_score > 80 and deployment_score > 90:
            status = "Platform is healthy and deployment-ready"
        elif health_score > 60:
            status = "Platform has minor issues requiring attention"
        else:
            status = "Platform has critical issues requiring immediate action"
        
        return {
            'status': status,
            'health_score': health_score,
            'deployment_score': deployment_score,
            'critical_issues': len([r for r in analysis['regression_risks'] if r['severity'] == 'high'])
        }
    
    def _generate_recommendations(self, analysis):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not analysis['data_integrity']['api_connections_configured']:
            recommendations.append("Configure authentic API connections for real data")
        
        if analysis['data_integrity']['no_hardcoded_data']:
            recommendations.append("Remove hardcoded data and use database storage")
        
        if not analysis['deployment_readiness']['ready']:
            recommendations.append("Optimize file sizes and clean dependencies for deployment")
        
        return recommendations
    
    def _generate_action_items(self, analysis):
        """Generate specific action items"""
        actions = []
        
        for risk in analysis['regression_risks']:
            if risk['severity'] == 'high':
                actions.append(f"URGENT: Address {risk['risk']}")
            else:
                actions.append(f"Address {risk['risk']}")
        
        return actions

def run_regression_analysis():
    """Run complete regression analysis"""
    analyzer = RegressionAnalyzer()
    return analyzer.generate_regression_report()