#!/usr/bin/env python3
"""
TRAXOVO Final QA - Selenium Headless Browser Interaction Test
Comprehensive testing of all clickable elements and navigation paths
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TRAXOVOQATest:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {
            'total_elements': 0,
            'successful_clicks': 0,
            'failed_clicks': 0,
            'errors': [],
            'routes_tested': [],
            'performance_metrics': {}
        }
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("✅ Chrome headless driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return False
    
    def login_to_system(self):
        """Authenticate with watson/watson credentials"""
        try:
            logger.info("🔐 Attempting login to TRAXOVO system...")
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            
            # Fill credentials
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys("watson")
            password_field.send_keys("watson")
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            
            # Wait for redirect to dashboard
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/dashboard")
            )
            
            logger.info("✅ Successfully logged into TRAXOVO system")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            self.test_results['errors'].append(f"Login failure: {e}")
            return False
    
    def test_clickable_elements(self):
        """Test all clickable elements on current page"""
        try:
            # Get all clickable elements
            clickable_selectors = [
                "a[href]",
                "button",
                "[onclick]",
                "[role='button']",
                ".btn",
                ".nav-link",
                ".metric-card",
                ".sidebar a"
            ]
            
            all_elements = []
            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_elements.extend(elements)
                except:
                    continue
            
            # Remove duplicates
            unique_elements = list(set(all_elements))
            self.test_results['total_elements'] += len(unique_elements)
            
            logger.info(f"🎯 Found {len(unique_elements)} clickable elements to test")
            
            for i, element in enumerate(unique_elements):
                try:
                    # Skip if element is not visible or disabled
                    if not element.is_displayed() or not element.is_enabled():
                        continue
                    
                    # Get element info
                    tag_name = element.tag_name
                    text = element.text[:50] if element.text else "No text"
                    href = element.get_attribute('href') if tag_name == 'a' else None
                    
                    logger.info(f"🖱️  Testing element {i+1}/{len(unique_elements)}: {tag_name} - {text}")
                    
                    # Record current URL before click
                    current_url = self.driver.current_url
                    
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                    
                    # Click element
                    element.click()
                    time.sleep(2)  # Wait for potential navigation/modal
                    
                    # Check if URL changed (navigation occurred)
                    new_url = self.driver.current_url
                    if new_url != current_url:
                        self.test_results['routes_tested'].append(new_url)
                        logger.info(f"✅ Navigation successful: {new_url}")
                        
                        # Go back to continue testing
                        self.driver.back()
                        time.sleep(2)
                    
                    self.test_results['successful_clicks'] += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️  Element click failed: {e}")
                    self.test_results['failed_clicks'] += 1
                    self.test_results['errors'].append(f"Click failure on {tag_name}: {e}")
                    
                    # Try to recover by going back to main page
                    try:
                        self.driver.get(f"{self.base_url}/dashboard")
                        time.sleep(2)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"❌ Critical error in element testing: {e}")
            self.test_results['errors'].append(f"Critical testing error: {e}")
    
    def test_navigation_routes(self):
        """Test major navigation routes"""
        routes_to_test = [
            "/dashboard",
            "/fleet-map", 
            "/attendance-matrix",
            "/asset-manager",
            "/billing",
            "/executive-reports",
            "/ai-assistant",
            "/industry-news"
        ]
        
        for route in routes_to_test:
            try:
                logger.info(f"🗺️  Testing route: {route}")
                start_time = time.time()
                
                self.driver.get(f"{self.base_url}{route}")
                
                # Wait for page to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                load_time = time.time() - start_time
                self.test_results['performance_metrics'][route] = load_time
                
                # Check for error indicators
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert-danger, [class*='error']")
                if error_elements:
                    logger.warning(f"⚠️  Error elements found on {route}")
                
                # Test clickable elements on this page
                self.test_clickable_elements()
                
                logger.info(f"✅ Route {route} tested successfully (load time: {load_time:.2f}s)")
                
            except TimeoutException:
                logger.error(f"❌ Route {route} timed out")
                self.test_results['errors'].append(f"Route timeout: {route}")
            except Exception as e:
                logger.error(f"❌ Route {route} failed: {e}")
                self.test_results['errors'].append(f"Route error {route}: {e}")
    
    def run_comprehensive_test(self):
        """Run the complete QA test suite"""
        logger.info("🚀 Starting TRAXOVO Comprehensive QA Test Suite")
        
        if not self.setup_driver():
            return False
        
        try:
            # Step 1: Login
            if not self.login_to_system():
                return False
            
            # Step 2: Test navigation routes
            self.test_navigation_routes()
            
            # Step 3: Generate report
            self.generate_test_report()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 TRAXOVO QA TEST RESULTS")
        logger.info("="*60)
        
        # Summary
        total_elements = self.test_results['total_elements']
        successful = self.test_results['successful_clicks']
        failed = self.test_results['failed_clicks']
        success_rate = (successful / total_elements * 100) if total_elements > 0 else 0
        
        logger.info(f"Total Elements Tested: {total_elements}")
        logger.info(f"Successful Interactions: {successful}")
        logger.info(f"Failed Interactions: {failed}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        # Routes tested
        logger.info(f"\nRoutes Successfully Tested: {len(self.test_results['routes_tested'])}")
        for route in set(self.test_results['routes_tested']):
            logger.info(f"  ✅ {route}")
        
        # Performance metrics
        logger.info("\nPerformance Metrics:")
        for route, load_time in self.test_results['performance_metrics'].items():
            status = "🟢 Fast" if load_time < 3 else "🟡 Slow" if load_time < 6 else "🔴 Very Slow"
            logger.info(f"  {route}: {load_time:.2f}s {status}")
        
        # Errors
        if self.test_results['errors']:
            logger.info(f"\nErrors Encountered ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors'][:10]:  # Show first 10 errors
                logger.info(f"  ❌ {error}")
        else:
            logger.info("\n✅ No critical errors encountered!")
        
        # Overall assessment
        if success_rate > 90 and len(self.test_results['errors']) < 5:
            logger.info("\n🎉 OVERALL ASSESSMENT: EXCELLENT - Ready for deployment")
        elif success_rate > 75:
            logger.info("\n✅ OVERALL ASSESSMENT: GOOD - Minor issues to address")
        else:
            logger.info("\n⚠️  OVERALL ASSESSMENT: NEEDS IMPROVEMENT - Review errors")
        
        logger.info("="*60)

if __name__ == "__main__":
    tester = TRAXOVOQATest()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)