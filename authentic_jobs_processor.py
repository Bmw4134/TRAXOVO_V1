"""
RAGLE INC Authentic Jobs Data Processor
Processes real job accounting data for integration into TRAXOVO platform
"""

import csv
import json
from datetime import datetime

class AuthenticJobsProcessor:
    def __init__(self):
        self.jobs_data = []
        self.processed_data = {}
        
    def load_authentic_jobs_data(self):
        """Load authentic job data from CSV file"""
        try:
            with open('attached_assets/List of New Jobs for Accounting(Sheet1)_1749591252566.csv', 'r', encoding='ISO-8859-1') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Project Name') and row.get('Project Name').strip():
                        # Clean and structure the data
                        job_data = {
                            'company': row.get('Company', '').strip(),
                            'owner': row.get('Owner', '').strip(),
                            'owner_job_number': row.get('Owner Job #', '').strip(),
                            'area': row.get('Area', '').strip(),
                            'project_name': row.get('Project Name', '').strip(),
                            'low_bid_date': row.get('Low Bid Date', '').strip(),
                            'contract_amount': self._parse_currency(row.get(' Contract Amount ', '')),
                            'total_cost': self._parse_currency(row.get(' Total Cost ', '')),
                            'pm_pe_labor_cost': self._parse_currency(row.get(' PM/PE Labor Cost ', '')),
                            'survey_labor_cost': self._parse_currency(row.get(' Survey Labor Cost ', '')),
                            'bond_cost': self._parse_currency(row.get(' Bond Cost ', '')),
                            'locations': row.get('Approx. Locations', '').strip(),
                            'estimator': row.get('Estimator', '').strip()
                        }
                        self.jobs_data.append(job_data)
            
            print(f"✓ Loaded {len(self.jobs_data)} authentic RAGLE INC jobs")
            return True
            
        except Exception as e:
            print(f"Error loading authentic jobs data: {e}")
            return False
    
    def _parse_currency(self, value):
        """Parse currency string to float"""
        if not value or value.strip() in ['', '-', '$-', ' $-   ']:
            return 0.0
        
        # Remove currency symbols and whitespace
        cleaned = value.replace('$', '').replace(',', '').strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def get_ragle_projects(self):
        """Get projects specifically for RAGLE company"""
        ragle_projects = [job for job in self.jobs_data if job['company'].lower() == 'ragle']
        return ragle_projects
    
    def get_select_projects(self):
        """Get projects for SELECT company"""
        select_projects = [job for job in self.jobs_data if job['company'].lower() == 'select']
        return select_projects
    
    def get_projects_by_area(self, area='DFW'):
        """Get projects by geographical area"""
        return [job for job in self.jobs_data if job['area'].upper() == area.upper()]
    
    def get_high_value_projects(self, min_value=10000000):
        """Get projects above certain contract value"""
        return [job for job in self.jobs_data if job['contract_amount'] >= min_value]
    
    def get_project_summary(self):
        """Generate summary statistics"""
        if not self.jobs_data:
            return {}
        
        total_contract_value = sum(job['contract_amount'] for job in self.jobs_data)
        total_cost = sum(job['total_cost'] for job in self.jobs_data)
        
        ragle_projects = self.get_ragle_projects()
        select_projects = self.get_select_projects()
        
        summary = {
            'total_projects': len(self.jobs_data),
            'total_contract_value': total_contract_value,
            'total_cost': total_cost,
            'profit_margin': ((total_contract_value - total_cost) / total_contract_value * 100) if total_contract_value > 0 else 0,
            'ragle_projects': len(ragle_projects),
            'select_projects': len(select_projects),
            'dfw_projects': len(self.get_projects_by_area('DFW')),
            'hou_projects': len(self.get_projects_by_area('HOU')),
            'high_value_projects': len(self.get_high_value_projects()),
            'estimators': list(set(job['estimator'] for job in self.jobs_data if job['estimator']))
        }
        
        return summary
    
    def export_for_platform_integration(self):
        """Export data in format suitable for platform integration"""
        return {
            'authentic_jobs': self.jobs_data,
            'summary': self.get_project_summary(),
            'ragle_projects': self.get_ragle_projects(),
            'select_projects': self.get_select_projects(),
            'dfw_operations': self.get_projects_by_area('DFW'),
            'houston_operations': self.get_projects_by_area('HOU')
        }

def process_authentic_jobs_data():
    """Main function to process authentic jobs data"""
    processor = AuthenticJobsProcessor()
    
    if processor.load_authentic_jobs_data():
        summary = processor.get_project_summary()
        print(f"✓ Processed {summary['total_projects']} authentic projects")
        print(f"✓ Total contract value: ${summary['total_contract_value']:,.2f}")
        print(f"✓ RAGLE projects: {summary['ragle_projects']}")
        print(f"✓ SELECT projects: {summary['select_projects']}")
        
        return processor.export_for_platform_integration()
    
    return None

if __name__ == "__main__":
    data = process_authentic_jobs_data()
    if data:
        # Save processed data
        with open('authentic_jobs_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("✓ Authentic jobs data exported to authentic_jobs_data.json")