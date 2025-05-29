"""
AEMP (Association of Equipment Management Professionals) News Integration
Real-time industry news and updates for equipment management professionals
"""

import requests
from datetime import datetime, timedelta
import trafilatura
from flask import Blueprint, render_template, jsonify
import logging

aemp_bp = Blueprint('aemp_news', __name__)

class AEMPNewsService:
    """Service to fetch and process AEMP industry news"""
    
    def __init__(self):
        self.base_urls = [
            'https://www.aemp.org/news-events/news/',
            'https://www.equipmentworld.com/news/',
            'https://www.forconstructionpros.com/news/',
            'https://www.constructionequipment.com/news/'
        ]
    
    def fetch_industry_news(self):
        """Fetch latest industry news from AEMP and related sources"""
        news_articles = []
        
        for url in self.base_urls:
            try:
                # Fetch content from website
                downloaded = trafilatura.fetch_url(url)
                if downloaded:
                    text_content = trafilatura.extract(downloaded)
                    
                    # Extract relevant news items (simplified extraction)
                    if text_content:
                        articles = self._parse_news_content(text_content, url)
                        news_articles.extend(articles)
                        
            except Exception as e:
                logging.warning(f"Failed to fetch news from {url}: {e}")
                
        return news_articles[:10]  # Return top 10 most recent
    
    def _parse_news_content(self, content, source_url):
        """Parse news content into structured articles"""
        articles = []
        
        # Split content into potential articles
        sections = content.split('\n\n')
        
        for i, section in enumerate(sections[:5]):  # Limit to 5 per source
            if len(section) > 100:  # Minimum content length
                articles.append({
                    'title': self._extract_title(section),
                    'summary': section[:200] + '...' if len(section) > 200 else section,
                    'source': self._get_source_name(source_url),
                    'date': datetime.now() - timedelta(days=i),
                    'relevance': self._calculate_relevance(section),
                    'category': self._categorize_article(section)
                })
        
        return articles
    
    def _extract_title(self, content):
        """Extract potential title from content"""
        lines = content.split('\n')
        for line in lines:
            if 20 < len(line) < 80 and not line.startswith('http'):
                return line.strip()
        return "Industry Update"
    
    def _get_source_name(self, url):
        """Extract source name from URL"""
        if 'aemp.org' in url:
            return 'AEMP'
        elif 'equipmentworld.com' in url:
            return 'Equipment World'
        elif 'forconstructionpros.com' in url:
            return 'For Construction Pros'
        elif 'constructionequipment.com' in url:
            return 'Construction Equipment'
        return 'Industry Source'
    
    def _calculate_relevance(self, content):
        """Calculate relevance score based on keywords"""
        keywords = [
            'fleet management', 'equipment utilization', 'maintenance',
            'telematics', 'gps tracking', 'cost reduction', 'efficiency',
            'rental', 'lifecycle', 'productivity', 'ROI'
        ]
        
        content_lower = content.lower()
        score = sum(1 for keyword in keywords if keyword in content_lower)
        return min(score * 10, 100)  # Cap at 100%
    
    def _categorize_article(self, content):
        """Categorize article based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['maintenance', 'repair', 'service']):
            return 'Maintenance'
        elif any(word in content_lower for word in ['telematics', 'gps', 'tracking']):
            return 'Technology'
        elif any(word in content_lower for word in ['cost', 'budget', 'financial']):
            return 'Financial'
        elif any(word in content_lower for word in ['regulation', 'compliance', 'safety']):
            return 'Compliance'
        else:
            return 'General'

@aemp_bp.route('/industry-news')
def industry_news_dashboard():
    """AEMP Industry News Dashboard"""
    news_service = AEMPNewsService()
    news_articles = news_service.fetch_industry_news()
    
    return render_template('aemp_news_dashboard.html', 
                         news_articles=news_articles,
                         last_updated=datetime.now())

@aemp_bp.route('/api/industry-news')
def api_industry_news():
    """API endpoint for industry news data"""
    news_service = AEMPNewsService()
    news_articles = news_service.fetch_industry_news()
    
    return jsonify({
        'articles': news_articles,
        'count': len(news_articles),
        'last_updated': datetime.now().isoformat()
    })

def get_aemp_news_service():
    """Get the AEMP news service instance"""
    return AEMPNewsService()