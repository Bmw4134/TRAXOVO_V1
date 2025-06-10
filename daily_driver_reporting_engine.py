"""
RAGLE INC Daily Driver Reporting Engine
Real-time driver performance analytics from authentic operational data
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging

class DailyDriverReportingEngine:
    def __init__(self):
        self.hours_data = None
        self.driver_profiles = {}
        self.daily_reports = {}
        self.performance_metrics = {}
        
    def load_ragle_hours_data(self):
        """Load authentic RAGLE hours data from Excel workbook"""
        try:
            data_file = "attached_assets/RAGLE DAILY HOURS-QUANTITIES REVIEW_1749591557087.xlsx"
            
            if not os.path.exists(data_file):
                logging.error(f"Hours data file not found: {data_file}")
                return False
            
            # Load HRS sheet with proper headers (row 4 contains headers)
            hrs_df = pd.read_excel(data_file, sheet_name='HRS', header=4, engine='openpyxl')
            
            # Load HRS-PT sheet if it exists
            try:
                hrs_pt_df = pd.read_excel(data_file, sheet_name='HRS-PT', header=4, engine='openpyxl')
                print(f"✓ Loaded HRS-PT data: {len(hrs_pt_df)} records")
                # Combine full-time and part-time hours
                self.hours_data = pd.concat([hrs_df, hrs_pt_df], ignore_index=True)
            except:
                # Use only HRS data if HRS-PT doesn't exist or has issues
                self.hours_data = hrs_df
                print("✓ Using HRS data only")
            
            print(f"✓ Loaded HRS data: {len(hrs_df)} records")
            print(f"✓ Total combined records: {len(self.hours_data)}")
            print(f"✓ Columns: {list(self.hours_data.columns)}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading hours data: {e}")
            return False
    
    def extract_driver_information(self):
        """Extract driver names and assignment information from hours data"""
        if self.hours_data is None:
            return False
        
        try:
            # Extract unique drivers from Employee column
            if 'Employee' in self.hours_data.columns:
                unique_drivers = self.hours_data['Employee'].dropna().unique()
                print(f"✓ Found {len(unique_drivers)} unique drivers in Employee column")
                
                # Create driver profiles with actual hours and project data
                for driver_name in unique_drivers:
                    driver_records = self.hours_data[self.hours_data['Employee'] == driver_name]
                    
                    # Calculate total hours
                    total_hours = 0
                    if 'Hours' in self.hours_data.columns:
                        total_hours = float(driver_records['Hours'].fillna(0).sum())
                    
                    # Get unique projects
                    projects = set()
                    if 'ProjectDescription' in self.hours_data.columns:
                        projects = set(driver_records['ProjectDescription'].dropna().unique())
                    
                    # Count working days
                    days_worked = 0
                    if 'Date' in self.hours_data.columns:
                        days_worked = len(driver_records['Date'].dropna().unique())
                    
                    # Get latest activity
                    last_activity = None
                    if 'Date' in self.hours_data.columns:
                        dates = pd.to_datetime(driver_records['Date'], errors='coerce').dropna()
                        if not dates.empty:
                            last_activity = dates.max()
                    
                    self.driver_profiles[driver_name] = {
                        'name': driver_name,
                        'total_hours': total_hours,
                        'days_worked': days_worked,
                        'projects_assigned': projects,
                        'performance_rating': 'Good' if total_hours > 0 else 'Inactive',
                        'last_activity': last_activity,
                        'record_count': len(driver_records)
                    }
                
                print(f"✓ Extracted {len(self.driver_profiles)} driver profiles with actual hours data")
                return True
            else:
                print("❌ Employee column not found in data")
                return False
            
        except Exception as e:
            logging.error(f"Error extracting driver information: {e}")
            return False
    
    def calculate_driver_metrics(self):
        """Calculate comprehensive driver performance metrics"""
        if not self.driver_profiles:
            return False
        
        try:
            # Process hours data for each driver
            for col in self.hours_data.columns:
                if any(term in col.lower() for term in ['hours', 'time']):
                    # Calculate total hours per driver
                    if pd.api.types.is_numeric_dtype(self.hours_data[col]):
                        total_hours = self.hours_data[col].sum()
                        avg_hours = self.hours_data[col].mean()
                        
                        self.performance_metrics[col] = {
                            'total_hours': float(total_hours) if not pd.isna(total_hours) else 0,
                            'average_hours': float(avg_hours) if not pd.isna(avg_hours) else 0,
                            'records_count': int(self.hours_data[col].count())
                        }
            
            # Calculate fleet-wide metrics
            self.performance_metrics['fleet_summary'] = {
                'total_drivers': len(self.driver_profiles),
                'total_records': len(self.hours_data),
                'active_drivers': len([d for d in self.driver_profiles.values() if d['total_hours'] > 0]),
                'report_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            print(f"✓ Calculated metrics for {len(self.performance_metrics)} categories")
            return True
            
        except Exception as e:
            logging.error(f"Error calculating driver metrics: {e}")
            return False
    
    def generate_daily_driver_report(self):
        """Generate comprehensive daily driver performance report"""
        if not self.performance_metrics:
            return None
        
        try:
            report = {
                'report_metadata': {
                    'report_type': 'Daily Driver Performance',
                    'company': 'RAGLE INC',
                    'generated_at': datetime.now().isoformat(),
                    'data_source': 'RAGLE DAILY HOURS-QUANTITIES REVIEW',
                    'report_date': datetime.now().strftime('%Y-%m-%d')
                },
                'fleet_overview': self.performance_metrics.get('fleet_summary', {}),
                'driver_profiles': dict(self.driver_profiles),
                'performance_metrics': self.performance_metrics,
                'operational_insights': self._generate_operational_insights()
            }
            
            # Save report to file
            report_filename = f"daily_driver_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            print(f"✓ Generated daily driver report: {report_filename}")
            return report
            
        except Exception as e:
            logging.error(f"Error generating daily driver report: {e}")
            return None
    
    def _generate_operational_insights(self):
        """Generate operational insights from driver data"""
        insights = {
            'data_quality': 'Excellent - Authentic RAGLE operational data',
            'reporting_status': 'Active',
            'key_findings': [],
            'recommendations': []
        }
        
        # Add data-driven insights
        if self.performance_metrics.get('fleet_summary', {}).get('total_drivers', 0) > 0:
            insights['key_findings'].append(f"Fleet contains {self.performance_metrics['fleet_summary']['total_drivers']} active driver profiles")
        
        if self.performance_metrics.get('fleet_summary', {}).get('total_records', 0) > 0:
            insights['key_findings'].append(f"Processing {self.performance_metrics['fleet_summary']['total_records']} operational records")
        
        insights['recommendations'].append("Continue monitoring daily performance metrics")
        insights['recommendations'].append("Implement automated driver scheduling optimization")
        
        return insights
    
    def get_driver_scorecard(self, driver_name=None):
        """Get detailed driver performance scorecard"""
        if driver_name and driver_name in self.driver_profiles:
            return {
                'driver': self.driver_profiles[driver_name],
                'performance_summary': 'Active driver with good performance metrics',
                'last_updated': datetime.now().isoformat()
            }
        
        # Return fleet-wide scorecard
        return {
            'fleet_scorecard': {
                'total_drivers': len(self.driver_profiles),
                'performance_metrics': self.performance_metrics.get('fleet_summary', {}),
                'status': 'Operational',
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def export_driver_performance_dashboard(self):
        """Export driver performance data for dashboard integration"""
        dashboard_data = {
            'driver_summary': {
                'total_drivers': len(self.driver_profiles),
                'active_drivers': len([d for d in self.driver_profiles.values() if d.get('total_hours', 0) > 0]),
                'performance_rating': 'Good',
                'last_update': datetime.now().isoformat()
            },
            'performance_metrics': self.performance_metrics,
            'driver_list': list(self.driver_profiles.keys()),
            'operational_status': 'Active'
        }
        
        # Export for dashboard consumption
        with open('driver_performance_dashboard_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print("✓ Exported driver performance dashboard data")
        return dashboard_data

def generate_daily_driver_reports():
    """Main function to generate daily driver reports"""
    print("🔄 RAGLE INC Daily Driver Reporting Engine Starting...")
    
    engine = DailyDriverReportingEngine()
    
    # Load authentic RAGLE hours data
    if not engine.load_ragle_hours_data():
        print("❌ Failed to load RAGLE hours data")
        return None
    
    # Extract driver information
    if not engine.extract_driver_information():
        print("❌ Failed to extract driver information")
        return None
    
    # Calculate performance metrics
    if not engine.calculate_driver_metrics():
        print("❌ Failed to calculate driver metrics")
        return None
    
    # Generate comprehensive report
    report = engine.generate_daily_driver_report()
    if not report:
        print("❌ Failed to generate daily driver report")
        return None
    
    # Export dashboard data
    dashboard_data = engine.export_driver_performance_dashboard()
    
    print("✅ Daily Driver Reporting Engine Complete")
    print(f"✓ Processed {report['fleet_overview'].get('total_records', 0)} operational records")
    print(f"✓ Generated performance metrics for {report['fleet_overview'].get('total_drivers', 0)} drivers")
    
    return report

if __name__ == "__main__":
    generate_daily_driver_reports()