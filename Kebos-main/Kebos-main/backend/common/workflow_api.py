"""
Workflow Management API
Provides endpoints for workflow status, control, and monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
import logging
from datetime import datetime

try:
    from .workflow_router import IntelligentWorkflowRouter, WorkflowPriority
    WORKFLOW_ROUTER_AVAILABLE = True
except ImportError:
    # Fallback for when workflow router is not available
    WORKFLOW_ROUTER_AVAILABLE = False
    WorkflowPriority = None

router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = logging.getLogger(__name__)

# Initialize workflow router if available
if WORKFLOW_ROUTER_AVAILABLE:
    try:
        intelligent_router = IntelligentWorkflowRouter()
    except Exception as e:
        logger.warning(f"Failed to initialize workflow router: {e}")
        intelligent_router = None
else:
    intelligent_router = None


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    workflow_id: str = Field(..., description="Workflow identifier")
    model_id: str = Field(..., description="Model identifier")
    model_type: str = Field(..., description="Model type")
    status: str = Field(..., description="Workflow status")
    progress: Dict[str, Any] = Field(default_factory=dict, description="Progress information")
    current_step: Optional[str] = Field(None, description="Current step")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    results: Dict[str, Any] = Field(default_factory=dict, description="Workflow results")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class WorkflowStepRequest(BaseModel):
    """Request model for workflow step operations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    workflow_id: str = Field(..., description="Workflow identifier")
    step_module: str = Field(..., description="Step module name")
    action: str = Field(..., description="Action to perform")  # "complete", "skip", "fail"
    result: Optional[Dict[str, Any]] = Field(None, description="Step result data")
    reason: Optional[str] = Field(None, max_length=500, description="Action reason")
    error: Optional[str] = Field(None, max_length=1000, description="Error message")


class WorkflowPreferences(BaseModel):
    """Model for user workflow preferences."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    skip_modules: List[str] = Field(default_factory=list, description="Modules to skip")
    module_priorities: Dict[str, str] = Field(default_factory=dict, description="Module priority settings")
    module_parameters: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Module parameters")


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get comprehensive status of a workflow.
    
    Args:
        workflow_id: Unique workflow identifier
        
    Returns:
        Comprehensive workflow status
    """
    try:
        if not intelligent_router:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Workflow service not available"
            )
            
        workflow_status = intelligent_router.get_workflow_status(workflow_id)
        
        if not workflow_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowStatusResponse(**workflow_status)
        
        return WorkflowStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/status", response_model=List[WorkflowStatusResponse])
async def get_all_workflows(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by workflow status")
):
    """
    Get status of all workflows with optional filtering.
    
    Args:
        user_id: Optional user ID filter
        model_type: Optional model type filter
        status: Optional status filter
        
    Returns:
        List of workflow statuses
    """
    try:
        workflows = []
        
        for workflow_id, workflow in intelligent_router.active_workflows.items():
            # Apply filters
            if user_id and workflow.user_id != user_id:
                continue
            if model_type and workflow.model_classification.model_type.value != model_type:
                continue
            if status and workflow.status.value != status:
                continue
            
            workflow_status = intelligent_router.get_workflow_status(workflow_id)
            if workflow_status:
                workflows.append(WorkflowStatusResponse(**workflow_status))
        
        return workflows
        
    except Exception as e:
        logger.error(f"Error getting workflows: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflows: {str(e)}"
        )


@router.get("/next-step/{workflow_id}")
async def get_next_step(workflow_id: str):
    """
    Get the next step to execute in a workflow.
    
    Args:
        workflow_id: Unique workflow identifier
        
    Returns:
        Next workflow step information
    """
    try:
        next_step = intelligent_router.get_next_step(workflow_id)
        
        if not next_step:
            # Check if workflow exists
            status = intelligent_router.get_workflow_status(workflow_id)
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow {workflow_id} not found"
                )
            else:
                return {"message": "No more steps to execute", "completed": True}
        
        return {
            "workflow_id": workflow_id,
            "module": next_step.module,
            "priority": next_step.priority.value,
            "estimated_time": next_step.estimated_time,
            "depends_on": next_step.depends_on,
            "parameters": next_step.parameters,
            "optional": next_step.optional
        }
        
    except Exception as e:
        logger.error(f"Error getting next step: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get next step: {str(e)}"
        )


@router.post("/step-control")
async def control_workflow_step(request: WorkflowStepRequest):
    """
    Control workflow step execution (complete, skip, fail).
    
    Args:
        request: Workflow step control request
        
    Returns:
        Operation result
    """
    try:
        success = False
        
        if request.action == "complete":
            if not request.result:
                raise HTTPException(
                    status_code=400,
                    detail="Result is required for completing a step"
                )
            success = intelligent_router.complete_step(
                request.workflow_id,
                request.step_module,
                request.result
            )
        
        elif request.action == "skip":
            if not request.reason:
                raise HTTPException(
                    status_code=400,
                    detail="Reason is required for skipping a step"
                )
            success = intelligent_router.skip_step(
                request.workflow_id,
                request.step_module,
                request.reason
            )
        
        elif request.action == "fail":
            if not request.error:
                raise HTTPException(
                    status_code=400,
                    detail="Error message is required for failing a step"
                )
            success = intelligent_router.fail_step(
                request.workflow_id,
                request.step_module,
                request.error
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action: {request.action}. Must be 'complete', 'skip', or 'fail'"
            )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update workflow step"
            )
        
        return {"success": True, "message": f"Step {request.step_module} {request.action}d successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling workflow step: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to control workflow step: {str(e)}"
        )


@router.get("/compatible-modules/{model_type}")
async def get_compatible_modules(model_type: str):
    """
    Get list of compatible modules for a model type.
    
    Args:
        model_type: Model type identifier
        
    Returns:
        List of compatible modules
    """
    try:
        from common.model_types import ModelType
        
        # Convert string to ModelType enum
        model_type_enum = None
        for mt in ModelType:
            if mt.value == model_type:
                model_type_enum = mt
                break
        
        if not model_type_enum:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {model_type}"
            )
        
        # Create a mock classification to get compatibility
        from common.model_types import ModelClassification
        mock_classification = ModelClassification(
            model_type=model_type_enum,
            framework=None,  # Will be handled by the compatibility check
            confidence=1.0
        )
        
        compatible_modules = intelligent_router.get_compatible_modules(mock_classification)
        
        return {
            "model_type": model_type,
            "compatible_modules": list(compatible_modules.keys()),
            "module_compatibility": compatible_modules
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compatible modules: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compatible modules: {str(e)}"
        )


@router.get("/workflow-templates")
async def get_workflow_templates():
    """
    Get all available workflow templates.
    
    Returns:
        Dictionary of workflow templates by model type
    """
    try:
        templates = {}
        
        for model_type, workflow_steps in intelligent_router.workflow_templates.items():
            templates[model_type.value] = [
                {
                    "module": step.module,
                    "priority": step.priority.value,
                    "estimated_time": step.estimated_time,
                    "depends_on": step.depends_on,
                    "optional": step.optional,
                    "llm_specific": step.llm_specific,
                    "traditional_ml_specific": step.traditional_ml_specific
                }
                for step in workflow_steps
            ]
        
        return {
            "workflow_templates": templates,
            "available_model_types": [mt.value for mt in intelligent_router.workflow_templates.keys()]
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow templates: {str(e)}"
        )


@router.post("/create-custom-workflow")
async def create_custom_workflow(
    model_id: str,
    user_id: str,
    model_type: str,
    preferences: WorkflowPreferences
):
    """
    Create a custom workflow with user preferences.
    
    Args:
        model_id: Model identifier
        user_id: User identifier
        model_type: Model type
        preferences: User workflow preferences
        
    Returns:
        Created workflow information
    """
    try:
        from common.model_types import ModelType, ModelClassification, FrameworkType
        
        # Convert string to ModelType enum
        model_type_enum = None
        for mt in ModelType:
            if mt.value == model_type:
                model_type_enum = mt
                break
        
        if not model_type_enum:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model type: {model_type}"
            )
        
        # Create a basic classification for workflow creation
        mock_classification = ModelClassification(
            model_type=model_type_enum,
            framework=FrameworkType.SKLEARN,  # Default
            confidence=1.0
        )
        
        # Convert preferences to router format
        user_preferences = {}
        for module in preferences.skip_modules:
            user_preferences[f"skip_{module}"] = True
        
        for module, priority in preferences.module_priorities.items():
            user_preferences[f"{module}_priority"] = priority
        
        for module, params in preferences.module_parameters.items():
            user_preferences[f"{module}_params"] = params
        
        # Create workflow
        workflow = intelligent_router.create_workflow(
            model_id=model_id,
            user_id=user_id,
            model_classification=mock_classification,
            user_preferences=user_preferences
        )
        
        return {
            "workflow_id": workflow.workflow_id,
            "model_id": workflow.model_id,
            "user_id": workflow.user_id,
            "estimated_completion": workflow.estimated_completion,
            "total_steps": len(workflow.steps),
            "steps": [
                {
                    "module": step.module,
                    "priority": step.priority.value,
                    "estimated_time": step.estimated_time,
                    "depends_on": step.depends_on,
                    "optional": step.optional
                }
                for step in workflow.steps
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create custom workflow: {str(e)}"
        )
