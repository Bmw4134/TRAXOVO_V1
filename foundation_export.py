"""
Foundation Accounting Export Module
Prepares TRAXOVO billing data for Foundation accounting software import
"""
import pandas as pd
import os
import json
from datetime import datetime
from authentic_data_service import authentic_data

class FoundationExporter:
    """Export TRAXOVO data in Foundation-compatible format"""
    
    def __init__(self):
        self.export_formats = ['CSV', 'Excel', 'QIF', 'IIF']
        
    def prepare_eq_billing_export(self, month=None, year=None):
        """Prepare equipment billing data for Foundation import"""
        if not month:
            month = datetime.now().month
        if not year:
            year = datetime.now().year
            
        # Get authentic data
        asset_data = authentic_data.get_asset_data()
        revenue_data = authentic_data.get_revenue_data()
        project_data = authentic_data.get_project_data()
        
        # Structure for Foundation accounting
        foundation_records = []
        
        # Equipment revenue entries
        for category, count in asset_data['categories'].items():
            if count > 0:
                revenue_per_unit = revenue_data['total_revenue'] / asset_data['total_assets']
                category_revenue = revenue_per_unit * count
                
                foundation_records.append({
                    'Date': f"{month:02d}/{year}",
                    'Account': '4000-Equipment Revenue',
                    'Description': f'{category} - Monthly Billing',
                    'Amount': round(category_revenue, 2),
                    'Class': self._get_class_code(category),
                    'Customer': 'Various Projects',
                    'Item': self._get_item_code(category),
                    'Memo': f'TRAXOVO Auto-Export {month}/{year}'
                })
        
        # Project-specific allocations
        total_project_revenue = sum(p['revenue'] for p in project_data)
        for project in project_data:
            foundation_records.append({
                'Date': f"{month:02d}/{year}",
                'Account': '1200-Accounts Receivable',
                'Description': f"Equipment Revenue - {project['name']}",
                'Amount': round(project['revenue'], 2),
                'Class': f"JOB-{project['job_number']}",
                'Customer': project['name'],
                'Item': 'EQUIPMENT',
                'Memo': f"Job {project['job_number']} - {project['assets_on_site']} assets"
            })
            
        return foundation_records
    
    def _get_class_code(self, category):
        """Map asset categories to Foundation class codes"""
        class_mapping = {
            'Standard Equipment': 'EQHVY',
            'Mechanic Trucks': 'EQSVC', 
            'Semi Trucks': 'EQTPT',
            'Heavy Haulers': 'EQHHL',
            'Pickup Trucks': 'EQPUP'
        }
        return class_mapping.get(category, 'EQGEN')
    
    def _get_item_code(self, category):
        """Map asset categories to Foundation item codes"""
        item_mapping = {
            'Standard Equipment': 'EQ-HEAVY',
            'Mechanic Trucks': 'EQ-SERVICE',
            'Semi Trucks': 'EQ-TRANSPORT', 
            'Heavy Haulers': 'EQ-HAULER',
            'Pickup Trucks': 'EQ-PICKUP'
        }
        return item_mapping.get(category, 'EQ-GENERAL')
    
    def export_to_csv(self, records, filename=None):
        """Export records to CSV for Foundation import"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'foundation_export_{timestamp}.csv'
            
        df = pd.DataFrame(records)
        df.to_csv(filename, index=False)
        return filename
    
    def export_to_excel(self, records, filename=None):
        """Export records to Excel for Foundation import"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'foundation_export_{timestamp}.xlsx'
            
        df = pd.DataFrame(records)
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_sheet(writer, sheet_name='Foundation Import', index=False)
            
            # Add summary sheet
            summary_data = self._create_export_summary(records)
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_sheet(writer, sheet_name='Export Summary', index=False)
            
        return filename
    
    def export_to_qif(self, records, filename=None):
        """Export to QIF format for Foundation import"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'foundation_export_{timestamp}.qif'
            
        qif_content = "!Type:Bank\n"
        
        for record in records:
            qif_content += f"D{record['Date']}\n"
            qif_content += f"T{record['Amount']}\n"
            qif_content += f"P{record['Description']}\n"
            qif_content += f"L{record['Account']}\n"
            qif_content += f"M{record['Memo']}\n"
            qif_content += "^\n"
            
        with open(filename, 'w') as f:
            f.write(qif_content)
            
        return filename
    
    def _create_export_summary(self, records):
        """Create summary data for export validation"""
        total_amount = sum(r['Amount'] for r in records)
        account_totals = {}
        
        for record in records:
            account = record['Account']
            if account not in account_totals:
                account_totals[account] = 0
            account_totals[account] += record['Amount']
            
        summary = [
            {'Metric': 'Total Records', 'Value': len(records)},
            {'Metric': 'Total Amount', 'Value': total_amount},
            {'Metric': 'Export Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
            {'Metric': 'Source', 'Value': 'TRAXOVO Equipment Billing System'}
        ]
        
        # Add account breakdowns
        for account, amount in account_totals.items():
            summary.append({
                'Metric': f'Account: {account}',
                'Value': amount
            })
            
        return summary
    
    def validate_export(self, records):
        """Validate export data before Foundation import"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        required_fields = ['Date', 'Account', 'Description', 'Amount']
        
        for i, record in enumerate(records):
            # Check required fields
            for field in required_fields:
                if field not in record or not record[field]:
                    validation_results['errors'].append(
                        f"Record {i+1}: Missing required field '{field}'"
                    )
                    validation_results['valid'] = False
            
            # Validate amount
            try:
                float(record.get('Amount', 0))
            except (ValueError, TypeError):
                validation_results['errors'].append(
                    f"Record {i+1}: Invalid amount value"
                )
                validation_results['valid'] = False
                
        # Check total balances
        total_revenue = sum(r['Amount'] for r in records if '4000' in r.get('Account', ''))
        total_receivable = sum(r['Amount'] for r in records if '1200' in r.get('Account', ''))
        
        if abs(total_revenue - total_receivable) > 0.01:
            validation_results['warnings'].append(
                f"Revenue/Receivable imbalance: ${abs(total_revenue - total_receivable):.2f}"
            )
            
        return validation_results

# Global instance
foundation_exporter = FoundationExporter()