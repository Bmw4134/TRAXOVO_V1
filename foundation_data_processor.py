"""
Foundation Accounting Data Processor
Processes authentic billing data from Foundation software for both Ragle and Select companies
"""

import os
import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

class FoundationDataProcessor:
    """Process Foundation software billing reports for authentic revenue and asset data"""
    
    def __init__(self):
        self.data_dir = "attached_assets"
        self.companies = ["RAGLE", "SELECT"]
        self.months = ["JAN", "FEB", "MARCH", "APRIL"]
        
    def extract_billing_data_from_pdf_text(self, pdf_content: str) -> Dict:
        """Extract billing data from PDF text content"""
        
        # Initialize data structure
        billing_data = {
            'total_revenue': 0.0,
            'equipment_count': 0,
            'job_totals': {},
            'equipment_details': []
        }
        
        lines = pdf_content.split('\n')
        current_job = None
        equipment_ids = set()  # Track unique equipment
        
        for line in lines:
            line = line.strip()
            
            # Extract job numbers and totals
            job_match = re.search(r'Job No:\s*([^\s]+)', line)
            if job_match:
                current_job = job_match.group(1)
                continue
                
            # Extract job totals - look for various total patterns
            total_patterns = [
                r'Total for Job [^:]+:\s*([0-9,]+\.\d+)',
                r'Total for Job [^:]+:\s*([0-9,]+\.\d+)',
                r'Job [^:]*Total[^:]*:\s*([0-9,]+\.\d+)'
            ]
            
            for pattern in total_patterns:
                total_match = re.search(pattern, line)
                if total_match and current_job:
                    amount = float(total_match.group(1).replace(',', ''))
                    if current_job not in billing_data['job_totals']:
                        billing_data['job_totals'][current_job] = 0
                    billing_data['job_totals'][current_job] += amount
                    billing_data['total_revenue'] += amount
                    break
            
            # Extract equipment details and amounts directly from line items
            # Look for equipment patterns with amounts
            equipment_patterns = [
                r'([A-Z0-9-]+)\s+-\s+([^0-9]+?)\s+\d{2}/\d{2}/\d{2}.*?([0-9,]+\.\d+)\s+([0-9,]+\.\d+)',
                r'([A-Z0-9-]+)\s+-\s+([^0-9]+?).*?Monthly\s+([0-9,]+\.\d+)\s+([0-9,]+\.\d+)',
                r'([A-Z0-9-]+)\s+-\s+.*?([0-9,]+\.\d+)\s+([0-9,]+\.\d+)\s+0\.00$'
            ]
            
            for pattern in equipment_patterns:
                equipment_match = re.search(pattern, line)
                if equipment_match:
                    groups = equipment_match.groups()
                    if len(groups) >= 4:
                        equipment_id = groups[0].strip()
                        # Get the amount (usually the second-to-last number)
                        amount = float(groups[-2].replace(',', ''))
                        
                        if equipment_id not in equipment_ids and amount > 0:
                            equipment_ids.add(equipment_id)
                            equipment_name = groups[1].strip() if len(groups) > 1 else "Equipment"
                            
                            billing_data['equipment_details'].append({
                                'equipment_id': equipment_id,
                                'equipment_name': equipment_name,
                                'amount': amount,
                                'job': current_job
                            })
                    break
        
        billing_data['equipment_count'] = len(equipment_ids)
        return billing_data
    
    def process_all_foundation_reports(self) -> Dict:
        """Process all available Foundation reports"""
        
        total_data = {
            'ragle': {'total_revenue': 0, 'equipment_count': 0, 'monthly_data': {}},
            'select': {'total_revenue': 0, 'equipment_count': 0, 'monthly_data': {}},
            'combined': {'total_revenue': 0, 'equipment_count': 0}
        }
        
        # Process PDF files
        pdf_files = [
            "SELECT EQ USAGE JOURNAL LIST - JAN 2025 (PRE-POST JOB-EQ)_02.10.2025.pdf",
            "SEL EQ USAGE JOURNAL LIST PRE-POST (JOB-EQ) - FEB 2025.pdf", 
            "SELECT EQ USAGE JOURNAL LIST (PRE-POST) JOB-EQ - MARCH 2025.pdf",
            "RAG EQ USAGE JOURNAL POST (JOB-EQ) - FEBRUARY 2025.pdf",
            "RAGLE EQ USAGE JOURNAL POST (JOB-EQ) MARCH 2025.pdf",
            "RAG APRIL 2025 - EQ USAGE JOURNAL LIST (PRE-POST).pdf"
        ]
        
        for pdf_file in pdf_files:
            file_path = os.path.join(self.data_dir, pdf_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    billing_data = self.extract_billing_data_from_pdf_text(content)
                    
                    # Determine company and month
                    company = 'ragle' if 'RAG' in pdf_file.upper() else 'select'
                    
                    if 'JAN' in pdf_file.upper():
                        month = 'january'
                    elif 'FEB' in pdf_file.upper():
                        month = 'february'  
                    elif 'MARCH' in pdf_file.upper():
                        month = 'march'
                    elif 'APRIL' in pdf_file.upper():
                        month = 'april'
                    else:
                        month = 'unknown'
                    
                    # Store monthly data
                    total_data[company]['monthly_data'][month] = billing_data
                    total_data[company]['total_revenue'] += billing_data['total_revenue']
                    
                    # Use unique equipment count (avoid double counting)
                    equipment_ids = set()
                    for detail in billing_data['equipment_details']:
                        equipment_ids.add(detail['equipment_id'])
                    
                    total_data[company]['equipment_count'] = len(equipment_ids)
                    
                except Exception as e:
                    print(f"Error processing {pdf_file}: {e}")
                    continue
        
        # Calculate combined totals
        total_data['combined']['total_revenue'] = (
            total_data['ragle']['total_revenue'] + 
            total_data['select']['total_revenue']
        )
        
        # Get unique equipment count across both companies
        all_equipment_ids = set()
        for company in ['ragle', 'select']:
            for month_data in total_data[company]['monthly_data'].values():
                for detail in month_data['equipment_details']:
                    all_equipment_ids.add(detail['equipment_id'])
        
        total_data['combined']['equipment_count'] = len(all_equipment_ids)
        
        return total_data
    
    def get_revenue_summary(self) -> Dict:
        """Get revenue summary from Foundation reports"""
        data = self.process_all_foundation_reports()
        
        return {
            'total_revenue': data['combined']['total_revenue'],
            'ragle_revenue': data['ragle']['total_revenue'], 
            'select_revenue': data['select']['total_revenue'],
            'billable_assets': data['combined']['equipment_count'],
            'data_source': 'Foundation Software - Authentic Billing Reports',
            'reporting_period': 'January - April 2025'
        }

def get_foundation_processor():
    """Get the Foundation data processor instance"""
    return FoundationDataProcessor()