"""
Equipment Health Prediction Module

This module uses machine learning to predict equipment health
and potential maintenance issues based on historical data.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import pickle
from pathlib import Path

# ML libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define directories
MODEL_DIR = Path('models')
MODEL_DIR.mkdir(exist_ok=True)

# Model file paths
HEALTH_CLASSIFIER_PATH = MODEL_DIR / 'health_classifier.pkl'
MAINTENANCE_PREDICTOR_PATH = MODEL_DIR / 'maintenance_predictor.pkl'

class EquipmentHealthPredictor:
    """
    Predicts equipment health and maintenance needs based on historical data
    """
    def __init__(self):
        # Initialize models
        self.health_classifier = None
        self.maintenance_predictor = None
        self.last_training_date = None
        
        # Load models if they exist
        self.load_models()
        
    def load_models(self):
        """Load pre-trained models if they exist"""
        try:
            if HEALTH_CLASSIFIER_PATH.exists():
                with open(HEALTH_CLASSIFIER_PATH, 'rb') as f:
                    self.health_classifier = pickle.load(f)
                logger.info(f"Loaded health classifier from {HEALTH_CLASSIFIER_PATH}")
            
            if MAINTENANCE_PREDICTOR_PATH.exists():
                with open(MAINTENANCE_PREDICTOR_PATH, 'rb') as f:
                    self.maintenance_predictor = pickle.load(f)
                logger.info(f"Loaded maintenance predictor from {MAINTENANCE_PREDICTOR_PATH}")
                
            # Check when models were last trained
            if HEALTH_CLASSIFIER_PATH.exists():
                self.last_training_date = datetime.fromtimestamp(HEALTH_CLASSIFIER_PATH.stat().st_mtime)
                logger.info(f"Models were last trained on {self.last_training_date}")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            # Initialize new models if loading fails
            self.initialize_models()
    
    def initialize_models(self):
        """Initialize new model instances"""
        # Health status classifier
        self.health_classifier = Pipeline([
            ('preprocessor', ColumnTransformer([
                ('num', Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler())
                ]), ['engineHours', 'fuelLevel', 'oilLevel', 'daysSinceLastService', 'temperatureAvg']),
                ('cat', Pipeline([
                    ('imputer', SimpleImputer(strategy='most_frequent')),
                    ('encoder', OneHotEncoder(handle_unknown='ignore'))
                ]), ['equipmentType', 'manufacturer'])
            ])),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        # Maintenance time predictor
        self.maintenance_predictor = Pipeline([
            ('preprocessor', ColumnTransformer([
                ('num', Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler())
                ]), ['engineHours', 'fuelLevel', 'oilLevel', 'daysSinceLastService', 'temperatureAvg', 'vibrationLevel']),
                ('cat', Pipeline([
                    ('imputer', SimpleImputer(strategy='most_frequent')),
                    ('encoder', OneHotEncoder(handle_unknown='ignore'))
                ]), ['equipmentType', 'manufacturer', 'model'])
            ])),
            ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
        ])
        
        logger.info("Initialized new prediction models")
    
    def prepare_data_from_assets(self, assets):
        """
        Transform asset data from API into format suitable for prediction
        
        Args:
            assets (list): List of asset dictionaries from Gauge API
            
        Returns:
            pd.DataFrame: DataFrame with features for prediction
        """
        if not assets:
            return pd.DataFrame()
            
        # Extract relevant features for prediction
        data = []
        for asset in assets:
            # Skip assets without necessary data
            if not asset.get('id'):
                continue
                
            # Extract basic info
            asset_id = asset.get('id') or asset.get('assetId')
            asset_name = asset.get('name', 'Unknown')
            
            # Extract equipment type from various possible fields
            equipment_type = asset.get('equipmentType') or asset.get('assetType') or asset.get('type') or asset.get('category', 'Unknown')
            
            # Extract manufacturer/model info
            manufacturer = asset.get('manufacturer') or asset.get('make', 'Unknown')
            model = asset.get('model', 'Unknown')
            
            # Extract operational data
            engine_hours = float(asset.get('engTime') or asset.get('engineHours') or 0)
            fuel_level = float(asset.get('fuelLevel') or 0)
            oil_level = float(asset.get('oilLevel') or 100)  # Assume 100% if not provided
            
            # Temperature data (may not be available for all assets)
            temperature_avg = float(asset.get('temperatureAvg') or asset.get('engineTemp') or 0)
            
            # Calculate days since last service (if available)
            days_since_last_service = 0
            if asset.get('lastService'):
                try:
                    last_service = datetime.fromisoformat(asset.get('lastService'))
                    days_since_last_service = (datetime.now() - last_service).days
                except (ValueError, TypeError):
                    days_since_last_service = 0
            
            # Generate estimated vibration level based on engine hours
            # (In a real implementation, this would come from sensors)
            vibration_level = min(100, engine_hours / 10)
            if engine_hours > 2000:
                # Add random noise to simulate increased vibration in older equipment
                vibration_level += np.random.normal(20, 10)
            
            # Assemble feature row
            feature_row = {
                'assetId': asset_id,
                'assetName': asset_name,
                'equipmentType': equipment_type,
                'manufacturer': manufacturer,
                'model': model,
                'engineHours': engine_hours,
                'fuelLevel': fuel_level,
                'oilLevel': oil_level,
                'temperatureAvg': temperature_avg,
                'daysSinceLastService': days_since_last_service,
                'vibrationLevel': vibration_level,
                'lastReportTimestamp': asset.get('lastReport')
            }
            
            data.append(feature_row)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # If we have no data, return empty DataFrame
        if df.empty:
            return df
            
        # Ensure numeric columns are the right type
        numeric_cols = ['engineHours', 'fuelLevel', 'oilLevel', 'temperatureAvg', 
                       'daysSinceLastService', 'vibrationLevel']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col].fillna(0, inplace=True)
        
        return df
    
    def train_on_asset_data(self, assets):
        """
        Train models using current asset data
        
        Note: In a real implementation, this would use historical data
        with known outcomes. Here we'll simulate outcomes based on
        engineering rules for demonstration purposes.
        
        Args:
            assets (list): List of asset dictionaries from Gauge API
            
        Returns:
            bool: True if training was successful, False otherwise
        """
        if not assets:
            logger.warning("No assets provided for training")
            return False
            
        # Prepare data from assets
        df = self.prepare_data_from_assets(assets)
        
        if df.empty:
            logger.warning("No valid data extracted for training")
            return False
            
        # Simulate health labels based on engineering rules
        df['healthStatus'] = 'Good'  # Default to good
        
        # Apply rules to determine health status
        # High engine hours + no recent service = Poor health
        mask = (df['engineHours'] > 1000) & (df['daysSinceLastService'] > 90)
        df.loc[mask, 'healthStatus'] = 'Poor'
        
        # Low oil level = Poor health
        mask = df['oilLevel'] < 20
        df.loc[mask, 'healthStatus'] = 'Poor'
        
        # Moderate wear indicators = Fair health
        mask = ((df['engineHours'] > 500) & (df['daysSinceLastService'] > 45)) | (df['oilLevel'] < 50)
        df.loc[mask & (df['healthStatus'] != 'Poor'), 'healthStatus'] = 'Fair'
        
        # Simulate days until maintenance needed based on rules
        df['daysUntilMaintenance'] = 180  # Default to 180 days
        
        # Adjust based on engine hours (higher hours = sooner maintenance)
        df['daysUntilMaintenance'] = df['daysUntilMaintenance'] - (df['engineHours'] / 20)
        
        # Adjust based on days since last service
        df['daysUntilMaintenance'] = df['daysUntilMaintenance'] - df['daysSinceLastService']
        
        # Adjust based on oil level (lower oil = sooner maintenance)
        df['daysUntilMaintenance'] = df['daysUntilMaintenance'] - ((100 - df['oilLevel']) / 2)
        
        # Ensure minimum 0 days
        df['daysUntilMaintenance'] = df['daysUntilMaintenance'].clip(lower=0)
        
        # Split data for health classification
        X_health = df.drop(['assetId', 'assetName', 'healthStatus', 'daysUntilMaintenance', 'lastReportTimestamp'], axis=1)
        y_health = df['healthStatus']
        
        # Split data for maintenance prediction
        X_maint = df.drop(['assetId', 'assetName', 'healthStatus', 'daysUntilMaintenance', 'lastReportTimestamp'], axis=1)
        y_maint = df['daysUntilMaintenance']
        
        try:
            # Train health classifier
            self.health_classifier.fit(X_health, y_health)
            
            # Train maintenance predictor
            self.maintenance_predictor.fit(X_maint, y_maint)
            
            # Save models
            with open(HEALTH_CLASSIFIER_PATH, 'wb') as f:
                pickle.dump(self.health_classifier, f)
            
            with open(MAINTENANCE_PREDICTOR_PATH, 'wb') as f:
                pickle.dump(self.maintenance_predictor, f)
                
            self.last_training_date = datetime.now()
            
            logger.info("Successfully trained and saved prediction models")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def predict_health(self, assets):
        """
        Predict health status and maintenance needs for assets
        
        Args:
            assets (list): List of asset dictionaries from Gauge API
            
        Returns:
            list: List of asset dictionaries with predictions added
        """
        if not assets:
            return []
            
        # Check if models exist, create them if needed
        if self.health_classifier is None or self.maintenance_predictor is None:
            if not self.train_on_asset_data(assets):
                logger.warning("Failed to train models and no pre-existing models found")
                # Return original assets without predictions
                return assets
        
        # Prepare data from assets
        df = self.prepare_data_from_assets(assets)
        
        if df.empty:
            return assets
            
        # Extract features for prediction
        X_pred = df.drop(['assetId', 'assetName', 'lastReportTimestamp'], axis=1)
        
        # Make predictions
        try:
            health_predictions = self.health_classifier.predict(X_pred)
            maintenance_days_predictions = self.maintenance_predictor.predict(X_pred)
            
            # Get probabilities for health status (for confidence scores)
            health_proba = self.health_classifier.predict_proba(X_pred)
            
            # Add predictions back to data
            df['predictedHealthStatus'] = health_predictions
            df['predictedDaysUntilMaintenance'] = maintenance_days_predictions
            
            # Calculate confidence scores (max probability across classes)
            health_confidence = np.max(health_proba, axis=1)
            df['healthPredictionConfidence'] = health_confidence
            
            # Enhance with maintenance date
            df['predictedMaintenanceDate'] = df['predictedDaysUntilMaintenance'].apply(
                lambda days: (datetime.now() + timedelta(days=max(0, days))).strftime('%Y-%m-%d')
            )
            
            # Add predictions to original assets
            for asset in assets:
                asset_id = asset.get('id') or asset.get('assetId')
                if asset_id:
                    asset_row = df[df['assetId'] == asset_id]
                    if not asset_row.empty:
                        asset['predictedHealthStatus'] = asset_row['predictedHealthStatus'].iloc[0]
                        asset['predictedDaysUntilMaintenance'] = round(asset_row['predictedDaysUntilMaintenance'].iloc[0])
                        asset['healthPredictionConfidence'] = round(asset_row['healthPredictionConfidence'].iloc[0] * 100)
                        asset['predictedMaintenanceDate'] = asset_row['predictedMaintenanceDate'].iloc[0]
            
            logger.info(f"Generated health predictions for {len(assets)} assets")
            return assets
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return assets

# Singleton instance
predictor = EquipmentHealthPredictor()

def predict_asset_health(assets):
    """
    Predict health for a list of assets
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        list: Same assets with predictions added
    """
    return predictor.predict_health(assets)

def train_prediction_models(assets):
    """
    Train prediction models using asset data
    
    Args:
        assets (list): List of asset dictionaries
        
    Returns:
        bool: True if training succeeded, False otherwise
    """
    return predictor.train_on_asset_data(assets)

def get_model_info():
    """
    Get information about the current models
    
    Returns:
        dict: Model information including last training date
    """
    return {
        'health_model_exists': predictor.health_classifier is not None,
        'maintenance_model_exists': predictor.maintenance_predictor is not None,
        'last_training_date': predictor.last_training_date
    }