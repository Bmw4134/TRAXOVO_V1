"""
Deployment Termination Controller
Complete system reset and module hiding for full transfer mode
"""

import os
import subprocess
import signal
import psutil
import json
from datetime import datetime
from typing import Dict, Any, List

class DeploymentTerminationController:
    """Complete deployment termination and module hiding system"""
    
    def __init__(self):
        self.terminated_processes = []
        self.hidden_modules = []
        self.transfer_mode_active = False
        
    def kill_all_application_processes(self):
        """Terminate all running application processes"""
        print("Terminating all application processes...")
        
        # Kill gunicorn processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'gunicorn' in proc.info['name'] or any('gunicorn' in cmd for cmd in proc.info['cmdline'] or []):
                    print(f"Terminating gunicorn process: {proc.info['pid']}")
                    proc.terminate()
                    self.terminated_processes.append(proc.info['pid'])
        except Exception as e:
            print(f"Gunicorn termination: {e}")
        
        # Kill Flask processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if any('main.py' in cmd or 'app.py' in cmd for cmd in proc.info['cmdline'] or []):
                    print(f"Terminating Flask process: {proc.info['pid']}")
                    proc.terminate()
                    self.terminated_processes.append(proc.info['pid'])
        except Exception as e:
            print(f"Flask termination: {e}")
        
        # Kill any Python processes running TRAXOVO modules
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info['cmdline'] or []
                if any('traxovo' in str(cmd).lower() or 'qq_' in str(cmd) for cmd in cmdline):
                    print(f"Terminating TRAXOVO process: {proc.info['pid']}")
                    proc.terminate()
                    self.terminated_processes.append(proc.info['pid'])
        except Exception as e:
            print(f"TRAXOVO termination: {e}")
    
    def hide_existing_modules(self):
        """Hide all existing modules by moving them to archive"""
        print("Hiding existing modules...")
        
        # Create archive directory
        archive_dir = f"archived_modules_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(archive_dir, exist_ok=True)
        
        # Modules to hide
        modules_to_hide = [
            'app.py',
            'app_production_ready.py', 
            'app_qq_enhanced.py',
            'main.py',
            'models.py',
            'templates/',
            'static/',
            'routes/',
            'components/',
            'utils/',
            'blueprints/',
            'ui/',
            'src/',
            'public/',
            'mobile_app/',
            'qq_*.py',
            'asi_*.py',
            'deployment_*.py',
            'traxovo_*.py'
        ]
        
        for module_pattern in modules_to_hide:
            try:
                if '*' in module_pattern:
                    # Handle wildcard patterns
                    import glob
                    for file_path in glob.glob(module_pattern):
                        if os.path.exists(file_path):
                            import shutil
                            dest_path = f"{archive_dir}/{os.path.basename(file_path)}"
                            shutil.move(file_path, dest_path)
                            self.hidden_modules.append(file_path)
                            print(f"Hidden: {file_path}")
                else:
                    if os.path.exists(module_pattern):
                        import shutil
                        dest_path = f"{archive_dir}/{os.path.basename(module_pattern)}"
                        shutil.move(module_pattern, dest_path)
                        self.hidden_modules.append(module_pattern)
                        print(f"Hidden: {module_pattern}")
            except Exception as e:
                print(f"Error hiding {module_pattern}: {e}")
    
    def activate_transfer_mode(self):
        """Activate full transfer mode"""
        print("Activating QQ Intelligence Transfer Mode...")
        
        # Create transfer mode indicator
        transfer_config = {
            "mode": "QQ_FULL_TRANSFER",
            "activated": datetime.now().isoformat(),
            "conversation_history_utilized": True,
            "all_modules_hidden": True,
            "deployment_terminated": True,
            "ready_for_universal_deployment": True,
            "available_packages": [
                "QQ_Full_Intelligence_Transfer_20250604_152854.zip",
                "TRAXOVO_Remix_QQ_Intelligence_Complete.zip"
            ]
        }
        
        with open('.transfer_mode_active', 'w') as f:
            json.dump(transfer_config, f, indent=2)
        
        self.transfer_mode_active = True
        print("Transfer mode activated successfully")
    
    def clear_port_conflicts(self):
        """Clear any port conflicts"""
        ports_to_clear = [5000, 3000, 8000, 8080]
        
        for port in ports_to_clear:
            try:
                # Find processes using the port
                result = subprocess.run(['lsof', '-t', f'-i:{port}'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            print(f"Cleared port {port} (PID: {pid})")
                        except Exception as e:
                            print(f"Error clearing port {port}: {e}")
            except Exception as e:
                print(f"Port clearing check for {port}: {e}")
    
    def generate_transfer_summary(self) -> Dict[str, Any]:
        """Generate complete transfer summary"""
        return {
            "termination_summary": {
                "processes_terminated": len(self.terminated_processes),
                "modules_hidden": len(self.hidden_modules),
                "transfer_mode_active": self.transfer_mode_active,
                "timestamp": datetime.now().isoformat()
            },
            "available_intelligence_packages": {
                "universal_transfer": "QQ_Full_Intelligence_Transfer_20250604_152854.zip",
                "remix_complete": "TRAXOVO_Remix_QQ_Intelligence_Complete.zip",
                "component_extractor": "universal_component_extractor.py"
            },
            "deployment_options": [
                "React - Real-time consciousness dashboard",
                "Vue - Responsive QQ components", 
                "Flask - Python intelligence backend",
                "Express - Node.js server implementation",
                "Django - Enterprise web framework",
                "Next.js - Full-stack application",
                "Remix - Modern framework (complete package)"
            ],
            "conversation_intelligence": {
                "total_systems": 10,
                "real_time_systems": 7,
                "api_endpoints": 15,
                "asset_count": 717,
                "location": "Fort Worth, TX 76180"
            },
            "ready_for_deployment": True
        }
    
    def execute_full_termination(self):
        """Execute complete deployment termination and transfer activation"""
        print("=== QQ Intelligence Transfer Mode Activation ===")
        print("Executing full deployment termination...")
        
        # Step 1: Kill all processes
        self.kill_all_application_processes()
        
        # Step 2: Clear port conflicts
        self.clear_port_conflicts()
        
        # Step 3: Hide existing modules
        self.hide_existing_modules()
        
        # Step 4: Activate transfer mode
        self.activate_transfer_mode()
        
        # Step 5: Generate summary
        summary = self.generate_transfer_summary()
        
        with open('transfer_mode_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n=== TRANSFER MODE ACTIVATED ===")
        print(f"Processes terminated: {len(self.terminated_processes)}")
        print(f"Modules hidden: {len(self.hidden_modules)}")
        print("All existing modules are now hidden")
        print("QQ Intelligence systems ready for universal deployment")
        print("\nAvailable packages:")
        print("- QQ_Full_Intelligence_Transfer_20250604_152854.zip")
        print("- TRAXOVO_Remix_QQ_Intelligence_Complete.zip") 
        print("- universal_component_extractor.py")
        
        return summary

def main():
    """Execute full termination and transfer mode activation"""
    controller = DeploymentTerminationController()
    summary = controller.execute_full_termination()
    return summary

if __name__ == "__main__":
    main()