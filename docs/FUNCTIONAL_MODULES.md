# Qlib-UI 功能模块划分文档

## 概述

基于 Qlib-UI PRD V1.2，本文档将整个系统划分为清晰的功能模块，便于开发团队进行架构设计、任务分配和项目管理。

---

## 一、核心功能模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端展示层 (Frontend)                      │
│  React/Next.js + TypeScript + State Management               │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                   API 网关层 (API Gateway)                    │
│  REST API + WebSocket + 认证中间件                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                  业务逻辑层 (Business Logic)                  │
│  数据管理 │ 策略构建 │ 回测引擎 │ 任务调度                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                  数据访问层 (Data Access)                     │
│  Qlib 集成 │ 文件系统 │ 数据库 │ 缓存                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、功能模块详细划分

### 模块 1: 用户引导与模式管理 (User Onboarding & Mode Management)

**模块职责**: 提供新手/专家模式切换，新手引导流程

**子模块**:

- **1.1 模式切换控制器**
  - 新手模式/专家模式状态管理
  - 模式切换UI组件
  - 用户偏好设置持久化

- **1.2 新手引导系统**
  - 3步快速上手教程
  - 引导式操作流程
  - 每步提示说明
  - 进度追踪

- **1.3 帮助与文档系统**
  - 功能说明弹窗
  - 操作示例展示
  - 常见问题解答(FAQ)
  - 指标解读卡片

**技术要点**:

- 前端: React Context/Redux 状态管理
- 交互: 分步引导组件 (如 react-joyride)
- 本地存储: localStorage 保存用户偏好

**依赖关系**: 被所有其他模块依赖，提供全局UI状态

---

### 模块 2: 数据管理模块 (Data Management Module)

**模块职责**: 数据导入、预处理、存储、可视化

#### 子模块 2.1: 数据导入 (Data Import)

**功能点**:

- **2.1.1 本地文件导入**
  - CSV/Excel 文件解析
  - 字段自动识别与手动映射
  - 批量上传(最多10个文件)
  - 数据预览(前100行，分页)
  - 数据校验(缺失/格式/重复)
  - 一键修复功能

- **2.1.2 Qlib 数据源集成**
  - 市场选择(中国A股/美股)
  - 股票代码筛选(行业/市值)
  - 批量搜索添加
  - 时间范围设置(精确到日)
  - 历史数据全量同步
  - 增量更新

- **2.1.3 第三方接口预留**
  - 接口架构设计
  - 未来扩展预留
  - 插件化接口定义

**API 设计**:

```python
POST /api/data/import/file          # 本地文件导入
POST /api/data/import/qlib          # Qlib数据源导入
GET  /api/data/preview/{dataset_id} # 数据预览
POST /api/data/validate/{dataset_id} # 数据校验
POST /api/data/repair/{dataset_id}  # 一键修复
```

**数据模型**:

```typescript
interface Dataset {
  id: string;
  name: string;
  source: 'local' | 'qlib' | 'thirdparty';
  importDate: Date;
  rowCount: number;
  columns: DataColumn[];
  status: 'valid' | 'invalid' | 'pending';
  validationResults: ValidationResult[];
}
```

#### 子模块 2.2: 数据预处理 (Data Preprocessing)

**功能点**:

- **2.2.1 缺失值处理**
  - 删除行
  - 均值填充
  - 中位数填充
  - 前向填充
  - 按列选择处理范围
  - 填充/删除数量统计

- **2.2.2 异常值处理**
  - 标准差法(1-5倍阈值)
  - 分位数法(上下分位数)
  - 替换为阈值/删除行
  - 异常值分布热力图

- **2.2.3 数据转换**
  - 归一化(Min-Max, Z-Score)
  - 标准化(两位小数)
  - 数据类型转换
  - 数据分布直方图预览
  - 转换规则保存

- **2.2.4 数据筛选**
  - 条件筛选(多条件组合)
  - 时间范围筛选
  - 筛选模板保存(最多20个)
  - 筛选结果对比

**API 设计**:

```python
POST /api/data/preprocess/missing      # 缺失值处理
POST /api/data/preprocess/outliers     # 异常值处理
POST /api/data/preprocess/transform    # 数据转换
POST /api/data/preprocess/filter       # 数据筛选
GET  /api/data/preprocess/templates    # 获取模板
POST /api/data/preprocess/templates    # 保存模板
```

**技术要点**:

- 后端: Pandas/NumPy 数据处理
- 性能: 大数据集异步处理
- 可视化: 热力图/直方图生成

#### 子模块 2.3: 数据可视化 (Data Visualization)

**功能点**:

- **2.3.1 基础图表**
  - K线图(蜡烛图/美国线)
  - 成交量副图
  - 均线图(5/10/20/60日，自定义)
  - 缩放/平移交互
  - 数据点详情弹窗

- **2.3.2 技术指标图表**
  - MACD(自定义参数/颜色)
  - RSI(超买超卖区间)
  - KDJ(金叉死叉标记)
  - 多指标同屏(最多3个)
  - 拖拽调整顺序

- **2.3.3 自定义图表**
  - X/Y轴字段选择
  - 图表类型选择(折线/柱状/散点)
  - 样式自定义
  - 图表交互配置

- **2.3.4 图表交互**
  - 指标标注(文字/图片)
  - 数据导出(CSV)
  - 图表保存(PNG，可设置分辨率)
  - 多图表联动

**API 设计**:

```python
POST /api/visualization/chart/basic      # 基础图表
POST /api/visualization/chart/indicator  # 指标图表
POST /api/visualization/chart/custom     # 自定义图表
POST /api/visualization/export           # 导出图表
```

**前端技术栈**:

- 图表库: ECharts / Recharts / TradingView Lightweight Charts
- 交互: 拖拽排序、联动选择
- 导出: html2canvas / jsPDF

**依赖关系**: 依赖子模块 2.1 (数据导入) 和 2.2 (数据预处理)

---

### 模块 3: 策略构建模块 (Strategy Builder Module)

**模块职责**: 策略模板、指标组件、策略逻辑编辑、参数优化

#### 子模块 3.1: 策略模板系统 (Strategy Templates)

**功能点**:

- **3.1.1 模板分类与管理**
  - 趋势跟踪(双均线、MACD)
  - 震荡策略(RSI、布林带)
  - 多因子(PE+PB+ROE)
  - 热门模板TOP5展示
  - 按使用量排序

- **3.1.2 模板详情展示**
  - 策略逻辑流程图
  - 核心参数说明(默认值/推荐范围)
  - 历史回测示例(近3年)
  - 市场/时间周期切换

- **3.1.3 模板操作**
  - 一键使用(进入参数配置)
  - 复制模板(生成副本)
  - 收藏模板(上限10个)
  - 模板评价(星级+评论)

**数据模型**:

```typescript
interface StrategyTemplate {
  id: string;
  name: string;
  category: 'trend' | 'oscillation' | 'multi_factor';
  description: string;
  flowchart: string;  // 流程图数据
  parameters: ParameterDef[];
  backtestExample: BacktestResult;
  usageCount: number;
  rating: number;
  reviews: Review[];
}
```

**API 设计**:

```python
GET  /api/strategy/templates              # 获取模板列表
GET  /api/strategy/templates/{id}         # 获取模板详情
POST /api/strategy/templates/{id}/use     # 使用模板
POST /api/strategy/templates/{id}/copy    # 复制模板
POST /api/strategy/templates/{id}/favorite # 收藏模板
POST /api/strategy/templates/{id}/review  # 评价模板
```

#### 子模块 3.2: 指标组件库 (Indicator Component Library)

**功能点**:

- **3.2.1 组件分类**
  - 技术指标(MA、MACD等20+)
    - 趋势类
    - 震荡类
    - 量能类
  - Talib指标(40+)
    - EMA、RSI、MACD、布林带、KDJ等
    - 按TA-Lib官方分类
  - 财务指标(PE、PB等10+)
    - 盈利能力
    - 偿债能力
  - 自定义因子
    - 用户保存的因子
    - 创建时间/使用次数

- **3.2.2 组件使用**
  - 拖拽到编辑区
  - 参数配置面板
  - 实时预览(前20条)
  - 组件锁定
  - 批量删除

- **3.2.3 因子构建**
  - 可视化公式编辑器
  - Python代码编写
    - 受控虚拟环境
    - 代码补全/语法高亮
    - 运行调试
    - 调用Qlib Factor类
  - 因子回测验证(IC值、分层回测)
  - 发布到个人组件库
  - 共享到社区(可选)

**数据模型**:

```typescript
interface IndicatorComponent {
  id: string;
  name: string;
  category: 'technical' | 'talib' | 'financial' | 'custom';
  subCategory: string;
  parameters: Parameter[];
  description: string;
  formula?: string;
  code?: string;
  usageCount: number;
}

interface CustomFactor {
  id: string;
  name: string;
  type: 'visual' | 'code';
  definition: string;  // 公式或代码
  icValue?: number;
  backtestResult?: LayeredBacktestResult;
  isPublic: boolean;
  createdAt: Date;
}
```

**API 设计**:

```python
GET  /api/indicators/components           # 获取组件列表
GET  /api/indicators/components/{id}      # 获取组件详情
POST /api/indicators/preview              # 预览指标计算
POST /api/factors/create                  # 创建自定义因子
POST /api/factors/backtest                # 因子回测验证
POST /api/factors/publish                 # 发布因子
GET  /api/factors/my                      # 获取我的因子
```

**技术要点**:

- 代码执行: 独立Python虚拟环境
- 安全检查: 静态代码分析(禁止os.system等)
- Talib集成: Python TA-Lib wrapper
- 公式编辑: 可视化拖拽编辑器

#### 子模块 3.3: 策略逻辑编辑器 (Strategy Logic Editor)

**功能点**:

- **3.3.1 编辑界面**
  - 左侧组件库
  - 中间画布(流程图)
  - 右侧参数面板
  - 画布缩放/网格对齐
  - 快照保存(最多5个)

- **3.3.2 逻辑节点**
  - 指标计算节点
  - 条件判断节点
  - 交易信号节点(买入/卖出，信号强度)
  - 仓位控制节点(固定/动态)
  - 止损止盈节点(百分比/均线/固定金额)

- **3.3.3 连接规则**
  - 单条件/多条件组合
  - 与/或/非逻辑运算
  - 多层嵌套(建议≤5层)
  - 自动生成逻辑说明

- **3.3.4 逻辑校验**
  - 无卖出信号检测
  - 仓位超限检测
  - 止损价异常检测
  - 错误位置高亮
  - 修改建议提示

**数据模型**:

```typescript
interface StrategyLogic {
  id: string;
  name: string;
  nodes: LogicNode[];
  connections: Connection[];
  snapshots: Snapshot[];
  validationErrors: ValidationError[];
}

interface LogicNode {
  id: string;
  type: 'indicator' | 'condition' | 'signal' | 'position' | 'stopLoss';
  position: { x: number; y: number };
  config: NodeConfig;
  locked: boolean;
}

interface Connection {
  from: string;  // node id
  to: string;
  condition?: string;
}
```

**API 设计**:

```python
POST /api/strategy/logic/create           # 创建策略逻辑
PUT  /api/strategy/logic/{id}             # 更新策略逻辑
POST /api/strategy/logic/{id}/validate    # 验证策略逻辑
POST /api/strategy/logic/{id}/snapshot    # 保存快照
GET  /api/strategy/logic/{id}/snapshots   # 获取快照列表
POST /api/strategy/logic/{id}/rollback    # 回退到快照
```

**前端技术栈**:

- 流程图编辑: ReactFlow / X6
- 拖拽: react-dnd / dnd-kit
- 节点连接: 自定义连接规则

#### 子模块 3.4: 参数优化引擎 (Parameter Optimization Engine)

**功能点**:

- **3.4.1 参数设置**
  - 参数选择(范围/步长)
  - 参数联动设置
  - 约束条件配置

- **3.4.2 优化配置**
  - 优化算法
    - 网格搜索
    - 随机搜索(迭代次数)
  - 优化目标
    - 夏普比率最大化
    - 最大回撤最小化
    - 年化收益最大化
    - 多目标权重配置
  - 约束条件
    - 最大回撤<20%
    - 胜率>50%

- **3.4.3 结果展示**
  - 参数热力图
  - 最优参数组合列表(前10组)
  - 参数敏感性曲线
  - 一键应用最优参数
  - 参数组合对比

- **3.4.4 任务管理**
  - 任务队列
  - 后台运行
  - 进度监控
  - 耗时提示

**API 设计**:

```python
POST /api/optimization/create             # 创建优化任务
GET  /api/optimization/{task_id}/status   # 获取任务状态
GET  /api/optimization/{task_id}/results  # 获取优化结果
POST /api/optimization/{task_id}/apply    # 应用最优参数
DELETE /api/optimization/{task_id}        # 取消任务
```

**技术要点**:

- 后端: Celery/RQ 任务队列
- 优化算法: scipy.optimize / optuna
- 性能: 并行计算(最多2个任务)
- WebSocket: 实时进度推送

**依赖关系**: 依赖子模块 3.3 (策略逻辑) 和模块 4 (回测引擎)

---

### 模块 4: 回测分析模块 (Backtesting & Analysis Module)

**模块职责**: 回测执行、结果分析、策略诊断

#### 子模块 4.1: 回测配置管理 (Backtest Configuration)

**功能点**:

- **4.1.1 基础参数**
  - 回测时间范围(精确到日)
  - 初始资金(10万-1000万)
  - 股票池选择
  - 排除ST股/次新股

- **4.1.2 交易成本**
  - 手续费(比例/固定)
  - 印花税(仅卖出)
  - 滑点(比例/固定/动态)
  - 分市场设置

- **4.1.3 特殊设置**
  - 涨跌停限制
  - 流动性过滤
  - 单只股票仓位上限
  - 最大持仓数量

**数据模型**:

```typescript
interface BacktestConfig {
  id: string;
  strategyId: string;
  timeRange: { start: Date; end: Date };
  initialCapital: number;
  stockPool: string[];
  tradingCosts: {
    commission: { type: 'ratio' | 'fixed'; value: number };
    stampDuty: number;
    slippage: { type: 'ratio' | 'fixed' | 'dynamic'; value: number };
  };
  constraints: {
    limitStop: boolean;
    liquidityThreshold: number;
    maxPositionRatio: number;
    maxHoldings: number;
  };
}
```

#### 子模块 4.2: 回测执行引擎 (Backtest Execution Engine)

**功能点**:

- **4.2.1 执行控制**
  - 一键启动
  - 暂停(保留进度)
  - 终止(生成部分结果)

- **4.2.2 进度监控**
  - 完成百分比
  - 当前处理日期
  - 剩余时间预估
  - 后台回测
  - 桌面通知

- **4.2.3 日志系统**
  - 实时打印交易日志
  - 日志筛选(类型/日期/标的)
  - 日志搜索(关键词)
  - 日志导出(TXT)

**API 设计**:

```python
POST   /api/backtest/start                # 启动回测
POST   /api/backtest/{id}/pause           # 暂停回测
POST   /api/backtest/{id}/terminate       # 终止回测
GET    /api/backtest/{id}/progress        # 获取进度
GET    /api/backtest/{id}/logs            # 获取日志
WS     /ws/backtest/{id}                  # WebSocket进度推送
```

**技术要点**:

- 后端: Qlib Backtest Engine集成
- 任务调度: Celery串行执行(可选2个并行)
- 状态管理: Redis缓存进度状态
- WebSocket: 实时日志/进度推送
- 性能: 进度估算算法

#### 子模块 4.3: 回测结果展示 (Backtest Results Visualization)

**功能点**:

- **4.3.1 核心指标表**
  - 15+指标(累计/年化收益、夏普、回撤等)
  - 基准对比(沪深300/上证指数)
  - 指标解读小图标

- **4.3.2 可视化图表**
  - 净值曲线(多策略叠加)
  - 回撤曲线(标记最大回撤)
  - 月度收益柱状图
  - 持仓分布饼图(行业/标的)
  - 时间段缩放
  - 数据点详情

- **4.3.3 交易明细**
  - 标的/日期/价格/数量
  - 盈亏金额/手续费
  - 持仓天数
  - 按盈亏排序
  - 标的筛选

- **4.3.4 结果导出**
  - 指标表(Excel)
  - 图表(PNG)
  - 完整报告(PDF)
  - 自定义封面/备注

**数据模型**:

```typescript
interface BacktestResult {
  id: string;
  backtestId: string;
  status: 'completed' | 'partial' | 'failed';
  metrics: {
    cumulativeReturn: number;
    annualizedReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitLossRatio: number;
    // ... 更多指标
  };
  curves: {
    equity: TimeSeriesData;
    drawdown: TimeSeriesData;
    monthlyReturns: MonthlyData[];
  };
  trades: Trade[];
  holdings: Holding[];
}

interface Trade {
  date: Date;
  symbol: string;
  action: 'buy' | 'sell';
  price: number;
  quantity: number;
  pnl: number;
  commission: number;
  holdingDays?: number;
}
```

**API 设计**:

```python
GET  /api/backtest/{id}/results           # 获取回测结果
GET  /api/backtest/{id}/metrics           # 获取指标
GET  /api/backtest/{id}/trades            # 获取交易明细
POST /api/backtest/{id}/export            # 导出结果
```

#### 子模块 4.4: 策略诊断系统 (Strategy Diagnosis)

**功能点**:

- **4.4.1 收益分析**
  - 收益来源(标的贡献TOP5)
  - 行业分布贡献
  - 收益稳定性(标准差)
  - 连续盈亏月数
  - 收益时段分布

- **4.4.2 风险分析**
  - 最大回撤时段
  - 市场环境对应
  - 波动风险(年化波动率)
  - 收益波动系数
  - 尾部风险

- **4.4.3 过拟合检测**
  - 样本外测试(20%数据)
  - 样本内/外收益差异
  - 参数敏感性分析(±10%)
  - Walk Forward检验
  - 滚动窗口回测

- **4.4.4 优化建议**
  - 具体可操作建议
  - 行业持仓优化
  - 参数范围调整
  - 风控条款添加

**API 设计**:

```python
POST /api/diagnosis/analyze               # 执行诊断分析
GET  /api/diagnosis/{id}/revenue          # 收益分析
GET  /api/diagnosis/{id}/risk             # 风险分析
GET  /api/diagnosis/{id}/overfitting      # 过拟合检测
GET  /api/diagnosis/{id}/suggestions      # 优化建议
```

**技术要点**:

- 后端: 统计分析算法实现
- 机器学习: 过拟合检测模型
- 自然语言: 建议生成模板

**依赖关系**: 依赖子模块 4.2 (回测执行) 和 4.3 (结果展示)

---

### 模块 5: 任务调度与系统管理 (Task Scheduling & System Management)

**模块职责**: 任务队列、后台任务、系统配置

#### 子模块 5.1: 任务队列管理 (Task Queue Management)

**功能点**:

- 任务创建与调度
- 串行执行(默认)
- 并行执行(最多2个)
- 任务优先级
- 任务暂停/恢复/取消
- 任务历史记录

**API 设计**:

```python
GET    /api/tasks                         # 获取任务列表
POST   /api/tasks/{id}/pause              # 暂停任务
POST   /api/tasks/{id}/resume             # 恢复任务
DELETE /api/tasks/{id}                    # 取消任务
GET    /api/tasks/history                 # 任务历史
```

**技术要点**:

- Celery + Redis/RabbitMQ
- 任务状态持久化
- 优先级队列

#### 子模块 5.2: 系统配置管理 (System Configuration)

**功能点**:

- 数据目录配置
- 实验结果路径
- 并行任务数量
- 虚拟环境配置
- 资源监控阈值

**API 设计**:

```python
GET  /api/system/config                   # 获取系统配置
PUT  /api/system/config                   # 更新配置
GET  /api/system/status                   # 系统状态
GET  /api/system/resources                # 资源占用
```

#### 子模块 5.3: 日志与监控 (Logging & Monitoring)

**功能点**:

- 系统日志收集
- 错误日志记录
- 性能监控
- 资源占用监控
- 告警通知

**技术要点**:

- 日志: structlog / loguru
- 监控: Prometheus / Grafana (可选)
- 告警: 桌面通知 / 邮件

---

### 模块 6: 代码执行安全模块 (Code Execution Security)

**模块职责**: 自定义代码执行、安全检查、虚拟环境隔离

#### 子模块 6.1: 虚拟环境管理 (Virtual Environment Management)

**功能点**:

- 独立Python虚拟环境创建
- 依赖包管理
- 环境隔离
- 环境清理

#### 子模块 6.2: 代码安全检查 (Code Security Check)

**功能点**:

- 静态代码分析
- 禁止高风险调用(os.system、subprocess)
- 导入模块白名单
- 代码复杂度检查

**技术要点**:

- AST解析: Python ast模块
- 安全检查: bandit / pylint
- 沙箱: RestrictedPython / PyPy sandboxing

#### 子模块 6.3: 代码执行引擎 (Code Execution Engine)

**功能点**:

- 代码执行
- 超时控制
- 资源限制(内存/CPU)
- 临时文件清理
- 执行结果返回

**API 设计**:

```python
POST /api/code/execute                    # 执行代码
POST /api/code/validate                   # 验证代码
GET  /api/code/whitelist                  # 获取模块白名单
```

---

### 模块 7: 用户界面与交互 (User Interface & Interaction)

**模块职责**: UI布局、交互逻辑、前端状态管理

#### 子模块 7.1: 布局系统 (Layout System)

**功能点**:

- 顶部导航栏(功能模块)
- 左侧工具栏(快捷操作)
- 中间工作区(核心功能)
- 右侧属性面板(参数配置)
- 响应式布局

**前端技术栈**:

- React/Next.js
- TypeScript
- Tailwind CSS / Ant Design / Material-UI

#### 子模块 7.2: 状态管理 (State Management)

**功能点**:

- 全局状态(用户模式、认证)
- 模块状态(数据、策略、回测)
- 本地持久化
- 状态同步

**技术方案**:

- Redux Toolkit / Zustand / Jotai
- React Query (服务端状态)
- localStorage / IndexedDB

#### 子模块 7.3: 错误处理与提示 (Error Handling & Notification)

**功能点**:

- 错误边界(Error Boundary)
- 友好错误提示
- 操作反馈(Toast/Notification)
- 二次确认对话框

**技术方案**:

- React Error Boundary
- Toast库: react-hot-toast / sonner
- Modal: 自定义对话框组件

---

## 三、模块依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│  模块 1: 用户引导与模式管理                                   │
│  (全局UI状态、帮助系统)                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │ 依赖
    ┌──────────────┴──────────────┬──────────────────────┐
    │                              │                      │
┌───▼─────┐  ┌──────────────────▼────┐  ┌──────────────▼─────┐
│ 模块 2: │  │   模块 3: 策略构建    │  │  模块 7: UI/交互   │
│ 数据管理│◄─┤   (依赖数据管理)      │  │  (全局布局/状态)   │
└───┬─────┘  └──────────┬────────────┘  └────────────────────┘
    │                   │
    │        ┌──────────▼────────────┐
    │        │   模块 4: 回测分析    │
    └───────►│ (依赖数据+策略)       │
             └──────────┬────────────┘
                        │
             ┌──────────▼────────────┐
             │ 模块 5: 任务调度      │
             │ (调度所有后台任务)    │
             └──────────┬────────────┘
                        │
             ┌──────────▼────────────┐
             │ 模块 6: 代码执行安全  │
             │ (支撑自定义代码)      │
             └───────────────────────┘
```

---

## 四、技术栈总结

### 后端技术栈

- **Web框架**: FastAPI (Python 3.9+)
- **任务队列**: Celery + Redis/RabbitMQ
- **数据处理**: Pandas, NumPy, TA-Lib
- **量化框架**: Qlib 0.8+
- **代码安全**: AST解析, RestrictedPython
- **优化算法**: scipy.optimize, optuna
- **WebSocket**: FastAPI WebSocket / Socket.IO
- **测试**: pytest, pytest-cov (覆盖率≥80%)

### 前端技术栈

- **框架**: React 18+ / Next.js 13+
- **语言**: TypeScript
- **状态管理**: Redux Toolkit / Zustand + React Query
- **UI组件**: Ant Design / Material-UI / shadcn/ui
- **样式**: Tailwind CSS / CSS Modules
- **图表**: ECharts / Recharts / TradingView Lightweight Charts
- **流程图**: ReactFlow / X6
- **拖拽**: dnd-kit / react-dnd
- **测试**: Vitest / Jest + React Testing Library

### 数据存储

- **数据库**: SQLite (本地) / PostgreSQL (可选)
- **缓存**: Redis
- **文件系统**: 本地存储(数据/结果/配置)

### 部署方案

- **运行环境**: 本地Web应用(127.0.0.1)
- **启动方式**: 一键启动脚本 / Makefile
- **容器化**: Docker (可选)
- **前端构建**: npm run build / 静态托管

---

## 五、开发优先级与里程碑

### Phase 1: MVP核心闭环 (4-6周)

**目标**: 实现数据导入→策略构建→回测分析的基本流程

**模块优先级**:

1. **高优先级**:
   - 模块 2.1: 数据导入 (Qlib数据源 + 本地文件)
   - 模块 3.1: 策略模板系统 (3-5个经典模板)
   - 模块 3.3: 策略逻辑编辑器 (基础节点 + 连接)
   - 模块 4.1 + 4.2: 回测配置 + 执行
   - 模块 4.3: 回测结果展示 (核心指标 + 基础图表)
   - 模块 7: UI/交互 (基础布局)

2. **中优先级**:
   - 模块 1.1: 模式切换
   - 模块 2.2: 数据预处理 (基础功能)
   - 模块 5.1: 任务队列 (串行执行)

3. **低优先级**:
   - 模块 1.2: 新手引导
   - 模块 6: 代码执行安全 (后续集成)

### Phase 2: 功能增强 (4-6周)

**目标**: 完善高级功能,提升用户体验

**模块优先级**:

1. **高优先级**:
   - 模块 2.3: 数据可视化 (完整功能)
   - 模块 3.2: 指标组件库 (Talib集成)
   - 模块 3.4: 参数优化引擎
   - 模块 4.4: 策略诊断系统
   - 模块 6: 代码执行安全 (自定义因子)

2. **中优先级**:
   - 模块 1.2 + 1.3: 新手引导 + 帮助系统
   - 模块 2.2: 数据预处理 (高级功能)
   - 模块 5.2 + 5.3: 系统配置 + 监控

### Phase 3: 优化与扩展 (2-4周)

**目标**: 性能优化、测试覆盖、文档完善

**工作内容**:

1. **性能优化**:
   - 大数据集处理优化
   - 回测速度优化
   - 前端渲染优化

2. **测试覆盖**:
   - 单元测试(覆盖率≥80%)
   - 集成测试
   - E2E测试

3. **文档完善**:
   - API文档
   - 用户手册
   - 开发者指南

---

## 六、接口规范示例

### REST API 命名规范

```
GET    /api/{module}/{resource}              # 获取列表
GET    /api/{module}/{resource}/{id}         # 获取详情
POST   /api/{module}/{resource}              # 创建资源
PUT    /api/{module}/{resource}/{id}         # 更新资源
DELETE /api/{module}/{resource}/{id}         # 删除资源
POST   /api/{module}/{resource}/{id}/{action} # 执行操作
```

### WebSocket 消息格式

```json
{
  "type": "progress" | "log" | "notification",
  "taskId": "uuid",
  "data": {
    "percentage": 45,
    "message": "Processing date: 2023-01-05",
    "timestamp": "2025-11-04T12:00:00Z"
  }
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "数据导入失败: 文件格式错误",
    "details": {
      "field": "file",
      "reason": "不支持的文件类型",
      "suggestion": "请确保为CSV/Excel格式"
    }
  }
}
```

---

## 七、测试策略

### 单元测试 (Unit Tests)

**覆盖目标**: 80%+

**测试范围**:

- 数据处理函数 (pandas操作)
- 指标计算逻辑
- 策略逻辑验证
- API端点单元测试

**工具**: pytest, pytest-cov

### 集成测试 (Integration Tests)

**测试场景**:

- 数据导入→预处理→可视化
- 策略构建→参数优化→回测
- 回测执行→结果分析→导出

**工具**: pytest + FastAPI TestClient

### E2E测试 (End-to-End Tests)

**测试用户流程**:

- 新手用户: 使用模板→配置参数→查看结果
- 资深用户: 自定义因子→优化参数→诊断策略

**工具**: Playwright / Cypress

### 性能测试 (Performance Tests)

**测试指标**:

- 50万+数据处理<30秒
- 5年200只股票回测<10分钟
- 并发任务稳定性

**工具**: pytest-benchmark, locust

---

## 八、风险缓解措施

### 技术风险

1. **自定义代码安全**:
   - 静态检查+白名单+虚拟环境三重防护
   - 详细的代码执行日志

2. **跨平台兼容**:
   - CI/CD多平台测试(Windows/macOS/Linux)
   - Docker容器化(可选)

### 功能风险

1. **模拟交易缺失**:
   - 在文档/UI明确说明当前版本定位
   - 提供未来路线图

2. **数据源有限**:
   - 优先保证Qlib数据源质量
   - 强化本地文件导入能力

### 性能风险

1. **大数据处理**:
   - 异步处理+进度提示
   - 分批加载+懒加载

2. **回测耗时**:
   - 后台任务+桌面通知
   - 参数优化建议

---

## 九、开发规范

### 代码规范

- **Python**: PEP 8, Black formatter, mypy类型检查
- **TypeScript**: ESLint + Prettier, strict模式
- **Git**: Conventional Commits

### TDD流程

1. 编写失败的测试
2. 实现最小功能
3. 重构代码
4. 确保测试通过

### CI/CD流程

```
提交代码 → Lint检查 → 单元测试 → 集成测试 → 构建 → 部署
```

---

## 十、总结

本文档将 Qlib-UI 系统划分为 **7大核心模块**:

1. **用户引导与模式管理**: 提供新手/专家模式和帮助系统
2. **数据管理模块**: 导入、预处理、可视化
3. **策略构建模块**: 模板、指标、逻辑编辑、参数优化
4. **回测分析模块**: 执行、结果展示、策略诊断
5. **任务调度与系统管理**: 队列、配置、监控
6. **代码执行安全模块**: 虚拟环境、安全检查
7. **用户界面与交互**: 布局、状态管理、错误处理

**开发建议**:

- 遵循MVP原则,优先完成核心闭环
- 使用TDD确保代码质量
- 保持模块低耦合、高内聚
- 预留扩展接口,支持未来功能迭代

**下一步行动**:

1. 技术选型确认
2. 数据库设计
3. API接口详细设计
4. 前端组件库选择
5. 开发环境搭建
