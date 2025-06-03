"""
TRAXOVO Smart PO System
Intelligent purchase order generation with internal asset validation
"""

import json
import pandas as pd
from datetime import datetime
import os
from internal_eq_tracker import check_internal_equipment

class SmartPOSystem:
    def __init__(self):
        self.po_settings = self.load_po_settings()
        self.po_ledger_file = 'po_ledger.csv'
        
    def load_po_settings(self):
        """Load PO approval settings and limits"""
        default_settings = {
            "divisions": {
                "PMS": {"code": "PM", "approver": "Project Manager", "limit": 5000},
                "PES": {"code": "PE", "approver": "Project Engineer", "limit": 10000},
                "OPS": {"code": "OP", "approver": "Operations Manager", "limit": 15000},
                "ADMIN": {"code": "AD", "approver": "Admin Manager", "limit": 25000}
            },
            "vendor_categories": {
                "Equipment Rental": {"requires_internal_check": True},
                "Materials": {"requires_internal_check": False},
                "Services": {"requires_internal_check": False},
                "Fuel": {"requires_internal_check": False}
            }
        }
        
        try:
            if os.path.exists('po_settings.json'):
                with open('po_settings.json', 'r') as f:
                    return json.load(f)
            else:
                # Create default settings file
                with open('po_settings.json', 'w') as f:
                    json.dump(default_settings, f, indent=2)
                return default_settings
        except Exception as e:
            print(f"Using default PO settings due to error: {e}")
            return default_settings
    
    def generate_po_number(self, division, job_id):
        """Generate unique PO number"""
        division_code = self.po_settings["divisions"].get(division, {}).get("code", "XX")
        date_code = datetime.now().strftime("%m%d")
        
        # Get next sequence number
        sequence = self.get_next_sequence(division_code, date_code)
        
        po_number = f"PO{division_code}{date_code}{sequence:03d}"
        return po_number
    
    def get_next_sequence(self, division_code, date_code):
        """Get next sequence number for PO generation"""
        if os.path.exists(self.po_ledger_file):
            try:
                df = pd.read_csv(self.po_ledger_file)
                today_pos = df[df['PONumber'].str.contains(f"PO{division_code}{date_code}", na=False)]
                return len(today_pos) + 1
            except:
                return 1
        return 1
    
    def validate_po_request(self, division, job_id, vendor, category, total_cost, description):
        """Validate PO request against business rules"""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'internal_alternatives': None
        }
        
        # Check division approval limits
        division_settings = self.po_settings["divisions"].get(division)
        if not division_settings:
            validation_result['errors'].append(f"Invalid division: {division}")
            validation_result['valid'] = False
        elif total_cost > division_settings["limit"]:
            validation_result['errors'].append(f"Amount ${total_cost:,.2f} exceeds {division} limit of ${division_settings['limit']:,.2f}")
            validation_result['valid'] = False
        
        # Check for internal equipment availability (rental prevention)
        category_settings = self.po_settings["vendor_categories"].get(category, {})
        if category_settings.get("requires_internal_check", False):
            # Extract equipment type from description
            equipment_type = self.extract_equipment_type(description)
            if equipment_type:
                internal_check = check_internal_equipment(equipment_type)
                if internal_check['internal_available']:
                    validation_result['warnings'].append(
                        f"⚠️ RENTAL PREVENTION: {internal_check['count']} internal {equipment_type}(s) available"
                    )
                    validation_result['internal_alternatives'] = internal_check
                    validation_result['warnings'].append(
                        f"💰 Potential savings: ${internal_check['potential_savings']:,.2f}/week"
                    )
        
        # Validate job ID format
        if not job_id or len(str(job_id)) < 3:
            validation_result['errors'].append("Invalid job ID format")
            validation_result['valid'] = False
        
        return validation_result
    
    def extract_equipment_type(self, description):
        """Extract equipment type from PO description"""
        equipment_keywords = {
            'excavator': 'Excavator',
            'dozer': 'Dozer', 
            'bulldozer': 'Dozer',
            'loader': 'Loader',
            'truck': 'Truck',
            'crane': 'Crane',
            'compactor': 'Equipment',
            'roller': 'Equipment'
        }
        
        description_lower = description.lower()
        for keyword, category in equipment_keywords.items():
            if keyword in description_lower:
                return category
        
        return None
    
    def create_purchase_order(self, division, job_id, vendor, category, total_cost, description, requested_by):
        """Create new purchase order with validation"""
        
        # Validate request
        validation = self.validate_po_request(division, job_id, vendor, category, total_cost, description)
        
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors'],
                'warnings': validation['warnings']
            }
        
        # Generate PO number
        po_number = self.generate_po_number(division, job_id)
        
        # Create PO record
        po_record = {
            'PONumber': po_number,
            'Division': division,
            'JobID': job_id,
            'Vendor': vendor,
            'Category': category,
            'TotalCost': total_cost,
            'Description': description,
            'RequestedBy': requested_by,
            'Approver': self.po_settings["divisions"][division]["approver"],
            'Status': 'PENDING' if validation['internal_alternatives'] else 'APPROVED',
            'CreatedDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Warnings': '; '.join(validation['warnings']) if validation['warnings'] else None
        }
        
        # Save to ledger
        self.save_to_ledger(po_record)
        
        return {
            'success': True,
            'po_number': po_number,
            'status': po_record['Status'],
            'warnings': validation['warnings'],
            'internal_alternatives': validation['internal_alternatives']
        }
    
    def save_to_ledger(self, po_record):
        """Save PO to ledger file"""
        try:
            if os.path.exists(self.po_ledger_file):
                df = pd.read_csv(self.po_ledger_file)
                df = pd.concat([df, pd.DataFrame([po_record])], ignore_index=True)
            else:
                df = pd.DataFrame([po_record])
            
            df.to_csv(self.po_ledger_file, index=False)
            
        except Exception as e:
            print(f"Error saving to PO ledger: {e}")
    
    def get_po_summary(self):
        """Get PO system summary"""
        if not os.path.exists(self.po_ledger_file):
            return {"total_pos": 0, "total_value": 0, "pending_pos": 0}
        
        try:
            df = pd.read_csv(self.po_ledger_file)
            
            return {
                "total_pos": len(df),
                "total_value": df['TotalCost'].sum(),
                "pending_pos": len(df[df['Status'] == 'PENDING']),
                "approved_pos": len(df[df['Status'] == 'APPROVED']),
                "recent_pos": df.tail(5)[['PONumber', 'Vendor', 'TotalCost', 'Status']].to_dict('records')
            }
        except Exception as e:
            print(f"Error reading PO ledger: {e}")
            return {"error": str(e)}

# Global instance
po_system = SmartPOSystem()

def create_po(division, job_id, vendor, category, total_cost, description, requested_by):
    """Create new purchase order"""
    return po_system.create_purchase_order(division, job_id, vendor, category, total_cost, description, requested_by)

def get_po_summary():
    """Get PO system summary"""
    return po_system.get_po_summary()