"""
Watson Manual Configuration Interface
Free API alternatives and manual credential management
"""

import os
import json
import requests
from datetime import datetime
from app import db
from models_clean import PlatformData

class WatsonManualConfig:
    """Manual configuration interface for Watson dashboard"""
    
    def __init__(self):
        self.free_apis = {
            'weather': 'wttr.in',
            'crypto': 'coinbase_public',
            'stocks': 'yahoo_finance_free',
            'news': 'newsapi_free',
            'forex': 'fixer_free'
        }
    
    def get_free_stock_data(self, symbols=['AAPL', 'MSFT', 'GOOGL', 'TSLA']):
        """Get stock data from free Yahoo Finance API"""
        
        stock_data = {}
        
        for symbol in symbols:
            try:
                # Using Yahoo Finance's free API
                url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    chart = data['chart']['result'][0]
                    meta = chart['meta']
                    
                    stock_data[symbol] = {
                        'price': round(meta['regularMarketPrice'], 2),
                        'change': round(meta['regularMarketPrice'] - meta['previousClose'], 2),
                        'change_percent': round(((meta['regularMarketPrice'] - meta['previousClose']) / meta['previousClose']) * 100, 2),
                        'volume': meta.get('regularMarketVolume', 0),
                        'market_cap': meta.get('marketCap', 'N/A'),
                        'currency': meta['currency']
                    }
            except:
                continue
        
        return stock_data
    
    def get_free_forex_data(self):
        """Get forex data from free ExchangeRate-API"""
        
        try:
            # Free exchange rate API (no key required)
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Major currency pairs
                major_pairs = ['EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
                
                forex_data = {}
                for currency in major_pairs:
                    if currency in data['rates']:
                        forex_data[f'USD{currency}'] = {
                            'rate': data['rates'][currency],
                            'base': 'USD',
                            'target': currency,
                            'timestamp': data['date']
                        }
                
                return forex_data
        except:
            return {}
    
    def get_free_news_data(self):
        """Get news from free RSS feeds"""
        
        try:
            # Using free RSS to JSON service
            rss_feeds = [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'https://feeds.bloomberg.com/markets/news.rss'
            ]
            
            news_data = []
            
            for feed_url in rss_feeds:
                try:
                    # Convert RSS to JSON using free service
                    api_url = f'https://api.rss2json.com/v1/api.json?rss_url={feed_url}&count=5'
                    response = requests.get(api_url, timeout=5)
                    
                    if response.status_code == 200:
                        feed_data = response.json()
                        
                        for item in feed_data.get('items', [])[:3]:
                            news_data.append({
                                'title': item['title'],
                                'description': item['description'][:200] + '...' if len(item['description']) > 200 else item['description'],
                                'link': item['link'],
                                'published': item['pubDate'],
                                'source': feed_data['feed']['title']
                            })
                except:
                    continue
            
            return news_data[:10]  # Return top 10 news items
        except:
            return []
    
    def manual_api_configuration(self):
        """Manual API configuration interface"""
        
        config_options = {
            'robinhood_alternative': {
                'name': 'Yahoo Finance Free API',
                'description': 'Replace Robinhood with free stock data',
                'implementation': 'get_free_stock_data',
                'cost': 'Free',
                'rate_limit': '2000 requests/hour'
            },
            'gauge_alternative': {
                'name': 'Manual Fleet Data Entry',
                'description': 'Manual fleet metrics configuration',
                'implementation': 'manual_fleet_entry',
                'cost': 'Free',
                'rate_limit': 'Unlimited'
            },
            'weather_configured': {
                'name': 'wttr.in Weather Service',
                'description': 'Free weather data (already implemented)',
                'implementation': 'wttr_weather_api',
                'cost': 'Free',
                'rate_limit': 'Unlimited'
            },
            'news_integration': {
                'name': 'RSS News Feeds',
                'description': 'Free news from major sources',
                'implementation': 'get_free_news_data',
                'cost': 'Free',
                'rate_limit': 'Reasonable use'
            },
            'forex_integration': {
                'name': 'ExchangeRate-API',
                'description': 'Free forex rates',
                'implementation': 'get_free_forex_data',
                'cost': 'Free',
                'rate_limit': '1500 requests/month'
            }
        }
        
        return config_options
    
    def save_manual_credentials(self, credentials_data):
        """Save manually entered credentials"""
        
        try:
            creds_record = PlatformData.query.filter_by(data_type='manual_credentials').first()
            if creds_record:
                existing_creds = creds_record.data_content
                existing_creds.update(credentials_data)
                creds_record.data_content = existing_creds
                creds_record.updated_at = datetime.utcnow()
            else:
                creds_record = PlatformData(
                    data_type='manual_credentials',
                    data_content=credentials_data
                )
                db.session.add(creds_record)
            
            db.session.commit()
            return {"status": "success", "message": "Credentials saved manually"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to save credentials: {str(e)}"}
    
    def get_saved_credentials(self):
        """Get manually saved credentials"""
        
        try:
            creds_record = PlatformData.query.filter_by(data_type='manual_credentials').first()
            return creds_record.data_content if creds_record else {}
        except:
            return {}
    
    def manual_fleet_entry(self, fleet_data):
        """Manual fleet data entry interface"""
        
        default_fleet = {
            'total_vehicles': fleet_data.get('total_vehicles', 45),
            'active_vehicles': fleet_data.get('active_vehicles', 38),
            'maintenance_vehicles': fleet_data.get('maintenance_vehicles', 4),
            'out_of_service': fleet_data.get('out_of_service', 3),
            'utilization_rate': fleet_data.get('utilization_rate', 84.4),
            'average_hours_per_day': fleet_data.get('average_hours_per_day', 8.2),
            'fuel_efficiency': fleet_data.get('fuel_efficiency', 12.5),
            'locations': fleet_data.get('locations', ['New York', 'San Francisco', 'Chicago', 'Dallas'])
        }
        
        try:
            fleet_record = PlatformData.query.filter_by(data_type='manual_fleet_data').first()
            if fleet_record:
                fleet_record.data_content = default_fleet
                fleet_record.updated_at = datetime.utcnow()
            else:
                fleet_record = PlatformData(
                    data_type='manual_fleet_data',
                    data_content=default_fleet
                )
                db.session.add(fleet_record)
            
            db.session.commit()
            return {"status": "success", "fleet_data": default_fleet}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def update_all_free_data_sources(self):
        """Update all free data sources"""
        
        results = {}
        
        # Update stock data
        try:
            stock_data = self.get_free_stock_data()
            if stock_data:
                self._store_data('stock_data', stock_data)
                results['stocks'] = 'success'
        except:
            results['stocks'] = 'failed'
        
        # Update forex data
        try:
            forex_data = self.get_free_forex_data()
            if forex_data:
                self._store_data('forex_data', forex_data)
                results['forex'] = 'success'
        except:
            results['forex'] = 'failed'
        
        # Update news data
        try:
            news_data = self.get_free_news_data()
            if news_data:
                self._store_data('news_data', news_data)
                results['news'] = 'success'
        except:
            results['news'] = 'failed'
        
        return results
    
    def _store_data(self, data_type, data):
        """Store data in database"""
        
        try:
            record = PlatformData.query.filter_by(data_type=data_type).first()
            if record:
                record.data_content = {
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'free_api'
                }
                record.updated_at = datetime.utcnow()
            else:
                record = PlatformData(
                    data_type=data_type,
                    data_content={
                        'data': data,
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'free_api'
                    }
                )
                db.session.add(record)
            
            db.session.commit()
        except Exception as e:
            print(f"Failed to store {data_type}: {e}")

# Global Watson config instance
watson_config = WatsonManualConfig()

def get_watson_config_options():
    """Get Watson configuration options"""
    return watson_config.manual_api_configuration()

def update_free_data_sources():
    """Update all free data sources"""
    return watson_config.update_all_free_data_sources()

def save_manual_credentials(credentials):
    """Save manual credentials"""
    return watson_config.save_manual_credentials(credentials)

def manual_fleet_entry(fleet_data):
    """Manual fleet data entry"""
    return watson_config.manual_fleet_entry(fleet_data)