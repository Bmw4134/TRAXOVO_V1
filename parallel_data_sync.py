"""
TRAXOVO Parallel Data Synchronization Engine
Handles background data updates without blocking UI
"""
import threading
import time
import json
from datetime import datetime
import logging
from authentic_data_service import authentic_data

class ParallelDataSync:
    """Background data synchronization with 30-second intervals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sync_active = False
        self.last_sync = None
        self.sync_thread = None
        self.data_cache = {}
        
    def start_background_sync(self):
        """Start the background data sync process"""
        if not self.sync_active:
            self.sync_active = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("Parallel data sync started")
    
    def stop_background_sync(self):
        """Stop the background sync process"""
        self.sync_active = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.info("Parallel data sync stopped")
    
    def _sync_loop(self):
        """Main sync loop running every 30 seconds"""
        while self.sync_active:
            try:
                self._perform_data_sync()
                time.sleep(30)  # 30-second intervals
            except Exception as e:
                self.logger.error(f"Sync error: {e}")
                time.sleep(10)  # Shorter wait on error
    
    def _perform_data_sync(self):
        """Perform the actual data synchronization"""
        sync_timestamp = datetime.now()
        
        # Sync revenue data
        try:
            revenue_data = authentic_data.get_revenue_data()
            if revenue_data != self.data_cache.get('revenue'):
                self.data_cache['revenue'] = revenue_data
                self.logger.info(f"Revenue data synced: ${revenue_data['total_revenue']:,.2f}")
        except Exception as e:
            self.logger.error(f"Revenue sync error: {e}")
        
        # Sync asset data
        try:
            asset_data = authentic_data.get_asset_data()
            if asset_data != self.data_cache.get('assets'):
                self.data_cache['assets'] = asset_data
                self.logger.info(f"Asset data synced: {asset_data['total_assets']} assets")
        except Exception as e:
            self.logger.error(f"Asset sync error: {e}")
        
        # Sync attendance data
        try:
            attendance_data = authentic_data.get_attendance_data()
            if attendance_data != self.data_cache.get('attendance'):
                self.data_cache['attendance'] = attendance_data
                self.logger.info("Attendance data synced")
        except Exception as e:
            self.logger.error(f"Attendance sync error: {e}")
        
        self.last_sync = sync_timestamp
    
    def get_cached_data(self, data_type):
        """Get cached data without blocking"""
        return self.data_cache.get(data_type, {})
    
    def get_sync_status(self):
        """Get current sync status"""
        return {
            'active': self.sync_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'cached_datasets': list(self.data_cache.keys()),
            'next_sync_in': 30 - ((datetime.now() - self.last_sync).seconds if self.last_sync else 0)
        }

# Global sync instance
parallel_sync = ParallelDataSync()

if __name__ == "__main__":
    # Test the sync system
    parallel_sync.start_background_sync()
    
    print("🔄 Testing parallel data sync...")
    time.sleep(35)  # Wait for one sync cycle
    
    status = parallel_sync.get_sync_status()
    print(f"✅ Sync Status: {status}")
    
    parallel_sync.stop_background_sync()