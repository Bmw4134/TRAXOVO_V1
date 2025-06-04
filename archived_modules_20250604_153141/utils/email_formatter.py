"""
TRAXORA Email Formatter Module
Generates professional HTML email reports for driver attendance distribution
Compatible with division and zone filters
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def format_attendance_email(attendance_data, filters=None, week_range="Current Week"):
    """
    Generate HTML email string for driver attendance reports
    
    Args:
        attendance_data: Driver attendance data with violations and metrics
        filters: Dictionary containing division, zone, and other filter settings
        week_range: Date range for the report
    
    Returns:
        str: HTML formatted email ready for clipboard copy
    """
    
    # Extract filter information
    division_filter = filters.get('division', 'All Divisions') if filters else 'All Divisions'
    zone_filter = filters.get('zone', 'All Zones') if filters else 'All Zones'
    
    # Generate report timestamp
    report_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # Calculate metrics
    total_drivers = len(attendance_data.get('drivers', []))
    violations = attendance_data.get('violations', [])
    violation_count = len(violations)
    compliance_rate = max(0, 100 - (violation_count / max(total_drivers, 1) * 100))
    
    # Create HTML email
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 25px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .summary-stats {{
            display: flex;
            justify-content: space-around;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border: 1px solid #e9ecef;
        }}
        .stat-item {{
            text-align: center;
            flex: 1;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 0;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6c757d;
            margin: 5px 0 0 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .filter-info {{
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 0 8px 8px 0;
        }}
        .filter-info h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 16px;
        }}
        .filter-tags {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .filter-tag {{
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 500;
        }}
        .violations-section {{
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 25px;
        }}
        .section-header {{
            background: #495057;
            color: white;
            padding: 15px 20px;
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }}
        .violation-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .violation-table th {{
            background: #f8f9fa;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 1px solid #dee2e6;
        }}
        .violation-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }}
        .violation-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .violation-type {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .late-start {{
            background: #fff3cd;
            color: #856404;
        }}
        .early-end {{
            background: #f8d7da;
            color: #721c24;
        }}
        .not-on-job {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        .compliance-section {{
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 25px;
        }}
        .compliance-rate {{
            font-size: 48px;
            font-weight: bold;
            color: #155724;
            margin: 0;
        }}
        .compliance-label {{
            font-size: 16px;
            color: #155724;
            margin: 5px 0 0 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            color: #6c757d;
            font-size: 14px;
        }}
        .footer strong {{
            color: #495057;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚛 TRAXOVO Driver Attendance Report</h1>
        <p>Weekly Compliance Summary • {week_range}</p>
    </div>
    
    <div class="summary-stats">
        <div class="stat-item">
            <div class="stat-number">{total_drivers}</div>
            <div class="stat-label">Total Drivers</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{violation_count}</div>
            <div class="stat-label">Violations</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{compliance_rate:.1f}%</div>
            <div class="stat-label">Compliance</div>
        </div>
    </div>
    
    <div class="filter-info">
        <h3>📋 Report Filters Applied</h3>
        <div class="filter-tags">
            <span class="filter-tag">📍 {division_filter}</span>
            <span class="filter-tag">🏗️ {zone_filter}</span>
            <span class="filter-tag">📅 {week_range}</span>
        </div>
    </div>
    
    <div class="compliance-section">
        <div class="compliance-rate">{compliance_rate:.1f}%</div>
        <div class="compliance-label">Overall Compliance Rate</div>
    </div>
"""
    
    # Add violations table if there are violations
    if violations:
        html_content += """
    <div class="violations-section">
        <h2 class="section-header">⚠️ Attendance Violations Requiring Action</h2>
        <table class="violation-table">
            <thead>
                <tr>
                    <th>Employee</th>
                    <th>Date</th>
                    <th>Violation Type</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add violation rows (limit to first 20 for email readability)
        for violation in violations[:20]:
            employee_name = violation.get('employee_name', 'Unknown')
            date = violation.get('date', 'N/A')
            violation_type = violation.get('violation_type', 'Unknown')
            details = violation.get('details', 'No details available')
            
            # Style violation type
            type_class = {
                'Late Start': 'late-start',
                'Early End': 'early-end',
                'Not on Job': 'not-on-job'
            }.get(violation_type, 'late-start')
            
            html_content += f"""
                <tr>
                    <td><strong>{employee_name}</strong></td>
                    <td>{date}</td>
                    <td><span class="violation-type {type_class}">{violation_type}</span></td>
                    <td>{details}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
    </div>
"""
    else:
        html_content += """
    <div class="violations-section">
        <h2 class="section-header">✅ No Violations Found</h2>
        <div style="padding: 20px; text-align: center; color: #155724;">
            <strong>Excellent! All drivers maintained perfect attendance compliance during this period.</strong>
        </div>
    </div>
"""
    
    # Add footer
    html_content += f"""
    <div class="footer">
        <strong>TRAXOVO Fleet Management System</strong><br>
        Report generated on {report_date}<br>
        🔒 Confidential - For authorized personnel only
    </div>
</body>
</html>
"""
    
    logger.info(f"Generated email report for {total_drivers} drivers with {violation_count} violations")
    return html_content

def generate_quick_summary_email(drivers_count, violations_count, week_range):
    """
    Generate a quick summary email for immediate distribution
    
    Args:
        drivers_count: Total number of drivers
        violations_count: Number of violations found
        week_range: Date range string
    
    Returns:
        str: HTML formatted summary email
    """
    
    compliance_rate = max(0, 100 - (violations_count / max(drivers_count, 1) * 100))
    timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stats {{ display: flex; justify-content: space-around; background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 12px; color: #6c757d; text-transform: uppercase; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🚛 TRAXOVO Quick Summary</h2>
        <p>{week_range}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-number">{drivers_count}</div>
            <div class="stat-label">Drivers</div>
        </div>
        <div class="stat">
            <div class="stat-number">{violations_count}</div>
            <div class="stat-label">Violations</div>
        </div>
        <div class="stat">
            <div class="stat-number">{compliance_rate:.1f}%</div>
            <div class="stat-label">Compliance</div>
        </div>
    </div>
    
    <p style="text-align: center; color: #6c757d; font-size: 14px;">
        Generated on {timestamp} • TRAXOVO Fleet Management
    </p>
</body>
</html>
"""
    
    return html_content