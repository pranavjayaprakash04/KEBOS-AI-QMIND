"""
CatBoost-based Two-Step Anomaly Detection and Attack Classification for CICIDS 2017
================================================================================

This module implements a robust two-step approach:
1. Anomaly Detection: Binary classification (Normal vs Attack)
2. Attack Classification: Multi-class classification of attack types

Features:
- Comprehensive data preprocessing with feature engineering
- Optuna hyperparameter optimization
- Cross-validation with overfitting prevention
- MLflow integration for experiment tracking
- Robust evaluation metrics and visualization
"""

import os
import json
import pickle
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
import logging

import pandas as pd
import numpy as np
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score
)
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, f1_score, accuracy_score,
    precision_score, recall_score
)
from sklearn.utils.class_weight import compute_class_weight
import catboost as cb
import optuna
import mlflow
import mlflow.catboost
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

@dataclass
class ModelConfig:
    """Configuration for the two-step CatBoost model."""
    data_dir: Path
    output_dir: Path
    test_size: float = 0.2
    val_size: float = 0.1
    random_state: int = 42
    n_trials: int = 100
    cv_folds: int = 5
    early_stopping_rounds: int = 50
    verbose: bool = True

class CICIDSDataProcessor:
    """
    Comprehensive data processor for CICIDS 2017 dataset.
    Handles loading, cleaning, feature engineering, and preprocessing.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.scaler = RobustScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns: List[str] = []
        self.attack_types: List[str] = []
        
    def load_all_datasets(self) -> pd.DataFrame:
        """Load and combine all CICIDS 2017 CSV files."""
        logger.info("Loading CICIDS 2017 datasets...")
        
        data_folders = [
            self.config.data_dir / "TrafficLabelling",
            self.config.data_dir / "MachineLearningCVE"
        ]
        
        dataframes = []
        total_samples = 0
        
        for folder in data_folders:
            if not folder.exists():
                logger.warning(f"Folder {folder} does not exist, skipping...")
                continue
                
            csv_files = list(folder.glob("*.csv"))
            logger.info(f"Found {len(csv_files)} CSV files in {folder}")
            
            for csv_file in csv_files:
                try:
                    logger.info(f"Loading {csv_file.name}...")
                    
                    # Try different encodings
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            df = pd.read_csv(csv_file, encoding=encoding, low_memory=False)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        logger.error(f"Could not decode {csv_file.name}")
                        continue
                    
                    # Standardize column names
                    df.columns = df.columns.str.strip()
                    if ' Label' in df.columns:
                        df = df.rename(columns={' Label': 'Label'})
                    elif 'label' in df.columns:
                        df = df.rename(columns={'label': 'Label'})
                    
                    if 'Label' not in df.columns:
                        logger.warning(f"No Label column found in {csv_file.name}")
                        continue
                    
                    dataframes.append(df)
                    total_samples += len(df)
                    logger.info(f"Loaded {len(df):,} samples from {csv_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error loading {csv_file.name}: {str(e)}")
        
        if not dataframes:
            raise ValueError("No valid datasets found!")
        
        # Combine all dataframes
        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Combined dataset: {len(combined_df):,} total samples")
        
        return combined_df
    
    def clean_and_preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the dataset."""
        logger.info("Cleaning and preprocessing data...")
        
        # Remove identifier columns
        id_columns = [
            'Flow ID', 'Source IP', 'Destination IP', 'Timestamp',
            'Src IP', 'Dst IP', 'Flow.ID', 'Src.IP', 'Dst.IP'
        ]
        
        existing_id_cols = [col for col in id_columns if col in df.columns]
        if existing_id_cols:
            df = df.drop(columns=existing_id_cols)
            logger.info(f"Removed identifier columns: {existing_id_cols}")
        
        # Handle missing values
        logger.info(f"Missing values before cleaning: {df.isnull().sum().sum()}")
        
        # Convert object columns to numeric where possible
        for col in df.columns:
            if col != 'Label' and df[col].dtype == 'object':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if 'Label' in numeric_cols:
            numeric_cols.remove('Label')
        
        # Fill missing values with median
        for col in numeric_cols:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
        
        # Handle infinite values
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], 0)
        
        logger.info(f"Missing values after cleaning: {df.isnull().sum().sum()}")
        logger.info(f"Final numeric columns: {len(numeric_cols)}")
        
        self.feature_columns = numeric_cols
        return df
    
    def create_attack_labels(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """Create binary and multi-class labels."""
        logger.info("Creating attack labels...")
        
        # Get label distribution
        label_counts = df['Label'].value_counts()
        logger.info(f"Original label distribution:")
        for label, count in label_counts.items():
            logger.info(f"  {label}: {count:,} ({count/len(df)*100:.2f}%)")
        
        # Create binary labels (0=BENIGN, 1=ATTACK)
        df['is_attack'] = (df['Label'] != 'BENIGN').astype(int)
        
        # Create attack type labels (only for attacks)
        attack_data = df[df['is_attack'] == 1].copy()
        attack_types = attack_data['Label'].unique().tolist()
        
        # Filter out attack types with very few samples (< 100)
        min_samples = 100
        valid_attack_types = []
        for attack_type in attack_types:
            count = (attack_data['Label'] == attack_type).sum()
            if count >= min_samples:
                valid_attack_types.append(attack_type)
            else:
                logger.info(f"Filtering out {attack_type}: only {count} samples")
        
        self.attack_types = valid_attack_types
        
        # Encode attack types
        attack_data_filtered = attack_data[attack_data['Label'].isin(valid_attack_types)]
        attack_data_filtered['attack_type'] = self.label_encoder.fit_transform(
            attack_data_filtered['Label']
        )
        
        # Add attack type labels back to main dataframe
        df['attack_type'] = -1  # Default for benign traffic
        df.loc[attack_data_filtered.index, 'attack_type'] = attack_data_filtered['attack_type']
        
        label_info = {
            'binary_distribution': df['is_attack'].value_counts().to_dict(),
            'attack_types': {
                attack_type: idx for idx, attack_type in 
                enumerate(self.label_encoder.classes_)
            },
            'attack_type_counts': attack_data_filtered['Label'].value_counts().to_dict()
        }
        
        logger.info(f"Binary classification distribution:")
        logger.info(f"  BENIGN: {label_info['binary_distribution'][0]:,}")
        logger.info(f"  ATTACK: {label_info['binary_distribution'][1]:,}")
        logger.info(f"Valid attack types for classification: {len(valid_attack_types)}")
        
        return df, label_info
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for better detection."""
        logger.info("Engineering features...")
        
        numeric_cols = self.feature_columns.copy()
        
        # Create flow statistics
        flow_features = []
        
        # Packet-based features
        packet_cols = [col for col in numeric_cols if 'packet' in col.lower() or 'pkt' in col.lower()]
        if packet_cols:
            for col in packet_cols:
                if df[col].sum() > 0:  # Only if column has non-zero values
                    # Log transform for skewed distributions
                    df[f'{col}_log'] = np.log1p(df[col])
                    flow_features.append(f'{col}_log')
        
        # Byte-based features
        byte_cols = [col for col in numeric_cols if 'byte' in col.lower() or 'length' in col.lower()]
        if byte_cols:
            for col in byte_cols:
                if df[col].sum() > 0:
                    # Log transform and normalization
                    df[f'{col}_log'] = np.log1p(df[col])
                    flow_features.append(f'{col}_log')
        
        # Time-based features
        time_cols = [col for col in numeric_cols if 'time' in col.lower() or 'duration' in col.lower()]
        if time_cols:
            for col in time_cols:
                if df[col].sum() > 0:
                    # Handle time features
                    df[f'{col}_sqrt'] = np.sqrt(df[col].clip(lower=0))
                    flow_features.append(f'{col}_sqrt')
        
        # Ratio features
        if len(byte_cols) >= 2:
            # Create ratios between different byte columns
            for i, col1 in enumerate(byte_cols[:3]):  # Limit to avoid too many features
                for col2 in byte_cols[i+1:4]:
                    ratio_name = f'{col1}_{col2}_ratio'
                    df[ratio_name] = np.where(
                        df[col2] != 0, 
                        df[col1] / (df[col2] + 1e-10), 
                        0
                    )
                    flow_features.append(ratio_name)
        
        # Statistical features for grouped columns
        stat_features = []
        flow_stat_cols = [col for col in numeric_cols if any(x in col.lower() 
                         for x in ['flow', 'fwd', 'bwd', 'forward', 'backward'])]
        
        if len(flow_stat_cols) >= 3:
            # Create statistical aggregations
            flow_data = df[flow_stat_cols].fillna(0)
            
            df['flow_mean'] = flow_data.mean(axis=1)
            df['flow_std'] = flow_data.std(axis=1)
            df['flow_max'] = flow_data.max(axis=1)
            df['flow_min'] = flow_data.min(axis=1)
            df['flow_range'] = df['flow_max'] - df['flow_min']
            
            stat_features.extend(['flow_mean', 'flow_std', 'flow_max', 'flow_min', 'flow_range'])
        
        # Update feature columns
        self.feature_columns.extend(flow_features + stat_features)
        
        logger.info(f"Created {len(flow_features + stat_features)} new features")
        logger.info(f"Total features: {len(self.feature_columns)}")
        
        return df
    
    def prepare_data_splits(self, df: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """Prepare train/val/test splits for both tasks."""
        logger.info("Preparing data splits...")
        
        # Features
        X = df[self.feature_columns].values
        
        # Binary classification data
        y_binary = df['is_attack'].values
        
        # Attack classification data (only attacks)
        attack_mask = df['is_attack'] == 1
        X_attacks = X[attack_mask]
        y_attacks = df.loc[attack_mask, 'attack_type'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_attacks_scaled = self.scaler.transform(X_attacks)
        
        # Binary classification splits
        X_train_bin, X_temp_bin, y_train_bin, y_temp_bin = train_test_split(
            X_scaled, y_binary, 
            test_size=self.config.test_size + self.config.val_size,
            stratify=y_binary,
            random_state=self.config.random_state
        )
        
        val_size_adjusted = self.config.val_size / (self.config.test_size + self.config.val_size)
        X_val_bin, X_test_bin, y_val_bin, y_test_bin = train_test_split(
            X_temp_bin, y_temp_bin,
            test_size=val_size_adjusted,
            stratify=y_temp_bin,
            random_state=self.config.random_state
        )
        
        # Attack classification splits
        X_train_att, X_temp_att, y_train_att, y_temp_att = train_test_split(
            X_attacks_scaled, y_attacks,
            test_size=self.config.test_size + self.config.val_size,
            stratify=y_attacks,
            random_state=self.config.random_state
        )
        
        X_val_att, X_test_att, y_val_att, y_test_att = train_test_split(
            X_temp_att, y_temp_att,
            test_size=val_size_adjusted,
            stratify=y_temp_att,
            random_state=self.config.random_state
        )
        
        data_splits = {
            'binary': {
                'train': (X_train_bin, y_train_bin),
                'val': (X_val_bin, y_val_bin),
                'test': (X_test_bin, y_test_bin)
            },
            'multiclass': {
                'train': (X_train_att, y_train_att),
                'val': (X_val_att, y_val_att),
                'test': (X_test_att, y_test_att)
            }
        }
        
        # Log data split info
        logger.info("Data splits created:")
        logger.info(f"Binary classification:")
        logger.info(f"  Train: {len(X_train_bin):,}, Val: {len(X_val_bin):,}, Test: {len(X_test_bin):,}")
        logger.info(f"Attack classification:")
        logger.info(f"  Train: {len(X_train_att):,}, Val: {len(X_val_att):,}, Test: {len(X_test_att):,}")
        
        return data_splits

class OptunaCatBoostOptimizer:
    """Optuna-based hyperparameter optimization for CatBoost models."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        
    def optimize_binary_classifier(self, data_splits: Dict) -> Dict[str, Any]:
        """Optimize hyperparameters for binary classification."""
        logger.info("Optimizing binary classifier hyperparameters...")
        
        X_train, y_train = data_splits['binary']['train']
        X_val, y_val = data_splits['binary']['val']
        
        def objective(trial):
            params = {
                'iterations': trial.suggest_int('iterations', 500, 2000),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'depth': trial.suggest_int('depth', 4, 10),
                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
                'border_count': trial.suggest_int('border_count', 32, 255),
                'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
                'random_strength': trial.suggest_float('random_strength', 0.0, 10.0),
                'od_type': 'Iter',
                'od_wait': self.config.early_stopping_rounds,
                'random_seed': self.config.random_state,
                'verbose': False,
                'allow_writing_files': False,
                'task_type': 'CPU'
            }
            
            # Add class weights for imbalanced data
            class_weights = compute_class_weight(
                'balanced', classes=np.unique(y_train), y=y_train
            )
            params['class_weights'] = class_weights.tolist()
            
            model = cb.CatBoostClassifier(**params)
            
            try:
                model.fit(
                    X_train, y_train,
                    eval_set=(X_val, y_val),
                    verbose=False,
                    plot=False
                )
                
                # Use F1 score as optimization metric
                y_pred = model.predict(X_val)
                f1 = f1_score(y_val, y_pred)
                
                # Penalty for overfitting
                train_f1 = f1_score(y_train, model.predict(X_train))
                overfitting_penalty = max(0, train_f1 - f1 - 0.05)  # Allow 5% gap
                
                return f1 - overfitting_penalty
                
            except Exception as e:
                logger.warning(f"Trial failed: {str(e)}")
                return 0.0
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.config.n_trials)
        
        logger.info(f"Binary classifier optimization completed:")
        logger.info(f"  Best F1 score: {study.best_value:.4f}")
        logger.info(f"  Best parameters: {study.best_params}")
        
        return study.best_params
    
    def optimize_multiclass_classifier(self, data_splits: Dict) -> Dict[str, Any]:
        """Optimize hyperparameters for multiclass classification."""
        logger.info("Optimizing multiclass classifier hyperparameters...")
        
        X_train, y_train = data_splits['multiclass']['train']
        X_val, y_val = data_splits['multiclass']['val']
        
        def objective(trial):
            params = {
                'iterations': trial.suggest_int('iterations', 500, 2000),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'depth': trial.suggest_int('depth', 4, 10),
                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1.0, 10.0),
                'border_count': trial.suggest_int('border_count', 32, 255),
                'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
                'random_strength': trial.suggest_float('random_strength', 0.0, 10.0),
                'od_type': 'Iter',
                'od_wait': self.config.early_stopping_rounds,
                'random_seed': self.config.random_state,
                'verbose': False,
                'allow_writing_files': False,
                'task_type': 'CPU'
            }
            
            # Add class weights for imbalanced data
            class_weights = compute_class_weight(
                'balanced', classes=np.unique(y_train), y=y_train
            )
            params['class_weights'] = class_weights.tolist()
            
            model = cb.CatBoostClassifier(**params)
            
            try:
                model.fit(
                    X_train, y_train,
                    eval_set=(X_val, y_val),
                    verbose=False,
                    plot=False
                )
                
                # Use weighted F1 score for multiclass
                y_pred = model.predict(X_val)
                f1 = f1_score(y_val, y_pred, average='weighted')
                
                # Penalty for overfitting
                train_f1 = f1_score(y_train, model.predict(X_train), average='weighted')
                overfitting_penalty = max(0, train_f1 - f1 - 0.05)
                
                return f1 - overfitting_penalty
                
            except Exception as e:
                logger.warning(f"Trial failed: {str(e)}")
                return 0.0
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=self.config.n_trials)
        
        logger.info(f"Multiclass classifier optimization completed:")
        logger.info(f"  Best weighted F1 score: {study.best_value:.4f}")
        logger.info(f"  Best parameters: {study.best_params}")
        
        return study.best_params

class TwoStepCatBoostModel:
    """
    Two-step CatBoost model for anomaly detection and attack classification.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.binary_classifier = None
        self.multiclass_classifier = None
        self.processor = CICIDSDataProcessor(config)
        self.optimizer = OptunaCatBoostOptimizer(config)
        
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train both binary and multiclass classifiers."""
        logger.info("Starting two-step model training...")
        
        # Preprocess data
        df_processed = self.processor.clean_and_preprocess(df)
        df_processed, label_info = self.processor.create_attack_labels(df_processed)
        df_processed = self.processor.feature_engineering(df_processed)
        
        # Prepare data splits
        data_splits = self.processor.prepare_data_splits(df_processed)
        
        # Optimize hyperparameters
        binary_params = self.optimizer.optimize_binary_classifier(data_splits)
        multiclass_params = self.optimizer.optimize_multiclass_classifier(data_splits)
        
        # Train final models
        logger.info("Training final binary classifier...")
        self.binary_classifier = self._train_binary_classifier(
            data_splits, binary_params
        )
        
        logger.info("Training final multiclass classifier...")
        self.multiclass_classifier = self._train_multiclass_classifier(
            data_splits, multiclass_params
        )
        
        # Evaluate models
        binary_metrics = self._evaluate_binary_classifier(data_splits)
        multiclass_metrics = self._evaluate_multiclass_classifier(data_splits)
        
        results = {
            'label_info': label_info,
            'binary_params': binary_params,
            'multiclass_params': multiclass_params,
            'binary_metrics': binary_metrics,
            'multiclass_metrics': multiclass_metrics,
            'feature_importance': self._get_feature_importance()
        }
        
        # Save models and results
        self._save_models_and_results(results)
        
        return results
    
    def _train_binary_classifier(self, data_splits: Dict, params: Dict) -> cb.CatBoostClassifier:
        """Train the binary classifier with optimized parameters."""
        X_train, y_train = data_splits['binary']['train']
        X_val, y_val = data_splits['binary']['val']
        
        # Add class weights
        class_weights = compute_class_weight(
            'balanced', classes=np.unique(y_train), y=y_train
        )
        params['class_weights'] = class_weights.tolist()
        params['verbose'] = self.config.verbose
        
        model = cb.CatBoostClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            verbose=self.config.verbose,
            plot=False
        )
        
        return model
    
    def _train_multiclass_classifier(self, data_splits: Dict, params: Dict) -> cb.CatBoostClassifier:
        """Train the multiclass classifier with optimized parameters."""
        X_train, y_train = data_splits['multiclass']['train']
        X_val, y_val = data_splits['multiclass']['val']
        
        # Add class weights
        class_weights = compute_class_weight(
            'balanced', classes=np.unique(y_train), y=y_train
        )
        params['class_weights'] = class_weights.tolist()
        params['verbose'] = self.config.verbose
        
        model = cb.CatBoostClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            verbose=self.config.verbose,
            plot=False
        )
        
        return model
    
    def _evaluate_binary_classifier(self, data_splits: Dict) -> Dict[str, float]:
        """Evaluate binary classifier performance."""
        X_test, y_test = data_splits['binary']['test']
        
        y_pred = self.binary_classifier.predict(X_test)
        y_pred_proba = self.binary_classifier.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }
        
        logger.info("Binary classifier test metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        
        return metrics
    
    def _evaluate_multiclass_classifier(self, data_splits: Dict) -> Dict[str, float]:
        """Evaluate multiclass classifier performance."""
        X_test, y_test = data_splits['multiclass']['test']
        
        y_pred = self.multiclass_classifier.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision_macro': precision_score(y_test, y_pred, average='macro'),
            'recall_macro': recall_score(y_test, y_pred, average='macro'),
            'f1_macro': f1_score(y_test, y_pred, average='macro'),
            'precision_weighted': precision_score(y_test, y_pred, average='weighted'),
            'recall_weighted': recall_score(y_test, y_pred, average='weighted'),
            'f1_weighted': f1_score(y_test, y_pred, average='weighted')
        }
        
        logger.info("Multiclass classifier test metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")
        
        return metrics
    
    def _get_feature_importance(self) -> Dict[str, List[Tuple[str, float]]]:
        """Get feature importance from both models."""
        binary_importance = list(zip(
            self.processor.feature_columns,
            self.binary_classifier.get_feature_importance()
        ))
        binary_importance.sort(key=lambda x: x[1], reverse=True)
        
        multiclass_importance = list(zip(
            self.processor.feature_columns,
            self.multiclass_classifier.get_feature_importance()
        ))
        multiclass_importance.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'binary': binary_importance[:20],  # Top 20 features
            'multiclass': multiclass_importance[:20]
        }
    
    def _save_models_and_results(self, results: Dict[str, Any]) -> None:
        """Save trained models and results."""
        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save models
        self.binary_classifier.save_model(
            str(self.config.output_dir / 'binary_classifier.cbm')
        )
        self.multiclass_classifier.save_model(
            str(self.config.output_dir / 'multiclass_classifier.cbm')
        )
        
        # Save processor
        with open(self.config.output_dir / 'data_processor.pkl', 'wb') as f:
            pickle.dump(self.processor, f)
        
        # Save results
        with open(self.config.output_dir / 'training_results.json', 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json_results = {}
            for key, value in results.items():
                if key == 'feature_importance':
                    json_results[key] = {
                        'binary': [(feat, float(imp)) for feat, imp in value['binary']],
                        'multiclass': [(feat, float(imp)) for feat, imp in value['multiclass']]
                    }
                else:
                    json_results[key] = value
            
            json.dump(json_results, f, indent=2)
        
        logger.info(f"Models and results saved to {self.config.output_dir}")
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Make predictions using the two-step approach."""
        # Step 1: Binary classification
        binary_pred = self.binary_classifier.predict(X)
        binary_proba = self.binary_classifier.predict_proba(X)
        
        # Step 2: Attack classification (only for predicted attacks)
        attack_mask = binary_pred == 1
        attack_pred = np.full(len(X), -1)  # -1 for benign traffic
        attack_proba = np.zeros((len(X), len(self.processor.attack_types)))
        
        if attack_mask.sum() > 0:
            X_attacks = X[attack_mask]
            attack_pred[attack_mask] = self.multiclass_classifier.predict(X_attacks)
            attack_proba[attack_mask] = self.multiclass_classifier.predict_proba(X_attacks)
        
        return {
            'binary_predictions': binary_pred,
            'binary_probabilities': binary_proba,
            'attack_predictions': attack_pred,
            'attack_probabilities': attack_proba
        }

class ModelVisualizer:
    """Visualization utilities for model results."""
    
    def __init__(self, model: TwoStepCatBoostModel, results: Dict[str, Any]):
        self.model = model
        self.results = results
        
    def plot_feature_importance(self, save_path: Optional[Path] = None) -> None:
        """Plot feature importance for both models."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Binary classifier feature importance
        binary_features, binary_importance = zip(*self.results['feature_importance']['binary'][:15])
        ax1.barh(range(len(binary_features)), binary_importance)
        ax1.set_yticks(range(len(binary_features)))
        ax1.set_yticklabels(binary_features)
        ax1.set_xlabel('Importance')
        ax1.set_title('Binary Classifier - Top 15 Features')
        ax1.invert_yaxis()
        
        # Multiclass classifier feature importance
        multi_features, multi_importance = zip(*self.results['feature_importance']['multiclass'][:15])
        ax2.barh(range(len(multi_features)), multi_importance)
        ax2.set_yticks(range(len(multi_features)))
        ax2.set_yticklabels(multi_features)
        ax2.set_xlabel('Importance')
        ax2.set_title('Multiclass Classifier - Top 15 Features')
        ax2.invert_yaxis()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path / 'feature_importance.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_metrics_comparison(self, save_path: Optional[Path] = None) -> None:
        """Plot metrics comparison for both models."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Binary classifier metrics
        binary_metrics = self.results['binary_metrics']
        ax1.bar(binary_metrics.keys(), binary_metrics.values())
        ax1.set_title('Binary Classifier Metrics')
        ax1.set_ylabel('Score')
        ax1.set_ylim(0, 1)
        ax1.tick_params(axis='x', rotation=45)
        
        # Multiclass classifier metrics
        multiclass_metrics = self.results['multiclass_metrics']
        ax2.bar(multiclass_metrics.keys(), multiclass_metrics.values())
        ax2.set_title('Multiclass Classifier Metrics')
        ax2.set_ylabel('Score')
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path / 'metrics_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    """Main execution function."""
    # Configuration
    config = ModelConfig(
        data_dir=Path("data"),
        output_dir=Path("models/cicids_catboost"),
        n_trials=50,  # Reduced for faster execution
        verbose=True
    )
    
    # Initialize MLflow
    mlflow.set_experiment("CICIDS-CatBoost-TwoStep")
    
    with mlflow.start_run():
        # Initialize model
        model = TwoStepCatBoostModel(config)
        
        # Load and prepare data
        logger.info("Loading CICIDS 2017 dataset...")
        df = model.processor.load_all_datasets()
        
        # Train model
        results = model.train(df)
        
        # Log results to MLflow
        mlflow.log_params(results['binary_params'])
        mlflow.log_params({f"multiclass_{k}": v for k, v in results['multiclass_params'].items()})
        mlflow.log_metrics(results['binary_metrics'])
        mlflow.log_metrics({f"multiclass_{k}": v for k, v in results['multiclass_metrics'].items()})
        
        # Log models
        mlflow.catboost.log_model(model.binary_classifier, "binary_classifier")
        mlflow.catboost.log_model(model.multiclass_classifier, "multiclass_classifier")
        
        # Create visualizations
        visualizer = ModelVisualizer(model, results)
        visualizer.plot_feature_importance(config.output_dir)
        visualizer.plot_metrics_comparison(config.output_dir)
        
        logger.info("Training completed successfully!")
        logger.info(f"Binary F1 Score: {results['binary_metrics']['f1_score']:.4f}")
        logger.info(f"Multiclass F1 Score (weighted): {results['multiclass_metrics']['f1_weighted']:.4f}")

if __name__ == "__main__":
    main()
