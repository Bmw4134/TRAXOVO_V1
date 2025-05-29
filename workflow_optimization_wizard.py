"""
Personalized Workflow Optimization Wizard
Creates customized workflows based on authentic Foundation operational data
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from excel_data_processor import get_excel_processor
from enhanced_foundation_processor import get_enhanced_foundation_processor

class WorkflowOptimizationWizard:
    
    def __init__(self):
        self.excel_processor = get_excel_processor()
        self.foundation_processor = get_enhanced_foundation_processor()
        
    def analyze_operational_patterns(self) -> Dict:
        """Analyze authentic data to identify optimization opportunities"""
        
        try:
            # Get comprehensive asset mapping from authentic data
            asset_mapping = self.excel_processor.create_comprehensive_asset_mapping()
            foundation_data = self.foundation_processor.get_comprehensive_revenue_summary()
            
            patterns = {
                'equipment_utilization': self._analyze_equipment_utilization(asset_mapping),
                'driver_efficiency': self._analyze_driver_patterns(asset_mapping),
                'maintenance_optimization': self._analyze_maintenance_patterns(asset_mapping),
                'revenue_optimization': self._analyze_revenue_patterns(foundation_data),
                'cost_efficiency': self._analyze_cost_patterns(asset_mapping, foundation_data)
            }
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing operational patterns: {e}")
            return self._get_fallback_analysis()
    
    def _analyze_equipment_utilization(self, asset_mapping: Dict) -> Dict:
        """Analyze equipment utilization from authentic usage data"""
        
        utilization_data = asset_mapping.get('utilization_patterns', {})
        equipment_costs = asset_mapping.get('equipment_costs', {})
        
        analysis = {
            'high_utilization_assets': [],
            'underutilized_assets': [],
            'optimization_opportunities': [],
            'recommendations': []
        }
        
        # Analyze utilization patterns
        for eq_id, utilization_history in utilization_data.items():
            if utilization_history and len(utilization_history) > 0:
                avg_utilization = sum(utilization_history) / len(utilization_history)
                
                if avg_utilization > 80:
                    analysis['high_utilization_assets'].append({
                        'equipment_id': eq_id,
                        'utilization': avg_utilization,
                        'recommendation': 'Consider additional units or schedule optimization'
                    })
                elif avg_utilization < 30:
                    analysis['underutilized_assets'].append({
                        'equipment_id': eq_id,
                        'utilization': avg_utilization,
                        'recommendation': 'Optimize scheduling or consider reassignment'
                    })
        
        # Generate optimization recommendations
        if len(analysis['underutilized_assets']) > 0:
            analysis['recommendations'].append({
                'priority': 'High',
                'category': 'Equipment Optimization',
                'action': 'Redistribute underutilized equipment to high-demand projects',
                'potential_savings': f"${len(analysis['underutilized_assets']) * 5000:,}/month"
            })
        
        return analysis
    
    def _analyze_driver_patterns(self, asset_mapping: Dict) -> Dict:
        """Analyze driver efficiency patterns from authentic assignment data"""
        
        driver_assignments = asset_mapping.get('asset_driver_mapping', {})
        work_order_frequency = asset_mapping.get('work_order_frequency', {})
        
        analysis = {
            'driver_workload': {},
            'efficiency_metrics': {},
            'recommendations': []
        }
        
        # Analyze driver workloads
        driver_counts = {}
        for equipment, driver in driver_assignments.items():
            if driver not in driver_counts:
                driver_counts[driver] = 0
            driver_counts[driver] += 1
            
            # Include maintenance frequency as efficiency indicator
            maintenance_freq = work_order_frequency.get(equipment, 0)
            if driver not in analysis['efficiency_metrics']:
                analysis['efficiency_metrics'][driver] = {'equipment_count': 0, 'total_maintenance': 0}
            
            analysis['efficiency_metrics'][driver]['equipment_count'] += 1
            analysis['efficiency_metrics'][driver]['total_maintenance'] += maintenance_freq
        
        # Generate driver optimization recommendations
        overloaded_drivers = [driver for driver, count in driver_counts.items() if count > 8]
        underloaded_drivers = [driver for driver, count in driver_counts.items() if count < 3]
        
        if overloaded_drivers:
            analysis['recommendations'].append({
                'priority': 'Medium',
                'category': 'Workload Balancing',
                'action': f'Redistribute equipment from overloaded drivers: {", ".join(overloaded_drivers[:3])}',
                'potential_benefit': 'Improved efficiency and reduced operator fatigue'
            })
        
        analysis['driver_workload'] = driver_counts
        return analysis
    
    def _analyze_maintenance_patterns(self, asset_mapping: Dict) -> Dict:
        """Analyze maintenance patterns for predictive optimization"""
        
        maintenance_history = asset_mapping.get('maintenance_history', {})
        work_order_frequency = asset_mapping.get('work_order_frequency', {})
        
        analysis = {
            'high_maintenance_equipment': [],
            'predictive_opportunities': [],
            'cost_optimization': [],
            'recommendations': []
        }
        
        # Identify high maintenance equipment
        for eq_id, frequency in work_order_frequency.items():
            if frequency > 10:  # High maintenance frequency
                cost = maintenance_history.get(eq_id, 0)
                analysis['high_maintenance_equipment'].append({
                    'equipment_id': eq_id,
                    'frequency': frequency,
                    'total_cost': cost,
                    'avg_cost_per_order': cost / frequency if frequency > 0 else 0
                })
        
        # Generate predictive maintenance recommendations
        if analysis['high_maintenance_equipment']:
            analysis['recommendations'].append({
                'priority': 'High',
                'category': 'Predictive Maintenance',
                'action': 'Implement preventive maintenance schedule for high-frequency equipment',
                'potential_savings': f"${sum([eq['total_cost'] for eq in analysis['high_maintenance_equipment']]) * 0.3:,.0f}/year"
            })
        
        return analysis
    
    def _analyze_revenue_patterns(self, foundation_data: Dict) -> Dict:
        """Analyze revenue patterns from Foundation accounting data"""
        
        monthly_breakdown = foundation_data.get('monthly_breakdown', {})
        
        analysis = {
            'revenue_trends': {},
            'optimization_opportunities': [],
            'recommendations': []
        }
        
        # Analyze revenue by company and month
        for company, months in monthly_breakdown.items():
            company_revenue = []
            for month, data in months.items():
                revenue = data.get('total_revenue', 0)
                company_revenue.append(revenue)
            
            if company_revenue:
                avg_revenue = sum(company_revenue) / len(company_revenue)
                analysis['revenue_trends'][company] = {
                    'average_monthly': avg_revenue,
                    'total_months': len(company_revenue),
                    'trend': 'stable' if max(company_revenue) - min(company_revenue) < avg_revenue * 0.2 else 'variable'
                }
        
        # Generate revenue optimization recommendations
        total_revenue = foundation_data.get('total_revenue', 0)
        if total_revenue > 0:
            analysis['recommendations'].append({
                'priority': 'Medium',
                'category': 'Revenue Optimization',
                'action': 'Analyze high-performing job categories for expansion opportunities',
                'potential_increase': f"${total_revenue * 0.15:,.0f}/year (15% improvement target)"
            })
        
        return analysis
    
    def _analyze_cost_patterns(self, asset_mapping: Dict, foundation_data: Dict) -> Dict:
        """Analyze cost efficiency from combined data sources"""
        
        equipment_costs = asset_mapping.get('equipment_costs', {})
        maintenance_costs = asset_mapping.get('maintenance_history', {})
        total_revenue = foundation_data.get('total_revenue', 0)
        
        analysis = {
            'cost_efficiency_ratios': {},
            'optimization_targets': [],
            'recommendations': []
        }
        
        # Calculate cost efficiency metrics
        total_equipment_costs = sum(equipment_costs.values())
        total_maintenance_costs = sum(maintenance_costs.values())
        total_costs = total_equipment_costs + total_maintenance_costs
        
        if total_revenue > 0 and total_costs > 0:
            profit_margin = (total_revenue - total_costs) / total_revenue
            analysis['cost_efficiency_ratios'] = {
                'profit_margin': profit_margin,
                'maintenance_to_revenue_ratio': total_maintenance_costs / total_revenue,
                'equipment_to_revenue_ratio': total_equipment_costs / total_revenue
            }
            
            # Generate cost optimization recommendations
            if profit_margin < 0.25:  # Below 25% margin
                analysis['recommendations'].append({
                    'priority': 'High',
                    'category': 'Cost Optimization',
                    'action': 'Review pricing strategy and operational efficiency',
                    'target_improvement': f"Increase profit margin to 25% (+${total_revenue * 0.1:,.0f})"
                })
        
        return analysis
    
    def _get_fallback_analysis(self) -> Dict:
        """Provide basic analysis when data processing fails"""
        return {
            'equipment_utilization': {'recommendations': [{'priority': 'Medium', 'category': 'Data Collection', 'action': 'Enhance data collection for better optimization analysis'}]},
            'driver_efficiency': {'recommendations': []},
            'maintenance_optimization': {'recommendations': []},
            'revenue_optimization': {'recommendations': []},
            'cost_efficiency': {'recommendations': []}
        }
    
    def generate_personalized_workflows(self) -> Dict:
        """Generate personalized workflow recommendations based on operational analysis"""
        
        patterns = self.analyze_operational_patterns()
        
        workflows = {
            'daily_optimization': self._create_daily_workflow(patterns),
            'weekly_planning': self._create_weekly_workflow(patterns),
            'monthly_review': self._create_monthly_workflow(patterns),
            'quarterly_strategy': self._create_quarterly_workflow(patterns)
        }
        
        return workflows
    
    def _create_daily_workflow(self, patterns: Dict) -> Dict:
        """Create daily optimization workflow"""
        
        daily_tasks = []
        
        # Equipment utilization checks
        equipment_analysis = patterns.get('equipment_utilization', {})
        if equipment_analysis.get('underutilized_assets'):
            daily_tasks.append({
                'time': '7:00 AM',
                'task': 'Review underutilized equipment assignments',
                'action': 'Check if idle equipment can be reassigned to active projects',
                'priority': 'High'
            })
        
        # Driver efficiency monitoring
        driver_analysis = patterns.get('driver_efficiency', {})
        if driver_analysis.get('recommendations'):
            daily_tasks.append({
                'time': '8:30 AM',
                'task': 'Monitor driver workload distribution',
                'action': 'Ensure balanced equipment assignments across team',
                'priority': 'Medium'
            })
        
        # Maintenance alerts
        maintenance_analysis = patterns.get('maintenance_optimization', {})
        if maintenance_analysis.get('high_maintenance_equipment'):
            daily_tasks.append({
                'time': '9:00 AM',
                'task': 'Check high-maintenance equipment status',
                'action': 'Verify operational status and schedule preventive maintenance',
                'priority': 'High'
            })
        
        return {
            'name': 'Daily Operations Optimization',
            'description': 'Personalized daily workflow based on your equipment and operational patterns',
            'tasks': daily_tasks,
            'estimated_time': f'{len(daily_tasks) * 15} minutes'
        }
    
    def _create_weekly_workflow(self, patterns: Dict) -> Dict:
        """Create weekly planning workflow"""
        
        weekly_tasks = [
            {
                'day': 'Monday',
                'task': 'Weekly utilization analysis',
                'action': 'Review previous week equipment utilization and plan optimizations',
                'data_source': 'Foundation usage reports'
            },
            {
                'day': 'Wednesday',
                'task': 'Driver performance review',
                'action': 'Analyze driver efficiency metrics and workload balance',
                'data_source': 'Asset assignment data'
            },
            {
                'day': 'Friday',
                'task': 'Maintenance planning',
                'action': 'Schedule upcoming maintenance based on usage patterns',
                'data_source': 'Work order history'
            }
        ]
        
        return {
            'name': 'Weekly Strategic Planning',
            'description': 'Weekly workflow optimized for your operational patterns',
            'tasks': weekly_tasks,
            'focus_areas': ['Equipment optimization', 'Resource planning', 'Preventive maintenance']
        }
    
    def _create_monthly_workflow(self, patterns: Dict) -> Dict:
        """Create monthly review workflow"""
        
        revenue_analysis = patterns.get('revenue_optimization', {})
        cost_analysis = patterns.get('cost_efficiency', {})
        
        monthly_tasks = [
            {
                'week': 'Week 1',
                'task': 'Monthly revenue analysis',
                'action': 'Compare current month performance against Foundation reports',
                'metrics': ['Revenue trends', 'Job profitability', 'Equipment ROI']
            },
            {
                'week': 'Week 2',
                'task': 'Cost efficiency review',
                'action': 'Analyze operational costs and identify optimization opportunities',
                'metrics': ['Maintenance costs', 'Utilization rates', 'Profit margins']
            },
            {
                'week': 'Week 3',
                'task': 'Strategic planning',
                'action': 'Plan next month operations based on performance data',
                'metrics': ['Resource allocation', 'Equipment deployment', 'Driver assignments']
            }
        ]
        
        return {
            'name': 'Monthly Performance Review',
            'description': 'Comprehensive monthly workflow based on Foundation data analysis',
            'tasks': monthly_tasks,
            'success_metrics': ['15% efficiency improvement', 'Reduced maintenance costs', 'Optimized resource allocation']
        }
    
    def _create_quarterly_workflow(self, patterns: Dict) -> Dict:
        """Create quarterly strategy workflow"""
        
        quarterly_objectives = []
        
        # Equipment optimization objectives
        equipment_analysis = patterns.get('equipment_utilization', {})
        if equipment_analysis.get('recommendations'):
            quarterly_objectives.append({
                'category': 'Equipment Optimization',
                'objective': 'Improve equipment utilization by 20%',
                'actions': ['Redistribute underutilized assets', 'Optimize scheduling', 'Consider fleet expansion']
            })
        
        # Revenue growth objectives
        revenue_analysis = patterns.get('revenue_optimization', {})
        if revenue_analysis.get('recommendations'):
            quarterly_objectives.append({
                'category': 'Revenue Growth',
                'objective': 'Increase quarterly revenue by 15%',
                'actions': ['Expand high-performing job categories', 'Optimize pricing strategy', 'Improve operational efficiency']
            })
        
        return {
            'name': 'Quarterly Strategic Review',
            'description': 'Strategic quarterly planning based on comprehensive operational analysis',
            'objectives': quarterly_objectives,
            'review_cycle': '90 days',
            'data_sources': ['Foundation accounting reports', 'Equipment usage data', 'Work order history']
        }

# Global instance
_workflow_wizard = None

def get_workflow_wizard():
    """Get the workflow optimization wizard instance"""
    global _workflow_wizard
    if _workflow_wizard is None:
        _workflow_wizard = WorkflowOptimizationWizard()
    return _workflow_wizard