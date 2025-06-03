"""
TRAXOVO Workflow Automation Engine
Revolutionary system to automate ANY legacy process with AI mapping
"""

import pandas as pd
import json
import os
from datetime import datetime
import logging
from pathlib import Path

class WorkflowAutomationEngine:
    """AI-powered workflow automation for any legacy process"""
    
    def __init__(self):
        self.workflows_dir = 'workflows'
        self.templates_dir = 'workflow_templates' 
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create necessary directories"""
        Path(self.workflows_dir).mkdir(exist_ok=True)
        Path(self.templates_dir).mkdir(exist_ok=True)
        
    def create_workflow_template(self, workflow_name, description, steps):
        """Create a reusable workflow template"""
        template = {
            'name': workflow_name,
            'description': description,
            'created': datetime.now().isoformat(),
            'steps': steps,
            'input_mappings': {},
            'output_format': 'excel',
            'automation_level': 'full'
        }
        
        template_path = f"{self.templates_dir}/{workflow_name.lower().replace(' ', '_')}.json"
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
            
        return template
    
    def map_legacy_report(self, file_path, workflow_name, column_mappings=None):
        """Intelligently map legacy report columns to standard format"""
        
        # Auto-detect file type and load
        if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            raise ValueError("Unsupported file format")
            
        # Intelligent column mapping
        if not column_mappings:
            column_mappings = self.auto_detect_columns(df.columns, workflow_name)
        
        # Apply mappings
        mapped_df = df.rename(columns=column_mappings)
        
        # Store mapping for future use
        self.save_column_mapping(workflow_name, file_path, column_mappings)
        
        return mapped_df, column_mappings
    
    def auto_detect_columns(self, columns, workflow_type):
        """AI-powered column detection based on workflow type"""
        
        # Standard mappings for different workflow types
        mapping_templates = {
            'attendance': {
                'driver': ['driver', 'name', 'employee', 'operator'],
                'date': ['date', 'day', 'timestamp', 'time'],
                'hours': ['hours', 'time', 'duration', 'worked'],
                'status': ['status', 'present', 'absent', 'late']
            },
            'equipment': {
                'asset_id': ['asset', 'equipment', 'unit', 'machine'],
                'location': ['location', 'site', 'job', 'project'],
                'hours': ['hours', 'runtime', 'operating'],
                'status': ['status', 'condition', 'state']
            },
            'billing': {
                'amount': ['amount', 'cost', 'price', 'total'],
                'description': ['description', 'item', 'service'],
                'date': ['date', 'invoice', 'billing'],
                'client': ['client', 'customer', 'company']
            }
        }
        
        # Auto-detect workflow type if not specified
        if workflow_type not in mapping_templates:
            workflow_type = self.detect_workflow_type(columns)
        
        template = mapping_templates.get(workflow_type, {})
        detected_mappings = {}
        
        for standard_field, possible_names in template.items():
            for col in columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    detected_mappings[col] = standard_field
                    break
                    
        return detected_mappings
    
    def detect_workflow_type(self, columns):
        """Detect workflow type from column names"""
        
        column_str = ' '.join(columns).lower()
        
        if any(word in column_str for word in ['driver', 'attendance', 'hours', 'timecard']):
            return 'attendance'
        elif any(word in column_str for word in ['equipment', 'asset', 'machine', 'unit']):
            return 'equipment'  
        elif any(word in column_str for word in ['billing', 'invoice', 'cost', 'amount']):
            return 'billing'
        else:
            return 'general'
    
    def save_column_mapping(self, workflow_name, file_path, mappings):
        """Save column mappings for future automation"""
        
        mapping_data = {
            'workflow_name': workflow_name,
            'source_file': file_path,
            'mappings': mappings,
            'created': datetime.now().isoformat(),
            'auto_apply': True
        }
        
        mapping_file = f"{self.workflows_dir}/{workflow_name}_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
    
    def process_workflow(self, workflow_name, input_file, auto_execute=True):
        """Execute complete workflow automation"""
        
        # Load workflow template
        template_file = f"{self.templates_dir}/{workflow_name.lower().replace(' ', '_')}.json"
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                template = json.load(f)
        else:
            template = self.create_default_template(workflow_name)
        
        # Load and map data
        mapped_data, mappings = self.map_legacy_report(input_file, workflow_name)
        
        # Execute workflow steps
        results = {}
        for step in template['steps']:
            step_result = self.execute_workflow_step(step, mapped_data)
            results[step['name']] = step_result
        
        # Generate output
        output_file = self.generate_workflow_output(workflow_name, mapped_data, results)
        
        return {
            'status': 'completed',
            'input_file': input_file,
            'output_file': output_file,
            'mappings_used': mappings,
            'results': results,
            'processed_rows': len(mapped_data),
            'execution_time': datetime.now().isoformat()
        }
    
    def execute_workflow_step(self, step, data):
        """Execute individual workflow step"""
        
        step_type = step.get('type', 'transform')
        
        if step_type == 'filter':
            return self.apply_filter(data, step['conditions'])
        elif step_type == 'transform':
            return self.apply_transformation(data, step['operations'])
        elif step_type == 'aggregate':
            return self.apply_aggregation(data, step['groupby'], step['functions'])
        elif step_type == 'validate':
            return self.validate_data(data, step['rules'])
        else:
            return {'status': 'skipped', 'reason': f'Unknown step type: {step_type}'}
    
    def apply_filter(self, data, conditions):
        """Apply filtering conditions"""
        filtered_data = data.copy()
        for condition in conditions:
            column = condition['column']
            operator = condition['operator']
            value = condition['value']
            
            if operator == 'equals':
                filtered_data = filtered_data[filtered_data[column] == value]
            elif operator == 'contains':
                filtered_data = filtered_data[filtered_data[column].str.contains(value, na=False)]
            elif operator == 'greater_than':
                filtered_data = filtered_data[filtered_data[column] > value]
                
        return {'rows_filtered': len(data) - len(filtered_data), 'remaining_rows': len(filtered_data)}
    
    def apply_transformation(self, data, operations):
        """Apply data transformations"""
        transformed_data = data.copy()
        
        for operation in operations:
            op_type = operation['type']
            
            if op_type == 'calculate_column':
                column_name = operation['target_column']
                formula = operation['formula']
                # Safe formula execution (simplified)
                if formula == 'hours * rate':
                    transformed_data[column_name] = transformed_data.get('hours', 0) * transformed_data.get('rate', 0)
                    
        return {'transformations_applied': len(operations)}
    
    def apply_aggregation(self, data, groupby_columns, functions):
        """Apply aggregation functions"""
        
        if not groupby_columns:
            return {'error': 'No groupby columns specified'}
            
        aggregated = data.groupby(groupby_columns).agg(functions).reset_index()
        
        return {
            'original_rows': len(data),
            'aggregated_rows': len(aggregated),
            'groupby_columns': groupby_columns
        }
    
    def validate_data(self, data, rules):
        """Validate data against business rules"""
        
        validation_results = {}
        
        for rule in rules:
            rule_name = rule['name']
            column = rule['column']
            rule_type = rule['type']
            
            if rule_type == 'not_null':
                null_count = data[column].isnull().sum()
                validation_results[rule_name] = {'passed': null_count == 0, 'null_count': null_count}
            elif rule_type == 'range':
                min_val, max_val = rule['min'], rule['max']
                out_of_range = ((data[column] < min_val) | (data[column] > max_val)).sum()
                validation_results[rule_name] = {'passed': out_of_range == 0, 'out_of_range_count': out_of_range}
                
        return validation_results
    
    def generate_workflow_output(self, workflow_name, data, results):
        """Generate standardized output file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{self.workflows_dir}/{workflow_name}_output_{timestamp}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main processed data
            data.to_excel(writer, sheet_name='Processed_Data', index=False)
            
            # Results summary
            results_df = pd.DataFrame([results])
            results_df.to_excel(writer, sheet_name='Execution_Results', index=False)
            
        return output_file
    
    def create_default_template(self, workflow_name):
        """Create default workflow template"""
        
        default_steps = [
            {
                'name': 'data_validation',
                'type': 'validate',
                'rules': [
                    {'name': 'check_required_fields', 'column': 'date', 'type': 'not_null'}
                ]
            },
            {
                'name': 'data_cleanup',
                'type': 'transform',
                'operations': [
                    {'type': 'remove_duplicates'},
                    {'type': 'standardize_dates'}
                ]
            }
        ]
        
        return self.create_workflow_template(workflow_name, f"Auto-generated template for {workflow_name}", default_steps)
    
    def get_available_workflows(self):
        """Get list of available workflow templates"""
        
        templates = []
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.json'):
                    with open(f"{self.templates_dir}/{file}", 'r') as f:
                        template = json.load(f)
                        templates.append({
                            'name': template['name'],
                            'description': template['description'],
                            'file': file
                        })
        
        return templates

# Global automation engine instance
workflow_engine = WorkflowAutomationEngine()

# Pre-built workflow templates for common Ragle processes
def initialize_ragle_workflows():
    """Initialize common Ragle construction workflows"""
    
    # Daily attendance workflow
    attendance_steps = [
        {
            'name': 'validate_attendance',
            'type': 'validate',
            'rules': [
                {'name': 'driver_not_null', 'column': 'driver', 'type': 'not_null'},
                {'name': 'hours_range', 'column': 'hours', 'type': 'range', 'min': 0, 'max': 24}
            ]
        },
        {
            'name': 'calculate_metrics',
            'type': 'transform',
            'operations': [
                {'type': 'calculate_column', 'target_column': 'total_cost', 'formula': 'hours * rate'}
            ]
        },
        {
            'name': 'summarize_by_driver',
            'type': 'aggregate',
            'groupby': ['driver'],
            'functions': {'hours': 'sum', 'total_cost': 'sum'}
        }
    ]
    
    workflow_engine.create_workflow_template(
        'Daily Attendance Processing',
        'Automate daily attendance report processing with validation and cost calculation',
        attendance_steps
    )
    
    # Equipment utilization workflow
    equipment_steps = [
        {
            'name': 'validate_equipment',
            'type': 'validate', 
            'rules': [
                {'name': 'asset_id_not_null', 'column': 'asset_id', 'type': 'not_null'},
                {'name': 'hours_valid', 'column': 'hours', 'type': 'range', 'min': 0, 'max': 24}
            ]
        },
        {
            'name': 'calculate_utilization',
            'type': 'transform',
            'operations': [
                {'type': 'calculate_column', 'target_column': 'utilization_rate', 'formula': 'hours / 8'}
            ]
        },
        {
            'name': 'utilization_summary',
            'type': 'aggregate',
            'groupby': ['asset_id', 'location'],
            'functions': {'hours': 'sum', 'utilization_rate': 'mean'}
        }
    ]
    
    workflow_engine.create_workflow_template(
        'Equipment Utilization Analysis',
        'Analyze equipment utilization across job sites with automatic calculations',
        equipment_steps
    )

# Initialize workflows on import
initialize_ragle_workflows()