"""
TRAXOVO One-Click API Performance Benchmark Tool
Real-time API performance testing with personalized recommendations
"""

import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import Dict, List, Any
import statistics


class APIPerformanceBenchmark:
    """One-click API performance benchmark with intelligent recommendations"""
    
    def __init__(self):
        self.test_apis = self.get_benchmark_apis()
        self.results = {}
        self.recommendations = {}
        
    def get_benchmark_apis(self) -> List[Dict]:
        """Get comprehensive API test suite for benchmarking"""
        return [
            {
                "name": "JSONPlaceholder",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "method": "GET",
                "category": "data",
                "use_case": "Mock data for development",
                "expected_response_time": 200
            },
            {
                "name": "HTTP Bin Echo",
                "url": "https://httpbin.org/delay/1",
                "method": "GET", 
                "category": "testing",
                "use_case": "API testing and debugging",
                "expected_response_time": 1100
            },
            {
                "name": "REST Countries",
                "url": "https://restcountries.com/v3.1/name/united",
                "method": "GET",
                "category": "geographic",
                "use_case": "Geographic and country data",
                "expected_response_time": 300
            },
            {
                "name": "OpenWeatherMap Sample",
                "url": "https://samples.openweathermap.org/data/2.5/weather?q=London,uk&appid=b6907d289e10d714a6e88b30761fae22",
                "method": "GET",
                "category": "weather",
                "use_case": "Weather data for fleet planning",
                "expected_response_time": 400
            },
            {
                "name": "GitHub API",
                "url": "https://api.github.com/users/octocat",
                "method": "GET",
                "category": "development",
                "use_case": "Developer tools integration",
                "expected_response_time": 250
            },
            {
                "name": "CoinGecko Crypto",
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                "method": "GET",
                "category": "financial",
                "use_case": "Cryptocurrency and financial data",
                "expected_response_time": 350
            },
            {
                "name": "Random Quote",
                "url": "https://api.quotable.io/random",
                "method": "GET",
                "category": "content",
                "use_case": "Content generation and inspiration",
                "expected_response_time": 300
            },
            {
                "name": "Cat Facts",
                "url": "https://cat-fact.herokuapp.com/facts/random",
                "method": "GET",
                "category": "fun",
                "use_case": "Fun content for user engagement",
                "expected_response_time": 500
            }
        ]
    
    async def benchmark_single_api(self, session: aiohttp.ClientSession, api: Dict) -> Dict:
        """Benchmark a single API endpoint with comprehensive metrics"""
        results = {
            "name": api["name"],
            "url": api["url"],
            "category": api["category"],
            "use_case": api["use_case"],
            "tests": [],
            "avg_response_time": 0,
            "success_rate": 0,
            "reliability_score": 0,
            "recommendation": "",
            "status": "unknown"
        }
        
        response_times = []
        successful_requests = 0
        total_requests = 5
        
        for i in range(total_requests):
            try:
                start_time = time.time()
                
                async with session.get(api["url"], timeout=aiohttp.ClientTimeout(total=10)) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    test_result = {
                        "attempt": i + 1,
                        "response_time": round(response_time, 2),
                        "status_code": response.status,
                        "success": response.status == 200,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results["tests"].append(test_result)
                    
                    if response.status == 200:
                        successful_requests += 1
                        response_times.append(response_time)
                        
            except Exception as e:
                test_result = {
                    "attempt": i + 1,
                    "response_time": 0,
                    "status_code": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results["tests"].append(test_result)
        
        # Calculate metrics
        if response_times:
            results["avg_response_time"] = round(statistics.mean(response_times), 2)
            results["min_response_time"] = round(min(response_times), 2)
            results["max_response_time"] = round(max(response_times), 2)
        
        results["success_rate"] = round((successful_requests / total_requests) * 100, 1)
        
        # Calculate reliability score
        results["reliability_score"] = self.calculate_reliability_score(results, api)
        
        # Generate recommendation
        results["recommendation"] = self.generate_api_recommendation(results, api)
        
        # Set status
        if results["success_rate"] >= 80 and results["avg_response_time"] <= api["expected_response_time"] * 1.5:
            results["status"] = "excellent"
        elif results["success_rate"] >= 60 and results["avg_response_time"] <= api["expected_response_time"] * 2:
            results["status"] = "good"
        elif results["success_rate"] >= 40:
            results["status"] = "fair"
        else:
            results["status"] = "poor"
            
        return results
    
    def calculate_reliability_score(self, results: Dict, api: Dict) -> float:
        """Calculate API reliability score based on multiple factors"""
        success_factor = results["success_rate"] / 100
        
        if results["avg_response_time"] > 0:
            speed_factor = min(1.0, api["expected_response_time"] / results["avg_response_time"])
        else:
            speed_factor = 0
            
        # Consistency factor based on response time variance
        if len([t for t in results["tests"] if t["success"]]) > 1:
            response_times = [t["response_time"] for t in results["tests"] if t["success"] and t["response_time"] > 0]
            if response_times:
                variance = statistics.variance(response_times) if len(response_times) > 1 else 0
                consistency_factor = max(0, 1 - (variance / 10000))  # Normalize variance
            else:
                consistency_factor = 0
        else:
            consistency_factor = 0.5
        
        reliability_score = (success_factor * 0.5) + (speed_factor * 0.3) + (consistency_factor * 0.2)
        return round(reliability_score * 100, 1)
    
    def generate_api_recommendation(self, results: Dict, api: Dict) -> str:
        """Generate personalized API recommendation"""
        if results["status"] == "excellent":
            return f"🟢 Highly recommended for {api['use_case']}. Excellent performance with {results['success_rate']}% uptime."
        elif results["status"] == "good":
            return f"🟡 Good choice for {api['use_case']}. Reliable with {results['avg_response_time']}ms average response."
        elif results["status"] == "fair":
            return f"🟠 Consider for non-critical {api['use_case']}. Monitor performance closely."
        else:
            return f"🔴 Not recommended for production use. Consider alternatives for {api['use_case']}."
    
    async def run_comprehensive_benchmark(self) -> Dict:
        """Run comprehensive API performance benchmark"""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.benchmark_single_api(session, api) for api in self.test_apis]
            api_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = round(end_time - start_time, 2)
        
        # Process results
        successful_results = [r for r in api_results if isinstance(r, dict)]
        
        # Generate overall recommendations
        recommendations = self.generate_personalized_recommendations(successful_results)
        
        return {
            "benchmark_summary": {
                "total_apis_tested": len(self.test_apis),
                "successful_tests": len(successful_results),
                "total_duration": total_duration,
                "timestamp": datetime.now().isoformat()
            },
            "api_results": successful_results,
            "personalized_recommendations": recommendations,
            "performance_insights": self.generate_performance_insights(successful_results)
        }
    
    def generate_personalized_recommendations(self, results: List[Dict]) -> Dict:
        """Generate personalized API recommendations by category"""
        categories = {}
        
        for result in results:
            category = result["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        recommendations = {}
        
        for category, apis in categories.items():
            # Sort by reliability score
            sorted_apis = sorted(apis, key=lambda x: x["reliability_score"], reverse=True)
            
            recommendations[category] = {
                "best_choice": sorted_apis[0]["name"] if sorted_apis else "None available",
                "alternatives": [api["name"] for api in sorted_apis[1:3]],
                "category_insights": self.get_category_insights(category, sorted_apis)
            }
        
        return recommendations
    
    def get_category_insights(self, category: str, apis: List[Dict]) -> str:
        """Get insights for specific API category"""
        if not apis:
            return "No APIs tested in this category"
            
        avg_reliability = statistics.mean([api["reliability_score"] for api in apis])
        
        insights = {
            "data": f"Data APIs average {avg_reliability:.1f}% reliability. Best for development and testing workflows.",
            "weather": f"Weather APIs show {avg_reliability:.1f}% reliability. Essential for fleet planning and route optimization.",
            "financial": f"Financial APIs maintain {avg_reliability:.1f}% reliability. Critical for cost tracking and budget analysis.",
            "geographic": f"Geographic APIs deliver {avg_reliability:.1f}% reliability. Valuable for location-based services.",
            "development": f"Developer APIs achieve {avg_reliability:.1f}% reliability. Important for CI/CD and automation.",
            "testing": f"Testing APIs provide {avg_reliability:.1f}% reliability. Useful for API development workflows.",
            "content": f"Content APIs maintain {avg_reliability:.1f}% reliability. Good for user engagement features.",
            "fun": f"Entertainment APIs show {avg_reliability:.1f}% reliability. Nice-to-have for user experience."
        }
        
        return insights.get(category, f"Category shows {avg_reliability:.1f}% average reliability")
    
    def generate_performance_insights(self, results: List[Dict]) -> Dict:
        """Generate overall performance insights"""
        if not results:
            return {"message": "No performance data available"}
        
        all_response_times = []
        all_success_rates = []
        
        for result in results:
            if result["avg_response_time"] > 0:
                all_response_times.append(result["avg_response_time"])
            all_success_rates.append(result["success_rate"])
        
        insights = {
            "fastest_api": min(results, key=lambda x: x["avg_response_time"] if x["avg_response_time"] > 0 else float('inf'))["name"],
            "most_reliable": max(results, key=lambda x: x["success_rate"])["name"],
            "overall_avg_response": round(statistics.mean(all_response_times), 2) if all_response_times else 0,
            "overall_success_rate": round(statistics.mean(all_success_rates), 1),
            "recommended_for_production": [r["name"] for r in results if r["status"] in ["excellent", "good"]],
            "needs_monitoring": [r["name"] for r in results if r["status"] == "fair"],
            "avoid_in_production": [r["name"] for r in results if r["status"] == "poor"]
        }
        
        return insights


def get_api_performance_benchmark():
    """Get API performance benchmark instance"""
    return APIPerformanceBenchmark()