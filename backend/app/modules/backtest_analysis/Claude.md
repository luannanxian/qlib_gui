# 模块 4: 回测分析模块 (Backtesting & Analysis Module)

## 模块概述

本模块是量化策略验证的核心，负责回测执行、结果分析、策略诊断，提供全面的策略评估能力。

## 核心职责

1. **回测配置**: 时间范围、初始资金、交易成本、约束条件设置
2. **回测执行**: 集成Qlib回测引擎，支持暂停/恢复/终止
3. **结果展示**: 15+核心指标、可视化图表、交易明细
4. **策略诊断**: 收益分析、风险分析、过拟合检测、优化建议

## 子模块结构

```
backtest_analysis/
├── configuration/       # 回测配置子模块
│   ├── config_manager.py    # 配置管理器
│   ├── cost_calculator.py   # 成本计算器
│   └── constraint_validator.py # 约束验证
├── execution/           # 回测执行子模块
│   ├── qlib_engine.py       # Qlib引擎封装
│   ├── task_manager.py      # 任务管理
│   ├── progress_tracker.py  # 进度追踪
│   └── log_handler.py       # 日志处理
├── results/             # 结果展示子模块
│   ├── metrics_calculator.py # 指标计算
│   ├── chart_generator.py    # 图表生成
│   ├── trade_analyzer.py     # 交易分析
│   └── report_exporter.py    # 报告导出
├── diagnosis/           # 策略诊断子模块
│   ├── revenue_analyzer.py   # 收益分析
│   ├── risk_analyzer.py      # 风险分析
│   ├── overfitting_detector.py # 过拟合检测
│   └── suggestion_generator.py # 建议生成
├── models/              # 数据模型
│   ├── backtest.py
│   ├── result.py
│   ├── trade.py
│   └── diagnosis.py
├── services/            # 业务逻辑服务
│   ├── backtest_service.py
│   ├── result_service.py
│   └── diagnosis_service.py
├── api/                 # API端点
│   ├── backtest_api.py
│   ├── result_api.py
│   └── diagnosis_api.py
├── schemas/             # Pydantic schemas
│   └── backtest_schemas.py
└── Claude.md            # 本文档
```

## API 端点

### 回测配置 API
```
POST /api/backtest/config                 # 创建回测配置
GET  /api/backtest/config/{id}            # 获取配置详情
PUT  /api/backtest/config/{id}            # 更新配置
```

### 回测执行 API
```
POST   /api/backtest/start                # 启动回测
POST   /api/backtest/{id}/pause           # 暂停回测
POST   /api/backtest/{id}/resume          # 恢复回测
POST   /api/backtest/{id}/terminate       # 终止回测
GET    /api/backtest/{id}/progress        # 获取进度
GET    /api/backtest/{id}/logs            # 获取日志
WS     /ws/backtest/{id}                  # WebSocket进度推送
```

### 回测结果 API
```
GET  /api/backtest/{id}/results           # 获取回测结果
GET  /api/backtest/{id}/metrics           # 获取核心指标
GET  /api/backtest/{id}/curves            # 获取曲线数据
GET  /api/backtest/{id}/trades            # 获取交易明细
GET  /api/backtest/{id}/holdings          # 获取持仓分布
POST /api/backtest/{id}/export            # 导出结果
```

### 策略诊断 API
```
POST /api/diagnosis/analyze               # 执行诊断分析
GET  /api/diagnosis/{id}/revenue          # 获取收益分析
GET  /api/diagnosis/{id}/risk             # 获取风险分析
GET  /api/diagnosis/{id}/overfitting      # 获取过拟合检测
GET  /api/diagnosis/{id}/suggestions      # 获取优化建议
```

## 数据模型

### BacktestConfig
```python
class BacktestConfig(BaseModel):
    id: str
    strategy_id: str
    time_range: TimeRange  # {start: date, end: date}
    initial_capital: float  # 10万-1000万
    stock_pool: List[str]

    # 交易成本
    trading_costs: TradingCosts

    # 约束条件
    constraints: Constraints

    created_at: datetime
    updated_at: datetime

class TradingCosts(BaseModel):
    commission_type: Literal["ratio", "fixed"]
    commission_value: float = 0.0003  # 默认0.03%
    stamp_duty: float = 0.001  # 默认0.1%
    slippage_type: Literal["ratio", "fixed", "dynamic"]
    slippage_value: float = 0.001  # 默认0.1%

class Constraints(BaseModel):
    limit_stop: bool = True  # 涨跌停限制
    liquidity_threshold: int = 500  # 流动性阈值
    max_position_ratio: float = 0.2  # 单只股票仓位上限
    max_holdings: int = 10  # 最大持仓数量
```

### BacktestResult
```python
class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIAL = "partial"  # 部分完成
    FAILED = "failed"

class BacktestResult(BaseModel):
    id: str
    backtest_id: str
    status: BacktestStatus

    # 核心指标(15+)
    metrics: BacktestMetrics

    # 曲线数据
    curves: CurveData

    # 交易明细
    trades: List[Trade]

    # 持仓分布
    holdings: List[Holding]

    # 元数据
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]  # 秒

class BacktestMetrics(BaseModel):
    cumulative_return: float      # 累计收益率
    annualized_return: float      # 年化收益率
    sharpe_ratio: float           # 夏普比率
    max_drawdown: float           # 最大回撤
    win_rate: float               # 胜率
    profit_loss_ratio: float      # 盈亏比
    volatility: float             # 波动率
    calmar_ratio: float           # 卡玛比率
    sortino_ratio: float          # 索提诺比率
    # ... 更多指标

class Trade(BaseModel):
    date: date
    symbol: str
    action: Literal["buy", "sell"]
    price: float
    quantity: int
    pnl: float  # 盈亏
    commission: float  # 手续费
    holding_days: Optional[int]
```

### DiagnosisResult
```python
class DiagnosisResult(BaseModel):
    id: str
    backtest_id: str

    # 收益分析
    revenue_analysis: RevenueAnalysis

    # 风险分析
    risk_analysis: RiskAnalysis

    # 过拟合检测
    overfitting_detection: OverfittingDetection

    # 优化建议
    suggestions: List[Suggestion]

    created_at: datetime

class RevenueAnalysis(BaseModel):
    top_contributors: List[StockContribution]  # TOP5贡献
    sector_distribution: Dict[str, float]      # 行业分布
    stability_metrics: StabilityMetrics        # 稳定性指标
    period_distribution: Dict[str, float]      # 时段分布

class RiskAnalysis(BaseModel):
    max_drawdown_period: DrawdownPeriod
    volatility_metrics: VolatilityMetrics
    tail_risk: TailRiskMetrics

class OverfittingDetection(BaseModel):
    in_sample_metrics: Dict[str, float]
    out_sample_metrics: Dict[str, float]
    parameter_sensitivity: List[ParameterSensitivity]
    walk_forward_results: List[WalkForwardResult]

class Suggestion(BaseModel):
    category: Literal["position", "parameter", "risk_control"]
    priority: Literal["high", "medium", "low"]
    title: str
    description: str
    action_items: List[str]
```

## 技术要点

### 回测执行
- **Qlib集成**: 封装Qlib Backtest API
- **任务调度**: Celery串行/并行执行
- **状态管理**: Redis缓存回测状态和进度
- **WebSocket**: 实时推送进度和日志
- **断点续传**: 支持暂停后恢复

### 性能优化
- **进度估算**: 基于已处理数据预估剩余时间
- **增量计算**: 指标计算采用增量更新
- **并行计算**: 多策略对比时并行回测
- **缓存策略**: 缓存中间计算结果

### 结果分析
- **指标计算**: 使用empyrical/quantstats库
- **图表生成**: ECharts/Plotly生成交互式图表
- **报告导出**: ReportLab生成PDF报告
- **数据导出**: pandas导出Excel

### 策略诊断
- **统计分析**: scipy统计分析工具
- **过拟合检测**:
  - 样本内/外测试
  - Walk Forward分析
  - 参数敏感性分析
- **建议生成**: 模板化建议+动态参数

## 依赖关系

- **依赖**:
  - 模块2(数据管理) - 回测数据来源
  - 模块3(策略构建) - 回测策略来源
  - 模块5(任务调度) - 任务队列管理
- **被依赖**:
  - 模块3(策略构建) - 参数优化需要回测结果

## 开发优先级

- **Phase 1 (高优先级)**:
  - 回测配置管理
  - 回测执行引擎
  - 核心指标展示
  - 基础图表生成

- **Phase 2 (高优先级)**:
  - 完整策略诊断
  - 过拟合检测
  - 优化建议生成
  - 报告导出功能

## 测试要点

### 单元测试
- 指标计算正确性
- 交易成本计算
- 约束条件验证
- 诊断算法准确性

### 集成测试
- 完整回测流程
- 暂停/恢复功能
- 报告导出完整性

### 性能测试
- 5年200只股票 < 10分钟
- 并发回测稳定性
- 内存占用控制

### 准确性验证
- 与Qlib原生回测结果对比
- 指标计算精度验证
- 交易明细一致性检查

## 注意事项

1. **数据一致性**: 回测结果需要可复现
2. **资源管理**: 回测任务占用资源需要监控
3. **错误处理**: 回测失败提供详细错误信息
4. **结果存储**: 大量回测结果需要定期清理
5. **时间精度**: 日频/分钟频回测时间处理
6. **基准对比**: 提供与沪深300等基准的对比
