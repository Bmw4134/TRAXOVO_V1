"""
QQ Unified Asset Status Analyzer
Comprehensive active vs inactive asset detection using authentic Fort Worth data
Integrates all existing filtering logic into a single authoritative system
"""

import json
import sqlite3
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QQUnifiedAssetStatusAnalyzer:
    """
    Unified asset status analyzer that combines all existing filtering logic
    to provide definitive active vs inactive asset classification
    """
    
    def __init__(self):
        self.db_path = "qq_unified_asset_status.db"
        self.inactive_keywords = [
            'sold', 'disposed', 'stolen', 'inactive', 'retired', 'scrapped',
            'out of service', 'decommissioned', 'transferred', 'salvage',
            'maintenance', 'repair', 'down', 'broken', 'damaged'
        ]
        self.excluded_types = [
            'trailer without gps', 'non-powered equipment', 'static equipment',
            'office equipment', 'tools', 'small tools'
        ]
        self.utilization_thresholds = {
            'critical_inactive': 0,      # 0% utilization = definitely inactive
            'likely_inactive': 15,       # <15% utilization = likely inactive
            'low_active': 40,           # 40-60% = low but active
            'optimal_active': 80        # >80% = optimal active
        }
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize unified asset status tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_status_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT UNIQUE NOT NULL,
                asset_name TEXT,
                status_classification TEXT NOT NULL,
                confidence_score REAL,
                last_activity_date TEXT,
                utilization_rate REAL,
                operational_status TEXT,
                gps_enabled BOOLEAN,
                days_inactive INTEGER,
                classification_reasons TEXT,
                last_analysis TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT,
                change_reason TEXT,
                confidence_change REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Unified asset status database initialized")
    
    def analyze_asset_status(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive asset status analysis using all available criteria
        
        Args:
            asset: Asset dictionary with all available data
            
        Returns:
            Dictionary with detailed status classification
        """
        asset_id = asset.get('asset_id', asset.get('AssetIdentifier', 'unknown'))
        asset_name = asset.get('asset_name', asset.get('Label', 'Unknown'))
        
        # Initialize analysis result
        analysis = {
            'asset_id': asset_id,
            'asset_name': asset_name,
            'status_classification': 'unknown',
            'confidence_score': 0.0,
            'classification_reasons': [],
            'activity_indicators': {},
            'recommendation': 'no_action'
        }
        
        confidence_factors = []
        
        # 1. Check explicit operational status
        operational_status = asset.get('operational_status', asset.get('status', '')).lower()
        if operational_status:
            if any(keyword in operational_status for keyword in self.inactive_keywords):
                analysis['status_classification'] = 'inactive'
                confidence_factors.append(('explicit_status_inactive', 0.9))
                analysis['classification_reasons'].append(f"Explicit status: {operational_status}")
            elif operational_status in ['active', 'operational', 'working', 'deployed']:
                confidence_factors.append(('explicit_status_active', 0.8))
                analysis['classification_reasons'].append(f"Explicit active status: {operational_status}")
        
        # 2. Analyze utilization rate
        utilization_rate = self._extract_utilization_rate(asset)
        if utilization_rate is not None:
            analysis['activity_indicators']['utilization_rate'] = utilization_rate
            
            if utilization_rate <= self.utilization_thresholds['critical_inactive']:
                analysis['status_classification'] = 'inactive'
                confidence_factors.append(('zero_utilization', 0.95))
                analysis['classification_reasons'].append("Zero utilization rate")
            elif utilization_rate <= self.utilization_thresholds['likely_inactive']:
                confidence_factors.append(('low_utilization_inactive', 0.7))
                analysis['classification_reasons'].append(f"Very low utilization: {utilization_rate}%")
            elif utilization_rate >= self.utilization_thresholds['optimal_active']:
                confidence_factors.append(('high_utilization_active', 0.8))
                analysis['classification_reasons'].append(f"High utilization: {utilization_rate}%")
        
        # 3. Check GPS and location data
        gps_enabled = self._check_gps_capability(asset)
        analysis['activity_indicators']['gps_enabled'] = gps_enabled
        
        if not gps_enabled:
            confidence_factors.append(('no_gps_likely_inactive', 0.6))
            analysis['classification_reasons'].append("No GPS tracking capability")
        
        # 4. Analyze last activity date
        last_activity = self._extract_last_activity(asset)
        if last_activity:
            days_inactive = (datetime.now() - last_activity).days
            analysis['activity_indicators']['days_inactive'] = days_inactive
            
            if days_inactive > 30:
                confidence_factors.append(('long_term_inactive', 0.8))
                analysis['classification_reasons'].append(f"No activity for {days_inactive} days")
            elif days_inactive > 7:
                confidence_factors.append(('short_term_inactive', 0.5))
                analysis['classification_reasons'].append(f"Inactive for {days_inactive} days")
            else:
                confidence_factors.append(('recent_activity', 0.7))
                analysis['classification_reasons'].append(f"Recent activity: {days_inactive} days ago")
        
        # 5. Check asset type exclusions
        asset_type = asset.get('asset_type', asset.get('AssetCategory', '')).lower()
        if any(excluded in asset_type for excluded in self.excluded_types):
            analysis['status_classification'] = 'excluded'
            confidence_factors.append(('excluded_type', 1.0))
            analysis['classification_reasons'].append(f"Excluded asset type: {asset_type}")
        
        # 6. Analyze fuel level (if available)
        fuel_level = asset.get('fuel_level')
        if fuel_level is not None:
            analysis['activity_indicators']['fuel_level'] = fuel_level
            if fuel_level > 50:
                confidence_factors.append(('adequate_fuel', 0.6))
                analysis['classification_reasons'].append("Adequate fuel level")
            elif fuel_level == 0:
                confidence_factors.append(('no_fuel_inactive', 0.4))
                analysis['classification_reasons'].append("Zero fuel level")
        
        # 7. Check maintenance status
        maintenance_status = asset.get('maintenance_status', '').lower()
        if 'required' in maintenance_status or 'overdue' in maintenance_status:
            confidence_factors.append(('maintenance_required', 0.3))
            analysis['classification_reasons'].append(f"Maintenance status: {maintenance_status}")
        
        # Calculate final confidence score and classification
        if confidence_factors:
            # Weight confidence factors
            weighted_scores = []
            for factor, score in confidence_factors:
                if 'inactive' in factor:
                    weighted_scores.append(score * -1)  # Negative for inactive indicators
                else:
                    weighted_scores.append(score)  # Positive for active indicators
            
            # Calculate weighted average
            total_weight = sum(abs(score) for _, score in confidence_factors)
            weighted_sum = sum(weighted_scores)
            
            if total_weight > 0:
                confidence_ratio = weighted_sum / total_weight
                analysis['confidence_score'] = abs(confidence_ratio)
                
                # Final classification logic
                if analysis['status_classification'] == 'unknown':
                    if confidence_ratio < -0.3:
                        analysis['status_classification'] = 'inactive'
                    elif confidence_ratio > 0.3:
                        analysis['status_classification'] = 'active'
                    else:
                        analysis['status_classification'] = 'uncertain'
        
        # Generate recommendation
        analysis['recommendation'] = self._generate_recommendation(analysis)
        
        # Store analysis results
        self._store_analysis_result(analysis)
        
        return analysis
    
    def _extract_utilization_rate(self, asset: Dict[str, Any]) -> Optional[float]:
        """Extract utilization rate from various possible fields"""
        utilization_fields = [
            'utilization_rate', 'utilization', 'usage_rate', 
            'efficiency', 'active_hours_percentage'
        ]
        
        for field in utilization_fields:
            value = asset.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        # Calculate from hours if available
        hours_today = asset.get('hours_today', asset.get('engine_hours', 0))
        if hours_today:
            try:
                hours = float(hours_today)
                # Assume 8-hour workday for utilization calculation
                return min(100, (hours / 8.0) * 100)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _check_gps_capability(self, asset: Dict[str, Any]) -> bool:
        """Check if asset has GPS tracking capability"""
        gps_lat = asset.get('gps_latitude', asset.get('gps_lat'))
        gps_lng = asset.get('gps_longitude', asset.get('gps_lng'))
        
        # Check for valid GPS coordinates
        if gps_lat is not None and gps_lng is not None:
            try:
                lat, lng = float(gps_lat), float(gps_lng)
                # Basic validation for reasonable coordinates
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    # Check if not default/null coordinates
                    if not (lat == 0 and lng == 0):
                        return True
            except (ValueError, TypeError):
                pass
        
        # Check asset type for GPS capability
        asset_type = asset.get('asset_type', asset.get('AssetCategory', '')).lower()
        if 'without gps' in asset_type or 'no gps' in asset_type:
            return False
        
        return True
    
    def _extract_last_activity(self, asset: Dict[str, Any]) -> Optional[datetime]:
        """Extract last activity date from various possible fields"""
        date_fields = [
            'last_update', 'last_activity', 'LastActivity', 
            'last_seen', 'timestamp', 'updated_at'
        ]
        
        for field in date_fields:
            date_str = asset.get(field)
            if date_str:
                try:
                    # Try different date formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            return datetime.strptime(str(date_str), fmt)
                        except ValueError:
                            continue
                except:
                    continue
        
        return None
    
    def _generate_recommendation(self, analysis: Dict[str, Any]) -> str:
        """Generate actionable recommendation based on analysis"""
        status = analysis['status_classification']
        confidence = analysis['confidence_score']
        
        if status == 'inactive' and confidence > 0.7:
            return 'investigate_for_redeployment'
        elif status == 'inactive' and confidence > 0.5:
            return 'verify_status'
        elif status == 'active' and confidence > 0.8:
            return 'monitor_performance'
        elif status == 'uncertain':
            return 'requires_investigation'
        elif status == 'excluded':
            return 'exclude_from_active_tracking'
        else:
            return 'insufficient_data'
    
    def _store_analysis_result(self, analysis: Dict[str, Any]):
        """Store analysis result in database with optimized connection handling"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO asset_status_analysis 
                (asset_id, asset_name, status_classification, confidence_score, 
                 utilization_rate, gps_enabled, days_inactive, classification_reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis['asset_id'],
                analysis['asset_name'],
                analysis['status_classification'],
                analysis['confidence_score'],
                analysis['activity_indicators'].get('utilization_rate'),
                analysis['activity_indicators'].get('gps_enabled'),
                analysis['activity_indicators'].get('days_inactive'),
                json.dumps(analysis['classification_reasons'])
            ))
            
            conn.commit()
            
        except sqlite3.OperationalError as e:
            logging.warning(f"Database operation skipped due to timeout: {e}")
        except Exception as e:
            logging.error(f"Database storage error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
    
    def analyze_all_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze all assets and provide comprehensive status summary
        
        Args:
            assets: List of asset dictionaries
            
        Returns:
            Summary analysis with counts and recommendations
        """
        if not assets:
            return {
                'total_assets': 0,
                'active_count': 0,
                'inactive_count': 0,
                'uncertain_count': 0,
                'excluded_count': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        status_counts = {
            'active': 0,
            'inactive': 0,
            'uncertain': 0,
            'excluded': 0
        }
        
        detailed_results = []
        high_confidence_inactive = []
        recommendations_summary = {}
        
        for asset in assets:
            analysis = self.analyze_asset_status(asset)
            detailed_results.append(analysis)
            
            status = analysis['status_classification']
            if status in status_counts:
                status_counts[status] += 1
            
            # Track high-confidence inactive assets for investigation
            if status == 'inactive' and analysis['confidence_score'] > 0.7:
                high_confidence_inactive.append({
                    'asset_id': analysis['asset_id'],
                    'asset_name': analysis['asset_name'],
                    'confidence_score': analysis['confidence_score'],
                    'reasons': analysis['classification_reasons']
                })
            
            # Count recommendations
            rec = analysis['recommendation']
            recommendations_summary[rec] = recommendations_summary.get(rec, 0) + 1
        
        # Calculate utilization statistics
        active_assets = [r for r in detailed_results if r['status_classification'] == 'active']
        avg_utilization = 0
        if active_assets:
            utilizations = [
                r['activity_indicators'].get('utilization_rate', 0) 
                for r in active_assets 
                if r['activity_indicators'].get('utilization_rate') is not None
            ]
            if utilizations:
                avg_utilization = sum(utilizations) / len(utilizations)
        
        return {
            'total_assets': len(assets),
            'active_count': status_counts['active'],
            'inactive_count': status_counts['inactive'],
            'uncertain_count': status_counts['uncertain'],
            'excluded_count': status_counts['excluded'],
            'active_percentage': (status_counts['active'] / len(assets)) * 100,
            'average_utilization': round(avg_utilization, 2),
            'high_confidence_inactive': high_confidence_inactive,
            'recommendations_summary': recommendations_summary,
            'detailed_analysis': detailed_results,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status_classification, COUNT(*) as count,
                   AVG(confidence_score) as avg_confidence,
                   AVG(utilization_rate) as avg_utilization
            FROM asset_status_analysis
            WHERE last_analysis > datetime('now', '-24 hours')
            GROUP BY status_classification
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        summary = {
            'status_breakdown': {},
            'last_updated': datetime.now().isoformat()
        }
        
        total_assets = sum(row[1] for row in results)
        
        for status, count, avg_conf, avg_util in results:
            summary['status_breakdown'][status] = {
                'count': count,
                'percentage': (count / total_assets * 100) if total_assets > 0 else 0,
                'average_confidence': round(avg_conf or 0, 3),
                'average_utilization': round(avg_util or 0, 2)
            }
        
        summary['total_analyzed'] = total_assets
        
        return summary

# Global analyzer instance
_asset_status_analyzer = None

def get_asset_status_analyzer() -> QQUnifiedAssetStatusAnalyzer:
    """Get global asset status analyzer instance"""
    global _asset_status_analyzer
    if _asset_status_analyzer is None:
        _asset_status_analyzer = QQUnifiedAssetStatusAnalyzer()
    return _asset_status_analyzer

def analyze_fort_worth_asset_status(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze Fort Worth asset status using unified analyzer"""
    analyzer = get_asset_status_analyzer()
    return analyzer.analyze_all_assets(assets)

def get_active_assets_only(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to return only definitively active assets"""
    analyzer = get_asset_status_analyzer()
    active_assets = []
    
    for asset in assets:
        analysis = analyzer.analyze_asset_status(asset)
        if analysis['status_classification'] == 'active' and analysis['confidence_score'] > 0.5:
            # Add analysis metadata to asset
            asset['_status_analysis'] = analysis
            active_assets.append(asset)
    
    return active_assets