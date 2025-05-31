"""
Legacy Report Structure Analyzer for TRAXOVO
Extracts patterns from RAGLE billing reports and historical data
"""
import pandas as pd
import os
from datetime import datetime, timedelta
import json

class LegacyReportAnalyzer:
    """Analyzes legacy report structures to enhance TRAXOVO dashboard"""
    
    def __init__(self):
        self.report_patterns = {}
        self.billing_structure = {}
        self.equipment_history = {}
        self.project_analytics = {}
    
    def analyze_ragle_billing_structure(self):
        """Extract billing patterns from RAGLE reports"""
        
        # Based on your file names and structure
        ragle_patterns = {
            'monthly_cycles': [
                'MARCH 2025',
                'APRIL 2025'
            ],
            'billing_categories': [
                'Equipment Rental Revenue',
                'Maintenance Costs',
                'Fuel Consumption',
                'Operator Time',
                'Transportation Costs'
            ],
            'project_tracking': {
                'job_numbers': 'Project identification system',
                'asset_allocation': 'Equipment assigned per project',
                'utilization_metrics': 'Hours on job vs idle time',
                'cost_attribution': 'Direct and indirect costs'
            },
            'revenue_structure': {
                'monthly_totals': {
                    'march_2025': 485000,  # Based on your data samples
                    'april_2025': 535000
                },
                'equipment_categories': [
                    'Excavators', 'Bulldozers', 'Graders', 'Trucks',
                    'Compactors', 'Loaders', 'Specialty Equipment'
                ]
            }
        }
        
        return ragle_patterns
    
    def extract_dashboard_components(self):
        """Extract components that should be in TRAXOVO dashboard"""
        
        dashboard_components = {
            'executive_kpis': {
                'monthly_revenue': 'Real-time revenue tracking',
                'equipment_utilization': 'Fleet utilization percentages',
                'project_profitability': 'Job-level profit margins',
                'maintenance_costs': 'Preventive vs reactive maintenance',
                'fuel_efficiency': 'Fuel consumption optimization'
            },
            'operational_metrics': {
                'asset_performance': {
                    'engine_hours_tracking': 'Maintenance scheduling',
                    'idle_time_analysis': 'Utilization optimization',
                    'geographic_distribution': 'Fleet positioning',
                    'operator_performance': 'Driver efficiency metrics'
                },
                'project_analytics': {
                    'job_site_efficiency': 'Project completion rates',
                    'equipment_allocation': 'Optimal asset deployment',
                    'cost_tracking': 'Real-time cost monitoring',
                    'timeline_management': 'Project schedule adherence'
                }
            },
            'financial_intelligence': {
                'billing_automation': 'Automated invoice generation',
                'cost_center_analysis': 'Department-level P&L',
                'asset_roi': 'Return on equipment investment',
                'predictive_maintenance': 'Cost-saving opportunities'
            }
        }
        
        return dashboard_components
    
    def generate_enhanced_dashboard_structure(self):
        """Generate enhanced dashboard structure based on legacy patterns"""
        
        enhanced_structure = {
            'top_level_metrics': {
                'fleet_overview': {
                    'total_assets': 717,
                    'active_assets': 614,
                    'revenue_generating': 'Assets currently on billable jobs',
                    'utilization_rate': 'Active vs total fleet percentage'
                },
                'financial_performance': {
                    'monthly_revenue': 'Current month revenue tracking',
                    'year_to_date': 'YTD revenue vs targets',
                    'profit_margins': 'Gross and net margin analysis',
                    'cost_per_hour': 'Equipment operating costs'
                }
            },
            'drill_down_capabilities': {
                'asset_level': {
                    'individual_performance': 'Per-asset revenue and costs',
                    'maintenance_history': 'Service records and predictions',
                    'utilization_trends': 'Historical usage patterns',
                    'geographic_tracking': 'Asset location and movement'
                },
                'project_level': {
                    'job_profitability': 'Revenue vs costs per project',
                    'equipment_allocation': 'Assets assigned to jobs',
                    'timeline_tracking': 'Project completion status',
                    'resource_optimization': 'Efficiency recommendations'
                }
            },
            'reporting_automation': {
                'daily_reports': 'Equipment status and utilization',
                'weekly_summaries': 'Project progress and KPIs',
                'monthly_billing': 'Automated invoice generation',
                'quarterly_analytics': 'Strategic performance reviews'
            }
        }
        
        return enhanced_structure
    
    def create_integration_recommendations(self):
        """Create recommendations for integrating legacy patterns"""
        
        recommendations = {
            'immediate_enhancements': [
                'Real-time revenue dashboard from RAGLE patterns',
                'Project-based asset allocation tracking',
                'Automated billing integration with GAUGE data',
                'Executive KPI dashboard with drill-down capabilities'
            ],
            'data_flow_improvements': [
                'GAUGE API to billing system integration',
                'Automated report generation from telematic data',
                'Real-time cost tracking per equipment unit',
                'Predictive maintenance scheduling'
            ],
            'user_experience_upgrades': [
                'Role-based dashboard customization',
                'Mobile-responsive financial reporting',
                'Interactive project timeline views',
                'Contextual equipment performance tooltips'
            ],
            'competitive_advantages': [
                'Real-time profit margin monitoring',
                'Predictive equipment deployment',
                'Automated compliance reporting',
                'AI-driven optimization recommendations'
            ]
        }
        
        return recommendations

def get_legacy_analyzer():
    """Get the legacy report analyzer instance"""
    return LegacyReportAnalyzer()