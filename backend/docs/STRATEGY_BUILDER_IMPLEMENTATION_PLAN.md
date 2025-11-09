# Strategy Builder 实施计划

## 概述

本文档详细说明Strategy Builder的分阶段实施计划,包括任务分解、技术细节和验收标准。

---

## 阶段1: 核心基础设施 (Week 1-2)

### 1.1 目录结构调整

```
backend/app/modules/strategy/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── strategy_api.py          # 现有
│   └── builder_api.py           # 新增 - Builder API端点
├── schemas/
│   ├── __init__.py
│   ├── strategy.py              # 现有
│   └── builder.py               # 新增 - Builder相关Schema
├── services/
│   ├── __init__.py
│   ├── template_service.py      # 现有
│   ├── instance_service.py      # 现有
│   ├── validation_service.py    # 现有
│   ├── builder_service.py       # 新增 - Builder辅助服务
│   ├── code_generator.py        # 新增 - 代码生成器
│   └── quick_test_service.py    # 新增 - 快速测试服务
├── generators/                  # 新增目录
│   ├── __init__.py
│   ├── base_generator.py        # 基础生成器
│   ├── qlib_generator.py        # Qlib格式生成器
│   ├── node_converters.py       # 节点转换器
│   └── code_templates.py        # 代码模板
└── tasks/
    ├── __init__.py
    └── code_generation.py       # 新增 - Celery异步任务
```

### 1.2 Task 1.1: 创建Builder Schema (2天)

**文件**: `backend/app/modules/strategy/schemas/builder.py`

**内容**:
```python
"""Builder相关的Pydantic Schema"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# FactorComponent Schema
class FactorComponent(BaseModel):
    id: str
    code: str = Field(..., description="因子代码")
    name: str = Field(..., description="因子名称")
    category: str = Field(..., description="因子分类")
    source: str = Field(..., description="因子来源")
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    default_params: Dict[str, Any] = Field(default_factory=dict)
    usage_count: int = 0

class FactorListResponse(BaseModel):
    total: int
    items: List[FactorComponent]
    skip: int
    limit: int

# NodeTemplate Schema
class NodeTemplate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    node_type: str = Field(..., description="节点类型")
    default_config: Dict[str, Any] = Field(default_factory=dict)
    icon: Optional[str] = None
    category: Optional[str] = None

# Code Generation Schemas
class CodeGenerationRequest(BaseModel):
    format: str = Field(default="qlib", description="代码格式")
    include_comments: bool = Field(default=True)
    validation_level: str = Field(default="strict")

class GeneratedCode(BaseModel):
    code: str
    language: str = "python"
    format: str
    imports: List[str] = Field(default_factory=list)
    class_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CodeValidationResult(BaseModel):
    is_valid: bool
    syntax_errors: List[Dict[str, Any]] = Field(default_factory=list)
    import_errors: List[str] = Field(default_factory=list)
    security_issues: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

# Quick Test Schemas
class QuickTestRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    benchmark: str = "SH000300"

class QuickTestResult(BaseModel):
    task_id: str
    status: str
    progress: int = 0
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# Export/Import Schemas
class StrategyExport(BaseModel):
    version: str = "1.0"
    strategy: Dict[str, Any]
    metadata: Dict[str, Any]
    template_info: Optional[Dict[str, Any]] = None

class StrategyImport(BaseModel):
    data: StrategyExport
    name: Optional[str] = None
    validate_only: bool = False
```

**验收标准**:
- [ ] 所有Schema通过Pydantic验证
- [ ] Schema包含完整的字段描述
- [ ] 包含示例数据

### 1.3 Task 1.2: 实现BuilderService (3天)

**文件**: `backend/app/modules/strategy/services/builder_service.py`

**核心功能**:
1. 从Indicator模块获取因子列表
2. 因子详情查询和转换
3. 节点模板库管理
4. 逻辑执行预览

**代码骨架**:
```python
"""BuilderService - Strategy Builder辅助服务"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import httpx

from app.modules.strategy.schemas.builder import (
    FactorComponent,
    FactorListResponse,
    NodeTemplate
)

class BuilderService:
    """Strategy Builder辅助服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.indicator_api_base = "http://localhost:8000/api"  # 可配置

    async def get_available_factors(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> FactorListResponse:
        """
        获取可用因子列表

        从Indicator模块获取因子,转换为Builder需要的格式
        """
        # 调用Indicator模块API
        async with httpx.AsyncClient() as client:
            params = {
                "skip": skip,
                "limit": limit,
                "is_enabled": True
            }
            if category:
                params["category"] = category
            if search:
                params["search"] = search

            response = await client.get(
                f"{self.indicator_api_base}/indicators",
                params=params
            )
            response.raise_for_status()
            data = response.json()

        # 转换为FactorComponent格式
        factors = [
            FactorComponent(
                id=item["id"],
                code=item["code"],
                name=item.get("name_en", item["code"]),
                category=item["category"],
                source=item["source"],
                description=item.get("description_en"),
                parameters=item.get("parameters", {}),
                default_params=item.get("default_params", {}),
                usage_count=item.get("usage_count", 0)
            )
            for item in data["indicators"]
        ]

        return FactorListResponse(
            total=data["total"],
            items=factors,
            skip=skip,
            limit=limit
        )

    async def get_factor_details(
        self,
        factor_id: str
    ) -> FactorComponent:
        """获取因子详细信息"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.indicator_api_base}/indicators/{factor_id}"
            )
            response.raise_for_status()
            data = response.json()

        return FactorComponent(
            id=data["id"],
            code=data["code"],
            name=data.get("name_en", data["code"]),
            category=data["category"],
            source=data["source"],
            description=data.get("description_en"),
            parameters=data.get("parameters", {}),
            default_params=data.get("default_params", {}),
            usage_count=data.get("usage_count", 0)
        )

    async def get_node_templates(
        self,
        node_type: Optional[str] = None
    ) -> List[NodeTemplate]:
        """
        获取预定义节点模板

        返回常用的节点配置模板,用于快速创建节点
        """
        templates = self._get_builtin_templates()

        if node_type:
            templates = [t for t in templates if t.node_type == node_type]

        return templates

    def _get_builtin_templates(self) -> List[NodeTemplate]:
        """内置节点模板"""
        return [
            # INDICATOR节点模板
            NodeTemplate(
                id="tpl_sma",
                name="简单移动平均线",
                description="计算简单移动平均线指标",
                node_type="INDICATOR",
                default_config={
                    "indicator": "SMA",
                    "parameters": {"period": 20, "field": "close"}
                },
                icon="trend",
                category="trend"
            ),
            NodeTemplate(
                id="tpl_rsi",
                name="相对强弱指数",
                description="计算RSI指标",
                node_type="INDICATOR",
                default_config={
                    "indicator": "RSI",
                    "parameters": {"period": 14, "field": "close"}
                },
                icon="momentum",
                category="momentum"
            ),
            # CONDITION节点模板
            NodeTemplate(
                id="tpl_price_cross_ma",
                name="价格穿越均线",
                description="价格向上穿越移动平均线",
                node_type="CONDITION",
                default_config={
                    "condition": "close > sma_20"
                },
                icon="condition",
                category="cross"
            ),
            # SIGNAL节点模板
            NodeTemplate(
                id="tpl_buy_signal",
                name="买入信号",
                description="生成买入信号",
                node_type="SIGNAL",
                default_config={
                    "signal_type": "BUY"
                },
                icon="buy",
                category="signal"
            ),
            # POSITION节点模板
            NodeTemplate(
                id="tpl_fixed_position",
                name="固定仓位",
                description="固定百分比仓位管理",
                node_type="POSITION",
                default_config={
                    "position_type": "FIXED",
                    "position_value": 50.0
                },
                icon="position",
                category="risk"
            ),
            # STOP_LOSS节点模板
            NodeTemplate(
                id="tpl_percentage_sl",
                name="百分比止损",
                description="基于百分比的止损策略",
                node_type="STOP_LOSS",
                default_config={
                    "stop_loss_type": "PERCENTAGE",
                    "stop_loss_value": 5.0
                },
                icon="shield",
                category="risk"
            )
        ]
```

**验收标准**:
- [ ] 能成功调用Indicator模块API
- [ ] 因子列表正确转换和返回
- [ ] 节点模板库包含所有节点类型
- [ ] 单元测试覆盖率 > 80%

### 1.4 Task 1.3: 实现代码生成器核心 (5天)

**文件**: `backend/app/modules/strategy/services/code_generator.py`

见下一节详细设计

---

## 阶段2: 代码生成器实现 (Week 2)

### 2.1 Task 2.1: 基础代码生成框架 (2天)

**文件**: `backend/app/modules/strategy/generators/base_generator.py`

**核心类**:
```python
"""基础代码生成器"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.modules.strategy.schemas.strategy import LogicFlow, LogicNode

class BaseCodeGenerator(ABC):
    """代码生成器基类"""

    @abstractmethod
    def generate(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any],
        include_comments: bool = True
    ) -> str:
        """生成策略代码"""
        pass

    @abstractmethod
    def _node_to_code(
        self,
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """将节点转换为代码"""
        pass

    def _build_imports(self) -> List[str]:
        """构建import语句"""
        return [
            "import pandas as pd",
            "import numpy as np"
        ]

    def _format_code(self, code: str) -> str:
        """格式化代码"""
        try:
            import black
            return black.format_str(code, mode=black.Mode())
        except ImportError:
            return code
```

**文件**: `backend/app/modules/strategy/generators/node_converters.py`

```python
"""节点转换器 - 将Logic Node转换为代码片段"""

from typing import Dict, Any
from app.modules.strategy.schemas.strategy import LogicNode
from app.database.models.strategy import NodeType

class NodeConverter:
    """节点转换器"""

    @staticmethod
    def indicator_to_code(
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """INDICATOR节点转代码"""
        indicator = node.indicator
        params = node.parameters or {}

        # 示例: SMA
        if indicator == "SMA":
            period = params.get("period", 20)
            field = params.get("field", "close")
            return f"""
    # {node.label or f"SMA({period})"}
    data['{node.id}_sma'] = data['{field}'].rolling(window={period}).mean()
"""

        # 示例: RSI
        elif indicator == "RSI":
            period = params.get("period", 14)
            return f"""
    # {node.label or f"RSI({period})"}
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window={period}).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window={period}).mean()
    rs = gain / loss
    data['{node.id}_rsi'] = 100 - (100 / (1 + rs))
"""

        else:
            # 通用指标处理
            return f"""
    # Custom indicator: {indicator}
    data['{node.id}_{indicator.lower()}'] = calculate_{indicator.lower()}(data, **{params})
"""

    @staticmethod
    def condition_to_code(
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """CONDITION节点转代码"""
        condition = node.condition or "True"

        return f"""
    # Condition: {node.label or condition}
    condition_{node.id} = {condition}
"""

    @staticmethod
    def signal_to_code(
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """SIGNAL节点转代码"""
        signal_type = node.signal_type
        signal_value = 1 if signal_type == "BUY" else -1

        return f"""
    # Generate {signal_type} signal
    signals['{node.id}'] = np.where(condition_{node.id}, {signal_value}, 0)
"""

    @staticmethod
    def position_to_code(
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """POSITION节点转代码"""
        position_type = node.position_type
        position_value = node.position_value or 0

        if position_type == "FIXED":
            return f"""
    # Fixed position: {position_value}%
    positions = signals * {position_value / 100.0}
"""
        else:
            return f"""
    # Dynamic position
    positions = calculate_dynamic_position(signals, data)
"""

    @staticmethod
    def stop_loss_to_code(
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """STOP_LOSS节点转代码"""
        stop_loss_type = node.stop_loss_type
        stop_loss_value = node.stop_loss_value or 0

        if stop_loss_type == "PERCENTAGE":
            return f"""
    # Percentage stop loss: {stop_loss_value}%
    stop_loss = data['close'] * (1 - {stop_loss_value / 100.0})
"""
        else:
            return f"""
    # {stop_loss_type} stop loss
    stop_loss = calculate_stop_loss(data, type='{stop_loss_type}', value={stop_loss_value})
"""
```

### 2.2 Task 2.2: Qlib格式生成器 (2天)

**文件**: `backend/app/modules/strategy/generators/qlib_generator.py`

```python
"""Qlib格式策略代码生成器"""

from typing import Dict, Any, List
from jinja2 import Template
from app.modules.strategy.generators.base_generator import BaseCodeGenerator
from app.modules.strategy.generators.node_converters import NodeConverter
from app.modules.strategy.schemas.strategy import LogicFlow, LogicNode
from app.database.models.strategy import NodeType

class QlibGenerator(BaseCodeGenerator):
    """Qlib策略代码生成器"""

    def generate(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any],
        include_comments: bool = True
    ) -> str:
        """生成Qlib格式策略代码"""

        # 1. 构建imports
        imports = self._build_imports()

        # 2. 生成指标计算代码
        indicator_code = self._generate_indicator_code(logic_flow, parameters)

        # 3. 生成条件判断代码
        condition_code = self._generate_condition_code(logic_flow, parameters)

        # 4. 生成信号生成代码
        signal_code = self._generate_signal_code(logic_flow, parameters)

        # 5. 生成仓位计算代码
        position_code = self._generate_position_code(logic_flow, parameters)

        # 6. 使用模板组装完整代码
        template = Template(self._get_qlib_template())
        code = template.render(
            imports="\n".join(imports),
            parameters=parameters,
            indicator_code=indicator_code,
            condition_code=condition_code,
            signal_code=signal_code,
            position_code=position_code,
            include_comments=include_comments
        )

        # 7. 格式化代码
        return self._format_code(code)

    def _node_to_code(
        self,
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """将节点转换为代码"""
        converter = NodeConverter()

        if node.type == NodeType.INDICATOR:
            return converter.indicator_to_code(node, parameters)
        elif node.type == NodeType.CONDITION:
            return converter.condition_to_code(node, parameters)
        elif node.type == NodeType.SIGNAL:
            return converter.signal_to_code(node, parameters)
        elif node.type == NodeType.POSITION:
            return converter.position_to_code(node, parameters)
        elif node.type == NodeType.STOP_LOSS:
            return converter.stop_loss_to_code(node, parameters)
        else:
            return f"# Unsupported node type: {node.type}\n"

    def _generate_indicator_code(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any]
    ) -> str:
        """生成所有指标计算代码"""
        code_parts = []
        for node in logic_flow.nodes:
            if node.type == NodeType.INDICATOR:
                code_parts.append(self._node_to_code(node, parameters))
        return "\n".join(code_parts)

    def _generate_condition_code(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any]
    ) -> str:
        """生成所有条件判断代码"""
        code_parts = []
        for node in logic_flow.nodes:
            if node.type == NodeType.CONDITION:
                code_parts.append(self._node_to_code(node, parameters))
        return "\n".join(code_parts)

    def _generate_signal_code(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any]
    ) -> str:
        """生成所有信号生成代码"""
        code_parts = []
        for node in logic_flow.nodes:
            if node.type == NodeType.SIGNAL:
                code_parts.append(self._node_to_code(node, parameters))
        return "\n".join(code_parts)

    def _generate_position_code(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any]
    ) -> str:
        """生成仓位计算代码"""
        code_parts = []
        for node in logic_flow.nodes:
            if node.type == NodeType.POSITION:
                code_parts.append(self._node_to_code(node, parameters))
        return "\n".join(code_parts) or "    # Default: full position\n    positions = signals"

    def _get_qlib_template(self) -> str:
        """获取Qlib代码模板"""
        return '''"""
Auto-generated Qlib Strategy
Generated at: {{ now() }}
"""

{{ imports }}
from qlib.strategy import BaseStrategy

class GeneratedStrategy(BaseStrategy):
    """
    自动生成的Qlib策略

    Parameters:
    {% for key, value in parameters.items() %}
        {{ key }}: {{ value }}
    {% endfor %}
    """

    def __init__(self, **kwargs):
        super().__init__()
        {% for key, value in parameters.items() %}
        self.{{ key }} = kwargs.get('{{ key }}', {{ value }})
        {% endfor %}

    def generate_signals(self, data):
        """
        生成交易信号

        Args:
            data: Market data DataFrame

        Returns:
            signals: Trading signals Series
        """
        {% if include_comments %}
        # Initialize signals
        {% endif %}
        signals = pd.Series(0, index=data.index)
        positions = pd.Series(0, index=data.index)

        {% if include_comments %}
        # ==================== Indicator Calculation ====================
        {% endif %}
{{ indicator_code }}

        {% if include_comments %}
        # ==================== Condition Checks ====================
        {% endif %}
{{ condition_code }}

        {% if include_comments %}
        # ==================== Signal Generation ====================
        {% endif %}
{{ signal_code }}

        {% if include_comments %}
        # ==================== Position Sizing ====================
        {% endif %}
{{ position_code }}

        return positions

    def get_risk_degree(self, *args, **kwargs):
        """Risk degree for portfolio management"""
        return 0.95
'''

    def _build_imports(self) -> List[str]:
        """构建Qlib特定的imports"""
        return [
            "import pandas as pd",
            "import numpy as np",
            "from qlib.strategy import BaseStrategy"
        ]
```

**验收标准**:
- [ ] 能生成完整的Qlib策略代码
- [ ] 代码语法正确,可以被Python解析
- [ ] 支持所有节点类型
- [ ] 生成的代码包含适当的注释
- [ ] 代码格式化正确 (使用black)

### 2.3 Task 2.3: 代码验证集成 (1天)

**文件**: `backend/app/modules/strategy/services/code_generator.py`

```python
"""代码生成服务"""

import ast
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.modules.strategy.generators.qlib_generator import QlibGenerator
from app.modules.strategy.schemas.builder import (
    GeneratedCode,
    CodeValidationResult,
    CodeGenerationRequest
)
from app.database.repositories.strategy_instance import StrategyInstanceRepository

class CodeGeneratorService:
    """策略代码生成服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.instance_repo = StrategyInstanceRepository(db)
        self.security_api_base = "http://localhost:8000/api/security"  # 可配置

    async def generate_strategy_code(
        self,
        strategy_id: str,
        request: CodeGenerationRequest
    ) -> GeneratedCode:
        """
        生成策略代码

        Args:
            strategy_id: 策略ID
            request: 代码生成请求

        Returns:
            GeneratedCode: 生成的代码和元数据

        Raises:
            ValueError: 策略不存在或生成失败
        """
        # 1. 获取策略实例
        strategy = await self.instance_repo.get(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy not found: {strategy_id}")

        # 2. 选择生成器
        if request.format == "qlib":
            generator = QlibGenerator()
        else:
            raise ValueError(f"Unsupported format: {request.format}")

        # 3. 生成代码
        from app.modules.strategy.schemas.strategy import LogicFlow
        logic_flow = LogicFlow.model_validate(strategy.logic_flow)

        code = generator.generate(
            logic_flow=logic_flow,
            parameters=strategy.parameters,
            include_comments=request.include_comments
        )

        # 4. 验证代码
        if request.validation_level == "strict":
            validation = await self.validate_code(code)
            if not validation.is_valid:
                raise ValueError(f"Generated code validation failed: {validation.syntax_errors}")

        # 5. 提取imports和class name
        imports, class_name = self._extract_code_metadata(code)

        # 6. 返回结果
        return GeneratedCode(
            code=code,
            language="python",
            format=request.format,
            imports=imports,
            class_name=class_name,
            metadata={
                "strategy_id": strategy_id,
                "node_count": len(logic_flow.nodes),
                "edge_count": len(logic_flow.edges),
                "validation_level": request.validation_level
            }
        )

    async def validate_code(
        self,
        code: str,
        validation_rules: Optional[list] = None
    ) -> CodeValidationResult:
        """
        验证代码

        Args:
            code: Python代码
            validation_rules: 验证规则列表

        Returns:
            CodeValidationResult: 验证结果
        """
        result = CodeValidationResult(is_valid=True)

        # 1. 语法检查
        try:
            ast.parse(code)
        except SyntaxError as e:
            result.is_valid = False
            result.syntax_errors.append({
                "line": e.lineno,
                "column": e.offset,
                "message": e.msg,
                "severity": "error"
            })

        # 2. 检查imports
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_allowed_import(alias.name):
                            result.import_errors.append(
                                f"Disallowed import: {alias.name}"
                            )
                            result.is_valid = False
                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._is_allowed_import(node.module):
                        result.import_errors.append(
                            f"Disallowed import: {node.module}"
                        )
                        result.is_valid = False
        except:
            pass

        # 3. 安全检查 (调用Code Security模块)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.security_api_base}/validate-code",
                    json={"code": code, "language": "python"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    security_result = response.json()
                    if not security_result.get("is_safe", True):
                        result.security_issues = security_result.get("issues", [])
                        result.is_valid = False
        except Exception as e:
            # 安全模块不可用时不影响基本验证
            pass

        return result

    def _extract_code_metadata(self, code: str) -> tuple:
        """提取代码元数据: imports和class name"""
        try:
            tree = ast.parse(code)
            imports = []
            class_name = "GeneratedStrategy"  # default

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = ", ".join(alias.name for alias in node.names)
                    imports.append(f"from {module} import {names}")
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    break

            return imports, class_name
        except:
            return [], "GeneratedStrategy"

    def _is_allowed_import(self, module: str) -> bool:
        """检查import是否在白名单中"""
        allowed_modules = {
            "pandas", "pd",
            "numpy", "np",
            "qlib", "qlib.strategy",
            "talib",
            "datetime", "time",
            "math",
            "typing"
        }

        # 允许子模块
        return any(
            module == allowed or module.startswith(f"{allowed}.")
            for allowed in allowed_modules
        )
```

**验收标准**:
- [ ] 语法错误能被正确检测
- [ ] 危险import被拦截
- [ ] 与Code Security模块集成正常
- [ ] 错误信息清晰明确

---

## 阶段3: API端点实现 (Week 2-3)

### 3.1 Task 3.1: Builder API端点 (2天)

**文件**: `backend/app/modules/strategy/api/builder_api.py`

见API规范文档 (`strategy_builder_api.yaml`)

**验收标准**:
- [ ] 所有端点实现完成
- [ ] 请求/响应符合OpenAPI规范
- [ ] 错误处理完善
- [ ] API文档自动生成

---

## 阶段4: 快速测试集成 (Week 3)

### 4.1 Task 4.1: QuickTestService实现 (3天)

**文件**: `backend/app/modules/strategy/services/quick_test_service.py`

**核心流程**:
1. 生成策略代码
2. 创建Backtest任务
3. 监控任务状态
4. 返回简化结果

**代码骨架**:
```python
"""快速测试服务"""

from typing import Optional
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import uuid

from app.modules.strategy.services.code_generator import CodeGeneratorService
from app.modules.strategy.schemas.builder import (
    QuickTestRequest,
    QuickTestResult,
    CodeGenerationRequest
)

class QuickTestService:
    """快速测试服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.code_generator = CodeGeneratorService(db)
        self.backtest_api_base = "http://localhost:8000/api/backtest"

    async def submit_quick_test(
        self,
        strategy_id: str,
        user_id: str,
        request: QuickTestRequest
    ) -> QuickTestResult:
        """提交快速测试任务"""

        # 1. 生成策略代码
        gen_request = CodeGenerationRequest(
            format="qlib",
            include_comments=False,
            validation_level="basic"
        )
        generated = await self.code_generator.generate_strategy_code(
            strategy_id, gen_request
        )

        # 2. 准备回测参数
        start_date = request.start_date or (date.today() - timedelta(days=90)).isoformat()
        end_date = request.end_date or date.today().isoformat()

        # 3. 调用Backtest模块
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.backtest_api_base}/tasks",
                json={
                    "name": f"Quick Test - {strategy_id}",
                    "strategy_code": generated.code,
                    "start_date": start_date,
                    "end_date": end_date,
                    "benchmark": request.benchmark,
                    "priority": "high",
                    "user_id": user_id
                },
                timeout=30.0
            )
            response.raise_for_status()
            task_data = response.json()

        # 4. 返回任务状态
        return QuickTestResult(
            task_id=task_data["id"],
            status=task_data["status"],
            progress=0,
            started_at=datetime.now()
        )

    async def get_test_status(
        self,
        task_id: str,
        user_id: str
    ) -> QuickTestResult:
        """获取测试状态和结果"""

        # 调用Backtest模块获取结果
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.backtest_api_base}/tasks/{task_id}",
                timeout=10.0
            )
            response.raise_for_status()
            task_data = response.json()

        # 转换为QuickTestResult
        result = QuickTestResult(
            task_id=task_id,
            status=task_data["status"],
            progress=task_data.get("progress", 0),
            started_at=task_data.get("started_at"),
            completed_at=task_data.get("completed_at")
        )

        # 如果完成,提取简化结果
        if task_data["status"] == "completed" and "results" in task_data:
            result.results = {
                "metrics": {
                    "total_return": task_data["results"].get("total_return"),
                    "sharpe_ratio": task_data["results"].get("sharpe_ratio"),
                    "max_drawdown": task_data["results"].get("max_drawdown"),
                    "win_rate": task_data["results"].get("win_rate")
                },
                "chart_data": task_data["results"].get("equity_curve"),
                "trade_summary": task_data["results"].get("trade_summary")
            }

        if task_data["status"] == "failed":
            result.error = task_data.get("error_message")

        return result
```

**验收标准**:
- [ ] 能成功创建Backtest任务
- [ ] 任务状态正确同步
- [ ] 结果格式简化明了
- [ ] 错误处理完善

---

## 阶段5: 测试和优化 (Week 4-5)

### 5.1 单元测试 (3天)
- BuilderService测试
- CodeGenerator测试
- QuickTestService测试
- API端点测试

### 5.2 集成测试 (2天)
- 完整流程测试
- 与其他模块集成测试
- 性能测试

### 5.3 文档和部署 (2天)
- API文档完善
- 用户手册
- 部署配置

---

## 总结

**总时间**: 5周
**关键里程碑**:
- Week 1: 基础设施完成
- Week 2: 代码生成器完成
- Week 3: 快速测试集成完成
- Week 4-5: 测试和上线

**成功指标**:
- [ ] 所有API端点实现并通过测试
- [ ] 代码生成成功率 > 95%
- [ ] 快速测试成功率 > 90%
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖所有核心流程
