"""
QQ UI/UX Patch Applicator
Automated system to apply design system fixes across all templates and components
"""
import os
import json
import re
from pathlib import Path
import logging

class UIUXPatchApplicator:
    def __init__(self):
        self.design_system_css = "static/css/traxovo-design-system.css"
        self.consistency_report = "qq_ui_ux_consistency_report.json"
        self.patches_applied = []
        
    def load_consistency_report(self):
        """Load the UI/UX consistency report"""
        with open(self.consistency_report, 'r') as f:
            return json.load(f)
            
    def apply_all_patches(self):
        """Apply all UI/UX consistency patches"""
        report = self.load_consistency_report()
        
        for file_path, clashes in report["detailed_results"].items():
            self.apply_file_patches(file_path, clashes)
            
        # Apply design system import to all HTML templates
        self.inject_design_system_imports()
        
        return self.patches_applied
        
    def apply_file_patches(self, file_path, clashes):
        """Apply specific patches to a file based on detected clashes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            for clash in clashes:
                content = self.apply_specific_patch(content, clash, file_path)
                
            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.patches_applied.append({
                    "file": file_path,
                    "clashes_fixed": clashes,
                    "status": "patched"
                })
                
        except Exception as e:
            logging.warning(f"Could not patch {file_path}: {e}")
            
    def apply_specific_patch(self, content, clash_type, file_path):
        """Apply specific patch based on clash type"""
        if clash_type == "color_scheme_inconsistency":
            return self.fix_color_scheme(content)
        elif clash_type == "inconsistent_spacing_detected":
            return self.fix_spacing_consistency(content)
        elif clash_type == "potential_z_index_conflicts":
            return self.fix_z_index_conflicts(content)
        elif clash_type == "overlapping_positioning":
            return self.fix_overlapping_positioning(content)
        return content
        
    def fix_color_scheme(self, content):
        """Fix color scheme inconsistencies"""
        # Replace common inconsistent colors with design system variables
        color_replacements = {
            '#007bff': 'var(--traxovo-primary)',
            '#28a745': 'var(--traxovo-success)',
            '#dc3545': 'var(--traxovo-error)',
            '#ffc107': 'var(--traxovo-warning)',
            '#17a2b8': 'var(--traxovo-info)',
            '#6c757d': 'var(--traxovo-gray-500)',
            '#343a40': 'var(--traxovo-gray-800)',
            '#f8f9fa': 'var(--traxovo-gray-50)'
        }
        
        for old_color, new_color in color_replacements.items():
            content = content.replace(old_color, new_color)
            
        return content
        
    def fix_spacing_consistency(self, content):
        """Fix spacing inconsistencies"""
        # Replace common spacing patterns with design system variables
        spacing_replacements = {
            'margin: 8px': 'margin: var(--space-sm)',
            'margin: 16px': 'margin: var(--space-md)',
            'margin: 24px': 'margin: var(--space-lg)',
            'padding: 8px': 'padding: var(--space-sm)',
            'padding: 16px': 'padding: var(--space-md)',
            'padding: 24px': 'padding: var(--space-lg)',
            'gap: 8px': 'gap: var(--space-sm)',
            'gap: 16px': 'gap: var(--space-md)',
            'gap: 24px': 'gap: var(--space-lg)'
        }
        
        for old_spacing, new_spacing in spacing_replacements.items():
            content = content.replace(old_spacing, new_spacing)
            
        return content
        
    def fix_z_index_conflicts(self, content):
        """Fix z-index conflicts"""
        # Replace common z-index values with design system variables
        z_index_replacements = {
            'z-index: 1000': 'z-index: var(--z-dropdown)',
            'z-index: 1020': 'z-index: var(--z-sticky)',
            'z-index: 1030': 'z-index: var(--z-fixed)',
            'z-index: 1040': 'z-index: var(--z-modal-backdrop)',
            'z-index: 1050': 'z-index: var(--z-modal)',
            'z-index: 1060': 'z-index: var(--z-popover)',
            'z-index: 1070': 'z-index: var(--z-tooltip)',
            'z-index: 999': 'z-index: var(--z-dropdown)',
            'z-index: 9999': 'z-index: var(--z-modal)'
        }
        
        for old_z, new_z in z_index_replacements.items():
            content = content.replace(old_z, new_z)
            
        return content
        
    def fix_overlapping_positioning(self, content):
        """Fix overlapping positioning issues"""
        # Add CSS Grid/Flexbox classes where appropriate
        if 'position: absolute' in content and 'display: grid' not in content:
            # Replace absolute positioning with grid/flexbox where possible
            content = re.sub(
                r'position:\s*absolute;?\s*top:\s*[^;]+;?\s*left:\s*[^;]+;?',
                'display: flex; align-items: center; justify-content: center;',
                content
            )
            
        return content
        
    def inject_design_system_imports(self):
        """Inject design system CSS import into all HTML templates"""
        templates_dir = Path("templates")
        
        if not templates_dir.exists():
            return
            
        design_system_import = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/traxovo-design-system.css\') }}">'
        
        for template_file in templates_dir.rglob("*.html"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if design system is already imported
                if 'traxovo-design-system.css' in content:
                    continue
                    
                # Find head section and inject import
                if '<head>' in content and design_system_import not in content:
                    content = content.replace(
                        '<head>',
                        f'<head>\n    {design_system_import}'
                    )
                    
                    with open(template_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    self.patches_applied.append({
                        "file": str(template_file),
                        "clashes_fixed": ["design_system_import_added"],
                        "status": "design_system_injected"
                    })
                    
            except Exception as e:
                logging.warning(f"Could not inject design system into {template_file}: {e}")
                
    def generate_patch_report(self):
        """Generate comprehensive patch application report"""
        report = {
            "patch_timestamp": Path(self.consistency_report).stat().st_mtime,
            "total_files_patched": len(self.patches_applied),
            "patch_summary": {
                "design_system_injections": len([p for p in self.patches_applied if "design_system_injected" in p.get("status", "")]),
                "color_scheme_fixes": len([p for p in self.patches_applied if "color_scheme_inconsistency" in str(p.get("clashes_fixed", []))]),
                "spacing_fixes": len([p for p in self.patches_applied if "inconsistent_spacing" in str(p.get("clashes_fixed", []))]),
                "z_index_fixes": len([p for p in self.patches_applied if "z_index_conflicts" in str(p.get("clashes_fixed", []))]),
                "positioning_fixes": len([p for p in self.patches_applied if "overlapping_positioning" in str(p.get("clashes_fixed", []))])
            },
            "patches_applied": self.patches_applied
        }
        
        with open("qq_ui_ux_patch_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        return report

def apply_ui_ux_patches():
    """Apply all UI/UX consistency patches"""
    applicator = UIUXPatchApplicator()
    patches = applicator.apply_all_patches()
    report = applicator.generate_patch_report()
    
    logging.info(f"UI/UX Patch Applicator: Applied patches to {report['total_files_patched']} files")
    logging.info(f"UI/UX Patch Applicator: Color fixes: {report['patch_summary']['color_scheme_fixes']}")
    logging.info(f"UI/UX Patch Applicator: Spacing fixes: {report['patch_summary']['spacing_fixes']}")
    logging.info(f"UI/UX Patch Applicator: Z-index fixes: {report['patch_summary']['z_index_fixes']}")
    logging.info(f"UI/UX Patch Applicator: Positioning fixes: {report['patch_summary']['positioning_fixes']}")
    
    return applicator

if __name__ == "__main__":
    applicator = apply_ui_ux_patches()
    print("🎨 UI/UX patches applied successfully")