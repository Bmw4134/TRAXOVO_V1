from flask import Blueprint, render_template, request, redirect, flash, send_from_directory, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from pathlib import Path

ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/ocr_tool', methods=['GET', 'POST'])
@login_required
def ocr_tool():
    """OCR document processing tool"""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'document' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['document']
        
        # If user does not select file, browser submits empty file without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file:
            # Create the uploads directory if it doesn't exist
            uploads_dir = Path('uploads')
            uploads_dir.mkdir(exist_ok=True)
            
            # Create the extracted_data directory if it doesn't exist
            extracted_dir = Path('extracted_data')
            extracted_dir.mkdir(exist_ok=True)
            
            # Save the uploaded file
            filename = secure_filename(file.filename)
            file_path = os.path.join(uploads_dir, filename)
            file.save(file_path)
            
            try:
                # Process the file with OCR
                from utils.ocr_processor import OCRProcessor
                ocr = OCRProcessor()
                result = ocr.process_file(file_path)
                
                # Save extracted text to file
                text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
                text_path = os.path.join(extracted_dir, text_filename)
                
                with open(text_path, 'w') as f:
                    f.write(result.get('text', 'No text extracted'))
                
                # Return success with extracted text
                return render_template('ocr_tool.html', 
                                      extracted_text=result.get('text', 'No text extracted'),
                                      original_filename=filename,
                                      text_filename=text_filename)
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
    
    # GET request - show upload form
    return render_template('ocr_tool.html')


@ocr_bp.route('/download_extracted_text/<filename>')
@login_required
def download_extracted_text(filename):
    """Download extracted text from OCR processing"""
    extracted_dir = Path('extracted_data')
    
    # Ensure directory exists
    extracted_dir.mkdir(exist_ok=True)
    
    return send_from_directory(extracted_dir, filename, as_attachment=True)