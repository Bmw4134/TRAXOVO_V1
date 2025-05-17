"""
OCR Processor Utility

This module provides functions for extracting text from PDF documents and images
using optical character recognition (OCR) technology. It supports various file formats
and customizable processing options.
"""

import os
import re
import cv2
import pytesseract
import numpy as np
import pandas as pd
import logging
from PIL import Image
from pathlib import Path
from pdf2image import convert_from_path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Path to tesseract executable (only needed for Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRProcessor:
    """OCR Processor class for handling PDF and image text extraction"""
    
    def __init__(self, temp_dir='temp_ocr', output_dir='extracted_data'):
        """
        Initialize OCR processor
        
        Args:
            temp_dir (str): Directory for temporary files
            output_dir (str): Directory for extracted data output
        """
        self.temp_dir = Path(temp_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure image processing parameters
        self.dpi = 300  # Resolution for PDF conversion
        self.image_processing_options = {
            'resize_factor': 1.5,  # Upscaling factor for better recognition
            'sharpen': True,  # Apply sharpening filter
            'denoise': True,  # Apply denoising filter
            'threshold': True  # Apply adaptive thresholding
        }
        
        # OCR configuration
        self.ocr_config = '--oem 3 --psm 6'  # Page segmentation mode and OCR engine mode
    
    def process_file(self, file_path, lang='eng', output_format='text', custom_config=None):
        """
        Process a file (PDF or image) with OCR
        
        Args:
            file_path (str): Path to the file
            lang (str): Language for OCR (default: 'eng')
            output_format (str): Output format ('text', 'csv', 'json', or 'excel')
            custom_config (str, optional): Custom tesseract configuration
            
        Returns:
            dict: Processing results including text, file paths, and metadata
        """
        try:
            file_path = Path(file_path)
            filename = file_path.stem
            file_ext = file_path.suffix.lower()
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return {"success": False, "error": "File not found"}
            
            # Process based on file type
            if file_ext == '.pdf':
                result = self.process_pdf(file_path, lang, custom_config)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']:
                result = self.process_image(file_path, lang, custom_config)
            else:
                logger.error(f"Unsupported file format: {file_ext}")
                return {"success": False, "error": "Unsupported file format"}
            
            # Save results
            if result["success"]:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f"{filename}_extracted_{timestamp}"
                
                output_paths = self.save_output(result["text"], result["structured_data"], 
                                               output_filename, output_format)
                
                result["output_paths"] = output_paths
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_pdf(self, pdf_path, lang='eng', custom_config=None):
        """
        Process a PDF file with OCR
        
        Args:
            pdf_path (str or Path): Path to PDF file
            lang (str): Language for OCR
            custom_config (str, optional): Custom tesseract configuration
            
        Returns:
            dict: Processing results
        """
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=self.dpi)
            logger.info(f"Converted PDF to {len(pages)} images")
            
            all_text = []
            page_texts = []
            structured_data = []
            
            # Process each page
            for i, page in enumerate(pages):
                logger.info(f"Processing page {i+1}/{len(pages)}")
                
                # Save temporary image
                img_path = self.temp_dir / f"page_{i+1}.png"
                page.save(img_path, 'PNG')
                
                # Process the image
                img_result = self.process_image(img_path, lang, custom_config)
                
                if img_result["success"]:
                    all_text.append(img_result["text"])
                    page_texts.append({
                        "page": i+1,
                        "text": img_result["text"],
                        "word_count": len(img_result["text"].split())
                    })
                    
                    # Add page number to structured data
                    for item in img_result.get("structured_data", []):
                        item["page"] = i+1
                        structured_data.append(item)
                
                # Remove temporary image
                if img_path.exists():
                    os.remove(img_path)
            
            # Combine text from all pages
            combined_text = "\n\n".join(all_text)
            
            return {
                "success": True,
                "text": combined_text,
                "page_count": len(pages),
                "page_texts": page_texts,
                "structured_data": structured_data,
                "word_count": len(combined_text.split()),
                "source_file": str(pdf_path)
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_image(self, image_path, lang='eng', custom_config=None):
        """
        Process an image file with OCR
        
        Args:
            image_path (str or Path): Path to image file
            lang (str): Language for OCR
            custom_config (str, optional): Custom tesseract configuration
            
        Returns:
            dict: Processing results
        """
        try:
            image_path = Path(image_path)
            logger.info(f"Processing image: {image_path}")
            
            # Read image with OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Could not read image: {image_path}")
                return {"success": False, "error": "Could not read image"}
            
            # Image preprocessing
            processed_img = self.preprocess_image(img)
            
            # Apply OCR
            config = custom_config if custom_config else self.ocr_config
            text = pytesseract.image_to_string(processed_img, lang=lang, config=config)
            
            # Get structured data
            structured_data = self.extract_structured_data(processed_img, lang)
            
            return {
                "success": True,
                "text": text,
                "structured_data": structured_data,
                "word_count": len(text.split()),
                "source_file": str(image_path)
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def preprocess_image(self, img):
        """
        Preprocess image to improve OCR accuracy
        
        Args:
            img: OpenCV image (numpy array)
            
        Returns:
            Processed image
        """
        # Convert to grayscale if it's a color image
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # Resize for better recognition
        if self.image_processing_options.get('resize_factor', 1) > 1:
            factor = self.image_processing_options['resize_factor']
            gray = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)
        
        # Apply denoising
        if self.image_processing_options.get('denoise', False):
            gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Apply sharpening
        if self.image_processing_options.get('sharpen', False):
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            gray = cv2.filter2D(gray, -1, kernel)
        
        # Apply adaptive thresholding
        if self.image_processing_options.get('threshold', False):
            gray = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
        
        return gray
    
    def extract_structured_data(self, img, lang='eng'):
        """
        Extract structured data from image (tables, forms, etc.)
        
        Args:
            img: OpenCV image
            lang (str): Language for OCR
            
        Returns:
            list: Structured data items
        """
        try:
            # Get data frames (tables)
            data_frames = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DATAFRAME)
            
            # Extract table-like structures
            structured_data = []
            
            # TODO: Implement more sophisticated table detection algorithm
            # This is a simplified approach
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return []
    
    def save_output(self, text, structured_data, filename, output_format='text'):
        """
        Save extracted text and data to file
        
        Args:
            text (str): Extracted text
            structured_data (list): Structured data
            filename (str): Base filename
            output_format (str): Output format
            
        Returns:
            dict: Paths to output files
        """
        output_paths = {}
        
        try:
            # Save text
            text_path = self.output_dir / f"{filename}.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            output_paths['text'] = str(text_path)
            
            # Save in requested format
            if output_format == 'csv' and structured_data:
                csv_path = self.output_dir / f"{filename}.csv"
                pd.DataFrame(structured_data).to_csv(csv_path, index=False)
                output_paths['csv'] = str(csv_path)
                
            elif output_format == 'excel' and structured_data:
                excel_path = self.output_dir / f"{filename}.xlsx"
                pd.DataFrame(structured_data).to_excel(excel_path, index=False)
                output_paths['excel'] = str(excel_path)
                
            elif output_format == 'json' and structured_data:
                json_path = self.output_dir / f"{filename}.json"
                pd.DataFrame(structured_data).to_json(json_path, orient='records')
                output_paths['json'] = str(json_path)
            
        except Exception as e:
            logger.error(f"Error saving output: {str(e)}")
        
        return output_paths
    
    def recognize_document_type(self, text):
        """
        Try to determine document type based on recognized text
        
        Args:
            text (str): OCR extracted text
            
        Returns:
            str: Document type or 'unknown'
        """
        text = text.lower()
        
        # Invoice patterns
        if re.search(r'invoice|bill to|payment due', text):
            return 'invoice'
            
        # Receipt patterns
        if re.search(r'receipt|thank you for your purchase', text):
            return 'receipt'
            
        # Driver timecard patterns
        if re.search(r'timecard|time card|hours worked|employee id', text):
            return 'timecard'
            
        # Equipment report patterns
        if re.search(r'equipment|maintenance report|service record', text):
            return 'equipment_report'
            
        # Asset allocation patterns
        if re.search(r'allocation|billing allocation|equipment allocation', text):
            return 'allocation_report'
            
        return 'unknown'

    def extract_driver_report_data(self, text):
        """
        Extract structured data from driver reports
        
        Args:
            text (str): OCR extracted text
            
        Returns:
            dict: Extracted data
        """
        data = {
            'driver_name': None,
            'driver_id': None,
            'date': None,
            'start_time': None,
            'end_time': None,
            'total_hours': None,
            'location': None,
            'equipment_used': [],
            'notes': None
        }
        
        # Extract driver name
        name_match = re.search(r'name:?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
        if name_match:
            data['driver_name'] = name_match.group(1).strip()
        
        # Extract driver ID
        id_match = re.search(r'id:?\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if id_match:
            data['driver_id'] = id_match.group(1).strip()
        
        # Extract date
        date_match = re.search(r'date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text, re.IGNORECASE)
        if date_match:
            data['date'] = date_match.group(1).strip()
        
        # Extract times
        start_time_match = re.search(r'start:?\s*(\d{1,2}:\d{2}\s*[aApP][mM]?)', text, re.IGNORECASE)
        if start_time_match:
            data['start_time'] = start_time_match.group(1).strip()
            
        end_time_match = re.search(r'end:?\s*(\d{1,2}:\d{2}\s*[aApP][mM]?)', text, re.IGNORECASE)
        if end_time_match:
            data['end_time'] = end_time_match.group(1).strip()
        
        # Extract total hours
        hours_match = re.search(r'total:?\s*(\d+\.?\d*)\s*hours', text, re.IGNORECASE)
        if hours_match:
            data['total_hours'] = float(hours_match.group(1).strip())
        
        # Extract location
        location_match = re.search(r'location:?\s*([A-Za-z0-9\s-]+)', text, re.IGNORECASE)
        if location_match:
            data['location'] = location_match.group(1).strip()
        
        # Extract equipment
        equipment_matches = re.findall(r'equipment:?\s*([A-Z]{2}-\d{4})', text, re.IGNORECASE)
        if equipment_matches:
            data['equipment_used'] = equipment_matches
        
        # Extract notes - everything after "notes:" or "comments:"
        notes_match = re.search(r'notes:?\s*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if not notes_match:
            notes_match = re.search(r'comments:?\s*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        
        if notes_match:
            data['notes'] = notes_match.group(1).strip()
        
        return data

    def batch_process(self, directory, output_format='text', lang='eng'):
        """
        Process all compatible files in a directory
        
        Args:
            directory (str): Directory containing files to process
            output_format (str): Output format
            lang (str): Language for OCR
            
        Returns:
            dict: Processing results
        """
        directory = Path(directory)
        results = {
            'success': [],
            'failed': [],
            'summary': {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'total_pages': 0,
                'total_words': 0
            }
        }
        
        # Find all PDF and image files
        compatible_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']
        files = []
        
        for ext in compatible_extensions:
            files.extend(list(directory.glob(f'*{ext}')))
        
        results['summary']['total_files'] = len(files)
        
        # Process each file
        for file_path in files:
            result = self.process_file(file_path, lang, output_format)
            
            if result['success']:
                results['success'].append({
                    'file': str(file_path),
                    'output': result['output_paths'],
                    'word_count': result.get('word_count', 0),
                    'page_count': result.get('page_count', 1)
                })
                
                results['summary']['successful'] += 1
                results['summary']['total_pages'] += result.get('page_count', 1)
                results['summary']['total_words'] += result.get('word_count', 0)
            else:
                results['failed'].append({
                    'file': str(file_path),
                    'error': result['error']
                })
                
                results['summary']['failed'] += 1
        
        return results

# Helper functions for working with OCR processor
def ocr_file(file_path, lang='eng', output_format='text'):
    """
    Process a single file with OCR
    
    Args:
        file_path (str): Path to the file
        lang (str): Language for OCR
        output_format (str): Output format
        
    Returns:
        dict: Processing results
    """
    processor = OCRProcessor()
    return processor.process_file(file_path, lang, output_format)

def ocr_directory(directory, output_format='text', lang='eng'):
    """
    Process all compatible files in a directory
    
    Args:
        directory (str): Directory containing files to process
        output_format (str): Output format
        lang (str): Language for OCR
        
    Returns:
        dict: Processing results
    """
    processor = OCRProcessor()
    return processor.batch_process(directory, output_format, lang)

def extract_driver_notes(file_path):
    """
    Extract driver notes from a report file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        dict: Extracted driver data with notes
    """
    processor = OCRProcessor()
    result = processor.process_file(file_path)
    
    if result['success']:
        text = result['text']
        doc_type = processor.recognize_document_type(text)
        
        if doc_type == 'timecard':
            return processor.extract_driver_report_data(text)
    
    return None