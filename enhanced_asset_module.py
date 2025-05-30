"""
Enhanced Asset Management Module
Optimized asset tracking with data integrity verification
"""
from flask import Blueprint, render_template, request, jsonify, flash
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import pandas as pd
import json
import os
from typing import Dict, List, Optional

Base = declarative_base()

class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    category = Column(String(100))
    make_model = Column(String(150))
    year = Column(Integer)
    serial_number = Column(String(100))
    
    # Status and location
    status = Column(String(50), default='Active')
    current_location = Column(String(200))
    assigned_job_site = Column(String(200))
    
    # Financial data
    purchase_price = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    hourly_rate = Column(Float, default=0.0)
    
    # Operational data
    total_hours = Column(Float, default=0.0)
    last_service_date = Column(DateTime)
    next_service_due = Column(DateTime)
    service_interval_hours = Column(Float, default=250.0)
    
    # GPS and tracking
    last_gps_lat = Column(Float)
    last_gps_lng = Column(Float)
    last_gps_update = Column(DateTime)
    
    # Metadata
    custom_fields = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AssetUsageLog(Base):
    __tablename__ = 'asset_usage_logs'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(String(50), nullable=False)
    usage_date = Column(DateTime, nullable=False)
    operator_id = Column(String(50))
    hours_used = Column(Float, default=0.0)
    fuel_used = Column(Float, default=0.0)
    job_site = Column(String(200))
    project_code = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetMaintenanceRecord(Base):
    __tablename__ = 'asset_maintenance'
    
    id = Column(Integer, primary_key=True)
    asset_id = Column(String(50), nullable=False)
    maintenance_type = Column(String(100))
    description = Column(Text)
    service_date = Column(DateTime, nullable=False)
    next_service_date = Column(DateTime)
    cost = Column(Float, default=0.0)
    vendor = Column(String(150))
    work_order_number = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class AssetManager:
    """Enhanced asset management engine"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def import_assets_from_excel(self, file_path: str) -> Dict:
        """Import assets from Excel with validation and deduplication"""
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
            
            imported_count = 0
            updated_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    asset_id = str(row.get('equipment_id', row.get('asset_id', ''))).strip()
                    if not asset_id:
                        errors.append(f"Row {index + 2}: Missing asset ID")
                        continue
                    
                    # Check if asset exists
                    existing_asset = self.session.query(Asset).filter(Asset.asset_id == asset_id).first()
                    
                    if existing_asset:
                        # Update existing asset
                        self._update_asset_from_row(existing_asset, row)
                        updated_count += 1
                    else:
                        # Create new asset
                        new_asset = self._create_asset_from_row(row, asset_id)
                        self.session.add(new_asset)
                        imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            self.session.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'updated_count': updated_count,
                'error_count': len(errors),
                'errors': errors
            }
            
        except Exception as e:
            self.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _create_asset_from_row(self, row, asset_id: str) -> Asset:
        """Create asset object from DataFrame row"""
        return Asset(
            asset_id=asset_id,
            description=str(row.get('description', '')).strip(),
            category=str(row.get('category', '')).strip(),
            make_model=str(row.get('make_model', row.get('make', ''))).strip(),
            year=self._safe_int(row.get('year')),
            serial_number=str(row.get('serial_number', '')).strip(),
            status=str(row.get('status', 'Active')).strip(),
            current_location=str(row.get('location', row.get('current_location', ''))).strip(),
            purchase_price=self._safe_float(row.get('purchase_price', row.get('cost', 0))),
            hourly_rate=self._safe_float(row.get('hourly_rate', row.get('rate', 0))),
            service_interval_hours=self._safe_float(row.get('service_interval', 250))
        )
    
    def _update_asset_from_row(self, asset: Asset, row):
        """Update existing asset with new data"""
        asset.description = str(row.get('description', asset.description)).strip()
        asset.category = str(row.get('category', asset.category)).strip()
        asset.make_model = str(row.get('make_model', row.get('make', asset.make_model))).strip()
        asset.year = self._safe_int(row.get('year')) or asset.year
        asset.status = str(row.get('status', asset.status)).strip()
        asset.current_location = str(row.get('location', row.get('current_location', asset.current_location))).strip()
        asset.updated_at = datetime.utcnow()
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer"""
        try:
            if pd.notna(value) and value != '':
                return int(float(value))
        except:
            pass
        return None
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if pd.notna(value) and value != '':
                return float(value)
        except:
            pass
        return 0.0
    
    def calculate_utilization_metrics(self, asset_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate comprehensive utilization metrics for an asset"""
        asset = self.session.query(Asset).filter(Asset.asset_id == asset_id).first()
        if not asset:
            return {'error': 'Asset not found'}
        
        # Get usage logs for date range
        usage_logs = self.session.query(AssetUsageLog).filter(
            AssetUsageLog.asset_id == asset_id,
            AssetUsageLog.usage_date >= start_date,
            AssetUsageLog.usage_date <= end_date
        ).all()
        
        total_hours_used = sum(log.hours_used for log in usage_logs)
        total_fuel_used = sum(log.fuel_used for log in usage_logs if log.fuel_used)
        
        # Calculate available hours (business days * 8 hours)
        business_days = pd.bdate_range(start=start_date, end=end_date)
        available_hours = len(business_days) * 8
        
        utilization_rate = (total_hours_used / available_hours * 100) if available_hours > 0 else 0
        
        # Revenue calculation
        revenue = total_hours_used * asset.hourly_rate
        
        # Get maintenance costs for period
        maintenance_costs = self.session.query(AssetMaintenanceRecord).filter(
            AssetMaintenanceRecord.asset_id == asset_id,
            AssetMaintenanceRecord.service_date >= start_date,
            AssetMaintenanceRecord.service_date <= end_date
        ).all()
        
        total_maintenance_cost = sum(record.cost for record in maintenance_costs)
        
        return {
            'asset_id': asset_id,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_hours_used': round(total_hours_used, 2),
            'available_hours': available_hours,
            'utilization_rate': round(utilization_rate, 2),
            'total_fuel_used': round(total_fuel_used, 2),
            'revenue': round(revenue, 2),
            'maintenance_cost': round(total_maintenance_cost, 2),
            'profit': round(revenue - total_maintenance_cost, 2),
            'usage_days': len(set(log.usage_date.date() for log in usage_logs)),
            'operators': list(set(log.operator_id for log in usage_logs if log.operator_id))
        }
    
    def get_maintenance_schedule(self, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming maintenance schedule"""
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        assets = self.session.query(Asset).filter(
            Asset.status == 'Active'
        ).all()
        
        maintenance_schedule = []
        
        for asset in assets:
            # Calculate next service based on hours
            if asset.last_service_date and asset.service_interval_hours:
                hours_since_service = asset.total_hours - (asset.total_hours - asset.service_interval_hours)
                if hours_since_service >= asset.service_interval_hours * 0.9:  # 90% threshold
                    maintenance_schedule.append({
                        'asset_id': asset.asset_id,
                        'description': asset.description,
                        'service_type': 'Scheduled Maintenance',
                        'hours_until_due': asset.service_interval_hours - hours_since_service,
                        'urgency': 'high' if hours_since_service >= asset.service_interval_hours else 'medium',
                        'estimated_date': asset.next_service_due
                    })
        
        return sorted(maintenance_schedule, key=lambda x: x['hours_until_due'])
    
    def validate_asset_data_integrity(self) -> Dict:
        """Validate asset data integrity and consistency"""
        issues = []
        
        # Check for duplicate asset IDs
        duplicates = self.session.execute("""
            SELECT asset_id, COUNT(*) as count 
            FROM assets 
            GROUP BY asset_id 
            HAVING COUNT(*) > 1
        """).fetchall()
        
        for dup in duplicates:
            issues.append(f"Duplicate asset ID: {dup[0]} ({dup[1]} records)")
        
        # Check for missing critical data
        missing_data = self.session.query(Asset).filter(
            (Asset.description == '') | 
            (Asset.category == '') |
            (Asset.hourly_rate <= 0)
        ).all()
        
        for asset in missing_data:
            missing_fields = []
            if not asset.description:
                missing_fields.append('description')
            if not asset.category:
                missing_fields.append('category')
            if asset.hourly_rate <= 0:
                missing_fields.append('hourly_rate')
            
            issues.append(f"Asset {asset.asset_id}: Missing {', '.join(missing_fields)}")
        
        # Check for inactive assets with recent usage
        recent_date = datetime.now() - timedelta(days=7)
        inactive_with_usage = self.session.query(Asset).join(AssetUsageLog).filter(
            Asset.status != 'Active',
            AssetUsageLog.usage_date >= recent_date
        ).all()
        
        for asset in inactive_with_usage:
            issues.append(f"Inactive asset {asset.asset_id} has recent usage")
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'validation_date': datetime.now().isoformat()
        }

# Flask Blueprint
asset_bp = Blueprint('asset', __name__, url_prefix='/asset')

@asset_bp.route('/')
def asset_dashboard():
    """Asset management dashboard"""
    return render_template('asset/dashboard.html')

@asset_bp.route('/import', methods=['POST'])
def import_assets():
    """Import assets from Excel file"""
    file = request.files.get('asset_file')
    if file and file.filename:
        temp_path = f"temp/{file.filename}"
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        from app import db
        manager = AssetManager(db.session)
        result = manager.import_assets_from_excel(temp_path)
        
        os.remove(temp_path)
        
        return jsonify(result)
    
    return jsonify({'success': False, 'error': 'No file provided'})

@asset_bp.route('/utilization/<asset_id>')
def asset_utilization(asset_id):
    """Get utilization metrics for specific asset"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        from app import db
        manager = AssetManager(db.session)
        metrics = manager.calculate_utilization_metrics(asset_id, start_date, end_date)
        
        return jsonify(metrics)
    
    return jsonify({'error': 'Invalid date range'})

@asset_bp.route('/maintenance-schedule')
def maintenance_schedule():
    """Get upcoming maintenance schedule"""
    days_ahead = request.args.get('days', 30, type=int)
    
    from app import db
    manager = AssetManager(db.session)
    schedule = manager.get_maintenance_schedule(days_ahead)
    
    return jsonify({'schedule': schedule})

@asset_bp.route('/validate-integrity')
def validate_integrity():
    """Validate asset data integrity"""
    from app import db
    manager = AssetManager(db.session)
    validation_result = manager.validate_asset_data_integrity()
    
    return jsonify(validation_result)