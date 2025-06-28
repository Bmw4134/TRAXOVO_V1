"""
TRAXOVO Intelligent Data Analyzer
Uses AI to understand uploaded data and automatically configure dashboards
"""
import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)


class IntelligentDataAnalyzer:
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json', '.txt']
        self.analysis_cache = {}
    
    def analyze_uploaded_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze uploaded file using AI to understand its structure and purpose
        """
        try:
            # Load the data
            data = self._load_data_file(file_path, filename)
            if data is None:
                return {"error": "Could not read file format"}
            
            # Get basic statistics
            stats = self._get_data_statistics(data)
            
            # Get sample of data for AI analysis
            sample_data = self._get_data_sample(data)
            
            # Use AI to understand the data
            ai_analysis = self._analyze_with_ai(sample_data, filename, stats)
            
            # Generate dashboard configuration
            dashboard_config = self._generate_dashboard_config(ai_analysis, data)
            
            return {
                "filename": filename,
                "rows": len(data),
                "columns": list(data.columns) if hasattr(data, 'columns') else [],
                "data_type": ai_analysis.get("data_type", "unknown"),
                "purpose": ai_analysis.get("purpose", "Data analysis"),
                "key_insights": ai_analysis.get("key_insights", []),
                "suggested_charts": ai_analysis.get("suggested_charts", []),
                "dashboard_config": dashboard_config,
                "sample_data": sample_data[:5],  # First 5 rows for preview
                "success": True
            }
        
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "success": False
            }
    
    def _load_data_file(self, file_path: str, filename: str) -> Optional[pd.DataFrame]:
        """Load data from various file formats"""
        try:
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == '.csv':
                return pd.read_csv(file_path)
            elif ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif ext == '.json':
                return pd.read_json(file_path)
            elif ext == '.txt':
                # Try to detect delimiter
                with open(file_path, 'r') as f:
                    first_line = f.readline()
                    if '\t' in first_line:
                        return pd.read_csv(file_path, sep='\t')
                    elif '|' in first_line:
                        return pd.read_csv(file_path, sep='|')
                    else:
                        return pd.read_csv(file_path)
            
            return None
        except Exception:
            return None
    
    def _get_data_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Get basic statistics about the data"""
        stats = {
            "total_rows": len(data),
            "total_columns": len(data.columns),
            "column_types": {},
            "missing_values": {},
            "numeric_columns": [],
            "text_columns": [],
            "date_columns": []
        }
        
        for col in data.columns:
            dtype = str(data[col].dtype)
            stats["column_types"][col] = dtype
            stats["missing_values"][col] = data[col].isnull().sum()
            
            if data[col].dtype in ['int64', 'float64']:
                stats["numeric_columns"].append(col)
            elif data[col].dtype == 'object':
                # Check if it might be dates
                try:
                    pd.to_datetime(data[col].dropna().head(10))
                    stats["date_columns"].append(col)
                except:
                    stats["text_columns"].append(col)
        
        return stats
    
    def _get_data_sample(self, data: pd.DataFrame) -> List[Dict]:
        """Get a sample of the data for AI analysis"""
        sample_size = min(10, len(data))
        sample = data.head(sample_size)
        return sample.to_dict('records')
    
    def _analyze_with_ai(self, sample_data: List[Dict], filename: str, stats: Dict) -> Dict[str, Any]:
        """Use AI to understand what the data represents and how to visualize it"""
        try:
            # Prepare context for AI
            context = {
                "filename": filename,
                "sample_data": sample_data,
                "statistics": {
                    "total_rows": stats["total_rows"],
                    "total_columns": stats["total_columns"],
                    "numeric_columns": stats["numeric_columns"],
                    "text_columns": stats["text_columns"],
                    "date_columns": stats["date_columns"]
                }
            }
            
            prompt = f"""
            Analyze this uploaded data and provide insights in JSON format:
            
            Filename: {filename}
            Data Sample: {json.dumps(sample_data[:3], indent=2)}
            Statistics: {json.dumps(context['statistics'], indent=2)}
            
            Please analyze this data and respond with JSON containing:
            {{
                "data_type": "What type of data this is (e.g., 'sales_data', 'employee_records', 'inventory', 'financial_data', 'customer_data', 'equipment_tracking', etc.)",
                "purpose": "What this data is likely used for in simple terms",
                "key_insights": ["List 3-5 key insights about what this data shows"],
                "suggested_charts": [
                    {{
                        "type": "chart_type (bar, line, pie, scatter, table)",
                        "title": "Chart title",
                        "x_axis": "column_name_for_x",
                        "y_axis": "column_name_for_y",
                        "description": "What this chart would show"
                    }}
                ],
                "dashboard_sections": [
                    {{
                        "title": "Section name",
                        "description": "What this section shows",
                        "metrics": ["key metrics to display"]
                    }}
                ]
            }}
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data analysis expert. Analyze uploaded data and provide intelligent insights about its purpose and best ways to visualize it. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            if result:
                return json.loads(result)
            else:
                raise Exception("Empty response from AI")
        
        except Exception as e:
            # Fallback analysis without AI
            return {
                "data_type": "user_data",
                "purpose": "Data analysis and visualization",
                "key_insights": [
                    f"Contains {stats['total_rows']} records",
                    f"Has {stats['total_columns']} data fields",
                    f"Includes {len(stats['numeric_columns'])} numeric fields"
                ],
                "suggested_charts": [
                    {
                        "type": "table",
                        "title": "Data Overview",
                        "description": "Complete data table view"
                    }
                ],
                "dashboard_sections": [
                    {
                        "title": "Data Overview",
                        "description": "Summary of uploaded data",
                        "metrics": ["Total Records", "Data Fields"]
                    }
                ]
            }
    
    def _generate_dashboard_config(self, ai_analysis: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate dashboard configuration based on AI analysis"""
        config = {
            "title": f"{ai_analysis.get('data_type', 'Data').replace('_', ' ').title()} Dashboard",
            "sections": [],
            "charts": [],
            "kpis": []
        }
        
        # Generate KPIs
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:4]:  # Limit to 4 KPIs
            config["kpis"].append({
                "title": col.replace('_', ' ').title(),
                "value": float(data[col].sum()) if col in data.columns else 0,
                "format": "number"
            })
        
        # Add suggested charts from AI
        for chart in ai_analysis.get("suggested_charts", []):
            if chart.get("x_axis") in data.columns and chart.get("y_axis") in data.columns:
                config["charts"].append(chart)
        
        # Add dashboard sections
        config["sections"] = ai_analysis.get("dashboard_sections", [])
        
        return config
    
    def get_chart_data(self, data: pd.DataFrame, chart_config: Dict) -> Dict[str, Any]:
        """Generate chart data based on configuration"""
        try:
            chart_type = chart_config.get("type", "table")
            x_col = chart_config.get("x_axis")
            y_col = chart_config.get("y_axis")
            
            if chart_type == "bar" and x_col and y_col:
                grouped = data.groupby(x_col)[y_col].sum().reset_index()
                return {
                    "labels": grouped[x_col].tolist(),
                    "data": grouped[y_col].tolist(),
                    "type": "bar"
                }
            
            elif chart_type == "line" and x_col and y_col:
                sorted_data = data.sort_values(x_col)
                return {
                    "labels": sorted_data[x_col].tolist(),
                    "data": sorted_data[y_col].tolist(),
                    "type": "line"
                }
            
            elif chart_type == "pie" and x_col:
                value_counts = data[x_col].value_counts()
                return {
                    "labels": value_counts.index.tolist(),
                    "data": value_counts.values.tolist(),
                    "type": "pie"
                }
            
            else:
                # Return table data
                return {
                    "columns": data.columns.tolist(),
                    "rows": data.head(50).values.tolist(),
                    "type": "table"
                }
        
        except Exception:
            return {
                "columns": data.columns.tolist(),
                "rows": data.head(50).values.tolist(),
                "type": "table"
            }