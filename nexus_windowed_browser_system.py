"""
NEXUS Windowed Browser System
Creates visible browser windows within the interface using VNC display
"""

import os
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, Any, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import threading

class WindowedBrowserSystem:
    """System for creating visible browser windows within the interface"""
    
    def __init__(self):
        self.active_windows = {}
        self.display_port = ":99"
        self.vnc_port = 5900
        self.setup_virtual_display()
        
    def setup_virtual_display(self):
        """Setup virtual display for windowed browsers"""
        try:
            # Start Xvfb virtual display
            subprocess.run([
                "Xvfb", self.display_port, 
                "-screen", "0", "1920x1080x24",
                "-ac", "-nolisten", "tcp"
            ], check=False, capture_output=True)
            
            # Set display environment
            os.environ["DISPLAY"] = self.display_port
            
            # Start VNC server for display sharing
            subprocess.run([
                "x11vnc", "-display", self.display_port,
                "-rfbport", str(self.vnc_port),
                "-forever", "-shared", "-bg"
            ], check=False, capture_output=True)
            
            print(f"Virtual display setup complete on {self.display_port}")
            return True
            
        except Exception as e:
            print(f"Virtual display setup failed: {e}")
            return False
    
    def create_windowed_browser(self, window_id: str = None, url: str = None) -> Dict[str, Any]:
        """Create a new windowed browser instance"""
        
        if not window_id:
            window_id = f"browser_{int(time.time() * 1000)}"
        
        if not url:
            url = "https://example.com"
        
        try:
            # Configure Chrome for windowed display
            chrome_options = Options()
            chrome_options.add_argument(f"--display={self.display_port}")
            chrome_options.add_argument("--window-size=800,600")
            chrome_options.add_argument("--window-position=100,100")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.binary_location = "/usr/bin/chromium"
            
            # Create driver instance
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Store window information
            self.active_windows[window_id] = {
                "driver": driver,
                "url": url,
                "created_at": datetime.utcnow().isoformat(),
                "window_handle": driver.current_window_handle,
                "status": "active"
            }
            
            return {
                "success": True,
                "window_id": window_id,
                "url": url,
                "vnc_display": f"localhost:{self.vnc_port}",
                "display": self.display_port,
                "status": "browser_window_created"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create windowed browser: {str(e)}"
            }
    
    def navigate_window(self, window_id: str, url: str) -> Dict[str, Any]:
        """Navigate a specific browser window to a new URL"""
        
        if window_id not in self.active_windows:
            return {"error": "Window not found"}
        
        try:
            driver = self.active_windows[window_id]["driver"]
            driver.get(url)
            self.active_windows[window_id]["url"] = url
            
            return {
                "success": True,
                "window_id": window_id,
                "new_url": url,
                "title": driver.title
            }
            
        except Exception as e:
            return {"error": f"Navigation failed: {str(e)}"}
    
    def get_window_info(self, window_id: str) -> Dict[str, Any]:
        """Get information about a specific browser window"""
        
        if window_id not in self.active_windows:
            return {"error": "Window not found"}
        
        try:
            window_data = self.active_windows[window_id]
            driver = window_data["driver"]
            
            return {
                "window_id": window_id,
                "url": driver.current_url,
                "title": driver.title,
                "size": driver.get_window_size(),
                "position": driver.get_window_position(),
                "created_at": window_data["created_at"],
                "status": window_data["status"]
            }
            
        except Exception as e:
            return {"error": f"Failed to get window info: {str(e)}"}
    
    def list_active_windows(self) -> Dict[str, Any]:
        """List all active browser windows"""
        
        windows = []
        for window_id, window_data in self.active_windows.items():
            try:
                driver = window_data["driver"]
                windows.append({
                    "window_id": window_id,
                    "url": driver.current_url,
                    "title": driver.title,
                    "status": window_data["status"],
                    "created_at": window_data["created_at"]
                })
            except:
                windows.append({
                    "window_id": window_id,
                    "status": "inactive",
                    "created_at": window_data["created_at"]
                })
        
        return {
            "total_windows": len(windows),
            "active_windows": windows,
            "vnc_display": f"localhost:{self.vnc_port}",
            "display_port": self.display_port
        }
    
    def close_window(self, window_id: str) -> Dict[str, Any]:
        """Close a specific browser window"""
        
        if window_id not in self.active_windows:
            return {"error": "Window not found"}
        
        try:
            driver = self.active_windows[window_id]["driver"]
            driver.quit()
            del self.active_windows[window_id]
            
            return {
                "success": True,
                "window_id": window_id,
                "status": "window_closed"
            }
            
        except Exception as e:
            return {"error": f"Failed to close window: {str(e)}"}
    
    def close_all_windows(self) -> Dict[str, Any]:
        """Close all active browser windows"""
        
        closed_count = 0
        errors = []
        
        for window_id in list(self.active_windows.keys()):
            try:
                result = self.close_window(window_id)
                if result.get("success"):
                    closed_count += 1
                else:
                    errors.append(f"Window {window_id}: {result.get('error')}")
            except Exception as e:
                errors.append(f"Window {window_id}: {str(e)}")
        
        return {
            "success": True,
            "closed_windows": closed_count,
            "errors": errors,
            "status": "all_windows_closed"
        }
    
    def execute_script_in_window(self, window_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript in a specific browser window"""
        
        if window_id not in self.active_windows:
            return {"error": "Window not found"}
        
        try:
            driver = self.active_windows[window_id]["driver"]
            result = driver.execute_script(script)
            
            return {
                "success": True,
                "window_id": window_id,
                "script_result": result
            }
            
        except Exception as e:
            return {"error": f"Script execution failed: {str(e)}"}
    
    def take_screenshot(self, window_id: str) -> Dict[str, Any]:
        """Take screenshot of a specific browser window"""
        
        if window_id not in self.active_windows:
            return {"error": "Window not found"}
        
        try:
            driver = self.active_windows[window_id]["driver"]
            screenshot_path = f"/tmp/screenshot_{window_id}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            
            return {
                "success": True,
                "window_id": window_id,
                "screenshot_path": screenshot_path
            }
            
        except Exception as e:
            return {"error": f"Screenshot failed: {str(e)}"}

# Global windowed browser system
windowed_browser_system = WindowedBrowserSystem()

def create_windowed_browser(url: str = None):
    """Create a new windowed browser"""
    return windowed_browser_system.create_windowed_browser(url=url)

def list_browser_windows():
    """List all active browser windows"""
    return windowed_browser_system.list_active_windows()

def navigate_browser_window(window_id: str, url: str):
    """Navigate browser window to URL"""
    return windowed_browser_system.navigate_window(window_id, url)

def close_browser_window(window_id: str):
    """Close specific browser window"""
    return windowed_browser_system.close_window(window_id)

def get_browser_window_info(window_id: str):
    """Get browser window information"""
    return windowed_browser_system.get_window_info(window_id)

if __name__ == "__main__":
    # Test windowed browser system
    print("🖥️ Creating windowed browser system...")
    
    # Create test browser window
    result = create_windowed_browser("https://www.google.com")
    print(json.dumps(result, indent=2))
    
    if result.get("success"):
        # List active windows
        windows = list_browser_windows()
        print("\nActive Windows:")
        print(json.dumps(windows, indent=2))
        
        # Wait for user interaction
        print(f"\nVNC Display available at: localhost:{windowed_browser_system.vnc_port}")
        print("Browser window should be visible through VNC viewer")
        
        time.sleep(10)  # Keep window open for demonstration
        
        # Close all windows
        close_result = windowed_browser_system.close_all_windows()
        print("\nClosure Result:")
        print(json.dumps(close_result, indent=2))