"""
TRAXOVO Intelligent Anomaly Detection Engine
Analyzes authentic fleet data to identify operational anomalies and performance deviations
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics

class AnomalyDetectionEngine:
    def __init__(self):
        self.data_path = "./attached_assets"
        self.anomaly_threshold = 0.05  # 5% threshold for outlier detection
        self.asset_data = {}
        self.anomaly_results = {}
        self.performance_baselines = {}
        
    def load_authentic_data(self):
        """Load authentic asset data from CSV files"""
        try:
            # Load main asset usage data
            usage_file = os.path.join(self.data_path, "AssetsTimeOnSite (2)_1749454865159.csv")
            if os.path.exists(usage_file):
                usage_df = pd.read_csv(usage_file, on_bad_lines='skip', encoding='utf-8')
                self.asset_data['usage'] = usage_df
                logging.info(f"Loaded usage data: {len(usage_df)} records")
            
            # Load daily usage data
            daily_usage_file = os.path.join(self.data_path, "DailyUsage_1749454857635.csv")
            if os.path.exists(daily_usage_file):
                daily_df = pd.read_csv(daily_usage_file, on_bad_lines='skip', encoding='utf-8')
                self.asset_data['daily'] = daily_df
                logging.info(f"Loaded daily usage data: {len(daily_df)} records")
            
            # Load activity detail data
            activity_file = os.path.join(self.data_path, "ActivityDetail (4)_1749454854416.csv")
            if os.path.exists(activity_file):
                activity_df = pd.read_csv(activity_file, on_bad_lines='skip', encoding='utf-8')
                self.asset_data['activity'] = activity_df
                logging.info(f"Loaded activity data: {len(activity_df)} records")
                
            # Load driving history for anomaly detection
            driving_file = os.path.join(self.data_path, "DrivingHistory (2)_1749454860929.csv")
            if os.path.exists(driving_file):
                driving_df = pd.read_csv(driving_file, on_bad_lines='skip', encoding='utf-8')
                self.asset_data['driving'] = driving_df
                logging.info(f"Loaded driving history: {len(driving_df)} records")
                
        except Exception as e:
            logging.error(f"Error loading authentic data: {e}")
    
    def establish_performance_baselines(self):
        """Establish normal performance baselines from historical data"""
        baselines = {}
        
        if 'usage' in self.asset_data:
            usage_data = self.asset_data['usage']
            
            # Calculate baseline metrics for each asset
            if 'Asset' in usage_data.columns and 'TimeOnSite' in usage_data.columns:
                asset_stats = usage_data.groupby('Asset')['TimeOnSite'].agg(['mean', 'std', 'median', 'count'])
                
                for asset in asset_stats.index:
                    stats_row = asset_stats.loc[asset]
                    baselines[asset] = {
                        'avg_time_on_site': stats_row['mean'],
                        'std_time_on_site': stats_row['std'],
                        'median_time_on_site': stats_row['median'],
                        'activity_frequency': stats_row['count'],
                        'normal_range_lower': stats_row['mean'] - (2 * stats_row['std']),
                        'normal_range_upper': stats_row['mean'] + (2 * stats_row['std'])
                    }
        
        self.performance_baselines = baselines
        logging.info(f"Established baselines for {len(baselines)} assets")
    
    def detect_utilization_anomalies(self) -> List[Dict]:
        """Detect assets with abnormal utilization patterns"""
        anomalies = []
        
        if 'daily' in self.asset_data:
            daily_data = self.asset_data['daily']
            
            # Analyze daily usage patterns
            if 'Asset' in daily_data.columns:
                for asset in daily_data['Asset'].unique():
                    asset_daily = daily_data[daily_data['Asset'] == asset]
                    
                    # Check for usage columns
                    usage_columns = [col for col in asset_daily.columns if 'usage' in col.lower() or 'time' in col.lower()]
                    
                    if usage_columns:
                        for usage_col in usage_columns:
                            # Convert to numeric and filter valid values
                            numeric_values = []
                            for val in asset_daily[usage_col]:
                                try:
                                    num_val = float(val)
                                    if not np.isnan(num_val):
                                        numeric_values.append(num_val)
                                except (ValueError, TypeError):
                                    continue
                            
                            if len(numeric_values) > 3:  # Need minimum data points
                                # Use IQR method for outlier detection with built-in functions
                                sorted_values = sorted(numeric_values)
                                n = len(sorted_values)
                                Q1 = sorted_values[n//4]
                                Q3 = sorted_values[3*n//4]
                                IQR = Q3 - Q1
                                lower_bound = Q1 - 1.5 * IQR
                                upper_bound = Q3 + 1.5 * IQR
                                
                                outliers = [v for v in numeric_values if v < lower_bound or v > upper_bound]
                                
                                if len(outliers) > 0:
                                    anomalies.append({
                                        'asset_id': asset,
                                        'anomaly_type': 'utilization_outlier',
                                        'severity': 'high' if len(outliers) > len(numeric_values) * 0.3 else 'medium',
                                        'metric': usage_col,
                                        'normal_range': f"{lower_bound:.2f} - {upper_bound:.2f}",
                                        'outlier_values': outliers,
                                        'description': f"Unusual {usage_col} patterns detected",
                                        'detected_at': datetime.now().isoformat()
                                    })
        
        return anomalies
    
    def detect_performance_degradation(self) -> List[Dict]:
        """Detect assets showing performance degradation over time"""
        anomalies = []
        
        if 'activity' in self.asset_data:
            activity_data = self.asset_data['activity']
            
            # Analyze performance trends
            if 'Asset' in activity_data.columns:
                for asset in activity_data['Asset'].unique():
                    if asset in self.performance_baselines:
                        baseline = self.performance_baselines[asset]
                        asset_activity = activity_data[activity_data['Asset'] == asset]
                        
                        # Check for performance metrics
                        performance_cols = [col for col in asset_activity.columns 
                                          if any(keyword in col.lower() for keyword in 
                                               ['efficiency', 'performance', 'speed', 'fuel', 'hours'])]
                        
                        for perf_col in performance_cols:
                            recent_values = pd.to_numeric(asset_activity[perf_col], errors='coerce').dropna()
                            
                            if len(recent_values) > 0:
                                avg_recent = recent_values.mean()
                                
                                # Compare with baseline if available
                                if 'avg_time_on_site' in baseline:
                                    deviation_pct = abs(avg_recent - baseline['avg_time_on_site']) / baseline['avg_time_on_site'] * 100
                                    
                                    if deviation_pct > 25:  # More than 25% deviation
                                        anomalies.append({
                                            'asset_id': asset,
                                            'anomaly_type': 'performance_degradation',
                                            'severity': 'high' if deviation_pct > 50 else 'medium',
                                            'metric': perf_col,
                                            'baseline_value': baseline['avg_time_on_site'],
                                            'current_value': avg_recent,
                                            'deviation_percent': deviation_pct,
                                            'description': f"Performance deviation of {deviation_pct:.1f}% from baseline",
                                            'detected_at': datetime.now().isoformat()
                                        })
        
        return anomalies
    
    def detect_behavioral_anomalies(self) -> List[Dict]:
        """Detect unusual behavioral patterns in asset operations"""
        anomalies = []
        
        if 'driving' in self.asset_data:
            driving_data = self.asset_data['driving']
            
            # Analyze driving behavior patterns
            if 'Asset' in driving_data.columns:
                for asset in driving_data['Asset'].unique():
                    asset_driving = driving_data[driving_data['Asset'] == asset]
                    
                    # Check for behavioral indicators
                    behavioral_cols = [col for col in asset_driving.columns 
                                     if any(keyword in col.lower() for keyword in 
                                          ['speed', 'acceleration', 'brake', 'idle', 'location'])]
                    
                    for behavior_col in behavioral_cols:
                        behavior_values = pd.to_numeric(asset_driving[behavior_col], errors='coerce').dropna()
                        
                        if len(behavior_values) > 5:
                            # Use statistical methods to detect anomalies with built-in functions
                            mean_val = statistics.mean(behavior_values)
                            std_val = statistics.stdev(behavior_values) if len(behavior_values) > 1 else 0
                            outliers = [v for v in behavior_values if abs(v - mean_val) > 3 * std_val]
                            
                            if len(outliers) > 0:
                                anomalies.append({
                                    'asset_id': asset,
                                    'anomaly_type': 'behavioral_anomaly',
                                    'severity': 'medium',
                                    'metric': behavior_col,
                                    'outlier_count': len(outlier_indices),
                                    'total_records': len(behavior_values),
                                    'anomaly_percentage': (len(outlier_indices) / len(behavior_values)) * 100,
                                    'description': f"Unusual {behavior_col} behavior detected",
                                    'detected_at': datetime.now().isoformat()
                                })
        
        return anomalies
    
    def detect_maintenance_anomalies(self) -> List[Dict]:
        """Detect maintenance-related anomalies and predict failures"""
        anomalies = []
        
        # Load service data if available
        try:
            service_file = os.path.join(self.data_path, "ServiceHistoryReport_1749454738568.csv")
            if os.path.exists(service_file):
                service_df = pd.read_csv(service_file, on_bad_lines='skip', encoding='utf-8')
                
                if 'Asset' in service_df.columns:
                    for asset in service_df['Asset'].unique():
                        asset_service = service_df[service_df['Asset'] == asset]
                        
                        # Check service intervals
                        if 'Date' in asset_service.columns:
                            service_dates = pd.to_datetime(asset_service['Date'], errors='coerce').dropna()
                            
                            if len(service_dates) > 1:
                                service_intervals = service_dates.diff().dt.days.dropna()
                                avg_interval = service_intervals.mean()
                                
                                # Check if current interval exceeds normal
                                last_service = service_dates.max()
                                days_since_service = (datetime.now() - last_service).days
                                
                                if days_since_service > avg_interval * 1.5:  # 50% over normal interval
                                    anomalies.append({
                                        'asset_id': asset,
                                        'anomaly_type': 'maintenance_overdue',
                                        'severity': 'high' if days_since_service > avg_interval * 2 else 'medium',
                                        'metric': 'service_interval',
                                        'normal_interval': avg_interval,
                                        'current_interval': days_since_service,
                                        'last_service_date': last_service.isoformat(),
                                        'description': f"Maintenance overdue by {days_since_service - avg_interval:.0f} days",
                                        'detected_at': datetime.now().isoformat()
                                    })
        
        except Exception as e:
            logging.error(f"Error detecting maintenance anomalies: {e}")
        
        return anomalies
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run complete anomaly detection analysis"""
        logging.info("Starting comprehensive anomaly detection analysis")
        
        # Load data and establish baselines
        self.load_authentic_data()
        self.establish_performance_baselines()
        
        # Run all anomaly detection algorithms
        utilization_anomalies = self.detect_utilization_anomalies()
        performance_anomalies = self.detect_performance_degradation()
        behavioral_anomalies = self.detect_behavioral_anomalies()
        maintenance_anomalies = self.detect_maintenance_anomalies()
        
        # Combine and categorize results
        all_anomalies = (utilization_anomalies + performance_anomalies + 
                        behavioral_anomalies + maintenance_anomalies)
        
        # Calculate severity distribution
        severity_counts = {}
        for anomaly in all_anomalies:
            severity = anomaly.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate summary statistics
        results = {
            'total_anomalies': len(all_anomalies),
            'anomalies_by_type': {
                'utilization': len(utilization_anomalies),
                'performance': len(performance_anomalies),
                'behavioral': len(behavioral_anomalies),
                'maintenance': len(maintenance_anomalies)
            },
            'severity_distribution': severity_counts,
            'anomalies': all_anomalies,
            'analysis_timestamp': datetime.now().isoformat(),
            'assets_analyzed': len(self.performance_baselines),
            'data_sources': list(self.asset_data.keys())
        }
        
        self.anomaly_results = results
        logging.info(f"Anomaly analysis complete: {len(all_anomalies)} anomalies detected")
        
        return results
    
    def get_asset_risk_score(self, asset_id: str) -> float:
        """Calculate risk score for specific asset based on anomalies"""
        if not self.anomaly_results:
            return 0.0
        
        asset_anomalies = [a for a in self.anomaly_results['anomalies'] 
                          if a.get('asset_id') == asset_id]
        
        if not asset_anomalies:
            return 0.1  # Low risk baseline
        
        # Weight anomalies by severity
        severity_weights = {'high': 1.0, 'medium': 0.6, 'low': 0.3}
        total_weight = sum(severity_weights.get(a.get('severity', 'low'), 0.3) 
                          for a in asset_anomalies)
        
        # Normalize to 0-1 scale
        risk_score = min(total_weight / 3.0, 1.0)  # Cap at 1.0
        
        return risk_score
    
    def get_fleet_health_summary(self) -> Dict:
        """Generate fleet-wide health summary"""
        if not self.anomaly_results:
            return {}
        
        total_assets = self.anomaly_results['assets_analyzed']
        total_anomalies = self.anomaly_results['total_anomalies']
        
        # Calculate overall fleet health score
        if total_assets > 0:
            anomaly_ratio = total_anomalies / total_assets
            fleet_health = max(0, 1 - (anomaly_ratio / 2))  # Inverse relationship
        else:
            fleet_health = 1.0
        
        return {
            'overall_health_score': fleet_health,
            'total_assets': total_assets,
            'assets_with_anomalies': len(set(a.get('asset_id') for a in self.anomaly_results['anomalies'])),
            'critical_assets': len([a for a in self.anomaly_results['anomalies'] 
                                  if a.get('severity') == 'high']),
            'health_status': 'excellent' if fleet_health > 0.9 else 
                           'good' if fleet_health > 0.7 else 
                           'fair' if fleet_health > 0.5 else 'poor'
        }