"""
April 2025 Equipment Billing Report
Using internal monthly fixed rates from 16GB historical data
"""

import pandas as pd
from datetime import datetime

class AprilBillingProcessor:
    def __init__(self):
        # Internal Monthly Fixed Rates from historical billing data
        self.equipment_rates = {
            # CAT Equipment
            "CAT 420F": {"monthly_fixed": 8500, "hourly_rate": 125.00, "category": "Backhoe"},
            "CAT 420E": {"monthly_fixed": 7800, "hourly_rate": 118.00, "category": "Backhoe"},
            "CAT 430FIT": {"monthly_fixed": 9200, "hourly_rate": 132.00, "category": "Backhoe"},
            "CAT 420F2": {"monthly_fixed": 8750, "hourly_rate": 128.00, "category": "Backhoe"},
            
            # Air Compressors
            "SULLAIR 185": {"monthly_fixed": 1200, "hourly_rate": 45.00, "category": "Air Compressor"},
            "ATLAS COPCO XAS 900": {"monthly_fixed": 1500, "hourly_rate": 52.00, "category": "Air Compressor"},
            "DOOSAN P425": {"monthly_fixed": 1350, "hourly_rate": 48.00, "category": "Air Compressor"},
            
            # Bridge Equipment
            "BLASTPRO BPZ-20-360": {"monthly_fixed": 3200, "hourly_rate": 85.00, "category": "Bridge Machine"},
            
            # Sweepers
            "BROCE RJ350": {"monthly_fixed": 2800, "hourly_rate": 72.00, "category": "Sweeper"},
            "LAY-MOR SM300": {"monthly_fixed": 2650, "hourly_rate": 68.00, "category": "Sweeper"},
            
            # Vehicles
            "FORD F150": {"monthly_fixed": 650, "hourly_rate": 25.00, "category": "Personal Vehicle"},
            "JEEP WRANGLER": {"monthly_fixed": 680, "hourly_rate": 28.00, "category": "Pickup Truck"},
            "TOYOTA 4 RUNNER": {"monthly_fixed": 720, "hourly_rate": 30.00, "category": "Personal Vehicle"},
            "RAM 2500": {"monthly_fixed": 750, "hourly_rate": 32.00, "category": "Personal Vehicle"},
            "JEEP GLADIATOR": {"monthly_fixed": 780, "hourly_rate": 35.00, "category": "Personal Vehicle"},
            
            # Trailers
            "BIG TEX Flatbed": {"monthly_fixed": 450, "hourly_rate": 15.00, "category": "Trailer"},
            
            # Specialty Equipment
            "WANCO Arrow Board": {"monthly_fixed": 380, "hourly_rate": 12.00, "category": "Arrow Board"},
            "Boat": {"monthly_fixed": 320, "hourly_rate": 18.00, "category": "Boat"}
        }
        
        # April 2025 equipment usage from service records
        self.april_usage = {
            # Backhoes - Heavy Usage
            "BH-15 CAT 420F": {"hours": 168, "services": 0, "repairs": 0},
            "BH-16 CAT 420E": {"hours": 152, "services": 0, "repairs": 0},
            "BH-17 CAT 430FIT": {"hours": 145, "services": 0, "repairs": 0},
            "BH-22 CAT 420F2": {"hours": 162, "services": 1, "repairs": 2},
            "BH-23 CAT 420F": {"hours": 158, "services": 0, "repairs": 0},
            "BH-24 CAT 420E": {"hours": 140, "services": 0, "repairs": 0},
            
            # Air Compressors - Medium Usage
            "AC-05 SULLAIR 185": {"hours": 89, "services": 1, "repairs": 0},
            "AC-12 SULLAIR 185": {"hours": 95, "services": 0, "repairs": 2},
            "AC-21 SULLAIR 185": {"hours": 78, "services": 0, "repairs": 1},
            "AC-23 DOOSAN P425": {"hours": 65, "services": 0, "repairs": 0},
            "AC-24 DOOSAN P425": {"hours": 72, "services": 0, "repairs": 0},
            "AC-04U ATLAS COPCO": {"hours": 82, "services": 0, "repairs": 0},
            
            # Bridge Equipment
            "BM-01 BLASTPRO": {"hours": 45, "services": 0, "repairs": 1},
            
            # Sweepers
            "BRO-02 BROCE": {"hours": 118, "services": 0, "repairs": 1},
            "BRO-03 BROCE": {"hours": 112, "services": 0, "repairs": 1},
            "BRO-08 LAY-MOR": {"hours": 125, "services": 0, "repairs": 1},
            
            # Personal Vehicles - Daily Use
            "#210003 FORD F150": {"hours": 186, "services": 0, "repairs": 0},
            "#210013 JEEP WRANGLER": {"hours": 142, "services": 0, "repairs": 0},
            "#210055 JEEP GLADIATOR": {"hours": 128, "services": 0, "repairs": 0},
            "#210073 TOYOTA 4RUNNER": {"hours": 135, "services": 0, "repairs": 0},
            "#410009 RAM 2500": {"hours": 148, "services": 0, "repairs": 0},
            
            # Trailers
            "14T-44 BIG TEX": {"hours": 85, "services": 0, "repairs": 0},
            
            # Specialty
            "Arrow Board WANCO": {"hours": 42, "services": 0, "repairs": 0},
            "BOAT-01": {"hours": 28, "services": 0, "repairs": 0}
        }
    
    def calculate_april_billing(self):
        """Calculate complete April 2025 billing using internal fixed rates"""
        billing_report = {
            "billing_period": "April 2025",
            "report_date": "2025-04-30",
            "total_monthly_fixed": 0.0,
            "total_hourly_charges": 0.0,
            "total_billing": 0.0,
            "equipment_details": [],
            "category_summaries": {},
            "division_totals": {
                "DIV1-INDIANA": 0.0,
                "DIV2-DFW": 0.0,
                "DIV3-WTX": 0.0,
                "DIV4-HOU": 0.0
            }
        }
        
        for asset_id, usage in self.april_usage.items():
            # Extract equipment model for rate lookup
            equipment_model = self._extract_equipment_model(asset_id)
            rates = self.equipment_rates.get(equipment_model, {
                "monthly_fixed": 500, "hourly_rate": 25.00, "category": "General"
            })
            
            # Calculate costs
            monthly_fixed = rates["monthly_fixed"]
            hourly_rate = rates["hourly_rate"]
            usage_hours = usage["hours"]
            hourly_charges = usage_hours * hourly_rate
            
            # Service and repair costs
            service_cost = usage["services"] * 150.00  # $150 per service
            repair_cost = usage["repairs"] * 225.00    # $225 per repair
            
            total_cost = monthly_fixed + hourly_charges + service_cost + repair_cost
            
            # Division assignment
            division = self._assign_division(asset_id)
            billing_report["division_totals"][division] += total_cost
            
            # Equipment detail
            equipment_detail = {
                "asset_id": asset_id,
                "equipment_model": equipment_model,
                "category": rates["category"],
                "monthly_fixed": monthly_fixed,
                "hourly_rate": hourly_rate,
                "usage_hours": usage_hours,
                "hourly_charges": hourly_charges,
                "service_cost": service_cost,
                "repair_cost": repair_cost,
                "total_cost": total_cost,
                "division": division,
                "utilization": round((usage_hours / 184) * 100, 1),  # April has 184 working hours
                "efficiency_rating": self._calculate_efficiency(usage_hours, usage["services"], usage["repairs"])
            }
            
            billing_report["equipment_details"].append(equipment_detail)
            billing_report["total_monthly_fixed"] += monthly_fixed
            billing_report["total_hourly_charges"] += hourly_charges
            billing_report["total_billing"] += total_cost
            
            # Category summaries
            category = rates["category"]
            if category not in billing_report["category_summaries"]:
                billing_report["category_summaries"][category] = {
                    "units": 0, "total_cost": 0.0, "total_hours": 0
                }
            billing_report["category_summaries"][category]["units"] += 1
            billing_report["category_summaries"][category]["total_cost"] += total_cost
            billing_report["category_summaries"][category]["total_hours"] += usage_hours
        
        # Add billing summary metrics
        billing_report["total_service_costs"] = sum([eq["service_cost"] for eq in billing_report["equipment_details"]])
        billing_report["total_repair_costs"] = sum([eq["repair_cost"] for eq in billing_report["equipment_details"]])
        billing_report["average_utilization"] = round(
            sum([eq["utilization"] for eq in billing_report["equipment_details"]]) / len(billing_report["equipment_details"]), 1
        )
        billing_report["total_equipment_count"] = len(billing_report["equipment_details"])
        
        return billing_report
    
    def _extract_equipment_model(self, asset_id):
        """Extract equipment model from asset ID"""
        model_mapping = {
            "BH-15": "CAT 420F", "BH-16": "CAT 420E", "BH-17": "CAT 430FIT",
            "BH-22": "CAT 420F2", "BH-23": "CAT 420F", "BH-24": "CAT 420E",
            "AC-05": "SULLAIR 185", "AC-12": "SULLAIR 185", "AC-21": "SULLAIR 185",
            "AC-23": "DOOSAN P425", "AC-24": "DOOSAN P425", "AC-04U": "ATLAS COPCO XAS 900",
            "BM-01": "BLASTPRO BPZ-20-360", "BRO-02": "BROCE RJ350", "BRO-03": "BROCE RJ350",
            "BRO-08": "LAY-MOR SM300", "#210003": "FORD F150", "#210013": "JEEP WRANGLER",
            "#210055": "JEEP GLADIATOR", "#210073": "TOYOTA 4 RUNNER", "#410009": "RAM 2500",
            "14T-44": "BIG TEX Flatbed", "Arrow Board": "WANCO Arrow Board", "BOAT-01": "Boat"
        }
        
        for prefix, model in model_mapping.items():
            if prefix in asset_id:
                return model
        return "General Equipment"
    
    def _assign_division(self, asset_id):
        """Assign equipment to division based on asset ID patterns"""
        if any(x in asset_id for x in ["BH-", "AC-", "BM-"]):
            return "DIV2-DFW"  # Heavy equipment primarily DFW
        elif "#210" in asset_id:
            return "DIV3-WTX"  # Personal vehicles West Texas
        elif "#410" in asset_id:
            return "DIV4-HOU"  # Houston region
        else:
            return "DIV1-INDIANA"  # Default
    
    def _calculate_efficiency(self, hours, services, repairs):
        """Calculate equipment efficiency rating"""
        if hours == 0:
            return "N/A"
        
        # Base efficiency on hours vs issues
        issue_ratio = (services + repairs) / (hours / 50)  # Issues per 50 hours
        
        if issue_ratio <= 0.1:
            return "Excellent"
        elif issue_ratio <= 0.3:
            return "Good"
        elif issue_ratio <= 0.6:
            return "Fair"
        else:
            return "Needs Attention"
    
    def generate_summary_report(self):
        """Generate executive summary for April billing"""
        billing_data = self.calculate_april_billing()
        
        summary = f"""
APRIL 2025 EQUIPMENT BILLING SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: 16GB Historical Data & Internal Monthly Fixed Rates

FINANCIAL SUMMARY:
• Total Monthly Fixed Costs: ${billing_data['total_monthly_fixed']:,.2f}
• Total Hourly Charges: ${billing_data['total_hourly_charges']:,.2f}
• Service Costs: ${billing_data['total_service_costs']:,.2f}
• Repair Costs: ${billing_data['total_repair_costs']:,.2f}
• TOTAL APRIL BILLING: ${billing_data['total_billing']:,.2f}

OPERATIONAL METRICS:
• Total Equipment Units: {billing_data['total_equipment_count']}
• Average Utilization: {billing_data['average_utilization']}%
• Services Performed: {sum([eq['usage_hours'] for eq in billing_data['equipment_details'] if 'BH' in eq['asset_id']])} total hours
• Repair Incidents: {len([eq for eq in billing_data['equipment_details'] if eq['repair_cost'] > 0])}

DIVISION BREAKDOWN:
• DIV1-INDIANA: ${billing_data['division_totals']['DIV1-INDIANA']:,.2f}
• DIV2-DFW: ${billing_data['division_totals']['DIV2-DFW']:,.2f}
• DIV3-WTX: ${billing_data['division_totals']['DIV3-WTX']:,.2f}
• DIV4-HOU: ${billing_data['division_totals']['DIV4-HOU']:,.2f}

TOP EQUIPMENT CATEGORIES:
"""
        
        # Add category breakdown
        for category, data in billing_data['category_summaries'].items():
            summary += f"• {category}: {data['units']} units, ${data['total_cost']:,.2f}, {data['total_hours']} hours\n"
        
        return summary

# Generate April 2025 billing report
if __name__ == "__main__":
    processor = AprilBillingProcessor()
    april_report = processor.calculate_april_billing()
    summary = processor.generate_summary_report()
    
    print(summary)
    print("\nDetailed billing data available in april_report variable")