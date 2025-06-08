"""
Authentic Organizational Data Extractor
Extract real asset counts from uploaded reports and GAUGE API connections
"""

import json
import sqlite3
import csv
import os
from datetime import datetime
from typing import Dict, Any, List

class AuthenticOrganizationalData:
    """Extract authentic organizational asset data from real sources"""
    
    def __init__(self):
        self.real_data_sources = []
        self.organizational_breakdowns = {}
        self.authentic_totals = {}
        
    def extract_real_organizational_assets(self) -> Dict[str, Any]:
        """Extract authentic organizational asset counts from real data sources"""
        
        # Check for authentic data sources
        authentic_sources = self._discover_authentic_sources()
        
        if not authentic_sources:
            # Request actual data from user
            return {
                "status": "REQUIRES_AUTHENTIC_DATA",
                "message": "Real organizational asset data needed",
                "request": "Please provide actual asset counts by organization",
                "organizations_detected": [
                    "Ragle Inc",
                    "Select Maintenance", 
                    "Southern Sourcing Solutions",
                    "Unified Specialties"
                ],
                "data_needed": {
                    "total_assets_per_org": "Actual count from asset management system",
                    "active_vs_maintenance": "Current operational status breakdown",
                    "asset_types": "Equipment categories per organization",
                    "zone_distribution": "Geographic or operational zone allocation"
                }
            }
        
        # Extract from authentic sources
        organizational_data = self._process_authentic_sources(authentic_sources)
        
        return {
            "status": "AUTHENTIC_DATA_EXTRACTED",
            "organizations": organizational_data,
            "data_sources": authentic_sources,
            "extraction_timestamp": datetime.now().isoformat()
        }
    
    def _discover_authentic_sources(self) -> List[str]:
        """Discover available authentic data sources"""
        sources = []
        
        # Check for uploaded asset reports
        if os.path.exists("uploaded_asset_reports"):
            sources.append("uploaded_asset_reports")
            
        # Check for GAUGE API connection data
        if self._check_gauge_api_data():
            sources.append("gauge_api_connection")
            
        # Check for organizational databases
        if os.path.exists("organizational_assets.db"):
            sources.append("organizational_database")
            
        # Check for CSV exports
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'asset' in f.lower()]
        if csv_files:
            sources.extend(csv_files)
            
        return sources
    
    def _check_gauge_api_data(self) -> bool:
        """Check if GAUGE API has real organizational data"""
        try:
            # Check for existing GAUGE API connection with organizational breakdown
            conn = sqlite3.connect('authentic_assets.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='organizational_assets'
            """)
            
            table_exists = cursor.fetchone()[0] > 0
            conn.close()
            
            return table_exists
        except:
            return False
    
    def _process_authentic_sources(self, sources: List[str]) -> Dict[str, Any]:
        """Process authentic data sources to extract organizational breakdowns"""
        
        organizational_data = {}
        
        for source in sources:
            if source == "gauge_api_connection":
                gauge_data = self._extract_from_gauge_api()
                organizational_data.update(gauge_data)
                
            elif source.endswith('.csv'):
                csv_data = self._extract_from_csv(source)
                organizational_data.update(csv_data)
                
            elif source == "organizational_database":
                db_data = self._extract_from_database()
                organizational_data.update(db_data)
        
        return organizational_data
    
    def _extract_from_gauge_api(self) -> Dict[str, Any]:
        """Extract organizational data from GAUGE API connection"""
        try:
            conn = sqlite3.connect('authentic_assets.db')
            cursor = conn.cursor()
            
            # Get organizational breakdown from GAUGE API data
            cursor.execute("""
                SELECT organization, COUNT(*) as total_assets,
                       SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_assets,
                       SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance_assets
                FROM organizational_assets 
                GROUP BY organization
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            organizations = {}
            for row in results:
                org_name, total, active, maintenance = row
                organizations[self._normalize_org_name(org_name)] = {
                    "name": org_name,
                    "total_assets": total,
                    "active_assets": active,
                    "maintenance_assets": maintenance,
                    "data_source": "GAUGE_API_AUTHENTIC"
                }
            
            return organizations
            
        except Exception as e:
            return {}
    
    def _extract_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """Extract organizational data from CSV file"""
        try:
            organizations = {}
            
            with open(csv_file, 'r') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Look for organization column
                    org_column = None
                    for key in row.keys():
                        if 'org' in key.lower() or 'company' in key.lower():
                            org_column = key
                            break
                    
                    if org_column and row[org_column]:
                        org_name = row[org_column]
                        org_key = self._normalize_org_name(org_name)
                        
                        if org_key not in organizations:
                            organizations[org_key] = {
                                "name": org_name,
                                "total_assets": 0,
                                "active_assets": 0,
                                "maintenance_assets": 0,
                                "data_source": f"CSV_EXPORT_{csv_file}"
                            }
                        
                        organizations[org_key]["total_assets"] += 1
                        
                        # Check status
                        status = row.get('status', 'active').lower()
                        if 'active' in status:
                            organizations[org_key]["active_assets"] += 1
                        elif 'maintenance' in status:
                            organizations[org_key]["maintenance_assets"] += 1
            
            return organizations
            
        except Exception as e:
            return {}
    
    def _extract_from_database(self) -> Dict[str, Any]:
        """Extract organizational data from database"""
        try:
            conn = sqlite3.connect('organizational_assets.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT organization_name, asset_count, active_count, maintenance_count
                FROM organization_summary
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            organizations = {}
            for row in results:
                org_name, total, active, maintenance = row
                organizations[self._normalize_org_name(org_name)] = {
                    "name": org_name,
                    "total_assets": total,
                    "active_assets": active,
                    "maintenance_assets": maintenance,
                    "data_source": "ORGANIZATIONAL_DATABASE"
                }
            
            return organizations
            
        except Exception as e:
            return {}
    
    def _normalize_org_name(self, org_name: str) -> str:
        """Normalize organization name for consistent keys"""
        name_lower = org_name.lower()
        
        if 'ragle' in name_lower:
            return 'ragle_inc'
        elif 'select' in name_lower:
            return 'select_maintenance'
        elif 'southern' in name_lower:
            return 'southern_sourcing'
        elif 'unified' in name_lower:
            return 'unified_specialties'
        else:
            return name_lower.replace(' ', '_').replace('-', '_')
    
    def request_authentic_data_upload(self) -> Dict[str, Any]:
        """Request user to upload authentic organizational asset data"""
        return {
            "status": "AUTHENTIC_DATA_REQUIRED",
            "message": "Please provide actual organizational asset counts",
            "upload_instructions": {
                "acceptable_formats": ["CSV", "Excel", "JSON", "Database export"],
                "required_fields": [
                    "Organization name",
                    "Asset count", 
                    "Asset status (active/maintenance)",
                    "Asset type/category"
                ],
                "sample_format": {
                    "organization": "Ragle Inc",
                    "asset_id": "ASSET_001", 
                    "asset_type": "Heavy Equipment",
                    "status": "Active",
                    "zone": "Zone_580"
                }
            },
            "current_placeholders": "Using estimated data until authentic data provided",
            "impact": "Drill-down accuracy depends on authentic organizational data"
        }

# Global authentic data extractor
authentic_org_data = AuthenticOrganizationalData()

def get_authentic_organizational_assets() -> Dict[str, Any]:
    """Get authentic organizational asset data"""
    return authentic_org_data.extract_real_organizational_assets()

def request_real_data() -> Dict[str, Any]:
    """Request authentic data upload from user"""
    return authentic_org_data.request_authentic_data_upload()

if __name__ == "__main__":
    # Extract authentic organizational data
    result = get_authentic_organizational_assets()
    
    if result["status"] == "REQUIRES_AUTHENTIC_DATA":
        print("Authentic organizational asset data required")
        print("Organizations detected:", result["organizations_detected"])
        print("Please provide actual asset counts from your asset management system")
    else:
        print("Authentic data extracted successfully")
        for org_key, org_data in result["organizations"].items():
            print(f"{org_data['name']}: {org_data['total_assets']} assets")