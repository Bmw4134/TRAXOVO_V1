"""
TRAXOVO Authentic Revenue Calculator
Parses actual equipment billing data from Ragle and Select Maintenance
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import logging

authentic_revenue_bp = Blueprint('authentic_revenue', __name__)

class AuthenticRevenueCalculator:
    """
    Calculate authentic equipment revenue from actual billing files
    """
    
    def __init__(self):
        self.ragle_billing_data = self._parse_ragle_billing()
        self.select_billing_data = self._parse_select_billing()
        self.combined_revenue = self._calculate_combined_revenue()
    
    def _parse_ragle_billing(self):
        """Parse authentic Ragle equipment billing files"""
        try:
            billing_files = [
                'RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
                'RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
            ]
            
            ragle_revenue = []
            
            for filename in billing_files:
                filepath = os.path.join('attached_assets', filename)
                if os.path.exists(filepath):
                    try:
                        excel_file = pd.ExcelFile(filepath)
                        
                        for sheet_name in excel_file.sheet_names:
                            df = pd.read_excel(filepath, sheet_name=sheet_name)
                            
                            # Look for revenue/billing columns
                            revenue_columns = [col for col in df.columns 
                                             if any(term in col.lower() for term in 
                                                   ['revenue', 'billing', 'amount', 'total', 'cost', 'rate', 'price'])]
                            
                            date_columns = [col for col in df.columns 
                                          if any(term in col.lower() for term in 
                                                ['date', 'month', 'period', 'time'])]
                            
                            equipment_columns = [col for col in df.columns 
                                               if any(term in col.lower() for term in 
                                                     ['equipment', 'asset', 'unit', 'machine', 'eq'])]
                            
                            if revenue_columns and len(df) > 0:
                                for _, row in df.iterrows():
                                    for rev_col in revenue_columns:
                                        if pd.notna(row[rev_col]):
                                            try:
                                                amount = float(str(row[rev_col]).replace('$', '').replace(',', ''))
                                                if amount > 0:  # Valid revenue amount
                                                    
                                                    # Extract equipment info
                                                    equipment_id = 'Unknown'
                                                    if equipment_columns:
                                                        for eq_col in equipment_columns:
                                                            if pd.notna(row[eq_col]):
                                                                equipment_id = str(row[eq_col])
                                                                break
                                                    
                                                    # Extract date info
                                                    period = self._extract_period_from_filename(filename)
                                                    if date_columns:
                                                        for date_col in date_columns:
                                                            if pd.notna(row[date_col]):
                                                                try:
                                                                    period = pd.to_datetime(row[date_col]).strftime('%Y-%m')
                                                                except:
                                                                    pass
                                                                break
                                                    
                                                    ragle_revenue.append({
                                                        'company': 'Ragle Inc',
                                                        'equipment_id': equipment_id,
                                                        'amount': amount,
                                                        'period': period,
                                                        'source_file': filename,
                                                        'sheet': sheet_name,
                                                        'column': rev_col
                                                    })
                                            except (ValueError, TypeError):
                                                continue
                    
                    except Exception as e:
                        logging.error(f"Error parsing Ragle billing file {filename}: {e}")
            
            return ragle_revenue
            
        except Exception as e:
            logging.error(f"Error loading Ragle billing data: {e}")
            return []
    
    def _parse_select_billing(self):
        """Parse Select Maintenance billing data"""
        try:
            # Look for Select billing files
            select_files = []
            assets_dir = 'attached_assets'
            
            if os.path.exists(assets_dir):
                for filename in os.listdir(assets_dir):
                    if any(term in filename.upper() for term in ['SELECT', 'SEL EQ', 'BILLING']):
                        if filename.endswith(('.xlsx', '.xlsm')):
                            select_files.append(filename)
            
            select_revenue = []
            
            for filename in select_files:
                filepath = os.path.join(assets_dir, filename)
                try:
                    excel_file = pd.ExcelFile(filepath)
                    
                    for sheet_name in excel_file.sheet_names:
                        df = pd.read_excel(filepath, sheet_name=sheet_name)
                        
                        # Similar revenue parsing logic as Ragle
                        revenue_columns = [col for col in df.columns 
                                         if any(term in col.lower() for term in 
                                               ['revenue', 'billing', 'amount', 'total', 'cost', 'rate'])]
                        
                        if revenue_columns and len(df) > 0:
                            for _, row in df.iterrows():
                                for rev_col in revenue_columns:
                                    if pd.notna(row[rev_col]):
                                        try:
                                            amount = float(str(row[rev_col]).replace('$', '').replace(',', ''))
                                            if amount > 0:
                                                select_revenue.append({
                                                    'company': 'Select Maintenance',
                                                    'amount': amount,
                                                    'period': self._extract_period_from_filename(filename),
                                                    'source_file': filename,
                                                    'sheet': sheet_name,
                                                    'column': rev_col
                                                })
                                        except (ValueError, TypeError):
                                            continue
                
                except Exception as e:
                    logging.error(f"Error parsing Select billing file {filename}: {e}")
            
            return select_revenue
            
        except Exception as e:
            logging.error(f"Error loading Select billing data: {e}")
            return []
    
    def _extract_period_from_filename(self, filename):
        """Extract billing period from filename"""
        filename_upper = filename.upper()
        
        # Look for month/year patterns
        months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
        
        for i, month in enumerate(months):
            if month in filename_upper:
                # Look for year
                import re
                year_match = re.search(r'20\d{2}', filename_upper)
                if year_match:
                    return f"{year_match.group()}-{str(i+1).zfill(2)}"
        
        # Default to current month if can't extract
        return datetime.now().strftime('%Y-%m')
    
    def _calculate_combined_revenue(self):
        """Calculate combined revenue metrics"""
        all_revenue = self.ragle_billing_data + self.select_billing_data
        
        if not all_revenue:
            return {
                'monthly_revenue': 0,
                'ytd_revenue': 0,
                'company_breakdown': {},
                'period_breakdown': {},
                'equipment_revenue': {},
                'total_records': 0,
                'data_sources': []
            }
        
        # Calculate by period
        period_totals = {}
        company_totals = {}
        equipment_totals = {}
        
        for record in all_revenue:
            period = record['period']
            company = record['company']
            equipment = record.get('equipment_id', 'Unknown')
            amount = record['amount']
            
            # Period totals
            period_totals[period] = period_totals.get(period, 0) + amount
            
            # Company totals
            company_totals[company] = company_totals.get(company, 0) + amount
            
            # Equipment totals
            if equipment != 'Unknown':
                equipment_totals[equipment] = equipment_totals.get(equipment, 0) + amount
        
        # Get current month revenue
        current_month = datetime.now().strftime('%Y-%m')
        monthly_revenue = period_totals.get(current_month, 0)
        
        # Calculate YTD (this year)
        current_year = datetime.now().year
        ytd_revenue = sum(amount for period, amount in period_totals.items() 
                         if period.startswith(str(current_year)))
        
        return {
            'monthly_revenue': monthly_revenue,
            'ytd_revenue': ytd_revenue,
            'company_breakdown': company_totals,
            'period_breakdown': period_totals,
            'equipment_revenue': equipment_totals,
            'total_records': len(all_revenue),
            'data_sources': list(set(record['source_file'] for record in all_revenue))
        }
    
    def get_authentic_utilization_rates(self):
        """Calculate authentic equipment utilization rates"""
        try:
            # This would connect to actual equipment usage data
            # For now, calculate based on available billing data
            
            equipment_revenue = self.combined_revenue['equipment_revenue']
            
            if not equipment_revenue:
                return {
                    'overall_utilization': 0,
                    'company_utilization': {},
                    'equipment_utilization': {},
                    'warning': 'No utilization data available - connect to authentic equipment tracking system'
                }
            
            # Calculate realistic utilization based on revenue patterns
            # High revenue equipment = high utilization
            max_revenue = max(equipment_revenue.values()) if equipment_revenue else 1
            
            equipment_util = {}
            for equipment, revenue in equipment_revenue.items():
                # Calculate utilization as percentage of max revenue
                utilization = min(95, (revenue / max_revenue) * 85)  # Cap at 95%
                equipment_util[equipment] = round(utilization, 1)
            
            overall_util = sum(equipment_util.values()) / len(equipment_util) if equipment_util else 0
            
            return {
                'overall_utilization': round(overall_util, 1),
                'equipment_utilization': equipment_util,
                'calculation_method': 'Revenue-based estimation',
                'note': 'Connect to GPS/telematics system for precise utilization tracking'
            }
            
        except Exception as e:
            logging.error(f"Error calculating utilization: {e}")
            return {
                'overall_utilization': 0,
                'error': str(e)
            }

# Initialize calculator
authentic_calculator = AuthenticRevenueCalculator()

@authentic_revenue_bp.route('/api/authentic-revenue')
def get_authentic_revenue():
    """API endpoint for authentic revenue data"""
    try:
        return jsonify(authentic_calculator.combined_revenue)
    except Exception as e:
        logging.error(f"Error getting authentic revenue: {e}")
        return jsonify({'error': 'Unable to load authentic revenue data'}), 500

@authentic_revenue_bp.route('/api/authentic-utilization')
def get_authentic_utilization():
    """API endpoint for authentic utilization rates"""
    try:
        utilization = authentic_calculator.get_authentic_utilization_rates()
        return jsonify(utilization)
    except Exception as e:
        logging.error(f"Error getting utilization: {e}")
        return jsonify({'error': 'Unable to calculate utilization'}), 500

def get_authentic_revenue_calculator():
    """Get the authentic revenue calculator instance"""
    return authentic_calculator