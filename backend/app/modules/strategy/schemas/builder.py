"""
Strategy Builder Schemas

Pydantic models for Strategy Builder API endpoints.

This module provides comprehensive request/response schemas for:
- Node Template management (create, update, list)
- Code generation from logic flows
- Quick test execution
- Session management with auto-save
- Factor integration with Indicator module

Author: Qlib-UI Strategy Builder Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum


# ==================== Enums ====================

class NodeTypeCategory(str, Enum):
    """Node template categories for logic flow builder"""
    INDICATOR = "INDICATOR"
    CONDITION = "CONDITION"
    SIGNAL = "SIGNAL"
    POSITION = "POSITION"
    STOP_LOSS = "STOP_LOSS"
    STOP_PROFIT = "STOP_PROFIT"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    CUSTOM = "CUSTOM"


class QuickTestStatus(str, Enum):
    """Quick test execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ValidationStatus(str, Enum):
    """Code validation status"""
    PENDING = "PENDING"
    VALID = "VALID"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"


class SessionType(str, Enum):
    """Builder session types"""
    DRAFT = "DRAFT"
    AUTOSAVE = "AUTOSAVE"
    COLLABORATIVE = "COLLABORATIVE"


class SecuritySeverity(str, Enum):
    """Security violation severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ==================== Node Template Schemas ====================

class PortDefinition(BaseModel):
    """Port definition for node inputs/outputs"""
    name: str = Field(..., description="Port name")
    type: str = Field(..., description="Port data type (e.g., TIMESERIES, SIGNAL)")
    required: bool = Field(True, description="Whether port is required")
    description: Optional[str] = Field(None, description="Port description")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "price_data",
                "type": "TIMESERIES",
                "required": True,
                "description": "Input price time series data"
            }
        }
    )


class NodeTemplateBase(BaseModel):
    """Base schema for node template"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Unique template name (snake_case)",
        examples=["ma_crossover", "rsi_signal"]
    )
    display_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="UI display name",
        examples=["Moving Average Crossover"]
    )
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Node description and usage guide"
    )
    node_type: NodeTypeCategory = Field(
        ...,
        description="Node type category"
    )
    category: Optional[str] = Field(
        None,
        max_length=100,
        description="Sub-category for organization (e.g., TREND, MOMENTUM)"
    )
    parameter_schema: Dict[str, Any] = Field(
        ...,
        description="JSON Schema for parameter validation"
    )
    default_parameters: Dict[str, Any] = Field(
        ...,
        description="Default parameter values"
    )
    input_ports: List[PortDefinition] = Field(
        ...,
        description="Input port definitions"
    )
    output_ports: List[PortDefinition] = Field(
        ...,
        description="Output port definitions"
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom validation rules"
    )
    execution_hints: Optional[Dict[str, Any]] = Field(
        None,
        description="Code generation hints"
    )
    icon: Optional[str] = Field(
        None,
        max_length=100,
        description="Icon identifier"
    )
    color: Optional[str] = Field(
        None,
        pattern=r'^#[0-9A-Fa-f]{6}$',
        description="Color code for UI",
        examples=["#4CAF50"]
    )

    @field_validator('parameter_schema')
    @classmethod
    def validate_parameter_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameter schema is a valid JSON Schema object"""
        if not isinstance(v, dict):
            raise ValueError("parameter_schema must be a dictionary")
        if 'type' not in v:
            raise ValueError("parameter_schema must have a 'type' field")
        return v


class NodeTemplateCreate(NodeTemplateBase):
    """Schema for creating a custom node template"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "custom_rsi_signal",
                "display_name": "Custom RSI Signal",
                "description": "Generates buy/sell signals based on RSI threshold",
                "node_type": "SIGNAL",
                "category": "MOMENTUM",
                "parameter_schema": {
                    "type": "object",
                    "properties": {
                        "rsi_period": {"type": "integer", "minimum": 2, "maximum": 100, "default": 14},
                        "overbought": {"type": "number", "minimum": 50, "maximum": 100, "default": 70},
                        "oversold": {"type": "number", "minimum": 0, "maximum": 50, "default": 30}
                    },
                    "required": ["rsi_period", "overbought", "oversold"]
                },
                "default_parameters": {
                    "rsi_period": 14,
                    "overbought": 70,
                    "oversold": 30
                },
                "input_ports": [
                    {"name": "price", "type": "TIMESERIES", "required": True}
                ],
                "output_ports": [
                    {"name": "signal", "type": "SIGNAL", "required": True}
                ],
                "icon": "chart-line",
                "color": "#FF5722"
            }
        }
    )


class NodeTemplateUpdate(BaseModel):
    """Schema for updating a custom node template"""
    display_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255
    )
    description: Optional[str] = Field(
        None,
        max_length=5000
    )
    parameter_schema: Optional[Dict[str, Any]] = None
    default_parameters: Optional[Dict[str, Any]] = None
    input_ports: Optional[List[PortDefinition]] = None
    output_ports: Optional[List[PortDefinition]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    execution_hints: Optional[Dict[str, Any]] = None
    icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(
        None,
        pattern=r'^#[0-9A-Fa-f]{6}$'
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "Updated RSI Signal",
                "description": "Enhanced RSI signal generator with dynamic thresholds",
                "default_parameters": {
                    "rsi_period": 21,
                    "overbought": 75,
                    "oversold": 25
                }
            }
        }
    )


class NodeTemplateResponse(NodeTemplateBase):
    """Schema for node template response"""
    id: str = Field(..., description="Template UUID")
    is_system_template: bool = Field(..., description="Whether template is system-defined")
    user_id: Optional[str] = Field(None, description="User ID for custom templates")
    usage_count: int = Field(0, ge=0, description="Number of times used")
    version: str = Field("1.0.0", description="Template version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "tpl_ma_crossover",
                "name": "ma_crossover",
                "display_name": "Moving Average Crossover",
                "description": "Generates buy/sell signals based on MA crossover",
                "node_type": "SIGNAL",
                "category": "TREND",
                "parameter_schema": {
                    "type": "object",
                    "properties": {
                        "short_period": {"type": "integer", "minimum": 1, "maximum": 100, "default": 5},
                        "long_period": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20}
                    },
                    "required": ["short_period", "long_period"]
                },
                "default_parameters": {
                    "short_period": 5,
                    "long_period": 20
                },
                "input_ports": [
                    {"name": "price_data", "type": "TIMESERIES", "required": True}
                ],
                "output_ports": [
                    {"name": "signal", "type": "SIGNAL", "required": True}
                ],
                "is_system_template": True,
                "user_id": None,
                "usage_count": 1250,
                "icon": "chart-line",
                "color": "#4CAF50",
                "version": "1.0.0",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        }
    )


class NodeTemplateListResponse(BaseModel):
    """Schema for paginated node template list"""
    items: List[NodeTemplateResponse] = Field(..., description="Template list")
    total: int = Field(..., ge=0, description="Total number of templates")
    skip: int = Field(..., ge=0, description="Pagination offset")
    limit: int = Field(..., ge=1, description="Page size")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 45,
                "skip": 0,
                "limit": 20
            }
        }
    )


# ==================== Factor Integration Schemas ====================

class FactorReference(BaseModel):
    """Schema for factor reference from Indicator module"""
    id: str = Field(..., description="Factor UUID")
    name: str = Field(..., description="Factor name")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Factor description")
    category: str = Field(..., description="Factor category (e.g., MOMENTUM, TREND)")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Available parameters")
    output_type: str = Field("FLOAT", description="Output data type")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "RSI_14",
                "display_name": "Relative Strength Index (14 days)",
                "description": "Momentum oscillator measuring speed and change of price movements",
                "category": "MOMENTUM",
                "parameters": {
                    "period": {"type": "integer", "min": 2, "max": 100, "default": 14}
                },
                "output_type": "FLOAT"
            }
        }
    )


class FactorListResponse(BaseModel):
    """Schema for factor list response"""
    items: List[FactorReference] = Field(..., description="Factor list")
    total: int = Field(..., ge=0, description="Total number of factors")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 128
            }
        }
    )


# ==================== Code Generation Schemas ====================

class LogicNode(BaseModel):
    """Schema for logic flow node"""
    id: str = Field(..., description="Node ID")
    type: str = Field(..., description="Node type")
    template_id: str = Field(..., description="Template ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Node parameters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "node_1",
                "type": "INDICATOR",
                "template_id": "tpl_ma_crossover",
                "parameters": {"short_period": 5, "long_period": 20}
            }
        }
    )


class LogicEdge(BaseModel):
    """Schema for logic flow edge/connection"""
    id: str = Field(..., description="Edge ID")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_port: Optional[str] = Field(None, description="Source port name")
    target_port: Optional[str] = Field(None, description="Target port name")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "edge_1",
                "source": "node_1",
                "target": "node_2",
                "source_port": "signal",
                "target_port": "condition"
            }
        }
    )


class LogicFlowStructure(BaseModel):
    """Schema for logic flow structure"""
    nodes: List[LogicNode] = Field(..., min_length=1, description="Node list")
    edges: List[LogicEdge] = Field(..., description="Edge list")

    @model_validator(mode='after')
    def validate_node_references(self):
        """Validate that all edge references point to existing nodes"""
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge source node not found: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge target node not found: {edge.target}")
        return self


class CodeGenerationRequest(BaseModel):
    """Schema for code generation request"""
    instance_id: str = Field(..., description="Strategy instance UUID")
    logic_flow: LogicFlowStructure = Field(..., description="Logic flow structure")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameter values")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "logic_flow": {
                    "nodes": [
                        {
                            "id": "node_1",
                            "type": "INDICATOR",
                            "template_id": "tpl_ma_crossover",
                            "parameters": {"short_period": 5, "long_period": 20}
                        }
                    ],
                    "edges": []
                },
                "parameters": {}
            }
        }
    )


class CodeValidationRequest(BaseModel):
    """Schema for code validation request"""
    code: str = Field(..., min_length=1, description="Python code to validate")
    strict_mode: bool = Field(
        True,
        description="Enable strict security checks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "def calculate_signal(data):\n    return data['close'] > data['ma_20']",
                "strict_mode": True
            }
        }
    )


class SyntaxCheck(BaseModel):
    """Schema for syntax validation result"""
    passed: bool = Field(..., description="Whether syntax check passed")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Syntax errors"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passed": False,
                "errors": [
                    {
                        "line": 5,
                        "message": "SyntaxError: invalid syntax"
                    }
                ]
            }
        }
    )


class SecurityViolation(BaseModel):
    """Schema for security violation"""
    severity: SecuritySeverity = Field(..., description="Violation severity")
    line: int = Field(..., ge=1, description="Line number")
    code: str = Field(..., description="Violation code")
    message: str = Field(..., description="Violation message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "CRITICAL",
                "line": 10,
                "code": "DANGEROUS_IMPORT",
                "message": "Import of 'os' module is forbidden"
            }
        }
    )


class SecurityCheck(BaseModel):
    """Schema for security validation result"""
    passed: bool = Field(..., description="Whether security check passed")
    violations: List[SecurityViolation] = Field(
        default_factory=list,
        description="Security violations"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passed": True,
                "violations": []
            }
        }
    )


class ImportCheck(BaseModel):
    """Schema for import validation result"""
    allowed: List[str] = Field(default_factory=list, description="Allowed imports")
    forbidden: List[str] = Field(default_factory=list, description="Forbidden imports")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "allowed": ["numpy", "pandas", "qlib"],
                "forbidden": []
            }
        }
    )


class ComplexityMetrics(BaseModel):
    """Schema for code complexity metrics"""
    cyclomatic_complexity: Optional[int] = Field(None, description="Cyclomatic complexity")
    cognitive_complexity: Optional[int] = Field(None, description="Cognitive complexity")
    max_nesting_depth: Optional[int] = Field(None, description="Maximum nesting depth")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cyclomatic_complexity": 5,
                "cognitive_complexity": 3,
                "max_nesting_depth": 2
            }
        }
    )


class ValidationChecks(BaseModel):
    """Schema for all validation checks"""
    syntax: SyntaxCheck = Field(..., description="Syntax validation result")
    security: SecurityCheck = Field(..., description="Security validation result")
    imports: ImportCheck = Field(..., description="Import validation result")
    complexity: ComplexityMetrics = Field(..., description="Complexity metrics")


class CodeValidationResponse(BaseModel):
    """Schema for code validation response"""
    is_valid: bool = Field(..., description="Overall validation result")
    validation_status: ValidationStatus = Field(..., description="Validation status")
    checks: ValidationChecks = Field(..., description="Detailed validation checks")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "validation_status": "VALID",
                "checks": {
                    "syntax": {"passed": True, "errors": []},
                    "security": {"passed": True, "violations": []},
                    "imports": {"allowed": ["numpy", "pandas"], "forbidden": []},
                    "complexity": {
                        "cyclomatic_complexity": 5,
                        "cognitive_complexity": 3,
                        "max_nesting_depth": 2
                    }
                }
            }
        }
    )


class CodeGenerationResponse(BaseModel):
    """Schema for code generation response"""
    generation_id: str = Field(..., description="Generation record UUID")
    generated_code: str = Field(..., description="Generated Python code")
    code_hash: str = Field(..., description="SHA-256 hash of code")
    validation_status: ValidationStatus = Field(..., description="Validation status")
    validation_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Validation result details"
    )
    syntax_check_passed: bool = Field(..., description="Syntax check result")
    security_check_passed: bool = Field(..., description="Security check result")
    line_count: int = Field(..., ge=0, description="Number of code lines")
    complexity_score: Optional[int] = Field(None, description="Complexity score")
    generation_time: float = Field(..., ge=0, description="Generation time in seconds")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "generation_id": "gen_a1b2c3d4",
                "generated_code": "def strategy_signal(data):\n    return data['close'] > data['ma_20']",
                "code_hash": "a1b2c3d4e5f6...",
                "validation_status": "VALID",
                "validation_result": None,
                "syntax_check_passed": True,
                "security_check_passed": True,
                "line_count": 145,
                "complexity_score": 8,
                "generation_time": 0.253
            }
        }
    )


class CodeGenerationHistoryItem(BaseModel):
    """Schema for code generation history item"""
    id: str = Field(..., description="Generation record UUID")
    code_hash: str = Field(..., description="Code hash")
    validation_status: ValidationStatus = Field(..., description="Validation status")
    syntax_check_passed: Optional[bool] = Field(None, description="Syntax check result")
    security_check_passed: Optional[bool] = Field(None, description="Security check result")
    line_count: int = Field(..., ge=0, description="Line count")
    complexity_score: Optional[int] = Field(None, description="Complexity score")
    generation_time: Optional[float] = Field(None, description="Generation time")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "gen_a1b2c3d4",
                "code_hash": "a1b2c3d4e5f6...",
                "validation_status": "VALID",
                "syntax_check_passed": True,
                "security_check_passed": True,
                "line_count": 145,
                "complexity_score": 8,
                "generation_time": 0.253,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    )


class CodeHistoryResponse(BaseModel):
    """Schema for code generation history response"""
    items: List[CodeGenerationHistoryItem] = Field(..., description="History items")
    total: int = Field(..., ge=0, description="Total count")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 15
            }
        }
    )


# ==================== Quick Test Schemas ====================

class QuickTestConfig(BaseModel):
    """Schema for quick test configuration"""
    date_range: str = Field(
        "3M",
        pattern=r'^(1M|3M|6M|1Y)$',
        description="Test date range"
    )
    stock_pool: str = Field(
        "CSI300",
        pattern=r'^(CSI300|CSI500|CSI800|ALL_A_SHARES)$',
        description="Stock pool"
    )
    initial_capital: float = Field(
        100000.0,
        ge=10000,
        le=10000000,
        description="Initial capital"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_range": "3M",
                "stock_pool": "CSI300",
                "initial_capital": 100000.0
            }
        }
    )


class QuickTestRequest(BaseModel):
    """Schema for quick test request"""
    instance_id: str = Field(..., description="Strategy instance UUID")
    test_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional test name"
    )
    test_config: QuickTestConfig = Field(
        default_factory=QuickTestConfig,
        description="Test configuration"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "test_name": "Quick validation test",
                "test_config": {
                    "date_range": "3M",
                    "stock_pool": "CSI300",
                    "initial_capital": 100000.0
                }
            }
        }
    )


class MetricsSummary(BaseModel):
    """Schema for test metrics summary"""
    total_return: float = Field(..., description="Total return")
    annual_return: float = Field(..., description="Annualized return")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    win_rate: float = Field(..., ge=0, le=1, description="Win rate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_return": 0.15,
                "annual_return": 0.62,
                "sharpe_ratio": 1.85,
                "max_drawdown": -0.08,
                "win_rate": 0.58
            }
        }
    )


class QuickTestResponse(BaseModel):
    """Schema for quick test response"""
    id: str = Field(..., description="Test UUID")
    instance_id: str = Field(..., description="Strategy instance UUID")
    test_name: Optional[str] = Field(None, description="Test name")
    status: QuickTestStatus = Field(..., description="Test status")
    test_config: QuickTestConfig = Field(..., description="Test configuration")
    metrics_summary: Optional[MetricsSummary] = Field(None, description="Metrics summary")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, ge=0, description="Execution time in seconds")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "qt_a1b2c3d4",
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "test_name": "Quick validation test",
                "status": "COMPLETED",
                "test_config": {
                    "date_range": "3M",
                    "stock_pool": "CSI300",
                    "initial_capital": 100000.0
                },
                "metrics_summary": {
                    "total_return": 0.15,
                    "annual_return": 0.62,
                    "sharpe_ratio": 1.85,
                    "max_drawdown": -0.08,
                    "win_rate": 0.58
                },
                "error_message": None,
                "execution_time": 23.5,
                "started_at": "2025-01-15T10:30:00Z",
                "completed_at": "2025-01-15T10:30:23Z",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:23Z"
            }
        }
    )


class QuickTestSummary(BaseModel):
    """Schema for quick test summary (list view)"""
    id: str = Field(..., description="Test UUID")
    instance_id: str = Field(..., description="Strategy instance UUID")
    test_name: Optional[str] = Field(None, description="Test name")
    status: QuickTestStatus = Field(..., description="Test status")
    metrics_summary: Optional[Dict[str, float]] = Field(
        None,
        description="Key metrics summary"
    )
    execution_time: Optional[float] = Field(None, description="Execution time")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "qt_a1b2c3d4",
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "test_name": "Quick validation test",
                "status": "COMPLETED",
                "metrics_summary": {
                    "total_return": 0.15,
                    "sharpe_ratio": 1.85
                },
                "execution_time": 23.5,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    )


class QuickTestHistoryResponse(BaseModel):
    """Schema for quick test history response"""
    items: List[QuickTestSummary] = Field(..., description="Test history items")
    total: int = Field(..., ge=0, description="Total count")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42
            }
        }
    )


# ==================== Session Management Schemas ====================

class SessionUpsertRequest(BaseModel):
    """Schema for creating or updating builder session"""
    instance_id: Optional[str] = Field(
        None,
        description="Strategy instance UUID (null for new unsaved strategies)"
    )
    session_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional session name"
    )
    session_type: SessionType = Field(
        SessionType.AUTOSAVE,
        description="Session type"
    )
    draft_logic_flow: Dict[str, Any] = Field(
        ...,
        description="Draft logic flow JSON"
    )
    draft_parameters: Dict[str, Any] = Field(
        ...,
        description="Draft parameter values"
    )
    draft_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="UI metadata (cursor position, zoom level, etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_name": "MA Crossover Strategy - Draft",
                "session_type": "AUTOSAVE",
                "draft_logic_flow": {
                    "nodes": [
                        {
                            "id": "node_1",
                            "type": "INDICATOR",
                            "template_id": "tpl_ma_crossover"
                        }
                    ],
                    "edges": []
                },
                "draft_parameters": {},
                "draft_metadata": {
                    "viewport": {"x": 0, "y": 0, "zoom": 1.0},
                    "cursor_position": {"x": 100, "y": 200}
                }
            }
        }
    )


class SessionResponse(BaseModel):
    """Schema for builder session response"""
    id: str = Field(..., description="Session UUID")
    instance_id: Optional[str] = Field(None, description="Strategy instance UUID")
    user_id: str = Field(..., description="User UUID")
    session_type: SessionType = Field(..., description="Session type")
    session_name: Optional[str] = Field(None, description="Session name")
    draft_logic_flow: Dict[str, Any] = Field(..., description="Draft logic flow")
    draft_parameters: Dict[str, Any] = Field(..., description="Draft parameters")
    draft_metadata: Optional[Dict[str, Any]] = Field(None, description="UI metadata")
    is_active: bool = Field(..., description="Whether session is active")
    last_activity_at: datetime = Field(..., description="Last activity timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "session_a1b2c3d4",
                "instance_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_001",
                "session_type": "AUTOSAVE",
                "session_name": "MA Crossover Strategy - Draft",
                "draft_logic_flow": {
                    "nodes": [],
                    "edges": []
                },
                "draft_parameters": {},
                "draft_metadata": {
                    "viewport": {"x": 0, "y": 0, "zoom": 1.0}
                },
                "is_active": True,
                "last_activity_at": "2025-01-15T10:30:00Z",
                "expires_at": "2025-01-16T10:30:00Z",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:30:00Z"
            }
        }
    )


# ==================== Export All Schemas ====================

__all__ = [
    # Enums
    "NodeTypeCategory",
    "QuickTestStatus",
    "ValidationStatus",
    "SessionType",
    "SecuritySeverity",

    # Node Templates
    "PortDefinition",
    "NodeTemplateBase",
    "NodeTemplateCreate",
    "NodeTemplateUpdate",
    "NodeTemplateResponse",
    "NodeTemplateListResponse",

    # Factors
    "FactorReference",
    "FactorListResponse",

    # Code Generation
    "LogicNode",
    "LogicEdge",
    "LogicFlowStructure",
    "CodeGenerationRequest",
    "CodeValidationRequest",
    "SyntaxCheck",
    "SecurityViolation",
    "SecurityCheck",
    "ImportCheck",
    "ComplexityMetrics",
    "ValidationChecks",
    "CodeValidationResponse",
    "CodeGenerationResponse",
    "CodeGenerationHistoryItem",
    "CodeHistoryResponse",

    # Quick Test
    "QuickTestConfig",
    "QuickTestRequest",
    "MetricsSummary",
    "QuickTestResponse",
    "QuickTestSummary",
    "QuickTestHistoryResponse",

    # Sessions
    "SessionUpsertRequest",
    "SessionResponse",
]
