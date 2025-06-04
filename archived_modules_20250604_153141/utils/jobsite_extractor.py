"""
Job Site Extraction Utilities

This module implements the legacy workbook formulas for extracting job numbers
and locations from various data sources, matching the exact logic used in
your original Excel workbooks.
"""

import re
import pandas as pd
from typing import Optional, Dict, List, Tuple

class JobSiteExtractor:
    """
    Extracts job site information using legacy workbook formulas
    """
    
    def __init__(self):
        # North Texas job site patterns based on legacy workbook
        self.job_patterns = [
            # Standard job number patterns: 2022-008, 2023-032, etc.
            r'(\d{4}-\d{3})',
            # Alternative patterns: 22-008, 23-032
            r'(\d{2}-\d{3})',
            # Project codes: P2022-008, P23-032
            r'P(\d{2,4}-\d{3})',
            # Location-based extraction: "Job 2022-008 DFW"
            r'Job\s+(\d{4}-\d{3})',
            # Equipment billing format
            r'EQMO\.\s+(\d{4}-\d{3})'
        ]
        
        # North Texas location mapping (from legacy workbook)
        self.location_codes = {
            'DFW': 'Dallas-Fort Worth',
            'HOU': 'Houston',
            'WT': 'West Texas',
            'DALLAS': 'Dallas-Fort Worth',
            'FORT WORTH': 'Dallas-Fort Worth',
            'HOUSTON': 'Houston',
            'AUSTIN': 'Austin',
            'SAN ANTONIO': 'San Antonio'
        }
        
        # Division assignments (from legacy workbook logic)
        self.division_mapping = {
            '2022': 'Infrastructure',
            '2023': 'Commercial', 
            '2024': 'Residential',
            '2025': 'Special Projects'
        }

    def extract_job_number(self, location_text: str) -> Optional[str]:
        """
        Extract job number from location text using legacy workbook formulas
        
        Legacy Excel formula equivalent:
        =IF(ISNUMBER(SEARCH("2024-",A1)),MID(A1,SEARCH("2024-",A1),8),
          IF(ISNUMBER(SEARCH("2023-",A1)),MID(A1,SEARCH("2023-",A1),8),
            IF(ISNUMBER(SEARCH("2022-",A1)),MID(A1,SEARCH("2022-",A1),8),"")))
        """
        if not location_text or pd.isna(location_text):
            return None
            
        location_text = str(location_text).upper().strip()
        
        # Apply each pattern in priority order
        for pattern in self.job_patterns:
            match = re.search(pattern, location_text)
            if match:
                job_num = match.group(1)
                # Ensure 4-digit year format
                if len(job_num.split('-')[0]) == 2:
                    year = '20' + job_num.split('-')[0]
                    job_num = year + '-' + job_num.split('-')[1]
                return job_num
        
        return None

    def extract_location_code(self, location_text: str) -> Optional[str]:
        """
        Extract location code from text using legacy workbook logic
        
        Legacy Excel formula equivalent:
        =IF(ISNUMBER(SEARCH("DFW",A1)),"DFW",
          IF(ISNUMBER(SEARCH("HOU",A1)),"HOU",
            IF(ISNUMBER(SEARCH("WT",A1)),"WT","UNKNOWN")))
        """
        if not location_text or pd.isna(location_text):
            return None
            
        location_text = str(location_text).upper().strip()
        
        # Check for location codes in priority order
        for code, full_name in self.location_codes.items():
            if code in location_text or full_name.upper() in location_text:
                return code
                
        return None

    def assign_division(self, job_number: str) -> str:
        """
        Assign division based on job number year
        
        Legacy workbook logic: =LEFT(A1,4) then lookup division
        """
        if not job_number:
            return 'Unassigned'
            
        try:
            year = job_number.split('-')[0]
            return self.division_mapping.get(year, 'Special Projects')
        except:
            return 'Unassigned'

    def process_location_data(self, df: pd.DataFrame, location_column: str = 'Location') -> pd.DataFrame:
        """
        Process entire dataframe to extract job sites using legacy formulas
        
        Args:
            df: DataFrame with location data
            location_column: Name of the column containing location text
            
        Returns:
            Enhanced DataFrame with job site information
        """
        result_df = df.copy()
        
        # Extract job numbers
        result_df['JobNumber'] = result_df[location_column].apply(self.extract_job_number)
        
        # Extract location codes
        result_df['LocationCode'] = result_df[location_column].apply(self.extract_location_code)
        
        # Assign divisions
        result_df['Division'] = result_df['JobNumber'].apply(self.assign_division)
        
        # Create full job site identifier
        result_df['JobSite'] = result_df.apply(
            lambda row: f"{row['JobNumber']} - {row['LocationCode']}" 
            if row['JobNumber'] and row['LocationCode'] 
            else row['JobNumber'] or 'UNASSIGNED', 
            axis=1
        )
        
        return result_df

    def get_job_site_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate job site summary statistics
        """
        processed_df = self.process_location_data(df)
        
        return {
            'total_records': len(processed_df),
            'identified_jobs': processed_df['JobNumber'].notna().sum(),
            'unassigned_locations': processed_df['JobNumber'].isna().sum(),
            'active_job_sites': processed_df['JobSite'].nunique(),
            'divisions': processed_df['Division'].value_counts().to_dict(),
            'location_breakdown': processed_df['LocationCode'].value_counts().to_dict()
        }

def extract_job_from_activity_detail(activity_text: str) -> Optional[str]:
    """
    Standalone function for extracting job numbers from Activity Detail
    Matches legacy workbook VLOOKUP logic
    """
    extractor = JobSiteExtractor()
    return extractor.extract_job_number(activity_text)

def extract_job_from_driving_history(location_text: str) -> Optional[str]:
    """
    Standalone function for extracting job numbers from Driving History
    Matches legacy workbook INDEX/MATCH logic
    """
    extractor = JobSiteExtractor()
    return extractor.extract_job_number(location_text)