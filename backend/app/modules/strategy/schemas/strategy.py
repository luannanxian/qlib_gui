"""
Pydantic Schemas for Strategy Template System

Defines request/response schemas for:
- Logic flow structures (nodes, edges)
- Strategy templates
- Strategy instances
- Template ratings
- Validation results
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from app.database.models.strategy import (
    StrategyCategory,
    StrategyStatus,
    NodeType,
    SignalType,
    PositionType,
    StopLossType
)


# ========================================
# Logic Flow Schemas
# ========================================

class LogicNode(BaseModel):
    """Node in the logic flow graph"""
    id: str = Field(..., description="Unique node ID")
    type: NodeType = Field(..., description="Node type (INDICATOR, CONDITION, SIGNAL, etc.)")
    label: Optional[str] = Field(None, description="Node label for display")

    # Node-specific fields (flexible JSON)
    indicator: Optional[str] = Field(None, description="Indicator name for INDICATOR nodes")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Node parameters")
    condition: Optional[str] = Field(None, description="Condition expression for CONDITION nodes")
    signal_type: Optional[SignalType] = Field(None, description="Signal type for SIGNAL nodes")
    position_type: Optional[PositionType] = Field(None, description="Position type for POSITION nodes")
    position_value: Optional[float] = Field(None, description="Position percentage (0-100)")
    stop_loss_type: Optional[StopLossType] = Field(None, description="Stop loss type")
    stop_loss_value: Optional[float] = Field(None, description="Stop loss value")

    class Config:
        use_enum_values = True


class LogicEdge(BaseModel):
    """Edge connecting nodes in the logic flow graph"""
    from_: str = Field(..., alias="from", description="Source node ID")
    to: str = Field(..., description="Target node ID")
    label: Optional[str] = Field(None, description="Edge label")

    class Config:
        populate_by_name = True


class LogicFlow(BaseModel):
    """Complete logic flow structure"""
    nodes: List[LogicNode] = Field(default_factory=list, description="List of nodes")
    edges: List[LogicEdge] = Field(default_factory=list, description="List of edges")


# ========================================
# Parameter Definition Schema
# ========================================

class ParameterDefinition(BaseModel):
    """Definition of a strategy parameter"""
    default: Any = Field(..., description="Default value")
    min: Optional[float] = Field(None, description="Minimum value (for numeric parameters)")
    max: Optional[float] = Field(None, description="Maximum value (for numeric parameters)")
    type: str = Field(default="number", description="Parameter type (number, string, boolean)")
    description: Optional[str] = Field(None, description="Parameter description")
    options: Optional[List[Any]] = Field(None, description="Available options (for enum parameters)")


# ========================================
# Strategy Template Schemas
# ========================================

class StrategyTemplateBase(BaseModel):
    """Base schema for strategy template"""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: StrategyCategory = Field(..., description="Strategy category")
    logic_flow: LogicFlow = Field(..., description="Logic flow structure")
    parameters: Dict[str, ParameterDefinition] = Field(default_factory=dict, description="Parameter definitions")

    class Config:
        use_enum_values = True


class StrategyTemplateCreate(StrategyTemplateBase):
    """Schema for creating a strategy template"""
    is_system_template: bool = Field(default=False, description="Whether this is a built-in template")
    backtest_example: Optional[Dict[str, Any]] = Field(None, description="Example backtest results")


class StrategyTemplateUpdate(BaseModel):
    """Schema for updating a strategy template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[StrategyCategory] = None
    logic_flow: Optional[LogicFlow] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    backtest_example: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True


class StrategyTemplateResponse(StrategyTemplateBase):
    """Schema for strategy template response"""
    id: str = Field(..., description="Template ID")
    is_system_template: bool = Field(..., description="Whether this is a built-in template")
    user_id: Optional[str] = Field(None, description="User ID (for custom templates)")
    usage_count: int = Field(..., description="Number of times used")
    rating_average: float = Field(..., description="Average rating (0-5)")
    rating_count: int = Field(..., description="Number of ratings")
    backtest_example: Optional[Dict[str, Any]] = Field(None, description="Example backtest results")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")

    class Config:
        from_attributes = True
        use_enum_values = True


class StrategyTemplateListResponse(BaseModel):
    """Schema for paginated template list response"""
    total: int = Field(..., description="Total number of templates")
    items: List[StrategyTemplateResponse] = Field(..., description="List of templates")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


# ========================================
# Strategy Instance Schemas
# ========================================

class StrategyInstanceBase(BaseModel):
    """Base schema for strategy instance"""
    name: str = Field(..., min_length=1, max_length=255, description="Strategy name")
    logic_flow: LogicFlow = Field(..., description="Logic flow structure")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values")
    status: StrategyStatus = Field(default=StrategyStatus.DRAFT, description="Strategy status")

    class Config:
        use_enum_values = True


class StrategyCreateRequest(StrategyInstanceBase):
    """Schema for creating a strategy from template"""
    template_id: Optional[str] = Field(None, description="Template ID (None for custom strategies)")


class StrategyUpdateRequest(BaseModel):
    """Schema for updating a strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logic_flow: Optional[LogicFlow] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[StrategyStatus] = None

    class Config:
        use_enum_values = True


class StrategyResponse(StrategyInstanceBase):
    """Schema for strategy instance response"""
    id: str = Field(..., description="Strategy ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    user_id: str = Field(..., description="Owner user ID")
    version: int = Field(..., description="Version number")
    parent_version_id: Optional[str] = Field(None, description="Parent version ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")

    class Config:
        from_attributes = True
        use_enum_values = True


class StrategyVersionResponse(BaseModel):
    """Schema for strategy version history item"""
    id: str = Field(..., description="Version ID")
    version: int = Field(..., description="Version number")
    created_at: datetime = Field(..., description="Creation timestamp")
    parameters: Dict[str, Any] = Field(..., description="Parameter values")

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """Schema for paginated strategy list response"""
    total: int = Field(..., description="Total number of strategies")
    items: List[StrategyResponse] = Field(..., description="List of strategies")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


# ========================================
# Template Rating Schemas
# ========================================

class TemplateRatingCreate(BaseModel):
    """Schema for creating/updating a template rating"""
    rating: int = Field(..., ge=1, le=5, description="Rating value (1-5)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment")


class TemplateRatingResponse(BaseModel):
    """Schema for template rating response"""
    id: str = Field(..., description="Rating ID")
    template_id: str = Field(..., description="Template ID")
    user_id: str = Field(..., description="User ID")
    rating: int = Field(..., description="Rating value (1-5)")
    comment: Optional[str] = Field(None, description="Rating comment")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class TemplateRatingListResponse(BaseModel):
    """Schema for paginated rating list response"""
    total: int = Field(..., description="Total number of ratings")
    items: List[TemplateRatingResponse] = Field(..., description="List of ratings")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


# ========================================
# Validation Schemas
# ========================================

class ValidationError(BaseModel):
    """Single validation error"""
    type: str = Field(..., description="Error type (e.g., 'missing_signal', 'invalid_position')")
    message: str = Field(..., description="Error message")
    node_id: Optional[str] = Field(None, description="Node ID where error occurred")
    severity: str = Field(default="error", description="Severity level (error, warning)")


class StrategyValidationResponse(BaseModel):
    """Schema for strategy validation response"""
    is_valid: bool = Field(..., description="Whether strategy is valid")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")
    warnings: List[ValidationError] = Field(default_factory=list, description="List of validation warnings")


# ========================================
# Query Parameter Schemas
# ========================================

class StrategyTemplateQuery(BaseModel):
    """Query parameters for template listing"""
    category: Optional[StrategyCategory] = None
    is_system_template: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search query")
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)

    class Config:
        use_enum_values = True


class StrategyInstanceQuery(BaseModel):
    """Query parameters for strategy listing"""
    status: Optional[StrategyStatus] = None
    template_id: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)

    class Config:
        use_enum_values = True
