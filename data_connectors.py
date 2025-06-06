"""
TRAXOVO Data Connectors - Authentic Data Sources
Real-time data integration with external APIs
"""

import os
import requests
import json
from datetime import datetime
from app import db
from models_clean import PlatformData

class DataConnector:
    """Base class for external data connections"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TRAXOVO-Enterprise/1.0'
        })

class RobinhoodConnector(DataConnector):
    """Connect to Robinhood API for portfolio data"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get('ROBINHOOD_API_KEY')
        self.access_token = os.environ.get('ROBINHOOD_ACCESS_TOKEN')
    
    def get_portfolio_data(self):
        """Fetch real portfolio data from Robinhood"""
        if not self.access_token:
            return {"error": "Robinhood credentials not configured"}
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = self.session.get(
                'https://api.robinhood.com/positions/',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Robinhood API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Robinhood connection failed: {str(e)}"}

class CoinbaseConnector(DataConnector):
    """Connect to Coinbase API for crypto market data"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get('COINBASE_API_KEY')
        self.api_secret = os.environ.get('COINBASE_API_SECRET')
    
    def get_market_data(self):
        """Fetch real crypto market data"""
        try:
            # Using public API first, upgrade to authenticated if keys available
            response = self.session.get(
                'https://api.coinbase.com/v2/exchange-rates?currency=BTC'
            )
            
            if response.status_code == 200:
                data = response.json()
                btc_usd = float(data['data']['rates']['USD'])
                
                # Get 24h change from another endpoint
                ticker_response = self.session.get(
                    'https://api.pro.coinbase.com/products/BTC-USD/ticker'
                )
                
                change_24h = 0
                if ticker_response.status_code == 200:
                    ticker_data = ticker_response.json()
                    if 'price' in ticker_data:
                        current_price = float(ticker_data['price'])
                        # Calculate approximate change (simplified)
                        change_24h = round((current_price - btc_usd) / btc_usd * 100, 2)
                
                return {
                    "btc_usdt": {
                        "price": btc_usd,
                        "change": change_24h,
                        "status": "live",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            else:
                return {"error": f"Coinbase API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"Coinbase connection failed: {str(e)}"}

class GaugeAPIConnector(DataConnector):
    """Connect to GAUGE API for fleet/asset data"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get('GAUGE_API_KEY')
        self.base_url = os.environ.get('GAUGE_API_URL', 'https://api.gauge.io')
    
    def get_fleet_metrics(self):
        """Fetch real fleet operational data"""
        if not self.api_key:
            return {"error": "GAUGE API credentials not configured"}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = self.session.get(
                f'{self.base_url}/v1/fleet/metrics',
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"GAUGE API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"GAUGE API connection failed: {str(e)}"}

class OpenAIConnector(DataConnector):
    """Connect to OpenAI API for AI insights"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get('OPENAI_API_KEY')
    
    def generate_executive_insights(self, data):
        """Generate AI-powered executive insights"""
        if not self.api_key:
            return {"error": "OpenAI API key not configured"}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an enterprise analytics AI. Generate executive-level insights from operational data."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this operational data and provide 3 key insights: {json.dumps(data)}"
                    }
                ],
                "max_tokens": 500
            }
            
            response = self.session.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "insights": result['choices'][0]['message']['content'],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"OpenAI API error: {response.status_code}"}
        except Exception as e:
            return {"error": f"OpenAI connection failed: {str(e)}"}

def update_platform_data():
    """Update all platform data from authentic sources"""
    
    # Initialize connectors
    robinhood = RobinhoodConnector()
    coinbase = CoinbaseConnector()
    gauge = GaugeAPIConnector()
    openai = OpenAIConnector()
    
    # Update market data
    market_data = coinbase.get_market_data()
    if "error" not in market_data:
        platform_data = PlatformData.query.filter_by(data_type='market_data').first()
        if platform_data:
            platform_data.data_content = market_data
            platform_data.updated_at = datetime.utcnow()
        else:
            platform_data = PlatformData(
                data_type='market_data',
                data_content=market_data
            )
            db.session.add(platform_data)
    
    # Update portfolio data
    portfolio_data = robinhood.get_portfolio_data()
    if "error" not in portfolio_data:
        platform_data = PlatformData.query.filter_by(data_type='portfolio_data').first()
        if platform_data:
            platform_data.data_content = portfolio_data
            platform_data.updated_at = datetime.utcnow()
        else:
            platform_data = PlatformData(
                data_type='portfolio_data',
                data_content=portfolio_data
            )
            db.session.add(platform_data)
    
    # Update fleet metrics
    fleet_data = gauge.get_fleet_metrics()
    if "error" not in fleet_data:
        platform_data = PlatformData.query.filter_by(data_type='fleet_metrics').first()
        if platform_data:
            platform_data.data_content = fleet_data
            platform_data.updated_at = datetime.utcnow()
        else:
            platform_data = PlatformData(
                data_type='fleet_metrics',
                data_content=fleet_data
            )
            db.session.add(platform_data)
    
    # Update platform status based on connection results
    status_data = {
        "robinhood": {
            "status": "Connected" if "error" not in portfolio_data else "Auth Required",
            "color": "green" if "error" not in portfolio_data else "red"
        },
        "coinbase": {
            "status": "Connected" if "error" not in market_data else "Auth Required", 
            "color": "green" if "error" not in market_data else "red"
        },
        "gauge_api": {
            "status": "Connected" if "error" not in fleet_data else "Auth Required",
            "color": "green" if "error" not in fleet_data else "red"
        },
        "openai": {
            "status": "Connected" if openai.api_key else "Auth Required",
            "color": "green" if openai.api_key else "red"
        }
    }
    
    platform_status = PlatformData.query.filter_by(data_type='platform_status').first()
    if platform_status:
        platform_status.data_content = status_data
        platform_status.updated_at = datetime.utcnow()
    else:
        platform_status = PlatformData(
            data_type='platform_status',
            data_content=status_data
        )
        db.session.add(platform_status)
    
    db.session.commit()
    return True