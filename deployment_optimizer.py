"""
TRAXOVO Deployment Size Optimizer
Reduces project size for rapid deployment under 2GB limit
"""

import os
import shutil
import logging
from pathlib import Path

class DeploymentOptimizer:
    """Optimizes project for deployment by removing non-essential files"""
    
    def __init__(self):
        self.removed_size = 0
        self.optimization_log = []
        
    def optimize_for_deployment(self):
        """Run complete optimization for deployment"""
        print("🚀 Starting TRAXOVO deployment optimization...")
        
        # Step 1: Remove large attached assets
        self._optimize_attached_assets()
        
        # Step 2: Clean test files
        self._clean_test_files()
        
        # Step 3: Remove backup files
        self._clean_backup_files()
        
        # Step 4: Optimize static assets
        self._optimize_static_assets()
        
        # Step 5: Clean cache and temp files
        self._clean_cache_files()
        
        print(f"✅ Optimization complete! Removed {self.removed_size / (1024*1024):.1f}MB")
        return self.optimization_log
    
    def _optimize_attached_assets(self):
        """Keep only essential attached assets"""
        assets_dir = Path("attached_assets")
        if not assets_dir.exists():
            return
            
        # Keep only small essential files
        essential_files = {
            "image.jpg",
            "IMG_8907.png", 
            "IMG_8935.png",
            "IMG_8940.png"
        }
        
        for file_path in assets_dir.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                
                # Remove large files not in essential list
                if file_size > 1024*1024 or file_path.name not in essential_files:  # >1MB
                    self.removed_size += file_size
                    file_path.unlink()
                    self.optimization_log.append(f"Removed large asset: {file_path.name}")
        
        # Remove entire subdirectories in attached_assets
        for subdir in assets_dir.iterdir():
            if subdir.is_dir():
                dir_size = sum(f.stat().st_size for f in subdir.rglob('*') if f.is_file())
                self.removed_size += dir_size
                shutil.rmtree(subdir)
                self.optimization_log.append(f"Removed asset directory: {subdir.name}")
    
    def _clean_test_files(self):
        """Remove large test and pipeline files"""
        test_files = [
            "pipeline_test_results_20250522_211001.json",
            "pipeline_test_results_20250522_211001.min.json"
        ]
        
        for filename in test_files:
            file_path = Path(filename)
            if file_path.exists():
                file_size = file_path.stat().st_size
                self.removed_size += file_size
                file_path.unlink()
                self.optimization_log.append(f"Removed test file: {filename}")
    
    def _clean_backup_files(self):
        """Remove backup directories and files"""
        backup_dirs = [
            "backup_excel_files",
            "templates_backup_20250527_170301",
            "backups",
            "temp_backup"
        ]
        
        for dirname in backup_dirs:
            dir_path = Path(dirname)
            if dir_path.exists():
                if dir_path.is_dir():
                    dir_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    self.removed_size += dir_size
                    shutil.rmtree(dir_path)
                    self.optimization_log.append(f"Removed backup directory: {dirname}")
        
        # Remove large Excel files
        excel_files = [
            "RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm",
            "RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm"
        ]
        
        for filename in excel_files:
            file_path = Path(filename)
            if file_path.exists():
                file_size = file_path.stat().st_size
                self.removed_size += file_size
                file_path.unlink()
                self.optimization_log.append(f"Removed large Excel file: {filename}")
    
    def _optimize_static_assets(self):
        """Optimize static directory"""
        static_dir = Path("static")
        if not static_dir.exists():
            return
            
        # Remove any large files in static
        for file_path in static_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > 500*1024:  # >500KB
                file_size = file_path.stat().st_size
                self.removed_size += file_size
                file_path.unlink()
                self.optimization_log.append(f"Removed large static file: {file_path.name}")
    
    def _clean_cache_files(self):
        """Remove cache and temporary files"""
        cache_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo", 
            ".pytest_cache",
            "node_modules/.cache",
            "*.log"
        ]
        
        # Remove __pycache__ directories
        for pycache_dir in Path('.').rglob('__pycache__'):
            if pycache_dir.is_dir():
                dir_size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                self.removed_size += dir_size
                shutil.rmtree(pycache_dir)
                self.optimization_log.append(f"Removed cache directory: {pycache_dir}")
        
        # Remove log files
        for log_file in Path('.').rglob('*.log'):
            if log_file.is_file():
                file_size = log_file.stat().st_size
                self.removed_size += file_size
                log_file.unlink()
                self.optimization_log.append(f"Removed log file: {log_file.name}")

if __name__ == "__main__":
    optimizer = DeploymentOptimizer()
    log = optimizer.optimize_for_deployment()
    
    for entry in log:
        print(f"  {entry}")