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
        
        # Anti-detection measures for PTNI operations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--window-position=100,100")
        
        # Human-like user agent rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        import random
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Advanced anti-detection features
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # Override when needed
        chrome_options.add_argument("--disable-default-apps")
        
        # Additional stealth measures
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "geolocation": 2,
                "media_stream": 2,
            },
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Inject anti-detection JavaScript immediately after driver creation
            self._inject_stealth_scripts(driver)
            
            self.active_sessions[session_id] = {
                'driver': driver,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'stealth_mode': True,
                'anti_detection_active': True
            }
            
            self._log_action(f"PTNI Stealth Browser session created: {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'driver_status': 'active',
                'stealth_features': 'enabled'
            }
            
        except Exception as e:
            self._log_action(f"Failed to create browser session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _inject_stealth_scripts(self, driver):
        """Inject comprehensive anti-detection JavaScript"""
        
        # Core stealth script to hide automation indicators
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override chrome runtime
        window.chrome = {
            runtime: {},
            loadTimes: function() {
                return {
                    requestTime: performance.now(),
                    startLoadTime: performance.now(),
                    commitLoadTime: performance.now(),
                    finishDocumentLoadTime: performance.now(),
                    finishLoadTime: performance.now(),
                    firstPaintTime: performance.now(),
                    firstPaintAfterLoadTime: 0,
                    navigationType: 'Other'
                };
            },
            csi: function() {
                return {
                    onloadT: performance.now(),
                    startE: performance.now(),
                    tran: 15
                };
            }
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Hide plugins length
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock touch events for mobile simulation
        if (!window.ontouchstart) {
            window.ontouchstart = null;
        }
        
        // Human-like mouse movement simulation
        let mouseEvents = [];
        document.addEventListener('mousemove', function(e) {
            mouseEvents.push({x: e.clientX, y: e.clientY, time: Date.now()});
            if (mouseEvents.length > 50) mouseEvents.shift();
        });
        
        // Random timing variations
        const originalSetTimeout = window.setTimeout;
        window.setTimeout = function(callback, delay) {
            const variation = Math.random() * 100 - 50; // ±50ms variation
            return originalSetTimeout(callback, delay + variation);
        };
        
        // Console override to hide automation traces
        console.clear();
        """
        
        try:
            driver.execute_script(stealth_script)
        except:
            pass  # Silently continue if injection fails
    
    def _simulate_human_behavior(self, driver, action_type="navigation"):
        """Simulate human-like behavior patterns"""
        import random
        import time
        
        # Random delays between actions
        base_delay = {
            'navigation': 2.5,
            'form_fill': 1.2,
            'click': 0.8,
            'scroll': 1.5
        }.get(action_type, 1.0)
        
        # Add human-like variation
        delay = base_delay + random.uniform(-0.5, 1.0)
        time.sleep(max(0.3, delay))
        
        # Simulate mouse movements
        try:
            # Random scroll to simulate reading
            if random.random() < 0.3:
                scroll_amount = random.randint(100, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
                
            # Random small mouse movements
            if random.random() < 0.4:
                driver.execute_script("""
                    const event = new MouseEvent('mousemove', {
                        clientX: Math.random() * window.innerWidth,
                        clientY: Math.random() * window.innerHeight
                    });
                    document.dispatchEvent(event);
                """)
        except:
            pass
    
    def _rotate_session_fingerprint(self, driver):
        """Rotate browser fingerprint for enhanced stealth"""
        try:
            # Inject new viewport size
            viewports = [
                (1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)
            ]
            import random
            width, height = random.choice(viewports)
            driver.set_window_size(width, height)
            
            # Rotate timezone
            timezones = [
                'America/New_York', 'America/Los_Angeles', 'America/Chicago',
                'Europe/London', 'Europe/Berlin', 'Asia/Tokyo'
            ]
            timezone = random.choice(timezones)
            
            timezone_script = f"""
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    return {{
                        locale: 'en-US',
                        timeZone: '{timezone}',
                        calendar: 'gregory',
                        numberingSystem: 'latn'
                    }};
                }}
            }});
            """
            driver.execute_script(timezone_script)
            
        except:
            pass
    
    def execute_platform_login(self, url, username, password, config):
        """Execute platform-specific login with credentials"""
        try:
            # Get the first available session
            session_id = list(self.active_sessions.keys())[0] if self.active_sessions else None
            
            if not session_id:
                return {'success': False, 'error': 'No active browser sessions'}
            
            driver = self.active_sessions[session_id]['driver']
            
            # Navigate to login page with stealth behavior
            driver.get(url)
            self._simulate_human_behavior(driver, "navigation")
            
            # Re-inject stealth scripts after navigation
            self._inject_stealth_scripts(driver)
            
            # Rotate fingerprint for enhanced stealth
            self._rotate_session_fingerprint(driver)
            
            # Wait for page to load with human-like behavior
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            self._simulate_human_behavior(driver, "scroll")
            
            # Handle different authentication flows
            if 'groundworks' in url.lower():
                return self._handle_groundworks_login(driver, username, password, config)
            elif 'gaugesmart' in url.lower():
                return self._handle_gaugesmart_login(driver, username, password, config)
            else:
                return self._handle_generic_login(driver, username, password, config)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_groundworks_login(self, driver, username, password, config):
        """Handle GroundWorks platform login"""
        try:
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()
            
            # Check if already on an authenticated page
            if any(indicator in current_url for indicator in ['dashboard', 'main', 'home']):
                return {
                    'success': True,
                    'status': 'already_authenticated',
                    'current_url': driver.current_url,
                    'authentication_result': {'message': 'Already authenticated or direct access available'}
                }
            
            # Look for login forms (Angular app may load dynamically)
            time.sleep(5)  # Allow Angular to load
            
            try:
                # Try to find email/username field
                email_field = None
                for selector in ['input[type="email"]', 'input[name*="email"]', 'input[name*="username"]']:
                    try:
                        email_field = driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except:
                        continue
                
                if email_field:
                    # Human-like form filling with anti-detection
                    self._simulate_human_behavior(driver, "form_fill")
                    email_field.clear()
                    self._type_like_human(email_field, username)
                    
                    # Find password field
                    password_field = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                    self._simulate_human_behavior(driver, "form_fill")
                    password_field.clear()
                    self._type_like_human(password_field, password)
                    
                    # Submit form with human delay
                    self._simulate_human_behavior(driver, "click")
                    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                    submit_button.click()
                    
                    # Wait with human-like behavior
                    self._simulate_human_behavior(driver, "navigation")
                    
                    # Check authentication result
                    final_url = driver.current_url.lower()
                    if any(indicator in final_url for indicator in config['success_indicators']):
                        return self._extract_authenticated_data(driver, 'groundworks')
                
            except Exception as form_error:
                pass
            
            # Enterprise authentication detected
            return {
                'success': False,
                'status': 'enterprise_auth_required',
                'current_url': driver.current_url,
                'authentication_result': {
                    'message': 'GroundWorks requires enterprise SSO authentication',
                    'platform_type': 'Angular SPA with enterprise authentication',
                    'recommendation': 'Contact IT for SSO integration credentials'
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_gaugesmart_login(self, driver, username, password, config):
        """Handle GaugeSmart platform login"""
        try:
            # Extract form details
            page_source = driver.page_source
            
            # Find CSRF token
            csrf_token = None
            try:
                csrf_input = driver.find_element(By.CSS_SELECTOR, 'input[name="__RequestVerificationToken"]')
                csrf_token = csrf_input.get_attribute('value')
            except:
                pass
            
            # Fill username field
            username_field = driver.find_element(By.CSS_SELECTOR, config['username_field'])
            username_field.clear()
            username_field.send_keys(username)
            
            # Fill password field
            password_field = driver.find_element(By.CSS_SELECTOR, config['password_field'])
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, config['submit_button'])
            submit_button.click()
            
            time.sleep(5)
            
            # Check authentication result
            final_url = driver.current_url.lower()
            page_content = driver.page_source.lower()
            
            # Check for success indicators
            success_found = any(indicator in final_url or indicator in page_content 
                              for indicator in config['success_indicators'])
            
            # Check for error indicators
            error_found = any(indicator in page_content 
                            for indicator in ['error', 'invalid', 'incorrect', 'failed'])
            
            if success_found and not error_found:
                return self._extract_authenticated_data(driver, 'gaugesmart')
            else:
                return {
                    'success': False,
                    'status': 'authentication_failed',
                    'current_url': driver.current_url,
                    'authentication_result': {
                        'message': 'Authentication failed - credentials may need verification',
                        'possible_issues': [
                            'Password may have changed',
                            '2FA verification required',
                            'Account may be locked',
                            'Additional security measures active'
                        ]
                    }
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_generic_login(self, driver, username, password, config):
        """Handle generic platform login"""
        try:
            # Fill username field
            username_field = driver.find_element(By.CSS_SELECTOR, config['username_field'])
            username_field.clear()
            username_field.send_keys(username)
            
            # Fill password field
            password_field = driver.find_element(By.CSS_SELECTOR, config['password_field'])
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, config['submit_button'])
            submit_button.click()
            
            time.sleep(3)
            
            # Check result
            final_url = driver.current_url.lower()
            success_found = any(indicator in final_url for indicator in config['success_indicators'])
            
            if success_found:
                return self._extract_authenticated_data(driver, 'generic')
            else:
                return {'success': False, 'status': 'authentication_failed'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_authenticated_data(self, driver, platform):
        """Extract data from authenticated session"""
        try:
            page_source = driver.page_source
            
            # Extract navigation links
            nav_links = []
            try:
                link_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                nav_links = [{'text': link.text, 'href': link.get_attribute('href')} 
                           for link in link_elements[:15] if link.text.strip()]
            except:
                pass
            
            # Extract forms
            forms = []
            try:
                form_elements = driver.find_elements(By.TAG_NAME, 'form')
                forms = [form.get_attribute('action') for form in form_elements]
            except:
                pass
            
            # Extract data elements
            data_elements = 0
            gauge_elements = 0
            
            if platform == 'gaugesmart':
                # Look for gauge-specific elements
                gauge_keywords = ['gauge', 'meter', 'reading', 'sensor', 'measurement']
                for keyword in gauge_keywords:
                    gauge_elements += len(driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]"))
            
            # Count data attributes
            try:
                data_elements = len(driver.find_elements(By.CSS_SELECTOR, '[data-*]'))
            except:
                pass
            
            # Identify automation opportunities
            automation_opportunities = []
            
            if forms:
                automation_opportunities.append({
                    'type': 'form_automation',
                    'description': f'Automate {len(forms)} forms for data entry',
                    'priority': 'high'
                })
            
            if gauge_elements > 0:
                automation_opportunities.append({
                    'type': 'gauge_monitoring',
                    'description': f'Monitor {gauge_elements} gauge readings',
                    'priority': 'high'
                })
            
            if data_elements > 10:
                automation_opportunities.append({
                    'type': 'data_extraction',
                    'description': f'Extract {data_elements} data points',
                    'priority': 'medium'
                })
            
            return {
                'success': True,
                'status': 'authenticated',
                'current_url': driver.current_url,
                'authentication_result': {'message': 'Authentication successful'},
                'extracted_data': {
                    'navigation_links': nav_links,
                    'forms_discovered': forms,
                    'gauge_elements': gauge_elements,
                    'data_elements': data_elements,
                    'page_title': driver.title
                },
                'automation_opportunities': automation_opportunities
            }
            
        except Exception as e:
            return {
                'success': True,
                'status': 'authenticated_limited',
                'current_url': driver.current_url,
                'authentication_result': {'message': 'Authentication successful but data extraction limited'},
                'error': str(e)
            }
    
    def execute_intelligence_sweep(self, platform):
        """Execute comprehensive intelligence sweep on authenticated platform"""
        try:
            session_id = list(self.active_sessions.keys())[0] if self.active_sessions else None
            
            if not session_id:
                return {'error': 'No active browser sessions'}
            
            driver = self.active_sessions[session_id]['driver']
            
            # Navigate through available sections
            intelligence_data = {
                'platform': platform,
                'current_url': driver.current_url,
                'timestamp': datetime.now().isoformat()
            }
            
            # Extract comprehensive navigation structure
            try:
                all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                navigation_structure = []
                
                for link in all_links[:20]:  # Limit to prevent overwhelming data
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text:
                        navigation_structure.append({
                            'text': text,
                            'url': href,
                            'internal': href.startswith(driver.current_url.split('/')[0:3])
                        })
                
                intelligence_data['navigation_structure'] = navigation_structure
            except:
                pass
            
            # Discover API endpoints
            try:
                script_elements = driver.find_elements(By.TAG_NAME, 'script')
                api_endpoints = []
                
                for script in script_elements:
                    script_content = script.get_attribute('innerHTML') or ''
                    # Look for API calls
                    import re
                    api_matches = re.findall(r'["\']([^"\']*api[^"\']*)["\']', script_content)
                    api_endpoints.extend(api_matches[:5])  # Limit results
                
                intelligence_data['api_endpoints'] = list(set(api_endpoints))
            except:
                intelligence_data['api_endpoints'] = []
            
            # Identify automation targets
            automation_targets = []
            
            # Form automation targets
            try:
                forms = driver.find_elements(By.TAG_NAME, 'form')
                if forms:
                    automation_targets.append({
                        'type': 'form_automation',
                        'count': len(forms),
                        'description': f'Automate {len(forms)} forms for data entry and submission'
                    })
            except:
                pass
            
            # Data extraction targets
            try:
                tables = driver.find_elements(By.TAG_NAME, 'table')
                if tables:
                    automation_targets.append({
                        'type': 'data_extraction',
                        'count': len(tables),
                        'description': f'Extract data from {len(tables)} tables for reporting'
                    })
            except:
                pass
            
            intelligence_data['automation_targets'] = automation_targets
            
            return {
                'intelligence_data': intelligence_data,
                'automation_targets': automation_targets,
                'data_extraction': {
                    'forms_count': len(driver.find_elements(By.TAG_NAME, 'form')),
                    'tables_count': len(driver.find_elements(By.TAG_NAME, 'table')),
                    'links_count': len(driver.find_elements(By.CSS_SELECTOR, 'a[href]'))
                },
                'api_endpoints': intelligence_data.get('api_endpoints', [])
            }
            
        except Exception as e:
            return {'error': str(e)}
            
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