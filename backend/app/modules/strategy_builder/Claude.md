# 模块 3: 策略构建模块 (Strategy Builder Module)

## 模块概述

本模块是量化策略创建和优化的核心，提供策略模板、指标组件库、可视化策略编辑器和参数优化引擎。

## 核心职责

1. **策略模板管理**: 提供10+经典策略模板，支持模板操作
2. **指标组件库**: 技术指标、Talib指标、财务指标、自定义因子
3. **策略逻辑编辑**: 可视化流程图编辑，节点连接，逻辑校验
4. **参数优化**: 网格搜索、随机搜索，多目标优化

## 子模块结构

```
strategy_builder/
├── templates/           # 策略模板子模块
│   ├── template_manager.py  # 模板管理器
│   ├── builtin_templates/   # 内置模板
│   │   ├── trend/           # 趋势跟踪策略
│   │   ├── oscillation/     # 震荡策略
│   │   └── multi_factor/    # 多因子策略
│   └── template_loader.py   # 模板加载器
├── indicators/          # 指标组件库子模块
│   ├── technical/       # 技术指标
│   │   ├── ma.py        # 移动平均
│   │   ├── macd.py      # MACD
│   │   └── ...
│   ├── talib_wrapper/   # TA-Lib封装
│   │   └── talib_indicators.py
│   ├── financial/       # 财务指标
│   │   ├── pe.py
│   │   ├── pb.py
│   │   └── ...
│   └── custom/          # 自定义因子
│       ├── factor_builder.py
│       └── factor_validator.py
├── logic_editor/        # 策略逻辑编辑器子模块
│   ├── nodes/           # 逻辑节点
│   │   ├── indicator_node.py
│   │   ├── condition_node.py
│   │   ├── signal_node.py
│   │   ├── position_node.py
│   │   └── stop_loss_node.py
│   ├── graph_builder.py # 策略图构建
│   ├── validator.py     # 逻辑校验器
│   └── code_generator.py# 代码生成器
├── optimization/        # 参数优化引擎子模块
│   ├── grid_search.py   # 网格搜索
│   ├── random_search.py # 随机搜索
│   ├── objective.py     # 优化目标函数
│   └── constraint.py    # 约束条件
├── models/              # 数据模型
│   ├── template.py
│   ├── indicator.py
│   ├── strategy.py
│   └── optimization.py
├── services/            # 业务逻辑服务
│   ├── template_service.py
│   ├── indicator_service.py
│   ├── strategy_service.py
│   └── optimization_service.py
├── api/                 # API端点
│   ├── template_api.py
│   ├── indicator_api.py
│   ├── strategy_api.py
│   └── optimization_api.py
├── schemas/             # Pydantic schemas
│   └── strategy_schemas.py
└── Claude.md            # 本文档
```

## API 端点

### 策略模板 API
```
GET  /api/strategy/templates              # 获取模板列表
GET  /api/strategy/templates/{id}         # 获取模板详情
POST /api/strategy/templates/{id}/use     # 使用模板
POST /api/strategy/templates/{id}/copy    # 复制模板
POST /api/strategy/templates/{id}/favorite# 收藏模板
POST /api/strategy/templates/{id}/review  # 评价模板
```

### 指标组件 API
```
GET  /api/indicators/components           # 获取组件列表
GET  /api/indicators/components/{id}      # 获取组件详情
POST /api/indicators/preview              # 预览指标计算
POST /api/factors/create                  # 创建自定义因子
POST /api/factors/backtest                # 因子回测验证
POST /api/factors/publish                 # 发布因子
GET  /api/factors/my                      # 获取我的因子
```

### 策略逻辑 API
```
POST /api/strategy/logic/create           # 创建策略逻辑
PUT  /api/strategy/logic/{id}             # 更新策略逻辑
POST /api/strategy/logic/{id}/validate    # 验证策略逻辑
POST /api/strategy/logic/{id}/snapshot    # 保存快照
GET  /api/strategy/logic/{id}/snapshots   # 获取快照列表
POST /api/strategy/logic/{id}/rollback    # 回退到快照
POST /api/strategy/logic/{id}/export      # 导出Qlib代码
```

### 参数优化 API
```
POST /api/optimization/create             # 创建优化任务
GET  /api/optimization/{task_id}/status   # 获取任务状态
GET  /api/optimization/{task_id}/results  # 获取优化结果
POST /api/optimization/{task_id}/apply    # 应用最优参数
DELETE /api/optimization/{task_id}        # 取消任务
```

## 数据模型

### StrategyTemplate
```python
class StrategyCategory(str, Enum):
    TREND = "trend"
    OSCILLATION = "oscillation"
    MULTI_FACTOR = "multi_factor"

class StrategyTemplate(BaseModel):
    id: str
    name: str
    category: StrategyCategory
    description: str
    flowchart: Dict[str, Any]  # 流程图数据
    parameters: List[ParameterDef]
    backtest_example: Optional[Dict]
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Review] = []
```

### IndicatorComponent
```python
class IndicatorCategory(str, Enum):
    TECHNICAL = "technical"
    TALIB = "talib"
    FINANCIAL = "financial"
    CUSTOM = "custom"

class IndicatorComponent(BaseModel):
    id: str
    name: str
    category: IndicatorCategory
    sub_category: str
    parameters: List[Parameter]
    description: str
    formula: Optional[str]
    code: Optional[str]
    usage_count: int = 0
```

### StrategyLogic
```python
class NodeType(str, Enum):
    INDICATOR = "indicator"
    CONDITION = "condition"
    SIGNAL = "signal"
    POSITION = "position"
    STOP_LOSS = "stop_loss"

class LogicNode(BaseModel):
    id: str
    type: NodeType
    position: Dict[str, float]  # {x, y}
    config: Dict[str, Any]
    locked: bool = False

class StrategyLogic(BaseModel):
    id: str
    name: str
    nodes: List[LogicNode]
    connections: List[Connection]
    snapshots: List[Snapshot] = []
    validation_errors: List[ValidationError] = []
```

### OptimizationTask
```python
class OptimizationAlgorithm(str, Enum):
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"

class OptimizationObjective(str, Enum):
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    ANNUAL_RETURN = "annual_return"

class OptimizationTask(BaseModel):
    id: str
    strategy_id: str
    algorithm: OptimizationAlgorithm
    parameters: List[ParameterRange]
    objective: OptimizationObjective
    constraints: List[Constraint]
    status: TaskStatus
    progress: float = 0.0
    results: Optional[OptimizationResult] = None
```

## 技术要点

### 策略模板
- **模板存储**: JSON格式存储策略配置
- **版本控制**: Git管理模板版本
- **热加载**: 支持动态加载新模板

### 指标组件
- **TA-Lib集成**: Python TA-Lib wrapper
- **自定义因子**: 独立虚拟环境执行
- **代码沙箱**: RestrictedPython限制危险操作
- **因子验证**: IC值计算、分层回测

### 策略编辑
- **图数据结构**: 使用NetworkX管理节点关系
- **逻辑校验**: AST分析检测逻辑错误
- **代码生成**: 根据图结构生成Qlib代码
- **快照管理**: Redis存储快照状态

### 参数优化
- **优化算法**: scipy.optimize、optuna
- **并行计算**: 使用Celery并行评估参数组合
- **早停机制**: 不满足约束条件提前终止
- **结果可视化**: 参数热力图、敏感性曲线

## 依赖关系

- **依赖**:
  - 模块2(数据管理) - 数据用于指标计算
  - 模块4(回测分析) - 参数优化需要回测
  - 模块6(代码安全) - 自定义因子执行
- **被依赖**:
  - 模块4(回测分析) - 使用构建的策略

## 开发优先级

- **Phase 1 (高优先级)**:
  - 策略模板系统(3-5个模板)
  - 基础指标组件(20+技术指标)
  - 策略逻辑编辑器(基础节点)

- **Phase 2 (高优先级)**:
  - Talib指标集成(40+)
  - 自定义因子构建
  - 参数优化引擎
  - 策略诊断功能

## 测试要点

### 单元测试
- 指标计算正确性
- 逻辑校验规则
- 参数优化算法
- 代码生成正确性

### 集成测试
- 策略创建完整流程
- 因子回测验证
- 参数优化端到端

### 性能测试
- 复杂策略图渲染
- 参数优化耗时
- 并发优化任务

## 注意事项

1. **代码安全**: 自定义因子代码必须在沙箱中执行
2. **性能优化**: 参数优化任务提供清晰的耗时估算
3. **用户体验**: 策略编辑器支持撤销/重做
4. **模板质量**: 内置模板需要经过充分回测验证
5. **版本兼容**: 保持与Qlib版本同步更新
