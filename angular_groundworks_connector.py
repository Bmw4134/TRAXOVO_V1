"""
Angular Ground Works Connector
Specialized connector for Angular-based Ground Works system
"""

import requests
import json
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AngularGroundWorksConnector:
    """Specialized connector for Angular-based Ground Works system"""
    
    def __init__(self, base_url="https://groundworks.ragleinc.com", username=None, password=None):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.authenticated = False
        self.driver = None
        self.session = requests.Session()
        
        # Set up Chrome options for headless operation
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    def authenticate_with_selenium(self):
        """Authenticate using Selenium to handle Angular authentication"""
        try:
            # Initialize Chrome driver
            self.driver = webdriver.Chrome(options=self.chrome_options)
            
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for Angular app to load
            time.sleep(3)
            
            # Wait for login form elements to be present
            wait = WebDriverWait(self.driver, 15)
            
            # Common Angular login form selectors
            username_selectors = [
                "input[name='username']",
                "input[name='email']",
                "input[name='user']",
                "input[type='text']",
                "input[placeholder*='username' i]",
                "input[placeholder*='email' i]",
                "input[placeholder*='user' i]",
                "#username",
                "#email",
                "#user",
                ".username",
                ".email-input",
                ".user-input"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                "#password",
                ".password",
                ".password-input"
            ]
            
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[class*='login' i]",
                "button[class*='submit' i]",
                ".login-button",
                ".submit-button",
                ".btn-login",
                ".btn-primary"
            ]
            
            username_element = None
            password_element = None
            submit_element = None
            
            # Find username input
            for selector in username_selectors:
                try:
                    username_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            # Find password input
            for selector in password_selectors:
                try:
                    password_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            # Find submit button
            for selector in submit_selectors:
                try:
                    submit_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not username_element or not password_element:
                logging.error("Could not find login form elements")
                return False
            
            # Fill in credentials
            username_element.clear()
            username_element.send_keys(self.username)
            
            password_element.clear()
            password_element.send_keys(self.password)
            
            # Take screenshot for debugging
            self.driver.save_screenshot("/tmp/login_form.png")
            
            # Submit form
            if submit_element:
                submit_element.click()
            else:
                # Try submitting via form submission
                password_element.submit()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # Success indicators
            success_indicators = [
                "dashboard",
                "welcome",
                "home",
                "main",
                "logout"
            ]
            
            # Failure indicators
            failure_indicators = [
                "login failed",
                "invalid credentials",
                "authentication failed",
                "error",
                "wrong password"
            ]
            
            # Check URL for success
            if any(indicator in current_url.lower() for indicator in success_indicators):
                self.authenticated = True
                logging.info("Authentication successful - URL indicates success")
                return True
            
            # Check page content for success
            if any(indicator in page_source.lower() for indicator in success_indicators):
                self.authenticated = True
                logging.info("Authentication successful - page content indicates success")
                return True
            
            # Check for failure indicators
            if any(indicator in page_source.lower() for indicator in failure_indicators):
                logging.error("Authentication failed - error message detected")
                return False
            
            # If we're not on login page anymore, consider it success
            if "login" not in current_url.lower():
                self.authenticated = True
                logging.info("Authentication likely successful - redirected from login page")
                return True
            
            logging.warning("Authentication status unclear")
            return False
            
        except Exception as e:
            logging.error(f"Selenium authentication error: {e}")
            return False
    
    def extract_authenticated_data(self):
        """Extract data from authenticated Angular application"""
        if not self.authenticated or not self.driver:
            return {
                'status': 'error',
                'message': 'Not authenticated or driver not available'
            }
        
        extracted_data = {
            'projects': [],
            'assets': [],
            'personnel': [],
            'reports': [],
            'dashboard_data': {},
            'user_info': {}
        }
        
        try:
            # Navigate to different sections and extract data
            sections = [
                '/dashboard',
                '/projects',
                '/assets',
                '/equipment',
                '/reports',
                '/personnel',
                '/calendar',
                '/tasks'
            ]
            
            for section in sections:
                try:
                    self.driver.get(f"{self.base_url}{section}")
                    time.sleep(3)  # Wait for Angular to load data
                    
                    # Extract visible data from the page
                    page_data = self._extract_angular_data(section)
                    
                    if page_data:
                        section_name = section.strip('/').replace('/', '_')
                        if section_name in extracted_data:
                            extracted_data[section_name] = page_data
                        else:
                            extracted_data['reports'].append({
                                'section': section_name,
                                'data': page_data,
                                'extracted_at': str(datetime.now())
                            })
                
                except Exception as e:
                    logging.debug(f"Failed to extract from {section}: {e}")
                    continue
            
            return {
                'status': 'success',
                'data': extracted_data,
                'extraction_method': 'angular_selenium'
            }
            
        except Exception as e:
            logging.error(f"Data extraction error: {e}")
            return {
                'status': 'error',
                'message': f'Data extraction failed: {e}'
            }
    
    def _extract_angular_data(self, section):
        """Extract structured data from Angular components"""
        try:
            # Wait for data to load
            time.sleep(2)
            
            # Common Angular data containers
            data_selectors = [
                '.data-table tbody tr',
                '.grid-row',
                '.list-item',
                '.card',
                '.data-item',
                'table tbody tr',
                '.ng-star-inserted',
                '.mat-row',
                '.mat-list-item'
            ]
            
            extracted_items = []
            
            for selector in data_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        for element in elements[:50]:  # Limit to first 50 items
                            item_data = {
                                'text': element.text.strip(),
                                'html': element.get_attribute('innerHTML'),
                                'attributes': {}
                            }
                            
                            # Extract common attributes
                            for attr in ['id', 'class', 'data-id', 'data-value']:
                                value = element.get_attribute(attr)
                                if value:
                                    item_data['attributes'][attr] = value
                            
                            if item_data['text']:
                                extracted_items.append(item_data)
                        
                        if extracted_items:
                            break
                
                except Exception as e:
                    continue
            
            # Also try to extract from JSON data embedded in page
            try:
                scripts = self.driver.find_elements(By.TAG_NAME, 'script')
                for script in scripts:
                    script_content = script.get_attribute('innerHTML')
                    if script_content and ('data' in script_content or 'json' in script_content.lower()):
                        # Look for JSON-like structures
                        import re
                        json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_content)
                        for match in json_matches:
                            try:
                                json_data = json.loads(match)
                                if isinstance(json_data, dict) and json_data:
                                    extracted_items.append({
                                        'type': 'embedded_json',
                                        'data': json_data
                                    })
                            except:
                                continue
            except:
                pass
            
            return extracted_items if extracted_items else None
            
        except Exception as e:
            logging.debug(f"Angular data extraction error: {e}")
            return None
    
    def connect_and_extract(self):
        """Main method to connect and extract all data"""
        try:
            # Authenticate using Selenium
            if not self.authenticate_with_selenium():
                return {
                    'status': 'error',
                    'message': 'Authentication failed'
                }
            
            # Extract data
            extraction_result = self.extract_authenticated_data()
            
            return extraction_result
            
        except Exception as e:
            logging.error(f"Connection error: {e}")
            return {
                'status': 'error',
                'message': f'Connection failed: {e}'
            }
        
        finally:
            # Clean up
            if self.driver:
                self.driver.quit()

def test_angular_groundworks_connection(username, password):
    """Test Angular Ground Works connection"""
    connector = AngularGroundWorksConnector(
        base_url="https://groundworks.ragleinc.com",
        username=username,
        password=password
    )
    
    result = connector.connect_and_extract()
    return result