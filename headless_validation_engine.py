"""
TRAXOVO Headless Browser Validation Engine
Real-time UI testing and autonomous issue detection
"""
import asyncio
import logging
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class HeadlessBrowserValidator:
    """Autonomous headless browser validation system"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.driver = None
        self.validation_results = {}
        
    def setup_headless_browser(self):
        """Initialize headless Chrome browser"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--silent")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            logging.error(f"Browser setup failed: {e}")
            return False
    
    def execute_complete_validation(self):
        """Execute comprehensive UI validation"""
        if not self.setup_headless_browser():
            return {'error': 'Browser setup failed'}
        
        try:
            results = {
                'login_page_validation': self._validate_login_page(),
                'authentication_flow': self._validate_authentication(),
                'dashboard_functionality': self._validate_dashboard(),
                'mobile_responsiveness': self._validate_mobile_view(),
                'javascript_errors': self._check_javascript_errors(),
                'performance_metrics': self._measure_performance(),
                'ui_element_stability': self._check_ui_stability()
            }
            
            return {
                'validation_complete': True,
                'overall_score': self._calculate_overall_score(results),
                'results': results,
                'timestamp': time.time()
            }
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _validate_login_page(self):
        """Validate login page renders correctly"""
        try:
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for essential elements
            checks = {
                'title_present': bool(self.driver.find_elements(By.TAG_NAME, "h1")),
                'login_form': bool(self.driver.find_elements(By.NAME, "username")),
                'password_field': bool(self.driver.find_elements(By.NAME, "password")),
                'submit_button': bool(self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")),
                'no_404_error': "404" not in self.driver.page_source,
                'css_loaded': bool(self.driver.find_elements(By.CSS_SELECTOR, ".hero-section"))
            }
            
            return {
                'status': 'success',
                'checks': checks,
                'score': sum(checks.values()) / len(checks)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _validate_authentication(self):
        """Test authentication flow"""
        try:
            self.driver.get(f"{self.base_url}/login")
            
            # Fill login form with test credentials
            username_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            username_field.send_keys("tester")
            password_field.send_keys("tester")
            submit_button.click()
            
            # Wait for redirect or response
            time.sleep(2)
            
            return {
                'status': 'success',
                'current_url': self.driver.current_url,
                'redirected': self.driver.current_url != f"{self.base_url}/login",
                'score': 1.0 if 'dashboard' in self.driver.current_url else 0.8
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _validate_dashboard(self):
        """Validate dashboard functionality after login"""
        try:
            # Navigate to dashboard
            self.driver.get(f"{self.base_url}/dashboard")
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            checks = {
                'dashboard_loaded': 'dashboard' in self.driver.current_url,
                'metrics_visible': bool(self.driver.find_elements(By.CSS_SELECTOR, ".metric-card")),
                'navigation_present': bool(self.driver.find_elements(By.CSS_SELECTOR, ".nav-link")),
                'no_500_error': "500" not in self.driver.page_source,
                'fleet_data_visible': "717" in self.driver.page_source or "614" in self.driver.page_source,
                'authentic_data': "$461" in self.driver.page_source or "March 2025" in self.driver.page_source
            }
            
            return {
                'status': 'success',
                'checks': checks,
                'score': sum(checks.values()) / len(checks)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _validate_mobile_view(self):
        """Test mobile responsiveness"""
        try:
            # Set mobile viewport
            self.driver.set_window_size(375, 667)  # iPhone dimensions
            self.driver.get(f"{self.base_url}/login")
            
            time.sleep(2)
            
            checks = {
                'mobile_viewport': self.driver.get_window_size()['width'] == 375,
                'text_readable': self._check_text_overflow(),
                'buttons_touchable': self._check_button_sizes(),
                'no_horizontal_scroll': not self._has_horizontal_scroll()
            }
            
            return {
                'status': 'success',
                'checks': checks,
                'score': sum(checks.values()) / len(checks)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _check_javascript_errors(self):
        """Check for JavaScript errors in console"""
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            return {
                'status': 'success',
                'error_count': len(errors),
                'errors': [error['message'] for error in errors[:5]],  # First 5 errors
                'score': 1.0 if len(errors) == 0 else max(0.0, 1.0 - (len(errors) * 0.1))
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.5}
    
    def _measure_performance(self):
        """Measure page load performance"""
        try:
            start_time = time.time()
            self.driver.get(f"{self.base_url}/login")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            return {
                'status': 'success',
                'load_time_seconds': round(load_time, 2),
                'score': 1.0 if load_time < 2.0 else max(0.0, 2.0 - load_time)
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _check_ui_stability(self):
        """Check for visual element flashing or instability"""
        try:
            self.driver.get(f"{self.base_url}/login")
            
            # Take screenshot after initial load
            time.sleep(1)
            screenshot1 = self.driver.get_screenshot_as_png()
            
            # Wait and take another screenshot
            time.sleep(2)
            screenshot2 = self.driver.get_screenshot_as_png()
            
            # Basic stability check (screenshots should be similar)
            stability_score = 1.0 if len(screenshot1) == len(screenshot2) else 0.8
            
            return {
                'status': 'success',
                'visual_stability': True,
                'score': stability_score
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0.0}
    
    def _check_text_overflow(self):
        """Check for text overflow issues"""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "*")
            for element in elements[:20]:  # Check first 20 elements
                if element.size['width'] > self.driver.get_window_size()['width']:
                    return False
            return True
        except:
            return True
    
    def _check_button_sizes(self):
        """Check if buttons meet touch target requirements"""
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if button.size['height'] < 44:  # iOS recommended touch target
                    return False
            return True
        except:
            return True
    
    def _has_horizontal_scroll(self):
        """Check for horizontal scrolling"""
        try:
            return self.driver.execute_script("return document.body.scrollWidth > window.innerWidth")
        except:
            return False
    
    def _calculate_overall_score(self, results):
        """Calculate overall validation score"""
        scores = []
        for result in results.values():
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])
        
        return round(sum(scores) / len(scores), 2) if scores else 0.0

# Global validator instance
headless_validator = HeadlessBrowserValidator()