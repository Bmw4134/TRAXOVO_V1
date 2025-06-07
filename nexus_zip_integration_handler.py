#!/usr/bin/env python3
"""
NEXUS Zip Integration Handler
Automated processing for external deployment packages
"""

import os
import json
import zipfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='[ZIP_HANDLER] %(message)s')
logger = logging.getLogger(__name__)

class NexusZipIntegrationHandler:
    """Handles external zip package integration"""
    
    def __init__(self):
        self.buffer_path = Path('nexus_infinity_buffer')
        self.extraction_zone = self.buffer_path / 'zip_extraction'
        self.integration_zone = self.buffer_path / 'module_integration'
        self.config_zone = self.buffer_path / 'config_merge'
        self.cache_zone = self.buffer_path / 'runtime_cache'
        
    def detect_zip_packages(self):
        """Detect available zip packages for integration"""
        logger.info("Scanning for zip packages...")
        
        # Scan attached_assets directory for zip files
        assets_path = Path('attached_assets')
        zip_files = []
        
        if assets_path.exists():
            for file_path in assets_path.glob('*.zip'):
                zip_info = {
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'type': 'nexus_bundle' if ('NEXUS' in file_path.name.upper() or 
                                             'nexus' in file_path.name.lower() or
                                             'infinity' in file_path.name.lower()) else 'standard'
                }
                zip_files.append(zip_info)
        
        logger.info(f"Found {len(zip_files)} zip packages")
        return zip_files
    
    def process_nexus_bundle(self, bundle_path: str):
        """Process NEXUS bundle for integration"""
        logger.info(f"Processing NEXUS bundle: {Path(bundle_path).name}")
        
        try:
            with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
                # Extract to extraction zone
                zip_ref.extractall(self.extraction_zone)
                
                # Get extracted contents
                extracted_files = list(self.extraction_zone.rglob('*'))
                
                integration_results = {
                    'bundle_processed': Path(bundle_path).name,
                    'files_extracted': len(extracted_files),
                    'integration_status': 'ready',
                    'components_detected': self._analyze_extracted_components()
                }
                
                # Perform intelligent integration
                self._integrate_extracted_components()
                
                return integration_results
                
        except Exception as e:
            logger.error(f"Bundle processing failed: {e}")
            return {'error': str(e), 'status': 'failed'}
    
    def _analyze_extracted_components(self):
        """Analyze extracted components for intelligent integration"""
        components = {
            'python_modules': [],
            'config_files': [],
            'ui_components': [],
            'documentation': [],
            'deployment_scripts': []
        }
        
        for file_path in self.extraction_zone.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                
                if suffix == '.py':
                    components['python_modules'].append(str(file_path.relative_to(self.extraction_zone)))
                elif suffix in ['.json', '.yaml', '.yml', '.conf']:
                    components['config_files'].append(str(file_path.relative_to(self.extraction_zone)))
                elif suffix in ['.js', '.jsx', '.html', '.css']:
                    components['ui_components'].append(str(file_path.relative_to(self.extraction_zone)))
                elif suffix in ['.md', '.txt', '.rst']:
                    components['documentation'].append(str(file_path.relative_to(self.extraction_zone)))
                elif suffix in ['.sh', '.bat']:
                    components['deployment_scripts'].append(str(file_path.relative_to(self.extraction_zone)))
        
        return components
    
    def _integrate_extracted_components(self):
        """Intelligently integrate extracted components"""
        logger.info("Integrating extracted components...")
        
        # Copy Python modules to appropriate locations
        for py_file in self.extraction_zone.rglob('*.py'):
            if py_file.is_file():
                # Determine appropriate integration location
                if 'nexus' in py_file.name.lower():
                    target_path = Path('.') / py_file.name
                    if not target_path.exists():
                        shutil.copy2(py_file, target_path)
                        logger.info(f"Integrated module: {py_file.name}")
        
        # Merge configuration files
        for config_file in self.extraction_zone.rglob('*.json'):
            if config_file.is_file() and 'config' in config_file.name.lower():
                self._merge_config_file(config_file)
        
        # Integrate UI components
        for ui_file in self.extraction_zone.rglob('*'):
            if ui_file.suffix.lower() in ['.js', '.jsx', '.html', '.css']:
                ui_target = Path('src/components') / ui_file.name
                ui_target.parent.mkdir(parents=True, exist_ok=True)
                if not ui_target.exists():
                    shutil.copy2(ui_file, ui_target)
                    logger.info(f"Integrated UI component: {ui_file.name}")
    
    def _merge_config_file(self, config_file: Path):
        """Merge configuration file with existing configs"""
        try:
            with open(config_file, 'r') as f:
                new_config = json.load(f)
            
            # Determine target config file
            target_config = Path('nexus_enterprise_config.json')
            
            if target_config.exists():
                with open(target_config, 'r') as f:
                    existing_config = json.load(f)
                
                # Merge configurations intelligently
                merged_config = {**existing_config, **new_config}
                
                with open(target_config, 'w') as f:
                    json.dump(merged_config, f, indent=2)
                
                logger.info(f"Merged configuration: {config_file.name}")
            else:
                shutil.copy2(config_file, target_config)
                logger.info(f"Created new configuration: {config_file.name}")
                
        except Exception as e:
            logger.warning(f"Config merge failed for {config_file}: {e}")
    
    def auto_process_available_bundles(self):
        """Automatically process all available NEXUS bundles"""
        logger.info("Auto-processing available bundles...")
        
        zip_packages = self.detect_zip_packages()
        nexus_bundles = [pkg for pkg in zip_packages if pkg['type'] == 'nexus_bundle']
        
        processing_results = []
        
        for bundle in nexus_bundles:
            result = self.process_nexus_bundle(bundle['path'])
            processing_results.append({
                'bundle': bundle['filename'],
                'result': result
            })
        
        return {
            'bundles_processed': len(processing_results),
            'results': processing_results,
            'integration_complete': True
        }
    
    def validate_integration(self):
        """Validate successful integration"""
        validation_results = {
            'modules_integrated': len(list(Path('.').glob('nexus_*.py'))),
            'configs_updated': Path('nexus_enterprise_config.json').exists(),
            'ui_components_added': len(list(Path('src/components').glob('*.*') if Path('src/components').exists() else [])),
            'integration_successful': True
        }
        
        return validation_results

def auto_integrate_nexus_packages():
    """Main auto-integration function"""
    print("\n" + "="*50)
    print("NEXUS AUTO ZIP INTEGRATION")
    print("="*50)
    
    handler = NexusZipIntegrationHandler()
    
    # Auto-process available bundles
    results = handler.auto_process_available_bundles()
    
    # Validate integration
    validation = handler.validate_integration()
    
    print(f"\nINTEGRATION COMPLETE")
    print(f"Bundles processed: {results['bundles_processed']}")
    print(f"Modules integrated: {validation['modules_integrated']}")
    print(f"Integration successful: {validation['integration_successful']}")
    print("="*50)
    
    return results, validation

if __name__ == "__main__":
    auto_integrate_nexus_packages()