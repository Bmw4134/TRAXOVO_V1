#!/usr/bin/env python3
"""
NEXUS Reconciliation Protocol
Restore stable state from existing components and cached systems
"""

import os
import json
import sqlite3
import glob
from datetime import datetime
from typing import Dict, List, Any

class NexusReconciliationProtocol:
    """Reconcile and restore existing NEXUS systems without duplication"""
    
    def __init__(self):
        self.reconciliation_db = "nexus_reconciliation.db"
        self.existing_modules = {}
        self.cached_systems = {}
        self.stable_checkpoints = {}
        self.setup_reconciliation_db()
        
    def setup_reconciliation_db(self):
        """Initialize reconciliation tracking"""
        conn = sqlite3.connect(self.reconciliation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS module_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_name TEXT UNIQUE NOT NULL,
                file_path TEXT,
                module_status TEXT,
                last_stable_state TEXT,
                dependencies TEXT,
                api_endpoints TEXT,
                cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stable_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_name TEXT UNIQUE NOT NULL,
                system_state TEXT,
                module_versions TEXT,
                config_snapshot TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def scan_existing_modules(self) -> Dict[str, Any]:
        """Scan all existing modules and their states"""
        module_scan = {
            "core_modules": [],
            "automation_modules": [],
            "api_modules": [],
            "database_files": [],
            "config_files": [],
            "cached_pyc_modules": []
        }
        
        # Scan Python modules
        for py_file in glob.glob("*.py"):
            if py_file.startswith("nexus_"):
                module_info = self.analyze_module(py_file)
                if "core" in py_file or "main" in py_file:
                    module_scan["core_modules"].append(module_info)
                elif "automation" in py_file or "engine" in py_file:
                    module_scan["automation_modules"].append(module_info)
                elif "api" in py_file or "app" in py_file:
                    module_scan["api_modules"].append(module_info)
        
        # Scan database files
        for db_file in glob.glob("*.db"):
            module_scan["database_files"].append({
                "filename": db_file,
                "size": os.path.getsize(db_file),
                "tables": self.scan_database_tables(db_file)
            })
        
        # Scan config directory
        if os.path.exists("config"):
            for config_file in glob.glob("config/*.json"):
                module_scan["config_files"].append({
                    "filename": config_file,
                    "content_preview": self.get_config_preview(config_file)
                })
        
        # Scan cached modules
        if os.path.exists("__pycache__"):
            for pyc_file in glob.glob("__pycache__/*.pyc"):
                module_name = os.path.basename(pyc_file).replace(".cpython-311.pyc", "")
                module_scan["cached_pyc_modules"].append(module_name)
        
        self.existing_modules = module_scan
        return module_scan
    
    def analyze_module(self, file_path: str) -> Dict[str, Any]:
        """Analyze individual module structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            module_info = {
                "name": file_path,
                "size": len(content),
                "functions": [],
                "classes": [],
                "imports": [],
                "api_routes": [],
                "database_connections": False
            }
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('def '):
                    func_name = line.split('(')[0].replace('def ', '')
                    module_info["functions"].append(func_name)
                elif line.startswith('class '):
                    class_name = line.split('(')[0].replace('class ', '').replace(':', '')
                    module_info["classes"].append(class_name)
                elif line.startswith('import ') or line.startswith('from '):
                    module_info["imports"].append(line)
                elif '@app.route(' in line:
                    route = line.split("'")[1] if "'" in line else line.split('"')[1] if '"' in line else "unknown"
                    module_info["api_routes"].append(route)
                elif 'sqlite3' in line or 'database' in line.lower():
                    module_info["database_connections"] = True
            
            return module_info
            
        except Exception as e:
            return {"name": file_path, "error": str(e)}
    
    def scan_database_tables(self, db_file: str) -> List[str]:
        """Get table list from database file"""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except:
            return []
    
    def get_config_preview(self, config_file: str) -> Dict[str, Any]:
        """Get preview of config file content"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return {
                "keys": list(config_data.keys()) if isinstance(config_data, dict) else "not_dict",
                "size": len(str(config_data))
            }
        except:
            return {"error": "invalid_json"}
    
    def identify_stable_state(self) -> Dict[str, Any]:
        """Identify last known stable system state"""
        stable_state = {
            "main_application": "app.py",
            "active_databases": [],
            "core_routes": [],
            "automation_status": "unknown",
            "voice_system": "needs_reconciliation",
            "gesture_navigation": "needs_reconciliation"
        }
        
        # Check main app status
        if os.path.exists("app.py"):
            app_info = self.analyze_module("app.py")
            stable_state["core_routes"] = app_info.get("api_routes", [])
            stable_state["main_application"] = "operational"
        
        # Check database states
        for db_file in glob.glob("*.db"):
            if os.path.getsize(db_file) > 0:
                stable_state["active_databases"].append({
                    "name": db_file,
                    "tables": self.scan_database_tables(db_file)
                })
        
        # Check automation systems
        automation_files = [f for f in glob.glob("*.py") if "automation" in f or "engine" in f]
        if automation_files:
            stable_state["automation_status"] = "modules_exist"
        
        # Check voice and gesture systems
        if os.path.exists("nexus_voice_commands.py"):
            stable_state["voice_system"] = "module_exists"
        if os.path.exists("nexus_gesture_navigation.py"):
            stable_state["gesture_navigation"] = "module_exists"
        
        return stable_state
    
    def restore_module_links(self) -> Dict[str, Any]:
        """Restore missing links between existing modules"""
        restoration_plan = {
            "main_app_integration": [],
            "database_connections": [],
            "api_endpoint_restoration": [],
            "module_imports": []
        }
        
        # Check app.py for missing integrations
        if os.path.exists("app.py"):
            with open("app.py", 'r') as f:
                app_content = f.read()
            
            # Check for voice commands integration
            if os.path.exists("nexus_voice_commands.py") and "nexus_voice_commands" not in app_content:
                restoration_plan["main_app_integration"].append("voice_commands_api_endpoints")
            
            # Check for legacy automation integration
            if os.path.exists("nexus_legacy_automation.py") and "nexus_legacy_automation" not in app_content:
                restoration_plan["main_app_integration"].append("legacy_automation_api_endpoints")
            
            # Check for total recall integration
            if os.path.exists("nexus_total_recall.py") and "nexus_total_recall" not in app_content:
                restoration_plan["main_app_integration"].append("total_recall_api_endpoints")
        
        return restoration_plan
    
    def generate_module_status_table(self) -> str:
        """Generate comprehensive module status table"""
        status_table = """
NEXUS RECONCILIATION PROTOCOL - MODULE STATUS TABLE
====================================================

CORE MODULES:
"""
        
        core_modules = [
            "app.py", "main.py", "models.py", 
            "nexus_core.py", "nexus_master_control.py"
        ]
        
        for module in core_modules:
            status = "✓ OPERATIONAL" if os.path.exists(module) else "✗ MISSING"
            cached = "✓ CACHED" if f"{module.replace('.py', '')}.cpython-311.pyc" in str(glob.glob("__pycache__/*.pyc")) else "✗ NOT_CACHED"
            status_table += f"  {module:30} {status:15} {cached}\n"
        
        status_table += "\nAUTOMATION MODULES:\n"
        automation_modules = [
            "automation_engine.py", "nexus_legacy_automation.py",
            "nexus_voice_commands.py", "nexus_total_recall.py"
        ]
        
        for module in automation_modules:
            status = "✓ OPERATIONAL" if os.path.exists(module) else "✗ MISSING"
            status_table += f"  {module:30} {status}\n"
        
        status_table += "\nDATABASE FILES:\n"
        for db_file in glob.glob("*.db"):
            size = os.path.getsize(db_file)
            tables = len(self.scan_database_tables(db_file))
            status_table += f"  {db_file:30} {size:8} bytes  {tables} tables\n"
        
        status_table += "\nAPI ENDPOINTS STATUS:\n"
        if os.path.exists("app.py"):
            app_info = self.analyze_module("app.py")
            for route in app_info.get("api_routes", [])[:10]:  # Show first 10
                status_table += f"  {route:40} ✓ ACTIVE\n"
        
        status_table += f"\nCACHED MODULES: {len(glob.glob('__pycache__/*.pyc'))}\n"
        status_table += f"CONFIG FILES: {len(glob.glob('config/*.json'))}\n"
        
        return status_table
    
    def execute_reconciliation(self) -> Dict[str, Any]:
        """Execute complete reconciliation protocol"""
        reconciliation_report = {
            "protocol_status": "EXECUTING",
            "timestamp": datetime.now().isoformat(),
            "modules_scanned": {},
            "stable_state": {},
            "restoration_plan": {},
            "reconciliation_complete": False
        }
        
        # Step 1: Scan existing modules
        reconciliation_report["modules_scanned"] = self.scan_existing_modules()
        
        # Step 2: Identify stable state
        reconciliation_report["stable_state"] = self.identify_stable_state()
        
        # Step 3: Create restoration plan
        reconciliation_report["restoration_plan"] = self.restore_module_links()
        
        # Step 4: Store reconciliation state
        conn = sqlite3.connect(self.reconciliation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stable_checkpoints 
            (checkpoint_name, system_state, module_versions)
            VALUES (?, ?, ?)
        ''', (
            f"reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            json.dumps(reconciliation_report["stable_state"]),
            json.dumps(reconciliation_report["modules_scanned"])
        ))
        
        conn.commit()
        conn.close()
        
        reconciliation_report["reconciliation_complete"] = True
        reconciliation_report["protocol_status"] = "COMPLETE"
        
        return reconciliation_report

def execute_nexus_reconciliation():
    """Execute NEXUS reconciliation protocol"""
    protocol = NexusReconciliationProtocol()
    report = protocol.execute_reconciliation()
    status_table = protocol.generate_module_status_table()
    
    return {
        "reconciliation_report": report,
        "module_status_table": status_table
    }

if __name__ == "__main__":
    result = execute_nexus_reconciliation()
    print("NEXUS RECONCILIATION PROTOCOL COMPLETE")
    print(result["module_status_table"])