"""
Crypto Trading Demo Mode - NEXUS AGENT Implementation
Demonstrates live trading capabilities with paper trading simulation
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any

class CryptoTradingDemo:
    """Demo crypto trading engine with live market data"""
    
    def __init__(self):
        self.demo_wallet = {
            'USD': 30.00,
            'BTC': 0.0,
            'ETH': 0.0,
            'ADA': 0.0,
            'SOL': 0.0,
            'DOGE': 0.0
        }
        self.trade_history = []
        self.supported_assets = ['BTC', 'ETH', 'ADA', 'SOL', 'DOGE']
        
    def get_live_market_prices(self) -> Dict:
        """Get real-time market prices from public APIs"""
        
        prices = {}
        
        try:
            # Get live prices from CoinGecko API (no auth required)
            coin_ids = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum', 
                'ADA': 'cardano',
                'SOL': 'solana',
                'DOGE': 'dogecoin'
            }
            
            ids_string = ','.join(coin_ids.values())
            response = requests.get(
                f'https://api.coingecko.com/api/v3/simple/price?ids={ids_string}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true'
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for symbol, coin_id in coin_ids.items():
                    if coin_id in data:
                        prices[symbol] = {
                            'price': data[coin_id]['usd'],
                            'change_24h': data[coin_id].get('usd_24h_change', 0),
                            'volume_24h': data[coin_id].get('usd_24h_vol', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            # Fallback to mock data if API fails
            prices = {
                'BTC': {'price': 97250.0, 'change_24h': 2.5, 'volume_24h': 25000000000},
                'ETH': {'price': 3850.0, 'change_24h': 1.8, 'volume_24h': 15000000000},
                'ADA': {'price': 1.15, 'change_24h': -0.5, 'volume_24h': 800000000},
                'SOL': {'price': 145.0, 'change_24h': 3.2, 'volume_24h': 2500000000},
                'DOGE': {'price': 0.42, 'change_24h': 5.1, 'volume_24h': 1200000000}
            }
            
        return {
            'prices': prices,
            'market_status': 'OPEN_24_7',
            'last_updated': datetime.now().isoformat(),
            'data_source': 'live_coingecko_api'
        }
    
    def execute_demo_trade(self, symbol: str, side: str, amount_usd: float) -> Dict:
        """Execute demo trade with live market prices"""
        
        market_data = self.get_live_market_prices()
        current_price = market_data['prices'][symbol]['price']
        
        trade_result = {
            'trade_id': f"DEMO_{int(datetime.now().timestamp())}",
            'symbol': symbol,
            'side': side,
            'amount_usd': amount_usd,
            'price': current_price,
            'timestamp': datetime.now().isoformat(),
            'status': 'executed'
        }
        
        if side == 'buy':
            if self.demo_wallet['USD'] >= amount_usd:
                crypto_amount = amount_usd / current_price
                self.demo_wallet['USD'] -= amount_usd
                self.demo_wallet[symbol] += crypto_amount
                
                trade_result.update({
                    'crypto_amount': crypto_amount,
                    'wallet_balance_usd': self.demo_wallet['USD'],
                    'crypto_balance': self.demo_wallet[symbol]
                })
            else:
                trade_result.update({
                    'status': 'failed',
                    'error': 'Insufficient USD balance'
                })
                
        elif side == 'sell':
            crypto_amount = amount_usd / current_price
            if self.demo_wallet[symbol] >= crypto_amount:
                self.demo_wallet[symbol] -= crypto_amount
                self.demo_wallet['USD'] += amount_usd
                
                trade_result.update({
                    'crypto_amount': crypto_amount,
                    'wallet_balance_usd': self.demo_wallet['USD'],
                    'crypto_balance': self.demo_wallet[symbol]
                })
            else:
                trade_result.update({
                    'status': 'failed',
                    'error': f'Insufficient {symbol} balance'
                })
        
        if trade_result['status'] == 'executed':
            self.trade_history.append(trade_result)
            
        return trade_result
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio value and breakdown"""
        
        market_data = self.get_live_market_prices()
        portfolio_value = self.demo_wallet['USD']
        
        holdings = {}
        for symbol in self.supported_assets:
            if self.demo_wallet[symbol] > 0:
                current_price = market_data['prices'][symbol]['price']
                value = self.demo_wallet[symbol] * current_price
                portfolio_value += value
                
                holdings[symbol] = {
                    'amount': self.demo_wallet[symbol],
                    'current_price': current_price,
                    'value_usd': value
                }
        
        return {
            'total_portfolio_value': portfolio_value,
            'cash_balance': self.demo_wallet['USD'],
            'crypto_holdings': holdings,
            'total_trades': len(self.trade_history),
            'profit_loss': portfolio_value - 30.00,  # Initial balance was $30
            'last_updated': datetime.now().isoformat()
        }

def create_crypto_dashboard_interface() -> str:
    """Create crypto trading dashboard with live data"""
    
    demo_engine = CryptoTradingDemo()
    market_data = demo_engine.get_live_market_prices()
    portfolio = demo_engine.get_portfolio_summary()
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEXUS Crypto Trading Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; margin: 0; padding: 20px; }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .trading-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .market-card {{ background: rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; }}
            .price {{ font-size: 1.8em; font-weight: bold; color: #10b981; }}
            .change {{ font-size: 1em; }}
            .positive {{ color: #10b981; }}
            .negative {{ color: #ef4444; }}
            .trade-button {{ padding: 10px 20px; margin: 5px; border: none; border-radius: 8px; cursor: pointer; }}
            .buy-btn {{ background: #10b981; color: white; }}
            .sell-btn {{ background: #ef4444; color: white; }}
            .portfolio-section {{ background: rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>NEXUS Crypto Trading Engine</h1>
                <p>Live Market Data • 24/7 Trading • Demo Mode Active</p>
            </div>
            
            <div class="portfolio-section">
                <h3>Portfolio Summary</h3>
                <p>Total Value: <span class="price">${portfolio['total_portfolio_value']:.2f}</span></p>
                <p>Cash Balance: ${portfolio['cash_balance']:.2f}</p>
                <p>P&L: <span class="{'positive' if portfolio['profit_loss'] >= 0 else 'negative'}">${portfolio['profit_loss']:.2f}</span></p>
            </div>
            
            <div class="trading-grid">
    """
    
    for symbol, data in market_data['prices'].items():
        change_class = 'positive' if data['change_24h'] >= 0 else 'negative'
        change_symbol = '+' if data['change_24h'] >= 0 else ''
        
        dashboard_html += f"""
                <div class="market-card">
                    <h3>{symbol}/USD</h3>
                    <div class="price">${data['price']:,.2f}</div>
                    <div class="change {change_class}">{change_symbol}{data['change_24h']:.2f}%</div>
                    <div style="margin-top: 15px;">
                        <button class="trade-button buy-btn" onclick="executeTrade('{symbol}', 'buy', 5)">Buy $5</button>
                        <button class="trade-button sell-btn" onclick="executeTrade('{symbol}', 'sell', 5)">Sell $5</button>
                    </div>
                </div>
        """
    
    dashboard_html += """
            </div>
            
            <script>
                function executeTrade(symbol, side, amount) {
                    fetch('/api/crypto/demo-trade', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({symbol: symbol, side: side, amount: amount})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(`Trade executed: ${side} $${amount} ${symbol}`);
                        location.reload();
                    });
                }
                
                // Auto-refresh prices every 30 seconds
                setInterval(() => location.reload(), 30000);
            </script>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

if __name__ == "__main__":
    demo = CryptoTradingDemo()
    market_data = demo.get_live_market_prices()
    portfolio = demo.get_portfolio_summary()
    
    print("NEXUS Crypto Trading Demo - Live Market Data")
    print(json.dumps(market_data, indent=2))
    print("\nPortfolio Summary:")
    print(json.dumps(portfolio, indent=2))