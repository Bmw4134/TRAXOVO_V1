"""
QQ Codebase Intelligence Engine
Autonomous file scanning, analysis, deduplication, and optimization system
"""

import os
import ast
import re
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from flask import Blueprint, jsonify, render_template
import difflib

@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    file_path: str
    file_size: int
    line_count: int
    function_count: int
    class_count: int
    import_count: int
    complexity_score: float
    duplicate_hash: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    quality_score: float
    is_duplicate: bool
    duplicate_of: Optional[str]
    last_modified: datetime

@dataclass
class DeduplicationResult:
    """Results of deduplication analysis"""
    total_files_scanned: int
    duplicate_groups: List[List[str]]
    bytes_saved: int
    files_to_remove: List[str]
    files_to_keep: List[str]
    consolidation_recommendations: List[Dict[str, Any]]

class QQCodebaseIntelligenceEngine:
    """
    QQ-powered codebase analysis and optimization engine
    Scans all files, detects duplicates, eliminates errors, optimizes performance
    """
    
    def __init__(self):
        self.project_root = "."
        self.analysis_results = {}
        self.file_hashes = {}
        self.duplicate_groups = []
        self.optimization_log = []
        
        # File patterns to analyze
        self.code_extensions = {'.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.md'}
        
        # Patterns to ignore
        self.ignore_patterns = {
            '__pycache__',
            '.git',
            'node_modules',
            '.replit',
            'venv',
            '.env'
        }
        
        # Critical files that should never be auto-deleted
        self.critical_files = {
            'main.py',
            'app.py',
            'app_fixed.py',
            'requirements.txt',
            'package.json',
            'Dockerfile'
        }
        
    def start_comprehensive_analysis(self) -> Dict[str, Any]:
        """Start comprehensive codebase analysis"""
        print("🔍 STARTING QQ CODEBASE INTELLIGENCE SCAN")
        
        analysis_start = datetime.now()
        
        # Phase 1: File discovery and cataloging
        files_found = self._discover_files()
        print(f"📁 Discovered {len(files_found)} files")
        
        # Phase 2: Individual file analysis
        for file_path in files_found:
            self._analyze_file(file_path)
        
        # Phase 3: Duplicate detection
        self._detect_duplicates()
        
        # Phase 4: Error analysis
        error_summary = self._analyze_errors()
        
        # Phase 5: Performance optimization opportunities
        optimization_opportunities = self._identify_optimizations()
        
        # Phase 6: Generate deduplication recommendations
        dedup_results = self._generate_deduplication_plan()
        
        analysis_end = datetime.now()
        analysis_duration = (analysis_end - analysis_start).total_seconds()
        
        return {
            "analysis_complete": True,
            "duration_seconds": analysis_duration,
            "files_analyzed": len(self.analysis_results),
            "duplicates_found": len(self.duplicate_groups),
            "errors_found": sum(len(analysis.errors) for analysis in self.analysis_results.values()),
            "warnings_found": sum(len(analysis.warnings) for analysis in self.analysis_results.values()),
            "optimization_opportunities": len(optimization_opportunities),
            "deduplication_results": dedup_results,
            "error_summary": error_summary,
            "optimization_recommendations": optimization_opportunities
        }
    
    def _discover_files(self) -> List[str]:
        """Discover all relevant files in the project"""
        files_found = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in self.ignore_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                # Include files with relevant extensions
                if file_ext in self.code_extensions or file in self.critical_files:
                    files_found.append(file_path)
        
        return files_found
    
    def _analyze_file(self, file_path: str) -> None:
        """Analyze individual file for quality, complexity, and issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic metrics
            file_size = len(content.encode('utf-8'))
            line_count = len(content.splitlines())
            
            # Generate content hash for duplicate detection
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Initialize analysis
            analysis = FileAnalysis(
                file_path=file_path,
                file_size=file_size,
                line_count=line_count,
                function_count=0,
                class_count=0,
                import_count=0,
                complexity_score=0.0,
                duplicate_hash=content_hash,
                errors=[],
                warnings=[],
                suggestions=[],
                quality_score=0.0,
                is_duplicate=False,
                duplicate_of=None,
                last_modified=datetime.fromtimestamp(os.path.getmtime(file_path))
            )
            
            # Python-specific analysis
            if file_path.endswith('.py'):
                analysis = self._analyze_python_file(file_path, content, analysis)
            
            # JavaScript-specific analysis
            elif file_path.endswith('.js'):
                analysis = self._analyze_javascript_file(file_path, content, analysis)
            
            # HTML-specific analysis
            elif file_path.endswith('.html'):
                analysis = self._analyze_html_file(file_path, content, analysis)
            
            # Generic text analysis
            else:
                analysis = self._analyze_generic_file(file_path, content, analysis)
            
            # Calculate overall quality score
            analysis.quality_score = self._calculate_quality_score(analysis)
            
            # Store analysis results
            self.analysis_results[file_path] = analysis
            
            # Store hash for duplicate detection
            if content_hash in self.file_hashes:
                self.file_hashes[content_hash].append(file_path)
            else:
                self.file_hashes[content_hash] = [file_path]
                
        except Exception as e:
            # Create error analysis for files that can't be read
            error_analysis = FileAnalysis(
                file_path=file_path,
                file_size=0,
                line_count=0,
                function_count=0,
                class_count=0,
                import_count=0,
                complexity_score=0.0,
                duplicate_hash="",
                errors=[f"File read error: {str(e)}"],
                warnings=[],
                suggestions=["Consider checking file encoding or permissions"],
                quality_score=0.0,
                is_duplicate=False,
                duplicate_of=None,
                last_modified=datetime.now()
            )
            self.analysis_results[file_path] = error_analysis
    
    def _analyze_python_file(self, file_path: str, content: str, analysis: FileAnalysis) -> FileAnalysis:
        """Analyze Python-specific patterns and issues"""
        try:
            # Parse AST for structural analysis
            tree = ast.parse(content)
            
            # Count functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis.function_count += 1
                elif isinstance(node, ast.ClassDef):
                    analysis.class_count += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis.import_count += 1
            
            # Calculate complexity (simplified McCabe)
            complexity = self._calculate_python_complexity(tree)
            analysis.complexity_score = complexity
            
            # Check for common issues
            self._check_python_issues(content, analysis)
            
        except SyntaxError as e:
            analysis.errors.append(f"Python syntax error: {str(e)}")
        except Exception as e:
            analysis.warnings.append(f"Python analysis warning: {str(e)}")
        
        return analysis
    
    def _analyze_javascript_file(self, file_path: str, content: str, analysis: FileAnalysis) -> FileAnalysis:
        """Analyze JavaScript-specific patterns"""
        # Count functions (simplified regex)
        function_pattern = r'function\s+\w+|=>\s*{|:\s*function'
        analysis.function_count = len(re.findall(function_pattern, content))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        analysis.class_count = len(re.findall(class_pattern, content))
        
        # Count imports
        import_pattern = r'import\s+.*from|require\s*\('
        analysis.import_count = len(re.findall(import_pattern, content))
        
        # Check for common JavaScript issues
        if 'console.log' in content:
            analysis.warnings.append("Contains console.log statements")
        
        if 'var ' in content:
            analysis.suggestions.append("Consider using 'let' or 'const' instead of 'var'")
        
        return analysis
    
    def _analyze_html_file(self, file_path: str, content: str, analysis: FileAnalysis) -> FileAnalysis:
        """Analyze HTML-specific patterns"""
        # Check for inline styles and scripts
        if 'style=' in content:
            analysis.warnings.append("Contains inline styles")
        
        if '<script>' in content and 'src=' not in content:
            analysis.warnings.append("Contains inline JavaScript")
        
        # Check for accessibility issues
        if 'alt=' not in content and '<img' in content:
            analysis.warnings.append("Images may be missing alt attributes")
        
        return analysis
    
    def _analyze_generic_file(self, file_path: str, content: str, analysis: FileAnalysis) -> FileAnalysis:
        """Analyze generic text files"""
        # Check for very long lines
        lines = content.splitlines()
        long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120]
        
        if long_lines:
            analysis.warnings.append(f"Long lines found at: {long_lines[:5]}")
        
        # Check for trailing whitespace
        if any(line.endswith(' ') or line.endswith('\t') for line in lines):
            analysis.warnings.append("Contains trailing whitespace")
        
        return analysis
    
    def _calculate_python_complexity(self, tree: ast.AST) -> float:
        """Calculate simplified complexity score for Python code"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return float(complexity)
    
    def _check_python_issues(self, content: str, analysis: FileAnalysis) -> None:
        """Check for common Python issues"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Check for print statements (should use logging)
            if re.search(r'\bprint\s*\(', line) and 'debug' not in line.lower():
                analysis.warnings.append(f"Print statement at line {i}")
            
            # Check for bare except clauses
            if 'except:' in line:
                analysis.warnings.append(f"Bare except clause at line {i}")
            
            # Check for long lines
            if len(line) > 120:
                analysis.warnings.append(f"Long line at {i} ({len(line)} chars)")
    
    def _calculate_quality_score(self, analysis: FileAnalysis) -> float:
        """Calculate overall quality score (0-100)"""
        base_score = 100.0
        
        # Deduct points for errors and warnings
        base_score -= len(analysis.errors) * 20
        base_score -= len(analysis.warnings) * 5
        
        # Deduct points for high complexity
        if analysis.complexity_score > 10:
            base_score -= (analysis.complexity_score - 10) * 2
        
        # Bonus points for good structure
        if analysis.function_count > 0 and analysis.line_count > 0:
            if analysis.line_count / analysis.function_count < 50:  # Good function size
                base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    def _detect_duplicates(self) -> None:
        """Detect duplicate files based on content hash"""
        self.duplicate_groups = []
        
        for content_hash, file_paths in self.file_hashes.items():
            if len(file_paths) > 1:
                self.duplicate_groups.append(file_paths)
                
                # Mark files as duplicates (keep the first one)
                primary_file = file_paths[0]
                for duplicate_file in file_paths[1:]:
                    if duplicate_file in self.analysis_results:
                        self.analysis_results[duplicate_file].is_duplicate = True
                        self.analysis_results[duplicate_file].duplicate_of = primary_file
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns across the codebase"""
        error_summary = {
            "total_errors": 0,
            "total_warnings": 0,
            "error_types": {},
            "files_with_errors": [],
            "most_problematic_files": []
        }
        
        for file_path, analysis in self.analysis_results.items():
            if analysis.errors:
                error_summary["total_errors"] += len(analysis.errors)
                error_summary["files_with_errors"].append({
                    "file": file_path,
                    "error_count": len(analysis.errors),
                    "errors": analysis.errors
                })
            
            if analysis.warnings:
                error_summary["total_warnings"] += len(analysis.warnings)
            
            # Categorize error types
            for error in analysis.errors:
                error_type = error.split(':')[0] if ':' in error else error
                if error_type in error_summary["error_types"]:
                    error_summary["error_types"][error_type] += 1
                else:
                    error_summary["error_types"][error_type] = 1
        
        # Sort files by problem count
        problematic_files = [
            (file_path, len(analysis.errors) + len(analysis.warnings))
            for file_path, analysis in self.analysis_results.items()
            if analysis.errors or analysis.warnings
        ]
        
        error_summary["most_problematic_files"] = sorted(
            problematic_files, key=lambda x: x[1], reverse=True
        )[:10]
        
        return error_summary
    
    def _identify_optimizations(self) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []
        
        # Large files that could be split
        large_files = [
            (file_path, analysis.line_count)
            for file_path, analysis in self.analysis_results.items()
            if analysis.line_count > 500
        ]
        
        for file_path, line_count in large_files:
            opportunities.append({
                "type": "file_size",
                "file": file_path,
                "issue": f"Large file with {line_count} lines",
                "recommendation": "Consider splitting into smaller modules",
                "priority": "medium"
            })
        
        # High complexity functions
        complex_files = [
            (file_path, analysis.complexity_score)
            for file_path, analysis in self.analysis_results.items()
            if analysis.complexity_score > 15
        ]
        
        for file_path, complexity in complex_files:
            opportunities.append({
                "type": "complexity",
                "file": file_path,
                "issue": f"High complexity score: {complexity}",
                "recommendation": "Refactor to reduce complexity",
                "priority": "high"
            })
        
        # Files with many warnings
        warning_heavy_files = [
            (file_path, len(analysis.warnings))
            for file_path, analysis in self.analysis_results.items()
            if len(analysis.warnings) > 5
        ]
        
        for file_path, warning_count in warning_heavy_files:
            opportunities.append({
                "type": "code_quality",
                "file": file_path,
                "issue": f"{warning_count} code quality warnings",
                "recommendation": "Address code quality issues",
                "priority": "medium"
            })
        
        return opportunities
    
    def _generate_deduplication_plan(self) -> DeduplicationResult:
        """Generate comprehensive deduplication plan"""
        files_to_remove = []
        files_to_keep = []
        consolidation_recommendations = []
        total_bytes_saved = 0
        
        for duplicate_group in self.duplicate_groups:
            if len(duplicate_group) > 1:
                # Choose the best file to keep (prefer non-backup files, shorter paths)
                primary_file = min(duplicate_group, key=lambda x: (
                    'backup' in x.lower(),
                    'copy' in x.lower(),
                    len(x),
                    x
                ))
                
                files_to_keep.append(primary_file)
                
                for duplicate_file in duplicate_group:
                    if duplicate_file != primary_file and duplicate_file not in self.critical_files:
                        files_to_remove.append(duplicate_file)
                        if duplicate_file in self.analysis_results:
                            total_bytes_saved += self.analysis_results[duplicate_file].file_size
                
                consolidation_recommendations.append({
                    "primary_file": primary_file,
                    "duplicates": [f for f in duplicate_group if f != primary_file],
                    "bytes_saved": sum(
                        self.analysis_results.get(f, FileAnalysis("", 0, 0, 0, 0, 0, 0, "", [], [], [], 0, False, None, datetime.now())).file_size 
                        for f in duplicate_group if f != primary_file
                    )
                })
        
        return DeduplicationResult(
            total_files_scanned=len(self.analysis_results),
            duplicate_groups=self.duplicate_groups,
            bytes_saved=total_bytes_saved,
            files_to_remove=files_to_remove,
            files_to_keep=files_to_keep,
            consolidation_recommendations=consolidation_recommendations
        )
    
    def execute_safe_cleanup(self) -> Dict[str, Any]:
        """Execute safe cleanup of identified issues"""
        cleanup_results = {
            "files_removed": [],
            "errors_fixed": [],
            "warnings_addressed": [],
            "optimizations_applied": [],
            "bytes_saved": 0
        }
        
        dedup_plan = self._generate_deduplication_plan()
        
        # Only remove files that are confirmed duplicates and not critical
        for file_to_remove in dedup_plan.files_to_remove:
            if (file_to_remove not in self.critical_files and 
                os.path.basename(file_to_remove) not in self.critical_files):
                try:
                    file_size = os.path.getsize(file_to_remove)
                    # Move to backup instead of deleting
                    backup_path = f"{file_to_remove}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.rename(file_to_remove, backup_path)
                    
                    cleanup_results["files_removed"].append({
                        "original": file_to_remove,
                        "backup": backup_path,
                        "size": file_size
                    })
                    cleanup_results["bytes_saved"] += file_size
                    
                except Exception as e:
                    print(f"Could not remove {file_to_remove}: {e}")
        
        return cleanup_results
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive analysis summary"""
        if not self.analysis_results:
            return {"error": "No analysis performed yet"}
        
        total_files = len(self.analysis_results)
        total_lines = sum(analysis.line_count for analysis in self.analysis_results.values())
        total_errors = sum(len(analysis.errors) for analysis in self.analysis_results.values())
        total_warnings = sum(len(analysis.warnings) for analysis in self.analysis_results.values())
        
        avg_quality = sum(analysis.quality_score for analysis in self.analysis_results.values()) / total_files
        
        return {
            "summary": {
                "total_files": total_files,
                "total_lines": total_lines,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "average_quality_score": round(avg_quality, 2),
                "duplicate_groups": len(self.duplicate_groups),
                "files_with_duplicates": sum(len(group) for group in self.duplicate_groups)
            },
            "top_quality_files": sorted(
                [(path, analysis.quality_score) for path, analysis in self.analysis_results.items()],
                key=lambda x: x[1], reverse=True
            )[:10],
            "lowest_quality_files": sorted(
                [(path, analysis.quality_score) for path, analysis in self.analysis_results.items()],
                key=lambda x: x[1]
            )[:10],
            "duplicate_groups": [
                {
                    "files": group,
                    "size": self.analysis_results[group[0]].file_size if group[0] in self.analysis_results else 0
                }
                for group in self.duplicate_groups
            ]
        }

# Global instance
qq_codebase_engine = QQCodebaseIntelligenceEngine()

# Flask Blueprint
codebase_intelligence = Blueprint('codebase_intelligence', __name__)

@codebase_intelligence.route('/codebase-analysis')
def codebase_analysis_dashboard():
    """Codebase analysis dashboard"""
    return render_template('codebase_analysis.html')

@codebase_intelligence.route('/api/start-codebase-analysis', methods=['POST'])
def start_codebase_analysis():
    """Start comprehensive codebase analysis"""
    result = qq_codebase_engine.start_comprehensive_analysis()
    return jsonify(result)

@codebase_intelligence.route('/api/codebase-summary')
def get_codebase_summary():
    """Get codebase analysis summary"""
    summary = qq_codebase_engine.get_analysis_summary()
    return jsonify(summary)

@codebase_intelligence.route('/api/execute-cleanup', methods=['POST'])
def execute_cleanup():
    """Execute safe codebase cleanup"""
    result = qq_codebase_engine.execute_safe_cleanup()
    return jsonify(result)

def get_qq_codebase_engine():
    """Get the global codebase intelligence engine"""
    return qq_codebase_engine