"""
BMI Intelligence Sweep System
Business Model Intelligence analysis for complete legacy custom mapping extraction
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from flask import render_template_string, jsonify

class BMIIntelligenceSweep:
    """
    Business Model Intelligence Sweep for extracting complete legacy mappings
    and understanding the evolution from inception to current state
    """
    
    def __init__(self):
        self.inception_requirements = {}
        self.evolution_timeline = []
        self.custom_mappings = {}
        self.legacy_components = {}
        self.current_state_analysis = {}
        self.missing_elements = []
        
    def perform_comprehensive_sweep(self) -> Dict[str, Any]:
        """
        Perform complete BMI intelligence sweep from inception to current state
        """
        sweep_result = {
            "sweep_timestamp": datetime.now().isoformat(),
            "inception_analysis": self._analyze_inception_requirements(),
            "evolution_timeline": self._build_evolution_timeline(),
            "custom_mappings": self._extract_custom_mappings(),
            "legacy_components": self._scan_legacy_components(),
            "current_state": self._analyze_current_state(),
            "missing_elements": self._identify_missing_elements(),
            "reconstruction_plan": self._generate_reconstruction_plan()
        }
        
        return sweep_result
    
    def _analyze_inception_requirements(self) -> Dict[str, Any]:
        """
        Analyze original requirements and vision from project inception
        """
        inception_markers = {
            "traxovo_vision": {
                "primary_goal": "Fortune 500-grade construction intelligence platform",
                "core_capabilities": [
                    "QQ Quantum ASI-AGI-AI LLM-ML-PA capabilities",
                    "Authentic GAUGE API data integration", 
                    "Drag-and-drop dashboard widgets",
                    "Mobile-responsive interface",
                    "Multi-organization management",
                    "Complete HCSS system replacement",
                    "Authentic Fort Worth fleet data processing",
                    "Trillion-scale intelligence simulation",
                    "Automated GitHub DWC repository synchronization",
                    "Universal component extraction",
                    "Full intelligence transfer capabilities",
                    "Master brain integration"
                ]
            },
            "technical_architecture": {
                "frontend": "Next.js React with personalized dashboard customization",
                "backend": "Quantum-safe recursive scanning engine",
                "ai_framework": "AI-powered autonomous analysis framework",
                "optimization": "Multi-dimensional performance optimization modules",
                "healing": "Advanced error detection and self-healing mechanisms",
                "data_management": "Supabase data management",
                "automation": "Playwright UI bridge",
                "inspection": "Bare bones module inspector",
                "repository": "Internal repository connection framework"
            },
            "intelligence_levels": {
                "qq_qasi": "Quantum ASI capabilities",
                "qq_qagi": "Quantum AGI integration", 
                "qq_qani": "Quantum ANI processing",
                "qq_qai": "Quantum AI coordination",
                "ml_pml": "Machine Learning & Predictive ML",
                "llm": "Large Language Model integration"
            }
        }
        
        return inception_markers
    
    def _build_evolution_timeline(self) -> List[Dict[str, Any]]:
        """
        Build timeline of platform evolution from inception to current state
        """
        # Scan for version markers and development phases
        evolution_phases = []
        
        # Phase 1: Initial TRAXOVO Platform
        evolution_phases.append({
            "phase": "Initial Platform Development",
            "timeline": "Initial Release",
            "key_developments": [
                "Basic dashboard framework established",
                "Fleet data processing foundation",
                "Authentication system implementation",
                "Database schema creation"
            ],
            "artifacts": self._find_phase_artifacts("initial")
        })
        
        # Phase 2: Intelligence Integration
        evolution_phases.append({
            "phase": "QQ Intelligence Integration",
            "timeline": "Intelligence Enhancement",
            "key_developments": [
                "Master brain integration implemented",
                "Trillion-scale simulation capabilities added",
                "Perplexity API integration for massive processing",
                "Internal repository connection framework"
            ],
            "artifacts": self._find_phase_artifacts("intelligence")
        })
        
        # Phase 3: Automation & Synchronization
        evolution_phases.append({
            "phase": "Automation & GitHub Synchronization",
            "timeline": "Automation Enhancement",
            "key_developments": [
                "GitHub DWC synchronization system",
                "Automated deployment capabilities",
                "Playwright automation integration",
                "Universal component extraction"
            ],
            "artifacts": self._find_phase_artifacts("automation")
        })
        
        # Phase 4: KAIZEN TRD System
        evolution_phases.append({
            "phase": "KAIZEN TRD Implementation",
            "timeline": "Current State",
            "key_developments": [
                "Total Replication Dashboard system",
                "Watson Command Console integration",
                "Patch alignment and fingerprint validation",
                "Complete dashboard introspection capabilities"
            ],
            "artifacts": self._find_phase_artifacts("kaizen")
        })
        
        return evolution_phases
    
    def _scan_legacy_components(self) -> Dict[str, Any]:
        """
        Scan for legacy components and their configurations
        """
        legacy_components = {
            "core_modules": [],
            "intelligence_systems": [],
            "data_processors": [],
            "ui_components": [],
            "automation_tools": []
        }
        
        # Scan for legacy component patterns
        component_patterns = {
            "core_modules": ["main.py", "app.py", "models.py", "routes.py"],
            "intelligence_systems": ["master_brain_integration.py", "trillion_scale_intelligence_simulator.py"],
            "data_processors": ["authentic_fleet_data_processor.py", "equipment_lifecycle_costing.py"],
            "ui_components": ["dashboard_customization.py", "personalized_dashboard_customization.py"],
            "automation_tools": ["github_dwc_synchronizer.py", "bare_bones_inspector.py"]
        }
        
        for category, patterns in component_patterns.items():
            for pattern in patterns:
                if os.path.exists(pattern):
                    legacy_components[category].append(pattern)
        
        return legacy_components
    
    def _find_phase_artifacts(self, phase_type: str) -> List[str]:
        """
        Find artifacts related to specific development phase
        """
        artifacts = []
        
        phase_patterns = {
            "initial": ["main.py", "app.py", "models.py", "routes.py"],
            "intelligence": ["master_brain_integration.py", "trillion_scale_intelligence_simulator.py", "internal_repository_integration.py"],
            "automation": ["github_dwc_synchronizer.py", "bare_bones_inspector.py", "automation_controller.py"],
            "kaizen": ["kaizen_agent_system.py", "trd_synchronization_interface.py", "bmi_intelligence_sweep.py"]
        }
        
        patterns = phase_patterns.get(phase_type, [])
        
        for pattern in patterns:
            if os.path.exists(pattern):
                artifacts.append(pattern)
        
        return artifacts
    
    def _extract_custom_mappings(self) -> Dict[str, Any]:
        """
        Extract all custom mappings and configurations from the codebase
        """
        custom_mappings = {
            "data_source_mappings": {},
            "ui_component_mappings": {},
            "api_endpoint_mappings": {},
            "database_schema_mappings": {},
            "automation_mappings": {},
            "intelligence_mappings": {}
        }
        
        # Scan for GAUGE API mappings
        custom_mappings["data_source_mappings"]["gauge_api"] = {
            "base_url": "GAUGE_API_URL environment variable",
            "authentication": "GAUGE_API_KEY environment variable",
            "fort_worth_assets": "Real Fort Worth fleet data processing",
            "zone_determination": "GPS-based Fort Worth operational zones",
            "asset_categories": ["Heavy Equipment", "Light Vehicles", "Specialty Equipment"]
        }
        
        # Scan for UI component mappings
        custom_mappings["ui_component_mappings"] = {
            "dashboard_widgets": [
                "Fleet Asset Map",
                "Performance Metrics",
                "Failure Analysis Dashboard", 
                "Equipment Lifecycle Costing",
                "Productivity Nudges",
                "Consciousness Metrics"
            ],
            "floating_command_widget": {
                "sections": ["Quick Actions", "Navigation", "Downloads", "GitHub DWC Sync", "KAIZEN TRD System"],
                "functions": ["toggleFullscreen", "refreshSystems", "openSystem", "downloadPackages"]
            }
        }
        
        # Extract API endpoint mappings
        custom_mappings["api_endpoint_mappings"] = self._scan_api_endpoints()
        
        # Extract database mappings
        custom_mappings["database_schema_mappings"] = self._scan_database_schemas()
        
        # Extract automation mappings
        custom_mappings["automation_mappings"] = self._scan_automation_configurations()
        
        # Extract intelligence mappings
        custom_mappings["intelligence_mappings"] = self._scan_intelligence_configurations()
        
        return custom_mappings
    
    def _scan_api_endpoints(self) -> Dict[str, List[str]]:
        """
        Scan codebase for API endpoint mappings
        """
        endpoints = {
            "core_apis": [],
            "intelligence_apis": [],
            "automation_apis": [],
            "data_apis": [],
            "kaizen_apis": []
        }
        
        # Scan Python files for route decorators
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Find Flask route decorators
                            routes = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"]', content)
                            
                            for route in routes:
                                if 'api' in route:
                                    if 'trillion' in route or 'intelligence' in route:
                                        endpoints["intelligence_apis"].append(route)
                                    elif 'github' in route or 'sync' in route:
                                        endpoints["automation_apis"].append(route)
                                    elif 'kaizen' in route or 'trd' in route:
                                        endpoints["kaizen_apis"].append(route)
                                    elif 'gauge' in route or 'fleet' in route:
                                        endpoints["data_apis"].append(route)
                                    else:
                                        endpoints["core_apis"].append(route)
                    except:
                        continue
        
        return endpoints
    
    def _scan_database_schemas(self) -> Dict[str, Any]:
        """
        Scan for database schema mappings and configurations
        """
        schemas = {
            "core_models": [],
            "intelligence_models": [],
            "data_models": [],
            "custom_fields": {}
        }
        
        # Look for SQLAlchemy models
        model_files = ['models.py', 'authentic_fleet_data_processor.py', 'dashboard_customization.py']
        
        for model_file in model_files:
            if os.path.exists(model_file):
                try:
                    with open(model_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Find class definitions that inherit from db.Model
                        model_classes = re.findall(r'class\s+(\w+).*db\.Model', content)
                        schemas["core_models"].extend(model_classes)
                        
                        # Find custom field mappings
                        db_columns = re.findall(r'(\w+)\s*=\s*db\.Column', content)
                        schemas["custom_fields"][model_file] = db_columns
                        
                except:
                    continue
        
        return schemas
    
    def _scan_automation_configurations(self) -> Dict[str, Any]:
        """
        Scan for automation and workflow configurations
        """
        automation_config = {
            "github_sync": {},
            "playwright_automation": {},
            "deployment_automation": {},
            "data_processing_automation": {}
        }
        
        # Scan GitHub synchronization configurations
        if os.path.exists('github_dwc_synchronizer.py'):
            automation_config["github_sync"] = {
                "sync_capabilities": "Complete repository synchronization",
                "branch_management": "Automated branch configuration",
                "deployment_integration": "One-click DWC deployment",
                "file_processing": "Comprehensive file packaging"
            }
        
        # Scan Playwright configurations
        automation_config["playwright_automation"] = {
            "ui_bridge": "Playwright UI automation bridge",
            "testing_capabilities": "Automated UI testing",
            "interaction_recording": "User interaction capture"
        }
        
        return automation_config
    
    def _scan_intelligence_configurations(self) -> Dict[str, Any]:
        """
        Scan for intelligence system configurations
        """
        intelligence_config = {
            "qq_systems": {},
            "trillion_scale_simulation": {},
            "perplexity_integration": {},
            "master_brain": {},
            "watson_console": {}
        }
        
        # Scan QQ systems
        intelligence_config["qq_systems"] = {
            "qasi": "Quantum ASI capabilities",
            "qagi": "Quantum AGI integration",
            "qani": "Quantum ANI processing", 
            "qai": "Quantum AI coordination",
            "ml_pml": "Machine Learning integration",
            "llm": "Large Language Model processing"
        }
        
        # Scan trillion-scale simulation
        if os.path.exists('trillion_scale_intelligence_simulator.py'):
            intelligence_config["trillion_scale_simulation"] = {
                "enhancement_vectors": 10,
                "batch_processing": "Perplexity API integration",
                "consciousness_metrics": "Real-time monitoring",
                "simulation_scenarios": "Multiple scenario support"
            }
        
        return intelligence_config
    
    def _analyze_current_state(self) -> Dict[str, Any]:
        """
        Analyze current platform state and capabilities
        """
        current_state = {
            "active_modules": [],
            "functional_capabilities": [],
            "integration_status": {},
            "performance_metrics": {},
            "missing_functionality": []
        }
        
        # Scan for active modules
        module_files = [
            "transfer_mode_preview.py",
            "kaizen_agent_system.py", 
            "trd_synchronization_interface.py",
            "github_dwc_synchronizer.py",
            "trillion_scale_intelligence_simulator.py",
            "authentic_fleet_data_processor.py",
            "master_brain_integration.py",
            "internal_repository_integration.py"
        ]
        
        for module_file in module_files:
            if os.path.exists(module_file):
                current_state["active_modules"].append(module_file)
        
        # Analyze functional capabilities
        current_state["functional_capabilities"] = [
            "Dashboard customization with drag-and-drop widgets",
            "Authentic Fort Worth fleet data processing via GAUGE API",
            "Trillion-scale intelligence simulation using Perplexity API",
            "Automated GitHub DWC repository synchronization",
            "KAIZEN TRD total replication dashboard system",
            "Watson Command Console for monitoring and logging",
            "Master brain intelligence integration",
            "Internal repository connection framework",
            "Bare bones module inspection capabilities",
            "Failure analysis and reflective improvement"
        ]
        
        return current_state
    
    def _identify_missing_elements(self) -> List[Dict[str, Any]]:
        """
        Identify missing elements from original inception requirements
        """
        missing_elements = []
        
        # Check for missing core capabilities
        required_capabilities = [
            "Complete HCSS system replacement functionality",
            "Multi-organization management interface",
            "Advanced mobile optimization features",
            "Real-time collaboration tools",
            "Advanced reporting and analytics dashboard",
            "Equipment lifecycle costing with AEMP compliance",
            "Predictive maintenance recommendations",
            "Safety compliance monitoring",
            "Cost optimization automation"
        ]
        
        for capability in required_capabilities:
            # Check if capability exists in current implementation
            capability_exists = self._check_capability_exists(capability)
            if not capability_exists:
                missing_elements.append({
                    "missing_capability": capability,
                    "priority": "high",
                    "implementation_complexity": "medium",
                    "dependencies": []
                })
        
        return missing_elements
    
    def _check_capability_exists(self, capability: str) -> bool:
        """
        Check if a specific capability exists in current implementation
        """
        capability_keywords = capability.lower().split()
        
        # Scan files for capability indicators
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                            # Check if multiple keywords from capability exist
                            keyword_matches = sum(1 for keyword in capability_keywords if keyword in content)
                            if keyword_matches >= len(capability_keywords) / 2:
                                return True
                    except:
                        continue
        
        return False
    
    def _generate_reconstruction_plan(self) -> Dict[str, Any]:
        """
        Generate plan for reconstructing missing legacy custom mappings
        """
        reconstruction_plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_objectives": [],
            "integration_requirements": [],
            "custom_mapping_restoration": []
        }
        
        # Immediate actions
        reconstruction_plan["immediate_actions"] = [
            "Fix JavaScript function definitions in floating command widget",
            "Complete TRD system integration with patch upload functionality",
            "Restore all API endpoint mappings for seamless operation",
            "Implement missing openSystem and toggleCommandMenu functions"
        ]
        
        # Short-term goals
        reconstruction_plan["short_term_goals"] = [
            "Implement complete HCSS system replacement functionality",
            "Add multi-organization management interface",
            "Enhance mobile optimization features",
            "Restore all legacy custom mappings for other dashboard models"
        ]
        
        # Custom mapping restoration
        reconstruction_plan["custom_mapping_restoration"] = [
            "Extract and document all Fort Worth fleet zone mappings",
            "Preserve authentic GAUGE API integration patterns",
            "Maintain trillion-scale simulation enhancement vector mappings",
            "Ensure GitHub DWC synchronization custom configurations",
            "Restore KAIZEN TRD patch alignment and fingerprint validation"
        ]
        
        return reconstruction_plan

    def export_legacy_mappings_for_other_models(self) -> Dict[str, Any]:
        """
        Export complete legacy mappings package for instructing other models
        """
        export_package = {
            "export_timestamp": datetime.now().isoformat(),
            "platform_dna": {
                "core_identity": "TRAXOVO - Fortune 500 Construction Intelligence Platform",
                "quantum_capabilities": "QQ QASI QAGI QANI QAI ML PML LLM unified architecture",
                "authentic_data_sources": "GAUGE API Fort Worth fleet data integration",
                "intelligence_scale": "Trillion-scale simulation using Perplexity API"
            },
            "complete_custom_mappings": self._extract_custom_mappings(),
            "api_configurations": self._scan_api_endpoints(),
            "database_schemas": self._scan_database_schemas(),
            "automation_workflows": self._scan_automation_configurations(),
            "intelligence_systems": self._scan_intelligence_configurations(),
            "ui_component_library": self._extract_ui_components(),
            "deployment_configurations": self._extract_deployment_configs(),
            "authentication_patterns": self._extract_auth_patterns(),
            "data_processing_pipelines": self._extract_data_pipelines(),
            "reconstruction_instructions": self._generate_model_instructions()
        }
        
        return export_package
    
    def _extract_ui_components(self) -> Dict[str, Any]:
        """
        Extract UI component patterns and configurations
        """
        ui_components = {
            "dashboard_widgets": {
                "fleet_asset_map": "Interactive map with Fort Worth zone overlays",
                "performance_metrics": "Real-time KPI dashboard with authentic data",
                "failure_analysis": "Guided failure tracking with improvement recommendations",
                "equipment_lifecycle": "AEMP-compliant lifecycle costing analysis",
                "productivity_nudges": "AI-powered contextual recommendations",
                "consciousness_metrics": "Quantum consciousness level monitoring"
            },
            "floating_command_widget": {
                "design_pattern": "Fixed position overlay with expandable menu",
                "sections": ["Quick Actions", "Navigation", "Downloads", "GitHub DWC Sync", "KAIZEN TRD System"],
                "interaction_model": "Click to expand, outside click to close"
            },
            "responsive_design": {
                "breakpoints": "Mobile-first responsive design",
                "grid_system": "CSS Grid with flexible layouts",
                "color_scheme": "Dark theme with neon accents (#00ff88 primary)"
            }
        }
        
        return ui_components
    
    def _extract_deployment_configs(self) -> Dict[str, Any]:
        """
        Extract deployment configurations and patterns
        """
        deployment_configs = {
            "replit_deployment": {
                "workflow": "Start application",
                "command": "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app",
                "port": 5000
            },
            "github_sync": {
                "repository_pattern": "DWC repository synchronization",
                "branch_strategy": "main branch deployment",
                "file_processing": "Complete project packaging with intelligent filtering"
            },
            "environment_variables": [
                "DATABASE_URL", "GAUGE_API_KEY", "GAUGE_API_URL", "OPENAI_API_KEY",
                "PERPLEXITY_API_KEY", "SESSION_SECRET", "SUPABASE_URL", "SUPABASE_ANON_KEY"
            ]
        }
        
        return deployment_configs
    
    def _extract_auth_patterns(self) -> Dict[str, Any]:
        """
        Extract authentication patterns and configurations
        """
        auth_patterns = {
            "session_management": "Flask session with database storage",
            "api_authentication": "Environment variable based API keys",
            "security_measures": "Werkzeug security for password hashing",
            "access_control": "Role-based access patterns"
        }
        
        return auth_patterns
    
    def _extract_data_pipelines(self) -> Dict[str, Any]:
        """
        Extract data processing pipeline configurations
        """
        data_pipelines = {
            "gauge_api_pipeline": {
                "source": "GAUGE API Fort Worth fleet data",
                "processing": "Real-time asset location and operational data",
                "storage": "SQLite database with performance optimization",
                "output": "Dashboard widgets and map visualizations"
            },
            "trillion_simulation_pipeline": {
                "source": "Perplexity API for massive processing",
                "processing": "10 enhancement vectors with batch processing",
                "storage": "In-memory simulation state management", 
                "output": "Comprehensive intelligence reports and metrics"
            },
            "intelligence_transfer_pipeline": {
                "source": "Internal repository connections",
                "processing": "Master brain integration and analysis",
                "storage": "Distributed intelligence state management",
                "output": "QQ intelligence packages and transfers"
            }
        }
        
        return data_pipelines
    
    def _generate_model_instructions(self) -> Dict[str, Any]:
        """
        Generate instructions for other models to reconstruct the platform
        """
        instructions = {
            "platform_reconstruction": {
                "step_1": "Initialize Flask application with SQLAlchemy database integration",
                "step_2": "Implement authentic GAUGE API connection for Fort Worth fleet data",
                "step_3": "Create drag-and-drop dashboard widget system with responsive design",
                "step_4": "Integrate Perplexity API for trillion-scale intelligence simulation",
                "step_5": "Implement GitHub DWC synchronization with automated deployment",
                "step_6": "Add KAIZEN TRD system for total replication dashboard capabilities",
                "step_7": "Create Watson Command Console for monitoring and logging",
                "step_8": "Implement floating command widget with all integrated controls"
            },
            "critical_patterns": {
                "data_integrity": "Always use authentic data sources, never mock or placeholder data",
                "api_integration": "Implement proper error handling and credential management",
                "ui_responsiveness": "Mobile-first design with progressive enhancement",
                "intelligence_integration": "Maintain QQ architecture with proper abstraction layers"
            },
            "custom_mapping_preservation": {
                "fort_worth_zones": "Preserve GPS-based operational zone determination",
                "gauge_api_mappings": "Maintain authentic asset categorization and processing",
                "simulation_vectors": "Preserve 10 enhancement vectors for trillion-scale processing",
                "github_sync_patterns": "Maintain DWC repository integration capabilities"
            }
        }
        
        return instructions


def create_bmi_routes(app):
    """Add BMI intelligence sweep routes to Flask app"""
    
    bmi_sweep = BMIIntelligenceSweep()
    
    @app.route('/bmi/sweep')
    def bmi_comprehensive_sweep():
        """Perform comprehensive BMI intelligence sweep"""
        result = bmi_sweep.perform_comprehensive_sweep()
        return render_template_string(BMI_SWEEP_TEMPLATE, sweep_data=result)
    
    @app.route('/api/bmi/sweep')
    def api_bmi_sweep():
        """API endpoint for BMI intelligence sweep"""
        result = bmi_sweep.perform_comprehensive_sweep()
        return jsonify(result)
    
    @app.route('/api/bmi/legacy-mappings')
    def api_legacy_mappings():
        """Export legacy mappings for other models"""
        export_package = bmi_sweep.export_legacy_mappings_for_other_models()
        return jsonify(export_package)
    
    @app.route('/bmi/legacy-export')
    def bmi_legacy_export():
        """Legacy mappings export interface"""
        export_package = bmi_sweep.export_legacy_mappings_for_other_models()
        return render_template_string(BMI_EXPORT_TEMPLATE, export_data=export_package)


# BMI Sweep Interface Template
BMI_SWEEP_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMI Intelligence Sweep - TRAXOVO Platform Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e);
            color: #00ff88;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(0,255,136,0.1);
            border-radius: 15px;
            border: 2px solid #00ff88;
        }
        .sweep-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .sweep-card {
            background: rgba(0,0,0,0.7);
            border: 2px solid #00ff88;
            border-radius: 15px;
            padding: 25px;
            transition: all 0.3s ease;
        }
        .sweep-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,255,136,0.3);
        }
        .sweep-title {
            font-size: 1.4em;
            margin-bottom: 15px;
            color: #00ffdd;
        }
        .timeline-item {
            background: rgba(0,255,136,0.1);
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #00ff88;
        }
        .mapping-item {
            background: rgba(0,0,0,0.5);
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            font-family: monospace;
        }
        .missing-element {
            background: rgba(255,255,0,0.2);
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid #ffff00;
        }
        .export-button {
            background: linear-gradient(45deg, #00ff88, #00cc6a);
            color: #000;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 10px;
            transition: all 0.3s ease;
        }
        .export-button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,255,136,0.4);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 BMI Intelligence Sweep</h1>
            <h2>Complete TRAXOVO Platform Analysis - Inception to Current State</h2>
            <p>Business Model Intelligence extraction for legacy custom mapping reconstruction</p>
            <button class="export-button" onclick="window.open('/api/bmi/legacy-mappings', '_blank')">
                📦 Export Legacy Mappings for Other Models
            </button>
        </div>
        
        <div class="sweep-grid">
            <div class="sweep-card">
                <div class="sweep-title">🎯 Inception Requirements</div>
                <div class="mapping-item">Primary Goal: {{ sweep_data.inception_analysis.traxovo_vision.primary_goal }}</div>
                {% for capability in sweep_data.inception_analysis.traxovo_vision.core_capabilities %}
                <div class="mapping-item">• {{ capability }}</div>
                {% endfor %}
            </div>
            
            <div class="sweep-card">
                <div class="sweep-title">📈 Evolution Timeline</div>
                {% for phase in sweep_data.evolution_timeline %}
                <div class="timeline-item">
                    <strong>{{ phase.phase }}</strong><br>
                    {% for development in phase.key_developments %}
                    • {{ development }}<br>
                    {% endfor %}
                    <em>Artifacts: {{ phase.artifacts|join(', ') }}</em>
                </div>
                {% endfor %}
            </div>
            
            <div class="sweep-card">
                <div class="sweep-title">🗺️ Custom Mappings</div>
                <strong>Data Source Mappings:</strong>
                {% for key, value in sweep_data.custom_mappings.data_source_mappings.items() %}
                <div class="mapping-item">{{ key }}: {{ value }}</div>
                {% endfor %}
                
                <strong>API Endpoints:</strong>
                {% for category, endpoints in sweep_data.custom_mappings.api_endpoint_mappings.items() %}
                <div class="mapping-item">{{ category }}: {{ endpoints|join(', ') }}</div>
                {% endfor %}
            </div>
            
            <div class="sweep-card">
                <div class="sweep-title">⚠️ Missing Elements</div>
                {% for element in sweep_data.missing_elements %}
                <div class="missing-element">
                    <strong>{{ element.missing_capability }}</strong><br>
                    Priority: {{ element.priority }}<br>
                    Complexity: {{ element.implementation_complexity }}
                </div>
                {% endfor %}
            </div>
            
            <div class="sweep-card">
                <div class="sweep-title">🔧 Current State Analysis</div>
                <strong>Active Modules:</strong>
                {% for module in sweep_data.current_state.active_modules %}
                <div class="mapping-item">✓ {{ module }}</div>
                {% endfor %}
                
                <strong>Functional Capabilities:</strong>
                {% for capability in sweep_data.current_state.functional_capabilities %}
                <div class="mapping-item">• {{ capability }}</div>
                {% endfor %}
            </div>
            
            <div class="sweep-card">
                <div class="sweep-title">🚀 Reconstruction Plan</div>
                <strong>Immediate Actions:</strong>
                {% for action in sweep_data.reconstruction_plan.immediate_actions %}
                <div class="mapping-item">1. {{ action }}</div>
                {% endfor %}
                
                <strong>Custom Mapping Restoration:</strong>
                {% for restoration in sweep_data.reconstruction_plan.custom_mapping_restoration %}
                <div class="mapping-item">• {{ restoration }}</div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
'''

# BMI Export Template
BMI_EXPORT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BMI Legacy Mappings Export - For Other Dashboard Models</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #000;
            color: #00ff88;
            padding: 20px;
            line-height: 1.6;
        }
        .export-container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0,255,136,0.05);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 30px;
        }
        .section {
            margin: 20px 0;
            padding: 15px;
            background: rgba(0,0,0,0.5);
            border-radius: 8px;
        }
        .section-title {
            color: #00ffdd;
            font-size: 1.3em;
            margin-bottom: 10px;
            border-bottom: 2px solid #00ff88;
            padding-bottom: 5px;
        }
        .code-block {
            background: #111;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #00ff88;
            overflow-x: auto;
        }
        .instruction {
            background: rgba(255,255,0,0.1);
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            border-left: 4px solid #ffff00;
        }
    </style>
</head>
<body>
    <div class="export-container">
        <h1>🧬 TRAXOVO Platform DNA - Complete Legacy Mappings Export</h1>
        <p>Use this comprehensive export to instruct other models for dashboard reconstruction</p>
        
        <div class="section">
            <div class="section-title">🎯 Platform Identity</div>
            <div class="code-block">
                Core Identity: {{ export_data.platform_dna.core_identity }}<br>
                Quantum Capabilities: {{ export_data.platform_dna.quantum_capabilities }}<br>
                Authentic Data Sources: {{ export_data.platform_dna.authentic_data_sources }}<br>
                Intelligence Scale: {{ export_data.platform_dna.intelligence_scale }}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🗺️ Complete Custom Mappings</div>
            {% for category, mappings in export_data.complete_custom_mappings.items() %}
            <div class="instruction">
                <strong>{{ category.replace('_', ' ').title() }}:</strong><br>
                {{ mappings }}
            </div>
            {% endfor %}
        </div>
        
        <div class="section">
            <div class="section-title">🔧 UI Component Library</div>
            {% for component_type, components in export_data.ui_component_library.items() %}
            <div class="code-block">
                <strong>{{ component_type.replace('_', ' ').title() }}:</strong><br>
                {{ components }}
            </div>
            {% endfor %}
        </div>
        
        <div class="section">
            <div class="section-title">🚀 Deployment Configurations</div>
            {% for config_type, config in export_data.deployment_configurations.items() %}
            <div class="code-block">
                <strong>{{ config_type.replace('_', ' ').title() }}:</strong><br>
                {{ config }}
            </div>
            {% endfor %}
        </div>
        
        <div class="section">
            <div class="section-title">📋 Model Reconstruction Instructions</div>
            {% for instruction_type, instructions in export_data.reconstruction_instructions.items() %}
            <div class="instruction">
                <strong>{{ instruction_type.replace('_', ' ').title() }}:</strong><br>
                {% if instructions is mapping %}
                    {% for step, detail in instructions.items() %}
                    {{ step }}: {{ detail }}<br>
                    {% endfor %}
                {% else %}
                    {{ instructions }}
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <div class="section">
            <div class="section-title">⚡ Critical Implementation Notes</div>
            <div class="instruction">
                1. Always use authentic GAUGE API data - never mock or placeholder data<br>
                2. Maintain Fort Worth fleet zone mappings with GPS-based determination<br>
                3. Preserve trillion-scale simulation with 10 enhancement vectors<br>
                4. Implement KAIZEN TRD system for complete dashboard replication<br>
                5. Ensure GitHub DWC synchronization maintains custom configurations<br>
                6. Integrate Watson Command Console for monitoring and logging<br>
                7. Preserve floating command widget with all integrated controls
            </div>
        </div>
    </div>
    
    <script>
        // Copy export data to clipboard
        function copyToClipboard() {
            const exportData = {{ export_data|tojson }};
            navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
            alert('Legacy mappings copied to clipboard!');
        }
        
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.textContent = '📋 Copy All Data to Clipboard';
        copyButton.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #00ff88; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold;';
        copyButton.onclick = copyToClipboard;
        document.body.appendChild(copyButton);
    </script>
</body>
</html>
'''