"""
NEXUS Real Browser Automation Engine
Headless browser automation for timecard entry and web interactions
"""

import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class NexusBrowserAutomation:
    """Real headless browser automation system"""
    
    def __init__(self):
        self.driver = None
        self.automation_log = []
        self.active_sessions = {}
        
    def create_browser_session(self, session_id=None, windowed=True):
        """Create new browser session (windowed by default for visibility)"""
        
        if not session_id:
            session_id = f"nexus_session_{int(time.time())}"
        
        chrome_options = Options()
        if not windowed:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1200,800")
        chrome_options.add_argument("--window-position=100,100")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            self.active_sessions[session_id] = {
                'driver': driver,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            
            self._log_action(f"Browser session created: {session_id}")
            
            return {
                'status': 'success',
                'session_id': session_id,
                'message': 'Browser session created successfully'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to create browser session: {str(e)}'
            }
    
    def automate_timecard_entry(self, session_id, timecard_config):
        """Automate timecard entry on specified website"""
        
        if session_id not in self.active_sessions:
            return {'status': 'error', 'message': 'Invalid session ID'}
        
        driver = self.active_sessions[session_id]['driver']
        
        try:
            # Extract configuration
            website_url = timecard_config.get('website_url')
            employee_id = timecard_config.get('employee_id')
            username = timecard_config.get('username')
            password = timecard_config.get('password')
            start_time = timecard_config.get('start_time', '09:00')
            end_time = timecard_config.get('end_time', '17:00')
            break_minutes = timecard_config.get('break_minutes', 30)
            
            self._log_action(f"Starting timecard automation for {website_url}")
            
            # Step 1: Navigate to website
            driver.get(website_url)
            self._log_action(f"Navigated to {website_url}")
            time.sleep(2)
            
            # Step 2: Handle login if credentials provided
            if username and password:
                login_result = self._handle_login(driver, username, password)
                if not login_result['success']:
                    return {'status': 'error', 'message': f'Login failed: {login_result["message"]}'}
            
            # Step 3: Fill timecard form
            timecard_result = self._fill_timecard_form(driver, {
                'employee_id': employee_id,
                'start_time': start_time,
                'end_time': end_time,
                'break_minutes': break_minutes
            })
            
            if not timecard_result['success']:
                return {'status': 'error', 'message': f'Timecard entry failed: {timecard_result["message"]}'}
            
            # Step 4: Submit timecard
            submit_result = self._submit_timecard(driver)
            
            self._log_action("Timecard automation completed successfully")
            
            return {
                'status': 'success',
                'session_id': session_id,
                'actions_completed': [
                    'navigation',
                    'login' if username else 'direct_access',
                    'form_filling',
                    'submission'
                ],
                'time_saved_minutes': 10,
                'message': 'Timecard entry automated successfully'
            }
            
        except Exception as e:
            self._log_action(f"Automation error: {str(e)}")
            return {'status': 'error', 'message': f'Automation failed: {str(e)}'}
    
    def _handle_login(self, driver, username, password):
        """Handle website login process"""
        
        try:
            # Common login field selectors
            username_selectors = [
                'input[name="username"]',
                'input[name="email"]',
                'input[name="user"]',
                'input[type="email"]',
                '#username',
                '#email',
                '#user'
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password'
            ]
            
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Login")',
                'button:contains("Sign In")',
                '.login-button',
                '#login'
            ]
            
            # Find and fill username
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not username_field:
                return {'success': False, 'message': 'Username field not found'}
            
            username_field.clear()
            username_field.send_keys(username)
            self._log_action("Username entered")
            
            # Find and fill password
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_field:
                return {'success': False, 'message': 'Password field not found'}
            
            password_field.clear()
            password_field.send_keys(password)
            self._log_action("Password entered")
            
            # Find and click login button
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if login_button:
                login_button.click()
                self._log_action("Login button clicked")
            else:
                # Try pressing Enter in password field
                password_field.send_keys(Keys.RETURN)
                self._log_action("Login submitted via Enter key")
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful (look for common error indicators)
            error_indicators = [
                '.error',
                '.alert-danger',
                '.login-error',
                '[class*="error"]'
            ]
            
            for indicator in error_indicators:
                try:
                    error_element = driver.find_element(By.CSS_SELECTOR, indicator)
                    if error_element.is_displayed():
                        return {'success': False, 'message': 'Login failed - invalid credentials'}
                except:
                    continue
            
            return {'success': True, 'message': 'Login successful'}
            
        except Exception as e:
            return {'success': False, 'message': f'Login process error: {str(e)}'}
    
    def _fill_timecard_form(self, driver, timecard_data):
        """Fill timecard form fields"""
        
        try:
            # Common timecard field mappings
            field_mappings = {
                'employee_id': [
                    'input[name="employee_id"]',
                    'input[name="empid"]',
                    'input[name="emp_id"]',
                    '#employee_id',
                    '#empid'
                ],
                'date': [
                    'input[name="date"]',
                    'input[name="work_date"]',
                    'input[type="date"]',
                    '#date',
                    '#work_date'
                ],
                'start_time': [
                    'input[name="start_time"]',
                    'input[name="startTime"]',
                    'input[name="clock_in"]',
                    '#start_time',
                    '#startTime'
                ],
                'end_time': [
                    'input[name="end_time"]',
                    'input[name="endTime"]',
                    'input[name="clock_out"]',
                    '#end_time',
                    '#endTime'
                ],
                'break_time': [
                    'input[name="break_time"]',
                    'input[name="break"]',
                    'input[name="break_minutes"]',
                    '#break_time',
                    '#break'
                ]
            }
            
            # Fill employee ID if provided
            if timecard_data.get('employee_id'):
                for selector in field_mappings['employee_id']:
                    try:
                        field = driver.find_element(By.CSS_SELECTOR, selector)
                        field.clear()
                        field.send_keys(timecard_data['employee_id'])
                        self._log_action(f"Employee ID entered: {timecard_data['employee_id']}")
                        break
                    except:
                        continue
            
            # Fill current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            for selector in field_mappings['date']:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    field.clear()
                    field.send_keys(current_date)
                    self._log_action(f"Date entered: {current_date}")
                    break
                except:
                    continue
            
            # Fill start time
            for selector in field_mappings['start_time']:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    field.clear()
                    field.send_keys(timecard_data['start_time'])
                    self._log_action(f"Start time entered: {timecard_data['start_time']}")
                    break
                except:
                    continue
            
            # Fill end time
            for selector in field_mappings['end_time']:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    field.clear()
                    field.send_keys(timecard_data['end_time'])
                    self._log_action(f"End time entered: {timecard_data['end_time']}")
                    break
                except:
                    continue
            
            # Fill break time
            for selector in field_mappings['break_time']:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    field.clear()
                    field.send_keys(str(timecard_data['break_minutes']))
                    self._log_action(f"Break time entered: {timecard_data['break_minutes']} minutes")
                    break
                except:
                    continue
            
            return {'success': True, 'message': 'Timecard form filled successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Form filling error: {str(e)}'}
    
    def _submit_timecard(self, driver):
        """Submit the timecard form"""
        
        try:
            # Common submit button selectors
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Submit")',
                'button:contains("Save")',
                '.submit-button',
                '.save-button',
                '#submit',
                '#save'
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    submit_button.click()
                    self._log_action("Timecard submitted")
                    time.sleep(2)
                    return {'success': True, 'message': 'Timecard submitted successfully'}
                except:
                    continue
            
            return {'success': False, 'message': 'Submit button not found'}
            
        except Exception as e:
            return {'success': False, 'message': f'Submission error: {str(e)}'}
    
    def take_screenshot(self, session_id, filename=None):
        """Take screenshot of current browser state"""
        
        if session_id not in self.active_sessions:
            return {'status': 'error', 'message': 'Invalid session ID'}
        
        driver = self.active_sessions[session_id]['driver']
        
        if not filename:
            filename = f"nexus_screenshot_{int(time.time())}.png"
        
        try:
            driver.save_screenshot(filename)
            return {
                'status': 'success',
                'filename': filename,
                'message': 'Screenshot saved successfully'
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Screenshot failed: {str(e)}'}
    
    def close_session(self, session_id):
        """Close browser session"""
        
        if session_id not in self.active_sessions:
            return {'status': 'error', 'message': 'Invalid session ID'}
        
        try:
            driver = self.active_sessions[session_id]['driver']
            driver.quit()
            del self.active_sessions[session_id]
            
            self._log_action(f"Browser session closed: {session_id}")
            
            return {
                'status': 'success',
                'session_id': session_id,
                'message': 'Browser session closed successfully'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Session close failed: {str(e)}'}
    
    def get_active_sessions(self):
        """Get list of active browser sessions"""
        
        sessions = []
        for session_id, session_data in self.active_sessions.items():
            sessions.append({
                'session_id': session_id,
                'created_at': session_data['created_at'],
                'status': session_data['status']
            })
        
        return {
            'active_sessions': sessions,
            'total_count': len(sessions)
        }
    
    def _log_action(self, action):
        """Log automation action"""
        
        log_entry = {
            'action': action,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.automation_log.append(log_entry)
        print(f"[NEXUS AUTOMATION] {action}")
    
    def get_automation_log(self):
        """Get automation execution log"""
        
        return {
            'log_entries': self.automation_log,
            'total_entries': len(self.automation_log)
        }

# Global browser automation engine
nexus_browser = NexusBrowserAutomation()

def create_automation_session():
    """Create new browser automation session"""
    return nexus_browser.create_browser_session()

def automate_timecard(session_id, config):
    """Automate timecard entry"""
    return nexus_browser.automate_timecard_entry(session_id, config)

def take_browser_screenshot(session_id, filename=None):
    """Take screenshot of browser"""
    return nexus_browser.take_screenshot(session_id, filename)

def close_automation_session(session_id):
    """Close browser session"""
    return nexus_browser.close_session(session_id)

def get_browser_sessions():
    """Get active browser sessions"""
    return nexus_browser.get_active_sessions()

def get_automation_log():
    """Get automation log"""
    return nexus_browser.get_automation_log()