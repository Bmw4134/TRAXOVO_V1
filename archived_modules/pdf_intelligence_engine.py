"""
TRAXOVO Document Intelligence Engine
Enterprise-grade PDF parsing with OCR and AI extraction for business documents
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from PyPDF2 import PdfReader
import openai

class DocumentIntelligenceEngine:
    """
    Advanced AI-powered document intelligence for business automation
    Specializes in property tax notices, vehicle registrations, and fleet documents
    """
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Document type templates for structured extraction
        self.document_templates = {
            'property_tax': {
                'fields': ['property_id', 'tax_year', 'assessment_value', 'tax_amount', 
                          'due_date', 'county', 'property_address', 'owner_name'],
                'patterns': ['tax notice', 'assessment', 'property tax', 'appraisal']
            },
            'vehicle_registration': {
                'fields': ['vin', 'license_plate', 'registration_date', 'expiration_date',
                          'vehicle_make', 'vehicle_model', 'vehicle_year', 'owner_name'],
                'patterns': ['registration', 'vehicle', 'vin', 'license plate']
            },
            'insurance_document': {
                'fields': ['policy_number', 'coverage_amount', 'deductible', 'expiration_date',
                          'insurance_company', 'vehicle_vin', 'premium_amount'],
                'patterns': ['insurance', 'policy', 'coverage', 'premium']
            },
            'maintenance_record': {
                'fields': ['service_date', 'vehicle_id', 'mileage', 'service_type',
                          'cost', 'next_service_due', 'parts_replaced', 'technician'],
                'patterns': ['maintenance', 'service', 'repair', 'inspection']
            }
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract raw text from PDF using PyPDF2
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def classify_document_type(self, text: str) -> str:
        """
        Classify document type based on content patterns
        """
        text_lower = text.lower()
        
        for doc_type, template in self.document_templates.items():
            pattern_matches = sum(1 for pattern in template['patterns'] 
                                if pattern in text_lower)
            if pattern_matches >= 2:
                return doc_type
        
        return 'general_business'

    def extract_structured_data(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Use OpenAI GPT to extract structured data from document text
        """
        if not self.openai_api_key:
            return self._fallback_extraction(text, document_type)
        
        try:
            template = self.document_templates.get(document_type, {})
            fields = template.get('fields', [])
            
            prompt = f"""
            Extract the following information from this {document_type.replace('_', ' ')} document:
            
            Fields to extract: {', '.join(fields)}
            
            Document text:
            {text}
            
            Return the data as a JSON object with the field names as keys.
            If a field is not found, use null as the value.
            Ensure dates are in YYYY-MM-DD format where possible.
            """
            
            response = openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are an expert document parser specializing in business documents. Extract only accurate information that is clearly present in the document."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                extracted_data = json.loads(content)
            else:
                return self._fallback_extraction(text, document_type)
            
            # Add metadata
            extracted_data['document_type'] = document_type
            extracted_data['extraction_timestamp'] = datetime.now().isoformat()
            extracted_data['confidence_score'] = self._calculate_confidence(extracted_data)
            
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error in AI extraction: {e}")
            return self._fallback_extraction(text, document_type)

    def _fallback_extraction(self, text: str, document_type: str) -> Dict[str, Any]:
        """
        Fallback extraction using pattern matching when AI is unavailable
        """
        extracted_data = {
            'document_type': document_type,
            'extraction_timestamp': datetime.now().isoformat(),
            'confidence_score': 0.7,
            'raw_text': text[:500] + "..." if len(text) > 500 else text
        }
        
        # Basic pattern matching for common fields
        import re
        
        # Extract dates
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        
        if dates:
            extracted_data['found_dates'] = dates[:3]  # First 3 dates found
        
        # Extract monetary amounts
        money_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.findall(money_pattern, text)
        if amounts:
            extracted_data['found_amounts'] = amounts[:3]
        
        # Extract VINs (17 character alphanumeric)
        vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
        vins = re.findall(vin_pattern, text)
        if vins:
            extracted_data['vin'] = vins[0]
        
        return extracted_data

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on extracted data completeness
        """
        total_fields = len(self.document_templates.get(data.get('document_type', ''), {}).get('fields', []))
        filled_fields = sum(1 for value in data.values() if value is not None and value != "")
        
        if total_fields == 0:
            return 0.8
        
        return min(0.95, max(0.5, filled_fields / total_fields))

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Main processing pipeline for document intelligence
        """
        self.logger.info(f"Processing document: {file_path}")
        
        # Step 1: Extract text
        text = self.extract_text_from_pdf(file_path)
        if not text:
            return {'error': 'Could not extract text from PDF'}
        
        # Step 2: Classify document type
        document_type = self.classify_document_type(text)
        self.logger.info(f"Classified as: {document_type}")
        
        # Step 3: Extract structured data
        extracted_data = self.extract_structured_data(text, document_type)
        
        # Step 4: Generate actionable insights
        insights = self.generate_insights(extracted_data)
        extracted_data['insights'] = insights
        
        return extracted_data

    def generate_insights(self, data: Dict[str, Any]) -> List[str]:
        """
        Generate actionable insights and recommendations
        """
        insights = []
        doc_type = data.get('document_type', '')
        
        if doc_type == 'property_tax':
            if 'due_date' in data and data['due_date']:
                insights.append(f"Property tax due: {data['due_date']} - Schedule payment reminder")
            if 'tax_amount' in data and data['tax_amount']:
                insights.append(f"Tax amount: {data['tax_amount']} - Budget for upcoming payment")
        
        elif doc_type == 'vehicle_registration':
            if 'expiration_date' in data and data['expiration_date']:
                insights.append(f"Registration expires: {data['expiration_date']} - Schedule renewal")
            if 'vin' in data and data['vin']:
                insights.append(f"Update asset manager with VIN: {data['vin']}")
        
        elif doc_type == 'maintenance_record':
            if 'next_service_due' in data and data['next_service_due']:
                insights.append(f"Next service due: {data['next_service_due']} - Schedule maintenance")
            if 'cost' in data and data['cost']:
                insights.append(f"Maintenance cost: {data['cost']} - Update budget tracking")
        
        return insights

    def save_extraction_results(self, data: Dict[str, Any], filename: str) -> str:
        """
        Save extraction results to structured file
        """
        output_dir = 'processed_documents'
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to: {output_path}")
        return output_path

# Global instance
_engine_instance = None

def get_document_intelligence_engine():
    """Get the global document intelligence engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DocumentIntelligenceEngine()
    return _engine_instance