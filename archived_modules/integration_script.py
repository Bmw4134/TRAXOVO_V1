"""
TRAXOVO Integration Script
Complete implementation of all enhanced modules
"""
from flask import Flask
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_traxovo_modules(app: Flask):
    """Integrate all TRAXOVO enhancement modules into the main application"""
    
    logger.info("Starting TRAXOVO module integration...")
    
    try:
        # 1. Register Enhanced Attendance Module
        from enhanced_attendance_module import attendance_bp
        app.register_blueprint(attendance_bp)
        logger.info("✓ Enhanced Attendance Module integrated")
        
        # 2. Register Enhanced Asset Module  
        from enhanced_asset_module import asset_bp
        app.register_blueprint(asset_bp)
        logger.info("✓ Enhanced Asset Module integrated")
        
        # 3. Register Interactive Geofence Map
        from interactive_geofence_map import map_bp
        app.register_blueprint(map_bp)
        logger.info("✓ Interactive Geofence Map integrated")
        
        # 4. Register Optimized Dashboard UI
        from optimized_dashboard_ui import dashboard_ui_bp
        app.register_blueprint(dashboard_ui_bp)
        logger.info("✓ Optimized Dashboard UI integrated")
        
        # 5. Initialize Data Consolidation
        from data_consolidation_engine import TRAXOVODataConsolidator
        consolidator = TRAXOVODataConsolidator()
        
        # Create context processor for consolidated data
        @app.context_processor
        def inject_consolidated_data():
            """Inject consolidated authentic data into all templates"""
            try:
                consolidated = consolidator.consolidate_all_data()
                return {
                    'authentic_asset_count': len(consolidated.get('assets', [])),
                    'authentic_attendance_count': len(consolidated.get('attendance', [])),
                    'last_data_refresh': datetime.now().strftime('%H:%M:%S')
                }
            except Exception as e:
                logger.error(f"Error in context processor: {e}")
                return {}
        
        logger.info("✓ Data Consolidation Engine initialized")
        
        # 6. Add custom template filters
        @app.template_filter('currency')
        def currency_filter(value):
            """Format currency values"""
            try:
                return f"${value:,.2f}"
            except (ValueError, TypeError):
                return "$0.00"
        
        @app.template_filter('percentage')
        def percentage_filter(value):
            """Format percentage values"""
            try:
                return f"{value:.1f}%"
            except (ValueError, TypeError):
                return "0.0%"
        
        logger.info("✓ Custom template filters added")
        
        # 7. Create necessary directories
        os.makedirs('exports', exist_ok=True)
        os.makedirs('temp', exist_ok=True)
        os.makedirs('consolidated_data', exist_ok=True)
        os.makedirs('templates/attendance', exist_ok=True)
        os.makedirs('templates/asset', exist_ok=True)
        os.makedirs('templates/dashboard', exist_ok=True)
        
        logger.info("✓ Directory structure created")
        
        # 8. Add error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404
        
        @app.errorhandler(500)
        def internal_error(error):
            return render_template('errors/500.html'), 500
        
        logger.info("✓ Error handlers configured")
        
        logger.info("🚀 TRAXOVO module integration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration failed: {e}")
        return False

def run_data_consolidation():
    """Execute data consolidation process"""
    logger.info("Running data consolidation...")
    
    try:
        from data_consolidation_engine import run_data_consolidation
        consolidated, summary = run_data_consolidation()
        
        logger.info(f"✓ Data consolidation completed: {summary['data_summary']}")
        return consolidated, summary
        
    except Exception as e:
        logger.error(f"❌ Data consolidation failed: {e}")
        return None, None

def cleanup_redundant_files():
    """Clean up redundant or unused files"""
    logger.info("Cleaning up redundant files...")
    
    # List of files/patterns to clean up
    cleanup_patterns = [
        'temp/*.tmp',
        '*.pyc',
        '__pycache__/*',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    import glob
    cleaned_count = 0
    
    for pattern in cleanup_patterns:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            try:
                os.remove(file)
                cleaned_count += 1
            except OSError:
                pass
    
    logger.info(f"✓ Cleaned up {cleaned_count} redundant files")
    return cleaned_count

if __name__ == "__main__":
    # This would be imported and called from your main app
    print("TRAXOVO Integration Script")
    print("This module should be imported and integrated with your Flask app")
    print("Example usage:")
    print("from integration_script import integrate_traxovo_modules")
    print("integrate_traxovo_modules(app)")