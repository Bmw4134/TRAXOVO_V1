"""
NEXUS Power BI Integration Module
Integrates Watson Intelligence data with Power BI for enterprise visualization
"""

import json
import os
from flask import jsonify
from datetime import datetime


class NexusPowerBIIntegrator:
    """Power BI integration for NEXUS Watson Intelligence platform"""
    
    def __init__(self):
        self.config = self.load_powerbi_config()
        self.base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        
    def load_powerbi_config(self):
        """Load Power BI configuration from provided JSON"""
        try:
            with open('attached_assets/nexus_powerbi_config_1749600404986.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self):
        """Default Power BI configuration"""
        return {
            "report": {
                "name": "Nexus Watson Intelligence",
                "dataSource": {
                    "type": "Web",
                    "url": f"https://{self.base_url}/api/export/full-intelligence",
                    "refreshRate": "PT5M"
                },
                "pages": [
                    {
                        "name": "Fleet Overview",
                        "visualizations": ["fleet_efficiency", "asset_status"]
                    },
                    {
                        "name": "Financial Dashboard", 
                        "visualizations": ["cost_savings", "roi_metrics"]
                    },
                    {
                        "name": "Operational Intelligence",
                        "visualizations": ["performance_kpis", "trends"]
                    }
                ]
            }
        }
    
    def get_powerbi_dataset_config(self):
        """Generate Power BI dataset configuration"""
        return {
            "dataset": {
                "name": "TRAXOVO_NEXUS_Intelligence",
                "description": "Real-time TRAXOVO fleet and operational data with Watson AI insights",
                "refreshSchedule": {
                    "frequency": "Every 5 minutes",
                    "times": ["06:00", "12:00", "18:00"],
                    "timezone": "Central Standard Time"
                },
                "tables": [
                    {
                        "name": "FleetAssets",
                        "source": {
                            "type": "Web",
                            "url": f"https://{self.base_url}/api/comprehensive-data",
                            "method": "GET"
                        },
                        "columns": [
                            {"name": "AssetID", "dataType": "string"},
                            {"name": "AssetNumber", "dataType": "string"},
                            {"name": "Status", "dataType": "string"},
                            {"name": "Location", "dataType": "string"},
                            {"name": "Utilization", "dataType": "double"},
                            {"name": "LastService", "dataType": "dateTime"},
                            {"name": "Organization", "dataType": "string"}
                        ]
                    },
                    {
                        "name": "FinancialMetrics",
                        "source": {
                            "type": "Web",
                            "url": f"https://{self.base_url}/api/financial-data",
                            "method": "GET"
                        },
                        "columns": [
                            {"name": "Period", "dataType": "dateTime"},
                            {"name": "Revenue", "dataType": "double"},
                            {"name": "Costs", "dataType": "double"},
                            {"name": "ProfitMargin", "dataType": "double"},
                            {"name": "ROI", "dataType": "double"}
                        ]
                    },
                    {
                        "name": "WatsonInsights",
                        "source": {
                            "type": "Web", 
                            "url": f"https://{self.base_url}/api/watson-intelligence",
                            "method": "GET"
                        },
                        "columns": [
                            {"name": "InsightID", "dataType": "string"},
                            {"name": "Category", "dataType": "string"},
                            {"name": "Recommendation", "dataType": "string"},
                            {"name": "Confidence", "dataType": "double"},
                            {"name": "Impact", "dataType": "string"},
                            {"name": "Timestamp", "dataType": "dateTime"}
                        ]
                    }
                ],
                "relationships": [
                    {
                        "fromTable": "FleetAssets",
                        "fromColumn": "AssetID",
                        "toTable": "WatsonInsights",
                        "toColumn": "AssetID",
                        "crossFilterDirection": "Both"
                    }
                ]
            }
        }
    
    def get_powerbi_report_template(self):
        """Generate Power BI report template configuration"""
        return {
            "report": {
                "name": "TRAXOVO_NEXUS_Executive_Dashboard",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "pages": [
                    {
                        "name": "Executive Overview",
                        "displayName": "Executive Overview",
                        "visualizations": [
                            {
                                "type": "card",
                                "title": "Total Fleet Assets",
                                "dataField": "FleetAssets[Count]",
                                "position": {"x": 0, "y": 0, "width": 200, "height": 100}
                            },
                            {
                                "type": "donutChart",
                                "title": "Asset Status Distribution",
                                "dataFields": {
                                    "category": "FleetAssets[Status]",
                                    "values": "FleetAssets[Count]"
                                },
                                "position": {"x": 220, "y": 0, "width": 300, "height": 200}
                            },
                            {
                                "type": "lineChart",
                                "title": "Fleet Utilization Trend",
                                "dataFields": {
                                    "axis": "FleetAssets[LastService]",
                                    "values": "FleetAssets[Utilization]"
                                },
                                "position": {"x": 0, "y": 220, "width": 520, "height": 200}
                            }
                        ]
                    },
                    {
                        "name": "Financial Intelligence",
                        "displayName": "Financial Intelligence",
                        "visualizations": [
                            {
                                "type": "card",
                                "title": "Monthly Revenue",
                                "dataField": "FinancialMetrics[Revenue]",
                                "position": {"x": 0, "y": 0, "width": 200, "height": 100}
                            },
                            {
                                "type": "card",
                                "title": "Cost Savings",
                                "dataField": "FinancialMetrics[CostSavings]",
                                "position": {"x": 220, "y": 0, "width": 200, "height": 100}
                            },
                            {
                                "type": "gauge",
                                "title": "ROI Performance",
                                "dataField": "FinancialMetrics[ROI]",
                                "target": 15.0,
                                "position": {"x": 440, "y": 0, "width": 200, "height": 200}
                            },
                            {
                                "type": "columnChart",
                                "title": "Revenue vs Costs Trend",
                                "dataFields": {
                                    "axis": "FinancialMetrics[Period]",
                                    "values": ["FinancialMetrics[Revenue]", "FinancialMetrics[Costs]"]
                                },
                                "position": {"x": 0, "y": 220, "width": 640, "height": 200}
                            }
                        ]
                    },
                    {
                        "name": "Watson AI Insights",
                        "displayName": "Watson AI Insights",
                        "visualizations": [
                            {
                                "type": "table",
                                "title": "AI Recommendations",
                                "dataFields": [
                                    "WatsonInsights[Category]",
                                    "WatsonInsights[Recommendation]",
                                    "WatsonInsights[Confidence]",
                                    "WatsonInsights[Impact]"
                                ],
                                "position": {"x": 0, "y": 0, "width": 640, "height": 300}
                            },
                            {
                                "type": "scatterChart",
                                "title": "Insight Confidence vs Impact",
                                "dataFields": {
                                    "x": "WatsonInsights[Confidence]",
                                    "y": "WatsonInsights[Impact]",
                                    "details": "WatsonInsights[Category]"
                                },
                                "position": {"x": 0, "y": 320, "width": 640, "height": 200}
                            }
                        ]
                    }
                ],
                "filters": [
                    {
                        "target": "FleetAssets[Organization]",
                        "type": "list",
                        "displayName": "Organization Filter"
                    },
                    {
                        "target": "FleetAssets[Status]",
                        "type": "list", 
                        "displayName": "Asset Status Filter"
                    },
                    {
                        "target": "FinancialMetrics[Period]",
                        "type": "dateRange",
                        "displayName": "Date Range Filter"
                    }
                ]
            }
        }
    
    def export_powerbi_config(self):
        """Export complete Power BI configuration for import"""
        dataset_config = self.get_powerbi_dataset_config()
        report_config = self.get_powerbi_report_template()
        
        # Save configurations to files
        os.makedirs('exports', exist_ok=True)
        
        dataset_path = 'exports/nexus_powerbi_dataset.json'
        report_path = 'exports/nexus_powerbi_report.json'
        
        with open(dataset_path, 'w') as f:
            json.dump(dataset_config, f, indent=2)
            
        with open(report_path, 'w') as f:
            json.dump(report_config, f, indent=2)
        
        return {
            "status": "success",
            "dataset_config_path": dataset_path,
            "report_config_path": report_path,
            "data_source_url": f"https://{self.base_url}/api/export/full-intelligence",
            "power_bi_config": {
                "dataset": dataset_config,
                "report": report_config
            },
            "connection_instructions": [
                "1. Open Power BI Desktop",
                "2. Get Data > Web",
                f"3. Enter URL: https://{self.base_url}/api/export/full-intelligence",
                "4. Import dataset configuration from exports/nexus_powerbi_dataset.json",
                "5. Import report template from exports/nexus_powerbi_report.json",
                "6. Configure scheduled refresh for real-time updates",
                "7. Publish to Power BI Service for enterprise sharing"
            ]
        }


def get_nexus_powerbi_integration():
    """Get NEXUS Power BI integration instance"""
    return NexusPowerBIIntegrator()