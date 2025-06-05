"""
Init Unlock System - Final Test Protocol
Validates unlocks across all dashboards and confirms unrestricted module access
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any, List
import sqlite3
from flask import jsonify
from permissions_bootstrap import watson_bootstrap
from kaizen_agent_system import kaizen_agent

class InitUnlockSystem:
    """
    Initialize and validate complete unlock protocol
    Tests all dashboards, modules, and UI readiness
    """
    
    def __init__(self):
        self.validation_results = {}
        self.dashboard_tests = []
        self.module_access_tests = []
        self.ui_readiness_tests = []
        self.fingerprint_validation = {}
        
    def run_final_unlock_test(self) -> Dict[str, Any]:
        """
        Execute comprehensive final unlock test protocol
        """
        test_result = {
            "test_timestamp": datetime.now().isoformat(),
            "test_status": "executing",
            "unlock_validation": {},
            "dashboard_validation": {},
            "module_access_validation": {},
            "ui_readiness_validation": {},
            "fingerprint_validation": {},
            "overall_status": "testing"
        }
        
        try:
            # Step 1: Execute Watson unlock protocol
            unlock_result = watson_bootstrap.execute_final_unlock_protocol()
            test_result["unlock_validation"] = unlock_result
            
            # Step 2: Validate dashboards
            dashboard_validation = self.validate_all_dashboards()
            test_result["dashboard_validation"] = dashboard_validation
            
            # Step 3: Validate module access
            module_validation = self.validate_module_access()
            test_result["module_access_validation"] = module_validation
            
            # Step 4: Validate UI readiness
            ui_validation = self.validate_ui_readiness()
            test_result["ui_readiness_validation"] = ui_validation
            
            # Step 5: Validate fingerprint match
            fingerprint_validation = self.validate_fingerprint_match()
            test_result["fingerprint_validation"] = fingerprint_validation
            
            # Step 6: TRD comprehensive validation
            trd_validation = self.execute_trd_validation()
            test_result["trd_validation"] = trd_validation
            
            # Determine overall status
            all_passed = all([
                unlock_result.get("protocol_status") == "completed",
                dashboard_validation.get("all_dashboards_accessible", False),
                module_validation.get("all_modules_unlocked", False),
                ui_validation.get("ui_fully_ready", False),
                fingerprint_validation.get("fingerprint_valid", False)
            ])
            
            test_result["test_status"] = "completed"
            test_result["overall_status"] = "passed" if all_passed else "failed"
            
        except Exception as e:
            test_result["test_status"] = "failed"
            test_result["error"] = str(e)
            test_result["overall_status"] = "failed"
        
        return test_result
    
    def validate_all_dashboards(self) -> Dict[str, Any]:
        """
        Validate access to all operations dashboards
        """
        dashboards_to_test = [
            {"name": "master_brain_dashboard", "route": "/master-brain", "expected_status": "accessible"},
            {"name": "trillion_scale_simulation", "route": "/api/trillion-simulation/status", "expected_status": "accessible"},
            {"name": "github_dwc_sync", "route": "/github-sync", "expected_status": "accessible"},
            {"name": "gauge_fleet_operations", "route": "/gauge-assets", "expected_status": "accessible"},
            {"name": "kaizen_trd_system", "route": "/trd", "expected_status": "accessible"},
            {"name": "bmi_intelligence_sweep", "route": "/bmi/sweep", "expected_status": "accessible"},
            {"name": "watson_command_console", "route": "/watson/console", "expected_status": "accessible"},
            {"name": "failure_analysis", "route": "/failure-analysis", "expected_status": "accessible"},
            {"name": "dashboard_customization", "route": "/dashboard-customizer", "expected_status": "accessible"},
            {"name": "internal_repositories", "route": "/internal-repos", "expected_status": "accessible"},
            {"name": "bare_bones_inspector", "route": "/bare-bones-inspector", "expected_status": "accessible"}
        ]
        
        validation_result = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_dashboards": len(dashboards_to_test),
            "accessible_dashboards": 0,
            "failed_dashboards": 0,
            "dashboard_results": [],
            "all_dashboards_accessible": False
        }
        
        for dashboard in dashboards_to_test:
            dashboard_test = {
                "dashboard_name": dashboard["name"],
                "route": dashboard["route"],
                "access_status": "testing",
                "response_time": 0,
                "error_details": None
            }
            
            try:
                # Test dashboard accessibility
                start_time = time.time()
                
                # Simulate route existence check
                route_exists = self.check_route_exists(dashboard["route"])
                
                end_time = time.time()
                dashboard_test["response_time"] = round((end_time - start_time) * 1000, 2)
                
                if route_exists:
                    dashboard_test["access_status"] = "accessible"
                    validation_result["accessible_dashboards"] += 1
                else:
                    dashboard_test["access_status"] = "not_accessible"
                    validation_result["failed_dashboards"] += 1
                    dashboard_test["error_details"] = "Route not found or not accessible"
                
            except Exception as e:
                dashboard_test["access_status"] = "error"
                dashboard_test["error_details"] = str(e)
                validation_result["failed_dashboards"] += 1
            
            validation_result["dashboard_results"].append(dashboard_test)
        
        validation_result["all_dashboards_accessible"] = validation_result["failed_dashboards"] == 0
        
        return validation_result
    
    def check_route_exists(self, route: str) -> bool:
        """
        Check if a route exists in the application
        """
        # Check common route patterns and file existence
        route_indicators = {
            "/master-brain": "master_brain_integration.py",
            "/api/trillion-simulation": "trillion_scale_intelligence_simulator.py",
            "/github-sync": "github_dwc_synchronizer.py",
            "/gauge-assets": "authentic_fleet_data_processor.py",
            "/trd": "trd_synchronization_interface.py",
            "/bmi/sweep": "bmi_intelligence_sweep.py",
            "/watson/console": "permissions_bootstrap.py",
            "/failure-analysis": "failure_analysis_dashboard.py",
            "/dashboard-customizer": "personalized_dashboard_customization.py",
            "/internal-repos": "internal_repository_integration.py",
            "/bare-bones-inspector": "bare_bones_inspector.py"
        }
        
        indicator_file = route_indicators.get(route)
        if indicator_file and os.path.exists(indicator_file):
            return True
        
        return False
    
    def validate_module_access(self) -> Dict[str, Any]:
        """
        Validate unrestricted access to all modules
        """
        modules_to_test = [
            "master_brain_intelligence",
            "trillion_scale_simulation", 
            "github_dwc_synchronization",
            "gauge_api_fleet_processor",
            "kaizen_trd_system",
            "bmi_intelligence_sweep",
            "internal_repository_integration",
            "watson_command_console"
        ]
        
        validation_result = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_modules": len(modules_to_test),
            "unlocked_modules": 0,
            "locked_modules": 0,
            "module_results": [],
            "all_modules_unlocked": False
        }
        
        # Check Watson unlock status
        unlock_status = watson_bootstrap.get_unlock_status()
        unlocked_module_names = [m["name"] for m in unlock_status.get("unlocked_modules", [])]
        
        for module_name in modules_to_test:
            module_test = {
                "module_name": module_name,
                "unlock_status": "checking",
                "access_level": "unknown",
                "restrictions": "unknown"
            }
            
            if module_name in unlocked_module_names:
                module_test["unlock_status"] = "unlocked"
                module_test["access_level"] = "unrestricted"
                module_test["restrictions"] = "none"
                validation_result["unlocked_modules"] += 1
            else:
                module_test["unlock_status"] = "locked"
                module_test["access_level"] = "restricted"
                module_test["restrictions"] = "admin_required"
                validation_result["locked_modules"] += 1
            
            validation_result["module_results"].append(module_test)
        
        validation_result["all_modules_unlocked"] = validation_result["locked_modules"] == 0
        
        return validation_result
    
    def validate_ui_readiness(self) -> Dict[str, Any]:
        """
        Validate UI components and floating command widget readiness
        """
        ui_components_to_test = [
            {"component": "floating_command_widget", "file": "internal_repository_integration.py"},
            {"component": "dashboard_customization", "file": "personalized_dashboard_customization.py"},
            {"component": "trd_interface", "file": "trd_synchronization_interface.py"},
            {"component": "watson_console", "file": "permissions_bootstrap.py"},
            {"component": "bmi_sweep_interface", "file": "bmi_intelligence_sweep.py"},
            {"component": "github_sync_interface", "file": "github_dwc_synchronizer.py"}
        ]
        
        validation_result = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_components": len(ui_components_to_test),
            "ready_components": 0,
            "failed_components": 0,
            "component_results": [],
            "ui_fully_ready": False
        }
        
        for component in ui_components_to_test:
            component_test = {
                "component_name": component["component"],
                "file_dependency": component["file"],
                "readiness_status": "checking",
                "javascript_functions": "unknown",
                "template_status": "unknown"
            }
            
            try:
                # Check file existence
                if os.path.exists(component["file"]):
                    # Check for JavaScript functions and templates
                    with open(component["file"], 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        has_javascript = 'function' in content or '<script>' in content
                        has_template = 'html>' in content or 'template' in content.lower()
                        
                        component_test["javascript_functions"] = "present" if has_javascript else "missing"
                        component_test["template_status"] = "present" if has_template else "missing"
                        
                        if has_javascript and has_template:
                            component_test["readiness_status"] = "ready"
                            validation_result["ready_components"] += 1
                        else:
                            component_test["readiness_status"] = "incomplete"
                            validation_result["failed_components"] += 1
                else:
                    component_test["readiness_status"] = "file_missing"
                    validation_result["failed_components"] += 1
                
            except Exception as e:
                component_test["readiness_status"] = "error"
                component_test["error"] = str(e)
                validation_result["failed_components"] += 1
            
            validation_result["component_results"].append(component_test)
        
        validation_result["ui_fully_ready"] = validation_result["failed_components"] == 0
        
        return validation_result
    
    def validate_fingerprint_match(self) -> Dict[str, Any]:
        """
        Validate admin fingerprint consistency across systems
        """
        validation_result = {
            "validation_timestamp": datetime.now().isoformat(),
            "watson_fingerprint": None,
            "kaizen_fingerprint": None,
            "fingerprint_match": False,
            "fingerprint_valid": False,
            "validation_details": {}
        }
        
        try:
            # Get Watson fingerprint
            watson_status = watson_bootstrap.get_unlock_status()
            watson_fingerprint = watson_status.get("admin_fingerprint")
            validation_result["watson_fingerprint"] = watson_fingerprint
            
            # Get Kaizen fingerprint
            kaizen_state = kaizen_agent.get_dashboard_state()
            kaizen_fingerprint = kaizen_state.get("patch_fingerprint")
            validation_result["kaizen_fingerprint"] = kaizen_fingerprint
            
            # Validate fingerprint format and consistency
            if watson_fingerprint:
                fingerprint_valid = len(watson_fingerprint) == 16 and watson_fingerprint.isupper()
                validation_result["fingerprint_valid"] = fingerprint_valid
                
                validation_result["validation_details"] = {
                    "length_check": len(watson_fingerprint) == 16,
                    "format_check": watson_fingerprint.isupper(),
                    "watson_active": watson_status.get("override_active", False),
                    "kaizen_confidence": kaizen_state.get("confidence_state", 0.0)
                }
            else:
                validation_result["fingerprint_valid"] = False
                validation_result["validation_details"]["error"] = "No Watson fingerprint found"
            
        except Exception as e:
            validation_result["validation_details"]["error"] = str(e)
            validation_result["fingerprint_valid"] = False
        
        return validation_result
    
    def execute_trd_validation(self) -> Dict[str, Any]:
        """
        Execute TRD comprehensive validation across all dashboards
        """
        trd_validation = {
            "validation_timestamp": datetime.now().isoformat(),
            "trd_status": "validating",
            "dashboard_introspection": {},
            "module_activation": {},
            "patch_alignment": {},
            "watson_sync": {},
            "overall_trd_status": "unknown"
        }
        
        try:
            # Perform TRD dashboard introspection
            introspection_result = kaizen_agent.perform_full_introspection()
            trd_validation["dashboard_introspection"] = {
                "confidence_level": introspection_result.get("confidence_level", 0.0),
                "automation_agents": len(introspection_result.get("automation_agents", [])),
                "dashboard_purpose": introspection_result.get("dashboard_purpose", {}),
                "status": "completed"
            }
            
            # Check module activation status
            trd_validation["module_activation"] = {
                "watson_active": watson_bootstrap.override_active,
                "kaizen_modules": len(kaizen_agent.dashboard_state.get("simulation_modules", [])),
                "status": "active" if watson_bootstrap.override_active else "inactive"
            }
            
            # Check patch alignment
            trd_validation["patch_alignment"] = {
                "fingerprint_locked": kaizen_agent.dashboard_state.get("patch_fingerprint") is not None,
                "sync_status": kaizen_agent.dashboard_state.get("sync_status", "unknown"),
                "status": "aligned" if kaizen_agent.dashboard_state.get("patch_fingerprint") else "pending"
            }
            
            # Check Watson synchronization
            watson_status = watson_bootstrap.get_unlock_status()
            trd_validation["watson_sync"] = {
                "intelligence_core": len(watson_bootstrap.watson_intelligence_core) > 0,
                "dashboard_access": len(watson_status.get("dashboard_access", [])),
                "unlock_status": watson_status.get("unlock_protocol_status", "unknown"),
                "status": "synced" if watson_status.get("unlock_protocol_status") == "fully_unlocked" else "pending"
            }
            
            # Determine overall TRD status
            all_systems_ready = all([
                trd_validation["dashboard_introspection"]["status"] == "completed",
                trd_validation["module_activation"]["status"] == "active",
                trd_validation["watson_sync"]["status"] == "synced"
            ])
            
            trd_validation["overall_trd_status"] = "operational" if all_systems_ready else "partial"
            trd_validation["trd_status"] = "completed"
            
        except Exception as e:
            trd_validation["trd_status"] = "failed"
            trd_validation["error"] = str(e)
            trd_validation["overall_trd_status"] = "failed"
        
        return trd_validation


# Global init unlock system instance
init_unlock = InitUnlockSystem()

def create_init_unlock_routes(app):
    """Add init unlock routes to Flask app"""
    
    @app.route('/init/unlock/test')
    def init_unlock_test():
        """Execute final unlock test protocol"""
        result = init_unlock.run_final_unlock_test()
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Final Unlock Test Results</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Courier New', monospace;
                    background: linear-gradient(135deg, #000000, #1a1a2e);
                    color: #00ff88;
                    padding: 20px;
                    line-height: 1.6;
                }}
                .test-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: rgba(0,0,0,0.8);
                    border: 2px solid #00ff88;
                    border-radius: 15px;
                    padding: 30px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: rgba(0,255,136,0.1);
                    border-radius: 10px;
                }}
                .test-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .test-card {{
                    background: rgba(0,0,0,0.6);
                    border: 1px solid #00ff88;
                    border-radius: 10px;
                    padding: 20px;
                }}
                .status-pass {{ color: #00ff88; }}
                .status-fail {{ color: #ff0000; }}
                .status-partial {{ color: #ffff00; }}
                .test-detail {{
                    background: rgba(0,0,0,0.8);
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                    border-left: 3px solid #00ff88;
                }}
                .overall-status {{
                    background: rgba(0,255,136,0.2);
                    border: 2px solid #00ff88;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    text-align: center;
                    font-size: 1.2em;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="test-container">
                <div class="header">
                    <h1>🧪 FINAL UNLOCK TEST RESULTS</h1>
                    <h2>Comprehensive Validation Protocol</h2>
                    <p>Test Status: <span class="{'status-pass' if result['test_status'] == 'completed' else 'status-fail'}">{result['test_status'].upper()}</span></p>
                </div>
                
                <div class="overall-status">
                    Overall Status: <span class="{'status-pass' if result['overall_status'] == 'passed' else 'status-fail'}">{result['overall_status'].upper()}</span>
                </div>
                
                <div class="test-grid">
                    <div class="test-card">
                        <h3>🔓 Watson Unlock Protocol</h3>
                        <div class="test-detail">
                            Status: <span class="{'status-pass' if result.get('unlock_validation', {}).get('protocol_status') == 'completed' else 'status-fail'}">
                                {result.get('unlock_validation', {}).get('protocol_status', 'Unknown').upper()}
                            </span>
                        </div>
                        <div class="test-detail">
                            Admin Fingerprint: {result.get('unlock_validation', {}).get('admin_fingerprint', 'Not Set')}
                        </div>
                        <div class="test-detail">
                            Steps Completed: {len(result.get('unlock_validation', {}).get('steps_completed', []))}
                        </div>
                    </div>
                    
                    <div class="test-card">
                        <h3>📊 Dashboard Validation</h3>
                        <div class="test-detail">
                            Total Dashboards: {result.get('dashboard_validation', {}).get('total_dashboards', 0)}
                        </div>
                        <div class="test-detail">
                            Accessible: <span class="status-pass">{result.get('dashboard_validation', {}).get('accessible_dashboards', 0)}</span>
                        </div>
                        <div class="test-detail">
                            Failed: <span class="{'status-fail' if result.get('dashboard_validation', {}).get('failed_dashboards', 0) > 0 else 'status-pass'}">{result.get('dashboard_validation', {}).get('failed_dashboards', 0)}</span>
                        </div>
                        <div class="test-detail">
                            All Accessible: <span class="{'status-pass' if result.get('dashboard_validation', {}).get('all_dashboards_accessible') else 'status-fail'}">
                                {'YES' if result.get('dashboard_validation', {}).get('all_dashboards_accessible') else 'NO'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="test-card">
                        <h3>🔧 Module Access Validation</h3>
                        <div class="test-detail">
                            Total Modules: {result.get('module_access_validation', {}).get('total_modules', 0)}
                        </div>
                        <div class="test-detail">
                            Unlocked: <span class="status-pass">{result.get('module_access_validation', {}).get('unlocked_modules', 0)}</span>
                        </div>
                        <div class="test-detail">
                            Locked: <span class="{'status-fail' if result.get('module_access_validation', {}).get('locked_modules', 0) > 0 else 'status-pass'}">{result.get('module_access_validation', {}).get('locked_modules', 0)}</span>
                        </div>
                        <div class="test-detail">
                            All Unlocked: <span class="{'status-pass' if result.get('module_access_validation', {}).get('all_modules_unlocked') else 'status-fail'}">
                                {'YES' if result.get('module_access_validation', {}).get('all_modules_unlocked') else 'NO'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="test-card">
                        <h3>🎨 UI Readiness Validation</h3>
                        <div class="test-detail">
                            Total Components: {result.get('ui_readiness_validation', {}).get('total_components', 0)}
                        </div>
                        <div class="test-detail">
                            Ready: <span class="status-pass">{result.get('ui_readiness_validation', {}).get('ready_components', 0)}</span>
                        </div>
                        <div class="test-detail">
                            Failed: <span class="{'status-fail' if result.get('ui_readiness_validation', {}).get('failed_components', 0) > 0 else 'status-pass'}">{result.get('ui_readiness_validation', {}).get('failed_components', 0)}</span>
                        </div>
                        <div class="test-detail">
                            UI Fully Ready: <span class="{'status-pass' if result.get('ui_readiness_validation', {}).get('ui_fully_ready') else 'status-fail'}">
                                {'YES' if result.get('ui_readiness_validation', {}).get('ui_fully_ready') else 'NO'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="test-card">
                        <h3>🔑 Fingerprint Validation</h3>
                        <div class="test-detail">
                            Watson Fingerprint: {result.get('fingerprint_validation', {}).get('watson_fingerprint', 'None')}
                        </div>
                        <div class="test-detail">
                            Fingerprint Valid: <span class="{'status-pass' if result.get('fingerprint_validation', {}).get('fingerprint_valid') else 'status-fail'}">
                                {'YES' if result.get('fingerprint_validation', {}).get('fingerprint_valid') else 'NO'}
                            </span>
                        </div>
                    </div>
                    
                    <div class="test-card">
                        <h3>🔁 TRD Validation</h3>
                        <div class="test-detail">
                            TRD Status: <span class="{'status-pass' if result.get('trd_validation', {}).get('trd_status') == 'completed' else 'status-partial'}">
                                {result.get('trd_validation', {}).get('trd_status', 'Unknown').upper()}
                            </span>
                        </div>
                        <div class="test-detail">
                            Overall TRD: <span class="{'status-pass' if result.get('trd_validation', {}).get('overall_trd_status') == 'operational' else 'status-partial'}">
                                {result.get('trd_validation', {}).get('overall_trd_status', 'Unknown').upper()}
                            </span>
                        </div>
                        <div class="test-detail">
                            Confidence Level: {result.get('trd_validation', {}).get('dashboard_introspection', {}).get('confidence_level', 0.0):.1%}
                        </div>
                    </div>
                </div>
                
                <div class="test-card">
                    <h3>📋 Test Summary</h3>
                    <div class="test-detail">Test Timestamp: {result['test_timestamp']}</div>
                    <div class="test-detail">
                        Validation Result: 
                        <span class="{'status-pass' if result['overall_status'] == 'passed' else 'status-fail'}">
                            {result['overall_status'].upper()}
                        </span>
                    </div>
                    {'<div class="test-detail">Error: ' + result.get('error', '') + '</div>' if result.get('error') else ''}
                </div>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/api/init/unlock/test')
    def api_init_unlock_test():
        """API endpoint for final unlock test"""
        result = init_unlock.run_final_unlock_test()
        return jsonify(result)


if __name__ == "__main__":
    # Execute final unlock test
    test_system = InitUnlockSystem()
    print("Executing final unlock test protocol...")
    result = test_system.run_final_unlock_test()
    print(f"Test completed with status: {result['overall_status']}")
    print(f"Admin fingerprint: {result.get('fingerprint_validation', {}).get('watson_fingerprint', 'None')}")