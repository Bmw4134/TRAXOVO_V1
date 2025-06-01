"""
TRAXOVO Automated Testing Suite
Comprehensive headless browser testing for all modules and functionality
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service


class TRAXOVOTestSuite:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'modules_tested': [],
            'performance_metrics': {},
            'errors': [],
            'success_rate': 0
        }

    def setup_driver(self):
        """Setup headless Chrome driver with optimal settings"""
        # Setup Chrome driver with headless options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location = '/usr/bin/chromium-browser'

        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)
        print("✓ Headless browser initialized")

    def login(self):
        """Authenticate with watson/watson credentials"""
        try:
            self.driver.get(f"{self.base_url}/login")

            # Wait for login form
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")

            username_field.send_keys("watson")
            password_field.send_keys("watson")

            # Submit login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            login_button.click()

            # Wait for redirect to dashboard
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/dashboard")
            )
            print("✓ Successfully logged in")
            return True

        except Exception as e:
            self.test_results['errors'].append(f"Login failed: {str(e)}")
            return False

    def test_module(self, module_name, url_path, expected_elements=None):
        """Test individual module functionality"""
        start_time = time.time()
        module_result = {
            'name': module_name,
            'url': url_path,
            'load_time': 0,
            'elements_found': [],
            'errors': [],
            'status': 'failed'
        }

        try:
            # Navigate to module
            self.driver.get(f"{self.base_url}{url_path}")

            # Wait for page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            load_time = time.time() - start_time
            module_result['load_time'] = round(load_time, 2)

            # Check for expected elements
            if expected_elements:
                for element_selector in expected_elements:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
                        if element.is_displayed():
                            module_result['elements_found'].append(element_selector)
                    except NoSuchElementException:
                        module_result['errors'].append(f"Element not found: {element_selector}")

            # Check for JavaScript errors in console
            logs = self.driver.get_log('browser')
            js_errors = [log for log in logs if log['level'] == 'SEVERE']
            if js_errors:
                module_result['errors'].extend([log['message'] for log in js_errors])

            # Test authentic data loading
            self.test_data_loading(module_result)

            module_result['status'] = 'success' if not module_result['errors'] else 'partial'
            print(f"✓ {module_name}: {load_time:.2f}s")

        except TimeoutException:
            module_result['errors'].append("Page load timeout")
            print(f"✗ {module_name}: Timeout")
        except Exception as e:
            module_result['errors'].append(str(e))
            print(f"✗ {module_name}: {str(e)}")

        self.test_results['modules_tested'].append(module_result)
        return module_result

    def test_data_loading(self, module_result):
        """Test authentic data loading in modules"""
        # Check for GAUGE data indicators
        gauge_indicators = [
            "[data-gauge-asset]",
            ".asset-count",
            ".fleet-total",
            "#total-assets",
            "#active-assets"
        ]

        for indicator in gauge_indicators:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                if element.text and element.text != "0":
                    module_result['elements_found'].append(f"Data loaded: {indicator}")
            except NoSuchElementException:
                continue

    def test_api_endpoints(self):
        """Test critical API endpoints"""
        api_tests = [
            ("/api/fleet/assets", "Fleet Assets API"),
            ("/api/performance/metrics", "Performance Metrics API"),
            ("/api/revenue/data", "Revenue Data API")
        ]

        for endpoint, name in api_tests:
            try:
                self.driver.get(f"{self.base_url}{endpoint}")

                # Check if JSON response is valid
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                if body_text.startswith('{') or body_text.startswith('['):
                    try:
                        json.loads(body_text)
                        print(f"✓ {name}: Valid JSON response")
                    except json.JSONDecodeError:
                        self.test_results['errors'].append(f"{name}: Invalid JSON")
                else:
                    self.test_results['errors'].append(f"{name}: Non-JSON response")

            except Exception as e:
                self.test_results['errors'].append(f"{name}: {str(e)}")

    def run_comprehensive_test(self):
        """Run complete test suite on all TRAXOVO modules"""
        try:
            self.setup_driver()

            if not self.login():
                return self.test_results

            # Define all modules to test
            modules_to_test = [
                ("Dashboard", "/dashboard", [".stat-card", ".module-card"]),
                ("Fleet Map", "/fleet-map", [".asset-map", ".map-container"]),
                ("Asset Manager", "/asset-manager", [".asset-list", ".equipment-grid"]),
                ("Driver Attendance", "/attendance-matrix", [".attendance-table", ".driver-metrics"]),
                ("Billing Intelligence", "/billing", [".billing-summary", ".revenue-chart"]),
                ("Equipment Billing", "/equipment-billing", [".billing-table", ".equipment-rates"]),
                ("Executive Reports", "/executive-reports", [".report-container", ".executive-summary"]),
                ("Automated Workflows", "/automated-workflows", [".workflow-status", ".automation-controls"]),
                ("AI Assistant", "/ai-assistant", [".chat-interface", ".ai-responses"]),
                ("Fleet Analytics", "/fleet-analytics", [".analytics-dashboard", ".metrics-grid"]),
                ("Performance Metrics", "/performance-metrics", [".performance-chart", ".kpi-cards"]),
                ("Project Accountability", "/project-accountability", [".project-list", ".job-sites"]),
                ("System Admin", "/system-admin", [".admin-modules", ".system-status"]),
                ("System Health", "/system-health", [".health-indicators", ".status-grid"]),
                ("Kaizen Optimization", "/kaizen", [".optimization-dashboard", ".improvement-suggestions"])
            ]

            print(f"\n🚀 Starting comprehensive test of {len(modules_to_test)} modules...")

            # Test each module
            for module_name, url_path, expected_elements in modules_to_test:
                self.test_module(module_name, url_path, expected_elements)
                time.sleep(1)  # Brief pause between tests

            # Test API endpoints
            print("\n🔍 Testing API endpoints...")
            self.test_api_endpoints()

            # Calculate success rate
            successful_modules = len([m for m in self.test_results['modules_tested'] if m['status'] == 'success'])
            total_modules = len(self.test_results['modules_tested'])
            self.test_results['success_rate'] = (successful_modules / total_modules) * 100 if total_modules > 0 else 0

            # Performance summary
            load_times = [m['load_time'] for m in self.test_results['modules_tested']]
            self.test_results['performance_metrics'] = {
                'average_load_time': round(sum(load_times) / len(load_times), 2) if load_times else 0,
                'slowest_module': max(self.test_results['modules_tested'], key=lambda x: x['load_time'])['name'] if load_times else None,
                'fastest_module': min(self.test_results['modules_tested'], key=lambda x: x['load_time'])['name'] if load_times else None
            }

        except Exception as e:
            self.test_results['errors'].append(f"Test suite error: {str(e)}")

        finally:
            if self.driver:
                self.driver.quit()

        return self.test_results

    def generate_report(self):
        """Generate comprehensive test report"""
        results = self.run_comprehensive_test()

        print("\n" + "="*60)
        print("TRAXOVO AUTOMATED TEST RESULTS")
        print("="*60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Modules Tested: {len(results['modules_tested'])}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Average Load Time: {results['performance_metrics'].get('average_load_time', 0)}s")

        if results['performance_metrics'].get('slowest_module'):
            print(f"Slowest Module: {results['performance_metrics']['slowest_module']}")

        print("\n📊 MODULE STATUS:")
        for module in results['modules_tested']:
            status_icon = "✓" if module['status'] == 'success' else "⚠" if module['status'] == 'partial' else "✗"
            print(f"{status_icon} {module['name']}: {module['load_time']}s ({module['status']})")

            if module['errors']:
                for error in module['errors'][:2]:  # Show first 2 errors
                    print(f"    └─ {error}")

        if results['errors']:
            print(f"\n🚨 CRITICAL ERRORS ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  • {error}")

        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Detailed results saved to: test_results.json")
        return results

def run_automated_tests():
    """Main function to run automated tests"""
    tester = TRAXOVOTestSuite()
    return tester.generate_report()

if __name__ == "__main__":
    run_automated_tests()