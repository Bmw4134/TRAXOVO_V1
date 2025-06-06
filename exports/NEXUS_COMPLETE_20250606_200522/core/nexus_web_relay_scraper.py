"""
NEXUS Web Relay Scraper
Autonomous web scraping with headless prompt injection and DOM parsing
"""

import os
import json
import time
import asyncio
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ScanResult:
    ticker: str
    price: float
    volume: str
    price_change: str
    momentum_signal: str
    source: str
    timestamp: str
    confidence: int
    alert_type: str

class NexusWebRelayScraper:
    """NEXUS-powered autonomous web scraper with prompt injection"""
    
    def __init__(self):
        self.driver = None
        self.target_sites = {
            'tradingview': 'https://www.tradingview.com/chart/',
            'finviz': 'https://finviz.com/screener.ashx',
            'yahoo_finance': 'https://finance.yahoo.com/screener/predefined/growth_technology_stocks',
            'investing_com': 'https://www.investing.com/equities/screener'
        }
        self.scan_results = []
        self.last_scan_data = {}
        self.is_scanning = False
        self.scan_interval = 5  # 5 seconds
        self.logs_directory = "trading/logs"
        os.makedirs(self.logs_directory, exist_ok=True)
        
    def initialize_driver(self):
        """Initialize headless Chrome driver with NEXUS configurations"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logging.info("[NEXUS SCRAPER] Headless browser initialized")
            return True
        except Exception as e:
            logging.error(f"[NEXUS SCRAPER] Failed to initialize driver: {e}")
            return False
    
    def inject_nexus_prompt(self, site_name: str) -> str:
        """Inject NEXUS intelligence prompts into trading pages"""
        
        nexus_prompts = {
            'tradingview': """
                // NEXUS Web Relay Injection
                function extractTradingViewData() {
                    const data = {};
                    
                    // Extract ticker from title or symbol display
                    const titleElement = document.querySelector('title');
                    if (titleElement) {
                        const title = titleElement.textContent;
                        const tickerMatch = title.match(/([A-Z]{1,5})/);
                        data.ticker = tickerMatch ? tickerMatch[1] : 'UNKNOWN';
                    }
                    
                    // Extract price data
                    const priceElements = document.querySelectorAll('[class*="price"], [class*="last"], [data-name="legend-source-item"]');
                    priceElements.forEach(el => {
                        const text = el.textContent;
                        if (text.match(/^\$?[\d,]+\.?\d*$/)) {
                            data.price = parseFloat(text.replace(/[$,]/g, ''));
                        }
                    });
                    
                    // Extract volume data
                    const volumeElements = document.querySelectorAll('[class*="volume"], [data-name*="volume"]');
                    volumeElements.forEach(el => {
                        const text = el.textContent;
                        if (text.match(/[\d.]+[KMB]?/)) {
                            data.volume = text;
                        }
                    });
                    
                    // Extract momentum indicators
                    const indicators = document.querySelectorAll('[class*="indicator"], [class*="signal"]');
                    let bullishSignals = 0;
                    let bearishSignals = 0;
                    
                    indicators.forEach(el => {
                        const text = el.textContent.toLowerCase();
                        if (text.includes('buy') || text.includes('bull') || text.includes('strong')) bullishSignals++;
                        if (text.includes('sell') || text.includes('bear') || text.includes('weak')) bearishSignals++;
                    });
                    
                    data.momentum = bullishSignals > bearishSignals ? 'BULLISH' : 
                                   bearishSignals > bullishSignals ? 'BEARISH' : 'NEUTRAL';
                    
                    return data;
                }
                
                return extractTradingViewData();
            """,
            
            'finviz': """
                // NEXUS Finviz Scraper
                function extractFinvizData() {
                    const results = [];
                    const rows = document.querySelectorAll('table[bgcolor="#d3d3d3"] tr');
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 12) {
                            const ticker = cells[1]?.textContent?.trim();
                            const price = cells[8]?.textContent?.trim();
                            const change = cells[9]?.textContent?.trim();
                            const volume = cells[11]?.textContent?.trim();
                            
                            if (ticker && ticker.match(/^[A-Z]{1,5}$/)) {
                                results.push({
                                    ticker: ticker,
                                    price: parseFloat(price) || 0,
                                    change: change || '0%',
                                    volume: volume || '0',
                                    momentum: change?.includes('+') ? 'BULLISH' : 'BEARISH'
                                });
                            }
                        }
                    });
                    
                    return results.slice(0, 10); // Top 10 results
                }
                
                return extractFinvizData();
            """,
            
            'yahoo_finance': """
                // NEXUS Yahoo Finance Scraper
                function extractYahooData() {
                    const results = [];
                    const rows = document.querySelectorAll('table tbody tr');
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 6) {
                            const ticker = cells[0]?.textContent?.trim();
                            const price = cells[2]?.textContent?.trim();
                            const change = cells[3]?.textContent?.trim();
                            const volume = cells[5]?.textContent?.trim();
                            
                            if (ticker) {
                                results.push({
                                    ticker: ticker,
                                    price: parseFloat(price?.replace(/,/g, '')) || 0,
                                    change: change || '0%',
                                    volume: volume || '0',
                                    momentum: change?.includes('+') ? 'BULLISH' : 'BEARISH'
                                });
                            }
                        }
                    });
                    
                    return results.slice(0, 10);
                }
                
                return extractYahooData();
            """
        }
        
        return nexus_prompts.get(site_name, "return {error: 'No NEXUS prompt for this site'};")
    
    async def scrape_site(self, site_name: str, url: str) -> List[ScanResult]:
        """Scrape a specific trading site with NEXUS prompt injection"""
        
        if not self.driver:
            if not self.initialize_driver():
                return []
        
        try:
            logging.info(f"[NEXUS SCRAPER] Scanning {site_name}: {url}")
            
            # Navigate to target site
            self.driver.get(url)
            
            # Wait for page load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Allow additional time for dynamic content
            time.sleep(3)
            
            # Inject NEXUS prompt and execute
            nexus_script = self.inject_nexus_prompt(site_name)
            raw_data = self.driver.execute_script(nexus_script)
            
            # Process extracted data
            scan_results = self.process_raw_data(raw_data, site_name)
            
            logging.info(f"[NEXUS SCRAPER] Extracted {len(scan_results)} results from {site_name}")
            return scan_results
            
        except TimeoutException:
            logging.error(f"[NEXUS SCRAPER] Timeout loading {site_name}")
            return []
        except Exception as e:
            logging.error(f"[NEXUS SCRAPER] Error scraping {site_name}: {e}")
            return []
    
    def process_raw_data(self, raw_data: any, source: str) -> List[ScanResult]:
        """Process raw scraped data into ScanResult objects"""
        
        results = []
        timestamp = datetime.now().isoformat()
        
        try:
            if isinstance(raw_data, list):
                # Multiple results (Finviz, Yahoo)
                for item in raw_data:
                    if isinstance(item, dict) and 'ticker' in item:
                        result = ScanResult(
                            ticker=item.get('ticker', 'UNKNOWN'),
                            price=float(item.get('price', 0)),
                            volume=str(item.get('volume', '0')),
                            price_change=str(item.get('change', '0%')),
                            momentum_signal=item.get('momentum', 'NEUTRAL'),
                            source=source,
                            timestamp=timestamp,
                            confidence=self.calculate_confidence(item),
                            alert_type=self.determine_alert_type(item)
                        )
                        results.append(result)
                        
            elif isinstance(raw_data, dict):
                # Single result (TradingView)
                if 'ticker' in raw_data:
                    result = ScanResult(
                        ticker=raw_data.get('ticker', 'UNKNOWN'),
                        price=float(raw_data.get('price', 0)),
                        volume=str(raw_data.get('volume', '0')),
                        price_change='0%',  # TradingView doesn't always provide change
                        momentum_signal=raw_data.get('momentum', 'NEUTRAL'),
                        source=source,
                        timestamp=timestamp,
                        confidence=self.calculate_confidence(raw_data),
                        alert_type=self.determine_alert_type(raw_data)
                    )
                    results.append(result)
                    
        except Exception as e:
            logging.error(f"[NEXUS SCRAPER] Error processing data from {source}: {e}")
        
        return results
    
    def calculate_confidence(self, data: Dict) -> int:
        """Calculate confidence score for scraped data"""
        confidence = 50  # Base confidence
        
        # Boost confidence based on data quality
        if data.get('price', 0) > 0:
            confidence += 20
        if data.get('volume') and data.get('volume') != '0':
            confidence += 15
        if data.get('momentum') in ['BULLISH', 'BEARISH']:
            confidence += 15
        
        return min(confidence, 100)
    
    def determine_alert_type(self, data: Dict) -> str:
        """Determine alert type based on scraped data"""
        momentum = data.get('momentum', 'NEUTRAL')
        price = data.get('price', 0)
        
        if momentum == 'BULLISH' and price > 0:
            return 'BUY_SIGNAL'
        elif momentum == 'BEARISH' and price > 0:
            return 'SELL_SIGNAL'
        else:
            return 'WATCH'
    
    def detect_deltas(self, new_results: List[ScanResult]) -> List[ScanResult]:
        """Detect changes from previous scan results"""
        
        deltas = []
        
        for new_result in new_results:
            ticker = new_result.ticker
            
            if ticker in self.last_scan_data:
                old_result = self.last_scan_data[ticker]
                
                # Check for significant price changes
                price_change = abs(new_result.price - old_result.price) / old_result.price if old_result.price > 0 else 0
                
                # Check for momentum changes
                momentum_changed = new_result.momentum_signal != old_result.momentum_signal
                
                if price_change > 0.01 or momentum_changed:  # 1% price change or momentum shift
                    deltas.append(new_result)
            else:
                # New ticker detected
                deltas.append(new_result)
        
        # Update last scan data
        self.last_scan_data = {result.ticker: result for result in new_results}
        
        return deltas
    
    def log_scan_results(self, results: List[ScanResult]):
        """Log scan results to /trading/logs/scan-results.json"""
        
        log_file = os.path.join(self.logs_directory, "scan-results.json")
        
        try:
            # Load existing logs
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new results
            for result in results:
                log_entry = {
                    'timestamp': result.timestamp,
                    'ticker': result.ticker,
                    'price': result.price,
                    'volume': result.volume,
                    'price_change': result.price_change,
                    'momentum_signal': result.momentum_signal,
                    'source': result.source,
                    'confidence': result.confidence,
                    'alert_type': result.alert_type
                }
                logs.append(log_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Save updated logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            logging.info(f"[NEXUS SCRAPER] Logged {len(results)} scan results")
            
        except Exception as e:
            logging.error(f"[NEXUS SCRAPER] Failed to log scan results: {e}")
    
    async def continuous_scan(self):
        """Run continuous scanning with delta detection"""
        
        self.is_scanning = True
        logging.info("[NEXUS SCRAPER] Starting continuous scan mode")
        
        while self.is_scanning:
            try:
                all_results = []
                
                # Scan each configured site
                for site_name, url in self.target_sites.items():
                    site_results = await self.scrape_site(site_name, url)
                    all_results.extend(site_results)
                    
                    # Brief pause between sites
                    await asyncio.sleep(1)
                
                # Detect deltas
                delta_results = self.detect_deltas(all_results)
                
                if delta_results:
                    logging.info(f"[NEXUS SCRAPER] Detected {len(delta_results)} changes")
                    
                    # Log delta results
                    self.log_scan_results(delta_results)
                    
                    # Update scan results for API access
                    self.scan_results = delta_results
                
                # Wait for next scan interval
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logging.error(f"[NEXUS SCRAPER] Error in continuous scan: {e}")
                await asyncio.sleep(self.scan_interval)
    
    def stop_scanning(self):
        """Stop continuous scanning"""
        self.is_scanning = False
        if self.driver:
            self.driver.quit()
            self.driver = None
        logging.info("[NEXUS SCRAPER] Scanning stopped")
    
    def get_recent_suggestions(self, limit: int = 20) -> List[Dict]:
        """Get recent scan results for suggestions feed"""
        
        log_file = os.path.join(self.logs_directory, "scan-results.json")
        
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                
                # Return most recent results
                recent_logs = logs[-limit:] if len(logs) > limit else logs
                return list(reversed(recent_logs))  # Most recent first
            
            return []
            
        except Exception as e:
            logging.error(f"[NEXUS SCRAPER] Error getting recent suggestions: {e}")
            return []
    
    def get_scan_status(self) -> Dict:
        """Get current scanning status"""
        return {
            'is_scanning': self.is_scanning,
            'scan_interval': self.scan_interval,
            'last_scan_count': len(self.scan_results),
            'total_sites': len(self.target_sites),
            'driver_active': self.driver is not None
        }

# Global scraper instance
nexus_scraper = NexusWebRelayScraper()

def start_nexus_scraping():
    """Start NEXUS web scraping in background"""
    asyncio.create_task(nexus_scraper.continuous_scan())
    return {"status": "NEXUS_SCRAPING_STARTED", "interval": nexus_scraper.scan_interval}

def stop_nexus_scraping():
    """Stop NEXUS web scraping"""
    nexus_scraper.stop_scanning()
    return {"status": "NEXUS_SCRAPING_STOPPED"}

def get_nexus_suggestions(limit: int = 20):
    """Get recent NEXUS scraping suggestions"""
    return nexus_scraper.get_recent_suggestions(limit)

def get_nexus_scraper_status():
    """Get NEXUS scraper status"""
    return nexus_scraper.get_scan_status()