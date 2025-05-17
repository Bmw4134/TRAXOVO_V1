"""
Row ID generator for PM Master processor
"""

import logging

logger = logging.getLogger(__name__)

def generate_row_ids(df):
    """
    Generate unique row IDs for a DataFrame
    
    Args:
        df (DataFrame): Input DataFrame
        
    Returns:
        DataFrame: DataFrame with row_id column added
    """
    try:
        # Add a unique identifier for each row if it doesn't exist
        if 'row_id' not in df.columns:
            # Make sure required columns exist
            for col in ['job_number', 'equipment_id']:
                if col not in df.columns:
                    df[col] = 'unknown'
                    
            # Generate unique row IDs
            df['row_id'] = df.apply(
                lambda row: f"{row['job_number']}_{row['equipment_id']}_{row.name}", 
                axis=1
            )
        return df
    except Exception as e:
        logger.error(f"Error generating row IDs: {str(e)}")
        return df