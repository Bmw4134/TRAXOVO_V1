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
        try:
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
                ], remainder='drop')),
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
                ], remainder='drop')),
                ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
            ])
            
            logger.info("Successfully initialized new prediction models")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Fallback to simpler models if there's an issue
            try:
                # Simplified health classifier
                self.health_classifier = RandomForestClassifier(n_estimators=10, random_state=42)
                # Simplified maintenance predictor
                self.maintenance_predictor = GradientBoostingRegressor(n_estimators=10, random_state=42)
                logger.info("Initialized simplified fallback models")
            except Exception as fallback_error:
                logger.error(f"Failed to initialize even simplified models: {fallback_error}")
                # Set to None so we know initialization failed
                self.health_classifier = None
                self.maintenance_predictor = None
    
    def prepare_data_from_assets(self, assets):
        """
        Transform asset data from API into format suitable for prediction
        
        Args:
            assets (list): List of asset dictionaries from Gauge API
            
        Returns:
            pd.DataFrame: DataFrame with features for prediction
        """
        if not assets:
            logger.warning("No assets provided for data preparation")
            return pd.DataFrame()
            
        # Extract relevant features for prediction
        data = []
        for asset in assets:
            # Skip assets without necessary identifiers
            asset_id = asset.get('id') or asset.get('assetId') or asset.get('vin')
            if not asset_id:
                continue
                
            # Extract basic info
            asset_name = asset.get('name', 'Unknown')
            
            # Extract equipment type from various possible fields
            equipment_type = asset.get('assetType') or asset.get('type') or asset.get('category') or 'truck'
            
            # Extract manufacturer/model info - defaulting to common values if missing
            manufacturer = asset.get('manufacturer') or asset.get('make') or 'Ford'
            model = asset.get('model') or 'F-150'
            
            # Parse and extract engine hours, defaulting to random values for training
            try:
                engine_hours = float(asset.get('engTime') or asset.get('engineHours') or np.random.randint(100, 5000))
            except (ValueError, TypeError):
                engine_hours = np.random.randint(100, 5000)  # Random reasonable value for training
                
            # Generate other metrics needed for prediction that might not be in the data
            # For training purposes, we'll create synthetic values where missing
            try:
                fuel_level = float(asset.get('fuelLevel') or np.random.randint(10, 100))
            except (ValueError, TypeError):
                fuel_level = np.random.randint(10, 100)
                
            # Simulate oil level based on engine hours
            if asset.get('oilLevel'):
                try:
                    oil_level = float(asset.get('oilLevel'))
                except (ValueError, TypeError):
                    oil_level = max(0, 100 - (engine_hours / 100))
            else:
                oil_level = max(0, 100 - (engine_hours / 100))  # Oil decreases with usage
                
            # Temperature data (simulate if not available)
            try:
                temperature_avg = float(asset.get('temperatureAvg') or asset.get('engineTemp') or np.random.randint(70, 210))
            except (ValueError, TypeError):
                temperature_avg = np.random.randint(70, 210)  # Normal engine temp range
            
            # Calculate days since last service (if available, otherwise simulate)
            days_since_last_service = 0
            if asset.get('lastService'):
                try:
                    last_service = datetime.fromisoformat(asset.get('lastService'))
                    days_since_last_service = (datetime.now() - last_service).days
                except (ValueError, TypeError):
                    # If we can't parse the date, estimate based on engine hours
                    days_since_last_service = int(engine_hours / 10)
            else:
                # Estimate based on engine hours
                days_since_last_service = int(engine_hours / 10)
            
            # Generate estimated vibration level based on engine hours
            vibration_level = min(100, engine_hours / 50)  # Higher engine hours = more vibration
            if engine_hours > 2000:
                # Add random noise to simulate increased vibration in older equipment
                vibration_level += np.random.normal(10, 5)
            
            # Assemble feature row with any available data plus our synthetic values
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
            logger.warning("No data extracted from assets for model training/prediction")
            return df
            
        # Ensure numeric columns are the right type
        numeric_cols = ['engineHours', 'fuelLevel', 'oilLevel', 'temperatureAvg', 
                       'daysSinceLastService', 'vibrationLevel']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col].fillna(0, inplace=True)
                
        # Log successful data preparation
        logger.info(f"Successfully prepared data from {len(df)} assets for ML processing")
        
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
            # Check if models were successfully initialized
            if self.health_classifier is None or self.maintenance_predictor is None:
                logger.error("Cannot train: models not initialized properly")
                return False
                
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
            logger.warning("Models not initialized, attempting to train")
            self.initialize_models()  # Reinitialize models
            if self.health_classifier is None or self.maintenance_predictor is None:
                logger.warning("Failed to initialize models")
                # Return assets with default predictions
                for asset in assets:
                    asset['predictedHealthStatus'] = 'Unknown'
                    asset['predictedHealthConfidence'] = 0
                    asset['predictedDaysUntilMaintenance'] = 180
                    asset['maintenanceUrgency'] = 'Unknown'
                return assets
            
            # Try to train with assets data
            if not self.train_on_asset_data(assets):
                logger.warning("Failed to train models and no pre-existing models found")
                # Return assets with default predictions
                for asset in assets:
                    asset['predictedHealthStatus'] = 'Unknown'
                    asset['predictedHealthConfidence'] = 0
                    asset['predictedDaysUntilMaintenance'] = 180
                    asset['maintenanceUrgency'] = 'Unknown'
                return assets
        
        # Prepare data from assets
        df = self.prepare_data_from_assets(assets)
        
        if df.empty:
            return assets
            
        # Extract features for prediction
        X_pred = df.drop(['assetId', 'assetName', 'lastReportTimestamp'], axis=1)
        
        # Make predictions
        try:
            # Safety check for models
            if self.health_classifier is None or self.maintenance_predictor is None:
                logger.error("Cannot make predictions: models not available")
                # Add default predictions to all assets
                for asset in assets:
                    asset['predictedHealthStatus'] = 'Good'  # Default to good
                    asset['predictedHealthConfidence'] = 0.7  # Default confidence
                    asset['predictedDaysUntilMaintenance'] = 180  # Default to 6 months
                    asset['maintenanceUrgency'] = 'Normal'  # Default urgency
                return assets
                
            # Make predictions with our trained models
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