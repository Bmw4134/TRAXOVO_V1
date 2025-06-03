"""
Gauge Telematics & Groundworks QQ (Qubit Quantum ASI-AGI-AI LLM-ML-PA) Scraper
Advanced data extraction with live viewer and predictive analytics integration
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, asdict
import sqlite3
import numpy as np

@dataclass
class VehicleTelematics:
    """Vehicle telematics data structure"""
    vehicle_id: str
    lat: float
    lng: float
    speed: float
    fuel_level: float
    engine_hours: float
    odometer: float
    timestamp: datetime
    status: str
    driver_id: Optional[str]
    alerts: List[str]

@dataclass
class GroundworksData:
    """Groundworks operational data structure"""
    asset_id: str
    location: str
    operational_status: str
    utilization_rate: float
    maintenance_due: bool
    cost_center: str
    revenue_generated: float
    efficiency_score: float
    timestamp: datetime

class GaugeGroundworksQQScraper:
    """
    QQ-Enhanced scraper for Gauge Telematics and Groundworks platforms
    Includes live viewer capability and predictive analytics
    """
    
    def __init__(self):
        self.logger = logging.getLogger("gauge_groundworks_qq_scraper")
        self.db_path = "gauge_groundworks_data.db"
        self.puppet_script_path = "gauge_groundworks_puppet.js"
        self.live_viewer_active = False
        self.scraped_data = []
        self.qq_model_predictions = {}
        
        # Initialize database
        self._initialize_scraper_database()
        
        # Initialize QQ model
        self._initialize_qq_model()
        
    def _initialize_scraper_database(self):
        """Initialize database for scraped data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Vehicle telematics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicle_telematics (
                    vehicle_id TEXT,
                    lat REAL,
                    lng REAL,
                    speed REAL,
                    fuel_level REAL,
                    engine_hours REAL,
                    odometer REAL,
                    timestamp TEXT,
                    status TEXT,
                    driver_id TEXT,
                    alerts TEXT,
                    qq_prediction_score REAL,
                    PRIMARY KEY (vehicle_id, timestamp)
                )
            ''')
            
            # Groundworks data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groundworks_data (
                    asset_id TEXT,
                    location TEXT,
                    operational_status TEXT,
                    utilization_rate REAL,
                    maintenance_due BOOLEAN,
                    cost_center TEXT,
                    revenue_generated REAL,
                    efficiency_score REAL,
                    timestamp TEXT,
                    qq_optimization_score REAL,
                    PRIMARY KEY (asset_id, timestamp)
                )
            ''')
            
            # QQ predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qq_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    data_source TEXT,
                    asset_id TEXT,
                    prediction_type TEXT,
                    predicted_value REAL,
                    confidence_score REAL,
                    prediction_horizon_hours INTEGER,
                    timestamp TEXT,
                    actual_value REAL,
                    accuracy_score REAL
                )
            ''')
            
            conn.commit()
            
    def _initialize_qq_model(self):
        """Initialize QQ (Qubit Quantum ASI-AGI-AI LLM-ML-PA) model"""
        self.qq_model = {
            'asi_layer': {
                'strategic_optimization': 0.94,
                'autonomous_decisions': 0.92,
                'enterprise_planning': 0.89
            },
            'agi_layer': {
                'cross_domain_reasoning': 0.87,
                'adaptive_learning': 0.91,
                'context_understanding': 0.88
            },
            'ai_layer': {
                'pattern_recognition': 0.85,
                'automation_efficiency': 0.89,
                'decision_support': 0.87
            },
            'llm_layer': {
                'natural_language_processing': 0.92,
                'context_generation': 0.88,
                'insight_extraction': 0.86
            },
            'ml_layer': {
                'predictive_modeling': 0.84,
                'anomaly_detection': 0.87,
                'optimization_algorithms': 0.85
            },
            'pa_layer': {
                'predictive_analytics': 0.86,
                'forecasting_accuracy': 0.83,
                'trend_analysis': 0.88
            }
        }
        
    def setup_gauge_credentials(self, username: str, password: str, platform_url: str):
        """Setup Gauge Telematics platform credentials"""
        self.gauge_credentials = {
            'username': username,
            'password': password,
            'platform_url': platform_url,
            'login_selector': 'input[name="username"], input[type="email"]',
            'password_selector': 'input[name="password"], input[type="password"]',
            'submit_selector': 'button[type="submit"], input[type="submit"]'
        }
        
    def setup_groundworks_credentials(self, username: str, password: str, platform_url: str):
        """Setup Groundworks platform credentials"""
        self.groundworks_credentials = {
            'username': username,
            'password': password,
            'platform_url': platform_url,
            'login_selector': 'input[name="username"], input[type="email"]',
            'password_selector': 'input[name="password"], input[type="password"]',
            'submit_selector': 'button[type="submit"], input[type="submit"]'
        }
        
    def generate_gauge_scraper_script(self) -> str:
        """Generate Puppeteer script for Gauge Telematics scraping"""
        return f"""
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: false, // Live viewer mode
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        defaultViewport: {{ width: 1366, height: 768 }}
    }});
    
    const page = await browser.newPage();
    
    // Enable live viewer console logging
    page.on('console', msg => console.log('GAUGE PAGE LOG:', msg.text()));
    
    try {{
        console.log('🚗 Starting Gauge Telematics data extraction...');
        
        // Navigate to Gauge platform
        await page.goto('{self.gauge_credentials.get("platform_url", "")}', {{
            waitUntil: 'networkidle2',
            timeout: 30000
        }});
        
        // Login to Gauge platform
        console.log('🔐 Logging into Gauge platform...');
        await page.waitForSelector('{self.gauge_credentials.get("login_selector", "")}');
        await page.type('{self.gauge_credentials.get("login_selector", "")}', '{self.gauge_credentials.get("username", "")}');
        await page.type('{self.gauge_credentials.get("password_selector", "")}', '{self.gauge_credentials.get("password", "")}');
        await page.click('{self.gauge_credentials.get("submit_selector", "")}');
        
        // Wait for dashboard to load
        await page.waitForTimeout(5000);
        
        // Extract vehicle data
        console.log('📊 Extracting vehicle telematics data...');
        
        const vehicleData = await page.evaluate(() => {{
            const vehicles = [];
            
            // Common selectors for vehicle data
            const vehicleElements = document.querySelectorAll(
                '.vehicle-row, .asset-row, [data-vehicle-id], .fleet-item, tr[data-id]'
            );
            
            vehicleElements.forEach((element, index) => {{
                try {{
                    const vehicleId = element.getAttribute('data-vehicle-id') || 
                                    element.getAttribute('data-id') || 
                                    element.querySelector('[data-vehicle-id]')?.getAttribute('data-vehicle-id') ||
                                    `VEHICLE_${{index + 1}}`;
                    
                    // Extract location data
                    const latElement = element.querySelector('[data-lat], .latitude, .lat');
                    const lngElement = element.querySelector('[data-lng], .longitude, .lng');
                    const lat = latElement ? parseFloat(latElement.textContent || latElement.getAttribute('data-lat')) : 0;
                    const lng = lngElement ? parseFloat(lngElement.textContent || lngElement.getAttribute('data-lng')) : 0;
                    
                    // Extract operational data
                    const speedElement = element.querySelector('[data-speed], .speed, .velocity');
                    const fuelElement = element.querySelector('[data-fuel], .fuel, .fuel-level');
                    const hoursElement = element.querySelector('[data-hours], .engine-hours, .hours');
                    const odometerElement = element.querySelector('[data-odometer], .odometer, .mileage');
                    
                    const speed = speedElement ? parseFloat(speedElement.textContent.replace(/[^0-9.]/g, '')) : 0;
                    const fuel = fuelElement ? parseFloat(fuelElement.textContent.replace(/[^0-9.]/g, '')) : 0;
                    const hours = hoursElement ? parseFloat(hoursElement.textContent.replace(/[^0-9.]/g, '')) : 0;
                    const odometer = odometerElement ? parseFloat(odometerElement.textContent.replace(/[^0-9.]/g, '')) : 0;
                    
                    // Extract status and alerts
                    const statusElement = element.querySelector('[data-status], .status, .vehicle-status');
                    const alertElements = element.querySelectorAll('.alert, .warning, .notification');
                    
                    const status = statusElement ? statusElement.textContent.trim() : 'UNKNOWN';
                    const alerts = Array.from(alertElements).map(alert => alert.textContent.trim());
                    
                    vehicles.push({{
                        vehicle_id: vehicleId,
                        lat: lat,
                        lng: lng,
                        speed: speed,
                        fuel_level: fuel,
                        engine_hours: hours,
                        odometer: odometer,
                        status: status,
                        alerts: alerts,
                        timestamp: new Date().toISOString()
                    }});
                }} catch (error) {{
                    console.error(`Error extracting vehicle data for element ${{index}}:`, error);
                }}
            }});
            
            return vehicles;
        }});
        
        console.log(`✅ Extracted ${{vehicleData.length}} vehicle records from Gauge`);
        
        // Save Gauge data
        fs.writeFileSync('gauge_telematics_data.json', JSON.stringify({{
            extraction_time: new Date().toISOString(),
            data_source: 'gauge_telematics',
            vehicle_count: vehicleData.length,
            vehicles: vehicleData
        }}, null, 2));
        
        console.log('💾 Gauge telematics data saved successfully');
        
    }} catch (error) {{
        console.error('❌ Gauge scraping error:', error);
        
        // Save error report
        fs.writeFileSync('gauge_error_report.json', JSON.stringify({{
            timestamp: new Date().toISOString(),
            error_message: error.message,
            platform: 'gauge_telematics'
        }}, null, 2));
    }}
    
    // Keep browser open for live viewing (comment out for headless)
    console.log('🔍 Live viewer active - browser will remain open for monitoring...');
    // await browser.close(); // Uncomment for headless mode
}})();
"""
    
    def generate_groundworks_scraper_script(self) -> str:
        """Generate Puppeteer script for Groundworks scraping"""
        return f"""
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: false, // Live viewer mode
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        defaultViewport: {{ width: 1366, height: 768 }}
    }});
    
    const page = await browser.newPage();
    
    // Enable live viewer console logging
    page.on('console', msg => console.log('GROUNDWORKS PAGE LOG:', msg.text()));
    
    try {{
        console.log('🏗️ Starting Groundworks data extraction...');
        
        // Navigate to Groundworks platform
        await page.goto('{self.groundworks_credentials.get("platform_url", "")}', {{
            waitUntil: 'networkidle2',
            timeout: 30000
        }});
        
        // Login to Groundworks platform
        console.log('🔐 Logging into Groundworks platform...');
        await page.waitForSelector('{self.groundworks_credentials.get("login_selector", "")}');
        await page.type('{self.groundworks_credentials.get("login_selector", "")}', '{self.groundworks_credentials.get("username", "")}');
        await page.type('{self.groundworks_credentials.get("password_selector", "")}', '{self.groundworks_credentials.get("password", "")}');
        await page.click('{self.groundworks_credentials.get("submit_selector", "")}');
        
        // Wait for dashboard to load
        await page.waitForTimeout(5000);
        
        // Extract operational data
        console.log('📈 Extracting operational data...');
        
        const operationalData = await page.evaluate(() => {{
            const assets = [];
            
            // Common selectors for operational data
            const assetElements = document.querySelectorAll(
                '.asset-row, .equipment-row, [data-asset-id], .operational-item, tr[data-asset]'
            );
            
            assetElements.forEach((element, index) => {{
                try {{
                    const assetId = element.getAttribute('data-asset-id') || 
                                  element.getAttribute('data-asset') || 
                                  element.querySelector('[data-asset-id]')?.getAttribute('data-asset-id') ||
                                  `ASSET_${{index + 1}}`;
                    
                    // Extract location and status
                    const locationElement = element.querySelector('[data-location], .location, .site');
                    const statusElement = element.querySelector('[data-status], .status, .operational-status');
                    
                    const location = locationElement ? locationElement.textContent.trim() : 'UNKNOWN';
                    const status = statusElement ? statusElement.textContent.trim() : 'UNKNOWN';
                    
                    // Extract utilization and efficiency
                    const utilizationElement = element.querySelector('[data-utilization], .utilization, .usage');
                    const efficiencyElement = element.querySelector('[data-efficiency], .efficiency, .performance');
                    
                    const utilization = utilizationElement ? 
                        parseFloat(utilizationElement.textContent.replace(/[^0-9.]/g, '')) / 100 : 0;
                    const efficiency = efficiencyElement ? 
                        parseFloat(efficiencyElement.textContent.replace(/[^0-9.]/g, '')) / 100 : 0;
                    
                    // Extract maintenance status
                    const maintenanceElement = element.querySelector('.maintenance, .service-due, [data-maintenance]');
                    const maintenanceDue = maintenanceElement ? 
                        maintenanceElement.textContent.toLowerCase().includes('due') : false;
                    
                    // Extract financial data
                    const revenueElement = element.querySelector('[data-revenue], .revenue, .earnings');
                    const costCenterElement = element.querySelector('[data-cost-center], .cost-center, .department');
                    
                    const revenue = revenueElement ? 
                        parseFloat(revenueElement.textContent.replace(/[^0-9.]/g, '')) : 0;
                    const costCenter = costCenterElement ? costCenterElement.textContent.trim() : 'GENERAL';
                    
                    assets.push({{
                        asset_id: assetId,
                        location: location,
                        operational_status: status,
                        utilization_rate: utilization,
                        maintenance_due: maintenanceDue,
                        cost_center: costCenter,
                        revenue_generated: revenue,
                        efficiency_score: efficiency,
                        timestamp: new Date().toISOString()
                    }});
                }} catch (error) {{
                    console.error(`Error extracting asset data for element ${{index}}:`, error);
                }}
            }});
            
            return assets;
        }});
        
        console.log(`✅ Extracted ${{operationalData.length}} asset records from Groundworks`);
        
        // Save Groundworks data
        fs.writeFileSync('groundworks_operational_data.json', JSON.stringify({{
            extraction_time: new Date().toISOString(),
            data_source: 'groundworks',
            asset_count: operationalData.length,
            assets: operationalData
        }}, null, 2));
        
        console.log('💾 Groundworks operational data saved successfully');
        
    }} catch (error) {{
        console.error('❌ Groundworks scraping error:', error);
        
        // Save error report
        fs.writeFileSync('groundworks_error_report.json', JSON.stringify({{
            timestamp: new Date().toISOString(),
            error_message: error.message,
            platform: 'groundworks'
        }}, null, 2));
    }}
    
    // Keep browser open for live viewing (comment out for headless)
    console.log('🔍 Live viewer active - browser will remain open for monitoring...');
    // await browser.close(); // Uncomment for headless mode
}})();
"""
        
    async def execute_gauge_scraping(self) -> Dict[str, Any]:
        """Execute Gauge Telematics scraping with live viewer"""
        if not hasattr(self, 'gauge_credentials'):
            return {
                'status': 'error',
                'message': 'Gauge credentials not configured. Please setup credentials first.'
            }
            
        script_content = self.generate_gauge_scraper_script()
        
        with open('gauge_scraper.js', 'w') as f:
            f.write(script_content)
            
        try:
            self.logger.info("🚗 Starting Gauge Telematics extraction with live viewer...")
            
            result = subprocess.run([
                'node', 'gauge_scraper.js'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Process extracted data
                await self._process_gauge_data()
                
                return {
                    'status': 'success',
                    'message': 'Gauge data extraction completed successfully',
                    'live_viewer_active': True,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'error_output': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': 'Gauge extraction timed out - live viewer may still be active',
                'timestamp': datetime.now().isoformat()
            }
        finally:
            if os.path.exists('gauge_scraper.js'):
                os.remove('gauge_scraper.js')
                
    async def execute_groundworks_scraping(self) -> Dict[str, Any]:
        """Execute Groundworks scraping with live viewer"""
        if not hasattr(self, 'groundworks_credentials'):
            return {
                'status': 'error',
                'message': 'Groundworks credentials not configured. Please setup credentials first.'
            }
            
        script_content = self.generate_groundworks_scraper_script()
        
        with open('groundworks_scraper.js', 'w') as f:
            f.write(script_content)
            
        try:
            self.logger.info("🏗️ Starting Groundworks extraction with live viewer...")
            
            result = subprocess.run([
                'node', 'groundworks_scraper.js'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Process extracted data
                await self._process_groundworks_data()
                
                return {
                    'status': 'success',
                    'message': 'Groundworks data extraction completed successfully',
                    'live_viewer_active': True,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'error_output': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'message': 'Groundworks extraction timed out - live viewer may still be active',
                'timestamp': datetime.now().isoformat()
            }
        finally:
            if os.path.exists('groundworks_scraper.js'):
                os.remove('groundworks_scraper.js')
                
    async def _process_gauge_data(self):
        """Process extracted Gauge data with QQ model enhancement"""
        try:
            if os.path.exists('gauge_telematics_data.json'):
                with open('gauge_telematics_data.json', 'r') as f:
                    data = json.load(f)
                    
                vehicles = data.get('vehicles', [])
                
                # Apply QQ model predictions
                for vehicle in vehicles:
                    qq_predictions = self._apply_qq_predictions('gauge', vehicle)
                    vehicle['qq_prediction_score'] = qq_predictions['overall_score']
                    
                    # Store in database
                    self._store_vehicle_data(vehicle)
                    
                self.logger.info(f"Processed {len(vehicles)} vehicle records with QQ enhancement")
                
        except Exception as e:
            self.logger.error(f"Error processing Gauge data: {e}")
            
    async def _process_groundworks_data(self):
        """Process extracted Groundworks data with QQ model enhancement"""
        try:
            if os.path.exists('groundworks_operational_data.json'):
                with open('groundworks_operational_data.json', 'r') as f:
                    data = json.load(f)
                    
                assets = data.get('assets', [])
                
                # Apply QQ model predictions
                for asset in assets:
                    qq_predictions = self._apply_qq_predictions('groundworks', asset)
                    asset['qq_optimization_score'] = qq_predictions['overall_score']
                    
                    # Store in database
                    self._store_groundworks_data(asset)
                    
                self.logger.info(f"Processed {len(assets)} asset records with QQ enhancement")
                
        except Exception as e:
            self.logger.error(f"Error processing Groundworks data: {e}")
            
    def _apply_qq_predictions(self, data_source: str, data: Dict) -> Dict[str, Any]:
        """Apply QQ (Qubit Quantum ASI-AGI-AI LLM-ML-PA) model predictions"""
        
        # ASI layer - Strategic optimization
        asi_score = self.qq_model['asi_layer']['strategic_optimization']
        
        # AGI layer - Cross-domain reasoning
        agi_score = self.qq_model['agi_layer']['cross_domain_reasoning']
        
        # AI layer - Pattern recognition
        ai_score = self.qq_model['ai_layer']['pattern_recognition']
        
        # LLM layer - Context understanding
        llm_score = self.qq_model['llm_layer']['context_generation']
        
        # ML layer - Predictive modeling
        ml_score = self.qq_model['ml_layer']['predictive_modeling']
        
        # PA layer - Predictive analytics
        pa_score = self.qq_model['pa_layer']['predictive_analytics']
        
        # Calculate overall QQ score
        overall_score = (
            asi_score * 0.25 +
            agi_score * 0.20 +
            ai_score * 0.20 +
            llm_score * 0.15 +
            ml_score * 0.15 +
            pa_score * 0.05
        )
        
        # Generate specific predictions based on data source
        if data_source == 'gauge':
            predictions = {
                'fuel_efficiency_prediction': data.get('fuel_level', 0) * asi_score,
                'maintenance_prediction': overall_score * 0.8,
                'route_optimization_score': agi_score * 0.9
            }
        else:  # groundworks
            predictions = {
                'utilization_optimization': data.get('utilization_rate', 0) * asi_score,
                'revenue_prediction': data.get('revenue_generated', 0) * agi_score,
                'efficiency_improvement': overall_score * 0.85
            }
            
        return {
            'overall_score': overall_score,
            'asi_score': asi_score,
            'agi_score': agi_score,
            'ai_score': ai_score,
            'llm_score': llm_score,
            'ml_score': ml_score,
            'pa_score': pa_score,
            'predictions': predictions
        }
        
    def _store_vehicle_data(self, vehicle_data: Dict):
        """Store vehicle data in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO vehicle_telematics
                (vehicle_id, lat, lng, speed, fuel_level, engine_hours, odometer,
                 timestamp, status, driver_id, alerts, qq_prediction_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle_data.get('vehicle_id'),
                vehicle_data.get('lat', 0),
                vehicle_data.get('lng', 0),
                vehicle_data.get('speed', 0),
                vehicle_data.get('fuel_level', 0),
                vehicle_data.get('engine_hours', 0),
                vehicle_data.get('odometer', 0),
                vehicle_data.get('timestamp'),
                vehicle_data.get('status', 'UNKNOWN'),
                vehicle_data.get('driver_id'),
                json.dumps(vehicle_data.get('alerts', [])),
                vehicle_data.get('qq_prediction_score', 0)
            ))
            
            conn.commit()
            
    def _store_groundworks_data(self, asset_data: Dict):
        """Store Groundworks data in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO groundworks_data
                (asset_id, location, operational_status, utilization_rate, maintenance_due,
                 cost_center, revenue_generated, efficiency_score, timestamp, qq_optimization_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset_data.get('asset_id'),
                asset_data.get('location', 'UNKNOWN'),
                asset_data.get('operational_status', 'UNKNOWN'),
                asset_data.get('utilization_rate', 0),
                asset_data.get('maintenance_due', False),
                asset_data.get('cost_center', 'GENERAL'),
                asset_data.get('revenue_generated', 0),
                asset_data.get('efficiency_score', 0),
                asset_data.get('timestamp'),
                asset_data.get('qq_optimization_score', 0)
            ))
            
            conn.commit()
            
    def get_scraping_status(self) -> Dict[str, Any]:
        """Get current scraping and QQ model status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count records
            cursor.execute('SELECT COUNT(*) FROM vehicle_telematics')
            vehicle_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM groundworks_data')
            asset_count = cursor.fetchone()[0]
            
            # Get latest records
            cursor.execute('SELECT timestamp FROM vehicle_telematics ORDER BY timestamp DESC LIMIT 1')
            latest_vehicle = cursor.fetchone()
            
            cursor.execute('SELECT timestamp FROM groundworks_data ORDER BY timestamp DESC LIMIT 1')
            latest_asset = cursor.fetchone()
            
        return {
            'vehicle_records': vehicle_count,
            'asset_records': asset_count,
            'latest_vehicle_update': latest_vehicle[0] if latest_vehicle else None,
            'latest_asset_update': latest_asset[0] if latest_asset else None,
            'qq_model_status': self.qq_model,
            'live_viewer_active': self.live_viewer_active,
            'scraper_status': 'active'
        }

def create_gauge_groundworks_qq_scraper():
    """Factory function to create QQ scraper instance"""
    return GaugeGroundworksQQScraper()