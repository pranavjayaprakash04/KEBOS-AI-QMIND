"""
Enhanced Model Type Detection and Classification
Provides comprehensive model type classification for intelligent workflow routing.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
import os
import pickle
import joblib
import json
import re
from pathlib import Path


class ModelType(Enum):
    """Comprehensive model type classification."""
    TRADITIONAL_ML = "traditional_ml"
    DEEP_LEARNING = "deep_learning"
    LLM = "llm"
    COMPUTER_VISION = "computer_vision"
    TIME_SERIES = "time_series"
    MULTIMODAL = "multimodal"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    EMBEDDING = "embedding"
    ENSEMBLE = "ensemble"
    UNKNOWN = "unknown"


class LLMSubtype(Enum):
    """LLM-specific subtypes."""
    GENERATIVE = "generative"
    DISCRIMINATIVE = "discriminative"
    EMBEDDING = "embedding"
    CHAT = "chat"
    INSTRUCTION_FOLLOWING = "instruction_following"
    CODE_GENERATION = "code_generation"
    MULTIMODAL_LLM = "multimodal_llm"


class FrameworkType(Enum):
    """Supported ML frameworks."""
    SKLEARN = "sklearn"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    HUGGINGFACE = "huggingface"
    ONNX = "onnx"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    KERAS = "keras"
    TRANSFORMERS = "transformers"


@dataclass
class ModelClassification:
    """Comprehensive model classification result."""
    model_type: ModelType
    framework: FrameworkType
    subtype: Optional[str] = None
    llm_subtype: Optional[LLMSubtype] = None
    architecture: Optional[str] = None
    task_type: Optional[str] = None
    input_modalities: List[str] = None
    output_modalities: List[str] = None
    estimated_parameters: Optional[int] = None
    model_size_mb: Optional[float] = None
    compatible_modules: List[str] = None
    recommended_workflow: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.input_modalities is None:
            self.input_modalities = []
        if self.output_modalities is None:
            self.output_modalities = []
        if self.compatible_modules is None:
            self.compatible_modules = []
        if self.recommended_workflow is None:
            self.recommended_workflow = []


class EnhancedModelClassifier:
    """Enhanced model classifier with LLM detection and intelligent routing."""
    
    def __init__(self):
        self.llm_indicators = {
            'transformer_keywords': [
                'transformer', 'bert', 'gpt', 'llama', 'falcon', 'bloom',
                'opt', 't5', 'bart', 'roberta', 'deberta', 'electra',
                'mistral', 'mixtral', 'claude', 'palm', 'bard'
            ],
            'architecture_patterns': [
                'attention', 'self_attention', 'multi_head', 'encoder_decoder',
                'causal_lm', 'masked_lm', 'sequence_classification'
            ],
            'config_keys': [
                'vocab_size', 'hidden_size', 'num_attention_heads',
                'num_hidden_layers', 'max_position_embeddings'
            ]
        }
        
        self.workflow_templates = {
            ModelType.LLM: [
                "model_validation",
                "docgen"
            ],
            ModelType.TRADITIONAL_ML: [
                "model_validation",
                "docgen"
            ],
            ModelType.COMPUTER_VISION: [
                "model_validation",
                "docgen"
            ],
            ModelType.TIME_SERIES: [
                "model_validation",
                "docgen"
            ]
        }
        
        self.module_compatibility = {
            ModelType.LLM: {
                "docgen": True
            },
            ModelType.TRADITIONAL_ML: {
                "docgen": True
            },
            ModelType.COMPUTER_VISION: {
                "docgen": True
            }
        }
    
    def classify_model(self, file_path: str, metadata: Dict[str, Any]) -> ModelClassification:
        """
        Classify model with enhanced detection capabilities.
        
        Args:
            file_path: Path to the model file
            metadata: Extracted model metadata
            
        Returns:
            Comprehensive model classification
        """
        try:
            # Get file extension and framework
            file_ext = Path(file_path).suffix.lower()
            framework = self._detect_framework(file_path, metadata)
            
            # Perform classification based on framework and content
            if framework == FrameworkType.HUGGINGFACE or self._is_llm_model(file_path, metadata):
                return self._classify_llm(file_path, metadata, framework)
            elif framework in [FrameworkType.TENSORFLOW, FrameworkType.PYTORCH, FrameworkType.KERAS]:
                return self._classify_deep_learning(file_path, metadata, framework)
            elif framework in [FrameworkType.SKLEARN, FrameworkType.XGBOOST, FrameworkType.LIGHTGBM]:
                return self._classify_traditional_ml(file_path, metadata, framework)
            else:
                return self._classify_unknown(file_path, metadata, framework)
                
        except Exception as e:
            return ModelClassification(
                model_type=ModelType.UNKNOWN,
                framework=FrameworkType.SKLEARN,
                confidence=0.0,
                compatible_modules=["docgen"]
            )
    
    def _detect_framework(self, file_path: str, metadata: Dict[str, Any]) -> FrameworkType:
        """Detect ML framework from file and metadata."""
        file_ext = Path(file_path).suffix.lower()
        
        # Check metadata for framework indicators
        framework_str = metadata.get('framework', '').lower()
        if 'huggingface' in framework_str or 'transformers' in framework_str:
            return FrameworkType.HUGGINGFACE
        elif 'tensorflow' in framework_str:
            return FrameworkType.TENSORFLOW
        elif 'pytorch' in framework_str or 'torch' in framework_str:
            return FrameworkType.PYTORCH
        elif 'sklearn' in framework_str or 'scikit' in framework_str:
            return FrameworkType.SKLEARN
        
        # Check file extension
        extension_mapping = {
            '.pkl': FrameworkType.SKLEARN,
            '.joblib': FrameworkType.SKLEARN,
            '.h5': FrameworkType.TENSORFLOW,
            '.pb': FrameworkType.TENSORFLOW,
            '.pt': FrameworkType.PYTORCH,
            '.pth': FrameworkType.PYTORCH,
            '.onnx': FrameworkType.ONNX
        }
        
        return extension_mapping.get(file_ext, FrameworkType.SKLEARN)
    
    def _is_llm_model(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Detect if model is an LLM based on multiple indicators."""
        # Check metadata for LLM indicators
        model_type = metadata.get('model_type', '').lower()
        
        # Check for transformer/LLM keywords
        text_content = f"{model_type} {metadata.get('architecture', '')} {metadata.get('parameters', {})}".lower()
        
        for keyword in self.llm_indicators['transformer_keywords']:
            if keyword in text_content:
                return True
        
        # Check for transformer architecture patterns
        if isinstance(metadata.get('parameters'), dict):
            params = metadata['parameters']
            for key in self.llm_indicators['config_keys']:
                if key in params:
                    return True
        
        # Check file structure for HuggingFace models
        if self._check_huggingface_structure(file_path):
            return True
        
        # Check for large parameter count (heuristic for LLMs)
        param_count = metadata.get('n_parameters', 0)
        if param_count > 10_000_000:  # 10M+ parameters suggests LLM
            return True
        
        return False
    
    def _check_huggingface_structure(self, file_path: str) -> bool:
        """Check if the model follows HuggingFace structure."""
        base_dir = Path(file_path).parent
        
        # Look for HuggingFace config files
        hf_files = ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'vocab.txt']
        
        for hf_file in hf_files:
            if (base_dir / hf_file).exists():
                return True
        
        return False
    
    def _classify_llm(self, file_path: str, metadata: Dict[str, Any], framework: FrameworkType) -> ModelClassification:
        """Classify LLM models with subtypes."""
        # Detect LLM subtype
        llm_subtype = self._detect_llm_subtype(metadata)
        
        # Estimate parameters and size
        estimated_params = self._estimate_llm_parameters(metadata)
        model_size = metadata.get('file_size', 0) / (1024 * 1024)  # Convert to MB
        
        # Determine architecture
        architecture = self._detect_llm_architecture(metadata)
        
        return ModelClassification(
            model_type=ModelType.LLM,
            framework=framework,
            llm_subtype=llm_subtype,
            architecture=architecture,
            task_type="text_generation",
            input_modalities=["text"],
            output_modalities=["text"],
            estimated_parameters=estimated_params,
            model_size_mb=model_size,
            compatible_modules=["docgen"],
            recommended_workflow=self.workflow_templates[ModelType.LLM],
            confidence=0.9
        )
    
    def _classify_deep_learning(self, file_path: str, metadata: Dict[str, Any], framework: FrameworkType) -> ModelClassification:
        """Classify deep learning models."""
        # Detect if it's computer vision model
        if self._is_vision_model(metadata):
            return ModelClassification(
                model_type=ModelType.COMPUTER_VISION,
                framework=framework,
                architecture=metadata.get('model_type', 'CNN'),
                task_type="image_classification",
                input_modalities=["image"],
                output_modalities=["classification"],
                model_size_mb=metadata.get('file_size', 0) / (1024 * 1024),
                compatible_modules=["docgen"],
                recommended_workflow=self.workflow_templates[ModelType.COMPUTER_VISION],
                confidence=0.8
            )
        
        # Default deep learning classification
        return ModelClassification(
            model_type=ModelType.DEEP_LEARNING,
            framework=framework,
            architecture=metadata.get('model_type', 'Neural Network'),
            input_modalities=["tabular"],
            output_modalities=["classification"],
            model_size_mb=metadata.get('file_size', 0) / (1024 * 1024),
            compatible_modules=["docgen"],
            recommended_workflow=self.workflow_templates[ModelType.TRADITIONAL_ML],
            confidence=0.7
        )
    
    def _classify_traditional_ml(self, file_path: str, metadata: Dict[str, Any], framework: FrameworkType) -> ModelClassification:
        """Classify traditional ML models."""
        model_type = metadata.get('model_type', '').lower()
        
        # Detect ensemble models
        if any(ensemble_term in model_type for ensemble_term in ['random', 'forest', 'gradient', 'boosting', 'bagging']):
            classification_type = ModelType.ENSEMBLE
        else:
            classification_type = ModelType.TRADITIONAL_ML
        
        return ModelClassification(
            model_type=classification_type,
            framework=framework,
            architecture=metadata.get('model_type', 'Traditional ML'),
            task_type=self._detect_task_type(metadata),
            input_modalities=["tabular"],
            output_modalities=["classification"],
            model_size_mb=metadata.get('file_size', 0) / (1024 * 1024),
            compatible_modules=["docgen"],
            recommended_workflow=self.workflow_templates[ModelType.TRADITIONAL_ML],
            confidence=0.85
        )
    
    def _classify_unknown(self, file_path: str, metadata: Dict[str, Any], framework: FrameworkType) -> ModelClassification:
        """Classify unknown models with fallback."""
        return ModelClassification(
            model_type=ModelType.UNKNOWN,
            framework=framework,
            architecture="Unknown",
            compatible_modules=["docgen"],
            recommended_workflow=["model_validation", "docgen"],
            confidence=0.1
        )
    
    def _detect_llm_subtype(self, metadata: Dict[str, Any]) -> LLMSubtype:
        """Detect specific LLM subtype."""
        model_type = metadata.get('model_type', '').lower()
        architecture = metadata.get('architecture', '').lower()
        
        if any(term in model_type for term in ['gpt', 'llama', 'falcon', 'bloom']):
            return LLMSubtype.GENERATIVE
        elif any(term in model_type for term in ['bert', 'roberta', 'deberta']):
            return LLMSubtype.DISCRIMINATIVE
        elif 'embed' in model_type:
            return LLMSubtype.EMBEDDING
        elif any(term in model_type for term in ['chat', 'instruct']):
            return LLMSubtype.CHAT
        else:
            return LLMSubtype.GENERATIVE  # Default for most LLMs
    
    def _detect_llm_architecture(self, metadata: Dict[str, Any]) -> str:
        """Detect LLM architecture details."""
        model_type = metadata.get('model_type', '')
        
        # Common LLM architectures
        if 'gpt' in model_type.lower():
            return 'GPT (Decoder-only Transformer)'
        elif 'bert' in model_type.lower():
            return 'BERT (Encoder-only Transformer)'
        elif 't5' in model_type.lower():
            return 'T5 (Encoder-Decoder Transformer)'
        elif 'llama' in model_type.lower():
            return 'LLaMA (Decoder-only Transformer)'
        else:
            return 'Transformer'
    
    def _estimate_llm_parameters(self, metadata: Dict[str, Any]) -> Optional[int]:
        """Estimate LLM parameter count."""
        # Try to get from metadata
        if 'n_parameters' in metadata:
            return metadata['n_parameters']
        
        # Estimate from model size (rough heuristic)
        file_size = metadata.get('file_size', 0)
        if file_size > 0:
            # Rough estimate: 1 parameter ≈ 4 bytes (fp32) or 2 bytes (fp16)
            return int(file_size / 2)  # Assume fp16
        
        return None
    
    def _is_vision_model(self, metadata: Dict[str, Any]) -> bool:
        """Detect if model is for computer vision."""
        model_type = metadata.get('model_type', '').lower()
        input_shape = metadata.get('input_shape', [])
        
        # Check for vision keywords
        vision_keywords = ['cnn', 'conv', 'resnet', 'vgg', 'inception', 'mobilenet', 'efficientnet']
        if any(keyword in model_type for keyword in vision_keywords):
            return True
        
        # Check input shape (3D or 4D suggests images)
        if isinstance(input_shape, list) and len(input_shape) >= 3:
            return True
        
        return False
    
    def _detect_task_type(self, metadata: Dict[str, Any]) -> str:
        """Detect the task type of the model."""
        model_type = metadata.get('model_type', '').lower()
        
        if 'classifi' in model_type:
            return 'classification'
        elif 'regress' in model_type:
            return 'regression'
        elif 'cluster' in model_type:
            return 'clustering'
        else:
            return 'classification'  # Default assumption
    
    def get_compatible_modules(self, model_classification: ModelClassification) -> List[str]:
        """Get list of compatible modules for a model type."""
        return self.module_compatibility.get(model_classification.model_type, {})
    
    def should_skip_module(self, model_classification: ModelClassification, module_name: str) -> bool:
        """Determine if a module should be skipped for this model type."""
        compatibility = self.module_compatibility.get(model_classification.model_type, {})
        return not compatibility.get(module_name, False)
    
    def get_recommended_workflow(self, model_classification: ModelClassification) -> List[str]:
        """Get recommended workflow steps for a model type."""
        return model_classification.recommended_workflow or ["docgen"]


# Global instance for use across the platform
enhanced_classifier = EnhancedModelClassifier()
