"""
TRAXOVO Unified Billing Processor
Consolidated deduplication engine with authentic GAUGE and RAGLE data integration
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from supabase import create_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedBillingProcessor:
    """Intelligent billing processor with semantic deduplication"""
    
    def __init__(self):
        self.similarity_threshold = 0.90
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Supabase connection
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        
        if self.supabase_url and self.supabase_key:
            self.supabase = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None
            logger.warning("Supabase credentials not configured")
    
    def clean_headers(self, df):
        """Remove fluff headers from Excel uploads"""
        df = df.dropna(how="all")
        
        # Look for actual data start
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]
            if row.astype(str).str.contains("Date|Time|Asset|Amount|Cost", case=False, na=False).any():
                df.columns = row
                df = df[idx+1:].reset_index(drop=True)
                break
        
        return df
    
    def handle_upload(self, file_path, table_name='billing_records'):
        """Main upload handler with deduplication"""
        try:
            # Load and clean file
            df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
            df = self.clean_headers(df)
            
            # Get existing records for comparison
            existing_records = self._load_existing_records(table_name)
            
            # Perform deduplication
            results = self._deduplicate_records(df, existing_records)
            
            # Insert new records
            inserted_count = self._insert_records(results['new_records'], table_name)
            
            return {
                'inserted': inserted_count,
                'skipped': len(results['duplicates']),
                'flagged': len(results['similar']),
                'total_processed': len(df)
            }
            
        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            return {'error': str(e), 'inserted': 0, 'skipped': 0, 'flagged': 0}
    
    def _load_existing_records(self, table_name):
        """Load existing records from Supabase"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table(table_name).select("*").execute()
            return response.data
        except Exception as e:
            logger.warning(f"Could not load existing records: {e}")
            return []
    
    def _deduplicate_records(self, new_df, existing_records):
        """Semantic deduplication using sentence transformers"""
        results = {'new_records': [], 'duplicates': [], 'similar': []}
        
        if not existing_records:
            results['new_records'] = new_df.to_dict('records')
            return results
        
        # Create text representations
        new_texts = [" ".join([str(v) for v in row.values()]) for _, row in new_df.iterrows()]
        existing_texts = [" ".join([str(v) for v in record.values()]) for record in existing_records]
        
        # Generate embeddings
        new_vectors = self.model.encode(new_texts)
        existing_vectors = self.model.encode(existing_texts)
        
        # Calculate similarities
        for idx, row in new_df.iterrows():
            row_vector = new_vectors[idx]
            similarities = util.cos_sim(row_vector, existing_vectors)
            max_sim = float(similarities.max()) if len(similarities) > 0 else 0
            
            if max_sim >= self.similarity_threshold:
                results['duplicates'].append({'record': row.to_dict(), 'similarity': max_sim})
            elif max_sim >= 0.75:
                results['similar'].append({'record': row.to_dict(), 'similarity': max_sim})
            else:
                results['new_records'].append(row.to_dict())
        
        return results
    
    def _insert_records(self, records, table_name):
        """Insert new records into Supabase"""
        if not records or not self.supabase:
            return 0
        
        try:
            response = self.supabase.table(table_name).insert(records).execute()
            return len(records)
        except Exception as e:
            logger.error(f"Error inserting records: {e}")
            return 0

# Global processor instance
unified_processor = UnifiedBillingProcessor()

def handle_upload(file_path, table_name='billing_records'):
    """API handler function"""
    return unified_processor.handle_upload(file_path, table_name)