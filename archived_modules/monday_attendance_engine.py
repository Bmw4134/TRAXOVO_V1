"""
TRAXOVO Monday Morning Attendance Engine
Production-ready system for GAUGE report import and executive reporting
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
import logging

class MondayAttendanceEngine:
    def __init__(self):
        self.data_dir = 'attached_assets'
        self.attendance_file = os.path.join(self.data_dir, 'attendance.json')
        self.gauge_reports_dir = 'gauge_reports'
        os.makedirs(self.gauge_reports_dir, exist_ok=True)
        
    def process_gauge_report_upload(self, file_path):
        """Process uploaded GAUGE report for Monday morning"""
        
        try:
            # Determine file type and process accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            # Process GAUGE data columns
            attendance_data = self.extract_attendance_from_gauge(df)
            
            # Save processed data
            self.save_attendance_data(attendance_data)
            
            # Generate executive report
            executive_summary = self.generate_executive_summary(attendance_data)
            
            return {
                'success': True,
                'records_processed': len(attendance_data),
                'executive_summary': executive_summary,
                'report_ready': True
            }
            
        except Exception as e:
            logging.error(f"GAUGE report processing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'report_ready': False
            }
    
    def extract_attendance_from_gauge(self, df):
        """Extract attendance patterns from GAUGE telematic data"""
        
        attendance_records = []
        
        # Map GAUGE columns to attendance data
        for _, row in df.iterrows():
            record = {
                'asset_id': row.get('Asset ID', row.get('Equipment ID', 'Unknown')),
                'operator': row.get('Operator', row.get('Driver', 'Unassigned')),
                'start_time': row.get('Start Time', row.get('First Activity', '')),
                'end_time': row.get('End Time', row.get('Last Activity', '')),
                'location': row.get('Location', row.get('Job Site', '')),
                'hours_worked': row.get('Hours', row.get('Engine Hours', 0)),
                'status': self.determine_status(row),
                'date': row.get('Date', datetime.now().strftime('%Y-%m-%d'))
            }
            attendance_records.append(record)
        
        return attendance_records
    
    def determine_status(self, row):
        """Determine attendance status from GAUGE data"""
        
        start_time = row.get('Start Time', '')
        end_time = row.get('End Time', '')
        hours = float(row.get('Hours', 0))
        
        if not start_time or not end_time:
            return 'Not on Job'
        
        # Parse start time to check for late start
        try:
            start_hour = int(start_time.split(':')[0])
            if start_hour > 7:  # After 7 AM considered late
                return 'Late Start'
            elif hours < 6:  # Less than 6 hours considered early end
                return 'Early End'
            else:
                return 'On Time'
        except:
            return 'Present'
    
    def save_attendance_data(self, attendance_data):
        """Save processed attendance data"""
        
        # Load existing data if available
        existing_data = []
        if os.path.exists(self.attendance_file):
            try:
                with open(self.attendance_file, 'r') as f:
                    existing_data = json.load(f)
            except:
                existing_data = []
        
        # Merge new data with existing
        combined_data = existing_data + attendance_data
        
        # Save updated data
        with open(self.attendance_file, 'w') as f:
            json.dump(combined_data, f, indent=2)
    
    def generate_executive_summary(self, attendance_data):
        """Generate executive summary for Monday morning report"""
        
        total_records = len(attendance_data)
        on_time_count = len([r for r in attendance_data if r['status'] == 'On Time'])
        late_start_count = len([r for r in attendance_data if r['status'] == 'Late Start'])
        early_end_count = len([r for r in attendance_data if r['status'] == 'Early End'])
        not_on_job_count = len([r for r in attendance_data if r['status'] == 'Not on Job'])
        
        on_time_rate = (on_time_count / total_records * 100) if total_records > 0 else 0
        
        # Calculate financial impact
        late_start_cost = late_start_count * 80  # $80 per late start
        early_end_revenue_loss = early_end_count * 120  # $120 per early end
        not_on_job_loss = not_on_job_count * 400  # $400 per not-on-job
        
        return {
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'total_assets_tracked': total_records,
            'on_time_rate': round(on_time_rate, 1),
            'performance_breakdown': {
                'on_time': on_time_count,
                'late_start': late_start_count,
                'early_end': early_end_count,
                'not_on_job': not_on_job_count
            },
            'financial_impact': {
                'late_start_cost': late_start_cost,
                'early_end_loss': early_end_revenue_loss,
                'not_on_job_loss': not_on_job_loss,
                'total_daily_impact': late_start_cost + early_end_revenue_loss + not_on_job_loss
            },
            'recommendations': self.generate_recommendations(attendance_data)
        }
    
    def generate_recommendations(self, attendance_data):
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Analyze patterns
        late_operators = [r['operator'] for r in attendance_data if r['status'] == 'Late Start']
        frequent_late = {op: late_operators.count(op) for op in set(late_operators)}
        
        if frequent_late:
            top_late_operator = max(frequent_late, key=frequent_late.get)
            recommendations.append(f"Schedule coaching session with {top_late_operator} (multiple late starts)")
        
        # Location-based recommendations
        locations = [r['location'] for r in attendance_data if r['location']]
        if locations:
            problem_locations = [loc for loc in set(locations) if 
                               len([r for r in attendance_data if r['location'] == loc and r['status'] in ['Late Start', 'Not on Job']]) > 1]
            
            for loc in problem_locations:
                recommendations.append(f"Review logistics for {loc} - multiple attendance issues")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def get_monday_morning_report(self):
        """Generate complete Monday morning report"""
        
        if not os.path.exists(self.attendance_file):
            return {
                'error': 'No attendance data available. Please upload GAUGE reports first.',
                'report_available': False
            }
        
        try:
            with open(self.attendance_file, 'r') as f:
                attendance_data = json.load(f)
            
            # Filter for recent data (last 7 days)
            recent_data = [r for r in attendance_data if self.is_recent_data(r['date'])]
            
            summary = self.generate_executive_summary(recent_data)
            detailed_report = self.generate_detailed_report(recent_data)
            
            return {
                'report_available': True,
                'summary': summary,
                'detailed_report': detailed_report,
                'ready_for_distribution': True
            }
            
        except Exception as e:
            logging.error(f"Monday report generation error: {e}")
            return {
                'error': str(e),
                'report_available': False
            }
    
    def is_recent_data(self, date_str):
        """Check if data is from the last 7 days"""
        
        try:
            data_date = datetime.strptime(date_str, '%Y-%m-%d')
            week_ago = datetime.now() - timedelta(days=7)
            return data_date >= week_ago
        except:
            return True  # Include if can't parse date
    
    def generate_detailed_report(self, attendance_data):
        """Generate detailed breakdown for managers"""
        
        # Group by operator
        operator_performance = {}
        for record in attendance_data:
            operator = record['operator']
            if operator not in operator_performance:
                operator_performance[operator] = {
                    'total_days': 0,
                    'on_time': 0,
                    'late_start': 0,
                    'early_end': 0,
                    'not_on_job': 0
                }
            
            operator_performance[operator]['total_days'] += 1
            status_key = record['status'].lower().replace(' ', '_')
            if status_key in operator_performance[operator]:
                operator_performance[operator][status_key] += 1
        
        # Calculate performance scores
        for operator in operator_performance:
            perf = operator_performance[operator]
            total = perf['total_days']
            if total > 0:
                perf['performance_score'] = round((perf['on_time'] / total) * 100, 1)
            else:
                perf['performance_score'] = 0
        
        return {
            'operator_performance': operator_performance,
            'top_performers': sorted(operator_performance.items(), 
                                   key=lambda x: x[1]['performance_score'], 
                                   reverse=True)[:5],
            'attention_needed': sorted(operator_performance.items(), 
                                     key=lambda x: x[1]['performance_score'])[:3]
        }

# Global instance for easy access
monday_engine = MondayAttendanceEngine()