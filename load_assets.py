"""
Load asset data into the database from the cached JSON file

This script is used to load the asset data from the cached JSON file into the database
to ensure it's available for display in the dashboard and asset pages.
"""
import os
import json
import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data file paths
DATA_FILE = os.path.join('data', 'gauge_api_data.json')

def main():
    """Main function to load asset data into the database"""
    # Import inside function to avoid circular imports
    from app import app, db
    from models.models import Asset

    logger.info("Starting asset data import to database...")

    if not os.path.exists(DATA_FILE):
        logger.error(f"Data file not found: {DATA_FILE}")
        return False

    try:
        # Load data from JSON file
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        # Check if the data is in the expected format
        if isinstance(data, dict) and 'assets' in data:
            assets = data['assets']
            logger.info(f"Loaded {len(assets)} assets from file")
        elif isinstance(data, list):
            assets = data
            logger.info(f"Loaded {len(assets)} assets from file (old format)")
        else:
            logger.error(f"Unexpected data format in file: {type(data)}")
            return False

        # Initialize counters
        created = 0
        updated = 0
        errors = 0
        
        # Process each asset
        with app.app_context():
            for asset_data in assets:
                try:
                    # Get required fields with fallbacks
                    asset_id = asset_data.get('AssetIdentifier')
                    if not asset_id:
                        logger.warning(f"Skipping asset without AssetIdentifier: {asset_data}")
                        continue
                    
                    # Check if asset already exists
                    asset = Asset.query.filter_by(asset_identifier=asset_id).first()
                    
                    if asset:
                        # Update existing asset
                        asset.label = asset_data.get('Label', '')
                        asset.asset_category = asset_data.get('AssetCategory', '')
                        asset.asset_class = asset_data.get('AssetClass', '')
                        asset.asset_make = asset_data.get('AssetMake', '')
                        asset.asset_model = asset_data.get('AssetModel', '')
                        asset.serial_number = asset_data.get('SerialNumber', '')
                        asset.device_serial_number = asset_data.get('DeviceSerialNumber', '')
                        asset.active = asset_data.get('Active', False)
                        asset.days_inactive = asset_data.get('DaysInactive', '')
                        asset.ignition = asset_data.get('Ignition', False)
                        asset.latitude = asset_data.get('Latitude')
                        asset.longitude = asset_data.get('Longitude')
                        asset.location = asset_data.get('Location', '')
                        asset.site = asset_data.get('Site', '')
                        asset.district = asset_data.get('District', '')
                        asset.sub_district = asset_data.get('SubDistrict', '')
                        asset.engine_hours = asset_data.get('Engine1Hours')
                        asset.odometer = asset_data.get('Odometer')
                        asset.speed = asset_data.get('Speed')
                        asset.speed_limit = asset_data.get('SpeedLimit')
                        asset.heading = asset_data.get('Heading', '')
                        asset.backup_battery_pct = asset_data.get('BackupBatteryPct')
                        asset.voltage = asset_data.get('Voltage')
                        asset.imei = asset_data.get('IMEI', '')
                        asset.event_date_time_string = asset_data.get('EventDateTimeString', '')
                        asset.reason = asset_data.get('Reason', '')
                        asset.time_zone = asset_data.get('TimeZone', '')
                        asset.updated_at = datetime.utcnow()
                        
                        updated += 1
                    else:
                        # Create new asset
                        asset = Asset(
                            asset_identifier=asset_id,
                            label=asset_data.get('Label', ''),
                            asset_category=asset_data.get('AssetCategory', ''),
                            asset_class=asset_data.get('AssetClass', ''),
                            asset_make=asset_data.get('AssetMake', ''),
                            asset_model=asset_data.get('AssetModel', ''),
                            serial_number=asset_data.get('SerialNumber', ''),
                            device_serial_number=asset_data.get('DeviceSerialNumber', ''),
                            active=asset_data.get('Active', False),
                            days_inactive=asset_data.get('DaysInactive', ''),
                            ignition=asset_data.get('Ignition', False),
                            latitude=asset_data.get('Latitude'),
                            longitude=asset_data.get('Longitude'),
                            location=asset_data.get('Location', ''),
                            site=asset_data.get('Site', ''),
                            district=asset_data.get('District', ''),
                            sub_district=asset_data.get('SubDistrict', ''),
                            engine_hours=asset_data.get('Engine1Hours'),
                            odometer=asset_data.get('Odometer'),
                            speed=asset_data.get('Speed'),
                            speed_limit=asset_data.get('SpeedLimit'),
                            heading=asset_data.get('Heading', ''),
                            backup_battery_pct=asset_data.get('BackupBatteryPct'),
                            voltage=asset_data.get('Voltage'),
                            imei=asset_data.get('IMEI', ''),
                            event_date_time_string=asset_data.get('EventDateTimeString', ''),
                            reason=asset_data.get('Reason', ''),
                            time_zone=asset_data.get('TimeZone', ''),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.session.add(asset)
                        created += 1
                    
                    # Commit periodically to avoid huge transactions
                    if (created + updated) % 100 == 0:
                        db.session.commit()
                        logger.info(f"Processed {created + updated} assets so far")
                
                except SQLAlchemyError as e:
                    logger.error(f"Database error while processing asset {asset_id}: {str(e)}")
                    errors += 1
                except Exception as e:
                    logger.error(f"Error processing asset {asset_id}: {str(e)}")
                    errors += 1
            
            # Final commit
            try:
                db.session.commit()
                logger.info(f"Successfully imported {created + updated} assets ({created} created, {updated} updated)")
                if errors > 0:
                    logger.warning(f"Encountered {errors} errors during import")
                return True
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Failed to commit changes: {str(e)}")
                return False
    
    except Exception as e:
        logger.error(f"Error importing assets: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()