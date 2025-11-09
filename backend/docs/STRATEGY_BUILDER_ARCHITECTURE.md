# Strategy Builder 完整架构设计

## 1. 架构决策

### 决策: 扩展现有Strategy模块,而非创建独立模块

**理由:**

1. **现有基础完善 (90%完成度)**
   - 完整的Logic Flow数据结构 (nodes + edges)
   - 策略模板和实例管理系统
   - 版本控制和快照功能 (最多5个版本)
   - 完善的验证服务 (结构、信号、仓位、止损验证)

2. **避免架构重复**
   - Logic Flow已在Strategy模块中定义
   - 独立模块会导致数据结构重复和同步问题
   - 减少模块间的耦合复杂度

3. **清晰的职责边界**
   - **现有功能**: 策略CRUD、模板管理、版本控制、基础验证
   - **新增功能**: 可视化构建、代码生成、因子集成、快速测试

---

## 2. 现有功能分析

### 2.1 已实现的核心功能

#### Strategy Template系统
- 模板CRUD操作
- 模板分类: TREND_FOLLOWING, OSCILLATION, MULTI_FACTOR
- 模板评分系统 (1-5星,带评论)
- 热门模板查询 (按usage_count排序)
- 使用统计跟踪

#### Strategy Instance管理
- 从模板创建策略实例
- 自定义策略创建 (无模板)
- 策略CRUD操作
- 策略复制/克隆
- 版本快照管理 (最多5个版本,FIFO删除)
- 版本恢复功能

#### Logic Flow系统
- **节点类型**:
  - INDICATOR: 技术指标计算
  - CONDITION: 条件判断
  - SIGNAL: 交易信号 (BUY/SELL)
  - POSITION: 仓位管理
  - STOP_LOSS: 止损
  - STOP_PROFIT: 止盈
- **边(Edge)**: 连接节点,定义执行流程
- **JSON存储**: 灵活的结构存储

#### 验证服务
- 流程结构验证 (非空、节点连接性)
- 信号完整性检查 (至少1个BUY和1个SELL)
- 仓位分配验证 (总和≤100%)
- 止损配置验证
- 循环依赖检测 (警告级别)

### 2.2 数据模型

#### StrategyTemplate表
```sql
- id (UUID, PK)
- name (策略模板名称)
- description (描述)
- category (分类: TREND_FOLLOWING, OSCILLATION, MULTI_FACTOR)
- logic_flow (JSON: 逻辑流程图)
- parameters (JSON: 参数定义)
- is_system_template (是否系统模板)
- user_id (自定义模板的创建者)
- usage_count (使用次数)
- rating_average (平均评分 0-5)
- rating_count (评分次数)
- backtest_example (JSON: 回测示例结果)
- created_at, updated_at, is_deleted
```

#### StrategyInstance表
```sql
- id (UUID, PK)
- name (策略实例名称)
- template_id (FK to StrategyTemplate, nullable)
- user_id (所有者)
- logic_flow (JSON: 逻辑流程图)
- parameters (JSON: 参数值)
- status (DRAFT, TESTING, ACTIVE, ARCHIVED)
- version (版本号)
- parent_version_id (FK to StrategyInstance, nullable)
- created_at, updated_at, is_deleted
```

#### TemplateRating表
```sql
- id (UUID, PK)
- template_id (FK to StrategyTemplate)
- user_id (评分用户)
- rating (1-5)
- comment (评论)
- created_at, updated_at, is_deleted
- UNIQUE(user_id, template_id)
```

---

## 3. 需要补充的功能

### 3.1 功能优先级

#### P0 (必须) - 核心构建功能

**1. 因子库集成API**
- 从Indicator模块获取可用因子列表
- 因子详情查询 (参数定义、默认值)
- 因子分类过滤 (trend, momentum, volatility, volume, custom)
- 因子搜索功能

**2. 策略代码生成**
- Logic Flow转Python代码
- 生成符合Qlib框架的策略代码
- 支持多种输出格式 (qlib, alphalens, custom)
- 包含代码注释和文档

**3. 代码语法验证**
- 与Code Security模块集成
- Python语法检查
- Import验证
- 安全性扫描

#### P1 (重要) - 增强功能

**4. 策略快速测试**
- 与Backtest模块集成
- 简化的回测参数 (默认3个月数据)
- 异步任务执行
- 基础性能指标展示

**5. 节点组件库查询**
- 预定义节点模板
- 按节点类型分类
- 常用配置模板

**6. 实时逻辑验证增强**
- 扩展现有ValidationService
- 实时错误提示
- 警告和建议

#### P2 (可选) - 辅助功能

**7. 策略导入/导出**
- JSON/YAML格式
- 版本兼容性检查
- 模板信息包含

**8. 策略模板克隆和修改**
- 一键克隆模板
- 在构建器中打开编辑
- 保留模板关联

**9. 参数优化建议**
- 基于历史数据的参数范围建议
- 常用参数组合推荐

### 3.2 新增API端点清单

见 `strategy_builder_api.yaml` 文件,主要包括:

**Builder Components (6个端点)**
- `GET /api/builder/factors` - 获取因子列表
- `GET /api/builder/factors/{factor_id}` - 因子详情
- `GET /api/builder/node-templates` - 节点模板库

**Code Generation (3个端点)**
- `POST /api/builder/strategies/{strategy_id}/generate-code` - 生成代码
- `POST /api/builder/validate-code` - 验证代码
- `POST /api/builder/preview-logic` - 预览执行逻辑

**Quick Testing (2个端点)**
- `POST /api/builder/strategies/{strategy_id}/quick-test` - 快速回测
- `GET /api/builder/quick-tests/{task_id}` - 获取测试结果

**Enhanced Templates (3个端点)**
- `POST /api/builder/templates/{template_id}/clone` - 克隆模板
- `GET /api/builder/strategies/{strategy_id}/export` - 导出策略
- `POST /api/builder/strategies/import` - 导入策略

---

## 4. 数据库设计

### 4.1 是否需要新表?

**决策: 不需要新的数据库表**

**理由:**
1. 现有表已足够存储Logic Flow和参数
2. 代码生成结果可以缓存在内存或Redis
3. 快速测试结果由Backtest模块管理
4. 节点模板可以作为系统级StrategyTemplate存储

### 4.2 需要扩展的字段

#### StrategyInstance表扩展 (可选)
```sql
ALTER TABLE strategy_instances
ADD COLUMN generated_code TEXT NULL COMMENT '缓存的生成代码';

ADD COLUMN code_hash VARCHAR(64) NULL COMMENT '代码哈希,用于检测变更';

ADD COLUMN last_code_generated_at TIMESTAMP NULL COMMENT '最后生成代码时间';
```

### 4.3 索引优化

现有索引已足够,但可以考虑:
```sql
-- 用于快速查询用户的草稿策略
CREATE INDEX ix_instance_user_status_updated
ON strategy_instances(user_id, status, updated_at DESC);

-- 用于查询热门因子
-- (在Indicator模块中)
CREATE INDEX ix_indicator_usage_count_desc
ON indicators(usage_count DESC, is_enabled);
```

---

## 5. 模块间交互设计

### 5.1 架构图 (文字描述)

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  - Visual Flow Editor (React Flow / D3.js)              │
│  - Node Component Library                                │
│  - Parameter Configuration Panel                         │
│  - Code Preview & Test Panel                            │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API / WebSocket
                  ↓
┌─────────────────────────────────────────────────────────┐
│              Strategy Builder (扩展层)                    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  BuilderService (新增)                           │   │
│  │  - get_available_factors()                       │   │
│  │  - get_node_templates()                          │   │
│  │  - preview_logic_execution()                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CodeGeneratorService (新增)                     │   │
│  │  - generate_strategy_code()                      │   │
│  │  - validate_generated_code()                     │   │
│  │  - format_code()                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  QuickTestService (新增)                         │   │
│  │  - submit_quick_test()                           │   │
│  │  - get_test_status()                             │   │
│  │  - get_test_results()                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────┬───────────────────┬───────────────────┬───────────┘
      │                   │                   │
      ↓                   ↓                   ↓
┌─────────────┐   ┌──────────────┐   ┌──────────────┐
│  Indicator  │   │   Backtest   │   │Code Security │
│   Module    │   │    Module    │   │   Module     │
│             │   │              │   │              │
│ - 因子库     │   │ - 回测引擎   │   │ - 代码验证   │
│ - 参数定义   │   │ - 任务管理   │   │ - 安全扫描   │
└─────────────┘   └──────────────┘   └──────────────┘
```

### 5.2 集成流程

#### 5.2.1 因子选择流程
```
1. 前端: 用户点击"添加指标节点"
   ↓
2. 前端: GET /api/builder/factors?category=trend
   ↓
3. BuilderService: 调用Indicator模块API
   → GET /api/indicators?category=trend&is_enabled=true
   ↓
4. BuilderService: 转换为FactorComponent格式返回
   ↓
5. 前端: 显示因子列表,用户选择
   ↓
6. 前端: GET /api/builder/factors/{factor_id}
   ↓
7. BuilderService: 获取因子详情(参数定义)
   ↓
8. 前端: 创建INDICATOR节点,填充参数默认值
```

#### 5.2.2 代码生成流程
```
1. 前端: 用户点击"生成代码"
   ↓
2. 前端: POST /api/builder/strategies/{id}/generate-code
   {
     "format": "qlib",
     "include_comments": true
   }
   ↓
3. CodeGeneratorService:
   a) 获取Strategy Instance的logic_flow和parameters
   b) 遍历节点,生成对应代码片段
   c) 组装完整的Qlib策略类
   d) 添加imports和注释
   ↓
4. CodeGeneratorService: 调用Code Security模块
   → POST /api/security/validate-code
   {
     "code": "生成的代码",
     "language": "python"
   }
   ↓
5. Code Security: 返回验证结果
   ↓
6. CodeGeneratorService:
   - 如果有错误: 返回错误信息
   - 如果通过: 返回生成的代码
   ↓
7. 前端: 显示代码,提供下载/复制功能
```

#### 5.2.3 快速测试流程
```
1. 前端: 用户点击"快速测试"
   ↓
2. 前端: POST /api/builder/strategies/{id}/quick-test
   {
     "start_date": "2024-08-01",
     "end_date": "2024-11-01"
   }
   ↓
3. QuickTestService:
   a) 生成策略代码 (调用CodeGeneratorService)
   b) 创建Backtest任务配置
   c) 调用Backtest模块API
   → POST /api/backtest/tasks
   {
     "strategy_code": "生成的代码",
     "start_date": "2024-08-01",
     "end_date": "2024-11-01",
     "benchmark": "SH000300",
     "priority": "high"
   }
   ↓
4. Backtest Module:
   - 创建任务,返回task_id
   - 异步执行回测
   ↓
5. QuickTestService: 返回task_id
   ↓
6. 前端:
   - 显示"测试中"状态
   - 轮询或WebSocket监听进度
   ↓
7. 前端: GET /api/builder/quick-tests/{task_id}
   ↓
8. QuickTestService:
   → GET /api/backtest/tasks/{task_id}/results
   ↓
9. Backtest Module: 返回结果
   ↓
10. QuickTestService: 转换为QuickTestResult格式
   ↓
11. 前端: 显示简化的回测结果
    - 收益率曲线
    - 关键指标 (总收益、夏普、最大回撤、胜率)
```

---

## 6. 核心服务设计

### 6.1 BuilderService

**职责**: 提供构建器所需的组件和辅助功能

```python
class BuilderService:
    """Strategy Builder辅助服务"""

    async def get_available_factors(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> FactorListResponse:
        """获取可用因子列表,从Indicator模块"""

    async def get_factor_details(
        self,
        factor_id: str
    ) -> FactorComponent:
        """获取因子详细信息"""

    async def get_node_templates(
        self,
        node_type: Optional[NodeType] = None
    ) -> List[NodeTemplate]:
        """获取预定义节点模板"""

    async def preview_logic_execution(
        self,
        logic_flow: LogicFlow,
        sample_data: Optional[Dict] = None
    ) -> LogicPreview:
        """预览逻辑执行流程"""
```

### 6.2 CodeGeneratorService

**职责**: 将Logic Flow转换为可执行的Python代码

```python
class CodeGeneratorService:
    """策略代码生成服务"""

    async def generate_strategy_code(
        self,
        strategy_id: str,
        format: CodeFormat = CodeFormat.QLIB,
        include_comments: bool = True
    ) -> GeneratedCode:
        """生成策略代码"""

    async def validate_code(
        self,
        code: str,
        validation_rules: Optional[List[str]] = None
    ) -> CodeValidationResult:
        """验证代码语法和安全性"""

    def _generate_qlib_strategy(
        self,
        logic_flow: LogicFlow,
        parameters: Dict[str, Any]
    ) -> str:
        """生成Qlib格式策略代码"""

    def _node_to_code(
        self,
        node: LogicNode,
        parameters: Dict[str, Any]
    ) -> str:
        """将单个节点转换为代码片段"""
```

### 6.3 QuickTestService

**职责**: 管理快速回测任务

```python
class QuickTestService:
    """快速测试服务"""

    async def submit_quick_test(
        self,
        strategy_id: str,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        benchmark: str = "SH000300"
    ) -> QuickTestTask:
        """提交快速测试任务"""

    async def get_test_status(
        self,
        task_id: str,
        user_id: str
    ) -> QuickTestResult:
        """获取测试状态和结果"""

    async def cancel_test(
        self,
        task_id: str,
        user_id: str
    ) -> bool:
        """取消测试任务"""
```

---

## 7. 代码生成逻辑详解

### 7.1 节点类型到代码的映射

#### INDICATOR节点
```python
# Logic Flow节点
{
  "id": "node_1",
  "type": "INDICATOR",
  "indicator": "SMA",  # 从Indicator模块获取
  "parameters": {"period": 20, "field": "close"}
}

# 生成的代码
def calculate_sma(self, data):
    """计算简单移动平均线"""
    return data['close'].rolling(window=20).mean()
```

#### CONDITION节点
```python
# Logic Flow节点
{
  "id": "node_2",
  "type": "CONDITION",
  "condition": "close > sma_20"
}

# 生成的代码
def check_condition(self, data):
    """检查条件: 收盘价 > SMA(20)"""
    return data['close'] > data['sma_20']
```

#### SIGNAL节点
```python
# Logic Flow节点
{
  "id": "node_3",
  "type": "SIGNAL",
  "signal_type": "BUY"
}

# 生成的代码
def generate_signal(self, data, condition):
    """生成买入信号"""
    signals = pd.Series(0, index=data.index)
    signals[condition] = 1  # 1 = BUY
    return signals
```

#### POSITION节点
```python
# Logic Flow节点
{
  "id": "node_4",
  "type": "POSITION",
  "position_type": "FIXED",
  "position_value": 50.0  # 50%
}

# 生成的代码
def calculate_position(self, signals):
    """计算仓位: 固定50%"""
    return signals * 0.5
```

### 7.2 完整策略代码模板

```python
"""
生成的Qlib策略
策略名称: {strategy_name}
生成时间: {generated_at}
"""

import pandas as pd
import numpy as np
from qlib.strategy import BaseStrategy

class GeneratedStrategy(BaseStrategy):
    """
    自动生成的策略

    参数:
        {parameter_docs}
    """

    def __init__(self, **kwargs):
        super().__init__()
        # 参数初始化
        {parameter_init}

    def generate_signals(self, data):
        """
        生成交易信号

        Args:
            data: 市场数据 DataFrame

        Returns:
            signals: 交易信号序列
        """
        # 计算指标
        {indicator_calculations}

        # 判断条件
        {condition_checks}

        # 生成信号
        {signal_generation}

        # 计算仓位
        {position_calculation}

        return signals

    def get_risk_degree(self, *args, **kwargs):
        """风险度量"""
        return 0.95
```

---

## 8. 技术栈建议

### 8.1 后端 (已有)
- FastAPI - REST API框架
- SQLAlchemy - ORM
- Pydantic - 数据验证
- Celery - 异步任务 (用于代码生成和快速测试)

### 8.2 新增依赖
```python
# 代码生成和格式化
black==24.0.0  # Python代码格式化
autopep8==2.0.0  # 代码风格检查
jinja2==3.1.0  # 代码模板引擎

# 代码分析
ast  # Python内置,AST解析
astroid==3.0.0  # 高级AST分析

# 缓存
redis==5.0.0  # 代码缓存,防止重复生成
```

### 8.3 前端建议 (React)
```json
{
  "react-flow-renderer": "^10.3.0",  // 可视化流程图
  "monaco-editor": "^0.44.0",        // 代码编辑器
  "recharts": "^2.10.0",              // 图表库
  "zustand": "^4.4.0",                // 状态管理
  "react-query": "^5.0.0"             // 数据获取
}
```

---

## 9. 性能优化考虑

### 9.1 代码生成缓存
```python
# 使用Redis缓存生成的代码
cache_key = f"strategy_code:{strategy_id}:{logic_flow_hash}"
if cached := await redis.get(cache_key):
    return cached

code = generate_code(logic_flow)
await redis.setex(cache_key, 3600, code)  # 1小时过期
```

### 9.2 因子列表缓存
```python
# 因子库变化不频繁,可以缓存
@lru_cache(maxsize=128, ttl=300)  # 5分钟缓存
async def get_available_factors():
    ...
```

### 9.3 异步任务
```python
# 代码生成和快速测试使用Celery异步执行
@celery_app.task
def generate_code_async(strategy_id: str):
    """异步代码生成任务"""
    ...

@celery_app.task
def run_quick_test_async(strategy_id: str, params: dict):
    """异步快速测试任务"""
    ...
```

---

## 10. 安全考虑

### 10.1 代码生成安全
- 禁止生成危险操作 (os.system, exec, eval)
- 限制import白名单 (qlib, pandas, numpy, talib等)
- 使用AST分析检测潜在风险

### 10.2 代码执行沙箱
- 快速测试在隔离环境中运行
- 资源限制 (CPU, 内存, 执行时间)
- 网络隔离

### 10.3 用户权限
- 策略只能被所有者查看和修改
- 代码生成需要登录
- 快速测试有频率限制

---

## 11. 测试策略

### 11.1 单元测试
```python
# 测试代码生成器
def test_generate_indicator_code():
    node = LogicNode(
        id="test",
        type=NodeType.INDICATOR,
        indicator="SMA",
        parameters={"period": 20}
    )
    code = generator._node_to_code(node, {})
    assert "rolling(window=20)" in code

# 测试验证器
def test_validate_strategy_code():
    code = "import os; os.system('rm -rf /')"
    result = validator.validate_code(code)
    assert not result.is_valid
    assert any("security" in e.type for e in result.errors)
```

### 11.2 集成测试
```python
# 测试完整流程
async def test_full_builder_workflow():
    # 1. 创建策略
    strategy = await create_strategy(...)

    # 2. 生成代码
    code = await generate_code(strategy.id)
    assert code.is_valid

    # 3. 快速测试
    task = await submit_quick_test(strategy.id)
    result = await wait_for_result(task.id)
    assert result.status == "completed"
```

### 11.3 E2E测试
- 使用Playwright模拟前端操作
- 测试拖拽创建节点 → 生成代码 → 运行测试的完整流程

---

## 12. 监控和日志

### 12.1 关键指标
```python
# 代码生成性能
metrics.histogram(
    "code_generation.duration",
    duration,
    tags={"node_count": len(nodes)}
)

# 快速测试成功率
metrics.increment(
    "quick_test.completed",
    tags={"status": result.status}
)
```

### 12.2 日志记录
```python
logger.info(
    "Generated code for strategy",
    extra={
        "strategy_id": strategy_id,
        "node_count": len(logic_flow.nodes),
        "code_lines": len(code.split('\n')),
        "validation_time": validation_time
    }
)
```

---

## 13. 下一步实施建议

### 阶段1: 核心功能 (2周)
1. **Week 1**:
   - BuilderService: 因子库集成API
   - CodeGeneratorService: 基础代码生成 (INDICATOR, CONDITION, SIGNAL节点)
   - 单元测试

2. **Week 2**:
   - CodeGeneratorService: 完整节点支持 (POSITION, STOP_LOSS)
   - 代码验证集成 (Code Security)
   - API端点实现

### 阶段2: 测试集成 (1周)
3. **Week 3**:
   - QuickTestService: 快速测试功能
   - 与Backtest模块集成
   - 异步任务处理

### 阶段3: 增强功能 (1周)
4. **Week 4**:
   - 节点模板库
   - 策略导入/导出
   - 逻辑执行预览
   - 前端集成测试

### 阶段4: 优化和上线 (1周)
5. **Week 5**:
   - 性能优化 (缓存、异步)
   - 安全加固
   - 文档完善
   - 生产环境部署

---

## 附录: 参考资料

### A. Qlib策略框架
- [Qlib Documentation](https://qlib.readthedocs.io/)
- [Qlib Strategy Examples](https://github.com/microsoft/qlib/tree/main/examples)

### B. React Flow (可视化编辑器)
- [React Flow Documentation](https://reactflow.dev/)
- [Custom Nodes Guide](https://reactflow.dev/docs/guides/custom-nodes/)

### C. 代码生成最佳实践
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [Python AST Module](https://docs.python.org/3/library/ast.html)
- [Black Code Formatter](https://black.readthedocs.io/)
