"""
Smart Employee Mapper Module

This module provides intelligent matching between employee names and asset identifiers.
It uses various pattern matching techniques and caches successful matches for future use.
"""

import os
import re
import sqlite3
import logging
import pandas as pd
from typing import Dict, List, Tuple, Union, Optional, Any
from datetime import datetime
from fuzzywuzzy import fuzz, process
from utils.kaizen import update_employee_asset_mapping, extract_employee_from_asset

logger = logging.getLogger(__name__)

# Constants
EMPLOYEE_CACHE_DB = "data/cache/employee_mappings.db"
NAME_MATCH_THRESHOLD = 80  # Minimum score (0-100) for fuzzy name matching

class EmployeeMapperException(Exception):
    """Exception raised for errors in the employee mapper."""
    pass

class EmployeeMapper:
    """Smart Employee-Asset Mapper"""
    
    def __init__(self):
        """Initialize the employee mapper"""
        self._initialize_cache_db()
        self.employees = {}
        self.assets = {}
        self.mappings = {}
        self.pattern_matches = {}
    
    def _initialize_cache_db(self):
        """Initialize the cache database"""
        os.makedirs(os.path.dirname(EMPLOYEE_CACHE_DB), exist_ok=True)
        
        conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT,
                email TEXT,
                department TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                match_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_employee_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_identifier TEXT NOT NULL,
                employee_id INTEGER,
                confidence REAL NOT NULL,
                method TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                match_count INTEGER DEFAULT 1,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        ''')
        
        # Create indices for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_name ON employees(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asset_identifier ON asset_employee_mappings(asset_identifier)')
        
        conn.commit()
        conn.close()
    
    def _get_employee_id(self, name: str) -> int:
        """
        Get or create an employee ID for the given name.
        
        Args:
            name: Employee name
            
        Returns:
            Employee ID
        """
        if not name:
            raise EmployeeMapperException("Employee name cannot be empty")
        
        # Normalize name
        name = self._normalize_name(name)
        
        conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
        cursor = conn.cursor()
        
        # Check if employee exists
        cursor.execute('SELECT id, match_count FROM employees WHERE name = ?', (name,))
        result = cursor.fetchone()
        
        now = datetime.now().isoformat()
        
        if result:
            # Update existing employee
            employee_id, match_count = result
            
            cursor.execute(
                'UPDATE employees SET last_seen = ?, match_count = ? WHERE id = ?',
                (now, match_count + 1, employee_id)
            )
        else:
            # Insert new employee
            cursor.execute(
                'INSERT INTO employees (name, first_seen, last_seen) VALUES (?, ?, ?)',
                (name, now, now)
            )
            employee_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return employee_id
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize employee name for better matching.
        
        Args:
            name: Employee name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to string if not already
        name = str(name).strip()
        
        # Replace multiple spaces with single space
        name = re.sub(r'\s+', ' ', name)
        
        # Convert to title case
        name = name.title()
        
        return name
    
    def _extract_from_asset_identifier(self, asset_identifier: str) -> Tuple[Optional[str], float, str]:
        """
        Extract employee name from asset identifier using various patterns.
        
        Args:
            asset_identifier: Asset identifier
            
        Returns:
            Tuple of (employee_name, confidence_score, method)
        """
        # Use the kaizen module's extraction function
        return extract_employee_from_asset(asset_identifier)
    
    def _get_mappings_from_cache(self, asset_identifiers: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get mappings from cache.
        
        Args:
            asset_identifiers: List of asset identifiers to get mappings for.
                              If None, get all mappings.
            
        Returns:
            Dictionary mapping asset identifiers to mapping information
        """
        conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT m.asset_identifier, m.confidence, m.method, m.match_count,
                   e.id as employee_id, e.name as employee_name
            FROM asset_employee_mappings m
            JOIN employees e ON m.employee_id = e.id
        '''
        
        params = []
        if asset_identifiers:
            query += ' WHERE m.asset_identifier IN ({})'.format(','.join(['?'] * len(asset_identifiers)))
            params = asset_identifiers
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Build mappings dictionary
        mappings = {}
        for row in rows:
            mappings[row['asset_identifier']] = {
                'employee_id': row['employee_id'],
                'employee_name': row['employee_name'],
                'confidence': row['confidence'],
                'method': row['method'],
                'match_count': row['match_count']
            }
        
        conn.close()
        
        return mappings
    
    def _update_cache_mapping(self, asset_identifier: str, employee_name: str, 
                              confidence: float, method: str) -> bool:
        """
        Update cache with a new mapping.
        
        Args:
            asset_identifier: Asset identifier
            employee_name: Employee name
            confidence: Confidence score (0-1)
            method: Method used to determine the mapping
            
        Returns:
            True if successful, False otherwise
        """
        if not asset_identifier or not employee_name:
            return False
        
        try:
            # Get or create employee ID
            employee_id = self._get_employee_id(employee_name)
            
            conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
            cursor = conn.cursor()
            
            # Check if mapping exists
            cursor.execute(
                'SELECT confidence, match_count FROM asset_employee_mappings WHERE asset_identifier = ?',
                (asset_identifier,)
            )
            result = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if result:
                # Only update if the new confidence is higher or the same method is used
                existing_confidence, match_count = result
                
                if confidence >= existing_confidence:
                    cursor.execute(
                        '''UPDATE asset_employee_mappings 
                           SET employee_id = ?, confidence = ?, method = ?, 
                               last_seen = ?, match_count = ?
                           WHERE asset_identifier = ?''',
                        (employee_id, confidence, method, now, match_count + 1, asset_identifier)
                    )
            else:
                # Insert new mapping
                cursor.execute(
                    '''INSERT INTO asset_employee_mappings 
                       (asset_identifier, employee_id, confidence, method, first_seen, last_seen)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (asset_identifier, employee_id, confidence, method, now, now)
                )
            
            conn.commit()
            conn.close()
            
            # Also update the Kaizen system's mapping for continuous improvement
            update_employee_asset_mapping(asset_identifier, employee_name, confidence, method)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update cache mapping: {e}")
            return False
    
    def analyze_asset_identifiers(self, asset_identifiers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze asset identifiers to extract employee names.
        
        Args:
            asset_identifiers: List of asset identifiers
            
        Returns:
            Dictionary mapping asset identifiers to mapping information
        """
        mappings = {}
        
        # First, get any existing mappings from cache
        cache_mappings = self._get_mappings_from_cache(asset_identifiers)
        mappings.update(cache_mappings)
        
        # For any remaining identifiers, try to extract employee names
        remaining_identifiers = [aid for aid in asset_identifiers if aid not in mappings]
        
        for aid in remaining_identifiers:
            employee_name, confidence, method = self._extract_from_asset_identifier(aid)
            
            if employee_name and confidence > 0.5:  # Only accept if confidence is above 50%
                # Update cache
                self._update_cache_mapping(aid, employee_name, confidence, method)
                
                # Add to result
                mappings[aid] = {
                    'employee_name': employee_name,
                    'confidence': confidence,
                    'method': method
                }
        
        return mappings
    
    def match_dataframe(self, df: pd.DataFrame, asset_col: str, employee_col: str = None) -> pd.DataFrame:
        """
        Match asset identifiers to employee names in a DataFrame.
        
        Args:
            df: DataFrame containing asset identifiers
            asset_col: Name of the column containing asset identifiers
            employee_col: Name of the column containing employee names.
                         If provided, will verify and improve confidence.
                         If None, will add a new column with extracted names.
            
        Returns:
            DataFrame with employee information
        """
        if asset_col not in df.columns:
            raise EmployeeMapperException(f"Column '{asset_col}' not found in DataFrame")
        
        # Get unique asset identifiers
        asset_identifiers = df[asset_col].dropna().unique().tolist()
        
        # Get mappings
        mappings = self.analyze_asset_identifiers(asset_identifiers)
        
        # Create mapping dictionaries
        employee_names = {}
        confidence_scores = {}
        methods = {}
        
        for aid, mapping in mappings.items():
            employee_names[aid] = mapping.get('employee_name', '')
            confidence_scores[aid] = mapping.get('confidence', 0.0)
            methods[aid] = mapping.get('method', '')
        
        # Add columns to DataFrame
        if employee_col and employee_col in df.columns:
            # Verify and improve existing employee names
            matched_indices = []
            
            for idx, row in df.iterrows():
                asset_id = row[asset_col]
                existing_name = row[employee_col]
                
                if asset_id in mappings and existing_name:
                    # Compare existing name with mapped name
                    mapped_name = mappings[asset_id]['employee_name']
                    
                    if existing_name != mapped_name:
                        # Calculate similarity
                        similarity = fuzz.token_sort_ratio(self._normalize_name(existing_name), 
                                                           self._normalize_name(mapped_name))
                        
                        if similarity >= NAME_MATCH_THRESHOLD:
                            # Names are similar, update mapping with higher confidence
                            self._update_cache_mapping(
                                asset_id, existing_name, 
                                max(0.95, mappings[asset_id]['confidence']), 
                                "data_verification"
                            )
                            
                            matched_indices.append(idx)
                        else:
                            # Names are different, keep both but flag
                            df.loc[idx, 'employee_mapped'] = mapped_name
                            df.loc[idx, 'mapping_confidence'] = mappings[asset_id]['confidence']
                            df.loc[idx, 'mapping_method'] = mappings[asset_id]['method']
                            df.loc[idx, 'name_conflict'] = True
                
                elif asset_id in mappings and not existing_name:
                    # No existing name, use mapped name
                    df.loc[idx, employee_col] = mappings[asset_id]['employee_name']
                    df.loc[idx, 'mapping_confidence'] = mappings[asset_id]['confidence']
                    df.loc[idx, 'mapping_method'] = mappings[asset_id]['method']
            
            # Update confidence for matched rows
            if matched_indices:
                df.loc[matched_indices, 'mapping_confidence'] = 0.99
                df.loc[matched_indices, 'mapping_method'] = "data_verification"
        else:
            # Add new columns with mapped employee information
            new_employee_col = employee_col if employee_col else 'employee_name'
            
            df[new_employee_col] = df[asset_col].map(employee_names)
            df['mapping_confidence'] = df[asset_col].map(confidence_scores)
            df['mapping_method'] = df[asset_col].map(methods)
        
        return df
    
    def manual_mapping(self, asset_identifier: str, employee_name: str) -> bool:
        """
        Manually map an asset identifier to an employee name.
        
        Args:
            asset_identifier: Asset identifier
            employee_name: Employee name
            
        Returns:
            True if successful, False otherwise
        """
        return self._update_cache_mapping(asset_identifier, employee_name, 1.0, "manual")
    
    def search_employees(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for employees by name.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching employees
        """
        if not query:
            return []
        
        try:
            conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Use LIKE for basic matching
            cursor.execute(
                '''SELECT id, name, employee_id, email, department, match_count
                   FROM employees
                   WHERE name LIKE ?
                   ORDER BY match_count DESC, name
                   LIMIT ?''',
                (f"%{query}%", limit)
            )
            
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search employees: {e}")
            return []
    
    def get_employee_assets(self, employee_id: int) -> List[Dict[str, Any]]:
        """
        Get all assets mapped to an employee.
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of assets
        """
        try:
            conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                '''SELECT asset_identifier, confidence, method, match_count, last_seen
                   FROM asset_employee_mappings
                   WHERE employee_id = ?
                   ORDER BY last_seen DESC''',
                (employee_id,)
            )
            
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get employee assets: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the employee mapper.
        
        Returns:
            Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(EMPLOYEE_CACHE_DB)
            cursor = conn.cursor()
            
            # Get employee stats
            cursor.execute('SELECT COUNT(*) FROM employees')
            employee_count = cursor.fetchone()[0]
            
            # Get mapping stats
            cursor.execute('SELECT COUNT(*) FROM asset_employee_mappings')
            mapping_count = cursor.fetchone()[0]
            
            # Get confidence stats
            cursor.execute(
                '''SELECT AVG(confidence) as avg_confidence,
                          COUNT(CASE WHEN confidence >= 0.9 THEN 1 END) as high_confidence,
                          COUNT(CASE WHEN confidence < 0.9 AND confidence >= 0.7 THEN 1 END) as medium_confidence,
                          COUNT(CASE WHEN confidence < 0.7 THEN 1 END) as low_confidence
                   FROM asset_employee_mappings'''
            )
            confidence_stats = cursor.fetchone()
            
            # Get method stats
            cursor.execute(
                '''SELECT method, COUNT(*) as count
                   FROM asset_employee_mappings
                   GROUP BY method
                   ORDER BY count DESC'''
            )
            method_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            # Build statistics dictionary
            statistics = {
                "employee_count": employee_count,
                "mapping_count": mapping_count,
                "avg_confidence": confidence_stats[0] if confidence_stats[0] is not None else 0,
                "high_confidence_count": confidence_stats[1],
                "medium_confidence_count": confidence_stats[2],
                "low_confidence_count": confidence_stats[3],
                "method_stats": method_stats
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "employee_count": 0,
                "mapping_count": 0,
                "error": str(e)
            }