"""
Comprehensive Billing Data Consolidation System
Processes all authentic Foundation billing files with duplicate detection
"""

import pandas as pd
import os
from datetime import datetime
from flask import Blueprint, jsonify, render_template
import hashlib

billing_consolidation_bp = Blueprint('billing_consolidation', __name__)

def get_all_billing_files():
    """Identify all authentic billing files from your uploads"""
    billing_files = []
    
    # Your authentic Foundation billing files
    authentic_files = [
        'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
        'attached_assets/RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm',
        'attached_assets/CURRENT EQ SERVICE-EXPENSE CODE LIST 052925.xlsx',
        'attached_assets/EQ CATEGORIES CONDENSED LIST 05.29.2025.xlsx',
        'attached_assets/EQ LIST ALL DETAILS SELECTED 052925.xlsx',
        'attached_assets/EQUIPMENT USAGE DETAIL 010125-053125.xlsx',
        'attached_assets/Equipment Detail History Report_01.01.2020-05.31.2025.xlsx',
        'attached_assets/FleetUtilization (2).xlsx',
        'attached_assets/FleetUtilization (3).xlsx'
    ]
    
    for file_path in authentic_files:
        if os.path.exists(file_path):
            billing_files.append({
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M'),
                'type': 'billing' if 'BILLING' in file_path else 'equipment_data'
            })
    
    return billing_files

def create_record_hash(equipment_id, amount, date_info):
    """Create unique hash for duplicate detection"""
    hash_string = f"{equipment_id}_{amount}_{date_info}"
    return hashlib.md5(hash_string.encode()).hexdigest()

def process_consolidated_billing():
    """Process all billing files and consolidate with duplicate detection"""
    all_files = get_all_billing_files()
    consolidated_data = []
    seen_hashes = set()
    duplicate_count = 0
    processing_stats = {}
    
    for file_info in all_files:
        file_path = file_info['path']
        file_stats = {
            'records_processed': 0,
            'valid_records': 0,
            'duplicates_found': 0,
            'total_amount': 0
        }
        
        try:
            # Read Excel file with multiple potential sheet structures
            if file_path.endswith('.xlsm') or file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
                
                # Process each row for billing data
                for idx, row in df.iterrows():
                    file_stats['records_processed'] += 1
                    
                    if pd.notna(row.iloc[0]):
                        equipment_id = str(row.iloc[0]).strip()
                        
                        # Extract financial data from various column structures
                        for col_idx in range(1, min(len(row), 15)):
                            try:
                                if pd.notna(row.iloc[col_idx]):
                                    cell_value = str(row.iloc[col_idx])
                                    
                                    # Clean and validate monetary values
                                    cleaned_value = cell_value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                                    
                                    if cleaned_value.replace('.', '').replace('-', '').isdigit() and len(cleaned_value) > 1:
                                        amount = float(cleaned_value)
                                        
                                        if abs(amount) > 10:  # Filter out insignificant amounts
                                            # Create unique identifier for duplicate detection
                                            date_context = file_info['name']  # Use filename as date context
                                            record_hash = create_record_hash(equipment_id, amount, date_context)
                                            
                                            if record_hash not in seen_hashes:
                                                seen_hashes.add(record_hash)
                                                file_stats['valid_records'] += 1
                                                file_stats['total_amount'] += abs(amount)
                                                
                                                consolidated_data.append({
                                                    'equipment_id': equipment_id,
                                                    'amount': amount,
                                                    'abs_amount': abs(amount),
                                                    'source_file': file_info['name'],
                                                    'file_type': file_info['type'],
                                                    'record_hash': record_hash,
                                                    'column_index': col_idx,
                                                    'row_index': idx,
                                                    'date_processed': datetime.now().strftime('%Y-%m-%d %H:%M')
                                                })
                                                break
                                            else:
                                                duplicate_count += 1
                                                file_stats['duplicates_found'] += 1
                            except (ValueError, TypeError):
                                continue
                                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        processing_stats[file_info['name']] = file_stats
    
    return consolidated_data, processing_stats, duplicate_count

def analyze_consolidated_data(consolidated_data):
    """Analyze the consolidated billing data for insights"""
    if not consolidated_data:
        return {}
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(consolidated_data)
    
    # Equipment-level analysis
    equipment_summary = df.groupby('equipment_id').agg({
        'abs_amount': ['sum', 'count', 'mean'],
        'source_file': lambda x: list(set(x))
    }).round(2)
    
    # File-level analysis
    file_summary = df.groupby('source_file').agg({
        'abs_amount': ['sum', 'count'],
        'equipment_id': lambda x: len(set(x))
    }).round(2)
    
    # Top performers
    top_equipment = df.groupby('equipment_id')['abs_amount'].sum().sort_values(ascending=False).head(10)
    
    # Monthly analysis (based on file names)
    monthly_data = {}
    for _, row in df.iterrows():
        if 'APRIL' in row['source_file'].upper():
            month = 'April 2025'
        elif 'MARCH' in row['source_file'].upper():
            month = 'March 2025'
        else:
            month = 'Other'
            
        if month not in monthly_data:
            monthly_data[month] = 0
        monthly_data[month] += row['abs_amount']
    
    return {
        'total_records': len(df),
        'unique_equipment': df['equipment_id'].nunique(),
        'total_amount': df['abs_amount'].sum(),
        'average_amount': df['abs_amount'].mean(),
        'equipment_summary': equipment_summary,
        'file_summary': file_summary,
        'top_equipment': top_equipment,
        'monthly_breakdown': monthly_data,
        'file_coverage': df.groupby('source_file')['equipment_id'].nunique().to_dict()
    }

@billing_consolidation_bp.route('/billing-consolidation')
def billing_consolidation_dashboard():
    """Comprehensive billing consolidation dashboard"""
    all_files = get_all_billing_files()
    consolidated_data, processing_stats, duplicate_count = process_consolidated_billing()
    analysis = analyze_consolidated_data(consolidated_data)
    
    # Calculate data quality metrics
    total_records_processed = sum(stats['records_processed'] for stats in processing_stats.values())
    total_valid_records = sum(stats['valid_records'] for stats in processing_stats.values())
    data_quality_score = (total_valid_records / total_records_processed * 100) if total_records_processed > 0 else 0
    
    context = {
        'page_title': 'Billing Data Consolidation',
        'files_processed': len(all_files),
        'total_records': analysis.get('total_records', 0),
        'unique_equipment': analysis.get('unique_equipment', 0),
        'duplicate_count': duplicate_count,
        'total_amount': analysis.get('total_amount', 0),
        'data_quality_score': round(data_quality_score, 1),
        'processing_stats': processing_stats,
        'analysis': analysis,
        'consolidated_data': consolidated_data[:50],  # Show first 50 records
        'monthly_breakdown': analysis.get('monthly_breakdown', {}),
        'top_equipment': analysis.get('top_equipment', {}).to_dict() if hasattr(analysis.get('top_equipment', {}), 'to_dict') else {},
        'file_list': all_files
    }
    
    return render_template('billing_consolidation_dashboard.html', **context)

@billing_consolidation_bp.route('/api/billing-export')
def export_consolidated_billing():
    """Export consolidated billing data"""
    consolidated_data, _, _ = process_consolidated_billing()
    
    return jsonify({
        'consolidated_data': consolidated_data,
        'export_timestamp': datetime.now().isoformat(),
        'total_records': len(consolidated_data),
        'data_integrity': 'Authentic Foundation billing data - duplicates removed'
    })

@billing_consolidation_bp.route('/api/equipment-detail/<equipment_id>')
def equipment_detail(equipment_id):
    """Get detailed billing history for specific equipment"""
    consolidated_data, _, _ = process_consolidated_billing()
    
    equipment_records = [record for record in consolidated_data if record['equipment_id'] == equipment_id]
    
    if equipment_records:
        total_amount = sum(record['abs_amount'] for record in equipment_records)
        avg_amount = total_amount / len(equipment_records)
        
        return jsonify({
            'equipment_id': equipment_id,
            'total_records': len(equipment_records),
            'total_amount': total_amount,
            'average_amount': avg_amount,
            'records': equipment_records,
            'files_found_in': list(set(record['source_file'] for record in equipment_records))
        })
    
    return jsonify({'error': 'Equipment not found'}), 404