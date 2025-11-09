# Strategy Builder 流程图和架构图

本文档包含Strategy Builder的各种流程图和架构图,帮助理解系统设计。

---

## 1. 系统架构图

```mermaid
graph TB
    subgraph Frontend["前端层 (React)"]
        UI[可视化编辑器<br/>React Flow]
        CodePanel[代码预览面板<br/>Monaco Editor]
        TestPanel[测试结果面板<br/>Recharts]
    end

    subgraph API["API层 (FastAPI)"]
        BuilderAPI[Builder API<br/>/api/builder/*]
        StrategyAPI[Strategy API<br/>/api/strategies/*]
    end

    subgraph Services["服务层"]
        BuilderSvc[BuilderService<br/>因子集成]
        CodeGenSvc[CodeGeneratorService<br/>代码生成]
        QuickTestSvc[QuickTestService<br/>快速测试]
        InstanceSvc[InstanceService<br/>策略管理]
        ValidationSvc[ValidationService<br/>逻辑验证]
    end

    subgraph Database["数据层"]
        StrategyTemplates[(strategy_templates)]
        StrategyInstances[(strategy_instances)]
        TemplateRatings[(template_ratings)]
    end

    subgraph External["外部模块"]
        Indicator[Indicator Module<br/>因子库]
        Backtest[Backtest Module<br/>回测引擎]
        Security[Code Security<br/>代码验证]
    end

    subgraph Cache["缓存层"]
        Redis[(Redis<br/>代码缓存)]
    end

    UI --> BuilderAPI
    CodePanel --> BuilderAPI
    TestPanel --> BuilderAPI

    BuilderAPI --> BuilderSvc
    BuilderAPI --> CodeGenSvc
    BuilderAPI --> QuickTestSvc
    StrategyAPI --> InstanceSvc
    StrategyAPI --> ValidationSvc

    BuilderSvc --> Indicator
    CodeGenSvc --> Security
    CodeGenSvc --> Redis
    QuickTestSvc --> Backtest

    InstanceSvc --> StrategyInstances
    InstanceSvc --> StrategyTemplates

    style Frontend fill:#e1f5ff
    style Services fill:#fff4e1
    style External fill:#ffe1e1
    style Cache fill:#e1ffe1
```

---

## 2. 因子选择流程

```mermaid
sequenceDiagram
    actor User as 用户
    participant UI as 前端编辑器
    participant API as Builder API
    participant BuilderSvc as BuilderService
    participant IndicatorAPI as Indicator API

    User->>UI: 点击"添加指标节点"
    UI->>API: GET /api/builder/factors?category=trend
    API->>BuilderSvc: get_available_factors(category='trend')
    BuilderSvc->>IndicatorAPI: GET /api/indicators?category=trend
    IndicatorAPI-->>BuilderSvc: 返回因子列表
    BuilderSvc-->>API: 转换为FactorComponent格式
    API-->>UI: 返回因子列表
    UI-->>User: 显示因子选择器

    User->>UI: 选择"SMA(简单移动平均)"
    UI->>API: GET /api/builder/factors/{sma_id}
    API->>BuilderSvc: get_factor_details(sma_id)
    BuilderSvc->>IndicatorAPI: GET /api/indicators/{sma_id}
    IndicatorAPI-->>BuilderSvc: 返回因子详情和参数定义
    BuilderSvc-->>API: 返回FactorComponent
    API-->>UI: 返回因子详情
    UI-->>User: 显示参数配置面板<br/>(period: 20, field: close)

    User->>UI: 确认添加节点
    UI->>UI: 创建INDICATOR节点<br/>包含参数默认值
    UI-->>User: 节点添加到画布
```

---

## 3. 代码生成流程

```mermaid
sequenceDiagram
    actor User as 用户
    participant UI as 前端
    participant API as Builder API
    participant CodeGenSvc as CodeGeneratorService
    participant QlibGen as QlibGenerator
    participant SecurityAPI as Code Security API
    participant Redis as Redis缓存

    User->>UI: 点击"生成代码"
    UI->>API: POST /api/builder/strategies/{id}/generate-code
    API->>CodeGenSvc: generate_strategy_code(strategy_id)

    CodeGenSvc->>CodeGenSvc: 获取Strategy Instance
    CodeGenSvc->>CodeGenSvc: 解析Logic Flow

    alt 代码已缓存
        CodeGenSvc->>Redis: 检查缓存
        Redis-->>CodeGenSvc: 返回缓存的代码
        CodeGenSvc-->>API: 返回缓存代码
    else 需要生成新代码
        CodeGenSvc->>QlibGen: generate(logic_flow, parameters)

        loop 遍历每个节点
            QlibGen->>QlibGen: node_to_code(node)
        end

        QlibGen->>QlibGen: 组装完整代码<br/>(Jinja2模板)
        QlibGen->>QlibGen: 格式化代码(Black)
        QlibGen-->>CodeGenSvc: 返回生成的代码

        CodeGenSvc->>SecurityAPI: POST /api/security/validate-code
        SecurityAPI-->>CodeGenSvc: 返回验证结果

        alt 验证通过
            CodeGenSvc->>Redis: 缓存代码(1小时)
            CodeGenSvc-->>API: 返回GeneratedCode
            API-->>UI: 返回代码和元数据
            UI-->>User: 显示代码预览
        else 验证失败
            CodeGenSvc-->>API: 返回错误信息
            API-->>UI: 返回CodeGenerationError
            UI-->>User: 显示错误提示
        end
    end
```

---

## 4. 快速测试流程

```mermaid
sequenceDiagram
    actor User as 用户
    participant UI as 前端
    participant API as Builder API
    participant QuickTestSvc as QuickTestService
    participant CodeGenSvc as CodeGeneratorService
    participant BacktestAPI as Backtest API
    participant Celery as Celery Worker

    User->>UI: 点击"快速测试"
    UI->>API: POST /api/builder/strategies/{id}/quick-test
    API->>QuickTestSvc: submit_quick_test(strategy_id)

    QuickTestSvc->>CodeGenSvc: generate_strategy_code(strategy_id)
    CodeGenSvc-->>QuickTestSvc: 返回生成的代码

    QuickTestSvc->>BacktestAPI: POST /api/backtest/tasks<br/>{strategy_code, dates, benchmark}
    BacktestAPI->>Celery: 创建异步回测任务
    BacktestAPI-->>QuickTestSvc: 返回task_id

    QuickTestSvc-->>API: 返回QuickTestResult(task_id, status: pending)
    API-->>UI: 返回任务ID
    UI-->>User: 显示"测试中..."

    Note over UI,Celery: 异步执行回测 (2-5分钟)

    Celery->>Celery: 执行回测
    Celery->>BacktestAPI: 更新任务状态和进度

    loop 轮询状态 (每5秒)
        UI->>API: GET /api/builder/quick-tests/{task_id}
        API->>QuickTestSvc: get_test_status(task_id)
        QuickTestSvc->>BacktestAPI: GET /api/backtest/tasks/{task_id}
        BacktestAPI-->>QuickTestSvc: 返回任务状态
        QuickTestSvc-->>API: 返回QuickTestResult
        API-->>UI: 返回状态和进度
        UI-->>User: 更新进度条
    end

    Celery->>BacktestAPI: 任务完成,保存结果

    UI->>API: GET /api/builder/quick-tests/{task_id}
    API->>QuickTestSvc: get_test_status(task_id)
    QuickTestSvc->>BacktestAPI: GET /api/backtest/tasks/{task_id}
    BacktestAPI-->>QuickTestSvc: 返回完整结果
    QuickTestSvc-->>API: 返回QuickTestResult(status: completed, results)
    API-->>UI: 返回测试结果
    UI-->>User: 显示结果<br/>(收益曲线、指标、交易明细)
```

---

## 5. 策略导入/导出流程

```mermaid
sequenceDiagram
    actor User as 用户
    participant UI as 前端
    participant API as Builder API
    participant InstanceSvc as InstanceService
    participant DB as Database

    rect rgb(200, 220, 240)
        Note over User,DB: 导出流程
        User->>UI: 点击"导出策略"
        UI->>API: GET /api/builder/strategies/{id}/export?format=json
        API->>InstanceSvc: get(strategy_id)
        InstanceSvc->>DB: 查询策略实例
        DB-->>InstanceSvc: 返回策略数据
        InstanceSvc-->>API: 返回Strategy Instance
        API->>API: 构建StrategyExport对象<br/>(策略+元数据+模板信息)
        API-->>UI: 返回JSON文件
        UI-->>User: 下载strategy_{name}.json
    end

    rect rgb(220, 240, 200)
        Note over User,DB: 导入流程
        User->>UI: 上传JSON文件
        UI->>API: POST /api/builder/strategies/import<br/>{data, name}
        API->>API: 验证JSON格式
        API->>API: 检查版本兼容性

        alt 验证通过
            API->>InstanceSvc: create(strategy_data, user_id)
            InstanceSvc->>DB: 插入新策略实例
            DB-->>InstanceSvc: 返回创建的策略
            InstanceSvc-->>API: 返回Strategy Instance
            API-->>UI: 返回策略ID和详情
            UI-->>User: 显示"导入成功"<br/>跳转到策略编辑页
        else 验证失败
            API-->>UI: 返回错误信息
            UI-->>User: 显示错误提示
        end
    end
```

---

## 6. 数据流向图

```mermaid
graph LR
    subgraph Input["输入数据"]
        UserInput[用户操作]
        FactorLib[因子库]
        HistData[历史数据]
    end

    subgraph Processing["处理流程"]
        VisualEdit[可视化编辑<br/>Logic Flow]
        CodeGen[代码生成<br/>Python Code]
        Validate[验证<br/>语法+安全]
        Backtest[回测执行<br/>性能评估]
    end

    subgraph Output["输出结果"]
        StrategyCode[策略代码]
        TestResults[测试结果]
        Performance[性能指标]
    end

    UserInput --> VisualEdit
    FactorLib --> VisualEdit

    VisualEdit --> CodeGen
    CodeGen --> Validate

    Validate -->|通过| Backtest
    Validate -->|失败| UserInput

    HistData --> Backtest

    CodeGen --> StrategyCode
    Backtest --> TestResults
    TestResults --> Performance

    Performance -.反馈.-> UserInput

    style Input fill:#e1f5ff
    style Processing fill:#fff4e1
    style Output fill:#e1ffe1
```

---

## 7. 节点转代码映射

```mermaid
graph TD
    subgraph LogicFlow["Logic Flow (JSON)"]
        Node1[INDICATOR Node<br/>indicator: SMA<br/>parameters: period=20]
        Node2[CONDITION Node<br/>condition: close > sma_20]
        Node3[SIGNAL Node<br/>signal_type: BUY]
        Node4[POSITION Node<br/>position_value: 50%]
    end

    subgraph Converter["NodeConverter"]
        Conv1[indicator_to_code]
        Conv2[condition_to_code]
        Conv3[signal_to_code]
        Conv4[position_to_code]
    end

    subgraph Code["Generated Code"]
        Code1["data['sma'] = <br/>data['close'].rolling(20).mean()"]
        Code2["condition = <br/>data['close'] > data['sma']"]
        Code3["signals = <br/>np.where(condition, 1, 0)"]
        Code4["positions = <br/>signals * 0.5"]
    end

    Node1 --> Conv1 --> Code1
    Node2 --> Conv2 --> Code2
    Node3 --> Conv3 --> Code3
    Node4 --> Conv4 --> Code4

    Code1 --> Template[Jinja2 Template]
    Code2 --> Template
    Code3 --> Template
    Code4 --> Template

    Template --> Final[Complete Strategy Class]

    style LogicFlow fill:#e1f5ff
    style Converter fill:#fff4e1
    style Code fill:#e1ffe1
```

---

## 8. 缓存策略

```mermaid
graph TD
    Request[代码生成请求] --> CheckCache{检查缓存}

    CheckCache -->|缓存命中| ReturnCached[返回缓存代码]
    CheckCache -->|缓存未命中| Generate[生成新代码]

    Generate --> Validate[验证代码]
    Validate -->|验证通过| SaveCache[保存到Redis<br/>TTL: 1小时]
    Validate -->|验证失败| ReturnError[返回错误]

    SaveCache --> ReturnNew[返回新代码]

    ReturnCached --> End[响应客户端]
    ReturnNew --> End
    ReturnError --> End

    style CheckCache fill:#fff4e1
    style SaveCache fill:#e1ffe1
    style ReturnError fill:#ffe1e1
```

---

## 9. 错误处理流程

```mermaid
graph TD
    Start[开始处理] --> Step1{步骤1: 获取策略}

    Step1 -->|成功| Step2{步骤2: 生成代码}
    Step1 -->|失败| Error1[404 策略不存在]

    Step2 -->|成功| Step3{步骤3: 语法验证}
    Step2 -->|失败| Error2[500 生成失败]

    Step3 -->|成功| Step4{步骤4: 安全验证}
    Step3 -->|失败| Error3[422 语法错误]

    Step4 -->|成功| Success[返回代码]
    Step4 -->|失败| Error4[422 安全风险]

    Error1 --> Response[错误响应]
    Error2 --> Response
    Error3 --> Response
    Error4 --> Response
    Success --> Response

    Response --> End[结束]

    style Success fill:#e1ffe1
    style Error1 fill:#ffe1e1
    style Error2 fill:#ffe1e1
    style Error3 fill:#ffe1e1
    style Error4 fill:#ffe1e1
```

---

## 10. 部署架构

```mermaid
graph TB
    subgraph Client["客户端"]
        Browser[浏览器]
    end

    subgraph LoadBalancer["负载均衡"]
        Nginx[Nginx]
    end

    subgraph AppServers["应用服务器"]
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
    end

    subgraph Workers["后台任务"]
        Celery1[Celery Worker 1]
        Celery2[Celery Worker 2]
    end

    subgraph Cache["缓存层"]
        Redis[(Redis)]
    end

    subgraph Database["数据库"]
        MySQL[(MySQL Primary)]
        MySQLReplica[(MySQL Replica)]
    end

    subgraph Queue["消息队列"]
        RabbitMQ[RabbitMQ]
    end

    Browser --> Nginx
    Nginx --> API1
    Nginx --> API2

    API1 --> Redis
    API2 --> Redis

    API1 --> MySQL
    API2 --> MySQLReplica

    API1 --> RabbitMQ
    API2 --> RabbitMQ

    RabbitMQ --> Celery1
    RabbitMQ --> Celery2

    Celery1 --> MySQL
    Celery2 --> MySQL

    style Client fill:#e1f5ff
    style AppServers fill:#fff4e1
    style Workers fill:#ffe1e1
    style Database fill:#e1ffe1
```

---

## 使用说明

### 如何查看这些图表

1. **在GitHub上查看**: GitHub原生支持Mermaid语法,直接显示图表
2. **在本地编辑器**: 使用支持Mermaid的Markdown编辑器 (VS Code + Mermaid插件)
3. **在线工具**: https://mermaid.live/ 复制代码查看

### 图表类型说明

- **graph TB/LR**: 流程图 (TB=从上到下, LR=从左到右)
- **sequenceDiagram**: 时序图 (显示交互顺序)
- **classDiagram**: 类图 (显示类结构)

### 自定义样式

在Mermaid图表中可以使用以下样式:
```mermaid
style NodeName fill:#color
```

颜色方案:
- 蓝色 (#e1f5ff): 前端/输入
- 黄色 (#fff4e1): 处理/服务
- 绿色 (#e1ffe1): 输出/成功
- 红色 (#ffe1e1): 错误/警告
