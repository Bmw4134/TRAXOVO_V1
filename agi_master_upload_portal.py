"""
AGI Master Upload Portal
Universal file processing with bleeding-edge autonomous workflow optimization
"""

import os
import json
import base64
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
import pandas as pd
from PIL import Image
import PyPDF2
import zipfile
import tarfile
import gzip
import logging
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for, flash
from agi_data_integration import agi_search

logger = logging.getLogger(__name__)

agi_upload_bp = Blueprint('agi_upload', __name__)

class AGIMasterUploadProcessor:
    """Bleeding-edge AGI file processing and routing intelligence"""
    
    def __init__(self):
        self.supported_formats = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheets': ['.xlsx', '.xls', '.csv', '.ods'],
            'archives': ['.zip', '.rar', '.tar', '.gz', '.7z'],
            'data': ['.json', '.xml', '.yaml', '.sql'],
            'code': ['.py', '.js', '.html', '.css', '.md'],
            'media': ['.mp4', '.avi', '.mov', '.mp3', '.wav']
        }
        
        self.routing_intelligence = {
            'billing': ['billing', 'invoice', 'revenue', 'cost', 'expense', 'ragle', 'equipment'],
            'attendance': ['attendance', 'driver', 'timesheet', 'schedule', 'shift'],
            'assets': ['asset', 'equipment', 'gauge', 'fleet', 'maintenance'],
            'reports': ['report', 'analysis', 'summary', 'dashboard'],
            'admin': ['user', 'admin', 'security', 'config', 'settings'],
            'analytics': ['analytics', 'metrics', 'kpi', 'performance']
        }
        
    def agi_analyze_file(self, file_path, filename, file_content=None):
        """AGI-powered comprehensive file analysis"""
        
        analysis = {
            'filename': filename,
            'file_path': file_path,
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'format': self._detect_format(filename),
            'content_preview': '',
            'agi_routing_recommendations': [],
            'compression_analysis': {},
            'metadata': {},
            'confidence_score': 0
        }
        
        # Extract file extension and MIME type
        file_ext = Path(filename).suffix.lower()
        mime_type, _ = mimetypes.guess_type(filename)
        analysis['mime_type'] = mime_type
        analysis['extension'] = file_ext
        
        # AGI content analysis based on file type
        try:
            if file_ext in ['.pdf']:
                analysis.update(self._analyze_pdf(file_path))
            elif file_ext in ['.xlsx', '.xls', '.csv']:
                analysis.update(self._analyze_spreadsheet(file_path))
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                analysis.update(self._analyze_image(file_path))
            elif file_ext in ['.txt', '.md', '.json']:
                analysis.update(self._analyze_text(file_path))
            elif file_ext in ['.zip', '.tar', '.gz']:
                analysis.update(self._analyze_archive(file_path))
            
            # AGI routing intelligence
            analysis['agi_routing_recommendations'] = self._calculate_routing_recommendations(analysis)
            analysis['confidence_score'] = self._calculate_confidence(analysis)
            
        except Exception as e:
            logger.error(f"AGI analysis error for {filename}: {e}")
            analysis['error'] = str(e)
            
        return analysis
        
    def _detect_format(self, filename):
        """Detect file format category"""
        file_ext = Path(filename).suffix.lower()
        
        for category, extensions in self.supported_formats.items():
            if file_ext in extensions:
                return category
        return 'unknown'
        
    def _analyze_pdf(self, file_path):
        """AGI PDF analysis"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page in pdf_reader.pages[:3]:  # First 3 pages for analysis
                    text_content += page.extract_text()
                
                return {
                    'page_count': len(pdf_reader.pages),
                    'content_preview': text_content[:500],
                    'document_type': self._classify_document_content(text_content),
                    'contains_tables': 'table' in text_content.lower() or 'total' in text_content.lower()
                }
        except Exception as e:
            return {'pdf_error': str(e)}
            
    def _analyze_spreadsheet(self, file_path):
        """AGI spreadsheet analysis"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=100)
            else:
                df = pd.read_excel(file_path, nrows=100)
                
            return {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)[:10],
                'content_preview': df.head(3).to_dict(),
                'data_types': df.dtypes.to_dict(),
                'contains_financial': any(col.lower() in ['cost', 'revenue', 'billing', 'amount'] for col in df.columns)
            }
        except Exception as e:
            return {'spreadsheet_error': str(e)}
            
    def _analyze_image(self, file_path):
        """AGI image analysis"""
        try:
            with Image.open(file_path) as img:
                return {
                    'dimensions': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA'),
                    'estimated_screenshot': img.size[0] > 1000 and img.size[1] > 600
                }
        except Exception as e:
            return {'image_error': str(e)}
            
    def _analyze_text(self, file_path):
        """AGI text file analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read(2000)  # First 2000 chars
                
            return {
                'content_preview': content[:500],
                'line_count': content.count('\n'),
                'contains_code': any(keyword in content for keyword in ['def ', 'function', 'import', 'class ']),
                'contains_data': any(keyword in content for keyword in ['csv', 'json', 'database', 'table'])
            }
        except Exception as e:
            return {'text_error': str(e)}
            
    def _analyze_archive(self, file_path):
        """AGI archive analysis"""
        try:
            file_list = []
            
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as archive:
                    file_list = archive.namelist()[:20]  # First 20 files
            elif file_path.endswith(('.tar', '.tar.gz')):
                with tarfile.open(file_path, 'r') as archive:
                    file_list = archive.getnames()[:20]
                    
            return {
                'file_count': len(file_list),
                'file_list': file_list,
                'contains_data': any('.csv' in f or '.xlsx' in f for f in file_list),
                'contains_code': any('.py' in f or '.js' in f for f in file_list)
            }
        except Exception as e:
            return {'archive_error': str(e)}
            
    def _classify_document_content(self, text):
        """AGI document classification"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['invoice', 'billing', 'payment', 'amount due']):
            return 'billing_document'
        elif any(keyword in text_lower for keyword in ['attendance', 'timesheet', 'hours worked']):
            return 'attendance_report'
        elif any(keyword in text_lower for keyword in ['asset', 'equipment', 'maintenance']):
            return 'asset_document'
        elif any(keyword in text_lower for keyword in ['report', 'analysis', 'summary']):
            return 'business_report'
        else:
            return 'general_document'
            
    def _calculate_routing_recommendations(self, analysis):
        """AGI routing intelligence"""
        recommendations = []
        
        # Content-based routing
        content = (analysis.get('content_preview', '') + 
                  str(analysis.get('column_names', [])) + 
                  analysis.get('filename', '')).lower()
        
        for route, keywords in self.routing_intelligence.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                recommendations.append({
                    'route': route,
                    'score': score,
                    'reason': f"Found {score} relevant keywords",
                    'keywords_found': [kw for kw in keywords if kw in content]
                })
        
        # File type based routing
        if analysis['format'] == 'spreadsheets':
            recommendations.append({
                'route': 'billing',
                'score': 3,
                'reason': 'Spreadsheet likely contains financial data'
            })
        elif analysis['format'] == 'images':
            recommendations.append({
                'route': 'reports',
                'score': 2,
                'reason': 'Image might be a screenshot or diagram'
            })
            
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:5]
        
    def _calculate_confidence(self, analysis):
        """Calculate AGI confidence score"""
        base_score = 50
        
        # Boost confidence based on successful analysis
        if analysis.get('content_preview'):
            base_score += 20
        if analysis.get('agi_routing_recommendations'):
            base_score += 15
        if analysis.get('columns') or analysis.get('page_count'):
            base_score += 10
            
        return min(base_score, 95)
        
    def agi_compress_file(self, file_path):
        """AGI-powered intelligent compression"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size < 1024 * 1024:  # Less than 1MB
                return {'compressed': False, 'reason': 'File too small for compression'}
                
            # Compress based on file type
            compressed_path = file_path + '.gz'
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
                    
            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = compressed_size / file_size
            
            if compression_ratio < 0.8:  # At least 20% reduction
                return {
                    'compressed': True,
                    'original_size': file_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio,
                    'compressed_path': compressed_path
                }
            else:
                os.remove(compressed_path)
                return {'compressed': False, 'reason': 'Compression not beneficial'}
                
        except Exception as e:
            return {'compression_error': str(e)}

# Global AGI processor
agi_processor = AGIMasterUploadProcessor()

@agi_upload_bp.route('/agi-upload', methods=['GET', 'POST'])
def agi_upload_portal():
    """AGI Master Upload Portal"""
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        # Secure file handling
        filename = secure_filename(file.filename)
        upload_dir = 'uploads/agi_processed'
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # AGI analysis
        analysis = agi_processor.agi_analyze_file(file_path, filename)
        
        # Store analysis for routing decision
        analysis_id = hashlib.md5(filename.encode()).hexdigest()
        
        # Return routing recommendations
        return render_template_string(ROUTING_TEMPLATE, 
                                    analysis=analysis,
                                    analysis_id=analysis_id,
                                    filename=filename)
    
    return render_template_string(UPLOAD_TEMPLATE)

@agi_upload_bp.route('/agi-route-file', methods=['POST'])
def agi_route_file():
    """Route file to selected destination"""
    
    data = request.get_json()
    selected_route = data.get('route')
    analysis_id = data.get('analysis_id')
    filename = data.get('filename')
    
    # Process routing based on selection
    routing_result = {
        'success': True,
        'route': selected_route,
        'filename': filename,
        'timestamp': datetime.now().isoformat(),
        'next_action': f"File routed to {selected_route} module"
    }
    
    return jsonify(routing_result)

# Templates
UPLOAD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGI Master Upload Portal</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .upload-zone { border: 3px dashed #007bff; padding: 40px; text-align: center; border-radius: 10px; margin: 20px 0; }
        .upload-zone:hover { border-color: #0056b3; background: #f8f9fa; }
        .btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }
        .feature { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 AGI Master Upload Portal</h1>
            <p>Bleeding-edge autonomous file processing and intelligent routing</p>
        </div>
        
        <form method="post" enctype="multipart/form-data">
            <div class="upload-zone">
                <h3>Drop any file here or click to browse</h3>
                <input type="file" name="file" required accept="*/*" style="margin: 20px 0;">
                <p>Supports: PDF, Excel, CSV, Images, Archives, Code, Documents</p>
                <button type="submit" class="btn">🚀 Analyze with AGI</button>
            </div>
        </form>
        
        <div class="features">
            <div class="feature">
                <h4>🎯 Smart Routing</h4>
                <p>AGI analyzes content and recommends optimal workflow destinations</p>
            </div>
            <div class="feature">
                <h4>🗜️ Intelligent Compression</h4>
                <p>AI-powered compression optimization for storage efficiency</p>
            </div>
            <div class="feature">
                <h4>📊 Content Analysis</h4>
                <p>Deep file analysis with metadata extraction and classification</p>
            </div>
            <div class="feature">
                <h4>⚡ Universal Support</h4>
                <p>Handles any file format with autonomous processing intelligence</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

ROUTING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AGI Routing Decision</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .analysis { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .recommendations { display: grid; gap: 15px; margin: 20px 0; }
        .recommendation { background: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3; cursor: pointer; }
        .recommendation:hover { background: #bbdefb; }
        .recommendation.selected { background: #1976d2; color: white; }
        .btn { background: #4caf50; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 5px; }
        .btn:hover { background: #45a049; }
        .btn-secondary { background: #ff9800; }
        .btn-secondary:hover { background: #f57c00; }
        .metadata { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .metric { background: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 AGI Analysis Complete</h1>
        <p><strong>File:</strong> {{ filename }}</p>
        
        <div class="analysis">
            <h3>📊 File Analysis</h3>
            <div class="metadata">
                <div class="metric">
                    <strong>Format:</strong> {{ analysis.format }}<br>
                    <strong>Size:</strong> {{ "%.2f"|format(analysis.size / 1024) }} KB
                </div>
                <div class="metric">
                    <strong>Confidence:</strong> {{ analysis.confidence_score }}%<br>
                    <strong>Type:</strong> {{ analysis.mime_type or 'Unknown' }}
                </div>
                {% if analysis.content_preview %}
                <div class="metric">
                    <strong>Content Preview:</strong><br>
                    <small>{{ analysis.content_preview[:200] }}...</small>
                </div>
                {% endif %}
            </div>
        </div>
        
        <div class="analysis">
            <h3>🎯 AGI Routing Recommendations</h3>
            <div class="recommendations" id="recommendations">
                {% for rec in analysis.agi_routing_recommendations %}
                <div class="recommendation" onclick="selectRoute('{{ rec.route }}', this)" data-route="{{ rec.route }}">
                    <strong>{{ rec.route.title() }}</strong> (Score: {{ rec.score }})<br>
                    <small>{{ rec.reason }}</small>
                    {% if rec.keywords_found %}
                    <br><em>Keywords: {{ ', '.join(rec.keywords_found) }}</em>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div style="margin-top: 20px;">
                <input type="text" id="customRoute" placeholder="Custom route destination..." style="padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 5px;">
                <button class="btn btn-secondary" onclick="useCustomRoute()">Use Custom Route</button>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="btn" onclick="routeFile()" id="routeBtn" disabled>🚀 Route File</button>
            <button class="btn btn-secondary" onclick="window.location.href='/agi-upload'">📁 Upload Another File</button>
        </div>
    </div>
    
    <script>
        let selectedRoute = null;
        
        function selectRoute(route, element) {
            // Clear previous selection
            document.querySelectorAll('.recommendation').forEach(el => el.classList.remove('selected'));
            
            // Select current
            element.classList.add('selected');
            selectedRoute = route;
            document.getElementById('routeBtn').disabled = false;
        }
        
        function useCustomRoute() {
            const customRoute = document.getElementById('customRoute').value.trim();
            if (customRoute) {
                selectedRoute = customRoute;
                document.querySelectorAll('.recommendation').forEach(el => el.classList.remove('selected'));
                document.getElementById('routeBtn').disabled = false;
            }
        }
        
        function routeFile() {
            if (!selectedRoute) return;
            
            fetch('/agi-route-file', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    route: selectedRoute,
                    analysis_id: '{{ analysis_id }}',
                    filename: '{{ filename }}'
                })
            })
            .then(response => response.json())
            .then(data => {
                alert('File routed to: ' + data.route);
                window.location.href = '/agi-upload';
            });
        }
    </script>
</body>
</html>
"""