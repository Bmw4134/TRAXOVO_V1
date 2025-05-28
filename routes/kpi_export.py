from flask import Blueprint, jsonify, send_file
import pandas as pd
from datetime import datetime
import io

kpi_bp = Blueprint('kpi', __name__)

@kpi_bp.route('/export/kpi-digest/<division>')
def export_kpi_digest(division):
    """Export KPI digest for specific division"""
    
    # Generate KPI data for the division
    kpi_data = {
        'DFW': {'on_time': 94.2, 'projects': 4, 'drivers': 235},
        'WTX': {'on_time': 91.8, 'projects': 2, 'drivers': 30}, 
        'HOU': {'on_time': 96.1, 'projects': 2, 'drivers': 77}
    }
    
    return jsonify({
        'division': division,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'metrics': kpi_data.get(division, {})
    })