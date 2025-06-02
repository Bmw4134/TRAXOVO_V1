"""
ASI Testing Automation Engine
Headless browser automation for testing + web scraping capabilities
Frontend accessible with real-time status monitoring
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import trafilatura
import requests

class ASITestingEngine:
    """
    ASI-enhanced testing automation with web scraping
    Real-time status monitoring and frontend integration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.test_results = []
        self.scraping_results = []
        self.status = "idle"
        
    def _setup_browser(self):
        """Setup headless Chrome browser with ASI optimization"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("ASI browser automation initialized")
            return True
        except Exception as e:
            self.logger.error(f"Browser setup failed: {e}")
            return False
    
    def test_traxovo_routes(self, base_url: str = None) -> Dict[str, Any]:
        """Test all TRAXOVO routes with ASI intelligence"""
        self.status = "testing_routes"
        
        if not base_url:
            base_url = "https://f2699832-8135-4557-9ec0-8d4d723b9ba2-00-347mwnpgyu8te.janeway.replit.dev"
        
        if not self._setup_browser():
            return {"error": "Browser setup failed"}
        
        routes_to_test = [
            "/",
            "/dashboard", 
            "/chris-fleet",
            "/watson-confidence",
            "/asi-analyzer",
            "/security-dashboard",
            "/api/fleet_overview",
            "/api/watson_confidence_data"
        ]
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "routes_tested": len(routes_to_test),
            "results": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
        for route in routes_to_test:
            result = self._test_single_route(base_url, route)
            test_results["results"].append(result)
            
            if result["status"] == "pass":
                test_results["summary"]["passed"] += 1
            else:
                test_results["summary"]["failed"] += 1
                test_results["summary"]["errors"].append(f"{route}: {result.get('error', 'Unknown error')}")
        
        self._cleanup_browser()
        self.test_results.append(test_results)
        self.status = "completed"
        
        return test_results
    
    def _test_single_route(self, base_url: str, route: str) -> Dict[str, Any]:
        """Test individual route with ASI analysis"""
        start_time = time.time()
        url = f"{base_url}{route}"
        
        try:
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # ASI analysis of page content
            page_title = self.driver.title
            page_source = self.driver.page_source
            
            # Check for errors
            error_indicators = ["error", "404", "500", "not found", "exception"]
            has_errors = any(indicator.lower() in page_source.lower() for indicator in error_indicators)
            
            # Check for TRAXOVO branding
            has_branding = "TRAXOVO" in page_source or "Fleet" in page_source
            
            # Check for interactive elements
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            return {
                "route": route,
                "url": url,
                "status": "fail" if has_errors else "pass",
                "response_time_ms": response_time,
                "page_title": page_title,
                "has_branding": has_branding,
                "interactive_elements": {
                    "buttons": len(buttons),
                    "forms": len(forms)
                },
                "page_size_kb": round(len(page_source) / 1024, 2),
                "timestamp": datetime.now().isoformat()
            }
            
        except TimeoutException:
            return {
                "route": route,
                "url": url,
                "status": "fail",
                "error": "Timeout loading page",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "route": route,
                "url": url,
                "status": "fail",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
                "timestamp": datetime.now().isoformat()
            }
    
    def scrape_website(self, url: str, extract_data: List[str] = None) -> Dict[str, Any]:
        """ASI-enhanced web scraping with intelligent data extraction"""
        self.status = "scraping"
        
        if not extract_data:
            extract_data = ["text", "links", "images", "tables"]
        
        try:
            # Use trafilatura for clean text extraction
            downloaded = trafilatura.fetch_url(url)
            clean_text = trafilatura.extract(downloaded) if downloaded else None
            
            # Use browser for structured data
            if not self._setup_browser():
                return {"error": "Browser setup failed"}
            
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            scraped_data = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "page_title": self.driver.title,
                "clean_text": clean_text[:2000] if clean_text else None,  # Limit for storage
                "extracted_data": {}
            }
            
            # Extract specific data types
            if "links" in extract_data:
                links = [link.get_attribute("href") for link in self.driver.find_elements(By.TAG_NAME, "a") if link.get_attribute("href")]
                scraped_data["extracted_data"]["links"] = links[:50]  # Limit results
            
            if "images" in extract_data:
                images = [img.get_attribute("src") for img in self.driver.find_elements(By.TAG_NAME, "img") if img.get_attribute("src")]
                scraped_data["extracted_data"]["images"] = images[:20]
            
            if "tables" in extract_data:
                tables = []
                for table in self.driver.find_elements(By.TAG_NAME, "table")[:5]:  # Limit to 5 tables
                    rows = []
                    for row in table.find_elements(By.TAG_NAME, "tr")[:10]:  # Limit rows
                        cells = [cell.text.strip() for cell in row.find_elements(By.TAG_NAME, "td")]
                        if cells:
                            rows.append(cells)
                    if rows:
                        tables.append(rows)
                scraped_data["extracted_data"]["tables"] = tables
            
            self._cleanup_browser()
            self.scraping_results.append(scraped_data)
            self.status = "completed"
            
            return scraped_data
            
        except Exception as e:
            self.logger.error(f"Scraping failed for {url}: {e}")
            self._cleanup_browser()
            return {
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_video_upload_functionality(self, base_url: str = None) -> Dict[str, Any]:
        """Test video upload functionality with ASI validation"""
        self.status = "testing_upload"
        
        if not base_url:
            base_url = "https://f2699832-8135-4557-9ec0-8d4d723b9ba2-00-347mwnpgyu8te.janeway.replit.dev"
        
        if not self._setup_browser():
            return {"error": "Browser setup failed"}
        
        try:
            # Navigate to ASI analyzer page
            self.driver.get(f"{base_url}/asi-analyzer")
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check for upload elements
            upload_elements = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            upload_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "page_loaded": True,
                "upload_elements_found": len(upload_elements),
                "buttons_found": len(upload_buttons),
                "asi_analyzer_functional": "asi-analyzer" in self.driver.current_url.lower(),
                "status": "pass" if upload_elements else "fail"
            }
            
            if not upload_elements:
                result["error"] = "No file upload elements found"
            
            self._cleanup_browser()
            return result
            
        except Exception as e:
            self._cleanup_browser()
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "fail",
                "error": str(e)
            }
    
    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time testing status for frontend"""
        return {
            "current_status": self.status,
            "last_test_count": len(self.test_results),
            "last_scrape_count": len(self.scraping_results),
            "timestamp": datetime.now().isoformat(),
            "capabilities": [
                "Route Testing",
                "Web Scraping", 
                "Upload Testing",
                "Real-time Monitoring"
            ]
        }
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get latest test and scraping results"""
        return {
            "latest_test": self.test_results[-1] if self.test_results else None,
            "latest_scrape": self.scraping_results[-1] if self.scraping_results else None,
            "total_tests": len(self.test_results),
            "total_scrapes": len(self.scraping_results)
        }
    
    def _cleanup_browser(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            self.logger.error(f"Browser cleanup error: {e}")

# Global instance
_asi_testing_engine = None

def get_asi_testing_engine():
    """Get ASI testing engine instance"""
    global _asi_testing_engine
    if _asi_testing_engine is None:
        _asi_testing_engine = ASITestingEngine()
    return _asi_testing_engine

# Flask route integration functions
def run_full_traxovo_test():
    """Run comprehensive TRAXOVO testing"""
    engine = get_asi_testing_engine()
    return engine.test_traxovo_routes()

def scrape_competitor_data(url: str):
    """Scrape competitor or industry data"""
    engine = get_asi_testing_engine()
    return engine.scrape_website(url, ["text", "links", "tables"])

def validate_upload_system():
    """Validate video upload functionality"""
    engine = get_asi_testing_engine()
    return engine.test_video_upload_functionality()