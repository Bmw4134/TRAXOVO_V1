"""
Debugging MTD Parser

This script helps debug the MTD file parsing issues by extracting and showing detailed information 
about the CSV files, headers, and matching records.
"""

import csv
import sys
import pandas as pd
import re
import logging
import datetime
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def debug_csv_file(file_path, target_date_str=None):
    """Analyze a CSV file and debug parsing issues"""
    logger.info(f"DEBUG: Analyzing file {file_path}")
    
    # If target date is provided, parse it
    target_date = None
    if target_date_str:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        logger.info(f"DEBUG: Filtering for target date {target_date}")
    
    # First, let's try to dump the raw file structure
    logger.info("DEBUG: Dumping raw file structure (first 20 lines):")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if i < 20:  # Limit to first 20 lines
                    logger.info(f"Line {i+1}: {line.strip()}")
                else:
                    break
    except Exception as e:
        logger.error(f"DEBUG: Error reading file: {e}")
        return
    
    # Now, analyze the file to find the header row
    logger.info("DEBUG: Looking for header row...")
    header_row = find_header_row(file_path)
    if not header_row:
        logger.error("DEBUG: Could not find header row!")
        return
    
    logger.info(f"DEBUG: Found header row: {header_row['row']}")
    logger.info(f"DEBUG: Header row index: {header_row['index']}")
    
    # Try to load the data with pandas, skipping the header rows
    try:
        logger.info(f"DEBUG: Loading data with pandas, skipping {header_row['index']} rows...")
        df = pd.read_csv(file_path, skiprows=header_row['index'], encoding='utf-8-sig')
        logger.info(f"DEBUG: DataFrame shape: {df.shape}")
        logger.info(f"DEBUG: DataFrame columns: {df.columns.tolist()}")
        
        # Show first few rows
        logger.info("DEBUG: First 3 rows:")
        logger.info(df.head(3))
        
        # Try to find the timestamp column
        timestamp_column = find_timestamp_column(df)
        if timestamp_column:
            logger.info(f"DEBUG: Found timestamp column: {timestamp_column}")
            
            # Try to parse timestamps and filter by date
            logger.info(f"DEBUG: Parsing timestamps from column '{timestamp_column}'...")
            df = parse_timestamps(df, timestamp_column)
            
            if 'parsed_timestamp' in df.columns:
                logger.info("DEBUG: Successfully parsed timestamps")
                logger.info(f"DEBUG: First 3 timestamps: {df['parsed_timestamp'].head(3).tolist()}")
                
                if target_date:
                    # Filter by target date
                    date_mask = df['parsed_timestamp'].dt.date == target_date
                    logger.info(f"DEBUG: Records matching target date {target_date}: {date_mask.sum()}")
                    
                    # Show some of the matching records
                    matching_records = df[date_mask].head(5)
                    logger.info(f"DEBUG: Sample matching records:\n{matching_records}")
            else:
                logger.error("DEBUG: Failed to parse timestamps")
        else:
            logger.error("DEBUG: Could not find a timestamp column")
        
        # Try to find the driver column
        driver_column = find_driver_column(df)
        if driver_column:
            logger.info(f"DEBUG: Found driver column: {driver_column}")
            logger.info(f"DEBUG: Unique drivers: {df[driver_column].nunique()}")
            logger.info(f"DEBUG: Sample driver values: {df[driver_column].dropna().unique()[:5]}")
        else:
            logger.error("DEBUG: Could not find a driver column")
            
        # Try to find the event type column
        event_column = find_event_column(df)
        if event_column:
            logger.info(f"DEBUG: Found event column: {event_column}")
            logger.info(f"DEBUG: Unique event types: {df[event_column].dropna().unique()[:10]}")
        else:
            logger.error("DEBUG: Could not find an event column")
            
    except Exception as e:
        logger.error(f"DEBUG: Error processing with pandas: {e}")
        import traceback
        logger.error(traceback.format_exc())

def find_header_row(file_path):
    """Find the most likely header row in the file"""
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        
        best_row = None
        best_score = 0
        
        for i, row in enumerate(reader):
            if len(row) == 0:
                continue
                
            # Score this row based on how likely it is to be a header
            score = score_header_row(row)
            logger.info(f"DEBUG: Row {i} score: {score} - {row[:5]}...")
            
            if score > best_score:
                best_score = score
                best_row = {"index": i, "row": row}
            
            # Stop after a reasonable number of lines
            if i > 30:
                break
    
    return best_row

def score_header_row(row):
    """Score a row based on how likely it is to be a header row"""
    score = 0
    
    # Headers often contain certain keywords
    header_keywords = ['contact', 'driver', 'event', 'date', 'time', 'location', 
                      'asset', 'latitude', 'longitude', 'speed', 'reason', 'msg']
    
    row_text = ' '.join(row).lower()
    
    # Check for common header keywords
    for keyword in header_keywords:
        if keyword in row_text:
            score += 10
    
    # Headers often have multiple columns
    score += min(len(row), 10)
    
    # Headers usually don't have long strings
    avg_len = sum(len(str(x)) for x in row) / max(len(row), 1)
    if avg_len < 15:
        score += 5
    
    # Headers usually don't have empty cells
    empty_cells = sum(1 for x in row if not str(x).strip())
    score -= empty_cells * 2
    
    return score

def find_timestamp_column(df):
    """Find the column most likely to contain timestamps"""
    # Look for columns with common timestamp names
    timestamp_keywords = ['eventdatetime', 'eventdatetimex', 'timestamp', 'datetime', 'date']
    
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in timestamp_keywords:
            if keyword in col_lower:
                return col
    
    # If no obvious name, try to analyze content
    for col in df.columns:
        # Sample values
        sample = df[col].dropna().astype(str).iloc[:10].tolist()
        sample_text = ' '.join(sample).lower()
        
        # Check for date/time patterns
        if any(re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', s) for s in sample) or \
           any(re.search(r'\d{2,4}-\d{1,2}-\d{1,2}', s) for s in sample) or \
           'am' in sample_text and 'pm' in sample_text:
            return col
    
    return None

def find_driver_column(df):
    """Find the column most likely to contain driver names"""
    driver_keywords = ['contact', 'driver', 'operator', 'user', 'person', 'name']
    
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in driver_keywords:
            if keyword in col_lower:
                return col
    
    return None

def find_event_column(df):
    """Find the column most likely to contain event types"""
    event_keywords = ['msgtype', 'reasonx', 'event', 'action', 'type']
    
    for col in df.columns:
        col_lower = str(col).lower()
        for keyword in event_keywords:
            if keyword in col_lower:
                return col
    
    return None

def parse_timestamps(df, timestamp_column):
    """Try to parse timestamps from the given column"""
    # Keep the original column
    df['original_timestamp'] = df[timestamp_column]
    
    # Try different parsing methods
    try:
        # First, try pandas automatic parsing
        df['parsed_timestamp'] = pd.to_datetime(df[timestamp_column], errors='coerce')
        
        # If too many NaTs, try specific formats
        if df['parsed_timestamp'].isna().sum() > len(df) * 0.5:
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y %I:%M:%S %p',
                '%m/%d/%Y %I:%M:%S %p CT',
                '%Y-%m-%dT%H:%M:%S',
                '%m/%d/%Y %I:%M %p',
            ]
            
            for fmt in formats:
                try:
                    df['parsed_timestamp'] = pd.to_datetime(df[timestamp_column], format=fmt, errors='coerce')
                    if df['parsed_timestamp'].isna().sum() < len(df) * 0.5:
                        logger.info(f"DEBUG: Successfully parsed timestamps with format {fmt}")
                        break
                except:
                    continue
    except Exception as e:
        logger.error(f"DEBUG: Error parsing timestamps: {e}")
    
    return df

if __name__ == "__main__":
    # Usage: python debug_mtd_parser.py <file_path> [target_date]
    if len(sys.argv) < 2:
        print("Usage: python debug_mtd_parser.py <file_path> [target_date]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    target_date = sys.argv[2] if len(sys.argv) > 2 else None
    
    debug_csv_file(file_path, target_date)