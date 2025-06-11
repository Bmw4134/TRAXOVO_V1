"""
TRAXOVO Interactive API Explorer with Code Snippet Generator
Personalized API recommendations with real-time code generation
"""

import json
from typing import Dict, List, Any
from datetime import datetime


class InteractiveAPIExplorer:
    """Interactive API explorer with personalized recommendations and code generation"""
    
    def __init__(self):
        self.api_catalog = self.load_comprehensive_api_catalog()
        self.user_preferences = {}
        
    def load_comprehensive_api_catalog(self) -> Dict:
        """Load comprehensive API catalog with real endpoints"""
        return {
            "weather": {
                "apis": [
                    {
                        "name": "OpenWeatherMap",
                        "description": "Comprehensive weather data for fleet planning",
                        "base_url": "https://api.openweathermap.org/data/2.5",
                        "auth_type": "api_key",
                        "pricing": "Free tier: 1000 calls/day",
                        "endpoints": [
                            {
                                "path": "/weather",
                                "method": "GET",
                                "description": "Current weather data",
                                "parameters": [
                                    {"name": "q", "type": "string", "required": True, "description": "City name"},
                                    {"name": "appid", "type": "string", "required": True, "description": "API key"},
                                    {"name": "units", "type": "string", "required": False, "description": "Temperature units"}
                                ]
                            },
                            {
                                "path": "/forecast",
                                "method": "GET", 
                                "description": "5-day weather forecast",
                                "parameters": [
                                    {"name": "q", "type": "string", "required": True, "description": "City name"},
                                    {"name": "appid", "type": "string", "required": True, "description": "API key"}
                                ]
                            }
                        ],
                        "use_cases": ["Route planning", "Equipment deployment", "Safety planning"],
                        "integration_difficulty": "Easy",
                        "reliability_score": 95
                    },
                    {
                        "name": "WeatherAPI",
                        "description": "Alternative weather service with forecast data",
                        "base_url": "https://api.weatherapi.com/v1",
                        "auth_type": "api_key",
                        "pricing": "Free tier: 1M calls/month",
                        "endpoints": [
                            {
                                "path": "/current.json",
                                "method": "GET",
                                "description": "Real-time weather",
                                "parameters": [
                                    {"name": "key", "type": "string", "required": True, "description": "API key"},
                                    {"name": "q", "type": "string", "required": True, "description": "Location query"}
                                ]
                            }
                        ],
                        "use_cases": ["Real-time monitoring", "Fleet dispatch"],
                        "integration_difficulty": "Easy",
                        "reliability_score": 92
                    }
                ]
            },
            "geolocation": {
                "apis": [
                    {
                        "name": "Google Geocoding API",
                        "description": "Convert addresses to coordinates and vice versa",
                        "base_url": "https://maps.googleapis.com/maps/api",
                        "auth_type": "api_key",
                        "pricing": "$5 per 1000 requests",
                        "endpoints": [
                            {
                                "path": "/geocode/json",
                                "method": "GET",
                                "description": "Geocode addresses",
                                "parameters": [
                                    {"name": "address", "type": "string", "required": True, "description": "Address to geocode"},
                                    {"name": "key", "type": "string", "required": True, "description": "API key"}
                                ]
                            }
                        ],
                        "use_cases": ["Asset tracking", "Route optimization", "Service area mapping"],
                        "integration_difficulty": "Medium",
                        "reliability_score": 98
                    },
                    {
                        "name": "Nominatim (OpenStreetMap)",
                        "description": "Free geocoding service",
                        "base_url": "https://nominatim.openstreetmap.org",
                        "auth_type": "none",
                        "pricing": "Free with rate limits",
                        "endpoints": [
                            {
                                "path": "/search",
                                "method": "GET",
                                "description": "Search for locations",
                                "parameters": [
                                    {"name": "q", "type": "string", "required": True, "description": "Search query"},
                                    {"name": "format", "type": "string", "required": True, "description": "Response format (json)"}
                                ]
                            }
                        ],
                        "use_cases": ["Basic geocoding", "Address validation"],
                        "integration_difficulty": "Easy",
                        "reliability_score": 85
                    }
                ]
            },
            "financial": {
                "apis": [
                    {
                        "name": "Alpha Vantage",
                        "description": "Financial market data and currency exchange",
                        "base_url": "https://www.alphavantage.co/query",
                        "auth_type": "api_key",
                        "pricing": "Free tier: 5 calls/minute",
                        "endpoints": [
                            {
                                "path": "",
                                "method": "GET",
                                "description": "Currency exchange rates",
                                "parameters": [
                                    {"name": "function", "type": "string", "required": True, "description": "API function"},
                                    {"name": "from_currency", "type": "string", "required": True, "description": "From currency"},
                                    {"name": "to_currency", "type": "string", "required": True, "description": "To currency"},
                                    {"name": "apikey", "type": "string", "required": True, "description": "API key"}
                                ]
                            }
                        ],
                        "use_cases": ["Currency conversion", "Cost tracking", "International operations"],
                        "integration_difficulty": "Medium",
                        "reliability_score": 93
                    }
                ]
            },
            "fuel_prices": {
                "apis": [
                    {
                        "name": "GasBuddy API",
                        "description": "Real-time fuel prices for fleet cost optimization",
                        "base_url": "https://api.gasbuddy.com/v3",
                        "auth_type": "api_key",
                        "pricing": "Contact for pricing",
                        "endpoints": [
                            {
                                "path": "/station-finder",
                                "method": "GET",
                                "description": "Find nearby gas stations",
                                "parameters": [
                                    {"name": "lat", "type": "number", "required": True, "description": "Latitude"},
                                    {"name": "lng", "type": "number", "required": True, "description": "Longitude"},
                                    {"name": "radius", "type": "number", "required": False, "description": "Search radius"}
                                ]
                            }
                        ],
                        "use_cases": ["Fleet fuel optimization", "Route cost calculation"],
                        "integration_difficulty": "Medium",
                        "reliability_score": 88
                    }
                ]
            },
            "communication": {
                "apis": [
                    {
                        "name": "Twilio",
                        "description": "SMS and voice communication for fleet alerts",
                        "base_url": "https://api.twilio.com/2010-04-01",
                        "auth_type": "basic_auth",
                        "pricing": "$0.0075 per SMS",
                        "endpoints": [
                            {
                                "path": "/Accounts/{AccountSid}/Messages.json",
                                "method": "POST",
                                "description": "Send SMS message",
                                "parameters": [
                                    {"name": "To", "type": "string", "required": True, "description": "Recipient phone number"},
                                    {"name": "From", "type": "string", "required": True, "description": "Twilio phone number"},
                                    {"name": "Body", "type": "string", "required": True, "description": "Message content"}
                                ]
                            }
                        ],
                        "use_cases": ["Emergency alerts", "Driver notifications", "Maintenance reminders"],
                        "integration_difficulty": "Medium",
                        "reliability_score": 99
                    }
                ]
            },
            "productivity": {
                "apis": [
                    {
                        "name": "Google Sheets API",
                        "description": "Integrate with spreadsheets for data management",
                        "base_url": "https://sheets.googleapis.com/v4",
                        "auth_type": "oauth2",
                        "pricing": "Free with limits",
                        "endpoints": [
                            {
                                "path": "/spreadsheets/{spreadsheetId}/values/{range}",
                                "method": "GET",
                                "description": "Read spreadsheet data",
                                "parameters": [
                                    {"name": "spreadsheetId", "type": "string", "required": True, "description": "Spreadsheet ID"},
                                    {"name": "range", "type": "string", "required": True, "description": "Cell range"}
                                ]
                            }
                        ],
                        "use_cases": ["Data import/export", "Report generation", "Asset tracking"],
                        "integration_difficulty": "Hard",
                        "reliability_score": 97
                    }
                ]
            }
        }
    
    def get_personalized_recommendations(self, user_profile: Dict) -> Dict:
        """Generate personalized API recommendations based on user profile"""
        industry = user_profile.get("industry", "general")
        use_cases = user_profile.get("use_cases", [])
        budget = user_profile.get("budget", "free")
        technical_level = user_profile.get("technical_level", "intermediate")
        
        recommendations = {
            "high_priority": [],
            "recommended": [],
            "budget_friendly": [],
            "advanced_options": []
        }
        
        for category, data in self.api_catalog.items():
            for api in data["apis"]:
                score = self.calculate_api_score(api, user_profile)
                
                recommendation = {
                    "api": api,
                    "category": category,
                    "score": score,
                    "reason": self.get_recommendation_reason(api, user_profile)
                }
                
                if score >= 90:
                    recommendations["high_priority"].append(recommendation)
                elif score >= 75:
                    recommendations["recommended"].append(recommendation)
                elif api["pricing"].lower().startswith("free"):
                    recommendations["budget_friendly"].append(recommendation)
                elif api["integration_difficulty"] == "Hard":
                    recommendations["advanced_options"].append(recommendation)
        
        # Sort by score
        for key in recommendations:
            recommendations[key].sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations
    
    def calculate_api_score(self, api: Dict, user_profile: Dict) -> int:
        """Calculate API recommendation score based on user profile"""
        score = api["reliability_score"]
        
        # Budget consideration
        budget = user_profile.get("budget", "free")
        if budget == "free" and "free" in api["pricing"].lower():
            score += 10
        elif budget == "low" and any(keyword in api["pricing"].lower() for keyword in ["free", "$0.", "cheap"]):
            score += 5
        
        # Technical level consideration
        tech_level = user_profile.get("technical_level", "intermediate")
        difficulty = api["integration_difficulty"]
        
        if tech_level == "beginner" and difficulty == "Easy":
            score += 10
        elif tech_level == "intermediate" and difficulty in ["Easy", "Medium"]:
            score += 5
        elif tech_level == "advanced":
            score += 3
        
        # Use case matching
        user_cases = set(user_profile.get("use_cases", []))
        api_cases = set(api.get("use_cases", []))
        
        if user_cases.intersection(api_cases):
            score += 15
        
        return min(100, max(0, score))
    
    def get_recommendation_reason(self, api: Dict, user_profile: Dict) -> str:
        """Generate explanation for API recommendation"""
        reasons = []
        
        if api["reliability_score"] >= 95:
            reasons.append("Highly reliable service")
        
        budget = user_profile.get("budget", "free")
        if budget == "free" and "free" in api["pricing"].lower():
            reasons.append("Fits your free budget")
        
        tech_level = user_profile.get("technical_level", "intermediate")
        if tech_level == "beginner" and api["integration_difficulty"] == "Easy":
            reasons.append("Easy to integrate for beginners")
        
        user_cases = set(user_profile.get("use_cases", []))
        api_cases = set(api.get("use_cases", []))
        matches = user_cases.intersection(api_cases)
        
        if matches:
            reasons.append(f"Perfect for {', '.join(list(matches)[:2])}")
        
        return "; ".join(reasons) if reasons else "Good general-purpose option"
    
    def generate_code_snippet(self, api: Dict, endpoint: Dict, language: str = "python") -> Dict:
        """Generate code snippets for API integration"""
        
        if language.lower() == "python":
            return self.generate_python_snippet(api, endpoint)
        elif language.lower() == "javascript":
            return self.generate_javascript_snippet(api, endpoint)
        elif language.lower() == "curl":
            return self.generate_curl_snippet(api, endpoint)
        else:
            return {"error": "Unsupported language"}
    
    def generate_python_snippet(self, api: Dict, endpoint: Dict) -> Dict:
        """Generate Python code snippet"""
        
        # Build URL
        base_url = api["base_url"]
        path = endpoint["path"]
        full_url = f"{base_url}{path}"
        
        # Build parameters
        params = []
        headers = []
        
        for param in endpoint.get("parameters", []):
            if param["name"] in ["key", "appid", "apikey"]:
                params.append(f'    "{param["name"]}": "YOUR_API_KEY"')
            elif param["required"]:
                if param["type"] == "string":
                    params.append(f'    "{param["name"]}": "example_value"')
                elif param["type"] == "number":
                    params.append(f'    "{param["name"]}": 0')
        
        if api["auth_type"] == "basic_auth":
            headers.append('    "Authorization": "Basic YOUR_ENCODED_CREDENTIALS"')
        
        params_str = ",\n".join(params)
        headers_str = ",\n".join(headers) if headers else ""
        
        code = f'''import requests

# {api["name"]} - {endpoint["description"]}
url = "{full_url}"

params = {{
{params_str}
}}
'''
        
        if headers_str:
            code += f'''
headers = {{
{headers_str}
}}

response = requests.{endpoint["method"].lower()}(url, params=params, headers=headers)
'''
        else:
            code += f'''
response = requests.{endpoint["method"].lower()}(url, params=params)
'''
        
        code += '''
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
'''
        
        return {
            "language": "python",
            "code": code,
            "dependencies": ["requests"],
            "notes": [
                "Replace YOUR_API_KEY with your actual API key",
                "Handle errors appropriately in production",
                "Consider rate limiting for API calls"
            ]
        }
    
    def generate_javascript_snippet(self, api: Dict, endpoint: Dict) -> Dict:
        """Generate JavaScript code snippet"""
        
        base_url = api["base_url"]
        path = endpoint["path"]
        full_url = f"{base_url}{path}"
        
        # Build query parameters
        params = []
        for param in endpoint.get("parameters", []):
            if param["name"] in ["key", "appid", "apikey"]:
                params.append(f'{param["name"]}=YOUR_API_KEY')
            elif param["required"]:
                if param["type"] == "string":
                    params.append(f'{param["name"]}=example_value')
                elif param["type"] == "number":
                    params.append(f'{param["name"]}=0')
        
        query_string = "&".join(params)
        
        code = f'''// {api["name"]} - {endpoint["description"]}
const apiUrl = "{full_url}?{query_string}";

async function fetch{api["name"].replace(" ", "")}Data() {{
    try {{
        const response = await fetch(apiUrl);
        
        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}
        
        const data = await response.json();
        console.log(data);
        return data;
        
    }} catch (error) {{
        console.error('Error fetching data:', error);
        throw error;
    }}
}}

// Call the function
fetch{api["name"].replace(" ", "")}Data()
    .then(data => {{
        // Process your data here
        console.log('Success:', data);
    }})
    .catch(error => {{
        console.error('Failed to fetch data:', error);
    }});
'''
        
        return {
            "language": "javascript",
            "code": code,
            "dependencies": ["fetch API (modern browsers)"],
            "notes": [
                "Replace YOUR_API_KEY with your actual API key",
                "This uses modern async/await syntax",
                "Consider using axios for older browser support"
            ]
        }
    
    def generate_curl_snippet(self, api: Dict, endpoint: Dict) -> Dict:
        """Generate cURL command snippet"""
        
        base_url = api["base_url"]
        path = endpoint["path"]
        full_url = f"{base_url}{path}"
        
        # Build parameters
        params = []
        for param in endpoint.get("parameters", []):
            if param["name"] in ["key", "appid", "apikey"]:
                params.append(f'{param["name"]}=YOUR_API_KEY')
            elif param["required"]:
                if param["type"] == "string":
                    params.append(f'{param["name"]}=example_value')
                elif param["type"] == "number":
                    params.append(f'{param["name"]}=0')
        
        if endpoint["method"].upper() == "GET":
            query_string = "&".join(params)
            code = f'''# {api["name"]} - {endpoint["description"]}
curl -X GET "{full_url}?{query_string}" \\
     -H "Content-Type: application/json"'''
        else:
            data = "{" + ", ".join([f'"{p.split("=")[0]}": "{p.split("=")[1]}"' for p in params]) + "}"
            code = f'''# {api["name"]} - {endpoint["description"]}
curl -X {endpoint["method"].upper()} "{full_url}" \\
     -H "Content-Type: application/json" \\
     -d '{data}' '''
        
        if api["auth_type"] == "basic_auth":
            code += ' \\\n     -u "username:password"'
        
        return {
            "language": "curl",
            "code": code,
            "dependencies": ["curl"],
            "notes": [
                "Replace YOUR_API_KEY with your actual API key",
                "Replace username:password with actual credentials if using basic auth",
                "Use -v flag for verbose output during testing"
            ]
        }
    
    def get_api_explorer_interface(self) -> Dict:
        """Get complete API explorer interface data"""
        return {
            "categories": list(self.api_catalog.keys()),
            "total_apis": sum(len(cat["apis"]) for cat in self.api_catalog.values()),
            "featured_apis": self.get_featured_apis(),
            "code_languages": ["python", "javascript", "curl"],
            "integration_tips": self.get_integration_tips()
        }
    
    def get_featured_apis(self) -> List[Dict]:
        """Get featured APIs based on reliability and ease of use"""
        featured = []
        
        for category, data in self.api_catalog.items():
            for api in data["apis"]:
                if api["reliability_score"] >= 95 and api["integration_difficulty"] in ["Easy", "Medium"]:
                    featured.append({
                        "name": api["name"],
                        "category": category,
                        "description": api["description"],
                        "reliability_score": api["reliability_score"],
                        "pricing": api["pricing"]
                    })
        
        return sorted(featured, key=lambda x: x["reliability_score"], reverse=True)[:6]
    
    def get_integration_tips(self) -> List[str]:
        """Get general API integration tips"""
        return [
            "Always store API keys securely using environment variables",
            "Implement proper error handling for network requests",
            "Respect API rate limits to avoid service interruption",
            "Use caching for frequently requested data",
            "Monitor API usage and costs regularly",
            "Keep API documentation bookmarked for reference",
            "Test APIs in development before production deployment",
            "Implement retry logic for transient failures"
        ]


def get_interactive_api_explorer():
    """Get interactive API explorer instance"""
    return InteractiveAPIExplorer()