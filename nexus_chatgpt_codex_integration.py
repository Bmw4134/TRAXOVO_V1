"""
NEXUS ChatGPT Codex Integration Module
Advanced AI-powered code generation and development assistance
"""

import openai
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import ast
import subprocess

class NexusCodexConnector:
    """Advanced ChatGPT Codex integration for NEXUS platform"""
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        self.client = openai.OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
    def authenticate_codex(self) -> Dict[str, Any]:
        """Verify ChatGPT/Codex API connectivity"""
        if not self.openai_api_key:
            return {
                'authenticated': False,
                'error': 'OpenAI API key not provided',
                'setup_required': True
            }
        
        try:
            # Test API connection with a simple request
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a code assistant for the NEXUS platform."},
                    {"role": "user", "content": "Respond with 'NEXUS_CODEX_CONNECTED' to confirm connectivity."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            if response.choices[0].message.content.strip() == "NEXUS_CODEX_CONNECTED":
                return {
                    'authenticated': True,
                    'model': 'gpt-4o',
                    'codex_ready': True,
                    'connection_verified': True
                }
            else:
                return {
                    'authenticated': True,
                    'model': 'gpt-4o',
                    'codex_ready': True,
                    'response_received': response.choices[0].message.content
                }
                
        except Exception as e:
            return {
                'authenticated': False,
                'error': str(e),
                'connection_failed': True
            }
    
    def generate_nexus_code(self, description: str, code_type: str = "module") -> Dict[str, Any]:
        """Generate NEXUS platform code using ChatGPT Codex"""
        if not self.client:
            return {'error': 'Codex not authenticated'}
        
        system_prompt = f"""You are an expert NEXUS platform developer. Generate production-ready Python code for the NEXUS Singularity Suite enterprise automation platform.

NEXUS Platform Context:
- Flask-based web application with SQLAlchemy database
- Real-time automation and AI integration
- Enterprise-grade security and authentication
- TRAXOVO fleet management integration
- Crypto trading automation
- Browser automation capabilities
- Multi-platform intelligence gathering

Code Requirements:
- Follow NEXUS naming conventions (nexus_*.py)
- Include comprehensive error handling
- Use proper logging and monitoring
- Implement security best practices
- Include detailed docstrings
- Generate {code_type} type code

User Request: {description}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {code_type} code for: {description}"}
                ],
                max_tokens=3000,
                temperature=0.2
            )
            
            generated_code = response.choices[0].message.content
            
            # Extract Python code from response
            code_blocks = self._extract_code_blocks(generated_code)
            
            return {
                'success': True,
                'generated_code': generated_code,
                'code_blocks': code_blocks,
                'tokens_used': response.usage.total_tokens,
                'model': 'gpt-4o',
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'generation_failed': True
            }
    
    def analyze_nexus_codebase(self, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Analyze NEXUS codebase and provide optimization suggestions"""
        if not self.client:
            return {'error': 'Codex not authenticated'}
        
        if file_patterns is None:
            file_patterns = ['app.py', 'nexus_*.py', 'traxovo_*.py']
        
        codebase_analysis = {
            'files_analyzed': [],
            'total_lines': 0,
            'functions_count': 0,
            'classes_count': 0,
            'imports_analysis': {},
            'complexity_score': 0
        }
        
        import glob
        
        for pattern in file_patterns:
            matching_files = glob.glob(pattern)
            
            for file_path in matching_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Analyze file structure
                    tree = ast.parse(content)
                    
                    file_analysis = {
                        'file': file_path,
                        'lines': len(content.splitlines()),
                        'functions': len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]),
                        'classes': len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]),
                        'imports': len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
                    }
                    
                    codebase_analysis['files_analyzed'].append(file_analysis)
                    codebase_analysis['total_lines'] += file_analysis['lines']
                    codebase_analysis['functions_count'] += file_analysis['functions']
                    codebase_analysis['classes_count'] += file_analysis['classes']
                    
                except Exception as e:
                    logging.error(f"Failed to analyze {file_path}: {e}")
        
        # Generate AI-powered analysis
        analysis_prompt = f"""Analyze this NEXUS platform codebase structure and provide optimization recommendations:

Codebase Summary:
- Total files: {len(codebase_analysis['files_analyzed'])}
- Total lines: {codebase_analysis['total_lines']}
- Functions: {codebase_analysis['functions_count']}
- Classes: {codebase_analysis['classes_count']}

Files analyzed: {[f['file'] for f in codebase_analysis['files_analyzed']]}

Provide specific recommendations for:
1. Code organization and modularity
2. Performance optimizations
3. Security enhancements
4. Maintainability improvements
5. NEXUS platform best practices

Format as JSON with recommendations array."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a senior NEXUS platform architect. Provide detailed code analysis and optimization recommendations."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'codebase_structure': codebase_analysis,
                'ai_recommendations': ai_analysis,
                'analysis_timestamp': datetime.now().isoformat(),
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'codebase_structure': codebase_analysis
            }
    
    def generate_nexus_tests(self, module_name: str) -> Dict[str, Any]:
        """Generate comprehensive tests for NEXUS modules"""
        if not self.client:
            return {'error': 'Codex not authenticated'}
        
        # Read module content
        try:
            with open(f"{module_name}.py", 'r', encoding='utf-8') as f:
                module_content = f.read()
        except FileNotFoundError:
            return {'error': f'Module {module_name}.py not found'}
        
        test_prompt = f"""Generate comprehensive pytest test suite for this NEXUS platform module:

Module: {module_name}.py
Content:
{module_content[:4000]}  # Truncate for token limits

Generate tests that cover:
1. Unit tests for all functions and methods
2. Integration tests for database operations
3. API endpoint tests with authentication
4. Error handling and edge cases
5. Security validation tests
6. Real data processing tests

Use pytest fixtures and follow NEXUS testing conventions."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a NEXUS platform test engineer. Generate comprehensive test suites with proper fixtures and mocking."},
                    {"role": "user", "content": test_prompt}
                ],
                max_tokens=3000,
                temperature=0.2
            )
            
            test_code = response.choices[0].message.content
            
            # Save test file
            test_filename = f"test_{module_name}.py"
            code_blocks = self._extract_code_blocks(test_code)
            
            if code_blocks:
                with open(test_filename, 'w', encoding='utf-8') as f:
                    f.write(code_blocks[0])
            
            return {
                'success': True,
                'test_file': test_filename,
                'test_code': test_code,
                'code_blocks': code_blocks,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_nexus_module(self, module_name: str) -> Dict[str, Any]:
        """Optimize existing NEXUS module using AI analysis"""
        if not self.client:
            return {'error': 'Codex not authenticated'}
        
        try:
            with open(f"{module_name}.py", 'r', encoding='utf-8') as f:
                original_code = f.read()
        except FileNotFoundError:
            return {'error': f'Module {module_name}.py not found'}
        
        optimization_prompt = f"""Optimize this NEXUS platform module for better performance, security, and maintainability:

Original Module: {module_name}.py
{original_code}

Optimization Goals:
1. Improve performance and reduce resource usage
2. Enhance error handling and logging
3. Add security validations
4. Improve code structure and readability
5. Add type hints and documentation
6. Optimize database queries and API calls
7. Implement caching where appropriate

Provide the complete optimized code with detailed comments explaining improvements."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a senior NEXUS platform optimization engineer. Provide production-ready optimized code with detailed improvements."},
                    {"role": "user", "content": optimization_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            optimized_code = response.choices[0].message.content
            code_blocks = self._extract_code_blocks(optimized_code)
            
            # Create optimized version
            optimized_filename = f"{module_name}_optimized.py"
            if code_blocks:
                with open(optimized_filename, 'w', encoding='utf-8') as f:
                    f.write(code_blocks[0])
            
            return {
                'success': True,
                'original_file': f"{module_name}.py",
                'optimized_file': optimized_filename,
                'optimized_code': optimized_code,
                'code_blocks': code_blocks,
                'tokens_used': response.usage.total_tokens,
                'optimization_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_documentation(self, modules: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive documentation for NEXUS platform"""
        if not self.client:
            return {'error': 'Codex not authenticated'}
        
        if modules is None:
            import glob
            modules = [f.replace('.py', '') for f in glob.glob('nexus_*.py')]
        
        documentation_sections = []
        
        for module in modules:
            try:
                with open(f"{module}.py", 'r', encoding='utf-8') as f:
                    module_content = f.read()
                
                doc_prompt = f"""Generate comprehensive technical documentation for this NEXUS platform module:

Module: {module}.py
{module_content[:2000]}

Create documentation including:
1. Module overview and purpose
2. Key functions and classes
3. API endpoints (if applicable)
4. Configuration requirements
5. Usage examples
6. Integration notes
7. Security considerations

Format as Markdown with clear sections and code examples."""
                
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {"role": "system", "content": "You are a technical documentation specialist for the NEXUS platform. Create clear, comprehensive documentation."},
                        {"role": "user", "content": doc_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.2
                )
                
                documentation_sections.append({
                    'module': module,
                    'documentation': response.choices[0].message.content
                })
                
            except Exception as e:
                logging.error(f"Failed to document {module}: {e}")
        
        # Compile complete documentation
        complete_docs = "# NEXUS Platform Documentation\n\n"
        complete_docs += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for section in documentation_sections:
            complete_docs += f"## {section['module']}\n\n"
            complete_docs += section['documentation']
            complete_docs += "\n\n---\n\n"
        
        # Save documentation
        with open('NEXUS_DOCUMENTATION.md', 'w', encoding='utf-8') as f:
            f.write(complete_docs)
        
        return {
            'success': True,
            'documentation_file': 'NEXUS_DOCUMENTATION.md',
            'modules_documented': len(documentation_sections),
            'documentation_sections': documentation_sections
        }
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from Codex response"""
        import re
        
        # Find Python code blocks
        python_blocks = re.findall(r'```python\n(.*?)\n```', text, re.DOTALL)
        if python_blocks:
            return python_blocks
        
        # Find generic code blocks
        code_blocks = re.findall(r'```\n(.*?)\n```', text, re.DOTALL)
        if code_blocks:
            return code_blocks
        
        # If no code blocks found, return the full text
        return [text]

# Global instance
codex_connector = NexusCodexConnector()

def connect_chatgpt_codex():
    """Connect to ChatGPT Codex"""
    return codex_connector.authenticate_codex()

def generate_nexus_module(description: str, module_type: str = "automation"):
    """Generate new NEXUS module using AI"""
    return codex_connector.generate_nexus_code(description, module_type)

def analyze_platform():
    """Analyze entire NEXUS platform"""
    return codex_connector.analyze_nexus_codebase()

def optimize_module(module_name: str):
    """Optimize specific NEXUS module"""
    return codex_connector.optimize_nexus_module(module_name)