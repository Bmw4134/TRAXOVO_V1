"""
Recursive Learning Database System
Creates a self-evolving database that learns from fleet operations patterns
"""

import os
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class LearningPattern:
    """Represents a learned pattern in fleet operations"""
    pattern_id: str
    pattern_type: str  # 'usage', 'maintenance', 'efficiency', 'location'
    confidence_score: float
    frequency: int
    last_observed: datetime
    prediction_accuracy: float
    related_assets: List[str]
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]

class RecursiveLearningDatabase:
    """Self-evolving database that learns from fleet operations"""
    
    def __init__(self):
        self.learning_patterns = {}
        self.prediction_history = {}
        self.adaptation_rules = {}
        self.performance_metrics = defaultdict(list)
        self.database_schema_evolution = []
        
    def analyze_asset_usage_patterns(self, asset_data: List[Dict]) -> List[LearningPattern]:
        """Analyze and learn from asset usage patterns"""
        patterns = []
        
        # Group assets by type and analyze usage patterns
        asset_groups = defaultdict(list)
        for asset in asset_data:
            category = asset.get('category', 'Unknown')
            asset_groups[category].append(asset)
        
        for category, assets in asset_groups.items():
            # Learn utilization patterns
            utilization_pattern = self._learn_utilization_pattern(category, assets)
            if utilization_pattern:
                patterns.append(utilization_pattern)
            
            # Learn location patterns
            location_pattern = self._learn_location_pattern(category, assets)
            if location_pattern:
                patterns.append(location_pattern)
            
            # Learn maintenance patterns
            maintenance_pattern = self._learn_maintenance_pattern(category, assets)
            if maintenance_pattern:
                patterns.append(maintenance_pattern)
        
        return patterns
    
    def _learn_utilization_pattern(self, category: str, assets: List[Dict]) -> Optional[LearningPattern]:
        """Learn asset utilization patterns"""
        try:
            # Calculate utilization metrics
            active_count = sum(1 for asset in assets if asset.get('status', '').lower() in ['active', 'moving'])
            total_count = len(assets)
            utilization_rate = active_count / total_count if total_count > 0 else 0
            
            # Calculate average monthly rates
            monthly_rates = [asset.get('monthly_rate', 0) for asset in assets if asset.get('monthly_rate', 0) > 0]
            avg_monthly_rate = np.mean(monthly_rates) if monthly_rates else 0
            
            pattern_id = f"utilization_{category}_{datetime.now().strftime('%Y%m%d')}"
            
            return LearningPattern(
                pattern_id=pattern_id,
                pattern_type='utilization',
                confidence_score=0.8 if len(assets) > 5 else 0.5,
                frequency=1,
                last_observed=datetime.now(),
                prediction_accuracy=0.0,  # Will be updated based on future predictions
                related_assets=[asset.get('asset_id', '') for asset in assets],
                conditions={
                    'category': category,
                    'asset_count': total_count,
                    'time_period': 'current'
                },
                outcomes={
                    'utilization_rate': utilization_rate,
                    'active_assets': active_count,
                    'avg_monthly_rate': avg_monthly_rate,
                    'revenue_potential': avg_monthly_rate * active_count
                }
            )
        except Exception as e:
            logger.error(f"Error learning utilization pattern: {e}")
            return None
    
    def _learn_location_pattern(self, category: str, assets: List[Dict]) -> Optional[LearningPattern]:
        """Learn asset location patterns"""
        try:
            # Analyze geographic distribution
            locations = []
            for asset in assets:
                lat = asset.get('latitude', 0)
                lng = asset.get('longitude', 0)
                if lat != 0 and lng != 0:
                    locations.append((lat, lng))
            
            if not locations:
                return None
            
            # Calculate location clusters
            center_lat = np.mean([loc[0] for loc in locations])
            center_lng = np.mean([loc[1] for loc in locations])
            
            # Calculate spread
            lat_spread = np.std([loc[0] for loc in locations])
            lng_spread = np.std([loc[1] for loc in locations])
            
            pattern_id = f"location_{category}_{datetime.now().strftime('%Y%m%d')}"
            
            return LearningPattern(
                pattern_id=pattern_id,
                pattern_type='location',
                confidence_score=0.7,
                frequency=1,
                last_observed=datetime.now(),
                prediction_accuracy=0.0,
                related_assets=[asset.get('asset_id', '') for asset in assets if asset.get('latitude', 0) != 0],
                conditions={
                    'category': category,
                    'location_count': len(locations)
                },
                outcomes={
                    'center_latitude': center_lat,
                    'center_longitude': center_lng,
                    'geographic_spread_lat': lat_spread,
                    'geographic_spread_lng': lng_spread,
                    'clustered': lat_spread < 0.1 and lng_spread < 0.1
                }
            )
        except Exception as e:
            logger.error(f"Error learning location pattern: {e}")
            return None
    
    def _learn_maintenance_pattern(self, category: str, assets: List[Dict]) -> Optional[LearningPattern]:
        """Learn maintenance and depreciation patterns"""
        try:
            # Analyze asset ages and depreciation
            purchase_prices = [asset.get('purchase_price', 0) for asset in assets if asset.get('purchase_price', 0) > 0]
            
            if not purchase_prices:
                return None
            
            avg_purchase_price = np.mean(purchase_prices)
            total_fleet_value = sum(purchase_prices)
            
            # Estimate depreciation (simplified)
            estimated_current_values = []
            for asset in assets:
                purchase_price = asset.get('purchase_price', 0)
                if purchase_price > 0:
                    # Assume 7-year depreciation for construction equipment
                    estimated_age = 3  # Average assumption
                    annual_depreciation = purchase_price / 7
                    current_value = max(0, purchase_price - (annual_depreciation * estimated_age))
                    estimated_current_values.append(current_value)
            
            avg_current_value = np.mean(estimated_current_values) if estimated_current_values else 0
            
            pattern_id = f"maintenance_{category}_{datetime.now().strftime('%Y%m%d')}"
            
            return LearningPattern(
                pattern_id=pattern_id,
                pattern_type='maintenance',
                confidence_score=0.6,
                frequency=1,
                last_observed=datetime.now(),
                prediction_accuracy=0.0,
                related_assets=[asset.get('asset_id', '') for asset in assets if asset.get('purchase_price', 0) > 0],
                conditions={
                    'category': category,
                    'asset_count': len(purchase_prices)
                },
                outcomes={
                    'avg_purchase_price': avg_purchase_price,
                    'avg_current_value': avg_current_value,
                    'total_fleet_value': total_fleet_value,
                    'depreciation_rate': (avg_purchase_price - avg_current_value) / avg_purchase_price if avg_purchase_price > 0 else 0
                }
            )
        except Exception as e:
            logger.error(f"Error learning maintenance pattern: {e}")
            return None
    
    def update_learning_patterns(self, new_patterns: List[LearningPattern]):
        """Update and evolve existing learning patterns"""
        for pattern in new_patterns:
            if pattern.pattern_id in self.learning_patterns:
                # Update existing pattern
                existing = self.learning_patterns[pattern.pattern_id]
                existing.frequency += 1
                existing.last_observed = pattern.last_observed
                
                # Evolve confidence based on consistency
                if self._patterns_are_consistent(existing, pattern):
                    existing.confidence_score = min(1.0, existing.confidence_score + 0.1)
                else:
                    existing.confidence_score = max(0.1, existing.confidence_score - 0.05)
                
                # Update outcomes with weighted average
                for key, value in pattern.outcomes.items():
                    if key in existing.outcomes and isinstance(value, (int, float)):
                        weight = 0.3  # Weight for new data
                        existing.outcomes[key] = (existing.outcomes[key] * (1 - weight) + value * weight)
            else:
                # Add new pattern
                self.learning_patterns[pattern.pattern_id] = pattern
    
    def _patterns_are_consistent(self, existing: LearningPattern, new: LearningPattern) -> bool:
        """Check if patterns are consistent for confidence evolution"""
        try:
            # Compare key outcomes
            for key in ['utilization_rate', 'avg_monthly_rate', 'depreciation_rate']:
                if key in existing.outcomes and key in new.outcomes:
                    existing_val = existing.outcomes[key]
                    new_val = new.outcomes[key]
                    if existing_val > 0 and abs(existing_val - new_val) / existing_val > 0.3:  # 30% threshold
                        return False
            return True
        except:
            return False
    
    def generate_predictions(self) -> Dict[str, Any]:
        """Generate predictions based on learned patterns"""
        predictions = {
            'utilization_forecast': {},
            'maintenance_forecast': {},
            'location_forecast': {},
            'revenue_forecast': {},
            'generated_at': datetime.now().isoformat()
        }
        
        for pattern in self.learning_patterns.values():
            if pattern.confidence_score > 0.5:  # Only use confident patterns
                if pattern.pattern_type == 'utilization':
                    self._generate_utilization_prediction(pattern, predictions)
                elif pattern.pattern_type == 'maintenance':
                    self._generate_maintenance_prediction(pattern, predictions)
                elif pattern.pattern_type == 'location':
                    self._generate_location_prediction(pattern, predictions)
        
        return predictions
    
    def _generate_utilization_prediction(self, pattern: LearningPattern, predictions: Dict):
        """Generate utilization predictions"""
        category = pattern.conditions.get('category', 'Unknown')
        current_rate = pattern.outcomes.get('utilization_rate', 0)
        
        # Predict utilization trend
        trend = 'stable'
        if pattern.frequency > 5:  # Enough data points
            if current_rate > 0.8:
                trend = 'high_utilization'
            elif current_rate < 0.5:
                trend = 'low_utilization'
        
        predictions['utilization_forecast'][category] = {
            'current_rate': current_rate,
            'predicted_trend': trend,
            'confidence': pattern.confidence_score,
            'recommendation': self._get_utilization_recommendation(current_rate, trend)
        }
    
    def _generate_maintenance_prediction(self, pattern: LearningPattern, predictions: Dict):
        """Generate maintenance predictions"""
        category = pattern.conditions.get('category', 'Unknown')
        depreciation_rate = pattern.outcomes.get('depreciation_rate', 0)
        
        predictions['maintenance_forecast'][category] = {
            'depreciation_rate': depreciation_rate,
            'avg_current_value': pattern.outcomes.get('avg_current_value', 0),
            'maintenance_urgency': 'high' if depreciation_rate > 0.6 else 'medium' if depreciation_rate > 0.3 else 'low',
            'confidence': pattern.confidence_score
        }
    
    def _generate_location_prediction(self, pattern: LearningPattern, predictions: Dict):
        """Generate location predictions"""
        category = pattern.conditions.get('category', 'Unknown')
        
        predictions['location_forecast'][category] = {
            'geographic_center': {
                'lat': pattern.outcomes.get('center_latitude', 0),
                'lng': pattern.outcomes.get('center_longitude', 0)
            },
            'is_clustered': pattern.outcomes.get('clustered', False),
            'confidence': pattern.confidence_score
        }
    
    def _get_utilization_recommendation(self, rate: float, trend: str) -> str:
        """Get utilization recommendations"""
        if trend == 'high_utilization':
            return 'Consider acquiring additional assets or optimizing deployment'
        elif trend == 'low_utilization':
            return 'Review asset allocation or consider disposal of underutilized assets'
        else:
            return 'Monitor utilization trends and maintain current strategy'
    
    def evolve_database_schema(self, new_data_patterns: Dict[str, Any]):
        """Evolve database schema based on learning patterns"""
        evolution = {
            'timestamp': datetime.now().isoformat(),
            'changes': [],
            'new_fields': [],
            'optimizations': []
        }
        
        # Analyze if new fields are needed
        for pattern_type, data in new_data_patterns.items():
            if pattern_type not in ['utilization', 'maintenance', 'location']:
                evolution['new_fields'].append({
                    'field_name': f'{pattern_type}_pattern',
                    'data_type': 'jsonb',
                    'reason': f'New pattern type discovered: {pattern_type}'
                })
        
        # Suggest index optimizations
        high_confidence_patterns = [p for p in self.learning_patterns.values() if p.confidence_score > 0.8]
        if len(high_confidence_patterns) > 10:
            evolution['optimizations'].append({
                'type': 'index',
                'suggestion': 'CREATE INDEX ON assets(category, status) WHERE confidence_score > 0.8',
                'reason': 'High confidence patterns show frequent category+status queries'
            })
        
        self.database_schema_evolution.append(evolution)
        return evolution
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        total_patterns = len(self.learning_patterns)
        high_confidence = len([p for p in self.learning_patterns.values() if p.confidence_score > 0.7])
        
        pattern_types = defaultdict(int)
        for pattern in self.learning_patterns.values():
            pattern_types[pattern.pattern_type] += 1
        
        return {
            'total_patterns_learned': total_patterns,
            'high_confidence_patterns': high_confidence,
            'confidence_rate': high_confidence / total_patterns if total_patterns > 0 else 0,
            'pattern_distribution': dict(pattern_types),
            'last_learning_session': max([p.last_observed for p in self.learning_patterns.values()]).isoformat() if self.learning_patterns else None,
            'schema_evolutions': len(self.database_schema_evolution),
            'learning_maturity': 'mature' if total_patterns > 50 else 'developing' if total_patterns > 10 else 'initial'
        }

# Global learning database
recursive_db = RecursiveLearningDatabase()

def get_recursive_database():
    """Get the recursive learning database"""
    return recursive_db