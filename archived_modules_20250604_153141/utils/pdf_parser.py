"""
PDF Parser for Gauge Smart Reports
Extracts structured data from Driving History and other reports
"""
import pandas as pd
import PyPDF2
import re
from io import StringIO

def parse_driving_history_pdf(pdf_path):
    """Parse Gauge Smart Driving History PDF into structured data"""
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
        
        # Parse the structured data from the PDF text
        data_rows = []
        
        # Look for the data table section
        lines = full_text.split('\n')
        in_data_section = False
        
        for line in lines:
            # Detect start of data table (after headers)
            if 'Date' in line and 'Message' in line and 'Latitude' in line:
                in_data_section = True
                continue
                
            # Parse data rows
            if in_data_section and line.strip():
                # Stop at page footer or end markers
                if 'Page' in line or 'Gauge Smart' in line:
                    break
                    
                # Extract structured data using regex patterns
                # Format: Date, Message, Latitude, Longitude, Location
                date_pattern = r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)'
                coord_pattern = r'(-?\d+\.\d+)'
                
                date_match = re.search(date_pattern, line)
                if date_match:
                    parts = line.split()
                    
                    # Extract coordinates (latitude, longitude)
                    coords = re.findall(coord_pattern, line)
                    
                    if len(coords) >= 2:
                        row = {
                            'Date': date_match.group(1),
                            'Asset_ID': extract_asset_id(line),
                            'Message': extract_message(line),
                            'Latitude': coords[0],
                            'Longitude': coords[1],
                            'Location': extract_location(line),
                            'Mileage': extract_mileage(line)
                        }
                        data_rows.append(row)
        
        # Convert to DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows)
            return df
        else:
            raise ValueError("No data rows found in PDF")
            
    except Exception as e:
        print(f"Error parsing PDF: {str(e)}")
        return None

def extract_asset_id(line):
    """Extract asset ID from line"""
    # Look for patterns like #210003 or similar
    match = re.search(r'#(\d+)', line)
    return match.group(1) if match else 'Unknown'

def extract_message(line):
    """Extract message/event type from line"""
    # Common messages: Key On, Key Off, Arrived, Departed
    messages = ['Key On', 'Key Off', 'Arrived', 'Departed', 'Speeding', 'Idle']
    for msg in messages:
        if msg in line:
            return msg
    return 'Event'

def extract_location(line):
    """Extract location information"""
    # Look for address patterns or location names
    # This would need to be customized based on your specific PDF format
    location_match = re.search(r'TX\s+\d{5}', line)
    if location_match:
        # Extract surrounding context for full address
        return line.split(location_match.group())[0][-50:] + location_match.group()
    return 'Location Unknown'

def extract_mileage(line):
    """Extract mileage if present"""
    mileage_match = re.search(r'(\d+\.\d+)\s+miles?', line, re.IGNORECASE)
    return float(mileage_match.group(1)) if mileage_match else 0.0

def parse_asset_report_pdf(pdf_path):
    """Parse other Gauge Smart reports"""
    # Similar structure for other report types
    pass