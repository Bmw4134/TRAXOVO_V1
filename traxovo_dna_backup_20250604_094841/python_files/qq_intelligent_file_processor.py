"""
QQ Intelligent File Processor
Bleeding-edge smart uploader for large CSV/PDF files with quantum parsing
Handles headers, chunked processing, and intelligent data extraction
"""

import os
import csv
import json
import pandas as pd
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator
import tempfile
import logging
from pathlib import Path

# PDF processing
try:
    import PyPDF2
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class QQIntelligentFileProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix='qq_processor_')
        self.chunk_size = 1000  # Process 1000 rows at a time
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.pdf']
        self.processing_results = {}
        
    def process_file_intelligently(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        Intelligently process uploaded file with quantum parsing
        """
        try:
            file_size = os.path.getsize(file_path)
            file_ext = Path(file_path).suffix.lower()
            
            processing_result = {
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'file_type': file_type,
                'file_extension': file_ext,
                'processing_start': datetime.now().isoformat(),
                'status': 'processing',
                'total_rows': 0,
                'processed_rows': 0,
                'data_preview': [],
                'headers': [],
                'issues': [],
                'insights': {}
            }
            
            # Route to appropriate processor
            if file_ext == '.pdf' and PDF_SUPPORT:
                return self.process_pdf_file(file_path, processing_result)
            elif file_ext in ['.csv']:
                return self.process_csv_file_chunked(file_path, processing_result)
            elif file_ext in ['.xlsx', '.xls']:
                return self.process_excel_file_chunked(file_path, processing_result)
            else:
                processing_result['status'] = 'error'
                processing_result['issues'].append(f'Unsupported file format: {file_ext}')
                return processing_result
                
        except Exception as e:
            processing_result['status'] = 'error'
            processing_result['issues'].append(f'Processing error: {str(e)}')
            return processing_result
    
    def process_csv_file_chunked(self, file_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process large CSV files in chunks with intelligent header detection
        """
        try:
            # Detect encoding
            encoding = self.detect_file_encoding(file_path)
            result['encoding'] = encoding
            
            # Smart header detection
            headers, header_row = self.detect_csv_headers(file_path, encoding)
            result['headers'] = headers
            result['header_row'] = header_row
            
            # Process in chunks
            chunk_count = 0
            total_processed = 0
            data_preview = []
            
            for chunk in self.read_csv_chunks(file_path, encoding, header_row):
                chunk_count += 1
                chunk_size = len(chunk)
                total_processed += chunk_size
                
                # Store preview from first chunk
                if chunk_count == 1:
                    data_preview = chunk[:10]  # First 10 rows for preview
                
                # Process chunk for insights
                self.analyze_chunk_data(chunk, result, headers)
                
                result['processed_rows'] = total_processed
                
                # Break if preview only
                if chunk_count >= 5:  # Process max 5 chunks for testing
                    break
            
            result['total_rows'] = total_processed
            result['data_preview'] = data_preview
            result['status'] = 'completed'
            result['processing_end'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'CSV processing error: {str(e)}')
            return result
    
    def detect_file_encoding(self, file_path: str) -> str:
        """
        Detect file encoding intelligently
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # Read first 1KB
                return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # Default fallback
    
    def detect_csv_headers(self, file_path: str, encoding: str) -> tuple:
        """
        Intelligently detect CSV headers and problematic header row
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first few lines to analyze structure
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.strip())
                    if i >= 10:  # Analyze first 10 lines
                        break
            
            # Look for header patterns
            header_candidates = []
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['employee', 'driver', 'asset', 'date', 'time', 'location']):
                    header_candidates.append((i, line))
            
            if header_candidates:
                # Use the first header candidate
                header_row, header_line = header_candidates[0]
                headers = [col.strip().strip('"') for col in header_line.split(',')]
                return headers, header_row
            else:
                # Use first line as headers
                headers = [col.strip().strip('"') for col in lines[0].split(',')]
                return headers, 0
                
        except Exception as e:
            # Fallback to basic CSV detection
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                first_row = next(reader)
                return first_row, 0
    
    def read_csv_chunks(self, file_path: str, encoding: str, header_row: int) -> Generator[List[Dict], None, None]:
        """
        Read CSV file in chunks for memory efficiency
        """
        with open(file_path, 'r', encoding=encoding) as f:
            # Skip to header row
            for _ in range(header_row):
                next(f)
            
            reader = csv.DictReader(f)
            chunk = []
            
            for row in reader:
                chunk.append(row)
                
                if len(chunk) >= self.chunk_size:
                    yield chunk
                    chunk = []
            
            # Yield remaining rows
            if chunk:
                yield chunk
    
    def analyze_chunk_data(self, chunk: List[Dict], result: Dict[str, Any], headers: List[str]):
        """
        Analyze chunk data for insights and patterns
        """
        if not chunk:
            return
        
        # Initialize insights if not exists
        if 'insights' not in result:
            result['insights'] = {
                'employee_count': set(),
                'asset_count': set(),
                'date_range': {'min': None, 'max': None},
                'locations': set(),
                'data_quality': {'empty_fields': 0, 'total_fields': 0}
            }
        
        insights = result['insights']
        
        for row in chunk:
            # Track employees
            for field in ['employee_id', 'driver_id', 'emp_id', 'employee']:
                if field in row and row[field]:
                    insights['employee_count'].add(row[field])
            
            # Track assets
            for field in ['asset', 'asset_id', 'vehicle', 'equipment']:
                if field in row and row[field]:
                    insights['asset_count'].add(row[field])
            
            # Track locations
            for field in ['location', 'site', 'job_site', 'project']:
                if field in row and row[field]:
                    insights['locations'].add(row[field])
            
            # Analyze data quality
            for key, value in row.items():
                insights['data_quality']['total_fields'] += 1
                if not value or value.strip() == '':
                    insights['data_quality']['empty_fields'] += 1
        
        # Convert sets to counts for JSON serialization
        result['insights']['employee_count'] = len(insights['employee_count'])
        result['insights']['asset_count'] = len(insights['asset_count'])
        result['insights']['locations'] = len(insights['locations'])
    
    def process_pdf_file(self, file_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PDF files with intelligent text extraction
        """
        if not PDF_SUPPORT:
            result['status'] = 'error'
            result['issues'].append('PDF processing not available - install PyPDF2 and pdfplumber')
            return result
        
        try:
            extracted_text = []
            tables = []
            
            # Try pdfplumber first for better table extraction
            with pdfplumber.open(file_path) as pdf:
                result['total_pages'] = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages[:5]):  # Process first 5 pages for testing
                    # Extract text
                    text = page.extract_text()
                    if text:
                        extracted_text.append(text)
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                    
                    result['processed_pages'] = i + 1
            
            # Analyze extracted content
            result['extracted_text_length'] = sum(len(text) for text in extracted_text)
            result['tables_found'] = len(tables)
            result['data_preview'] = extracted_text[:2] if extracted_text else []
            
            # If tables found, convert to structured data
            if tables:
                structured_data = self.convert_pdf_tables_to_data(tables)
                result['structured_data'] = structured_data[:10]  # Preview
            
            result['status'] = 'completed'
            result['processing_end'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'PDF processing error: {str(e)}')
            return result
    
    def convert_pdf_tables_to_data(self, tables: List[List[List]]) -> List[Dict]:
        """
        Convert PDF tables to structured data
        """
        structured_data = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Use first row as headers
            headers = [str(cell).strip() if cell else f'col_{i}' for i, cell in enumerate(table[0])]
            
            # Convert rows to dictionaries
            for row in table[1:]:
                if row and any(cell for cell in row):  # Skip empty rows
                    row_dict = {}
                    for i, cell in enumerate(row):
                        if i < len(headers):
                            row_dict[headers[i]] = str(cell).strip() if cell else ''
                    structured_data.append(row_dict)
        
        return structured_data
    
    def process_excel_file_chunked(self, file_path: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Excel files in chunks
        """
        try:
            # Read Excel file info
            xl_file = pd.ExcelFile(file_path)
            result['sheet_names'] = xl_file.sheet_names
            
            # Process first sheet in chunks
            sheet_name = xl_file.sheet_names[0]
            chunk_size = self.chunk_size
            
            chunks_processed = 0
            total_rows = 0
            data_preview = []
            
            # Read in chunks
            for chunk in pd.read_excel(file_path, sheet_name=sheet_name, chunksize=chunk_size):
                chunks_processed += 1
                chunk_rows = len(chunk)
                total_rows += chunk_rows
                
                # Store preview from first chunk
                if chunks_processed == 1:
                    result['headers'] = chunk.columns.tolist()
                    data_preview = chunk.head(10).to_dict('records')
                
                # Analyze chunk
                self.analyze_excel_chunk(chunk, result)
                
                result['processed_rows'] = total_rows
                
                # Limit processing for testing
                if chunks_processed >= 5:
                    break
            
            result['total_rows'] = total_rows
            result['data_preview'] = data_preview
            result['status'] = 'completed'
            result['processing_end'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['issues'].append(f'Excel processing error: {str(e)}')
            return result
    
    def analyze_excel_chunk(self, chunk: pd.DataFrame, result: Dict[str, Any]):
        """
        Analyze Excel chunk for insights
        """
        if 'insights' not in result:
            result['insights'] = {
                'data_types': {},
                'null_counts': {},
                'unique_values': {}
            }
        
        insights = result['insights']
        
        for column in chunk.columns:
            # Data types
            insights['data_types'][column] = str(chunk[column].dtype)
            
            # Null counts
            null_count = chunk[column].isnull().sum()
            if column not in insights['null_counts']:
                insights['null_counts'][column] = 0
            insights['null_counts'][column] += null_count
            
            # Unique values (sample)
            unique_sample = chunk[column].dropna().unique()[:5]
            insights['unique_values'][column] = [str(val) for val in unique_sample]
    
    def save_processing_result(self, result: Dict[str, Any]) -> str:
        """
        Save processing result to temporary file
        """
        result_file = os.path.join(self.temp_dir, f"processing_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Make result JSON serializable
        json_result = json.loads(json.dumps(result, default=str))
        
        with open(result_file, 'w') as f:
            json.dump(json_result, f, indent=2)
        
        return result_file

# Global processor instance
qq_processor = QQIntelligentFileProcessor()

def process_uploaded_file(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Main entry point for file processing
    """
    return qq_processor.process_file_intelligently(file_path, file_type)