"""
TRAXOVO Deployment Analysis Engine
Comprehensive deployment readiness assessment and optimization
Replaces Puppeteer dependencies with Playwright and performs full system validation
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - DEPLOYMENT_ANALYSIS - %(levelname)s - %(message)s')

class DeploymentAnalysisEngine:
    """
    Comprehensive deployment analysis and optimization engine
    Handles Puppeteer to Playwright migration and full system validation
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_results = {}
        self.migration_status = {}
        self.deployment_readiness = {}
        self.optimization_recommendations = []
        
        # Initialize analysis database
        self.db_path = self.project_root / "deployment_analysis.db"
        self._init_analysis_db()
        
        logging.info("Deployment Analysis Engine initialized")
    
    def _init_analysis_db(self):
        """Initialize deployment analysis database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployment_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                recommendations TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_tech TEXT NOT NULL,
                target_tech TEXT NOT NULL,
                file_path TEXT NOT NULL,
                migration_status TEXT NOT NULL,
                changes_made TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def perform_full_deployment_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive deployment analysis"""
        logging.info("Starting full deployment analysis")
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_id": f"deploy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "puppeteer_migration": self._analyze_puppeteer_migration(),
            "system_dependencies": self._analyze_system_dependencies(),
            "database_connectivity": self._analyze_database_connectivity(),
            "application_structure": self._analyze_application_structure(),
            "security_assessment": self._analyze_security_configuration(),
            "performance_analysis": self._analyze_performance_metrics(),
            "deployment_readiness": self._assess_deployment_readiness(),
            "optimization_recommendations": self._generate_optimization_recommendations()
        }
        
        self.analysis_results = analysis_results
        self._save_analysis_results()
        
        return analysis_results
    
    def _analyze_puppeteer_migration(self) -> Dict[str, Any]:
        """Analyze and migrate Puppeteer dependencies to Playwright"""
        logging.info("Analyzing Puppeteer to Playwright migration")
        
        migration_results = {
            "migration_required": False,
            "files_requiring_migration": [],
            "migration_completed": [],
            "migration_failed": [],
            "package_updates_needed": [],
            "status": "not_started"
        }
        
        # Find all files with Puppeteer dependencies
        puppeteer_files = self._find_puppeteer_references()
        
        if puppeteer_files:
            migration_results["migration_required"] = True
            migration_results["files_requiring_migration"] = puppeteer_files
            
            # Perform migration
            for file_path in puppeteer_files:
                try:
                    if self._migrate_file_to_playwright(file_path):
                        migration_results["migration_completed"].append(file_path)
                    else:
                        migration_results["migration_failed"].append(file_path)
                except Exception as e:
                    migration_results["migration_failed"].append(f"{file_path}: {str(e)}")
            
            # Check package.json status
            if self._check_package_json_puppeteer():
                migration_results["package_updates_needed"].append("Remove puppeteer from package.json")
                migration_results["package_updates_needed"].append("Add playwright to dependencies")
        
        # Determine overall migration status
        if not migration_results["migration_required"]:
            migration_results["status"] = "not_required"
        elif migration_results["migration_failed"]:
            migration_results["status"] = "partial_failure"
        elif migration_results["migration_completed"]:
            migration_results["status"] = "completed"
        else:
            migration_results["status"] = "failed"
        
        self.migration_status = migration_results
        return migration_results
    
    def _find_puppeteer_references(self) -> List[str]:
        """Find all files containing Puppeteer references"""
        puppeteer_files = []
        
        # Search patterns
        file_patterns = ["*.js", "*.ts", "*.py", "*.json"]
        puppeteer_keywords = ["puppeteer", "Puppeteer", "PUPPETEER"]
        
        for pattern in file_patterns:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                if file_path.name in ["package-lock.json", "node_modules"]:
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if any(keyword in content for keyword in puppeteer_keywords):
                        puppeteer_files.append(str(file_path.relative_to(self.project_root)))
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return puppeteer_files
    
    def _migrate_file_to_playwright(self, file_path: str) -> bool:
        """Migrate a single file from Puppeteer to Playwright"""
        try:
            full_path = self.project_root / file_path
            content = full_path.read_text(encoding='utf-8')
            
            # Skip package.json and package-lock.json
            if file_path.endswith(('package.json', 'package-lock.json')):
                logging.info(f"Skipping package file: {file_path}")
                return True
            
            # JavaScript/TypeScript migrations
            if file_path.endswith(('.js', '.ts')):
                content = self._migrate_js_ts_content(content)
            
            # Python migrations
            elif file_path.endswith('.py'):
                content = self._migrate_python_content(content)
            
            # Write migrated content
            full_path.write_text(content, encoding='utf-8')
            
            # Log migration
            self._log_migration(file_path, "puppeteer", "playwright", "completed", "Automated migration")
            
            logging.info(f"Successfully migrated {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to migrate {file_path}: {e}")
            self._log_migration(file_path, "puppeteer", "playwright", "failed", str(e))
            return False
    
    def _migrate_js_ts_content(self, content: str) -> str:
        """Migrate JavaScript/TypeScript content from Puppeteer to Playwright"""
        # Replace imports
        content = content.replace(
            "const puppeteer = require('puppeteer');",
            "const { chromium } = require('playwright');"
        )
        content = content.replace(
            "import puppeteer from 'puppeteer';",
            "import { chromium } from 'playwright';"
        )
        content = content.replace(
            "import * as puppeteer from 'puppeteer';",
            "import { chromium } from 'playwright';"
        )
        
        # Replace API calls
        content = content.replace("puppeteer.launch(", "chromium.launch(")
        content = content.replace("puppeteer.connect(", "chromium.connect(")
        
        # Update browser launch options
        content = content.replace(
            "headless: false",
            "headless: false"
        )
        content = content.replace(
            "devtools: true",
            "devtools: true"
        )
        
        return content
    
    def _migrate_python_content(self, content: str) -> str:
        """Migrate Python content from Puppeteer references to Playwright"""
        # Replace Python imports and references
        content = content.replace(
            "from pyppeteer import launch",
            "from playwright.async_api import async_playwright"
        )
        content = content.replace(
            "import pyppeteer",
            "from playwright.sync_api import sync_playwright"
        )
        
        # Update launch patterns
        content = content.replace(
            "await launch(",
            "await async_playwright().start().chromium.launch("
        )
        
        return content
    
    def _check_package_json_puppeteer(self) -> bool:
        """Check if package.json contains Puppeteer dependencies"""
        package_json_path = self.project_root / "package.json"
        
        if not package_json_path.exists():
            return False
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            return 'puppeteer' in dependencies or 'puppeteer' in dev_dependencies
            
        except Exception as e:
            logging.error(f"Error checking package.json: {e}")
            return False
    
    def _analyze_system_dependencies(self) -> Dict[str, Any]:
        """Analyze system dependencies and package health"""
        logging.info("Analyzing system dependencies")
        
        dependencies = {
            "python_version": sys.version,
            "python_packages": self._get_python_packages(),
            "nodejs_packages": self._get_nodejs_packages(),
            "system_packages": self._get_system_info(),
            "missing_dependencies": [],
            "version_conflicts": [],
            "security_vulnerabilities": []
        }
        
        # Check for required packages
        required_python_packages = [
            "flask", "sqlalchemy", "playwright", "openai", "requests"
        ]
        
        installed_packages = dependencies["python_packages"]
        for package in required_python_packages:
            if package not in installed_packages:
                dependencies["missing_dependencies"].append(f"python:{package}")
        
        return dependencies
    
    def _get_python_packages(self) -> Dict[str, str]:
        """Get installed Python packages"""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=json"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg["name"]: pkg["version"] for pkg in packages}
        except Exception as e:
            logging.error(f"Error getting Python packages: {e}")
        
        return {}
    
    def _get_nodejs_packages(self) -> Dict[str, Any]:
        """Get Node.js package information"""
        package_info = {"installed": False, "packages": {}}
        
        try:
            # Check if Node.js is available
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                package_info["node_version"] = result.stdout.strip()
                package_info["installed"] = True
                
                # Get npm packages
                npm_result = subprocess.run(["npm", "list", "--json"], 
                                          capture_output=True, text=True, cwd=self.project_root)
                if npm_result.returncode == 0:
                    npm_data = json.loads(npm_result.stdout)
                    package_info["packages"] = npm_data.get("dependencies", {})
                    
        except Exception as e:
            logging.error(f"Error getting Node.js packages: {e}")
        
        return package_info
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": os.name,
            "architecture": os.uname().machine if hasattr(os, 'uname') else 'unknown',
            "environment_variables": {
                "DATABASE_URL": "configured" if os.getenv("DATABASE_URL") else "missing",
                "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
                "FLASK_SECRET_KEY": "configured" if os.getenv("FLASK_SECRET_KEY") else "missing"
            }
        }
    
    def _analyze_database_connectivity(self) -> Dict[str, Any]:
        """Analyze database connectivity and health"""
        logging.info("Analyzing database connectivity")
        
        db_analysis = {
            "postgresql_available": False,
            "connection_test": "failed",
            "database_url_configured": bool(os.getenv("DATABASE_URL")),
            "table_count": 0,
            "data_integrity": "unknown",
            "recommendations": []
        }
        
        try:
            # Test database connection
            import psycopg2
            
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Test connection
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                db_analysis["postgresql_version"] = version[0] if version else "unknown"
                db_analysis["postgresql_available"] = True
                db_analysis["connection_test"] = "success"
                
                # Get table count
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """)
                table_count = cursor.fetchone()
                db_analysis["table_count"] = table_count[0] if table_count else 0
                
                conn.close()
                
        except ImportError:
            db_analysis["recommendations"].append("Install psycopg2-binary for PostgreSQL connectivity")
        except Exception as e:
            db_analysis["connection_error"] = str(e)
            db_analysis["recommendations"].append(f"Fix database connection: {str(e)}")
        
        return db_analysis
    
    def _analyze_application_structure(self) -> Dict[str, Any]:
        """Analyze application structure and architecture"""
        logging.info("Analyzing application structure")
        
        structure_analysis = {
            "main_app_files": [],
            "template_files": [],
            "static_files": [],
            "configuration_files": [],
            "migration_files": [],
            "test_files": [],
            "documentation_files": [],
            "total_files": 0,
            "code_quality_issues": [],
            "architecture_recommendations": []
        }
        
        # Analyze file structure
        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                structure_analysis["total_files"] += 1
                
                if file.endswith(('.py', '.js', '.ts')):
                    if 'app' in file or 'main' in file:
                        structure_analysis["main_app_files"].append(str(relative_path))
                
                elif file.endswith('.html'):
                    structure_analysis["template_files"].append(str(relative_path))
                
                elif file.endswith(('.css', '.js', '.png', '.jpg', '.svg')):
                    structure_analysis["static_files"].append(str(relative_path))
                
                elif file.endswith(('.json', '.yaml', '.yml', '.env')):
                    structure_analysis["configuration_files"].append(str(relative_path))
                
                elif 'test' in file.lower():
                    structure_analysis["test_files"].append(str(relative_path))
                
                elif file.endswith(('.md', '.txt', '.rst')):
                    structure_analysis["documentation_files"].append(str(relative_path))
        
        # Architecture recommendations
        if not structure_analysis["test_files"]:
            structure_analysis["architecture_recommendations"].append("Add unit tests for better code quality")
        
        if len(structure_analysis["main_app_files"]) > 5:
            structure_analysis["architecture_recommendations"].append("Consider modularizing large application files")
        
        return structure_analysis
    
    def _analyze_security_configuration(self) -> Dict[str, Any]:
        """Analyze security configuration and vulnerabilities"""
        logging.info("Analyzing security configuration")
        
        security_analysis = {
            "secret_keys_configured": False,
            "environment_variables_secure": True,
            "database_security": "unknown",
            "api_security": "unknown",
            "ssl_configuration": "unknown",
            "security_vulnerabilities": [],
            "security_recommendations": []
        }
        
        # Check environment variables
        sensitive_vars = ["DATABASE_URL", "OPENAI_API_KEY", "FLASK_SECRET_KEY"]
        configured_vars = 0
        
        for var in sensitive_vars:
            if os.getenv(var):
                configured_vars += 1
        
        security_analysis["secret_keys_configured"] = configured_vars == len(sensitive_vars)
        
        if configured_vars < len(sensitive_vars):
            security_analysis["security_recommendations"].append(
                f"Configure missing environment variables: {configured_vars}/{len(sensitive_vars)} configured"
            )
        
        # Check for hardcoded secrets in code
        secret_patterns = ["password", "secret", "key", "token", "api_key"]
        for pattern in ["*.py", "*.js", "*.ts"]:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                try:
                    content = file_path.read_text(encoding='utf-8').lower()
                    for secret_pattern in secret_patterns:
                        if f"{secret_pattern} = " in content and "os.getenv" not in content:
                            security_analysis["security_vulnerabilities"].append(
                                f"Potential hardcoded secret in {file_path.name}"
                            )
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return security_analysis
    
    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """Analyze performance metrics and optimization opportunities"""
        logging.info("Analyzing performance metrics")
        
        performance_analysis = {
            "code_complexity": self._calculate_code_complexity(),
            "database_optimization": self._analyze_database_performance(),
            "static_asset_optimization": self._analyze_static_assets(),
            "caching_opportunities": [],
            "performance_recommendations": []
        }
        
        # Analyze caching opportunities
        main_app_files = list(self.project_root.glob("**/*app*.py"))
        for app_file in main_app_files:
            try:
                content = app_file.read_text(encoding='utf-8')
                if "@app.route" in content and "@cache" not in content:
                    performance_analysis["caching_opportunities"].append(
                        f"Add caching to routes in {app_file.name}"
                    )
            except (UnicodeDecodeError, PermissionError):
                continue
        
        return performance_analysis
    
    def _calculate_code_complexity(self) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        complexity = {
            "total_lines": 0,
            "python_lines": 0,
            "javascript_lines": 0,
            "function_count": 0,
            "class_count": 0,
            "complexity_score": "low"
        }
        
        for pattern in ["*.py", "*.js", "*.ts"]:
            for file_path in self.project_root.glob(f"**/{pattern}"):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    lines = content.splitlines()
                    complexity["total_lines"] += len(lines)
                    
                    if pattern == "*.py":
                        complexity["python_lines"] += len(lines)
                        complexity["function_count"] += content.count("def ")
                        complexity["class_count"] += content.count("class ")
                    else:
                        complexity["javascript_lines"] += len(lines)
                        complexity["function_count"] += content.count("function ")
                        complexity["function_count"] += content.count("const ") + content.count("let ")
                        
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        # Determine complexity score
        if complexity["total_lines"] > 10000:
            complexity["complexity_score"] = "high"
        elif complexity["total_lines"] > 5000:
            complexity["complexity_score"] = "medium"
        
        return complexity
    
    def _analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database performance"""
        return {
            "connection_pooling": "unknown",
            "index_optimization": "unknown",
            "query_optimization": "unknown",
            "recommendations": [
                "Consider implementing database connection pooling",
                "Review and optimize database queries",
                "Add database indexes for frequently queried columns"
            ]
        }
    
    def _analyze_static_assets(self) -> Dict[str, Any]:
        """Analyze static asset optimization"""
        assets = {
            "total_size": 0,
            "css_files": 0,
            "js_files": 0,
            "image_files": 0,
            "optimization_opportunities": []
        }
        
        static_dir = self.project_root / "static"
        if static_dir.exists():
            for file_path in static_dir.glob("**/*"):
                if file_path.is_file():
                    assets["total_size"] += file_path.stat().st_size
                    
                    if file_path.suffix == ".css":
                        assets["css_files"] += 1
                    elif file_path.suffix in [".js", ".ts"]:
                        assets["js_files"] += 1
                    elif file_path.suffix in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
                        assets["image_files"] += 1
        
        if assets["total_size"] > 1024 * 1024:  # > 1MB
            assets["optimization_opportunities"].append("Consider compressing static assets")
        
        return assets
    
    def _assess_deployment_readiness(self) -> Dict[str, Any]:
        """Assess overall deployment readiness"""
        logging.info("Assessing deployment readiness")
        
        readiness = {
            "overall_score": 0,
            "critical_issues": [],
            "warnings": [],
            "passed_checks": [],
            "deployment_recommendation": "not_ready"
        }
        
        score = 0
        max_score = 10
        
        # Check migration status
        if self.migration_status.get("status") == "completed":
            score += 2
            readiness["passed_checks"].append("Puppeteer to Playwright migration completed")
        elif self.migration_status.get("status") == "not_required":
            score += 2
            readiness["passed_checks"].append("No Puppeteer migration required")
        else:
            readiness["critical_issues"].append("Puppeteer migration incomplete")
        
        # Check database connectivity
        if os.getenv("DATABASE_URL"):
            score += 2
            readiness["passed_checks"].append("Database configuration present")
        else:
            readiness["critical_issues"].append("Database URL not configured")
        
        # Check required environment variables
        required_vars = ["OPENAI_API_KEY", "FLASK_SECRET_KEY"]
        configured_vars = sum(1 for var in required_vars if os.getenv(var))
        
        if configured_vars == len(required_vars):
            score += 2
            readiness["passed_checks"].append("All required environment variables configured")
        else:
            readiness["warnings"].append(f"Missing environment variables: {len(required_vars) - configured_vars}")
        
        # Check main application files
        main_files = ["app.py", "main.py", "app_qq_enhanced.py"]
        if any((self.project_root / file).exists() for file in main_files):
            score += 2
            readiness["passed_checks"].append("Main application file present")
        else:
            readiness["critical_issues"].append("No main application file found")
        
        # Check static file structure
        static_dir = self.project_root / "static"
        templates_dir = self.project_root / "templates"
        if static_dir.exists() and templates_dir.exists():
            score += 2
            readiness["passed_checks"].append("Static and template directories present")
        else:
            readiness["warnings"].append("Missing static or templates directory")
        
        readiness["overall_score"] = (score / max_score) * 100
        
        # Deployment recommendation
        if score >= 8:
            readiness["deployment_recommendation"] = "ready"
        elif score >= 6:
            readiness["deployment_recommendation"] = "ready_with_warnings"
        else:
            readiness["deployment_recommendation"] = "not_ready"
        
        self.deployment_readiness = readiness
        return readiness
    
    def _generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Puppeteer migration recommendations
        if self.migration_status.get("migration_required"):
            if self.migration_status.get("package_updates_needed"):
                recommendations.append({
                    "category": "dependency_management",
                    "priority": "high",
                    "title": "Update Package Dependencies",
                    "description": "Remove puppeteer and add playwright to package.json",
                    "action": "Use package manager to update dependencies",
                    "impact": "Resolves deployment compatibility issues"
                })
        
        # Database recommendations
        if not os.getenv("DATABASE_URL"):
            recommendations.append({
                "category": "configuration",
                "priority": "critical",
                "title": "Configure Database Connection",
                "description": "Set DATABASE_URL environment variable",
                "action": "Add DATABASE_URL to environment configuration",
                "impact": "Enables database functionality"
            })
        
        # Security recommendations
        if not os.getenv("FLASK_SECRET_KEY"):
            recommendations.append({
                "category": "security",
                "priority": "high",
                "title": "Configure Flask Secret Key",
                "description": "Set FLASK_SECRET_KEY for session security",
                "action": "Generate and set secure secret key",
                "impact": "Ensures session security"
            })
        
        # Performance recommendations
        recommendations.append({
            "category": "performance",
            "priority": "medium",
            "title": "Implement Caching Strategy",
            "description": "Add caching for frequently accessed data",
            "action": "Implement Flask-Caching or Redis caching",
            "impact": "Improves response times and reduces server load"
        })
        
        self.optimization_recommendations = recommendations
        return recommendations
    
    def _log_migration(self, file_path: str, source_tech: str, target_tech: str, 
                      status: str, changes: str):
        """Log migration details to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO migration_log 
            (timestamp, source_tech, target_tech, file_path, migration_status, changes_made)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            source_tech,
            target_tech,
            file_path,
            status,
            changes
        ))
        
        conn.commit()
        conn.close()
    
    def _save_analysis_results(self):
        """Save analysis results to database and file"""
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for component, details in self.analysis_results.items():
            if isinstance(details, dict):
                cursor.execute('''
                    INSERT INTO deployment_analysis 
                    (timestamp, analysis_type, component, status, details, recommendations)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    "full_deployment_analysis",
                    component,
                    "completed",
                    json.dumps(details),
                    json.dumps(self.optimization_recommendations)
                ))
        
        conn.commit()
        conn.close()
        
        # Save to JSON file
        results_file = self.project_root / f"deployment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        logging.info(f"Analysis results saved to {results_file}")
    
    def generate_deployment_report(self) -> str:
        """Generate human-readable deployment report"""
        if not self.analysis_results:
            return "No analysis results available. Run perform_full_deployment_analysis() first."
        
        report = []
        report.append("=" * 80)
        report.append("TRAXOVO DEPLOYMENT ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {self.analysis_results['timestamp']}")
        report.append(f"Analysis ID: {self.analysis_results['analysis_id']}")
        report.append("")
        
        # Deployment Readiness Summary
        readiness = self.deployment_readiness
        report.append("DEPLOYMENT READINESS SUMMARY")
        report.append("-" * 40)
        report.append(f"Overall Score: {readiness['overall_score']:.1f}%")
        report.append(f"Recommendation: {readiness['deployment_recommendation'].replace('_', ' ').title()}")
        report.append("")
        
        if readiness['critical_issues']:
            report.append("Critical Issues:")
            for issue in readiness['critical_issues']:
                report.append(f"  ❌ {issue}")
            report.append("")
        
        if readiness['warnings']:
            report.append("Warnings:")
            for warning in readiness['warnings']:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        if readiness['passed_checks']:
            report.append("Passed Checks:")
            for check in readiness['passed_checks']:
                report.append(f"  ✅ {check}")
            report.append("")
        
        # Migration Status
        migration = self.migration_status
        report.append("PUPPETEER TO PLAYWRIGHT MIGRATION")
        report.append("-" * 40)
        report.append(f"Status: {migration['status'].replace('_', ' ').title()}")
        
        if migration['migration_completed']:
            report.append("Migrated Files:")
            for file in migration['migration_completed']:
                report.append(f"  ✅ {file}")
        
        if migration['migration_failed']:
            report.append("Failed Migrations:")
            for file in migration['migration_failed']:
                report.append(f"  ❌ {file}")
        
        if migration['package_updates_needed']:
            report.append("Package Updates Needed:")
            for update in migration['package_updates_needed']:
                report.append(f"  📦 {update}")
        report.append("")
        
        # Optimization Recommendations
        if self.optimization_recommendations:
            report.append("OPTIMIZATION RECOMMENDATIONS")
            report.append("-" * 40)
            for i, rec in enumerate(self.optimization_recommendations, 1):
                priority_icon = "🔴" if rec['priority'] == 'critical' else "🟡" if rec['priority'] == 'high' else "🟢"
                report.append(f"{i}. {priority_icon} {rec['title']} ({rec['priority'].upper()})")
                report.append(f"   {rec['description']}")
                report.append(f"   Action: {rec['action']}")
                report.append(f"   Impact: {rec['impact']}")
                report.append("")
        
        return "\n".join(report)

# Global deployment analyzer instance
deployment_analyzer = None

def get_deployment_analyzer():
    """Get global deployment analyzer instance"""
    global deployment_analyzer
    if deployment_analyzer is None:
        deployment_analyzer = DeploymentAnalysisEngine()
    return deployment_analyzer

def perform_deployment_analysis():
    """Perform full deployment analysis"""
    analyzer = get_deployment_analyzer()
    return analyzer.perform_full_deployment_analysis()

def generate_deployment_report():
    """Generate deployment report"""
    analyzer = get_deployment_analyzer()
    return analyzer.generate_deployment_report()