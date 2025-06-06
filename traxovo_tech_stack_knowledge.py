"""
TRAXOVO Proprietary Tech Stack Knowledge Base
Unified technology specifications for Perplexity deep search integration
"""

import os
import json
import requests
from datetime import datetime
from app import db
from models_clean import PlatformData

class TRAXOVOTechStackKnowledge:
    """Comprehensive tech stack knowledge for TRAXOVO platform"""
    
    def __init__(self):
        self.tech_stack_spec = self._build_comprehensive_tech_spec()
        self.perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
        
    def _build_comprehensive_tech_spec(self):
        """Build complete TRAXOVO technology specification"""
        
        return {
            "platform_identity": {
                "name": "TRAXOVO Enterprise Intelligence Platform",
                "architecture": "Flask-PostgreSQL-AI Hybrid",
                "deployment_target": "Cloud Run",
                "primary_purpose": "Enterprise operational intelligence with AI-powered automation"
            },
            
            "core_technologies": {
                "backend_framework": {
                    "primary": "Flask 3.0+",
                    "orm": "SQLAlchemy with DeclarativeBase",
                    "database": "PostgreSQL (Supabase)",
                    "session_management": "Flask-Session with database storage",
                    "wsgi_server": "Gunicorn with proxy headers"
                },
                
                "authentication_system": {
                    "method": "Session-based authentication",
                    "accounts": ["admin/admin123", "troy/troy2025", "william/william2025", "executive/exec2025", "demo/demo123"],
                    "protection": "All API endpoints require authentication",
                    "session_secret": "Environment variable SESSION_SECRET"
                },
                
                "database_schema": {
                    "platform_data": "JSON storage for dynamic configuration and metrics",
                    "users": "Standard user management with roles",
                    "assets": "Fleet and operational asset tracking",
                    "operational_metrics": "Time-series operational data"
                },
                
                "ai_integration": {
                    "primary_llm": "OpenAI GPT-4o for regression analysis",
                    "watson_integration": "Custom Watson LLM connector for proprietary insights",
                    "regression_fixer": "AI-powered automatic regression detection and resolution",
                    "nexus_infinity": "Self-healing validation system"
                }
            },
            
            "data_integration_layer": {
                "authentic_sources": {
                    "robinhood_api": {
                        "purpose": "Portfolio and trading data",
                        "authentication": "Bearer token via ROBINHOOD_ACCESS_TOKEN",
                        "endpoints": ["accounts", "positions", "orders"]
                    },
                    "coinbase_api": {
                        "purpose": "Cryptocurrency market data",
                        "authentication": "API key via COINBASE_API_KEY (optional for public endpoints)",
                        "endpoints": ["exchange-rates", "ticker", "products"]
                    },
                    "gauge_api": {
                        "purpose": "Fleet and operational metrics",
                        "authentication": "Bearer token via GAUGE_API_KEY",
                        "endpoints": ["fleet/metrics", "assets", "utilization"]
                    }
                },
                
                "data_storage_pattern": {
                    "principle": "PostgreSQL-first storage",
                    "no_hardcoded_data": "All metrics sourced from authentic APIs",
                    "real_time_updates": "Automated refresh every 5-15 minutes",
                    "data_validation": "Authenticity verification before storage"
                }
            },
            
            "automation_engine": {
                "core_modules": {
                    "data_synchronization": "Automated polling of external APIs",
                    "regression_monitoring": "Continuous platform health assessment",
                    "self_healing": "Automatic issue detection and resolution",
                    "market_analysis": "AI-powered financial insights",
                    "fleet_optimization": "Operational efficiency recommendations"
                },
                
                "scheduling_system": {
                    "framework": "Python schedule library",
                    "data_updates": "Every 5 minutes",
                    "market_analysis": "Every 15 minutes",
                    "fleet_optimization": "Every hour",
                    "regression_checks": "Every 30 minutes"
                }
            },
            
            "ui_ux_architecture": {
                "design_system": {
                    "primary_theme": "TRAXOVO Enterprise (dark gradient backgrounds)",
                    "color_scheme": ["#0f0f23", "#1a1a2e", "#16213e", "#00ff88", "#00bfff"],
                    "typography": "Apple system fonts with clean corporate styling",
                    "responsive_design": "Mobile-first with desktop optimization"
                },
                
                "interface_hierarchy": {
                    "landing_page": "Public TRAXOVO branding with feature showcase",
                    "authentication": "Secure login with multiple account options",
                    "executive_dashboard": "JDD-style metrics with real-time data",
                    "navigation": "Bottom navigation bar with 5 primary sections"
                }
            },
            
            "api_architecture": {
                "endpoint_structure": {
                    "authentication_required": "All /api/* endpoints except /health",
                    "response_format": "JSON with consistent error handling",
                    "rate_limiting": "None (internal use)",
                    "versioning": "Implicit v1 in current implementation"
                },
                
                "core_endpoints": {
                    "/api/platform_status": "Real-time integration status",
                    "/api/market_data": "Live financial market data",
                    "/api/executive_metrics": "Key performance indicators",
                    "/api/self_heal/check": "Nexus Infinity validation",
                    "/api/self_heal/recover": "Automated recovery protocols",
                    "/api/update_data": "Manual data refresh trigger"
                }
            },
            
            "deployment_specifications": {
                "container_strategy": {
                    "base_image": "Python 3.11 slim",
                    "package_manager": "pip with requirements-production.txt",
                    "file_optimization": "No large files, database-centric storage",
                    "port_configuration": "5000 with 0.0.0.0 binding"
                },
                
                "environment_requirements": {
                    "mandatory": ["DATABASE_URL", "SESSION_SECRET"],
                    "optional_but_recommended": ["OPENAI_API_KEY", "ROBINHOOD_ACCESS_TOKEN", "GAUGE_API_KEY"],
                    "cloud_run_optimized": "Stateless design with database persistence"
                }
            },
            
            "proprietary_innovations": {
                "nexus_infinity_core": {
                    "purpose": "Comprehensive platform validation and self-healing",
                    "validation_categories": [
                        "platform_integrity", "ui_ux_compliance", "data_authenticity",
                        "endpoint_health", "database_integrity", "authentication_security",
                        "deployment_readiness"
                    ],
                    "healing_protocols": "Automated issue detection and resolution"
                },
                
                "ai_regression_fixer": {
                    "purpose": "Prevent feature regression through AI analysis",
                    "llm_integration": "GPT-4o for code analysis and recommendations",
                    "watson_connector": "Custom Watson LLM for proprietary insights",
                    "continuous_monitoring": "Real-time regression detection"
                },
                
                "automation_intelligence": {
                    "purpose": "Autonomous platform operations",
                    "data_orchestration": "Multi-source API coordination",
                    "predictive_analytics": "Market trend analysis and fleet optimization",
                    "executive_insights": "AI-generated strategic recommendations"
                }
            },
            
            "integration_protocols": {
                "external_api_patterns": {
                    "authentication_handling": "Bearer tokens with environment variable storage",
                    "error_resilience": "Graceful degradation with fallback mechanisms",
                    "data_validation": "Authenticity verification before database storage",
                    "rate_limit_compliance": "Respectful API usage patterns"
                },
                
                "internal_communication": {
                    "database_access": "SQLAlchemy ORM with connection pooling",
                    "session_management": "Secure session handling with database storage",
                    "logging_strategy": "Structured logging for debugging and monitoring"
                }
            },
            
            "security_architecture": {
                "authentication_model": "Multi-account session-based authentication",
                "data_protection": "Environment variable secret management",
                "api_security": "Authentication required for all sensitive endpoints",
                "session_security": "Secure session handling with proper cleanup"
            }
        }
    
    def generate_perplexity_search_context(self, search_query):
        """Generate comprehensive context for Perplexity deep search"""
        
        if not self.perplexity_api_key:
            return {"error": "PERPLEXITY_API_KEY not configured - please provide your API key"}
        
        # Build enhanced search context
        enhanced_query = f"""
        TRAXOVO Enterprise Intelligence Platform Technical Context:
        
        Platform: Flask-PostgreSQL enterprise platform with AI-powered automation
        Architecture: {json.dumps(self.tech_stack_spec['core_technologies'], indent=2)}
        
        Specific Query: {search_query}
        
        Search for cutting-edge solutions, best practices, and implementation strategies that align with:
        - Enterprise-grade Flask applications with PostgreSQL
        - AI-powered regression detection and self-healing systems
        - Real-time data integration from financial and operational APIs
        - Secure authentication and session management
        - Cloud Run deployment optimization
        - Automated data orchestration and validation
        
        Focus on actionable technical insights for enterprise operational intelligence platforms.
        """
        
        try:
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.perplexity_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    "model": "llama-3.1-sonar-large-128k-online",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical research assistant specializing in enterprise platform architecture and implementation strategies."
                        },
                        {
                            "role": "user",
                            "content": enhanced_query
                        }
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.2,
                    "search_recency_filter": "month",
                    "return_related_questions": True,
                    "return_images": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Store search results for future reference
                search_record = {
                    'query': search_query,
                    'enhanced_context': enhanced_query,
                    'perplexity_response': result,
                    'tech_stack_context': self.tech_stack_spec,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                self._store_search_results(search_record)
                
                return {
                    'search_results': result,
                    'tech_context_applied': True,
                    'citations': result.get('citations', []),
                    'related_questions': result.get('choices', [{}])[0].get('message', {}).get('content', ''),
                    'traxovo_context': self.tech_stack_spec
                }
            else:
                return {"error": f"Perplexity API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Perplexity search failed: {str(e)}"}
    
    def get_unified_tech_knowledge(self):
        """Get complete unified tech stack knowledge"""
        
        return {
            'traxovo_specifications': self.tech_stack_spec,
            'deployment_checklist': self._generate_deployment_checklist(),
            'integration_patterns': self._generate_integration_patterns(),
            'best_practices': self._generate_best_practices(),
            'troubleshooting_guide': self._generate_troubleshooting_guide()
        }
    
    def _generate_deployment_checklist(self):
        """Generate deployment readiness checklist"""
        
        return {
            'environment_setup': [
                'DATABASE_URL configured with PostgreSQL connection',
                'SESSION_SECRET set for secure session management',
                'OPENAI_API_KEY configured for AI features',
                'External API keys configured (ROBINHOOD, GAUGE, COINBASE)'
            ],
            'file_optimization': [
                'No files larger than 50MB',
                'requirements-production.txt properly defined',
                'Dockerfile optimized for Cloud Run',
                '.dockerignore configured to exclude unnecessary files'
            ],
            'code_validation': [
                'All imports resolve correctly',
                'Database models create successfully',
                'Authentication system functional',
                'API endpoints return expected responses'
            ],
            'security_verification': [
                'All sensitive endpoints require authentication',
                'Session management working properly',
                'Environment variables properly secured',
                'No hardcoded secrets in code'
            ]
        }
    
    def _generate_integration_patterns(self):
        """Generate integration patterns and best practices"""
        
        return {
            'api_integration': {
                'pattern': 'Connector class with error handling',
                'authentication': 'Environment variable bearer tokens',
                'data_validation': 'Authenticity verification before storage',
                'error_handling': 'Graceful degradation with fallback data'
            },
            'database_patterns': {
                'storage_strategy': 'PostgreSQL with JSON columns for flexibility',
                'data_modeling': 'PlatformData table for dynamic configuration',
                'migration_strategy': 'SQLAlchemy ORM with automatic table creation',
                'performance': 'Connection pooling and query optimization'
            },
            'ai_integration': {
                'llm_usage': 'GPT-4o for analysis, Watson for proprietary insights',
                'prompt_engineering': 'Structured prompts with JSON response format',
                'error_handling': 'Fallback mechanisms for API failures',
                'cost_optimization': 'Intelligent token usage and caching'
            }
        }
    
    def _generate_best_practices(self):
        """Generate TRAXOVO best practices"""
        
        return {
            'development': [
                'Use authentic data sources, never mock data',
                'Implement comprehensive error handling',
                'Follow TRAXOVO UI/UX design standards',
                'Maintain database-first storage approach'
            ],
            'deployment': [
                'Optimize for Cloud Run constraints',
                'Minimize file sizes and dependencies',
                'Use environment variables for configuration',
                'Implement health check endpoints'
            ],
            'monitoring': [
                'Use Nexus Infinity for continuous validation',
                'Implement automated regression detection',
                'Monitor API rate limits and usage',
                'Track platform health scores'
            ]
        }
    
    def _generate_troubleshooting_guide(self):
        """Generate troubleshooting guide"""
        
        return {
            'common_issues': {
                'deployment_failures': 'Usually caused by large files or missing dependencies',
                'database_errors': 'Check DATABASE_URL and table creation',
                'authentication_issues': 'Verify SESSION_SECRET and account credentials',
                'api_failures': 'Check external API keys and rate limits'
            },
            'diagnostic_endpoints': {
                '/health': 'Basic platform health check',
                '/api/self_heal/check': 'Comprehensive validation',
                '/api/platform_health': 'Detailed health metrics'
            },
            'recovery_procedures': [
                'Use /api/self_heal/recover for automated fixes',
                'Check Nexus Infinity validation results',
                'Verify environment variable configuration',
                'Restart application if needed'
            ]
        }
    
    def _store_search_results(self, search_record):
        """Store Perplexity search results for future reference"""
        
        try:
            search_history = PlatformData.query.filter_by(data_type='perplexity_searches').first()
            if search_history:
                existing_searches = search_history.data_content.get('searches', [])
                existing_searches.append(search_record)
                # Keep only last 50 searches
                search_history.data_content = {'searches': existing_searches[-50:]}
                search_history.updated_at = datetime.utcnow()
            else:
                search_history = PlatformData(
                    data_type='perplexity_searches',
                    data_content={'searches': [search_record]}
                )
                db.session.add(search_history)
            
            db.session.commit()
        except Exception as e:
            print(f"Failed to store search results: {e}")

# Global tech stack knowledge instance
traxovo_knowledge = TRAXOVOTechStackKnowledge()

def search_with_traxovo_context(query):
    """Search with TRAXOVO tech stack context"""
    return traxovo_knowledge.generate_perplexity_search_context(query)

def get_complete_tech_stack():
    """Get complete TRAXOVO tech stack specifications"""
    return traxovo_knowledge.get_unified_tech_knowledge()