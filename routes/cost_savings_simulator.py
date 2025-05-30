"""
Dynamic Cost-Savings Simulation Tool
Real-time analysis using authentic Foundation billing data
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request

cost_simulator_bp = Blueprint('cost_simulator', __name__)

def load_authentic_billing_data():
    """Load authentic Foundation billing data for analysis"""
    billing_files = {
        'april_2025': 'attached_assets/RAGLE EQ BILLINGS - APRIL 2025 (JG REVIEWED 5.12).xlsm',
        'march_2025': 'attached_assets/RAGLE EQ BILLINGS - MARCH 2025 (TO REVIEW 04.03.25).xlsm'
    }
    
    equipment_costs = {}
    monthly_totals = {}
    
    for month, file_path in billing_files.items():
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                month_total = 0
                
                for _, row in df.iterrows():
                    if pd.notna(row.iloc[0]):
                        equipment_id = str(row.iloc[0]).strip()
                        
                        # Extract cost data from billing structure
                        for col_idx in range(1, min(len(row), 10)):
                            try:
                                if pd.notna(row.iloc[col_idx]):
                                    val = str(row.iloc[col_idx]).replace('$', '').replace(',', '')
                                    if val.replace('.', '').replace('-', '').isdigit():
                                        amount = float(val)
                                        if amount > 0:
                                            month_total += amount
                                            
                                            if equipment_id not in equipment_costs:
                                                equipment_costs[equipment_id] = []
                                            equipment_costs[equipment_id].append({
                                                'month': month,
                                                'amount': amount,
                                                'daily_rate': amount / 30  # Estimate daily usage
                                            })
                                            break
                            except:
                                continue
                
                monthly_totals[month] = month_total
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    
    return equipment_costs, monthly_totals

def simulate_rental_vs_ownership(equipment_data, simulation_params):
    """Simulate cost scenarios for rental vs ownership"""
    
    # Rental market rates (industry standard markup)
    rental_multipliers = {
        'excavator': 1.45,    # 45% markup
        'truck': 1.35,        # 35% markup  
        'dozer': 1.50,        # 50% markup
        'crane': 1.60,        # 60% markup
        'grader': 1.40,       # 40% markup
        'loader': 1.38        # 38% markup
    }
    
    scenarios = {}
    
    for equipment_id, cost_history in equipment_data.items():
        if not cost_history:
            continue
            
        # Calculate current internal costs
        avg_monthly_cost = sum(item['amount'] for item in cost_history) / len(cost_history)
        annual_internal_cost = avg_monthly_cost * 12
        
        # Determine equipment type and rental rate
        equipment_type = 'truck'  # Default
        for eq_type in rental_multipliers.keys():
            if eq_type.upper() in equipment_id.upper():
                equipment_type = eq_type
                break
        
        rental_multiplier = rental_multipliers[equipment_type]
        annual_rental_cost = annual_internal_cost * rental_multiplier
        
        # Calculate savings scenarios
        annual_savings = annual_rental_cost - annual_internal_cost
        three_year_savings = annual_savings * 3
        five_year_savings = annual_savings * 5
        
        # Factor in depreciation and maintenance
        depreciation_factor = 0.15  # 15% annual depreciation
        maintenance_factor = 0.08   # 8% annual maintenance
        
        ownership_total_cost = annual_internal_cost * (1 + depreciation_factor + maintenance_factor)
        net_annual_savings = annual_rental_cost - ownership_total_cost
        
        scenarios[equipment_id] = {
            'equipment_type': equipment_type,
            'annual_internal_cost': annual_internal_cost,
            'annual_rental_cost': annual_rental_cost,
            'annual_savings': annual_savings,
            'net_annual_savings': net_annual_savings,
            'three_year_savings': three_year_savings,
            'five_year_savings': five_year_savings,
            'rental_multiplier': rental_multiplier,
            'break_even_months': (annual_rental_cost - annual_internal_cost) / (avg_monthly_cost * 0.2) if avg_monthly_cost > 0 else 0,
            'cost_history': cost_history
        }
    
    return scenarios

def calculate_fleet_optimization(scenarios, optimization_type='maximize_savings'):
    """Calculate optimal fleet configuration"""
    
    optimization_results = {
        'current_configuration': {
            'total_annual_cost': sum(s['annual_internal_cost'] for s in scenarios.values()),
            'equipment_count': len(scenarios)
        },
        'optimized_configuration': {},
        'recommendations': []
    }
    
    if optimization_type == 'maximize_savings':
        # Prioritize equipment with highest rental savings
        sorted_equipment = sorted(scenarios.items(), key=lambda x: x[1]['annual_savings'], reverse=True)
        
        total_optimized_cost = 0
        total_current_cost = 0
        
        for equipment_id, data in sorted_equipment:
            total_current_cost += data['annual_internal_cost']
            
            # Decision logic: keep internal if savings > 20%
            if data['annual_savings'] > data['annual_internal_cost'] * 0.20:
                total_optimized_cost += data['annual_internal_cost']
                optimization_results['recommendations'].append({
                    'equipment': equipment_id,
                    'recommendation': 'keep_internal',
                    'reason': f"High savings: ${data['annual_savings']:,.0f} annually",
                    'savings': data['annual_savings']
                })
            else:
                total_optimized_cost += data['annual_rental_cost']
                optimization_results['recommendations'].append({
                    'equipment': equipment_id,
                    'recommendation': 'consider_rental',
                    'reason': f"Low savings: ${data['annual_savings']:,.0f} annually",
                    'savings': -data['annual_savings']
                })
        
        optimization_results['optimized_configuration'] = {
            'total_annual_cost': total_optimized_cost,
            'total_savings': total_current_cost - total_optimized_cost if total_optimized_cost < total_current_cost else 0
        }
    
    return optimization_results

@cost_simulator_bp.route('/cost-simulator')
def cost_simulator_dashboard():
    """Dynamic cost-savings simulation dashboard"""
    equipment_data, monthly_totals = load_authentic_billing_data()
    
    simulation_params = {
        'time_horizon': 3,  # years
        'rental_market': 'competitive',
        'maintenance_factor': 0.08
    }
    
    scenarios = simulate_rental_vs_ownership(equipment_data, simulation_params)
    optimization = calculate_fleet_optimization(scenarios)
    
    # Calculate summary metrics
    total_annual_savings = sum(s['annual_savings'] for s in scenarios.values())
    total_equipment = len(scenarios)
    avg_savings_per_unit = total_annual_savings / total_equipment if total_equipment > 0 else 0
    
    context = {
        'page_title': 'Cost-Savings Simulation',
        'scenarios': scenarios,
        'optimization': optimization,
        'summary_metrics': {
            'total_annual_savings': total_annual_savings,
            'total_equipment': total_equipment,
            'avg_savings_per_unit': avg_savings_per_unit,
            'data_source': 'RAGLE EQ BILLINGS March/April 2025'
        },
        'monthly_totals': monthly_totals,
        'simulation_date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    
    return render_template('cost_simulator_dashboard.html', **context)

@cost_simulator_bp.route('/api/simulate-scenario', methods=['POST'])
def simulate_scenario():
    """API endpoint for dynamic scenario simulation"""
    params = request.get_json()
    
    equipment_data, _ = load_authentic_billing_data()
    scenarios = simulate_rental_vs_ownership(equipment_data, params)
    optimization = calculate_fleet_optimization(scenarios, params.get('optimization_type', 'maximize_savings'))
    
    return jsonify({
        'scenarios': scenarios,
        'optimization': optimization,
        'timestamp': datetime.now().isoformat()
    })

@cost_simulator_bp.route('/api/equipment-analysis/<equipment_id>')
def equipment_analysis(equipment_id):
    """Detailed analysis for specific equipment"""
    equipment_data, _ = load_authentic_billing_data()
    
    if equipment_id in equipment_data:
        simulation_params = {'time_horizon': 5}
        scenarios = simulate_rental_vs_ownership({equipment_id: equipment_data[equipment_id]}, simulation_params)
        
        return jsonify({
            'equipment_id': equipment_id,
            'analysis': scenarios.get(equipment_id, {}),
            'recommendation': 'keep_internal' if scenarios.get(equipment_id, {}).get('annual_savings', 0) > 0 else 'consider_rental'
        })
    
    return jsonify({'error': 'Equipment not found'}), 404