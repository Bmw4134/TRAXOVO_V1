"""
Template Audit Tool

This script analyzes the Flask application to identify used and unused templates,
helping to keep the template directory clean and organized.
"""

import os
import re
import sys
import logging
import inspect
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def collect_all_templates():
    """Collect all HTML templates in the templates directory"""
    logger.info("Collecting all templates...")
    
    all_templates = set()
    template_dir = os.path.join(os.getcwd(), 'templates')
    
    if not os.path.exists(template_dir):
        logger.error(f"Template directory not found: {template_dir}")
        return all_templates
    
    for root, _, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, template_dir)
                all_templates.add(rel_path.replace('\\', '/'))
    
    logger.info(f"Found {len(all_templates)} templates")
    return all_templates

def extract_templates_from_file(file_path):
    """Extract template references from a Python file"""
    templates = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find render_template calls
        render_calls = re.findall(r'render_template\((.*?)\)', content)
        for call in render_calls:
            # Extract the template path
            path_match = re.findall(r'["\']([^"\']+\.html)["\']', call)
            templates.update(path_match)
            
        # Find direct references to templates in blueprints
        template_refs = re.findall(r'template_folder\s*=\s*["\']([^"\']+)["\']', content)
        if template_refs:
            logger.debug(f"Template folder reference in {file_path}: {template_refs}")
    
    except Exception as e:
        logger.error(f"Error extracting templates from {file_path}: {str(e)}")
    
    return templates

def collect_used_templates():
    """Collect all templates referenced in Python files"""
    logger.info("Collecting used templates...")
    
    used_templates = set()
    
    # Directories to scan
    dirs_to_scan = ['routes', 'utils', '.', 'admin', 'attendance']
    
    for dir_path in dirs_to_scan:
        dir_to_scan = os.path.join(os.getcwd(), dir_path)
        
        if not os.path.exists(dir_to_scan):
            logger.debug(f"Directory not found: {dir_to_scan}")
            continue
            
        logger.debug(f"Scanning directory: {dir_to_scan}")
        
        if os.path.isdir(dir_to_scan):
            for root, _, files in os.walk(dir_to_scan):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        templates = extract_templates_from_file(file_path)
                        used_templates.update(templates)
        elif os.path.isfile(dir_to_scan) and dir_to_scan.endswith('.py'):
            templates = extract_templates_from_file(dir_to_scan)
            used_templates.update(templates)
    
    logger.info(f"Found {len(used_templates)} used templates")
    return used_templates

def create_archive_dir():
    """Create the archive directory for unused templates"""
    archive_dir = os.path.join(os.getcwd(), 'templates', 'archived')
    os.makedirs(archive_dir, exist_ok=True)
    return archive_dir

def move_template_to_archive(template_path):
    """Move an unused template to the archive directory"""
    template_dir = os.path.join(os.getcwd(), 'templates')
    full_path = os.path.join(template_dir, template_path)
    
    if not os.path.exists(full_path):
        logger.warning(f"Template not found: {full_path}")
        return False
    
    archive_dir = create_archive_dir()
    target_path = os.path.join(archive_dir, os.path.basename(template_path))
    
    # Create subdirectories in archive if needed
    if os.path.dirname(template_path):
        sub_archive_dir = os.path.join(archive_dir, os.path.dirname(template_path))
        os.makedirs(sub_archive_dir, exist_ok=True)
        target_path = os.path.join(sub_archive_dir, os.path.basename(template_path))
    
    try:
        # Move the file
        os.rename(full_path, target_path)
        logger.info(f"Moved template to archive: {template_path}")
        return True
    except Exception as e:
        logger.error(f"Error moving template {template_path} to archive: {str(e)}")
        return False

def run_audit(move_unused=True):
    """Run the template audit"""
    logger.info("Starting template audit...")
    
    all_templates = collect_all_templates()
    used_templates = collect_used_templates()
    
    # Calculate results
    unused_templates = all_templates - used_templates
    missing_templates = used_templates - all_templates
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(os.getcwd(), f"template_audit_report_{timestamp}.md")
    
    with open(report_path, "w") as f:
        f.write("# 🧾 Template Audit Report\n\n")
        
        f.write("## ✅ Used Templates\n")
        for t in sorted(all_templates & used_templates):
            f.write(f"- {t}\n")
        
        f.write("\n## ❌ Unused Templates\n")
        for t in sorted(unused_templates):
            f.write(f"- {t}\n")
        
        f.write("\n## ⚠️ Missing Templates (Used but Not Found)\n")
        for t in sorted(missing_templates):
            f.write(f"- {t}\n")
    
    logger.info(f"Audit report generated: {report_path}")
    
    # Move unused templates to archive
    if move_unused and unused_templates:
        logger.info("Moving unused templates to archive...")
        
        moved_count = 0
        for template in unused_templates:
            if move_template_to_archive(template):
                moved_count += 1
        
        logger.info(f"Moved {moved_count} unused templates to archive")
    
    return {
        "all_templates": len(all_templates),
        "used_templates": len(all_templates & used_templates),
        "unused_templates": len(unused_templates),
        "missing_templates": len(missing_templates),
        "report_path": report_path
    }

if __name__ == "__main__":
    # Get command line arguments
    move_unused = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "no-move":
        move_unused = False
        logger.info("Audit only mode - templates will not be moved")
    
    # Run the audit
    results = run_audit(move_unused)
    
    # Print summary
    print("\nTemplate Audit Summary:")
    print(f"Total Templates: {results['all_templates']}")
    print(f"Used Templates: {results['used_templates']}")
    print(f"Unused Templates: {results['unused_templates']}")
    print(f"Missing Templates: {results['missing_templates']}")
    print(f"Report: {results['report_path']}")