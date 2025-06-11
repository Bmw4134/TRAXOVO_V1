"""
TRAXOVO One-Click API Performance Benchmark Tool
Comprehensive testing and analysis of API performance, reliability, and integration capabilities
"""

import time
import json
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp

class APIPerformanceBenchmark:
    """One-click API performance benchmark tool with comprehensive testing capabilities"""
    
    def __init__(self):
        self.test_results = []
        self.benchmark_start_time = None
        self.benchmark_end_time = None
        self.test_apis = self._initialize_test_apis()
        
    def _initialize_test_apis(self) -> List[Dict]:
        """Initialize comprehensive list of APIs for performance testing"""
        return [
            {
                "name": "JSONPlaceholder Posts",
                "url": "https://jsonplaceholder.typicode.com/posts",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Testing API"
            },
            {
                "name": "JSONPlaceholder Users",
                "url": "https://jsonplaceholder.typicode.com/users",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Testing API"
            },
            {
                "name": "GitHub API - Public Repos",
                "url": "https://api.github.com/repositories",
                "method": "GET",
                "timeout": 15,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Development API"
            },
            {
                "name": "CoinGecko Crypto API",
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Financial API"
            },
            {
                "name": "REST Countries API",
                "url": "https://restcountries.com/v3.1/name/usa",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Geographic API"
            },
            {
                "name": "OpenWeatherMap Sample",
                "url": "https://samples.openweathermap.org/data/2.5/weather?q=London&appid=sample",
                "method": "GET",
                "timeout": 10,
                "expected_status": [200, 401],  # 401 expected for sample endpoint
                "test_type": "public_api",
                "category": "Weather API"
            },
            {
                "name": "HTTPBin Test API",
                "url": "https://httpbin.org/json",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "public_api",
                "category": "Testing API"
            },
            {
                "name": "TRAXOVO Internal - Asset Data",
                "url": "/api/comprehensive-data",
                "method": "GET",
                "timeout": 30,
                "expected_status": 200,
                "test_type": "internal_api",
                "category": "TRAXOVO Core"
            },
            {
                "name": "TRAXOVO Internal - GAUGE Status",
                "url": "/api/gauge-status",
                "method": "GET",
                "timeout": 20,
                "expected_status": 200,
                "test_type": "internal_api",
                "category": "TRAXOVO Integration"
            },
            {
                "name": "TRAXOVO Internal - Health Check",
                "url": "/health",
                "method": "GET",
                "timeout": 10,
                "expected_status": 200,
                "test_type": "internal_api",
                "category": "TRAXOVO Core"
            }
        ]

    def run_comprehensive_benchmark(self, base_url: str = "https://f2699832-8135-4557-9ec0-8d4d723b9ba2-00-347mwnpgyu8te.janeway.replit.dev") -> Dict[str, Any]:
        """Run comprehensive API performance benchmark"""
        print("🚀 Starting TRAXOVO API Performance Benchmark...")
        
        self.benchmark_start_time = datetime.now()
        self.test_results = []
        
        # Run tests in parallel for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_api = {}
            
            for api in self.test_apis:
                url = api['url']
                if url.startswith('/'):
                    url = base_url + url
                    
                future = executor.submit(self._test_single_api, api, url)
                future_to_api[future] = api
            
            for future in as_completed(future_to_api):
                api = future_to_api[future]
                try:
                    result = future.result()
                    self.test_results.append(result)
                    print(f"✓ Tested {api['name']}: {result['status']}")
                except Exception as e:
                    error_result = {
                        "api_name": api['name'],
                        "status": "error",
                        "error_message": str(e),
                        "response_time": 0,
                        "reliability_score": 0
                    }
                    self.test_results.append(error_result)
                    print(f"✗ Error testing {api['name']}: {str(e)}")
        
        self.benchmark_end_time = datetime.now()
        
        # Generate comprehensive analysis
        return self._generate_benchmark_report()

    def _test_single_api(self, api_config: Dict, url: str) -> Dict[str, Any]:
        """Test a single API endpoint with comprehensive metrics"""
        response_times = []
        success_count = 0
        total_tests = 3  # Test each API 3 times for reliability
        
        for attempt in range(total_tests):
            try:
                start_time = time.time()
                
                response = requests.request(
                    method=api_config['method'],
                    url=url,
                    timeout=api_config['timeout'],
                    headers={'User-Agent': 'TRAXOVO-Benchmark/1.0'}
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                response_times.append(response_time)
                
                # Check if response status is expected
                expected_statuses = api_config['expected_status']
                if isinstance(expected_statuses, int):
                    expected_statuses = [expected_statuses]
                
                if response.status_code in expected_statuses:
                    success_count += 1
                    
            except Exception as e:
                # Add timeout/error as maximum response time
                response_times.append(api_config['timeout'] * 1000)
                print(f"Error testing {api_config['name']} (attempt {attempt + 1}): {str(e)}")
        
        # Calculate metrics
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        success_rate = (success_count / total_tests) * 100
        
        # Calculate reliability score based on success rate and response time
        reliability_score = self._calculate_reliability_score(success_rate, avg_response_time)
        
        # Determine status
        if success_rate >= 90 and avg_response_time < 2000:
            status = "excellent"
        elif success_rate >= 70 and avg_response_time < 5000:
            status = "good"
        elif success_rate >= 50:
            status = "fair"
        else:
            status = "poor"
        
        return {
            "api_name": api_config['name'],
            "category": api_config['category'],
            "test_type": api_config['test_type'],
            "url": url,
            "status": status,
            "success_rate": round(success_rate, 1),
            "avg_response_time": round(avg_response_time, 1),
            "min_response_time": round(min_response_time, 1),
            "max_response_time": round(max_response_time, 1),
            "reliability_score": round(reliability_score, 1),
            "total_tests": total_tests,
            "successful_tests": success_count,
            "recommendation": self._get_api_recommendation(status, success_rate, avg_response_time)
        }

    def _calculate_reliability_score(self, success_rate: float, avg_response_time: float) -> float:
        """Calculate overall reliability score based on success rate and performance"""
        # Weight success rate more heavily than response time
        success_weight = 0.7
        performance_weight = 0.3
        
        # Normalize response time (assume 5000ms is very poor, 100ms is excellent)
        performance_score = max(0, 100 - (avg_response_time / 50))
        
        reliability_score = (success_rate * success_weight) + (performance_score * performance_weight)
        return min(100, max(0, reliability_score))

    def _get_api_recommendation(self, status: str, success_rate: float, avg_response_time: float) -> str:
        """Generate recommendation based on API performance"""
        if status == "excellent":
            return "Recommended for production use. Excellent performance and reliability."
        elif status == "good":
            return "Suitable for production with monitoring. Good performance overall."
        elif status == "fair":
            if success_rate < 70:
                return "Reliability concerns. Consider implementing retry logic."
            else:
                return "Acceptable for non-critical applications. Monitor performance."
        else:
            return "Not recommended for production. Investigate connectivity issues."

    def _generate_benchmark_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark analysis report"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        duration = (self.benchmark_end_time - self.benchmark_start_time).total_seconds()
        
        # Calculate overall statistics
        successful_apis = [r for r in self.test_results if r.get('status') not in ['error', 'poor']]
        total_successful_tests = sum(r.get('successful_tests', 0) for r in self.test_results)
        total_tests = sum(r.get('total_tests', 0) for r in self.test_results)
        
        overall_success_rate = (total_successful_tests / total_tests * 100) if total_tests > 0 else 0
        avg_response_times = [r.get('avg_response_time', 0) for r in self.test_results if r.get('avg_response_time', 0) > 0]
        overall_avg_response = statistics.mean(avg_response_times) if avg_response_times else 0
        
        # Find best and worst performing APIs
        best_performance = min(self.test_results, key=lambda x: x.get('avg_response_time', float('inf')))
        most_reliable = max(self.test_results, key=lambda x: x.get('reliability_score', 0))
        
        # Categorize results
        categories = {}
        for result in self.test_results:
            category = result.get('category', 'Unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Production readiness assessment
        production_ready = [r for r in self.test_results if r.get('status') in ['excellent', 'good']]
        
        return {
            "benchmark_summary": {
                "total_apis_tested": len(self.test_results),
                "successful_tests": len(successful_apis),
                "total_duration": round(duration, 2),
                "benchmark_timestamp": self.benchmark_start_time.isoformat()
            },
            "performance_insights": {
                "overall_success_rate": round(overall_success_rate, 1),
                "overall_avg_response": round(overall_avg_response, 1),
                "fastest_api": best_performance.get('api_name', 'Unknown'),
                "most_reliable": most_reliable.get('api_name', 'Unknown'),
                "production_ready_count": len(production_ready),
                "recommended_for_production": [api['api_name'] for api in production_ready]
            },
            "api_results": self.test_results,
            "category_breakdown": {
                category: {
                    "total_apis": len(apis),
                    "avg_performance": round(statistics.mean([api.get('avg_response_time', 0) for api in apis]), 1),
                    "avg_reliability": round(statistics.mean([api.get('reliability_score', 0) for api in apis]), 1)
                }
                for category, apis in categories.items()
            },
            "recommendations": self._generate_overall_recommendations(production_ready, self.test_results),
            "next_steps": [
                "Review APIs with poor performance for optimization opportunities",
                "Implement monitoring for production-ready APIs",
                "Consider retry logic for APIs with reliability concerns",
                "Schedule regular performance benchmarks"
            ]
        }

    def _generate_overall_recommendations(self, production_ready: List[Dict], all_results: List[Dict]) -> List[str]:
        """Generate overall recommendations based on benchmark results"""
        recommendations = []
        
        production_rate = len(production_ready) / len(all_results) * 100
        
        if production_rate >= 80:
            recommendations.append("Excellent API ecosystem. Most APIs are production-ready.")
        elif production_rate >= 60:
            recommendations.append("Good API performance overall. Some optimization opportunities exist.")
        else:
            recommendations.append("API performance needs improvement. Focus on reliability and response times.")
        
        # API-specific recommendations
        slow_apis = [r for r in all_results if r.get('avg_response_time', 0) > 3000]
        if slow_apis:
            recommendations.append(f"Consider optimizing {len(slow_apis)} slow-performing APIs.")
        
        unreliable_apis = [r for r in all_results if r.get('success_rate', 100) < 80]
        if unreliable_apis:
            recommendations.append(f"Address reliability issues in {len(unreliable_apis)} APIs.")
        
        return recommendations

    def get_quick_benchmark_summary(self) -> Dict[str, Any]:
        """Get a quick summary of the last benchmark run"""
        if not self.test_results:
            return {"status": "no_data", "message": "No benchmark data available. Run benchmark first."}
        
        excellent_count = len([r for r in self.test_results if r.get('status') == 'excellent'])
        good_count = len([r for r in self.test_results if r.get('status') == 'good'])
        total_count = len(self.test_results)
        
        return {
            "status": "available",
            "total_apis": total_count,
            "excellent_apis": excellent_count,
            "good_apis": good_count,
            "production_ready": excellent_count + good_count,
            "last_benchmark": self.benchmark_start_time.isoformat() if self.benchmark_start_time else None
        }

def get_api_benchmark_tool():
    """Get API benchmark tool instance"""
    return APIPerformanceBenchmark()

def run_quick_benchmark():
    """Run quick API performance benchmark"""
    benchmark_tool = APIPerformanceBenchmark()
    return benchmark_tool.run_comprehensive_benchmark()

def get_benchmark_results():
    """Get existing benchmark results"""
    benchmark_tool = APIPerformanceBenchmark()
    return benchmark_tool.get_quick_benchmark_summary()