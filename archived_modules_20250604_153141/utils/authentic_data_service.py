def get_driver_count_authentic():
    """Get the authentic count of active drivers from multiple sources"""
    try:
        # Source 1: Database
        from models.driver import Driver
        db_count = Driver.query.filter_by(is_active=True).count()

        # Source 2: Recent attendance data
        from utils.attendance_pipeline_connector import get_attendance_data
        import pandas as pd

        recent_data = get_attendance_data(force_refresh=False)
        if recent_data and 'driver_data' in recent_data:
            attendance_drivers = set()
            for record in recent_data['driver_data']:
                if record.get('name'):
                    attendance_drivers.add(record['name'])
            attendance_count = len(attendance_drivers)
        else:
            attendance_count = 0

        # Source 3: CSV files in attached_assets
        csv_count = get_csv_driver_count()

        return {
            "database_count": db_count,
            "attendance_count": attendance_count, 
            "csv_count": csv_count,
            "max_count": max(db_count, attendance_count, csv_count),
            "desktop_sync_safe": True
        }

    except Exception as e:
        return {
            "error": str(e),
            "fallback_count": 25,  # Conservative estimate
            "desktop_sync_safe": True
        }

def get_csv_driver_count():
    """Count drivers from CSV files"""
    try:
        import os
        import pandas as pd

        driver_names = set()
        csv_dir = "attached_assets"

        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    try:
                        df = pd.read_csv(os.path.join(csv_dir, file))

                        # Look for driver columns
                        driver_cols = ['Driver', 'driver', 'name', 'driver_name', 'employee']
                        for col in driver_cols:
                            if col in df.columns:
                                unique_drivers = df[col].dropna().unique()
                                for driver in unique_drivers:
                                    if str(driver) not in ['nan', 'None', '']:
                                        driver_names.add(str(driver))
                                break
                    except Exception:
                        continue

        return len(driver_names)

    except Exception:
        return 0

def get_authentic_driver_count():
    """Get the authentic count of active drivers"""