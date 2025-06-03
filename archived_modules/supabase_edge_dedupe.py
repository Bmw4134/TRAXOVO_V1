"""
TRAXOVO Billing Deduplication Engine
Supabase-powered intelligent deduplication for billing uploads
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BillingDedupeEngine:
    """Intelligent billing record deduplication with semantic matching"""
    
    def __init__(self):
        self.similarity_threshold = 0.90
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True,
            max_features=1000
        )
        
    def handle_upload(self, file_path, table_name='billing_records'):
        """Main handler for billing file uploads with deduplication"""
        try:
            # Load and clean the uploaded file
            df = self._load_billing_file(file_path)
            
            # Skip fluff header rows
            df = self._skip_fluff_headers(df)
            
            # Load existing records from database
            existing_records = self._load_existing_records(table_name)
            
            # Perform semantic deduplication
            results = self._deduplicate_records(df, existing_records)
            
            # Insert new records
            inserted_count = self._insert_new_records(results['new_records'], table_name)
            
            return {
                'inserted': inserted_count,
                'skipped': len(results['duplicates']),
                'flagged': len(results['similar_records']),
                'total_processed': len(df),
                'similarity_threshold': self.similarity_threshold
            }
            
        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            return {
                'error': str(e),
                'inserted': 0,
                'skipped': 0,
                'flagged': 0
            }
    
    def _load_billing_file(self, file_path):
        """Load billing file with robust Excel handling"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # Try to read Excel file
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                raise ValueError("Unsupported file format")
                
            logger.info(f"Loaded {len(df)} records from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            raise
    
    def _skip_fluff_headers(self, df):
        """Skip unnecessary header rows in Excel uploads"""
        # Look for the first row with substantial data
        for idx, row in df.iterrows():
            # Check if row has meaningful data (not just headers/titles)
            non_null_count = row.count()
            if non_null_count >= 3:  # At least 3 non-null values
                # Check if values look like data rather than headers
                data_indicators = ['$', 'date', 'amount', 'cost', 'revenue']
                row_text = ' '.join(str(val).lower() for val in row if pd.notna(val))
                
                if any(indicator in row_text for indicator in data_indicators):
                    logger.info(f"Starting data extraction from row {idx}")
                    return df.iloc[idx:].reset_index(drop=True)
        
        # If no clear data start found, use original dataframe
        return df
    
    def _load_existing_records(self, table_name):
        """Load existing records from Supabase for comparison"""
        # This would connect to Supabase in production
        # For now, return empty list to simulate first-time upload
        try:
            # Placeholder for Supabase connection
            # supabase = create_client(url, key)
            # response = supabase.table(table_name).select("*").execute()
            # return response.data
            
            logger.info("Loading existing records for deduplication check")
            return []  # Empty for initial implementation
            
        except Exception as e:
            logger.warning(f"Could not load existing records: {e}")
            return []
    
    def _deduplicate_records(self, new_df, existing_records):
        """Perform semantic deduplication using TF-IDF and cosine similarity"""
        results = {
            'new_records': [],
            'duplicates': [],
            'similar_records': []
        }
        
        if not existing_records:
            # No existing records to compare against
            results['new_records'] = new_df.to_dict('records')
            return results
        
        # Convert existing records to comparable format
        existing_df = pd.DataFrame(existing_records)
        
        # Create text representations for comparison
        new_texts = self._create_text_representations(new_df)
        existing_texts = self._create_text_representations(existing_df)
        
        # Vectorize all texts
        all_texts = new_texts + existing_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        
        new_vectors = tfidf_matrix[:len(new_texts)]
        existing_vectors = tfidf_matrix[len(new_texts):]
        
        # Calculate similarities
        similarities = cosine_similarity(new_vectors, existing_vectors)
        
        for idx, (_, row) in enumerate(new_df.iterrows()):
            max_similarity = np.max(similarities[idx]) if len(similarities[idx]) > 0 else 0
            
            if max_similarity >= self.similarity_threshold:
                results['duplicates'].append({
                    'record': row.to_dict(),
                    'similarity': max_similarity
                })
            elif max_similarity >= 0.75:  # Flag as similar but not duplicate
                results['similar_records'].append({
                    'record': row.to_dict(),
                    'similarity': max_similarity
                })
            else:
                results['new_records'].append(row.to_dict())
        
        logger.info(f"Deduplication complete: {len(results['new_records'])} new, "
                   f"{len(results['duplicates'])} duplicates, "
                   f"{len(results['similar_records'])} flagged")
        
        return results
    
    def _create_text_representations(self, df):
        """Create text representations of records for similarity comparison"""
        text_representations = []
        
        for _, row in df.iterrows():
            # Combine key fields into a text representation
            text_parts = []
            
            # Include common billing fields
            for col in ['description', 'item', 'service', 'equipment', 'project', 'date']:
                if col in df.columns and pd.notna(row.get(col)):
                    text_parts.append(str(row[col]))
            
            # Include amount/cost information
            for col in ['amount', 'cost', 'revenue', 'total', 'price']:
                if col in df.columns and pd.notna(row.get(col)):
                    text_parts.append(str(row[col]))
            
            text_representation = ' '.join(text_parts)
            text_representations.append(text_representation)
        
        return text_representations
    
    def _insert_new_records(self, records, table_name):
        """Insert new records into Supabase"""
        if not records:
            return 0
        
        try:
            # Placeholder for Supabase insertion
            # supabase = create_client(url, key)
            # response = supabase.table(table_name).insert(records).execute()
            
            logger.info(f"Would insert {len(records)} new records into {table_name}")
            return len(records)
            
        except Exception as e:
            logger.error(f"Error inserting records: {e}")
            return 0

# Initialize global deduplication engine
dedupe_engine = BillingDedupeEngine()

def handle_upload(file_path, table_name='billing_records'):
    """Main API handler function"""
    return dedupe_engine.handle_upload(file_path, table_name)