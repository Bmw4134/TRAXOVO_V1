"""
TRAXOVO One-Click API Performance Benchmark Tool
Enterprise-grade API performance testing and analytics system
"""

import time
import statistics
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any
import concurrent.futures
import threading
import logging

class APIPerformanceBenchmark:
    """One-click API performance benchmark and analytics tool"""
    
    def __init__(self):
        self.benchmark_results = {}
        self.test_configurations = {
            'light': {'concurrent_users': 5, 'requests_per_user': 10, 'duration': 30},
            'standard': {'concurrent_users': 25, 'requests_per_user': 50, 'duration': 60},
            'stress': {'concurrent_users': 100, 'requests_per_user': 100, 'duration': 120},
            'enterprise': {'concurrent_users': 500, 'requests_per_user': 200, 'duration': 300}
        }
        
    def get_api_endpoints(self) -> List[Dict]:
        """Get list of API endpoints to benchmark"""
        return [
            {
                'name': 'Ground Works Projects',
                'endpoint': '/api/ground-works/projects',
                'method': 'GET',
                'category': 'data_retrieval',
                'expected_response_time': 200,
                'critical': True
            },
            {
                'name': 'Ground Works Data',
                'endpoint': '/api/groundworks/data',
                'method': 'GET',
                'category': 'data_retrieval',
                'expected_response_time': 150,
                'critical': True
            },
            {
                'name': 'RAGLE Daily Hours',
                'endpoint': '/api/ragle-daily-hours',
                'method': 'GET',
                'category': 'analytics',
                'expected_response_time': 300,
                'critical': False
            },
            {
                'name': 'Ground Works Connect',
                'endpoint': '/api/groundworks/connect',
                'method': 'POST',
                'category': 'authentication',
                'expected_response_time': 500,
                'critical': True,
                'payload': {'username': 'test', 'password': 'test', 'base_url': 'test'}
            },
            {
                'name': 'Dashboard Home',
                'endpoint': '/',
                'method': 'GET',
                'category': 'ui',
                'expected_response_time': 100,
                'critical': True
            },
            {
                'name': 'Ultimate Troy Dashboard',
                'endpoint': '/ultimate-troy-dashboard',
                'method': 'GET',
                'category': 'dashboard',
                'expected_response_time': 400,
                'critical': False
            },
            {
                'name': 'Ground Works Complete',
                'endpoint': '/ground-works-complete',
                'method': 'GET',
                'category': 'dashboard',
                'expected_response_time': 500,
                'critical': False
            }
        ]
    
    def benchmark_endpoint(self, endpoint: Dict, base_url: str = "http://localhost:5000") -> Dict:
        """Benchmark a single endpoint with detailed metrics"""
        url = f"{base_url}{endpoint['endpoint']}"
        method = endpoint['method']
        payload = endpoint.get('payload', None)
        
        # Timing measurements
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, timeout=30)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                return {
                    'endpoint': endpoint['name'],
                    'url': url,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'content_length': len(response.text),
                    'success': response.status_code < 400,
                    'timestamp': datetime.now().isoformat(),
                    'category': endpoint['category'],
                    'critical': endpoint['critical']
                }
            elif method == 'POST':
                response = requests.post(url, json=payload, timeout=30)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                return {
                    'endpoint': endpoint['name'],
                    'url': url,
                    'status_code': response.status_code,
                    'response_time_ms': response_time,
                    'content_length': len(response.text),
                    'success': response.status_code < 400,
                    'timestamp': datetime.now().isoformat(),
                    'category': endpoint['category'],
                    'critical': endpoint['critical']
                }
                    
        except Exception as e:
            end_time = time.time()
            return {
                'endpoint': endpoint['name'],
                'url': url,
                'status_code': 0,
                'response_time_ms': (end_time - start_time) * 1000,
                'content_length': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'category': endpoint['category'],
                'critical': endpoint['critical']
            }
    
    def run_concurrent_benchmark(self, test_type: str = 'standard') -> Dict:
        """Run concurrent benchmark test with specified configuration"""
        config = self.test_configurations[test_type]
        endpoints = self.get_api_endpoints()
        
        benchmark_start = datetime.now()
        all_results = []
        
        # Create concurrent tasks using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=config['concurrent_users']) as executor:
            # Submit all benchmark tasks
            futures = []
            for _ in range(config['concurrent_users']):
                for _ in range(config['requests_per_user']):
                    for endpoint in endpoints:
                        future = executor.submit(self.benchmark_endpoint, endpoint)
                        futures.append(future)
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    # Handle failed requests
                    all_results.append({
                        'endpoint': 'unknown',
                        'success': False,
                        'error': str(e),
                        'response_time_ms': 0,
                        'timestamp': datetime.now().isoformat()
                    })
        
        benchmark_end = datetime.now()
        
        # Calculate comprehensive analytics
        analytics = self.calculate_performance_analytics(all_results, config, 
                                                        benchmark_start, benchmark_end)
        
        return {
            'test_type': test_type,
            'configuration': config,
            'start_time': benchmark_start.isoformat(),
            'end_time': benchmark_end.isoformat(),
            'total_duration': (benchmark_end - benchmark_start).total_seconds(),
            'raw_results': all_results,
            'analytics': analytics,
            'summary': self.generate_performance_summary(analytics)
        }
    
    def calculate_performance_analytics(self, results: List[Dict], config: Dict, 
                                      start_time: datetime, end_time: datetime) -> Dict:
        """Calculate comprehensive performance analytics from benchmark results"""
        
        # Group results by endpoint
        endpoint_groups = {}
        for result in results:
            endpoint_name = result['endpoint']
            if endpoint_name not in endpoint_groups:
                endpoint_groups[endpoint_name] = []
            endpoint_groups[endpoint_name].append(result)
        
        # Calculate metrics for each endpoint
        endpoint_analytics = {}
        for endpoint_name, endpoint_results in endpoint_groups.items():
            response_times = [r['response_time_ms'] for r in endpoint_results if r['success']]
            success_count = len([r for r in endpoint_results if r['success']])
            total_count = len(endpoint_results)
            
            if response_times:
                endpoint_analytics[endpoint_name] = {
                    'total_requests': total_count,
                    'successful_requests': success_count,
                    'failed_requests': total_count - success_count,
                    'success_rate': (success_count / total_count) * 100,
                    'avg_response_time': statistics.mean(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'median_response_time': statistics.median(response_times),
                    'p95_response_time': self.percentile(response_times, 95),
                    'p99_response_time': self.percentile(response_times, 99),
                    'requests_per_second': success_count / (end_time - start_time).total_seconds(),
                    'category': endpoint_results[0]['category'],
                    'critical': endpoint_results[0]['critical']
                }
            else:
                endpoint_analytics[endpoint_name] = {
                    'total_requests': total_count,
                    'successful_requests': 0,
                    'failed_requests': total_count,
                    'success_rate': 0,
                    'avg_response_time': 0,
                    'requests_per_second': 0,
                    'category': endpoint_results[0]['category'],
                    'critical': endpoint_results[0]['critical']
                }
        
        # Calculate overall system analytics
        all_response_times = [r['response_time_ms'] for r in results if r['success']]
        total_success = len([r for r in results if r['success']])
        total_requests = len(results)
        
        overall_analytics = {
            'total_requests': total_requests,
            'successful_requests': total_success,
            'failed_requests': total_requests - total_success,
            'overall_success_rate': (total_success / total_requests) * 100 if total_requests > 0 else 0,
            'avg_response_time': statistics.mean(all_response_times) if all_response_times else 0,
            'median_response_time': statistics.median(all_response_times) if all_response_times else 0,
            'p95_response_time': self.percentile(all_response_times, 95) if all_response_times else 0,
            'p99_response_time': self.percentile(all_response_times, 99) if all_response_times else 0,
            'total_throughput': total_success / (end_time - start_time).total_seconds(),
            'concurrent_users': config['concurrent_users'],
            'requests_per_user': config['requests_per_user']
        }
        
        return {
            'endpoints': endpoint_analytics,
            'overall': overall_analytics,
            'performance_grade': self.calculate_performance_grade(overall_analytics, endpoint_analytics)
        }
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value from data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_data):
            return sorted_data[-1]
        
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def calculate_performance_grade(self, overall: Dict, endpoints: Dict) -> Dict:
        """Calculate performance grade and recommendations"""
        grade_score = 100
        issues = []
        recommendations = []
        
        # Check overall success rate
        if overall['overall_success_rate'] < 95:
            grade_score -= 20
            issues.append("Low success rate - system reliability issues detected")
            recommendations.append("Investigate failed requests and improve error handling")
        
        # Check response times
        if overall['avg_response_time'] > 1000:
            grade_score -= 15
            issues.append("High average response time - performance optimization needed")
            recommendations.append("Optimize database queries and implement caching")
        
        if overall['p95_response_time'] > 2000:
            grade_score -= 10
            issues.append("High P95 response time - inconsistent performance")
            recommendations.append("Identify and optimize slow endpoints")
        
        # Check critical endpoints
        critical_issues = 0
        for endpoint_name, metrics in endpoints.items():
            if metrics['critical'] and metrics['success_rate'] < 98:
                critical_issues += 1
                issues.append(f"Critical endpoint '{endpoint_name}' has reliability issues")
        
        if critical_issues > 0:
            grade_score -= critical_issues * 10
            recommendations.append("Prioritize fixing critical endpoint issues")
        
        # Check throughput
        if overall['total_throughput'] < 10:
            grade_score -= 10
            issues.append("Low throughput - scalability concerns")
            recommendations.append("Implement load balancing and horizontal scaling")
        
        # Determine letter grade
        if grade_score >= 90:
            letter_grade = "A"
            status = "Excellent"
        elif grade_score >= 80:
            letter_grade = "B"
            status = "Good"
        elif grade_score >= 70:
            letter_grade = "C"
            status = "Fair"
        elif grade_score >= 60:
            letter_grade = "D"
            status = "Poor"
        else:
            letter_grade = "F"
            status = "Critical"
        
        return {
            'score': max(0, grade_score),
            'letter_grade': letter_grade,
            'status': status,
            'issues': issues,
            'recommendations': recommendations
        }
    
    def generate_performance_summary(self, analytics: Dict) -> Dict:
        """Generate executive summary of performance benchmark"""
        overall = analytics['overall']
        grade = analytics['performance_grade']
        
        # Calculate cost impact estimates
        failed_requests = overall['failed_requests']
        avg_response_time = overall['avg_response_time']
        
        # Estimated productivity impact
        if avg_response_time > 1000:
            productivity_impact = "High - User experience significantly degraded"
        elif avg_response_time > 500:
            productivity_impact = "Medium - Noticeable delays in user interactions"
        else:
            productivity_impact = "Low - Acceptable performance levels"
        
        # Infrastructure recommendations
        if overall['total_throughput'] < 50:
            infrastructure_rec = "Scale up server resources and implement load balancing"
        elif overall['total_throughput'] < 100:
            infrastructure_rec = "Optimize current infrastructure and monitor scaling needs"
        else:
            infrastructure_rec = "Current infrastructure performs well under load"
        
        return {
            'performance_status': grade['status'],
            'grade': f"{grade['letter_grade']} ({grade['score']}/100)",
            'key_metrics': {
                'success_rate': f"{overall['overall_success_rate']:.1f}%",
                'avg_response_time': f"{overall['avg_response_time']:.0f}ms",
                'throughput': f"{overall['total_throughput']:.1f} req/sec",
                'p95_response_time': f"{overall['p95_response_time']:.0f}ms"
            },
            'productivity_impact': productivity_impact,
            'infrastructure_recommendation': infrastructure_rec,
            'immediate_actions': grade['recommendations'][:3],
            'estimated_monthly_cost_impact': self.estimate_cost_impact(overall, failed_requests)
        }
    
    def estimate_cost_impact(self, overall: Dict, failed_requests: int) -> str:
        """Estimate monthly cost impact of performance issues"""
        # Simplified cost calculation based on failed requests and response times
        base_cost_per_failed_request = 0.50  # Estimated cost per failed request
        response_time_penalty = max(0, (overall['avg_response_time'] - 200) * 0.01)
        
        monthly_failed_cost = failed_requests * base_cost_per_failed_request * 30
        monthly_performance_cost = response_time_penalty * overall['successful_requests'] * 30
        
        total_estimated_cost = monthly_failed_cost + monthly_performance_cost
        
        if total_estimated_cost < 100:
            return "Low impact - Under $100/month"
        elif total_estimated_cost < 500:
            return f"Medium impact - ~${total_estimated_cost:.0f}/month"
        else:
            return f"High impact - ~${total_estimated_cost:.0f}/month in productivity losses"
    
    def run_quick_benchmark(self) -> Dict:
        """Run a quick 30-second benchmark for immediate feedback"""
        return self.run_concurrent_benchmark('light')
    
    def run_standard_benchmark(self) -> Dict:
        """Run a standard 1-minute benchmark for comprehensive analysis"""
        return self.run_concurrent_benchmark('standard')
    
    def run_stress_test(self) -> Dict:
        """Run a 2-minute stress test for scalability analysis"""
        return self.run_concurrent_benchmark('stress')
    
    def run_enterprise_test(self) -> Dict:
        """Run a 5-minute enterprise-grade performance test"""
        return self.run_concurrent_benchmark('enterprise')

def get_benchmark_tool():
    """Get API Performance Benchmark tool instance"""
    return APIPerformanceBenchmark()

# Test function for immediate execution
if __name__ == "__main__":
    benchmark = APIPerformanceBenchmark()
    print("Running quick API performance benchmark...")
    results = benchmark.run_quick_benchmark()
    print(f"Benchmark completed with grade: {results['summary']['grade']}")