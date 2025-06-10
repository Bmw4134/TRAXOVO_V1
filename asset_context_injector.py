"""
TRAXOVO ∞ Clarity Core - Asset Context Injector
Python-based asset metadata context injection for enterprise intelligence
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class AssetMetadata:
    """Structured asset metadata container"""
    driver_name: str = ""
    raw_id: str = ""
    equipment_type: Optional[str] = None
    department_code: Optional[str] = None
    location_code: Optional[str] = None
    status_code: Optional[str] = None
    project_code: Optional[str] = None
    vin: Optional[str] = None
    original_asset_id: str = ""
    description: str = ""

class AssetContextInjector:
    """Advanced asset context injection system for AI/Agent interactions"""
    
    def __init__(self):
        self.equipment_types = {
            'MT': 'Motor Grader',
            'DT': 'Dump Truck', 
            'EX': 'Excavator',
            'BH': 'Backhoe',
            'CR': 'Crane',
            'LD': 'Loader',
            'BZ': 'Bulldozer',
            'SK': 'Skid Steer',
            'TR': 'Truck',
            'TL': 'Tractor-Trailer',
            'GR': 'Grader',
            'SW': 'Street Sweeper',
            'PV': 'Paving Machine',
            'CM': 'Compactor'
        }
        
        self.asset_pattern = re.compile(
            r'(?:#?\s*)?(?:([A-Z]{2,3})-?)?(\d+)(?:\s*-\s*([^@#\[\{]+?))?'
            r'(?:\s*\[([A-Z]{2,4})\])?(?:\s*@([A-Z0-9]+))?'
            r'(?:\s*\{([A-Z]+)\})?(?:\s*#([A-Z0-9-]+))?'
            r'(?:\s*VIN:([A-Z0-9]{17}))?',
            re.IGNORECASE
        )
    
    def parse_asset_meta(self, asset_id: str) -> AssetMetadata:
        """Parse asset ID into structured metadata"""
        if not asset_id:
            return AssetMetadata()
        
        # Handle parentheses format: "Asset 100 (John Smith)"
        parentheses_match = re.search(r'\(([^)]+)\)', asset_id)
        dash_parts = asset_id.split(" - ")
        
        # Extract driver name
        driver_name = ""
        if len(dash_parts) > 1:
            driver_name = dash_parts[1].strip()
        elif parentheses_match:
            driver_name = parentheses_match.group(1).strip()
        
        # Extract raw ID (all numbers)
        raw_id = re.sub(r'[^0-9]', '', dash_parts[0] if dash_parts else asset_id)
        
        # Enhanced pattern matching for complex asset IDs
        match = self.asset_pattern.search(asset_id)
        equipment_type = match.group(1) if match and match.group(1) else None
        department_code = match.group(4) if match and match.group(4) else None
        location_code = match.group(5) if match and match.group(5) else None
        status_code = match.group(6) if match and match.group(6) else None
        project_code = match.group(7) if match and match.group(7) else None
        vin = match.group(8) if match and match.group(8) else None
        
        # Generate description
        description = self._generate_description(
            equipment_type, raw_id, driver_name, location_code
        )
        
        return AssetMetadata(
            driver_name=driver_name,
            raw_id=raw_id,
            equipment_type=equipment_type,
            department_code=department_code,
            location_code=location_code,
            status_code=status_code,
            project_code=project_code,
            vin=vin,
            original_asset_id=asset_id,
            description=description
        )
    
    def _generate_description(self, equipment_type: str, raw_id: str, 
                            driver_name: str, location_code: str) -> str:
        """Generate human-readable asset description"""
        parts = []
        
        if equipment_type and equipment_type in self.equipment_types:
            parts.append(self.equipment_types[equipment_type])
        
        if raw_id:
            parts.append(f"#{raw_id}")
        
        if driver_name:
            parts.append(f"operated by {driver_name}")
        
        if location_code:
            parts.append(f"at location {location_code}")
        
        return " ".join(parts) if parts else "Unknown Asset"
    
    def extract_asset_ids_from_text(self, text: str) -> List[str]:
        """Extract all potential asset IDs from text"""
        patterns = [
            r'#\d{3,6}\s*-\s*[A-Z\s.]+',  # #210013 - MATTHEW C. SHAYLOR
            r'[A-Z]{2,3}-\d+\s*-\s*[A-Z\s.]+',  # MT-07 - JAMES WILSON
            r'Asset\s+\d+\s*\([^)]+\)',  # Asset 100 (John Smith)
            r'Vehicle\s*#\d+\s*-\s*[A-Z\s.]+',  # Vehicle #500 - Jane Doe
            r'[A-Z]{2,3}-\d+\s*\[[A-Z]+\]\s*@[A-Z]+\s*\{[A-Z]+\}\s*#[0-9-]+',  # Complex format
        ]
        
        asset_ids = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            asset_ids.extend(matches)
        
        return list(set(asset_ids))  # Remove duplicates
    
    def inject_asset_context(self, user_input: str, existing_context: List[str] = None) -> List[str]:
        """Inject asset metadata context into conversation"""
        if existing_context is None:
            existing_context = []
        
        context = existing_context.copy()
        asset_ids = self.extract_asset_ids_from_text(user_input)
        
        if not asset_ids:
            return context
        
        context.append("🔍 ASSET CONTEXT DETECTED:")
        context.append("=" * 50)
        
        for asset_id in asset_ids:
            metadata = self.parse_asset_meta(asset_id)
            
            context.append(f"Asset ID: {asset_id}")
            context.append(f"Description: {metadata.description}")
            
            if metadata.driver_name:
                context.append(f"Operator: {metadata.driver_name}")
            
            if metadata.equipment_type:
                equipment_name = self.equipment_types.get(metadata.equipment_type, metadata.equipment_type)
                context.append(f"Equipment Type: {equipment_name} ({metadata.equipment_type})")
            
            if metadata.location_code:
                context.append(f"Location: {metadata.location_code}")
            
            if metadata.department_code:
                context.append(f"Department: {metadata.department_code}")
            
            if metadata.status_code:
                context.append(f"Status: {metadata.status_code}")
            
            if metadata.project_code:
                context.append(f"Project: {metadata.project_code}")
            
            context.append("-" * 30)
        
        context.append("This context provides asset intelligence for enhanced responses.")
        context.append("")
        
        return context
    
    def generate_smart_suggestions(self, partial_input: str, known_assets: List[str] = None) -> List[str]:
        """Generate intelligent asset suggestions based on partial input"""
        if known_assets is None:
            known_assets = []
        
        suggestions = []
        
        # Filter known assets
        for asset in known_assets:
            if partial_input.lower() in asset.lower():
                suggestions.append(asset)
        
        # Generate pattern-based suggestions
        if len(partial_input) >= 2:
            pattern_suggestions = [
                f"MT-{partial_input} - OPERATOR NAME",
                f"DT-{partial_input} - OPERATOR NAME", 
                f"#{partial_input} - OPERATOR NAME",
                f"EX-{partial_input} - OPERATOR NAME"
            ]
            suggestions.extend(pattern_suggestions)
        
        return suggestions[:10]  # Limit to 10 suggestions
    
    def validate_asset_id(self, asset_id: str) -> Tuple[bool, str]:
        """Validate asset ID format and content"""
        if not asset_id or not isinstance(asset_id, str):
            return False, "Asset ID must be a non-empty string"
        
        if len(asset_id) < 3:
            return False, "Asset ID must be at least 3 characters"
        
        if len(asset_id) > 100:
            return False, "Asset ID must be no more than 100 characters"
        
        if not re.search(r'\d', asset_id):
            return False, "Asset ID must contain at least one numeric digit"
        
        return True, "Valid asset ID"
    
    def batch_process_assets(self, asset_ids: List[str]) -> List[Dict]:
        """Process multiple asset IDs and return metadata"""
        results = []
        
        for asset_id in asset_ids:
            metadata = self.parse_asset_meta(asset_id)
            results.append({
                'original': asset_id,
                'metadata': metadata.__dict__,
                'description': metadata.description,
                'is_valid': self.validate_asset_id(asset_id)[0]
            })
        
        return results
    
    def export_context_json(self, user_input: str) -> str:
        """Export asset context as JSON for API consumption"""
        asset_ids = self.extract_asset_ids_from_text(user_input)
        results = self.batch_process_assets(asset_ids)
        
        return json.dumps({
            'user_input': user_input,
            'detected_assets': len(asset_ids),
            'asset_metadata': results,
            'context_generated': len(results) > 0
        }, indent=2)

# Convenience functions for easy integration
def inject_asset_meta_context(user_input: str, context: List[str] = None) -> List[str]:
    """Quick function to inject asset context into conversation"""
    injector = AssetContextInjector()
    return injector.inject_asset_context(user_input, context)

def parse_asset_from_text(asset_id: str) -> Dict:
    """Quick function to parse single asset ID"""
    injector = AssetContextInjector()
    metadata = injector.parse_asset_meta(asset_id)
    return metadata.__dict__

# Testing and demonstration
if __name__ == "__main__":
    print("TRAXOVO ∞ Clarity Core - Asset Context Injector")
    print("=" * 60)
    
    injector = AssetContextInjector()
    
    # Test cases
    test_inputs = [
        "Check status of #210013 - MATTHEW C. SHAYLOR",
        "MT-07 - JAMES WILSON needs maintenance",
        "Asset 100 (John Smith) is operational", 
        "MT-05 [RD] @FTW {ACTIVE} #2019-044 requires inspection",
        "No assets mentioned in this text"
    ]
    
    print("\n1. Asset Context Injection Tests:")
    print("-" * 40)
    
    for test_input in test_inputs:
        print(f"\nInput: {test_input}")
        context = injector.inject_asset_context(test_input)
        if len(context) > 0:
            for line in context[-5:]:  # Show last 5 context lines
                print(f"  {line}")
        else:
            print("  No asset context detected")
    
    print("\n2. Batch Processing Test:")
    print("-" * 40)
    
    test_assets = [
        "#210013 - MATTHEW C. SHAYLOR",
        "MT-07 - JAMES WILSON", 
        "DT-08 - MARIA RODRIGUEZ"
    ]
    
    results = injector.batch_process_assets(test_assets)
    for result in results:
        print(f"Asset: {result['original']}")
        print(f"Description: {result['description']}")
        print(f"Valid: {result['is_valid']}")
        print()
    
    print("✓ Asset context injection system ready for integration")