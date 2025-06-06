"""
Watson Deployment Master - Ultimate Deployment Resolution System
Handles all deployment conflicts with advanced intelligence
"""

import os
import sys
import time
import psutil
import signal
import subprocess
from datetime import datetime

class WatsonDeploymentMaster:
    def __init__(self):
        self.target_port = 5000
        self.max_retries = 5
        self.deployment_log = []
        
    def execute_deployment(self):
        """Execute foolproof deployment with Watson intelligence"""
        
        print("Watson Deployment Master: Initiating ultimate deployment sequence...")
        
        # Step 1: Complete port clearance
        self._clear_port_completely()
        
        # Step 2: Verify system readiness
        self._verify_system_readiness()
        
        # Step 3: Start application with monitoring
        self._start_application_with_monitoring()
        
        # Step 4: Verify deployment success
        return self._verify_deployment_success()
    
    def _clear_port_completely(self):
        """Completely clear port 5000 of all processes"""
        
        print(f"Watson: Clearing port {self.target_port} completely...")
        
        # Find all processes using port 5000
        port_processes = []
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == self.target_port:
                port_processes.append(conn.pid)
        
        # Terminate all port processes
        for pid in port_processes:
            try:
                process = psutil.Process(pid)
                print(f"Terminating process {pid}: {process.name()}")
                process.terminate()
                time.sleep(2)
                
                if process.is_running():
                    process.kill()
                    print(f"Force killed process {pid}")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Kill any remaining Python processes running main.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline:
                        print(f"Terminating Python process: {proc.info['pid']}")
                        proc.terminate()
                        time.sleep(1)
                        if proc.is_running():
                            proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Final verification that port is clear
        time.sleep(3)
        port_clear = True
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == self.target_port:
                port_clear = False
                break
        
        if port_clear:
            print(f"Watson: Port {self.target_port} successfully cleared")
        else:
            print(f"Watson: Warning - Port {self.target_port} may still be occupied")
        
        return port_clear
    
    def _verify_system_readiness(self):
        """Verify system is ready for deployment"""
        
        print("Watson: Verifying system readiness...")
        
        readiness_checks = {
            'main_py_exists': os.path.exists('main.py'),
            'memory_available': psutil.virtual_memory().percent < 90,
            'disk_space': psutil.disk_usage('/').percent < 95,
            'port_available': self._check_port_availability()
        }
        
        for check, status in readiness_checks.items():
            print(f"  {check}: {'✓' if status else '✗'}")
        
        all_ready = all(readiness_checks.values())
        print(f"Watson: System readiness: {'Ready' if all_ready else 'Issues detected'}")
        
        return all_ready
    
    def _check_port_availability(self):
        """Check if target port is available"""
        
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', self.target_port))
            sock.close()
            return True
        except socket.error:
            return False
    
    def _start_application_with_monitoring(self):
        """Start application with continuous monitoring"""
        
        print("Watson: Starting application with monitoring...")
        
        # Set environment variables
        os.environ['SESSION_SECRET'] = 'nexus_watson_supreme_deployment'
        
        # Start application in background
        try:
            # Use exec to replace shell process
            app_process = subprocess.Popen([
                sys.executable, 'main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
            
            print(f"Watson: Application started with PID {app_process.pid}")
            
            # Monitor startup for 10 seconds
            startup_success = False
            for i in range(10):
                time.sleep(1)
                
                # Check if process is still running
                if app_process.poll() is not None:
                    stdout, stderr = app_process.communicate()
                    print(f"Watson: Application exited early. Error: {stderr.decode()}")
                    break
                
                # Check if port is being used (application started successfully)
                if self._is_port_in_use():
                    print(f"Watson: Application successfully bound to port {self.target_port}")
                    startup_success = True
                    break
                
                print(f"Watson: Monitoring startup... {i+1}/10")
            
            return startup_success, app_process.pid
            
        except Exception as e:
            print(f"Watson: Application start failed: {e}")
            return False, None
    
    def _is_port_in_use(self):
        """Check if target port is currently in use"""
        
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == self.target_port:
                return True
        return False
    
    def _verify_deployment_success(self):
        """Verify deployment was successful"""
        
        print("Watson: Verifying deployment success...")
        
        # Check if application is responding on port
        success_metrics = {
            'port_bound': self._is_port_in_use(),
            'process_running': self._check_app_process_health(),
            'response_test': self._test_application_response()
        }
        
        for metric, status in success_metrics.items():
            print(f"  {metric}: {'✓' if status else '✗'}")
        
        deployment_success = all(success_metrics.values())
        
        if deployment_success:
            print("Watson: Deployment completed successfully!")
            print(f"Application available at: http://0.0.0.0:{self.target_port}")
        else:
            print("Watson: Deployment verification failed")
        
        return deployment_success
    
    def _check_app_process_health(self):
        """Check if application process is healthy"""
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline:
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    def _test_application_response(self):
        """Test if application is responding"""
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', self.target_port))
            sock.close()
            return result == 0
        except:
            return False

def execute_watson_deployment():
    """Execute Watson's ultimate deployment solution"""
    
    deployment_master = WatsonDeploymentMaster()
    return deployment_master.execute_deployment()

if __name__ == "__main__":
    success = execute_watson_deployment()
    exit(0 if success else 1)