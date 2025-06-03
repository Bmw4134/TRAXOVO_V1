#!/usr/bin/env python3
"""Simple server for testing Contextual Productivity Nudges"""

from flask import Flask, render_template, jsonify, request
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "traxovo-test-key"

@app.route('/')
def index():
    return render_template('quantum_asi_dashboard.html')

@app.route('/quantum_asi_dashboard')
def quantum_asi_dashboard():
    return render_template('quantum_asi_dashboard.html')

@app.route('/api/contextual-nudges')
def api_contextual_nudges():
    # Sample productivity nudges for testing
    nudges = [
        {
            'id': 'nudge_1',
            'title': 'Asset Utilization Optimization',
            'description': 'Fort Worth fleet showing 23% idle time this morning. Consider redistributing CAT 320 excavator from Site A to maximize productivity.',
            'priority': 4,
            'category': 'efficiency',
            'estimated_impact': 850.00
        },
        {
            'id': 'nudge_2', 
            'title': 'Maintenance Window Opportunity',
            'description': 'Equipment downtime predicted between 2-4 PM today. Schedule preventive maintenance for maximum efficiency.',
            'priority': 5,
            'category': 'maintenance',
            'estimated_impact': 1200.00
        },
        {
            'id': 'nudge_3',
            'title': 'Route Optimization Savings',
            'description': 'ASI analysis indicates route optimization could save $340 in fuel costs today.',
            'priority': 4,
            'category': 'cost_savings',
            'estimated_impact': 340.00
        }
    ]
    
    metrics = {
        'productivity_score': 94.8,
        'active_nudges_count': len(nudges),
        'total_potential_savings': sum(n['estimated_impact'] for n in nudges)
    }
    
    return jsonify({
        'status': 'success',
        'nudges': nudges,
        'metrics': metrics,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/execute-nudge-action', methods=['POST'])
def api_execute_nudge_action():
    data = request.get_json() or {}
    return jsonify({
        'status': 'success',
        'message': f"Nudge action executed successfully",
        'nudge_id': data.get('nudge_id'),
        'executed_at': datetime.now().isoformat()
    })

@app.route('/api/execute-kaizen-sweep', methods=['POST'])
def api_execute_kaizen_sweep():
    return jsonify({
        'status': 'success',
        'sweep_results': {
            'overall_optimization_score': 97.3,
            'optimization_level': 'QUANTUM EXCELLENCE ACHIEVED'
        },
        'message': 'Kaizen Quantum Sweep completed successfully'
    })

if __name__ == '__main__':
    print("Starting TRAXOVO Contextual Productivity Nudges Test Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)