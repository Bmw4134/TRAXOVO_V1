"""
Data File Organizer Script

This script organizes CSV and Excel files into a structured directory system
based on their content, file type, and embedded dates using machine learning techniques.
"""

import os
import re
import pandas as pd
import numpy as np
import shutil
import logging
import datetime
import json
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File type categories
FILE_CATEGORIES = {
    'driving_history': ['driving', 'history', 'drive', 'driver', 'DrivingHistory'],
    'activity_detail': ['activity', 'detail', 'ActivityDetail'],
    'assets_time': ['assets', 'time', 'on', 'site', 'AssetsTimeOnSite'],
    'daily_usage': ['daily', 'usage', 'DailyUsage'],
    'fleet_utilization': ['fleet', 'utilization', 'FleetUtilization'],
    'billing_allocation': ['billing', 'allocation', 'EQMO', 'BILLING'],
    'monthly': ['monthly', 'month', 'MTD'],
    'employee': ['employee', 'Consolidated_Employee']
}

class SmartFileOrganizer:
    """Smart File Organizer with ML-based categorization"""
    
    def __init__(self, source_dir="attached_assets", target_dir="organized_data"):
        """
        Initialize the organizer
        
        Args:
            source_dir (str): Directory containing source files
            target_dir (str): Directory where organized files will be stored
        """
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.file_metadata = {}
        self.categorized_files = defaultdict(list)
        self.date_extracted_files = defaultdict(list)
        
    def scan_files(self):
        """Scan directory for CSV and Excel files"""
        logger.info(f"Scanning {self.source_dir} for CSV and Excel files...")
        
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith(('.csv', '.xlsx', '.xls')):
                    file_path = os.path.join(root, file)
                    self.file_metadata[file_path] = {
                        'filename': file,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path),
                        'category': None,
                        'date': None,
                        'content_hash': None
                    }
        
        logger.info(f"Found {len(self.file_metadata)} CSV and Excel files")
        return self.file_metadata
    
    def analyze_files(self):
        """Analyze files to extract metadata and categorize them"""
        logger.info("Analyzing files for categorization...")
        
        for file_path in self.file_metadata:
            try:
                # Determine category based on filename
                category = self._categorize_by_name(file_path)
                self.file_metadata[file_path]['category'] = category
                self.categorized_files[category].append(file_path)
                
                # Extract date from filename or content
                date = self._extract_date(file_path)
                self.file_metadata[file_path]['date'] = date
                if date:
                    self.date_extracted_files[date].append(file_path)
                
                # Generate content hash for duplicate detection
                self.file_metadata[file_path]['content_hash'] = self._generate_content_hash(file_path)
                
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {str(e)}")
        
        return self.file_metadata
    
    def _categorize_by_name(self, file_path):
        """Categorize file based on its name"""
        filename = os.path.basename(file_path).lower()
        
        # Try to match with known categories
        for category, keywords in FILE_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in filename:
                    return category
        
        # If we can't categorize by name, try to peek at content
        try:
            if file_path.endswith('.csv'):
                # Use on_bad_lines='skip' for newer pandas versions
                df = pd.read_csv(file_path, nrows=5, on_bad_lines='skip')
            else:  # Excel
                df = pd.read_excel(file_path, nrows=5)
                
            # Check column names for category hints
            columns = ' '.join(df.columns).lower()
            for category, keywords in FILE_CATEGORIES.items():
                for keyword in keywords:
                    if keyword.lower() in columns:
                        return category
        except Exception as e:
            logger.debug(f"Error categorizing {file_path}: {str(e)}")
        
        return 'uncategorized'
    
    def _extract_date(self, file_path):
        """Extract date from filename or file content"""
        filename = os.path.basename(file_path)
        
        # Try to find date patterns in filename
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(\d{2}\.\d{2}\.\d{4})',  # MM.DD.YYYY
            r'_(\d{8})_',  # _YYYYMMDD_
            r'(\d{2}_\d{2}_\d{4})',  # MM_DD_YYYY
            r'(\d{4})[-_\.]?(\d{2})[-_\.]?(\d{2})',  # YYYYMMDD with optional separators
            r'MAY[-_ ](\d{1,2})',  # MAY DD 
            r'APR[-_ ](\d{1,2})',  # APR DD
            r'MAR[-_ ](\d{1,2})',  # MAR DD
            r'(\d{1,2})[-_ ](\d{1,2})[-_ ](\d{4})',  # M-D-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    # Handle different date formats
                    if pattern == r'(\d{4}-\d{2}-\d{2})':
                        return match.group(1)
                    elif pattern == r'(\d{2}-\d{2}-\d{4})':
                        parts = match.group(1).split('-')
                        return f"{parts[2]}-{parts[0]}-{parts[1]}"
                    elif pattern == r'MAY[-_ ](\d{1,2})' or pattern == r'APR[-_ ](\d{1,2})' or pattern == r'MAR[-_ ](\d{1,2})':
                        month = {'MAY': '05', 'APR': '04', 'MAR': '03'}
                        month_name = filename[match.start():match.start()+3].upper()
                        day = match.group(1).zfill(2)
                        return f"2025-{month[month_name]}-{day}"
                    elif pattern == r'(\d{1,2})[-_ ](\d{1,2})[-_ ](\d{4})':
                        m, d, y = match.groups()
                        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                    else:
                        # Try to parse using pandas
                        return pd.to_datetime(match.group(0)).strftime('%Y-%m-%d')
                except Exception as e:
                    logger.debug(f"Error parsing date {match.group(0)}: {str(e)}")
                    continue
        
        # If we can't find date in filename, try to peek at content
        try:
            if file_path.endswith('.csv'):
                # Use on_bad_lines='skip' for newer pandas versions
                df = pd.read_csv(file_path, nrows=5, on_bad_lines='skip')
            else:  # Excel
                df = pd.read_excel(file_path, nrows=5)
                
            # Look for date columns
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            if date_columns and not df[date_columns[0]].empty:
                try:
                    date_val = pd.to_datetime(df[date_columns[0]].iloc[0])
                    return date_val.strftime('%Y-%m-%d')
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error extracting date from {file_path}: {str(e)}")
        
        return None
    
    def _generate_content_hash(self, file_path):
        """Generate a hash based on file content for duplicate detection"""
        try:
            if file_path.endswith('.csv'):
                # Use on_bad_lines='skip' for newer pandas versions
                df = pd.read_csv(file_path, nrows=100, on_bad_lines='skip')
            else:  # Excel
                df = pd.read_excel(file_path, nrows=100)
                
            # Sample the dataframe to generate a content signature
            sample = df.sample(min(len(df), 10)) if len(df) > 0 else df
            content_str = sample.to_string()
            return hash(content_str)
        except Exception as e:
            logger.debug(f"Error generating content hash for {file_path}: {str(e)}")
            # If we can't read the file, use file size and name as hash
            return hash(f"{os.path.basename(file_path)}_{os.path.getsize(file_path)}")
    
    def find_similar_files(self, threshold=0.8):
        """Find similar files based on content and metadata"""
        logger.info("Finding similar files based on content...")
        
        # Prepare content-based features
        filenames = list(self.file_metadata.keys())
        filename_texts = [os.path.basename(f) for f in filenames]
        
        # Use TF-IDF to vectorize filenames
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 5))
        tfidf_matrix = vectorizer.fit_transform(filename_texts)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find similar pairs
        similar_pairs = []
        for i in range(len(filenames)):
            for j in range(i+1, len(filenames)):
                if similarity_matrix[i, j] > threshold:
                    similar_pairs.append((filenames[i], filenames[j], similarity_matrix[i, j]))
        
        # Check for content hash duplicates
        hash_groups = defaultdict(list)
        for file_path, metadata in self.file_metadata.items():
            if metadata['content_hash']:
                hash_groups[metadata['content_hash']].append(file_path)
        
        duplicate_groups = [files for hash_val, files in hash_groups.items() if len(files) > 1]
        
        return {
            'similar_pairs': similar_pairs,
            'duplicate_groups': duplicate_groups
        }
    
    def organize_files(self, create_symlinks=False):
        """Organize files into a structured directory system"""
        logger.info(f"Organizing files into {self.target_dir}...")
        
        # Create target directory if it doesn't exist
        os.makedirs(self.target_dir, exist_ok=True)
        
        # Create category directories
        for category in set([meta['category'] for meta in self.file_metadata.values()]):
            category_dir = os.path.join(self.target_dir, category)
            os.makedirs(category_dir, exist_ok=True)
        
        # Create date directories for dated files
        for date in self.date_extracted_files:
            for category in set([self.file_metadata[f]['category'] for f in self.date_extracted_files[date]]):
                date_dir = os.path.join(self.target_dir, category, date)
                os.makedirs(date_dir, exist_ok=True)
        
        # Move or symlink files to appropriate directories
        for file_path, metadata in self.file_metadata.items():
            category = metadata['category']
            date = metadata['date']
            
            if date:
                target_dir = os.path.join(self.target_dir, category, date)
            else:
                target_dir = os.path.join(self.target_dir, category)
            
            target_path = os.path.join(target_dir, metadata['filename'])
            
            if create_symlinks:
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.symlink(file_path, target_path)
                logger.info(f"Created symlink: {target_path} -> {file_path}")
            else:
                shutil.copy2(file_path, target_path)
                logger.info(f"Copied: {file_path} -> {target_path}")
        
        return self.target_dir
    
    def generate_report(self):
        """Generate a summary report of the file organization"""
        report = {
            'total_files': len(self.file_metadata),
            'categories': {cat: len(files) for cat, files in self.categorized_files.items()},
            'dates': {date: len(files) for date, files in self.date_extracted_files.items()},
            'organization_structure': self._get_directory_structure(self.target_dir)
        }
        
        # Save report to JSON
        report_path = os.path.join(self.target_dir, 'organization_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print a summary
        print("\n\n==== FILE ORGANIZATION SUMMARY ====")
        print(f"Total files processed: {report['total_files']}")
        print("\nFiles by category:")
        for category, count in report['categories'].items():
            print(f"  - {category}: {count} files")
        
        print("\nFiles by date:")
        for date, count in list(report['dates'].items())[:10]:  # Show first 10 dates
            print(f"  - {date}: {count} files")
        
        if len(report['dates']) > 10:
            print(f"  - ... and {len(report['dates']) - 10} more dates")
        
        logger.info(f"Report generated at {report_path}")
        return report
    
    def _get_directory_structure(self, rootdir):
        """Helper to get directory structure recursively"""
        structure = {}
        for item in os.listdir(rootdir):
            item_path = os.path.join(rootdir, item)
            if os.path.isdir(item_path):
                structure[item] = self._get_directory_structure(item_path)
            else:
                structure[item] = None
        return structure


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Smart File Organizer')
    parser.add_argument('--source', default='attached_assets', help='Source directory containing files to organize')
    parser.add_argument('--target', default='organized_data', help='Target directory where organized files will be stored')
    parser.add_argument('--symlinks', action='store_true', help='Create symlinks instead of copying files')
    args = parser.parse_args()
    
    print(f"Starting file organization from {args.source} to {args.target}")
    print(f"Using {'symlinks' if args.symlinks else 'file copies'}")
    
    # Create and run the organizer
    organizer = SmartFileOrganizer(args.source, args.target)
    organizer.scan_files()
    organizer.analyze_files()
    
    # Find similar files
    similarity_report = organizer.find_similar_files()
    print(f"Found {len(similarity_report['duplicate_groups'])} duplicate groups")
    print(f"Found {len(similarity_report['similar_pairs'])} similar file pairs")
    
    # Organize files
    organizer.organize_files(create_symlinks=args.symlinks)
    
    # Generate report
    report = organizer.generate_report()
    
    print(f"\nOrganization complete! Files organized in {args.target}")
    print(f"See {os.path.join(args.target, 'organization_report.json')} for full details")