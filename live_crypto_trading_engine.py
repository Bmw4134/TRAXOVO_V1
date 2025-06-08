"""
Live Crypto Trading Engine - NEXUS AGENT Implementation
Real-time trading with Robinhood & Coinbase Pro integration
"""

import os
import json
import requests
import hashlib
import hmac
import base64
import time
from datetime import datetime
from typing import Dict, List, Any

class LiveCryptoTradingEngine:
    """Live crypto trading with authenticated API access"""
    
    def __init__(self):
        self.robinhood_username = os.environ.get('ROBINHOOD_USERNAME')
        self.robinhood_password = os.environ.get('ROBINHOOD_PASSWORD')
        self.coinbase_api_key = os.environ.get('COINBASE_API_KEY')
        self.coinbase_secret = os.environ.get('COINBASE_SECRET')
        self.coinbase_passphrase = os.environ.get('COINBASE_PASSPHRASE')
        
        self.robinhood_token = None
        self.trading_active = False
        self.wallet_balance = 30.00
        self.supported_assets = ['BTC', 'ETH', 'ADA', 'DOT', 'SOL', 'DOGE']
        
    def authenticate_robinhood(self) -> Dict:
        """Authenticate with Robinhood API"""
        
        if not self.robinhood_username or not self.robinhood_password:
            return {'status': 'error', 'message': 'Robinhood credentials not configured'}
        
        auth_url = 'https://robinhood.com/api-token-auth/'
        auth_data = {
            'username': self.robinhood_username,
            'password': self.robinhood_password
        }
        
        try:
            response = requests.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.robinhood_token = data.get('token')
                
                return {
                    'status': 'authenticated',
                    'platform': 'robinhood',
                    'token_received': bool(self.robinhood_token),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'auth_failed',
                    'platform': 'robinhood',
                    'error_code': response.status_code,
                    'message': 'Authentication failed'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'platform': 'robinhood',
                'message': str(e)
            }
    
    def authenticate_coinbase(self) -> Dict:
        """Authenticate with Coinbase Pro API"""
        
        if not all([self.coinbase_api_key, self.coinbase_secret, self.coinbase_passphrase]):
            return {'status': 'error', 'message': 'Coinbase credentials not configured'}
        
        try:
            # Test authentication with accounts endpoint
            timestamp = str(int(time.time()))
            message = timestamp + 'GET' + '/accounts'
            signature = base64.b64encode(
                hmac.new(
                    base64.b64decode(self.coinbase_secret),
                    message.encode(),
                    hashlib.sha256
                ).digest()
            ).decode()
            
            headers = {
                'CB-ACCESS-KEY': self.coinbase_api_key,
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-PASSPHRASE': self.coinbase_passphrase,
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://api.pro.coinbase.com/accounts', headers=headers)
            
            if response.status_code == 200:
                accounts = response.json()
                
                return {
                    'status': 'authenticated',
                    'platform': 'coinbase_pro',
                    'accounts_found': len(accounts),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'auth_failed',
                    'platform': 'coinbase_pro',
                    'error_code': response.status_code,
                    'message': 'Authentication failed'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'platform': 'coinbase_pro',
                'message': str(e)
            }
    
    def get_portfolio_balance(self) -> Dict:
        """Get current portfolio balance from authenticated exchanges"""
        
        portfolio = {
            'total_balance_usd': self.wallet_balance,
            'robinhood_balance': 0.0,
            'coinbase_balance': 0.0,
            'asset_breakdown': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # Get Robinhood balance
        if self.robinhood_token:
            try:
                headers = {'Authorization': f'Token {self.robinhood_token}'}
                response = requests.get('https://robinhood.com/api/accounts/', headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        buying_power = float(data['results'][0].get('buying_power', 0))
                        portfolio['robinhood_balance'] = buying_power
                        
            except Exception as e:
                portfolio['robinhood_error'] = str(e)
        
        # Get Coinbase balance
        if all([self.coinbase_api_key, self.coinbase_secret]):
            try:
                timestamp = str(int(time.time()))
                message = timestamp + 'GET' + '/accounts'
                signature = base64.b64encode(
                    hmac.new(
                        base64.b64decode(self.coinbase_secret),
                        message.encode(),
                        hashlib.sha256
                    ).digest()
                ).decode()
                
                headers = {
                    'CB-ACCESS-KEY': self.coinbase_api_key,
                    'CB-ACCESS-SIGN': signature,
                    'CB-ACCESS-TIMESTAMP': timestamp,
                    'CB-ACCESS-PASSPHRASE': self.coinbase_passphrase
                }
                
                response = requests.get('https://api.pro.coinbase.com/accounts', headers=headers)
                
                if response.status_code == 200:
                    accounts = response.json()
                    total_balance = 0
                    
                    for account in accounts:
                        balance = float(account.get('balance', 0))
                        currency = account.get('currency', 'USD')
                        
                        if balance > 0:
                            portfolio['asset_breakdown'][currency] = balance
                            if currency == 'USD':
                                total_balance += balance
                    
                    portfolio['coinbase_balance'] = total_balance
                    
            except Exception as e:
                portfolio['coinbase_error'] = str(e)
        
        # Update total balance
        portfolio['total_balance_usd'] = portfolio['robinhood_balance'] + portfolio['coinbase_balance']
        
        return portfolio
    
    def execute_market_order(self, symbol: str, side: str, amount: float, platform: str = 'coinbase') -> Dict:
        """Execute live market order"""
        
        if not self.trading_active:
            return {'status': 'error', 'message': 'Trading engine not active'}
        
        order_result = {
            'order_id': f"NEXUS_{int(time.time())}",
            'symbol': symbol,
            'side': side,  # 'buy' or 'sell'
            'amount': amount,
            'platform': platform,
            'order_type': 'market',
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        if platform == 'coinbase' and all([self.coinbase_api_key, self.coinbase_secret]):
            try:
                # Coinbase Pro market order
                order_data = {
                    'size': str(amount),
                    'side': side,
                    'product_id': f'{symbol}-USD',
                    'type': 'market'
                }
                
                timestamp = str(int(time.time()))
                message = timestamp + 'POST' + '/orders' + json.dumps(order_data)
                signature = base64.b64encode(
                    hmac.new(
                        base64.b64decode(self.coinbase_secret),
                        message.encode(),
                        hashlib.sha256
                    ).digest()
                ).decode()
                
                headers = {
                    'CB-ACCESS-KEY': self.coinbase_api_key,
                    'CB-ACCESS-SIGN': signature,
                    'CB-ACCESS-TIMESTAMP': timestamp,
                    'CB-ACCESS-PASSPHRASE': self.coinbase_passphrase,
                    'Content-Type': 'application/json'
                }
                
                response = requests.post('https://api.pro.coinbase.com/orders', 
                                       json=order_data, headers=headers)
                
                if response.status_code == 200:
                    order_response = response.json()
                    order_result.update({
                        'status': 'submitted',
                        'exchange_order_id': order_response.get('id'),
                        'filled_size': order_response.get('filled_size', '0'),
                        'executed_value': order_response.get('executed_value', '0')
                    })
                else:
                    order_result.update({
                        'status': 'failed',
                        'error_code': response.status_code,
                        'error_message': response.text
                    })
                    
            except Exception as e:
                order_result.update({
                    'status': 'error',
                    'error_message': str(e)
                })
        
        elif platform == 'robinhood' and self.robinhood_token:
            # Robinhood order implementation would go here
            order_result.update({
                'status': 'simulated',
                'message': 'Robinhood order simulation (API implementation pending)'
            })
        
        return order_result
    
    def get_live_market_data(self) -> Dict:
        """Get live market data for supported assets"""
        
        market_data = {
            'timestamp': datetime.now().isoformat(),
            'market_status': 'OPEN_24_7',
            'prices': {},
            'market_cap': {},
            'volume_24h': {}
        }
        
        try:
            # Get live prices from Coinbase Pro
            for symbol in self.supported_assets:
                try:
                    response = requests.get(f'https://api.pro.coinbase.com/products/{symbol}-USD/ticker')
                    
                    if response.status_code == 200:
                        ticker = response.json()
                        market_data['prices'][symbol] = {
                            'price': float(ticker.get('price', 0)),
                            'volume': float(ticker.get('volume', 0)),
                            'change_24h': 0  # Would calculate from historical data
                        }
                        
                except Exception as e:
                    market_data['prices'][symbol] = {
                        'price': 0,
                        'error': str(e)
                    }
            
        except Exception as e:
            market_data['error'] = str(e)
        
        return market_data
    
    def activate_trading_engine(self) -> Dict:
        """Activate live trading engine with full authentication"""
        
        activation_result = {
            'activation_timestamp': datetime.now().isoformat(),
            'trading_engine_status': 'activating',
            'authentication_results': {},
            'portfolio_verification': {},
            'market_data_connection': {}
        }
        
        # Authenticate with exchanges
        robinhood_auth = self.authenticate_robinhood()
        coinbase_auth = self.authenticate_coinbase()
        
        activation_result['authentication_results'] = {
            'robinhood': robinhood_auth,
            'coinbase': coinbase_auth
        }
        
        # Check if at least one exchange is authenticated
        authenticated_exchanges = []
        if robinhood_auth.get('status') == 'authenticated':
            authenticated_exchanges.append('robinhood')
        if coinbase_auth.get('status') == 'authenticated':
            authenticated_exchanges.append('coinbase')
        
        if authenticated_exchanges:
            self.trading_active = True
            
            # Get portfolio balance
            portfolio = self.get_portfolio_balance()
            activation_result['portfolio_verification'] = portfolio
            
            # Get live market data
            market_data = self.get_live_market_data()
            activation_result['market_data_connection'] = market_data
            
            activation_result.update({
                'trading_engine_status': 'active',
                'authenticated_exchanges': authenticated_exchanges,
                'live_trading_enabled': True,
                'portfolio_balance': portfolio.get('total_balance_usd', self.wallet_balance),
                'supported_assets': self.supported_assets,
                'market_hours_bypass': True
            })
            
        else:
            activation_result.update({
                'trading_engine_status': 'authentication_failed',
                'live_trading_enabled': False,
                'error': 'No exchanges successfully authenticated'
            })
        
        return activation_result

def initialize_live_crypto_trading():
    """Initialize and activate live crypto trading engine"""
    
    engine = LiveCryptoTradingEngine()
    activation_result = engine.activate_trading_engine()
    
    return {
        'engine_initialization': 'completed',
        'activation_result': activation_result,
        'engine_instance': engine,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    result = initialize_live_crypto_trading()
    print(json.dumps(result['activation_result'], indent=2))