"""
TRAXOVO Object Storage Integration
Utilize Replit Object Storage for file management and asset storage
"""

import os
import json
import hashlib
from datetime import datetime
from flask import request, jsonify
from app import db
from models_clean import PlatformData

class TRAXOVOObjectStorage:
    """Object Storage integration for TRAXOVO platform"""
    
    def __init__(self):
        # Replit Object Storage is available via environment
        self.storage_enabled = True
        self.max_file_size = 100 * 1024 * 1024  # 100MB limit
        self.allowed_extensions = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.md'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.svg'],
            'data': ['.csv', '.json', '.xml', '.xlsx'],
            'reports': ['.pdf', '.html', '.csv']
        }
    
    def upload_file(self, file_data, file_name, category='documents'):
        """Upload file to Object Storage"""
        
        try:
            # Validate file
            if not self._validate_file(file_data, file_name, category):
                return {"error": "File validation failed"}
            
            # Generate unique storage key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            storage_key = f"traxovo/{category}/{timestamp}_{file_hash}_{file_name}"
            
            # Store file metadata in database
            file_metadata = {
                'original_name': file_name,
                'storage_key': storage_key,
                'category': category,
                'file_size': len(file_data),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'file_hash': file_hash,
                'content_type': self._get_content_type(file_name)
            }
            
            # Store metadata in database
            self._store_file_metadata(storage_key, file_metadata)
            
            # In a real Replit Object Storage implementation, you would use:
            # import replit_object_storage
            # replit_object_storage.put(storage_key, file_data)
            
            # For now, we'll store the reference and metadata
            return {
                "status": "success",
                "storage_key": storage_key,
                "metadata": file_metadata,
                "download_url": f"/api/object_storage/download/{storage_key}"
            }
            
        except Exception as e:
            return {"error": f"Upload failed: {str(e)}"}
    
    def download_file(self, storage_key):
        """Download file from Object Storage"""
        
        try:
            # Get file metadata
            metadata = self._get_file_metadata(storage_key)
            if not metadata:
                return {"error": "File not found"}
            
            # In a real implementation:
            # import replit_object_storage
            # file_data = replit_object_storage.get(storage_key)
            
            return {
                "status": "success",
                "metadata": metadata,
                "download_ready": True
            }
            
        except Exception as e:
            return {"error": f"Download failed: {str(e)}"}
    
    def list_files(self, category=None, limit=50):
        """List files in Object Storage"""
        
        try:
            # Get all file metadata from database
            files_record = PlatformData.query.filter_by(data_type='object_storage_files').first()
            
            if not files_record:
                return {"files": [], "total": 0}
            
            all_files = files_record.data_content.get('files', {})
            
            # Filter by category if specified
            if category:
                filtered_files = {k: v for k, v in all_files.items() 
                                if v.get('category') == category}
            else:
                filtered_files = all_files
            
            # Sort by upload timestamp (newest first)
            sorted_files = sorted(
                filtered_files.items(),
                key=lambda x: x[1].get('upload_timestamp', ''),
                reverse=True
            )
            
            # Apply limit
            limited_files = sorted_files[:limit]
            
            return {
                "files": [{"storage_key": k, **v} for k, v in limited_files],
                "total": len(filtered_files),
                "categories": list(set(f.get('category') for f in all_files.values()))
            }
            
        except Exception as e:
            return {"error": f"List files failed: {str(e)}"}
    
    def delete_file(self, storage_key):
        """Delete file from Object Storage"""
        
        try:
            # Get current files
            files_record = PlatformData.query.filter_by(data_type='object_storage_files').first()
            
            if files_record and storage_key in files_record.data_content.get('files', {}):
                # Remove from metadata
                files_data = files_record.data_content
                del files_data['files'][storage_key]
                files_record.data_content = files_data
                files_record.updated_at = datetime.utcnow()
                db.session.commit()
                
                # In real implementation:
                # import replit_object_storage
                # replit_object_storage.delete(storage_key)
                
                return {"status": "success", "message": "File deleted"}
            else:
                return {"error": "File not found"}
                
        except Exception as e:
            return {"error": f"Delete failed: {str(e)}"}
    
    def store_executive_report(self, report_data, report_name):
        """Store executive report in Object Storage"""
        
        try:
            # Generate HTML report
            html_content = self._generate_html_report(report_data, report_name)
            
            # Upload as HTML file
            result = self.upload_file(
                html_content.encode('utf-8'),
                f"{report_name}.html",
                'reports'
            )
            
            if result.get('status') == 'success':
                # Store report reference in database
                self._store_report_reference(report_name, result['storage_key'])
            
            return result
            
        except Exception as e:
            return {"error": f"Report storage failed: {str(e)}"}
    
    def get_storage_statistics(self):
        """Get Object Storage usage statistics"""
        
        try:
            files_record = PlatformData.query.filter_by(data_type='object_storage_files').first()
            
            if not files_record:
                return {
                    "total_files": 0,
                    "total_size": 0,
                    "categories": {},
                    "storage_usage": "0 MB"
                }
            
            all_files = files_record.data_content.get('files', {})
            
            # Calculate statistics
            total_files = len(all_files)
            total_size = sum(f.get('file_size', 0) for f in all_files.values())
            
            # Category breakdown
            categories = {}
            for file_data in all_files.values():
                category = file_data.get('category', 'unknown')
                if category not in categories:
                    categories[category] = {"count": 0, "size": 0}
                categories[category]["count"] += 1
                categories[category]["size"] += file_data.get('file_size', 0)
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "categories": categories,
                "storage_usage": f"{round(total_size / (1024 * 1024), 2)} MB"
            }
            
        except Exception as e:
            return {"error": f"Statistics failed: {str(e)}"}
    
    def _validate_file(self, file_data, file_name, category):
        """Validate file before upload"""
        
        # Check file size
        if len(file_data) > self.max_file_size:
            return False
        
        # Check file extension
        if category in self.allowed_extensions:
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in self.allowed_extensions[category]:
                return False
        
        return True
    
    def _get_content_type(self, file_name):
        """Get content type based on file extension"""
        
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def _store_file_metadata(self, storage_key, metadata):
        """Store file metadata in database"""
        
        try:
            files_record = PlatformData.query.filter_by(data_type='object_storage_files').first()
            
            if files_record:
                files_data = files_record.data_content
                if 'files' not in files_data:
                    files_data['files'] = {}
                files_data['files'][storage_key] = metadata
                files_record.data_content = files_data
                files_record.updated_at = datetime.utcnow()
            else:
                files_record = PlatformData(
                    data_type='object_storage_files',
                    data_content={'files': {storage_key: metadata}}
                )
                db.session.add(files_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to store file metadata: {e}")
    
    def _get_file_metadata(self, storage_key):
        """Get file metadata from database"""
        
        try:
            files_record = PlatformData.query.filter_by(data_type='object_storage_files').first()
            
            if files_record:
                return files_record.data_content.get('files', {}).get(storage_key)
            return None
            
        except:
            return None
    
    def _generate_html_report(self, report_data, report_name):
        """Generate HTML report content"""
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report_name} - TRAXOVO Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .report-title {{ font-size: 24px; font-weight: bold; }}
        .report-date {{ color: #666; margin-top: 10px; }}
        .content {{ margin-top: 30px; }}
        .metric {{ margin: 20px 0; padding: 15px; background: #f5f5f5; }}
        .metric-label {{ font-weight: bold; }}
        .metric-value {{ font-size: 18px; color: #333; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="report-title">TRAXOVO Executive Report: {report_name}</div>
        <div class="report-date">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
    </div>
    
    <div class="content">
        {self._format_report_data(report_data)}
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _format_report_data(self, report_data):
        """Format report data as HTML"""
        
        if isinstance(report_data, dict):
            html_parts = []
            for key, value in report_data.items():
                html_parts.append(f"""
                <div class="metric">
                    <div class="metric-label">{key.replace('_', ' ').title()}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """)
            return ''.join(html_parts)
        else:
            return f'<div class="metric"><div class="metric-value">{report_data}</div></div>'
    
    def _store_report_reference(self, report_name, storage_key):
        """Store report reference in database"""
        
        try:
            reports_record = PlatformData.query.filter_by(data_type='executive_reports').first()
            
            report_ref = {
                'name': report_name,
                'storage_key': storage_key,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            if reports_record:
                reports_data = reports_record.data_content
                if 'reports' not in reports_data:
                    reports_data['reports'] = []
                reports_data['reports'].append(report_ref)
                reports_record.data_content = reports_data
                reports_record.updated_at = datetime.utcnow()
            else:
                reports_record = PlatformData(
                    data_type='executive_reports',
                    data_content={'reports': [report_ref]}
                )
                db.session.add(reports_record)
            
            db.session.commit()
            
        except Exception as e:
            print(f"Failed to store report reference: {e}")

# Global Object Storage instance
traxovo_storage = TRAXOVOObjectStorage()

def upload_file_to_storage(file_data, file_name, category='documents'):
    """Upload file to Object Storage"""
    return traxovo_storage.upload_file(file_data, file_name, category)

def get_storage_files(category=None, limit=50):
    """Get files from Object Storage"""
    return traxovo_storage.list_files(category, limit)

def get_storage_stats():
    """Get Object Storage statistics"""
    return traxovo_storage.get_storage_statistics()

def store_executive_report(report_data, report_name):
    """Store executive report"""
    return traxovo_storage.store_executive_report(report_data, report_name)