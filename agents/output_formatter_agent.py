"""
Output Formatter Agent

This agent formats and transforms report data into different output formats
such as JSON, CSV, PDF, and HTML for display and distribution.
"""
import logging
import json
import time
import csv
import os
from datetime import datetime
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle(data, format_type='json', config=None):
    """
    Format data into the specified output format
    
    Args:
        data (dict): Data to format
        format_type (str): Output format type (json, csv, html, text)
        config (dict): Formatting configuration options
        
    Returns:
        dict: Formatted data with metadata
    """
    start_time = time.time()
    logger.info(f"Output Formatter Agent formatting data to {format_type}")
    
    # Set defaults for configuration
    if not config:
        config = {}
    
    pretty_print = config.get('pretty_print', True)
    include_metadata = config.get('include_metadata', True)
    output_path = config.get('output_path', None)
    
    # Format data based on requested type
    formatted_data = None
    if format_type.lower() == 'json':
        formatted_data = format_json(data, pretty_print)
    elif format_type.lower() == 'csv':
        formatted_data = format_csv(data)
    elif format_type.lower() == 'html':
        formatted_data = format_html(data, config)
    elif format_type.lower() == 'text':
        formatted_data = format_text(data)
    else:
        logger.warning(f"Unsupported format type: {format_type}, defaulting to JSON")
        formatted_data = format_json(data, pretty_print)
    
    processing_time = time.time() - start_time
    
    # Save to file if output path is provided
    if output_path:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_data)
            logger.info(f"Output saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving output to {output_path}: {e}")
    
    # Log usage
    log_usage(
        format_type, 
        len(str(data)) if data else 0,
        len(formatted_data) if formatted_data else 0,
        processing_time
    )
    
    # Return formatted data with metadata
    result = {
        'formatted_data': formatted_data,
        'format_type': format_type
    }
    
    if include_metadata:
        result['metadata'] = {
            'formatted_at': datetime.now().isoformat(),
            'processing_time': round(processing_time, 3),
            'original_size': len(str(data)) if data else 0,
            'formatted_size': len(formatted_data) if formatted_data else 0,
            'output_path': output_path
        }
    
    return result

def run(data, format_type='json', config=None):
    """Alias for handle() function"""
    return handle(data, format_type, config)

def format_json(data, pretty_print=True):
    """
    Format data as JSON
    
    Args:
        data (dict): Data to format
        pretty_print (bool): Whether to format with indentation
        
    Returns:
        str: JSON formatted string
    """
    try:
        if pretty_print:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    except Exception as e:
        logger.error(f"Error formatting JSON: {e}")
        return json.dumps({"error": str(e)})

def format_csv(data):
    """
    Format data as CSV
    
    Args:
        data (dict): Data to format
        
    Returns:
        str: CSV formatted string
    """
    try:
        output = StringIO()
        
        # Handle different data structures
        if isinstance(data, list) and len(data) > 0:
            # List of dictionaries
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        elif isinstance(data, dict):
            # Single dictionary or nested structure
            if 'drivers' in data and isinstance(data['drivers'], list) and len(data['drivers']) > 0:
                # Extract drivers list
                writer = csv.DictWriter(output, fieldnames=data['drivers'][0].keys())
                writer.writeheader()
                writer.writerows(data['drivers'])
            elif 'job_sites' in data and isinstance(data['job_sites'], list) and len(data['job_sites']) > 0:
                # Extract job sites list
                writer = csv.DictWriter(output, fieldnames=data['job_sites'][0].keys())
                writer.writeheader()
                writer.writerows(data['job_sites'])
            else:
                # Flatten dictionary
                writer = csv.writer(output)
                for key, value in data.items():
                    if not isinstance(value, (dict, list)):
                        writer.writerow([key, value])
        else:
            raise ValueError("Data format not supported for CSV conversion")
            
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error formatting CSV: {e}")
        return f"Error formatting CSV: {e}"

def format_html(data, config=None):
    """
    Format data as HTML
    
    Args:
        data (dict): Data to format
        config (dict): HTML formatting options
        
    Returns:
        str: HTML formatted string
    """
    try:
        # Default configuration
        if not config:
            config = {}
        
        title = config.get('title', 'TRAXORA Report')
        include_css = config.get('include_css', True)
        include_charts = config.get('include_charts', True)
        
        # Start HTML document
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        """
        
        # Add CSS if requested
        if include_css:
            html += """
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .summary { background-color: #e7f0fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .good { color: green; }
                .warning { color: orange; }
                .critical { color: red; }
                .chart-container { height: 300px; margin-bottom: 30px; }
            </style>
            """
        
        # Add chart library if requested
        if include_charts:
            html += """
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            """
        
        html += """
        </head>
        <body>
        """
        
        # Add title
        html += f"""
        <h1>{title}</h1>
        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Add summary section if available
        if isinstance(data, dict) and ('summary' in data or 'driver_summary' in data):
            html += """
            <div class="summary">
                <h2>Summary</h2>
            """
            
            if 'summary' in data:
                html += "<table>"
                for key, value in data['summary'].items():
                    html += f"<tr><th>{key.replace('_', ' ').title()}</th><td>{value}</td></tr>"
                html += "</table>"
            elif 'driver_summary' in data:
                html += "<h3>Driver Summary</h3>"
                html += "<table>"
                for key, value in data['driver_summary'].items():
                    html += f"<tr><th>{key.replace('_', ' ').title()}</th><td>{value}</td></tr>"
                html += "</table>"
                
                if 'job_site_summary' in data:
                    html += "<h3>Job Site Summary</h3>"
                    html += "<table>"
                    for key, value in data['job_site_summary'].items():
                        html += f"<tr><th>{key.replace('_', ' ').title()}</th><td>{value}</td></tr>"
                    html += "</table>"
            
            html += """
            </div>
            """
        
        # Add charts if requested and data is available
        if include_charts and isinstance(data, dict):
            if 'driver_summary' in data or 'summary' in data:
                summary = data.get('driver_summary', data.get('summary', {}))
                
                if 'on_time_count' in summary and 'late_count' in summary and 'early_end_count' in summary:
                    html += """
                    <div class="chart-container">
                        <canvas id="statusChart"></canvas>
                    </div>
                    <script>
                        var ctx = document.getElementById('statusChart').getContext('2d');
                        var statusChart = new Chart(ctx, {
                            type: 'pie',
                            data: {
                                labels: ['On Time', 'Late', 'Early End', 'Not On Job'],
                                datasets: [{
                                    data: [%d, %d, %d, %d],
                                    backgroundColor: ['#4CAF50', '#FFC107', '#FF9800', '#F44336']
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                title: {
                                    display: true,
                                    text: 'Driver Status Distribution'
                                }
                            }
                        });
                    </script>
                    """ % (
                        summary.get('on_time_count', 0),
                        summary.get('late_count', 0),
                        summary.get('early_end_count', 0),
                        summary.get('not_on_job_count', 0)
                    )
        
        # Add data tables
        if isinstance(data, dict):
            # Add drivers table if available
            if 'drivers' in data and isinstance(data['drivers'], list) and len(data['drivers']) > 0:
                html += """
                <h2>Drivers</h2>
                <table>
                    <tr>
                """
                
                # Get all unique keys from all driver dictionaries
                keys = set()
                for driver in data['drivers']:
                    keys.update(driver.keys())
                
                # Add table headers
                for key in keys:
                    html += f"<th>{key.replace('_', ' ').title()}</th>"
                
                html += "</tr>"
                
                # Add table rows
                for driver in data['drivers']:
                    html += "<tr>"
                    for key in keys:
                        value = driver.get(key, "")
                        html += f"<td>{value}</td>"
                    html += "</tr>"
                
                html += "</table>"
            
            # Add job sites table if available
            if 'job_sites' in data and isinstance(data['job_sites'], list) and len(data['job_sites']) > 0:
                html += """
                <h2>Job Sites</h2>
                <table>
                    <tr>
                """
                
                # Get all unique keys from all job site dictionaries
                keys = set()
                for site in data['job_sites']:
                    keys.update(site.keys())
                
                # Add table headers
                for key in keys:
                    html += f"<th>{key.replace('_', ' ').title()}</th>"
                
                html += "</tr>"
                
                # Add table rows
                for site in data['job_sites']:
                    html += "<tr>"
                    for key in keys:
                        value = site.get(key, "")
                        html += f"<td>{value}</td>"
                    html += "</tr>"
                
                html += "</table>"
        
        # Close HTML document
        html += """
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        logger.error(f"Error formatting HTML: {e}")
        return f"<html><body><h1>Error</h1><p>{e}</p></body></html>"

def format_text(data):
    """
    Format data as plain text
    
    Args:
        data (dict): Data to format
        
    Returns:
        str: Text formatted string
    """
    try:
        output = []
        
        # Add header
        output.append("=== TRAXORA REPORT ===")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 30)
        
        # Format based on data structure
        if isinstance(data, dict):
            # Add summary if available
            if 'summary' in data:
                output.append("\n=== SUMMARY ===")
                for key, value in data['summary'].items():
                    output.append(f"{key.replace('_', ' ').title()}: {value}")
            elif 'driver_summary' in data:
                output.append("\n=== DRIVER SUMMARY ===")
                for key, value in data['driver_summary'].items():
                    output.append(f"{key.replace('_', ' ').title()}: {value}")
                
                if 'job_site_summary' in data:
                    output.append("\n=== JOB SITE SUMMARY ===")
                    for key, value in data['job_site_summary'].items():
                        output.append(f"{key.replace('_', ' ').title()}: {value}")
            
            # Add drivers if available
            if 'drivers' in data and isinstance(data['drivers'], list):
                output.append("\n=== DRIVERS ===")
                for i, driver in enumerate(data['drivers'], 1):
                    output.append(f"\nDriver {i}:")
                    for key, value in driver.items():
                        output.append(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Add job sites if available
            if 'job_sites' in data and isinstance(data['job_sites'], list):
                output.append("\n=== JOB SITES ===")
                for i, site in enumerate(data['job_sites'], 1):
                    output.append(f"\nJob Site {i}:")
                    for key, value in site.items():
                        output.append(f"  {key.replace('_', ' ').title()}: {value}")
        elif isinstance(data, list):
            # Format list of dictionaries
            for i, item in enumerate(data, 1):
                output.append(f"\nItem {i}:")
                if isinstance(item, dict):
                    for key, value in item.items():
                        output.append(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    output.append(f"  {item}")
        else:
            # Simple string representation
            output.append(str(data))
        
        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error formatting text: {e}")
        return f"Error formatting text: {e}"

def log_usage(format_type, input_size, output_size, processing_time):
    """
    Log agent usage statistics
    
    Args:
        format_type (str): Type of formatting performed
        input_size (int): Size of input data in characters
        output_size (int): Size of output data in characters
        processing_time (float): Processing time in seconds
    """
    usage_log = {
        "agent": "output_formatter",
        "timestamp": datetime.now().isoformat(),
        "format_type": format_type,
        "input_size": input_size,
        "output_size": output_size,
        "processing_time": round(processing_time, 3),
        "throughput_kb_per_sec": round((input_size / 1024) / processing_time, 2) if processing_time > 0 else 0
    }
    
    logger.info(f"Agent usage: {json.dumps(usage_log)}")
    
    # In a production environment, this could write to a database or external logging system
    try:
        with open("logs/agent_usage.log", "a") as f:
            f.write(json.dumps(usage_log) + "\n")
    except Exception as e:
        logger.warning(f"Could not write to agent usage log: {e}")

if __name__ == "__main__":
    # Example usage
    test_data = {
        "driver_summary": {
            "total_drivers": 3,
            "on_time_count": 1,
            "on_time_percent": 33,
            "late_count": 1,
            "late_percent": 33,
            "early_end_count": 1,
            "early_end_percent": 33
        },
        "drivers": [
            {"name": "John Doe", "job_site": "Downtown Project", "status": "on_time"},
            {"name": "Jane Smith", "job_site": "Uptown Project", "status": "late"},
            {"name": "Bob Johnson", "job_site": "Downtown Project", "status": "early_end"}
        ]
    }
    
    # Test JSON formatting
    json_result = handle(test_data, 'json')
    print("JSON formatting example:")
    print(json_result['formatted_data'][:200] + "...\n")
    
    # Test CSV formatting
    csv_result = handle(test_data, 'csv')
    print("CSV formatting example:")
    print(csv_result['formatted_data'][:200] + "...\n")
    
    # Test text formatting
    text_result = handle(test_data, 'text')
    print("Text formatting example:")
    print(text_result['formatted_data'][:200] + "...")