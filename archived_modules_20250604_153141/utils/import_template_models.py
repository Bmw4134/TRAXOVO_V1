"""
Models for import templates
"""

from datetime import datetime
from main import db


class ModelTemplate:
    """Base class for model templates"""
    columns = []
    required_columns = []
    
    @classmethod
    def validate_columns(cls, df):
        """Validate that the required columns are present in the dataframe"""
        missing = []
        for col in cls.required_columns:
            if col not in df.columns:
                missing.append(col)
        return missing
    
    @classmethod
    def map_to_model(cls, row_data):
        """Map row data to model fields"""
        raise NotImplementedError("Subclasses must implement this method")


class AssetDriverImportTemplate(ModelTemplate):
    """Template for asset-driver import"""
    columns = [
        'asset_identifier', 
        'driver_name',
        'driver_id',
        'start_date',
        'end_date',
        'is_current',
        'notes'
    ]
    required_columns = ['asset_identifier', 'driver_name']
    
    @classmethod
    def map_to_model(cls, row_data):
        """Map row data to model fields"""
        from main import AssetDriverMapping, Asset, Driver
        
        # Get the asset by identifier
        asset = Asset.query.filter_by(asset_identifier=row_data['asset_identifier']).first()
        if not asset:
            return None, f"Asset not found: {row_data['asset_identifier']}"
        
        # Get the driver by name or ID
        driver = None
        if 'driver_id' in row_data and row_data['driver_id']:
            driver = Driver.query.filter_by(employee_id=row_data['driver_id']).first()
        
        if not driver and 'driver_name' in row_data:
            # Try to find by name (exact or partial match)
            driver_name = row_data['driver_name'].strip()
            driver = Driver.query.filter(Driver.name == driver_name).first()
            if not driver:
                # Try partial match
                drivers = Driver.query.filter(Driver.name.ilike(f"%{driver_name}%")).all()
                if len(drivers) == 1:
                    driver = drivers[0]
        
        if not driver:
            return None, f"Driver not found: {row_data.get('driver_name', row_data.get('driver_id', 'Unknown'))}"
        
        # Parse dates
        start_date = datetime.now().date()
        if 'start_date' in row_data and row_data['start_date']:
            try:
                if isinstance(row_data['start_date'], datetime):
                    start_date = row_data['start_date'].date()
                else:
                    start_date = datetime.strptime(str(row_data['start_date']), '%Y-%m-%d').date()
            except ValueError:
                try:
                    start_date = datetime.strptime(str(row_data['start_date']), '%m/%d/%Y').date()
                except ValueError:
                    return None, f"Invalid start date format: {row_data['start_date']}"
        
        end_date = None
        if 'end_date' in row_data and row_data['end_date'] and row_data['end_date'] != 'None':
            try:
                if isinstance(row_data['end_date'], datetime):
                    end_date = row_data['end_date'].date()
                else:
                    end_date = datetime.strptime(str(row_data['end_date']), '%Y-%m-%d').date()
            except ValueError:
                try:
                    end_date = datetime.strptime(str(row_data['end_date']), '%m/%d/%Y').date()
                except ValueError:
                    return None, f"Invalid end date format: {row_data['end_date']}"
        
        # Determine if current
        is_current = True
        if 'is_current' in row_data:
            if isinstance(row_data['is_current'], bool):
                is_current = row_data['is_current']
            elif isinstance(row_data['is_current'], str):
                is_current = row_data['is_current'].lower() in ['true', 'yes', '1', 'y']
        
        # If we have an end date and it's in the past, assignment is not current
        if end_date and end_date < datetime.now().date():
            is_current = False
        
        # Create the model
        mapping = AssetDriverMapping(
            asset_id=asset.id,
            driver_id=driver.id,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            notes=row_data.get('notes', '')
        )
        
        return mapping, None