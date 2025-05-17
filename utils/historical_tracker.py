"""
Historical Data Tracking and Trend Analysis Module

This module provides tools for tracking historical data across PM allocations,
equipment usage, and billing patterns, allowing for trend analysis and
performance forecasting.
"""

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

logger = logging.getLogger(__name__)

# Set up directories
BASE_DIR = Path('.')
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR = DATA_DIR / 'history'
HISTORY_DIR.mkdir(exist_ok=True)
CHARTS_DIR = BASE_DIR / 'static' / 'charts'
CHARTS_DIR.mkdir(exist_ok=True, parents=True)

# Database connection (read from environment variable)
try:
    DB_URL = os.environ.get('DATABASE_URL')
    engine = create_engine(DB_URL) if DB_URL else None
except Exception as e:
    logger.error(f"Error setting up database connection: {str(e)}")
    engine = None


class HistoricalDataTracker:
    """
    Class for tracking and analyzing historical data across multiple dimensions
    """
    
    def __init__(self, use_db=True):
        """
        Initialize the historical data tracker
        
        Args:
            use_db (bool): Whether to use database for storage (vs. file-based)
        """
        self.use_db = use_db and engine is not None
        
        # Load existing historical data if available
        self.history = {}
        try:
            if self.use_db:
                # Load from database
                self._load_history_from_db()
            else:
                # Load from file
                history_file = HISTORY_DIR / 'allocation_history.json'
                if history_file.exists():
                    with open(history_file, 'r') as f:
                        self.history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
    
    def _load_history_from_db(self):
        """Load historical data from database"""
        if not engine:
            return
            
        try:
            # Check if history table exists
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'pm_allocation_history'
                    )
                """))
                if not result.scalar():
                    # Table doesn't exist yet
                    return
                    
                # Load history from database
                result = conn.execute(text("""
                    SELECT month_year, data 
                    FROM pm_allocation_history
                    ORDER BY created_at DESC
                """))
                
                for row in result:
                    self.history[row[0]] = json.loads(row[1])
        except SQLAlchemyError as e:
            logger.error(f"Database error loading history: {str(e)}")
    
    def _ensure_history_table(self):
        """Ensure the history table exists in the database"""
        if not engine:
            return False
            
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pm_allocation_history (
                        id SERIAL PRIMARY KEY,
                        month_year VARCHAR(50) NOT NULL,
                        data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                conn.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error creating history table: {str(e)}")
            return False
    
    def add_allocation_data(self, month_year, allocation_data, metadata=None):
        """
        Add new allocation data to the historical record
        
        Args:
            month_year (str): Month and year identifier (e.g., 'April 2025')
            allocation_data (DataFrame): PM allocation data
            metadata (dict, optional): Additional metadata about this allocation
        
        Returns:
            bool: Whether the operation was successful
        """
        try:
            # Convert to serializable format
            if isinstance(allocation_data, pd.DataFrame):
                data_dict = allocation_data.to_dict(orient='records')
            else:
                data_dict = allocation_data
                
            # Add metadata
            record = {
                'data': data_dict,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Add to history
            self.history[month_year] = record
            
            # Save to persistent storage
            if self.use_db:
                if self._ensure_history_table():
                    with engine.connect() as conn:
                        # Check if record already exists
                        result = conn.execute(text("""
                            SELECT id FROM pm_allocation_history
                            WHERE month_year = :month_year
                        """), {"month_year": month_year})
                        
                        row = result.fetchone()
                        
                        if row:
                            # Update existing record
                            conn.execute(text("""
                                UPDATE pm_allocation_history
                                SET data = :data::jsonb, updated_at = NOW()
                                WHERE id = :id
                            """), {"id": row[0], "data": json.dumps(record)})
                        else:
                            # Insert new record
                            conn.execute(text("""
                                INSERT INTO pm_allocation_history (month_year, data)
                                VALUES (:month_year, :data::jsonb)
                            """), {"month_year": month_year, "data": json.dumps(record)})
                        
                        conn.commit()
            else:
                # Save to file
                history_file = HISTORY_DIR / 'allocation_history.json'
                with open(history_file, 'w') as f:
                    json.dump(self.history, f)
                    
            return True
        except Exception as e:
            logger.error(f"Error adding allocation data: {str(e)}")
            return False

    def get_allocation_history(self, months=6):
        """
        Get historical allocation data for the last N months
        
        Args:
            months (int): Number of months of history to retrieve
            
        Returns:
            dict: Historical allocation data by month
        """
        try:
            # Sort by month/year in descending order
            sorted_history = {}
            
            # Parse month/year strings and sort chronologically
            month_map = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            
            # Convert to sortable format (year, month)
            dated_history = []
            for month_year, data in self.history.items():
                try:
                    parts = month_year.split()
                    if len(parts) == 2:
                        month, year = parts
                        month_num = month_map.get(month, 0)
                        year_num = int(year)
                        dated_history.append(((year_num, month_num), month_year, data))
                except Exception:
                    # Skip entries with invalid format
                    continue
            
            # Sort by date (newest first) and take last N months
            dated_history.sort(reverse=True)
            for _, month_year, data in dated_history[:months]:
                sorted_history[month_year] = data
            
            return sorted_history
        except Exception as e:
            logger.error(f"Error retrieving allocation history: {str(e)}")
            return {}

    def generate_equipment_usage_trend(self, equipment_id=None, job_number=None, months=6):
        """
        Generate usage trend analysis for a specific equipment or job
        
        Args:
            equipment_id (str, optional): Equipment ID to analyze
            job_number (str, optional): Job number to analyze
            months (int): Number of months to include
            
        Returns:
            dict: Trend analysis data and metadata
        """
        try:
            history = self.get_allocation_history(months=months)
            
            # Prepare data structure for trend analysis
            trend_data = {
                'months': [],
                'days_allocated': [],
                'total_amount': [],
                'utilization_rate': [],
                'jobs': [],
                'cost_codes': {},
                'billing_by_job': {},
                'attendance_correlation': []
            }
            
            # Process history data
            for month_year, record in history.items():
                allocation_data = record.get('data', [])
                
                # Filter data based on equipment_id and/or job_number
                filtered_data = []
                for item in allocation_data:
                    if equipment_id and item.get('equipment_id') != equipment_id:
                        continue
                    if job_number and item.get('job_number') != job_number:
                        continue
                    filtered_data.append(item)
                
                if filtered_data:
                    # Calculate metrics
                    total_days = sum(item.get('days', 0) for item in filtered_data)
                    total_amount = sum(item.get('amount', 0) for item in filtered_data)
                    
                    # Calculate utilization rate (days allocated / days in month)
                    month, year = month_year.split()
                    days_in_month = 30  # Default
                    month_num = {'January': 1, 'February': 2, 'March': 3, 'April': 4,
                               'May': 5, 'June': 6, 'July': 7, 'August': 8,
                               'September': 9, 'October': 10, 'November': 11, 'December': 12}.get(month, 0)
                    year_num = int(year)
                    
                    if month_num in [4, 6, 9, 11]:
                        days_in_month = 30
                    elif month_num == 2:
                        days_in_month = 29 if (year_num % 4 == 0 and year_num % 100 != 0) or (year_num % 400 == 0) else 28
                    else:
                        days_in_month = 31
                    
                    utilization_rate = (total_days / days_in_month) * 100 if days_in_month > 0 else 0
                    
                    # Track jobs this equipment worked on
                    unique_jobs = set(item.get('job_number') for item in filtered_data 
                                     if item.get('job_number'))
                    
                    # Collect billing by job
                    billing_by_job = {}
                    for item in filtered_data:
                        job = item.get('job_number')
                        if job:
                            if job not in billing_by_job:
                                billing_by_job[job] = {
                                    'amount': 0,
                                    'days': 0,
                                    'cost_codes': {}
                                }
                            
                            amount = item.get('amount', 0)
                            days = item.get('days', 0)
                            cost_code = item.get('cost_code', 'Unknown')
                            
                            billing_by_job[job]['amount'] += amount
                            billing_by_job[job]['days'] += days
                            
                            # Track cost codes
                            if cost_code:
                                billing_by_job[job]['cost_codes'][cost_code] = \
                                    billing_by_job[job]['cost_codes'].get(cost_code, 0) + amount
                    
                    # Aggregate cost codes across all jobs for this month
                    month_cost_codes = {}
                    for job_data in billing_by_job.values():
                        for code, amount in job_data['cost_codes'].items():
                            month_cost_codes[code] = month_cost_codes.get(code, 0) + amount
                    
                    # Fetch attendance data if available
                    attendance_correlation = 0
                    try:
                        # This would connect to the attendance database
                        # For now, we'll use a placeholder value
                        # In a real implementation, this would query the attendance_records table
                        attendance_correlation = 0.85  # Placeholder
                    except Exception as e:
                        logger.warning(f"Could not fetch attendance data: {str(e)}")
                    
                    # Add to trend data
                    trend_data['months'].append(month_year)
                    trend_data['days_allocated'].append(total_days)
                    trend_data['total_amount'].append(total_amount)
                    trend_data['utilization_rate'].append(utilization_rate)
                    trend_data['jobs'].append(len(unique_jobs))
                    trend_data['cost_codes'][month_year] = month_cost_codes
                    trend_data['billing_by_job'][month_year] = billing_by_job
                    trend_data['attendance_correlation'].append(attendance_correlation)
            
            # Calculate trend indicators
            if len(trend_data['months']) > 1:
                # Days trend
                days_trend = calculate_trend(trend_data['days_allocated'])
                
                # Amount trend
                amount_trend = calculate_trend(trend_data['total_amount'])
                
                # Utilization trend
                utilization_trend = calculate_trend(trend_data['utilization_rate'])
                
                # Jobs count trend
                jobs_trend = calculate_trend(trend_data['jobs'])
                
                # Cost code distribution trend
                cost_code_trends = {}
                all_cost_codes = set()
                for month_codes in trend_data['cost_codes'].values():
                    all_cost_codes.update(month_codes.keys())
                
                for code in all_cost_codes:
                    code_values = []
                    for month in trend_data['months']:
                        month_codes = trend_data['cost_codes'].get(month, {})
                        code_values.append(month_codes.get(code, 0))
                    
                    if any(code_values) and len(code_values) > 1:
                        cost_code_trends[code] = calculate_trend(code_values)
                
                # Forecast next month (simple linear regression)
                next_days = forecast_next_value(trend_data['days_allocated'])
                next_amount = forecast_next_value(trend_data['total_amount'])
                next_utilization = forecast_next_value(trend_data['utilization_rate'])
                next_jobs = forecast_next_value(trend_data['jobs'])
                
                # Calculate per-job forecasts
                job_forecasts = {}
                all_jobs = set()
                for month_jobs in trend_data['billing_by_job'].values():
                    all_jobs.update(month_jobs.keys())
                
                for job in all_jobs:
                    job_amounts = []
                    for month in trend_data['months']:
                        month_jobs = trend_data['billing_by_job'].get(month, {})
                        job_data = month_jobs.get(job, {})
                        job_amounts.append(job_data.get('amount', 0))
                    
                    if any(job_amounts) and len(job_amounts) > 1:
                        job_forecasts[job] = {
                            'trend': calculate_trend(job_amounts),
                            'forecast': forecast_next_value(job_amounts)
                        }
                
                trend_result = {
                    'data': trend_data,
                    'trends': {
                        'days_trend': days_trend,
                        'amount_trend': amount_trend,
                        'utilization_trend': utilization_trend,
                        'jobs_trend': jobs_trend,
                        'cost_code_trends': cost_code_trends
                    },
                    'forecast': {
                        'next_days': next_days,
                        'next_amount': next_amount,
                        'next_utilization': next_utilization,
                        'next_jobs': next_jobs,
                        'job_forecasts': job_forecasts
                    }
                }
                
                # Generate chart if data exists
                if len(trend_data['months']) > 1:
                    chart_path = self.generate_trend_chart(
                        trend_data, 
                        title=f"Equipment Trend: {equipment_id}" if equipment_id else f"Job Trend: {job_number}",
                        filename=f"trend_{equipment_id or job_number}_{datetime.now().strftime('%Y%m%d')}.png"
                    )
                    if chart_path:
                        trend_result['chart_path'] = chart_path
                    
                    # Generate additional job-specific chart for equipment
                    if equipment_id and trend_data['billing_by_job']:
                        job_chart_path = self.generate_job_billing_chart(
                            trend_data,
                            title=f"Job Billing for Equipment: {equipment_id}",
                            filename=f"job_billing_{equipment_id}_{datetime.now().strftime('%Y%m%d')}.png"
                        )
                        if job_chart_path:
                            trend_result['job_chart_path'] = job_chart_path
                    
                    # Generate cost code distribution chart
                    if trend_data['cost_codes']:
                        cost_code_chart_path = self.generate_cost_code_chart(
                            trend_data,
                            title=f"Cost Code Distribution: {equipment_id or job_number}",
                            filename=f"cost_code_{equipment_id or job_number}_{datetime.now().strftime('%Y%m%d')}.png"
                        )
                        if cost_code_chart_path:
                            trend_result['cost_code_chart_path'] = cost_code_chart_path
                
                return trend_result
            else:
                return {
                    'data': trend_data,
                    'error': 'Insufficient data for trend analysis (need at least 2 months)'
                }
                
        except Exception as e:
            logger.error(f"Error generating trend analysis: {str(e)}")
            return {'error': str(e)}

    def generate_trend_chart(self, trend_data, title="Equipment Trend Analysis", filename=None):
        """
        Generate a chart for trend visualization
        
        Args:
            trend_data (dict): Trend data structure
            title (str): Chart title
            filename (str, optional): Filename for saving chart
            
        Returns:
            str: Path to the generated chart file, or None if failed
        """
        try:
            # Create figure with dual Y-axis
            fig, ax1 = plt.subplots(figsize=(12, 7))
            
            # Plot days allocated (primary Y-axis)
            color = 'tab:blue'
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Days Allocated', color=color)
            ax1.plot(trend_data['months'], trend_data['days_allocated'], marker='o', color=color, label='Days')
            ax1.tick_params(axis='y', labelcolor=color)
            
            # Create second Y-axis for amount
            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('Amount ($)', color=color)
            ax2.plot(trend_data['months'], trend_data['total_amount'], marker='s', color=color, label='Amount')
            ax2.tick_params(axis='y', labelcolor=color)
            
            # Utilization line
            color = 'tab:green'
            ax3 = ax1.twinx()
            ax3.spines['right'].set_position(('outward', 60))
            ax3.set_ylabel('Utilization Rate (%)', color=color)
            ax3.plot(trend_data['months'], trend_data['utilization_rate'], marker='^', color=color, 
                    linestyle='--', label='Utilization')
            ax3.tick_params(axis='y', labelcolor=color)
            ax3.set_ylim([0, 100])
            
            # Job count line if available
            if 'jobs' in trend_data and trend_data['jobs']:
                color = 'tab:orange'
                ax4 = ax1.twinx()
                ax4.spines['right'].set_position(('outward', 120))
                ax4.set_ylabel('Jobs Count', color=color)
                ax4.plot(trend_data['months'], trend_data['jobs'], marker='d', color=color, 
                        linestyle=':', label='Jobs')
                ax4.tick_params(axis='y', labelcolor=color)
                # Set appropriate y limit for job count
                if max(trend_data['jobs']) > 0:
                    ax4.set_ylim([0, max(trend_data['jobs']) * 1.2])
                
                # Update legend to include job count
                lines4, labels4 = ax4.get_legend_handles_labels()
            else:
                lines4, labels4 = [], []
            
            # Add grid and title
            ax1.grid(True, alpha=0.3)
            plt.title(title)
            
            # Adjust x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Add legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            lines3, labels3 = ax3.get_legend_handles_labels()
            ax1.legend(lines1 + lines2 + lines3 + lines4, 
                      labels1 + labels2 + labels3 + labels4, 
                      loc='upper center', 
                      bbox_to_anchor=(0.5, -0.15), 
                      ncol=4)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            if not filename:
                filename = f"trend_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
            chart_path = CHARTS_DIR / filename
            plt.savefig(chart_path)
            plt.close()
            
            return str(chart_path.relative_to(BASE_DIR))
            
        except Exception as e:
            logger.error(f"Error generating trend chart: {str(e)}")
            return None
            
    def generate_job_billing_chart(self, trend_data, title="Job Billing Analysis", filename=None):
        """
        Generate a chart showing billing breakdown by job
        
        Args:
            trend_data (dict): Trend data structure
            title (str): Chart title
            filename (str, optional): Filename for saving chart
            
        Returns:
            str: Path to the generated chart file, or None if failed
        """
        try:
            # Extract job billing data across months
            months = trend_data['months']
            billing_by_job = trend_data['billing_by_job']
            
            # Get all unique jobs across all months
            all_jobs = set()
            for month_data in billing_by_job.values():
                all_jobs.update(month_data.keys())
                
            if not all_jobs:
                logger.warning("No job billing data available for chart")
                return None
                
            # Prepare data for stacked bar chart
            job_data = {}
            for job in all_jobs:
                job_data[job] = []
                for month in months:
                    month_jobs = billing_by_job.get(month, {})
                    job_amount = month_jobs.get(job, {}).get('amount', 0) if job in month_jobs else 0
                    job_data[job].append(job_amount)
            
            # Create the stacked bar chart
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Sort jobs by total amount (descending)
            sorted_jobs = sorted(
                job_data.keys(),
                key=lambda j: sum(job_data[j]),
                reverse=True
            )
            
            # Generate distinct colors for each job
            colors = plt.cm.tab20(np.linspace(0, 1, len(sorted_jobs)))
            
            # Plot stacked bars
            bottom = np.zeros(len(months))
            for i, job in enumerate(sorted_jobs):
                ax.bar(months, job_data[job], bottom=bottom, label=f"Job {job}", color=colors[i % len(colors)])
                bottom += np.array(job_data[job])
            
            # Add chart elements
            ax.set_title(title)
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            if not filename:
                filename = f"job_billing_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
            chart_path = CHARTS_DIR / filename
            plt.savefig(chart_path)
            plt.close()
            
            return str(chart_path.relative_to(BASE_DIR))
            
        except Exception as e:
            logger.error(f"Error generating job billing chart: {str(e)}")
            return None
            
    def generate_cost_code_chart(self, trend_data, title="Cost Code Distribution", filename=None):
        """
        Generate a chart showing cost code distribution over time
        
        Args:
            trend_data (dict): Trend data structure
            title (str): Chart title
            filename (str, optional): Filename for saving chart
            
        Returns:
            str: Path to the generated chart file, or None if failed
        """
        try:
            # Extract cost code data across months
            months = trend_data['months']
            cost_codes = trend_data['cost_codes']
            
            if not cost_codes:
                logger.warning("No cost code data available for chart")
                return None
                
            # Get all unique cost codes across all months
            all_codes = set()
            for month_data in cost_codes.values():
                all_codes.update(month_data.keys())
                
            # Prepare data for area chart
            code_data = {}
            for code in all_codes:
                code_data[code] = []
                for month in months:
                    month_codes = cost_codes.get(month, {})
                    code_amount = month_codes.get(code, 0)
                    code_data[code].append(code_amount)
            
            # Create multiple subplots for different views
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Sort codes by total amount (descending)
            sorted_codes = sorted(
                code_data.keys(),
                key=lambda c: sum(code_data[c]),
                reverse=True
            )
            
            # Generate distinct colors for each cost code
            colors = plt.cm.tab20(np.linspace(0, 1, len(sorted_codes)))
            
            # 1. Stacked area chart (left)
            y_stack = np.zeros(len(months))
            for i, code in enumerate(sorted_codes):
                ax1.fill_between(months, y_stack, y_stack + np.array(code_data[code]), 
                                label=code, alpha=0.7, color=colors[i % len(colors)])
                y_stack += np.array(code_data[code])
                
            ax1.set_title("Cost Code Distribution Over Time")
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Amount ($)')
            
            # 2. Pie chart of average distribution (right)
            code_totals = {code: sum(values) for code, values in code_data.items()}
            total_amount = sum(code_totals.values())
            
            # Filter out small segments (less than 3% of total) for readability
            threshold = total_amount * 0.03
            other_total = 0
            filtered_codes = {}
            
            for code, amount in code_totals.items():
                if amount >= threshold:
                    filtered_codes[code] = amount
                else:
                    other_total += amount
                    
            if other_total > 0:
                filtered_codes['Other Cost Codes'] = other_total
                
            # Plot pie chart
            wedges, texts, autotexts = ax2.pie(
                filtered_codes.values(), 
                labels=filtered_codes.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=plt.cm.tab20(np.linspace(0, 1, len(filtered_codes)))
            )
            
            # Make text white for better visibility on dark segments
            for text in autotexts:
                text.set_color('white')
                
            ax2.set_title("Average Cost Code Distribution")
            
            # Adjust legend and layout
            ax1.legend(loc='upper left', bbox_to_anchor=(1, 1))
            
            # Rotate x-axis labels for better readability
            ax1.tick_params(axis='x', rotation=45)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            if not filename:
                filename = f"cost_code_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                
            chart_path = CHARTS_DIR / filename
            plt.savefig(chart_path)
            plt.close()
            
            return str(chart_path.relative_to(BASE_DIR))
            
        except Exception as e:
            logger.error(f"Error generating cost code chart: {str(e)}")
            return None

    def generate_summary_report(self, months=6):
        """
        Generate a comprehensive summary report across all historical data
        
        Args:
            months (int): Number of months to include
            
        Returns:
            dict: Summary report data
        """
        try:
            history = self.get_allocation_history(months=months)
            
            # Initialize summary structure
            summary = {
                'months_analyzed': len(history),
                'total_equipment_count': set(),
                'total_job_count': set(),
                'monthly_totals': {},
                'equipment_utilization': {},
                'job_allocation': {},
                'top_equipment': [],
                'top_jobs': [],
                'trend_indicators': {}
            }
            
            # Process historical data
            monthly_data = []
            
            for month_year, record in history.items():
                allocation_data = record.get('data', [])
                
                # Monthly statistics
                equipment_set = set()
                job_set = set()
                monthly_amount = 0
                monthly_days = 0
                
                # Equipment and job counters for this month
                equipment_counter = {}
                job_counter = {}
                
                for item in allocation_data:
                    equipment_id = item.get('equipment_id')
                    job_number = item.get('job_number')
                    days = item.get('days', 0)
                    amount = item.get('amount', 0)
                    
                    if equipment_id:
                        equipment_set.add(equipment_id)
                        summary['total_equipment_count'].add(equipment_id)
                        
                        # Update equipment counter
                        if equipment_id not in equipment_counter:
                            equipment_counter[equipment_id] = {'days': 0, 'amount': 0}
                        equipment_counter[equipment_id]['days'] += days
                        equipment_counter[equipment_id]['amount'] += amount
                    
                    if job_number:
                        job_set.add(job_number)
                        summary['total_job_count'].add(job_number)
                        
                        # Update job counter
                        if job_number not in job_counter:
                            job_counter[job_number] = {'days': 0, 'amount': 0}
                        job_counter[job_number]['days'] += days
                        job_counter[job_number]['amount'] += amount
                    
                    monthly_amount += amount
                    monthly_days += days
                
                # Add monthly totals
                summary['monthly_totals'][month_year] = {
                    'equipment_count': len(equipment_set),
                    'job_count': len(job_set),
                    'total_amount': monthly_amount,
                    'total_days': monthly_days
                }
                
                # Update equipment utilization data
                for equipment_id, data in equipment_counter.items():
                    if equipment_id not in summary['equipment_utilization']:
                        summary['equipment_utilization'][equipment_id] = []
                    
                    summary['equipment_utilization'][equipment_id].append({
                        'month': month_year,
                        'days': data['days'],
                        'amount': data['amount']
                    })
                
                # Update job allocation data
                for job_number, data in job_counter.items():
                    if job_number not in summary['job_allocation']:
                        summary['job_allocation'][job_number] = []
                    
                    summary['job_allocation'][job_number].append({
                        'month': month_year,
                        'days': data['days'],
                        'amount': data['amount']
                    })
                
                # Save month data for trend analysis
                monthly_data.append({
                    'month': month_year,
                    'equipment_count': len(equipment_set),
                    'job_count': len(job_set),
                    'total_amount': monthly_amount,
                    'total_days': monthly_days
                })
            
            # Calculate top equipment by total amount
            equipment_totals = {}
            for equipment_id, data in summary['equipment_utilization'].items():
                equipment_totals[equipment_id] = sum(item['amount'] for item in data)
            
            summary['top_equipment'] = sorted(
                [{'equipment_id': k, 'total_amount': v} for k, v in equipment_totals.items()],
                key=lambda x: x['total_amount'],
                reverse=True
            )[:10]  # Top 10
            
            # Calculate top jobs by total amount
            job_totals = {}
            for job_number, data in summary['job_allocation'].items():
                job_totals[job_number] = sum(item['amount'] for item in data)
            
            summary['top_jobs'] = sorted(
                [{'job_number': k, 'total_amount': v} for k, v in job_totals.items()],
                key=lambda x: x['total_amount'],
                reverse=True
            )[:10]  # Top 10
            
            # Calculate trend indicators from monthly data
            if len(monthly_data) > 1:
                # Sort by month chronologically
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                
                monthly_data.sort(key=lambda x: (
                    int(x['month'].split()[1]),  # Year
                    month_map.get(x['month'].split()[0], 0)  # Month
                ))
                
                # Calculate trends
                summary['trend_indicators'] = {
                    'amount_trend': calculate_trend([item['total_amount'] for item in monthly_data]),
                    'days_trend': calculate_trend([item['total_days'] for item in monthly_data]),
                    'equipment_count_trend': calculate_trend([item['equipment_count'] for item in monthly_data]),
                    'job_count_trend': calculate_trend([item['job_count'] for item in monthly_data])
                }
                
                # Generate forecasts
                summary['forecasts'] = {
                    'next_month_amount': forecast_next_value([item['total_amount'] for item in monthly_data]),
                    'next_month_days': forecast_next_value([item['total_days'] for item in monthly_data])
                }
                
                # Generate summary chart
                summary['chart_path'] = self.generate_summary_chart(monthly_data)
            
            # Convert sets to counts
            summary['total_equipment_count'] = len(summary['total_equipment_count'])
            summary['total_job_count'] = len(summary['total_job_count'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return {'error': str(e)}

    def generate_summary_chart(self, monthly_data):
        """
        Generate a summary chart from monthly data
        
        Args:
            monthly_data (list): List of monthly data dictionaries
            
        Returns:
            str: Path to the generated chart file, or None if failed
        """
        try:
            # Extract data series
            months = [item['month'] for item in monthly_data]
            amounts = [item['total_amount'] for item in monthly_data]
            days = [item['total_days'] for item in monthly_data]
            equipment_counts = [item['equipment_count'] for item in monthly_data]
            
            # Create figure with multiple subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            # Plot total amount and days
            ax1.set_ylabel('Amount ($)')
            line1 = ax1.plot(months, amounts, marker='o', color='tab:blue', label='Total Amount')
            
            # Add days allocated on secondary Y-axis
            ax1_twin = ax1.twinx()
            ax1_twin.set_ylabel('Days')
            line2 = ax1_twin.plot(months, days, marker='s', color='tab:orange', label='Total Days')
            
            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc='upper left')
            
            # Plot equipment and job counts
            ax2.set_ylabel('Count')
            ax2.plot(months, equipment_counts, marker='^', color='tab:green', label='Equipment Count')
            ax2.set_xlabel('Month')
            
            # Format x-axis
            plt.xticks(rotation=45)
            
            # Add grid
            ax1.grid(True, alpha=0.3)
            ax2.grid(True, alpha=0.3)
            
            # Add title
            plt.suptitle('Monthly Billing Summary', fontsize=16)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save chart
            filename = f"summary_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            chart_path = CHARTS_DIR / filename
            plt.savefig(chart_path)
            plt.close()
            
            return str(chart_path.relative_to(BASE_DIR))
            
        except Exception as e:
            logger.error(f"Error generating summary chart: {str(e)}")
            return None


def calculate_trend(values):
    """
    Calculate trend direction and magnitude from a series of values
    
    Args:
        values (list): List of numeric values
        
    Returns:
        dict: Trend information including direction, magnitude and confidence
    """
    if len(values) < 2:
        return {
            'direction': 'neutral',
            'magnitude': 0,
            'confidence': 0
        }
    
    try:
        # Calculate linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Handle constant values
        if np.all(y == y[0]):
            return {
                'direction': 'neutral',
                'magnitude': 0,
                'confidence': 1.0  # High confidence in flat trend
            }
        
        # Calculate slope and R-squared
        n = len(x)
        xy_sum = np.sum(x * y)
        x_sum = np.sum(x)
        y_sum = np.sum(y)
        x_squared_sum = np.sum(x ** 2)
        
        # Calculate slope
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum ** 2)
        
        # Calculate y-intercept
        b = (y_sum - slope * x_sum) / n
        
        # Calculate predicted values
        y_pred = b + slope * x
        
        # Calculate R-squared
        ss_total = np.sum((y - np.mean(y)) ** 2)
        ss_residual = np.sum((y - y_pred) ** 2)
        r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
        
        # Determine direction and magnitude
        direction = 'up' if slope > 0 else 'down' if slope < 0 else 'neutral'
        
        # Normalize magnitude to [0, 1] based on percentage change
        first_value = values[0] if values[0] != 0 else 0.0001  # Avoid division by zero
        total_change = (values[-1] - first_value) / first_value
        
        # Limit to reasonable range [-1, 1]
        magnitude = max(min(total_change, 1), -1)
        
        return {
            'direction': direction,
            'magnitude': magnitude,
            'confidence': r_squared,
            'slope': slope
        }
        
    except Exception as e:
        logger.error(f"Error calculating trend: {str(e)}")
        return {
            'direction': 'error',
            'magnitude': 0,
            'confidence': 0,
            'error': str(e)
        }


def forecast_next_value(values, periods=1):
    """
    Forecast the next value in a series using simple linear regression
    
    Args:
        values (list): List of historical values
        periods (int): Number of periods to forecast ahead
        
    Returns:
        float: Forecasted value
    """
    if len(values) < 2:
        # Not enough data, return last value or zero
        return values[-1] if values else 0
    
    try:
        # Calculate linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope and intercept
        n = len(x)
        xy_sum = np.sum(x * y)
        x_sum = np.sum(x)
        y_sum = np.sum(y)
        x_squared_sum = np.sum(x ** 2)
        
        # Calculate slope
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum ** 2)
        
        # Calculate y-intercept
        b = (y_sum - slope * x_sum) / n
        
        # Forecast next value(s)
        next_value = b + slope * (len(values) + periods - 1)
        
        # Ensure forecast is not negative for quantities
        return max(0, next_value)
        
    except Exception as e:
        logger.error(f"Error forecasting next value: {str(e)}")
        # Return the last value as fallback
        return values[-1] if values else 0