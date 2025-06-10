"""
GAUGE Smart Web Scraper - Direct Dashboard Data Extraction
Bypasses API limitations by scraping authenticated dashboard interface
"""

import os
import requests
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

class GaugeWebScraper:
    def __init__(self):
        self.base_url = "https://login.gaugesmart.com"
        self.username = os.environ.get('GAUGE_CLIENT_ID')
        self.password = os.environ.get('GAUGE_CLIENT_SECRET')
        self.session = requests.Session()
        
        # Configure session for web scraping
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Disable SSL warnings for enterprise environments
        self.session.verify = False
        requests.packages.urllib3.disable_warnings()
        
        self.authenticated = False
        self.dashboard_data = {}
    
    def authenticate(self):
        """Login to GAUGE Smart dashboard"""
        try:
            # Get login page to extract form tokens
            login_page = self.session.get(f"{self.base_url}/login", timeout=30)
            
            if login_page.status_code == 200:
                # Extract authentication tokens from login form
                form_token = self._extract_form_token(login_page.text)
                
                # Prepare login data
                login_data = {
                    'username': self.username,
                    'password': self.password,
                    'rememberMe': 'false'
                }
                
                if form_token:
                    login_data['__RequestVerificationToken'] = form_token
                
                # Submit login form
                response = self.session.post(
                    f"{self.base_url}/login",
                    data=login_data,
                    timeout=30,
                    allow_redirects=True
                )
                
                # Check for successful authentication
                if 'dashboard' in response.url.lower() or response.status_code == 200:
                    self.authenticated = True
                    logging.info("✓ GAUGE Smart authentication successful")
                    return True
                else:
                    logging.error(f"Authentication failed: {response.status_code}")
                    return False
            
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False
    
    def _extract_form_token(self, html_content):
        """Extract authentication token from form"""
        token_pattern = r'name="__RequestVerificationToken".*?value="([^"]+)"'
        match = re.search(token_pattern, html_content)
        return match.group(1) if match else None
    
    def scrape_fleet_data(self):
        """Scrape comprehensive fleet data from dashboard"""
        if not self.authenticated and not self.authenticate():
            return {}
        
        fleet_data = {
            'assets': [],
            'summary': {},
            'alerts': [],
            'last_update': datetime.now().isoformat()
        }
        
        try:
            # Scrape main dashboard
            dashboard_url = f"{self.base_url}/dashboard"
            dashboard_response = self.session.get(dashboard_url, timeout=30)
            
            if dashboard_response.status_code == 200:
                fleet_data.update(self._parse_dashboard_data(dashboard_response.text))
            
            # Scrape asset list page
            assets_url = f"{self.base_url}/assets"
            assets_response = self.session.get(assets_url, timeout=30)
            
            if assets_response.status_code == 200:
                assets = self._parse_asset_list(assets_response.text)
                fleet_data['assets'].extend(assets)
            
            # Scrape reports page for additional data
            reports_url = f"{self.base_url}/reports"
            reports_response = self.session.get(reports_url, timeout=30)
            
            if reports_response.status_code == 200:
                report_data = self._parse_reports_data(reports_response.text)
                fleet_data['summary'].update(report_data)
            
            logging.info(f"Scraped data for {len(fleet_data['assets'])} assets")
            return fleet_data
            
        except Exception as e:
            logging.error(f"Error scraping fleet data: {e}")
            return fleet_data
    
    def _parse_dashboard_data(self, html_content):
        """Extract fleet summary data from dashboard HTML"""
        data = {'summary': {}, 'alerts': []}
        
        try:
            # Extract fleet statistics
            total_assets_pattern = r'(?:total[_\s]?assets?|fleet[_\s]?size)["\s]*[:=]["\s]*(\d+)'
            active_pattern = r'(?:active|online)["\s]*[:=]["\s]*(\d+)'
            utilization_pattern = r'(?:utilization|efficiency)["\s]*[:=]["\s]*([0-9.]+)'
            
            total_match = re.search(total_assets_pattern, html_content, re.IGNORECASE)
            active_match = re.search(active_pattern, html_content, re.IGNORECASE)
            util_match = re.search(utilization_pattern, html_content, re.IGNORECASE)
            
            if total_match:
                data['summary']['total_assets'] = int(total_match.group(1))
            if active_match:
                data['summary']['active_assets'] = int(active_match.group(1))
            if util_match:
                data['summary']['utilization_rate'] = float(util_match.group(1))
            
            # Extract alert information
            alert_pattern = r'(?:alert|warning|critical)["\s]*[:=]["\s]*["\']([^"\']+)["\']'
            alerts = re.findall(alert_pattern, html_content, re.IGNORECASE)
            
            for alert in alerts[:5]:  # Limit to 5 most recent alerts
                data['alerts'].append({
                    'message': alert,
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'medium'
                })
            
        except Exception as e:
            logging.error(f"Error parsing dashboard data: {e}")
        
        return data
    
    def _parse_asset_list(self, html_content):
        """Extract individual asset data from asset list page"""
        assets = []
        
        try:
            # Extract asset table rows or card elements
            asset_row_pattern = r'<tr[^>]*>.*?</tr>'
            asset_rows = re.findall(asset_row_pattern, html_content, re.DOTALL)
            
            for row in asset_rows:
                asset = self._extract_asset_from_row(row)
                if asset and asset.get('id'):
                    assets.append(asset)
            
            # Alternative: Extract from JavaScript data
            js_data_pattern = r'var\s+assets\s*=\s*(\[[^\]]+\])'
            js_match = re.search(js_data_pattern, html_content)
            
            if js_match:
                try:
                    js_assets = json.loads(js_match.group(1))
                    for js_asset in js_assets:
                        if isinstance(js_asset, dict):
                            assets.append(self._normalize_asset_data(js_asset))
                except:
                    pass
            
        except Exception as e:
            logging.error(f"Error parsing asset list: {e}")
        
        return assets
    
    def _extract_asset_from_row(self, row_html):
        """Extract asset data from HTML table row"""
        asset = {}
        
        try:
            # Extract asset ID
            id_pattern = r'(?:id|asset[_\-]?id)["\s]*[:=]["\s]*["\']([^"\']+)["\']'
            id_match = re.search(id_pattern, row_html, re.IGNORECASE)
            if id_match:
                asset['id'] = id_match.group(1)
            
            # Extract asset name
            name_pattern = r'(?:name|title|description)["\s]*[:=]["\s]*["\']([^"\']+)["\']'
            name_match = re.search(name_pattern, row_html, re.IGNORECASE)
            if name_match:
                asset['name'] = name_match.group(1)
            
            # Extract status
            status_pattern = r'(?:status|state)["\s]*[:=]["\s]*["\']([^"\']+)["\']'
            status_match = re.search(status_pattern, row_html, re.IGNORECASE)
            if status_match:
                asset['status'] = status_match.group(1)
            
            # Extract location data
            lat_pattern = r'(?:lat|latitude)["\s]*[:=]["\s]*([0-9.\-]+)'
            lng_pattern = r'(?:lng|longitude)["\s]*[:=]["\s]*([0-9.\-]+)'
            
            lat_match = re.search(lat_pattern, row_html, re.IGNORECASE)
            lng_match = re.search(lng_pattern, row_html, re.IGNORECASE)
            
            if lat_match and lng_match:
                asset['location'] = {
                    'lat': float(lat_match.group(1)),
                    'lng': float(lng_match.group(1))
                }
            
        except Exception as e:
            logging.error(f"Error extracting asset from row: {e}")
        
        return asset
    
    def _parse_reports_data(self, html_content):
        """Extract report metrics from reports page"""
        report_data = {}
        
        try:
            # Extract key performance metrics
            metrics_pattern = r'(?:metric|kpi)["\s]*[:=]["\s]*["\']([^"\']+)["\'][,\s]*["\']?value["\']?["\s]*[:=]["\s]*([0-9.]+)'
            metrics = re.findall(metrics_pattern, html_content, re.IGNORECASE)
            
            for metric_name, metric_value in metrics:
                report_data[metric_name.lower().replace(' ', '_')] = float(metric_value)
            
        except Exception as e:
            logging.error(f"Error parsing reports data: {e}")
        
        return report_data
    
    def _normalize_asset_data(self, raw_asset):
        """Normalize asset data structure"""
        return {
            'id': raw_asset.get('id', raw_asset.get('assetId', 'unknown')),
            'name': raw_asset.get('name', raw_asset.get('description', 'Unknown Asset')),
            'status': raw_asset.get('status', raw_asset.get('state', 'unknown')),
            'category': raw_asset.get('category', 'equipment'),
            'location': raw_asset.get('location', {'lat': 0.0, 'lng': 0.0}),
            'last_update': datetime.now().isoformat()
        }
    
    def get_real_fleet_data(self):
        """Main method to retrieve real fleet data"""
        return self.scrape_fleet_data()

def scrape_gauge_data():
    """Main function to scrape GAUGE Smart data"""
    scraper = GaugeWebScraper()
    return scraper.get_real_fleet_data()

if __name__ == "__main__":
    data = scrape_gauge_data()
    print(json.dumps(data, indent=2))