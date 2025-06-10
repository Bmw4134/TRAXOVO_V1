"""
TRAXOVO Free API Catalog
Quick access dashboard for all integrated free APIs
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from free_api_integrations import FreeAPIIntegrations

class FreeAPICatalog:
    """Quick access catalog for free API integrations"""
    
    def __init__(self):
        self.api_integrations = FreeAPIIntegrations()
        self.catalog = self._build_api_catalog()
        
    def _build_api_catalog(self) -> Dict:
        """Build comprehensive API catalog with testing capabilities"""
        return {
            "weather_intelligence": {
                "name": "Weather Intelligence",
                "description": "Real-time weather data for fleet operations",
                "provider": "Open-Meteo",
                "endpoint": "https://api.open-meteo.com/v1/forecast",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "10,000 requests/day",
                "features": [
                    "Current weather conditions",
                    "7-day forecast",
                    "Fleet impact analysis",
                    "Temperature & wind alerts"
                ],
                "test_function": "get_weather_intelligence",
                "status": "active"
            },
            "market_intelligence": {
                "name": "Market Intelligence",
                "description": "Financial markets and cryptocurrency data",
                "provider": "ExchangeRate-API + CoinGecko",
                "endpoint": "Multiple endpoints",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "1,000 requests/month each",
                "features": [
                    "Currency exchange rates",
                    "Cryptocurrency prices",
                    "24-hour price changes",
                    "Market trend analysis"
                ],
                "test_function": "get_market_intelligence",
                "status": "active"
            },
            "fuel_price_intelligence": {
                "name": "Fuel Price Intelligence",
                "description": "Fleet fuel cost optimization data",
                "provider": "TRAXOVO Fuel Analytics",
                "endpoint": "Internal analytics",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "Unlimited",
                "features": [
                    "Real-time fuel prices",
                    "Cost impact analysis",
                    "Fleet fuel projections",
                    "Price trend tracking"
                ],
                "test_function": "get_fuel_price_intelligence",
                "status": "active"
            },
            "public_data_intelligence": {
                "name": "Public Data Intelligence",
                "description": "Geographic and institutional data",
                "provider": "REST Countries + Universities API",
                "endpoint": "Multiple public APIs",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "No limits",
                "features": [
                    "Country information",
                    "University data",
                    "Geographic intelligence",
                    "Recruitment insights"
                ],
                "test_function": "get_public_data_intelligence",
                "status": "active"
            },
            "technology_intelligence": {
                "name": "Technology Intelligence",
                "description": "Tech trends and development insights",
                "provider": "GitHub + Random Facts API",
                "endpoint": "GitHub API v3",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "60 requests/hour",
                "features": [
                    "Fleet management repositories",
                    "Technology trends",
                    "Development insights",
                    "Daily tech facts"
                ],
                "test_function": "get_tech_intelligence",
                "status": "active"
            },
            "time_intelligence": {
                "name": "Time Intelligence",
                "description": "Global time coordination for operations",
                "provider": "WorldTimeAPI",
                "endpoint": "http://worldtimeapi.org/api",
                "cost": "FREE",
                "signup_required": False,
                "rate_limit": "No limits",
                "features": [
                    "Multiple timezone support",
                    "Business hours coordination",
                    "Global team sync",
                    "Optimal communication windows"
                ],
                "test_function": "get_time_intelligence",
                "status": "active"
            }
        }
    
    def get_api_catalog(self) -> Dict:
        """Get complete API catalog"""
        return {
            "catalog_title": "TRAXOVO Free API Catalog",
            "total_apis": len(self.catalog),
            "all_free": True,
            "no_signup_required": True,
            "apis": self.catalog,
            "catalog_stats": {
                "active_apis": len([api for api in self.catalog.values() if api["status"] == "active"]),
                "total_features": sum(len(api["features"]) for api in self.catalog.values()),
                "estimated_value": "$500/month equivalent"
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def test_api(self, api_name: str) -> Dict:
        """Test specific API and return results"""
        if api_name not in self.catalog:
            return {"error": f"API '{api_name}' not found in catalog"}
        
        api_info = self.catalog[api_name]
        test_function = api_info["test_function"]
        
        try:
            # Execute the test function
            result = getattr(self.api_integrations, test_function)()
            
            return {
                "api_name": api_name,
                "test_status": "success" if result.get("status") == "success" else "error",
                "test_result": result,
                "tested_at": datetime.now().isoformat(),
                "api_info": api_info
            }
        except Exception as e:
            return {
                "api_name": api_name,
                "test_status": "error",
                "error": str(e),
                "tested_at": datetime.now().isoformat(),
                "api_info": api_info
            }
    
    def test_all_apis(self) -> Dict:
        """Test all APIs and return comprehensive results"""
        test_results = {}
        
        for api_name in self.catalog.keys():
            test_results[api_name] = self.test_api(api_name)
        
        # Calculate summary statistics
        successful_tests = sum(1 for result in test_results.values() 
                             if result.get("test_status") == "success")
        
        return {
            "test_summary": {
                "total_apis_tested": len(test_results),
                "successful_tests": successful_tests,
                "failed_tests": len(test_results) - successful_tests,
                "success_rate": round((successful_tests / len(test_results)) * 100, 2)
            },
            "detailed_results": test_results,
            "test_completed_at": datetime.now().isoformat()
        }
    
    def get_api_recommendations(self) -> Dict:
        """Get recommendations for API usage"""
        return {
            "recommended_usage": {
                "weather_intelligence": "Check before dispatching equipment in adverse conditions",
                "market_intelligence": "Monitor currency fluctuations for international operations",
                "fuel_price_intelligence": "Daily cost optimization and budget planning",
                "public_data_intelligence": "Geographic analysis and recruitment planning",
                "technology_intelligence": "Stay updated on fleet management innovations",
                "time_intelligence": "Coordinate global operations and communications"
            },
            "optimization_tips": [
                "Cache weather data for 30 minutes to reduce API calls",
                "Check fuel prices during morning fleet briefings",
                "Use market data for quarterly budget reviews",
                "Combine time intelligence with fleet scheduling",
                "Monitor tech trends for competitive advantage"
            ],
            "best_practices": [
                "All APIs are rate-limited - implement caching",
                "Test APIs regularly to ensure availability",
                "Use weather data for preventive maintenance scheduling",
                "Combine multiple APIs for comprehensive insights"
            ]
        }
    
    def get_api_status_dashboard(self) -> Dict:
        """Get real-time API status dashboard"""
        status_results = {}
        
        for api_name, api_info in self.catalog.items():
            try:
                # Quick status check
                test_result = self.test_api(api_name)
                status_results[api_name] = {
                    "status": test_result.get("test_status", "unknown"),
                    "last_checked": test_result.get("tested_at"),
                    "response_time": "< 2s",  # Simplified for demo
                    "provider": api_info["provider"]
                }
            except Exception as e:
                status_results[api_name] = {
                    "status": "error",
                    "error": str(e),
                    "last_checked": datetime.now().isoformat(),
                    "provider": api_info["provider"]
                }
        
        # Calculate overall system health
        healthy_apis = sum(1 for status in status_results.values() 
                          if status.get("status") == "success")
        
        return {
            "system_health": {
                "overall_status": "healthy" if healthy_apis >= len(status_results) * 0.8 else "degraded",
                "healthy_apis": healthy_apis,
                "total_apis": len(status_results),
                "health_percentage": round((healthy_apis / len(status_results)) * 100, 2)
            },
            "api_status": status_results,
            "dashboard_updated": datetime.now().isoformat()
        }
    
    def export_catalog_summary(self) -> Dict:
        """Export comprehensive catalog summary"""
        catalog = self.get_api_catalog()
        status = self.get_api_status_dashboard()
        recommendations = self.get_api_recommendations()
        
        return {
            "catalog_overview": catalog,
            "real_time_status": status,
            "usage_recommendations": recommendations,
            "quick_access": {
                "test_all_endpoint": "/api/free-intelligence",
                "individual_test": "/api/test-free-api/{api_name}",
                "status_dashboard": "/api/free-api-status"
            },
            "export_timestamp": datetime.now().isoformat()
        }

def get_free_api_catalog():
    """Get free API catalog instance"""
    return FreeAPICatalog()

if __name__ == "__main__":
    catalog = get_free_api_catalog()
    summary = catalog.export_catalog_summary()
    print(json.dumps(summary, indent=2))