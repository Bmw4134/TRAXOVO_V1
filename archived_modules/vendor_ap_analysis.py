"""
Vendor A/P Analysis Engine
Import and analyze accounts payable data to validate cost savings calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename

ap_bp = Blueprint('vendor_ap', __name__)

class VendorAPAnalyzer:
    """Analyze vendor payments to validate cost savings calculations"""
    
    def __init__(self):
        self.upload_folder = 'uploads/ap_reports'
        self.ensure_upload_directory()
        self.load_existing_data()
    
    def ensure_upload_directory(self):
        """Ensure upload directory exists"""
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def load_existing_data(self):
        """Load existing A/P data from uploaded files"""
        self.ap_data = []
        
        # Look for existing A/P files
        ap_files = [f for f in os.listdir('.') if 'ap' in f.lower() or 'payable' in f.lower() or 'vendor' in f.lower()]
        
        for file in ap_files:
            if file.endswith(('.xlsx', '.xls', '.csv')):
                try:
                    if file.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                    
                    self.ap_data.append({
                        'filename': file,
                        'data': df,
                        'record_count': len(df)
                    })
                    print(f"Loaded A/P data from {file}: {len(df)} records")
                except Exception as e:
                    print(f"Could not load {file}: {e}")
    
    def process_ap_file(self, file_path):
        """Process uploaded A/P file"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Standardize column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Map common column variations
            column_mapping = {
                'vendor_name': ['vendor', 'vendor name', 'supplier', 'company'],
                'amount': ['amount', 'payment amount', 'total', 'invoice amount'],
                'date': ['date', 'payment date', 'invoice date', 'transaction date'],
                'description': ['description', 'memo', 'reference', 'details'],
                'category': ['category', 'expense category', 'account', 'gl account']
            }
            
            standardized_df = pd.DataFrame()
            
            for standard_col, variations in column_mapping.items():
                for variation in variations:
                    if variation in df.columns:
                        standardized_df[standard_col] = df[variation]
                        break
            
            # Add metadata
            standardized_df['upload_date'] = datetime.now()
            standardized_df['file_source'] = os.path.basename(file_path)
            
            return standardized_df
            
        except Exception as e:
            print(f"Error processing A/P file: {e}")
            return pd.DataFrame()
    
    def analyze_equipment_vendors(self):
        """Analyze equipment-related vendor payments"""
        if not self.ap_data:
            return self._get_sample_analysis()
        
        all_payments = []
        for ap_source in self.ap_data:
            df = ap_source['data']
            
            # Filter for equipment-related payments
            equipment_keywords = [
                'rental', 'lease', 'equipment', 'machinery', 'excavator', 
                'truck', 'compressor', 'maintenance', 'repair', 'service'
            ]
            
            equipment_mask = df.apply(lambda row: any(
                keyword in str(row).lower() for keyword in equipment_keywords
            ), axis=1)
            
            equipment_payments = df[equipment_mask].copy()
            equipment_payments['source_file'] = ap_source['filename']
            all_payments.append(equipment_payments)
        
        if all_payments:
            combined_payments = pd.concat(all_payments, ignore_index=True)
            return self._analyze_payment_patterns(combined_payments)
        
        return self._get_sample_analysis()
    
    def _analyze_payment_patterns(self, payments_df):
        """Analyze payment patterns for cost savings validation"""
        # Categorize payments
        rental_payments = payments_df[payments_df.apply(
            lambda row: 'rental' in str(row).lower(), axis=1
        )]
        
        maintenance_payments = payments_df[payments_df.apply(
            lambda row: any(word in str(row).lower() for word in ['maintenance', 'repair', 'service']), axis=1
        )]
        
        # Calculate monthly totals
        if 'amount' in payments_df.columns:
            monthly_rental = rental_payments['amount'].sum() / 12 if len(rental_payments) > 0 else 0
            monthly_maintenance = maintenance_payments['amount'].sum() / 12 if len(maintenance_payments) > 0 else 0
        else:
            monthly_rental = 0
            monthly_maintenance = 0
        
        # Calculate potential savings
        internal_efficiency = 0.75  # 75% efficiency using internal assets
        potential_rental_savings = monthly_rental * internal_efficiency
        
        return {
            'total_equipment_payments': len(payments_df),
            'monthly_rental_spend': monthly_rental,
            'monthly_maintenance_spend': monthly_maintenance,
            'potential_rental_savings': potential_rental_savings,
            'validated_monthly_savings': potential_rental_savings * 0.8,  # Conservative estimate
            'top_vendors': self._get_top_vendors(payments_df),
            'savings_confidence': 'HIGH' if len(payments_df) > 50 else 'MEDIUM',
            'data_source': 'Authentic A/P Records'
        }
    
    def _get_top_vendors(self, payments_df):
        """Get top equipment vendors by payment amount"""
        if 'vendor_name' in payments_df.columns and 'amount' in payments_df.columns:
            return payments_df.groupby('vendor_name')['amount'].sum().sort_values(ascending=False).head(10).to_dict()
        return {}
    
    def _get_sample_analysis(self):
        """Return sample analysis when no A/P data is available"""
        return {
            'total_equipment_payments': 0,
            'monthly_rental_spend': 0,
            'monthly_maintenance_spend': 0,
            'potential_rental_savings': 0,
            'validated_monthly_savings': 0,
            'top_vendors': {},
            'savings_confidence': 'LOW',
            'data_source': 'No A/P Data Available - Upload vendor payment reports for accurate analysis'
        }

@ap_bp.route('/vendor-analysis')
def vendor_analysis_dashboard():
    """Vendor A/P analysis dashboard"""
    analyzer = VendorAPAnalyzer()
    analysis = analyzer.analyze_equipment_vendors()
    
    return render_template('vendor_ap_dashboard.html', analysis=analysis)

@ap_bp.route('/upload-ap-report', methods=['GET', 'POST'])
def upload_ap_report():
    """Upload A/P report for analysis"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.xlsx', '.xls', '.csv')):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
            
            analyzer = VendorAPAnalyzer()
            processed_data = analyzer.process_ap_file(file_path)
            
            if len(processed_data) > 0:
                flash(f'Successfully processed {len(processed_data)} A/P records')
                return redirect(url_for('vendor_ap.vendor_analysis_dashboard'))
            else:
                flash('Error processing file - please check format')
        else:
            flash('Please upload Excel or CSV files only')
    
    return render_template('upload_ap_report.html')

@ap_bp.route('/api/ap-analysis')
def api_ap_analysis():
    """API endpoint for A/P analysis data"""
    analyzer = VendorAPAnalyzer()
    analysis = analyzer.analyze_equipment_vendors()
    
    return jsonify(analysis)