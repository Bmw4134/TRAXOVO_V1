"""
TRAXORA Fleet Management System - Model Replacement Script

This script rebuilds the Driver model without the problematic assigned_assets relationship.
"""
import os
import logging
import importlib
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def rebuild_models():
    """Rebuild the models.py file to remove the assigned_assets relationship"""
    # Backup the original models.py file
    try:
        with open('models.py', 'r') as f:
            original_content = f.read()
        
        backup_filename = f'models.py.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(backup_filename, 'w') as f:
            f.write(original_content)
        
        logger.info(f"Backed up original models.py to {backup_filename}")
        
        # Replace all instances of "assigned_assets" in the file
        modified_content = original_content.replace("assigned_assets", "_removed_assigned_assets")
        
        # Write the modified content back to models.py
        with open('models.py', 'w') as f:
            f.write(modified_content)
        
        logger.info("Successfully removed assigned_assets references from models.py")
        return True
    
    except Exception as e:
        logger.error(f"Error rebuilding models: {str(e)}")
        return False

if __name__ == "__main__":
    success = rebuild_models()
    if success:
        print("✅ Driver model successfully rebuilt! Please restart the application.")
    else:
        print("❌ Failed to rebuild Driver model. Check the logs for details.")