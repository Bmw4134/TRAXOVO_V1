"""
Weather Integration for TRAXOVO Fleet Management
Provides weather alerts and forecasts for North Texas job sites
"""

import requests
import json
from datetime import datetime
import logging

class WeatherIntegration:
    """
    Weather service integration for construction site planning
    """
    
    def __init__(self):
        self.weather_api_key = None  # Will need API key from user
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_job_site_weather(self, lat, lng):
        """
        Get current weather conditions for a specific job site
        """
        if not self.weather_api_key:
            return {"error": "Weather API key required"}
            
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lng,
                'appid': self.weather_api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params)
            weather_data = response.json()
            
            return {
                'temperature': weather_data['main']['temp'],
                'conditions': weather_data['weather'][0]['description'],
                'wind_speed': weather_data['wind']['speed'],
                'visibility': weather_data.get('visibility', 'N/A')
            }
            
        except Exception as e:
            logging.error(f"Weather API error: {e}")
            return {"error": "Weather data unavailable"}
    
    def check_severe_weather_alerts(self, lat, lng):
        """
        Check for severe weather that could affect equipment operations
        """
        weather = self.get_job_site_weather(lat, lng)
        
        alerts = []
        
        # Check for dangerous conditions
        if isinstance(weather.get('wind_speed'), (int, float)) and weather['wind_speed'] > 25:
            alerts.append("High wind warning - secure equipment")
            
        if 'rain' in weather.get('conditions', '').lower():
            alerts.append("Rain detected - monitor equipment safety")
            
        return alerts
    
    def get_north_texas_forecast(self):
        """
        Get weather forecast for all North Texas regions
        """
        regions = {
            'DFW': (32.7767, -96.7970),
            'Houston': (29.7604, -95.3698),
            'West_Texas': (31.9974, -102.0779)
        }
        
        forecasts = {}
        
        for region, (lat, lng) in regions.items():
            forecasts[region] = self.get_job_site_weather(lat, lng)
            
        return forecasts
