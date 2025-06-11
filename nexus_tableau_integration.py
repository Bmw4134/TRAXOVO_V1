"""
NEXUS Tableau Integration Module
Integrates Watson Intelligence data with Tableau for enterprise visualization
"""

import json
import os
from flask import jsonify
from datetime import datetime


class NexusTableauIntegrator:
    """Tableau integration for NEXUS Watson Intelligence platform"""
    
    def __init__(self):
        self.config = self.load_tableau_config()
        self.base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        
    def load_tableau_config(self):
        """Load Tableau configuration from provided JSON"""
        try:
            with open('attached_assets/nexus_tableau_config_1749600365541.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self):
        """Default Tableau configuration"""
        return {
            "workbook": {
                "name": "Nexus Watson Intelligence",
                "datasource": {
                    "name": "Nexus Data",
                    "connection": {
                        "class": "webdata-direct",
                        "url": f"https://{self.base_url}/api/export/full-intelligence"
                    }
                },
                "worksheets": [
                    {
                        "name": "Fleet Dashboard",
                        "type": "dashboard"
                    },
                    {
                        "name": "Financial KPIs", 
                        "type": "scorecard"
                    },
                    {
                        "name": "Operational Metrics",
                        "type": "visualization"
                    }
                ]
            }
        }
    
    def get_tableau_data_source(self):
        """Generate Tableau-compatible data source configuration"""
        return {
            "datasource": {
                "name": "TRAXOVO_NEXUS_Intelligence",
                "connection": {
                    "class": "webdata-direct",
                    "url": f"https://{self.base_url}/api/export/full-intelligence",
                    "authentication": "none",
                    "refresh_frequency": "15min"
                },
                "tables": [
                    {
                        "name": "fleet_assets",
                        "schema": {
                            "asset_id": "string",
                            "asset_number": "string", 
                            "status": "string",
                            "location": "string",
                            "utilization": "number",
                            "last_service": "datetime"
                        }
                    },
                    {
                        "name": "financial_metrics",
                        "schema": {
                            "period": "datetime",
                            "revenue": "number",
                            "costs": "number",
                            "profit_margin": "number",
                            "roi": "number"
                        }
                    },
                    {
                        "name": "operational_kpis",
                        "schema": {
                            "metric_name": "string",
                            "value": "number",
                            "target": "number",
                            "variance": "number",
                            "timestamp": "datetime"
                        }
                    }
                ]
            }
        }
    
    def get_tableau_workbook_config(self):
        """Generate complete Tableau workbook configuration"""
        return {
            "workbook": {
                "name": "TRAXOVO_NEXUS_Executive_Intelligence",
                "version": "2024.1",
                "created": datetime.now().isoformat(),
                "datasources": [self.get_tableau_data_source()],
                "dashboards": [
                    {
                        "name": "Executive Overview",
                        "sheets": [
                            "Fleet_Performance_Summary",
                            "Financial_KPI_Scorecard", 
                            "Operational_Efficiency_Metrics"
                        ]
                    },
                    {
                        "name": "Asset Intelligence",
                        "sheets": [
                            "Asset_Utilization_Heatmap",
                            "Maintenance_Schedule_Timeline",
                            "Geographic_Asset_Distribution"
                        ]
                    },
                    {
                        "name": "Watson Intelligence Insights",
                        "sheets": [
                            "AI_Recommendations",
                            "Predictive_Analytics",
                            "Anomaly_Detection_Alerts"
                        ]
                    }
                ],
                "parameters": {
                    "date_range": {
                        "type": "date_range",
                        "default": "last_30_days"
                    },
                    "asset_filter": {
                        "type": "string_list", 
                        "default": "all"
                    },
                    "organization_filter": {
                        "type": "string_list",
                        "default": "all"
                    }
                }
            }
        }
    
    def export_tableau_config(self):
        """Export complete Tableau configuration for import"""
        config = self.get_tableau_workbook_config()
        
        # Save configuration to file
        output_path = 'exports/nexus_tableau_workbook.json'
        os.makedirs('exports', exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "status": "success",
            "config_path": output_path,
            "tableau_config": config,
            "data_source_url": f"https://{self.base_url}/api/export/full-intelligence",
            "connection_instructions": [
                "1. Open Tableau Desktop",
                "2. Connect to Data > Web Data Connector",
                f"3. Enter URL: https://{self.base_url}/api/export/full-intelligence", 
                "4. Import the workbook configuration from exports/nexus_tableau_workbook.json",
                "5. Configure refresh schedule for real-time updates"
            ]
        }


def get_nexus_tableau_integration():
    """Get NEXUS Tableau integration instance"""
    return NexusTableauIntegrator()