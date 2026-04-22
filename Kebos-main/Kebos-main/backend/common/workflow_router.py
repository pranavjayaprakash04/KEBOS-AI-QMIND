"""
Intelligent Workflow Router
Routes analysis workflows based on model type and user preferences.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from .model_types import ModelClassification, ModelType, enhanced_classifier


class WorkflowPriority(Enum):
    """Workflow execution priority levels."""
    CRITICAL = "critical"      # Security and validation
    HIGH = "high"             # Core analysis
    MEDIUM = "medium"         # Additional insights
    LOW = "low"              # Optional enhancements


class ModuleStatus(Enum):
    """Module execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """Individual workflow step definition."""
    module: str
    priority: WorkflowPriority
    estimated_time: int  # seconds
    depends_on: List[str]
    parameters: Dict[str, Any]
    optional: bool = False
    llm_specific: bool = False
    traditional_ml_specific: bool = False
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.parameters is None:
            self.parameters = {}


@dataclass
class WorkflowExecution:
    """Workflow execution state."""
    workflow_id: str
    model_id: str
    user_id: str
    model_classification: ModelClassification
    steps: List[WorkflowStep]
    current_step: int = 0
    status: ModuleStatus = ModuleStatus.PENDING
    results: Dict[str, Any] = None
    errors: List[str] = None
    start_time: Optional[str] = None
    estimated_completion: Optional[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []


class IntelligentWorkflowRouter:
    """Smart workflow routing based on model type and capabilities."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.workflow_templates = self._initialize_workflow_templates()
        self.module_time_estimates = self._initialize_time_estimates()
        self.active_workflows = {}
    
    def _initialize_workflow_templates(self) -> Dict[ModelType, List[WorkflowStep]]:
        """Initialize predefined workflow templates for different model types."""
        
        # Common validation step for all models
        validation_step = WorkflowStep(
            module="model_validation",
            priority=WorkflowPriority.CRITICAL,
            estimated_time=30,
            depends_on=[],
            parameters={"quick_validation": True}
        )
        
        # LLM-specific workflow
        llm_workflow = [
            validation_step,
            WorkflowStep(
                module="docgen",
                priority=WorkflowPriority.LOW,
                estimated_time=60,
                depends_on=["model_validation"],
                parameters={"include_llm_specific": True}
            )
        ]
        
        # Traditional ML workflow
        traditional_workflow = [
            validation_step,
            WorkflowStep(
                module="docgen",
                priority=WorkflowPriority.LOW,
                estimated_time=45,
                depends_on=["model_validation"],
                parameters={"include_traditional_ml": True}
            )
        ]
        
        # Computer Vision workflow
        vision_workflow = [
            validation_step,
            WorkflowStep(
                module="docgen",
                priority=WorkflowPriority.LOW,
                estimated_time=40,
                depends_on=["model_validation"],
                parameters={"include_vision_specific": True}
            )
        ]
        
        # Time Series workflow
        timeseries_workflow = [
            validation_step,
            WorkflowStep(
                module="docgen",
                priority=WorkflowPriority.LOW,
                estimated_time=50,
                depends_on=["model_validation"],
                parameters={"include_timeseries": True}
            )
        ]
        
        return {
            ModelType.LLM: llm_workflow,
            ModelType.TRADITIONAL_ML: traditional_workflow,
            ModelType.COMPUTER_VISION: vision_workflow,
            ModelType.TIME_SERIES: timeseries_workflow,
            ModelType.DEEP_LEARNING: traditional_workflow,  # Default to traditional
            ModelType.ENSEMBLE: traditional_workflow,
            ModelType.UNKNOWN: [validation_step, WorkflowStep(
                module="docgen",
                priority=WorkflowPriority.LOW,
                estimated_time=30,
                depends_on=["model_validation"],
                parameters={"minimal_report": True}
            )]
        }
    
    def _initialize_time_estimates(self) -> Dict[str, int]:
        """Initialize time estimates for different modules."""
        return {
            "model_validation": 30,
            "docgen": 45
        }
    
    def create_workflow(
        self,
        model_id: str,
        user_id: str,
        model_classification: ModelClassification,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Create an intelligent workflow based on model type and user preferences.
        
        Args:
            model_id: Unique model identifier
            user_id: User identifier
            model_classification: Model classification result
            user_preferences: Optional user preferences for workflow customization
            
        Returns:
            WorkflowExecution object with optimized workflow
        """
        workflow_id = f"workflow_{model_id}_{user_id}_{len(self.active_workflows)}"
        
        # Get base workflow template
        base_workflow = self.workflow_templates.get(
            model_classification.model_type,
            self.workflow_templates[ModelType.UNKNOWN]
        ).copy()
        
        # Customize workflow based on user preferences
        customized_workflow = self._customize_workflow(
            base_workflow,
            model_classification,
            user_preferences or {}
        )
        
        # Optimize workflow order
        optimized_workflow = self._optimize_workflow_order(customized_workflow)
        
        # Create workflow execution
        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            model_id=model_id,
            user_id=user_id,
            model_classification=model_classification,
            steps=optimized_workflow
        )
        
        # Calculate estimated completion time
        total_time = sum(step.estimated_time for step in optimized_workflow)
        workflow.estimated_completion = f"{total_time // 60}m {total_time % 60}s"
        
        self.active_workflows[workflow_id] = workflow
        
        self.logger.info(
            f"Created workflow {workflow_id} for model type {model_classification.model_type.value} "
            f"with {len(optimized_workflow)} steps"
        )
        
        return workflow
    
    def _customize_workflow(
        self,
        base_workflow: List[WorkflowStep],
        model_classification: ModelClassification,
        user_preferences: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Customize workflow based on user preferences and model capabilities."""
        
        customized = []
        
        for step in base_workflow:
            # Check if user wants to skip this module
            if user_preferences.get(f"skip_{step.module}", False):
                continue
            
            # Check model compatibility
            if enhanced_classifier.should_skip_module(model_classification, step.module):
                continue
            
            # Adjust parameters based on user preferences
            customized_step = WorkflowStep(
                module=step.module,
                priority=step.priority,
                estimated_time=step.estimated_time,
                depends_on=step.depends_on.copy(),
                parameters=step.parameters.copy(),
                optional=step.optional,
                llm_specific=step.llm_specific,
                traditional_ml_specific=step.traditional_ml_specific
            )
            
            # Apply user-specific parameters
            module_params = user_preferences.get(f"{step.module}_params", {})
            customized_step.parameters.update(module_params)
            
            # Adjust priority based on user preferences
            priority_override = user_preferences.get(f"{step.module}_priority")
            if priority_override:
                try:
                    customized_step.priority = WorkflowPriority(priority_override)
                except ValueError:
                    pass  # Keep original priority if invalid
            
            customized.append(customized_step)
        
        return customized
    
    def _optimize_workflow_order(self, workflow: List[WorkflowStep]) -> List[WorkflowStep]:
        """Optimize workflow order based on dependencies and priorities."""
        
        # Sort by priority first (critical -> low), then by dependencies
        def sort_key(step):
            priority_order = {
                WorkflowPriority.CRITICAL: 0,
                WorkflowPriority.HIGH: 1,
                WorkflowPriority.MEDIUM: 2,
                WorkflowPriority.LOW: 3
            }
            return (priority_order[step.priority], len(step.depends_on))
        
        # Create dependency-aware ordering
        ordered_workflow = []
        remaining_steps = workflow.copy()
        completed_modules = set()
        
        while remaining_steps:
            # Find steps with satisfied dependencies
            ready_steps = [
                step for step in remaining_steps
                if all(dep in completed_modules for dep in step.depends_on)
            ]
            
            if not ready_steps:
                # Handle circular dependencies or missing dependencies
                self.logger.warning("Circular or missing dependencies detected, adding remaining steps")
                ready_steps = remaining_steps
            
            # Sort ready steps by priority
            ready_steps.sort(key=sort_key)
            
            # Add the highest priority ready step
            next_step = ready_steps[0]
            ordered_workflow.append(next_step)
            completed_modules.add(next_step.module)
            remaining_steps.remove(next_step)
        
        return ordered_workflow
    
    def get_next_step(self, workflow_id: str) -> Optional[WorkflowStep]:
        """Get the next step to execute in the workflow."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow or workflow.current_step >= len(workflow.steps):
            return None
        
        return workflow.steps[workflow.current_step]
    
    def complete_step(
        self,
        workflow_id: str,
        step_module: str,
        result: Dict[str, Any],
        status: ModuleStatus = ModuleStatus.COMPLETED
    ) -> bool:
        """Mark a workflow step as completed and store results."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Find and update the step
        current_step = workflow.steps[workflow.current_step]
        if current_step.module != step_module:
            self.logger.error(f"Step mismatch: expected {current_step.module}, got {step_module}")
            return False
        
        # Store results
        workflow.results[step_module] = {
            "status": status.value,
            "result": result,
            "module": step_module
        }
        
        # Move to next step
        workflow.current_step += 1
        
        self.logger.info(f"Completed step {step_module} in workflow {workflow_id}")
        
        # Check if workflow is complete
        if workflow.current_step >= len(workflow.steps):
            workflow.status = ModuleStatus.COMPLETED
            self.logger.info(f"Workflow {workflow_id} completed")
        
        return True
    
    def skip_step(self, workflow_id: str, step_module: str, reason: str) -> bool:
        """Skip a workflow step with reason."""
        return self.complete_step(
            workflow_id,
            step_module,
            {"skipped": True, "reason": reason},
            ModuleStatus.SKIPPED
        )
    
    def fail_step(self, workflow_id: str, step_module: str, error: str) -> bool:
        """Mark a workflow step as failed."""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.errors.append(f"{step_module}: {error}")
        
        return self.complete_step(
            workflow_id,
            step_module,
            {"error": error},
            ModuleStatus.FAILED
        )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive workflow status."""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return None
        
        completed_steps = workflow.current_step
        total_steps = len(workflow.steps)
        progress_percent = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            "workflow_id": workflow_id,
            "model_id": workflow.model_id,
            "model_type": workflow.model_classification.model_type.value,
            "status": workflow.status.value,
            "progress": {
                "completed_steps": completed_steps,
                "total_steps": total_steps,
                "progress_percent": round(progress_percent, 2)
            },
            "current_step": workflow.steps[workflow.current_step].module if workflow.current_step < total_steps else None,
            "estimated_completion": workflow.estimated_completion,
            "results": workflow.results,
            "errors": workflow.errors
        }
    
    def get_compatible_modules(self, model_classification: ModelClassification) -> List[str]:
        """Get list of compatible modules for a model type."""
        return enhanced_classifier.get_compatible_modules(model_classification)
    
    def estimate_workflow_time(self, workflow_steps: List[WorkflowStep]) -> int:
        """Estimate total workflow execution time in seconds."""
        return sum(step.estimated_time for step in workflow_steps)
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Clean up completed workflows older than specified age."""
        # Implementation would check timestamps and remove old workflows
        # For now, just return count
        return 0


# Global router instance
intelligent_router = IntelligentWorkflowRouter()
