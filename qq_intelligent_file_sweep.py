"""
QQ Intelligent File Sweep System
Advanced dependency analysis and bloat removal with visual reporting
"""

import os
import ast
import json
import re
from collections import defaultdict
from datetime import datetime

class QQIntelligentFileSweep:
    """Quantum-enhanced file analysis and cleanup system"""
    
    def __init__(self):
        self.dependency_graph = defaultdict(set)
        self.file_usage = defaultdict(int)
        self.bloat_analysis = {}
        self.core_files = set()
        self.redundant_files = set()
        self.safe_to_remove = set()
        
    def analyze_codebase(self):
        """Comprehensive codebase analysis"""
        print("🔮 QQ INTELLIGENT FILE SWEEP ANALYSIS")
        print("="*60)
        
        # Scan all Python files
        python_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        print(f"📊 Analyzing {len(python_files)} Python files...")
        
        # Build dependency graph
        for file in python_files:
            self._analyze_file_dependencies(file)
        
        # Analyze templates
        self._analyze_template_usage()
        
        # Identify core vs bloat
        self._identify_core_files()
        self._identify_bloat_files()
        
        # Generate comprehensive report
        return self._generate_sweep_report()
    
    def _analyze_file_dependencies(self, filename):
        """Analyze imports and dependencies in a Python file"""
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse AST for imports
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self._track_dependency(filename, alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._track_dependency(filename, node.module)
            except:
                # Fallback to regex for problematic files
                self._regex_import_analysis(filename, content)
                
        except Exception as e:
            print(f"⚠️  Error analyzing {filename}: {e}")
    
    def _track_dependency(self, filename, import_name):
        """Track dependency relationships"""
        # Check if it's a local module
        local_file = f"{import_name}.py"
        if os.path.exists(local_file):
            self.dependency_graph[filename].add(local_file)
            self.file_usage[local_file] += 1
    
    def _regex_import_analysis(self, filename, content):
        """Regex-based import analysis for complex files"""
        import_patterns = [
            r'from\s+(\w+)\s+import',
            r'import\s+(\w+)',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                local_file = f"{match}.py"
                if os.path.exists(local_file):
                    self.dependency_graph[filename].add(local_file)
                    self.file_usage[local_file] += 1
    
    def _analyze_template_usage(self):
        """Analyze template file usage"""
        if not os.path.exists('templates'):
            return
            
        template_files = os.listdir('templates')
        python_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        for template in template_files:
            template_name = template
            used = False
            
            for py_file in python_files:
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if template_name in content:
                            used = True
                            self.file_usage[f"templates/{template}"] += 1
                except:
                    pass
            
            if not used:
                self.safe_to_remove.add(f"templates/{template}")
    
    def _identify_core_files(self):
        """Identify absolutely essential files"""
        essential_patterns = [
            'main.py',
            'app.py',
            'routes.py',
            'models.py',
            'qq_*.py',
            'quantum_*.py',
            'asi_*.py',
            'executive_*.py',
            'radio_map_*.py'
        ]
        
        all_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        for file in all_files:
            for pattern in essential_patterns:
                if self._matches_pattern(file, pattern):
                    self.core_files.add(file)
                    break
    
    def _identify_bloat_files(self):
        """Identify redundant and bloat files"""
        all_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        for file in all_files:
            if file in self.core_files:
                continue
                
            # Check usage frequency
            usage_count = self.file_usage.get(file, 0)
            
            # Identify potential bloat
            if usage_count == 0:
                self.safe_to_remove.add(file)
            elif usage_count < 2 and self._is_redundant_functionality(file):
                self.redundant_files.add(file)
    
    def _is_redundant_functionality(self, filename):
        """Check if file contains redundant functionality"""
        redundant_indicators = [
            'test_',
            '_test.py',
            'debug_',
            '_debug.py',
            'backup_',
            '_backup.py',
            'old_',
            '_old.py',
            'legacy_',
            'temp_',
            'scratch_',
            'draft_'
        ]
        
        return any(indicator in filename for indicator in redundant_indicators)
    
    def _matches_pattern(self, filename, pattern):
        """Check if filename matches wildcard pattern"""
        if '*' in pattern:
            prefix = pattern.split('*')[0]
            suffix = pattern.split('*')[1] if len(pattern.split('*')) > 1 else ''
            return filename.startswith(prefix) and filename.endswith(suffix)
        return filename == pattern
    
    def _generate_sweep_report(self):
        """Generate comprehensive sweep analysis report"""
        total_files = len([f for f in os.listdir('.') if f.endswith('.py')])
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_python_files': total_files,
            'core_files': len(self.core_files),
            'safe_to_remove': len(self.safe_to_remove),
            'redundant_files': len(self.redundant_files),
            'dependency_chains': len(self.dependency_graph),
            'file_details': {
                'core_files': list(self.core_files),
                'safe_to_remove': list(self.safe_to_remove),
                'redundant_files': list(self.redundant_files),
                'dependency_graph': {k: list(v) for k, v in self.dependency_graph.items()},
                'usage_stats': dict(self.file_usage)
            }
        }
        
        return report
    
    def execute_intelligent_cleanup(self, report):
        """Execute safe cleanup based on analysis"""
        print("\n🧹 EXECUTING INTELLIGENT CLEANUP")
        print("="*50)
        
        # Create cleanup archive
        archive_dir = 'qq_intelligent_archive'
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
        
        removed_count = 0
        
        # Remove safe files
        for file in self.safe_to_remove:
            if os.path.exists(file):
                if file.startswith('templates/'):
                    # Handle template files
                    archive_templates = f"{archive_dir}/templates"
                    if not os.path.exists(archive_templates):
                        os.makedirs(archive_templates)
                    os.rename(file, f"{archive_templates}/{os.path.basename(file)}")
                else:
                    os.rename(file, f"{archive_dir}/{file}")
                removed_count += 1
                print(f"🗑️  Archived: {file}")
        
        print(f"\n✅ Cleanup complete: {removed_count} files archived")
        print(f"📁 Files preserved in: {archive_dir}")
        
        return removed_count
    
    def display_visual_report(self, report):
        """Display visual analysis report"""
        print("\n📊 QQ INTELLIGENT FILE ANALYSIS REPORT")
        print("="*60)
        
        print(f"📈 Total Files Analyzed: {report['total_python_files']}")
        print(f"🔥 Core Files (Keep): {report['core_files']}")
        print(f"🗑️  Safe to Remove: {report['safe_to_remove']}")
        print(f"⚠️  Redundant Files: {report['redundant_files']}")
        print(f"🔗 Dependency Chains: {report['dependency_chains']}")
        
        reduction_percent = ((report['safe_to_remove'] + report['redundant_files']) / report['total_python_files']) * 100
        print(f"📉 Potential Reduction: {reduction_percent:.1f}%")
        
        print("\n🔥 CORE FILES TO PRESERVE:")
        for file in sorted(report['file_details']['core_files']):
            print(f"  ✅ {file}")
        
        print(f"\n🗑️  SAFE TO REMOVE ({len(report['file_details']['safe_to_remove'])} files):")
        for file in sorted(report['file_details']['safe_to_remove'])[:10]:  # Show first 10
            print(f"  🗑️  {file}")
        if len(report['file_details']['safe_to_remove']) > 10:
            print(f"  ... and {len(report['file_details']['safe_to_remove']) - 10} more")
        
        if report['file_details']['redundant_files']:
            print(f"\n⚠️  REDUNDANT FILES ({len(report['file_details']['redundant_files'])} files):")
            for file in sorted(report['file_details']['redundant_files'])[:5]:
                print(f"  ⚠️  {file}")

def main():
    """Execute QQ intelligent file sweep"""
    sweep = QQIntelligentFileSweep()
    
    # Analyze codebase
    report = sweep.analyze_codebase()
    
    # Display visual report
    sweep.display_visual_report(report)
    
    # Save detailed report
    with open('qq_file_sweep_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved: qq_file_sweep_report.json")
    
    # Ask user for cleanup execution
    print("\n🤖 Execute intelligent cleanup? (y/n):")
    response = input().lower().strip()
    
    if response == 'y':
        removed_count = sweep.execute_intelligent_cleanup(report)
        print(f"\n🎉 QQ Intelligent Sweep Complete!")
        print(f"📁 Archived {removed_count} files")
        print(f"🔥 Core functionality preserved")
    else:
        print("📊 Analysis complete. No files modified.")

if __name__ == "__main__":
    main()