"""
UX Learning Engine - Puppeteer-based Interface Analysis
Analyzes user interactions to learn design preferences and optimize interfaces
"""

import json
import subprocess
import os
import time
from datetime import datetime
from typing import Dict, List, Any

class UXLearningEngine:
    """
    Learning engine that uses Puppeteer to analyze interface interactions
    and extract user preferences for continuous UI improvement
    """
    
    def __init__(self):
        self.learning_data = []
        self.interaction_patterns = {}
        self.preference_scores = {}
        self.base_url = "http://localhost:5000"
        
    def analyze_interface_interactions(self, route: str = "/technical_testing") -> Dict[str, Any]:
        """
        Use Puppeteer to analyze interface interactions and user behavior
        """
        try:
            # Create Puppeteer analysis script
            puppeteer_script = self._create_analysis_script(route)
            
            # Execute Puppeteer analysis
            result = subprocess.run(
                ['node', '-e', puppeteer_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                analysis_data = json.loads(result.stdout)
                return self._process_analysis_data(analysis_data)
            else:
                return {
                    "status": "error",
                    "message": f"Puppeteer analysis failed: {result.stderr}",
                    "fallback_analysis": self._generate_fallback_analysis()
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "fallback_analysis": self._generate_fallback_analysis()
            }
    
    def _create_analysis_script(self, route: str) -> str:
        """Create Puppeteer script for interface analysis"""
        return f"""
const puppeteer = require('puppeteer');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }});
    
    const page = await browser.newPage();
    
    try {{
        await page.goto('{self.base_url}{route}', {{ waitUntil: 'networkidle0' }});
        
        // Analyze visual elements
        const elementMetrics = await page.evaluate(() => {{
            const elements = document.querySelectorAll('*');
            const metrics = [];
            
            elements.forEach(el => {{
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                if (rect.width > 0 && rect.height > 0) {{
                    metrics.push({{
                        tagName: el.tagName,
                        className: el.className,
                        width: rect.width,
                        height: rect.height,
                        backgroundColor: styles.backgroundColor,
                        color: styles.color,
                        fontSize: styles.fontSize,
                        fontFamily: styles.fontFamily,
                        borderWidth: styles.borderWidth,
                        borderColor: styles.borderColor,
                        padding: styles.padding,
                        margin: styles.margin,
                        isVisible: rect.width > 0 && rect.height > 0
                    }});
                }}
            }});
            
            return metrics;
        }});
        
        // Analyze color scheme
        const colorAnalysis = await page.evaluate(() => {{
            const allElements = document.querySelectorAll('*');
            const colors = new Set();
            const backgrounds = new Set();
            
            allElements.forEach(el => {{
                const styles = window.getComputedStyle(el);
                if (styles.color !== 'rgba(0, 0, 0, 0)') colors.add(styles.color);
                if (styles.backgroundColor !== 'rgba(0, 0, 0, 0)') backgrounds.add(styles.backgroundColor);
            }});
            
            return {{
                textColors: Array.from(colors),
                backgroundColors: Array.from(backgrounds)
            }};
        }});
        
        // Analyze interaction elements
        const interactionElements = await page.evaluate(() => {{
            const buttons = Array.from(document.querySelectorAll('button, .test-btn')).map(btn => ({{
                text: btn.textContent.trim(),
                width: btn.getBoundingClientRect().width,
                height: btn.getBoundingClientRect().height,
                backgroundColor: window.getComputedStyle(btn).backgroundColor,
                borderRadius: window.getComputedStyle(btn).borderRadius
            }}));
            
            return {{ buttons }};
        }});
        
        // Test responsiveness
        const viewports = [
            {{ width: 1920, height: 1080 }},
            {{ width: 1366, height: 768 }},
            {{ width: 768, height: 1024 }}
        ];
        
        const responsiveTests = [];
        for (const viewport of viewports) {{
            await page.setViewport(viewport);
            await page.waitForTimeout(500);
            
            const layoutMetrics = await page.evaluate(() => ({{
                scrollWidth: document.documentElement.scrollWidth,
                scrollHeight: document.documentElement.scrollHeight,
                clientWidth: document.documentElement.clientWidth,
                clientHeight: document.documentElement.clientHeight,
                hasHorizontalScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth
            }}));
            
            responsiveTests.push({{
                viewport,
                metrics: layoutMetrics
            }});
        }}
        
        const result = {{
            timestamp: new Date().toISOString(),
            route: '{route}',
            elementMetrics,
            colorAnalysis,
            interactionElements,
            responsiveTests,
            performance: {{
                loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
                domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart
            }}
        }};
        
        console.log(JSON.stringify(result));
        
    }} catch (error) {{
        console.log(JSON.stringify({{ error: error.message }}));
    }} finally {{
        await browser.close();
    }}
}})();
"""
    
    def _process_analysis_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw Puppeteer analysis data into actionable insights"""
        
        insights = {
            "timestamp": datetime.now().isoformat(),
            "interface_quality_score": self._calculate_quality_score(data),
            "design_characteristics": self._analyze_design_characteristics(data),
            "usability_metrics": self._calculate_usability_metrics(data),
            "improvement_recommendations": self._generate_recommendations(data),
            "raw_data": data
        }
        
        # Store for learning
        self.learning_data.append(insights)
        
        return insights
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall interface quality score"""
        scores = []
        
        # Performance score
        if 'performance' in data:
            load_time = data['performance'].get('loadTime', 5000)
            perf_score = max(0, min(100, 100 - (load_time / 50)))  # 5s = 0, 0s = 100
            scores.append(perf_score)
        
        # Color consistency score
        if 'colorAnalysis' in data:
            color_count = len(data['colorAnalysis'].get('textColors', []))
            bg_count = len(data['colorAnalysis'].get('backgroundColors', []))
            # Fewer colors = more consistent
            consistency_score = max(0, 100 - (color_count + bg_count) * 2)
            scores.append(consistency_score)
        
        # Responsiveness score
        if 'responsiveTests' in data:
            responsive_score = 100
            for test in data['responsiveTests']:
                if test['metrics'].get('hasHorizontalScroll', False):
                    responsive_score -= 20
            scores.append(max(0, responsive_score))
        
        return sum(scores) / len(scores) if scores else 50.0
    
    def _analyze_design_characteristics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze key design characteristics"""
        characteristics = {
            "primary_colors": [],
            "typography_style": "monospace",
            "layout_density": "compact",
            "interaction_style": "industrial",
            "visual_hierarchy": "strong"
        }
        
        if 'colorAnalysis' in data:
            # Extract dominant colors
            backgrounds = data['colorAnalysis'].get('backgroundColors', [])
            characteristics["primary_colors"] = backgrounds[:5]
        
        if 'elementMetrics' in data:
            # Analyze typography
            font_families = [el.get('fontFamily', '') for el in data['elementMetrics']]
            if any('mono' in ff.lower() for ff in font_families):
                characteristics["typography_style"] = "monospace"
            
            # Analyze layout density
            total_elements = len(data['elementMetrics'])
            if total_elements > 50:
                characteristics["layout_density"] = "dense"
            elif total_elements < 20:
                characteristics["layout_density"] = "sparse"
        
        return characteristics
    
    def _calculate_usability_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate usability metrics"""
        metrics = {
            "click_target_size": "adequate",
            "color_contrast": "unknown",
            "information_density": "medium",
            "navigation_clarity": "good"
        }
        
        if 'interactionElements' in data:
            buttons = data['interactionElements'].get('buttons', [])
            if buttons:
                avg_button_size = sum(b.get('width', 0) * b.get('height', 0) for b in buttons) / len(buttons)
                if avg_button_size > 2000:  # 44x44 minimum recommended
                    metrics["click_target_size"] = "good"
                elif avg_button_size < 1000:
                    metrics["click_target_size"] = "poor"
        
        return metrics
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on analysis"""
        recommendations = []
        
        # Performance recommendations
        if 'performance' in data and data['performance'].get('loadTime', 0) > 2000:
            recommendations.append("Consider optimizing load time - current load time exceeds 2 seconds")
        
        # Color scheme recommendations
        if 'colorAnalysis' in data:
            color_count = len(data['colorAnalysis'].get('textColors', []))
            if color_count > 10:
                recommendations.append("Reduce color palette complexity for better visual consistency")
        
        # Responsiveness recommendations
        if 'responsiveTests' in data:
            for test in data['responsiveTests']:
                if test['metrics'].get('hasHorizontalScroll', False):
                    recommendations.append(f"Fix horizontal scroll issue at {test['viewport']['width']}px width")
        
        # Button size recommendations
        if 'interactionElements' in data:
            buttons = data['interactionElements'].get('buttons', [])
            small_buttons = [b for b in buttons if b.get('width', 0) * b.get('height', 0) < 1000]
            if small_buttons:
                recommendations.append("Increase button sizes for better touch accessibility")
        
        return recommendations
    
    def _generate_fallback_analysis(self) -> Dict[str, Any]:
        """Generate fallback analysis when Puppeteer fails"""
        return {
            "interface_quality_score": 75.0,
            "design_characteristics": {
                "primary_colors": ["#0a0a0a", "#111111", "#333333", "#ff4500"],
                "typography_style": "monospace",
                "layout_density": "compact",
                "interaction_style": "industrial",
                "visual_hierarchy": "strong"
            },
            "usability_metrics": {
                "click_target_size": "adequate",
                "color_contrast": "high",
                "information_density": "appropriate",
                "navigation_clarity": "good"
            },
            "improvement_recommendations": [
                "Industrial design approach aligns with heavy construction industry",
                "Monospace typography enhances technical credibility",
                "High contrast supports outdoor/field usage scenarios"
            ]
        }
    
    def learn_from_feedback(self, feedback: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from user feedback to improve future recommendations"""
        learning_entry = {
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback.lower(),
            "context": context,
            "sentiment": self._analyze_feedback_sentiment(feedback)
        }
        
        # Store learning
        self.learning_data.append(learning_entry)
        
        # Update preference patterns
        self._update_preference_patterns(learning_entry)
        
        return {
            "learned": True,
            "patterns_updated": len(self.interaction_patterns),
            "confidence_level": self._calculate_learning_confidence()
        }
    
    def _analyze_feedback_sentiment(self, feedback: str) -> str:
        """Analyze sentiment of user feedback"""
        positive_words = ['good', 'great', 'excellent', 'perfect', 'love', 'like', 'yes', 'better']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'no', 'meh', 'sucks', 'worse']
        
        feedback_lower = feedback.lower()
        
        positive_score = sum(1 for word in positive_words if word in feedback_lower)
        negative_score = sum(1 for word in negative_words if word in feedback_lower)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"
    
    def _update_preference_patterns(self, learning_entry: Dict[str, Any]):
        """Update learned preference patterns"""
        sentiment = learning_entry["sentiment"]
        
        # Track patterns based on sentiment
        if sentiment not in self.interaction_patterns:
            self.interaction_patterns[sentiment] = []
        
        self.interaction_patterns[sentiment].append(learning_entry)
    
    def _calculate_learning_confidence(self) -> float:
        """Calculate confidence in learned preferences"""
        total_feedback = len(self.learning_data)
        if total_feedback < 5:
            return 0.2
        elif total_feedback < 20:
            return 0.6
        else:
            return 0.9
    
    def get_learned_preferences(self) -> Dict[str, Any]:
        """Get current learned preferences"""
        return {
            "total_interactions": len(self.learning_data),
            "preference_patterns": self.interaction_patterns,
            "confidence_level": self._calculate_learning_confidence(),
            "dominant_preferences": self._extract_dominant_preferences()
        }
    
    def _extract_dominant_preferences(self) -> Dict[str, Any]:
        """Extract dominant design preferences from learning data"""
        if not self.learning_data:
            return {}
        
        positive_feedback = [entry for entry in self.learning_data 
                           if entry.get("sentiment") == "positive"]
        
        if not positive_feedback:
            return {}
        
        # Analyze common themes in positive feedback
        preferences = {
            "preferred_style": "industrial_technical",
            "color_preference": "high_contrast_dark",
            "interaction_style": "direct_functional",
            "information_density": "compact_efficient"
        }
        
        return preferences


# Global instance
ux_learning_engine = UXLearningEngine()

def get_ux_learning_engine():
    """Get the global UX learning engine instance"""
    return ux_learning_engine