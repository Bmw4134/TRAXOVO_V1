"""
TRAXOVO Agent Integration - Equipment Billing Automation
Reconstructed from existing modules to fix 400 Bad Request errors
"""

import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import sqlite3

class TRAXOVOAgent:
    """TRAXOVO Autonomous Agent for Equipment Billing and Fleet Management"""
    
    def __init__(self):
        self.database_file = "traxovo_agent.db"
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize TRAXOVO agent database"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Equipment billing table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_billing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT,
                    billing_period TEXT,
                    amount DECIMAL(10,2),
                    status TEXT,
                    processed_date TIMESTAMP,
                    automation_notes TEXT
                )
            ''')
            
            # Daily driver reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_driver_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_id TEXT,
                    report_date DATE,
                    hours_worked DECIMAL(5,2),
                    miles_driven INTEGER,
                    equipment_used TEXT,
                    status TEXT,
                    processed_timestamp TIMESTAMP
                )
            ''')
            
            # Fleet optimization table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fleet_optimization (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    optimization_date DATE,
                    recommendations TEXT,
                    cost_savings DECIMAL(10,2),
                    implementation_status TEXT,
                    created_timestamp TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("TRAXOVO agent database initialized")
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
    
    def daily_driver_report(self, driver_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process daily driver report with automation"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Extract driver information
            driver_id = driver_data.get('driver_id', 'UNKNOWN')
            report_date = driver_data.get('date', datetime.now().date())
            hours_worked = driver_data.get('hours', 0.0)
            miles_driven = driver_data.get('miles', 0)
            equipment_used = json.dumps(driver_data.get('equipment', []))
            
            # Insert daily report
            cursor.execute('''
                INSERT INTO daily_driver_reports 
                (driver_id, report_date, hours_worked, miles_driven, equipment_used, status, processed_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (driver_id, report_date, hours_worked, miles_driven, equipment_used, 'processed', datetime.now()))
            
            conn.commit()
            conn.close()
            
            # Generate automation insights
            insights = self._generate_driver_insights(driver_data)
            
            return {
                'status': 'success',
                'driver_id': driver_id,
                'report_processed': True,
                'automation_insights': insights,
                'processed_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Daily driver report error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def equipment_monthly_billing(self, billing_period: str = None) -> Dict[str, Any]:
        """Process monthly equipment billing automation"""
        try:
            if not billing_period:
                billing_period = datetime.now().strftime('%Y-%m')
            
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Generate billing data from daily reports
            cursor.execute('''
                SELECT equipment_used, COUNT(*) as usage_count, SUM(hours_worked) as total_hours
                FROM daily_driver_reports 
                WHERE strftime('%Y-%m', report_date) = ?
                GROUP BY equipment_used
            ''', (billing_period,))
            
            equipment_usage = cursor.fetchall()
            
            billing_summary = []
            total_billing = 0.0
            
            for equipment_json, usage_count, total_hours in equipment_usage:
                try:
                    equipment_list = json.loads(equipment_json)
                    for equipment in equipment_list:
                        # Calculate billing based on usage
                        base_rate = 150.0  # Base hourly rate
                        equipment_cost = total_hours * base_rate * 0.1  # 10% of hourly rate
                        
                        billing_entry = {
                            'equipment_id': equipment,
                            'usage_count': usage_count,
                            'total_hours': total_hours,
                            'calculated_cost': equipment_cost,
                            'billing_period': billing_period
                        }
                        
                        billing_summary.append(billing_entry)
                        total_billing += equipment_cost
                        
                        # Store in database
                        cursor.execute('''
                            INSERT INTO equipment_billing 
                            (equipment_id, billing_period, amount, status, processed_date, automation_notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (equipment, billing_period, equipment_cost, 'calculated', datetime.now(), 
                              f'Auto-calculated from {usage_count} usage records'))
                
                except json.JSONDecodeError:
                    continue
            
            conn.commit()
            conn.close()
            
            return {
                'status': 'success',
                'billing_period': billing_period,
                'total_equipment_cost': total_billing,
                'equipment_breakdown': billing_summary,
                'automation_status': 'completed',
                'processed_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Equipment billing error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_driver_insights(self, driver_data: Dict[str, Any]) -> List[str]:
        """Generate automation insights for driver performance"""
        insights = []
        
        hours = driver_data.get('hours', 0)
        miles = driver_data.get('miles', 0)
        
        if hours > 10:
            insights.append("Driver worked overtime - consider workload redistribution")
        
        if miles > 500:
            insights.append("High mileage day - monitor vehicle maintenance")
        
        if hours > 0 and miles > 0:
            efficiency = miles / hours
            if efficiency > 50:
                insights.append(f"High efficiency: {efficiency:.1f} miles/hour")
            elif efficiency < 20:
                insights.append(f"Low efficiency: {efficiency:.1f} miles/hour - investigate delays")
        
        return insights
    
    def get_fleet_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate fleet optimization recommendations"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Analyze recent driver data
            cursor.execute('''
                SELECT AVG(hours_worked), AVG(miles_driven), COUNT(*)
                FROM daily_driver_reports 
                WHERE report_date >= date('now', '-30 days')
            ''')
            
            avg_hours, avg_miles, total_reports = cursor.fetchone()
            
            recommendations = []
            cost_savings = 0.0
            
            if avg_hours and avg_hours > 9:
                recommendations.append("Consider hiring additional drivers to reduce overtime")
                cost_savings += 5000  # Estimated monthly savings
            
            if avg_miles and avg_miles > 400:
                recommendations.append("Optimize routing to reduce average daily mileage")
                cost_savings += 2500  # Fuel savings
            
            if total_reports < 20:
                recommendations.append("Increase driver utilization to maximize fleet efficiency")
                cost_savings += 3000  # Revenue opportunity
            
            # Store optimization recommendations
            cursor.execute('''
                INSERT INTO fleet_optimization 
                (optimization_date, recommendations, cost_savings, implementation_status, created_timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().date(), json.dumps(recommendations), cost_savings, 'pending', datetime.now()))
            
            conn.commit()
            conn.close()
            
            return {
                'status': 'success',
                'recommendations': recommendations,
                'estimated_monthly_savings': cost_savings,
                'analysis_period': '30 days',
                'generated_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Fleet optimization error: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current TRAXOVO agent status"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Count recent records
            cursor.execute('SELECT COUNT(*) FROM daily_driver_reports WHERE report_date >= date("now", "-7 days")')
            recent_reports = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM equipment_billing WHERE processed_date >= datetime("now", "-30 days")')
            recent_billing = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM fleet_optimization WHERE created_timestamp >= datetime("now", "-30 days")')
            recent_optimizations = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'operational',
                'recent_driver_reports': recent_reports,
                'recent_billing_records': recent_billing,
                'recent_optimizations': recent_optimizations,
                'agent_health': 'healthy',
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
traxovo_agent = TRAXOVOAgent()

def process_daily_driver_report(driver_data):
    """Process daily driver report"""
    return traxovo_agent.daily_driver_report(driver_data)

def process_equipment_billing(billing_period=None):
    """Process monthly equipment billing"""
    return traxovo_agent.equipment_monthly_billing(billing_period)

def get_fleet_recommendations():
    """Get fleet optimization recommendations"""
    return traxovo_agent.get_fleet_optimization_recommendations()

def get_traxovo_status():
    """Get TRAXOVO agent status"""
    return traxovo_agent.get_agent_status()