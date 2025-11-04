# 模块 5: 任务调度与系统管理 (Task Scheduling & System Management)

## 模块概述

本模块是系统的任务调度和管理中心，负责异步任务队列、系统配置管理、日志监控和资源管理。

## 核心职责

1. **任务队列管理**: 创建、调度、执行、监控各类后台任务
2. **系统配置管理**: 数据目录、并行任务、虚拟环境配置
3. **日志与监控**: 系统日志收集、性能监控、资源占用监控
4. **告警通知**: 异常告警、任务完成通知

## 子模块结构

```
task_scheduling/
├── queue/               # 任务队列子模块
│   ├── task_manager.py      # 任务管理器
│   ├── scheduler.py         # 任务调度器
│   ├── executor.py          # 任务执行器
│   └── priority_queue.py    # 优先级队列
├── config/              # 系统配置子模块
│   ├── config_manager.py    # 配置管理器
│   ├── settings.py          # 系统设置
│   └── validator.py         # 配置验证
├── monitoring/          # 监控子模块
│   ├── log_collector.py     # 日志收集器
│   ├── metrics_collector.py # 指标收集器
│   ├── resource_monitor.py  # 资源监控器
│   └── alert_manager.py     # 告警管理器
├── celery_app/          # Celery应用
│   ├── celery_config.py     # Celery配置
│   ├── tasks.py             # 任务定义
│   └── beat_schedule.py     # 定时任务
├── models/              # 数据模型
│   ├── task.py
│   ├── config.py
│   └── log.py
├── services/            # 业务逻辑服务
│   ├── task_service.py
│   ├── config_service.py
│   └── monitoring_service.py
├── api/                 # API端点
│   ├── task_api.py
│   ├── config_api.py
│   └── monitoring_api.py
├── schemas/             # Pydantic schemas
│   └── task_schemas.py
└── Claude.md            # 本文档
```

## API 端点

### 任务队列 API
```
GET    /api/tasks                         # 获取任务列表
GET    /api/tasks/{id}                    # 获取任务详情
POST   /api/tasks                         # 创建任务
POST   /api/tasks/{id}/pause              # 暂停任务
POST   /api/tasks/{id}/resume             # 恢复任务
POST   /api/tasks/{id}/cancel             # 取消任务
DELETE /api/tasks/{id}                    # 删除任务
GET    /api/tasks/history                 # 任务历史记录
GET    /api/tasks/statistics              # 任务统计
```

### 系统配置 API
```
GET  /api/system/config                   # 获取系统配置
PUT  /api/system/config                   # 更新系统配置
POST /api/system/config/validate          # 验证配置
GET  /api/system/status                   # 系统状态
GET  /api/system/resources                # 资源占用情况
GET  /api/system/health                   # 健康检查
```

### 监控日志 API
```
GET  /api/logs                            # 获取日志列表
GET  /api/logs/{id}                       # 获取日志详情
POST /api/logs/search                     # 搜索日志
GET  /api/metrics                         # 获取系统指标
GET  /api/metrics/realtime                # 实时指标
GET  /api/alerts                          # 获取告警列表
POST /api/alerts/{id}/acknowledge         # 确认告警
```

## 数据模型

### Task
```python
class TaskType(str, Enum):
    BACKTEST = "backtest"
    OPTIMIZATION = "optimization"
    DATA_IMPORT = "data_import"
    DATA_PREPROCESSING = "data_preprocessing"
    FACTOR_BACKTEST = "factor_backtest"
    CUSTOM_CODE = "custom_code"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class Task(BaseModel):
    id: str
    type: TaskType
    name: str
    status: TaskStatus
    priority: TaskPriority = TaskPriority.NORMAL

    # 任务参数
    params: Dict[str, Any]

    # 进度信息
    progress: float = 0.0  # 0-100
    current_step: Optional[str]
    eta: Optional[int]  # 预计剩余秒数

    # 结果
    result: Optional[Dict[str, Any]]
    error: Optional[str]

    # 元数据
    created_by: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: datetime
```

### SystemConfig
```python
class SystemConfig(BaseModel):
    # 数据目录配置
    data_dir: str = "./data"
    result_dir: str = "./results"
    log_dir: str = "./logs"
    cache_dir: str = "./cache"

    # 任务调度配置
    max_parallel_tasks: int = 2
    task_timeout: int = 3600  # 秒
    enable_task_queue: bool = True

    # 虚拟环境配置
    venv_dir: str = "./venvs"
    python_path: Optional[str]

    # 资源限制
    max_memory_mb: int = 8192
    max_cpu_percent: float = 80.0

    # 日志配置
    log_level: str = "INFO"
    log_rotation: str = "10MB"
    log_retention: str = "30 days"

    # 缓存配置
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    updated_at: datetime
```

### SystemMetrics
```python
class SystemMetrics(BaseModel):
    timestamp: datetime

    # CPU指标
    cpu_percent: float
    cpu_count: int

    # 内存指标
    memory_total: int
    memory_used: int
    memory_percent: float

    # 磁盘指标
    disk_total: int
    disk_used: int
    disk_percent: float

    # 任务指标
    active_tasks: int
    pending_tasks: int
    completed_tasks_today: int
    failed_tasks_today: int

    # Redis指标
    redis_connected: bool
    redis_memory_used: Optional[int]
```

### Alert
```python
class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(str, Enum):
    RESOURCE = "resource"
    TASK_FAILURE = "task_failure"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE = "performance"

class Alert(BaseModel):
    id: str
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    details: Optional[Dict[str, Any]]
    acknowledged: bool = False
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime
```

## 技术要点

### 任务调度
- **Celery**: 分布式任务队列
- **Redis/RabbitMQ**: 消息代理
- **优先级队列**: 支持任务优先级
- **任务持久化**: PostgreSQL/SQLite存储任务状态
- **断点续传**: 支持任务暂停和恢复

### 系统配置
- **配置管理**: pydantic-settings管理配置
- **环境变量**: 支持环境变量覆盖
- **配置验证**: 启动时验证配置合法性
- **热更新**: 部分配置支持热更新

### 日志监控
- **结构化日志**: structlog/loguru
- **日志轮转**: 按大小/时间轮转
- **日志聚合**: 集中收集各模块日志
- **实时监控**: WebSocket推送实时指标

### 资源监控
- **psutil**: 监控CPU、内存、磁盘
- **阈值告警**: 超过阈值触发告警
- **历史趋势**: 记录资源使用趋势
- **自动清理**: 磁盘空间不足时自动清理

## 依赖关系

- **依赖**:
  - Redis(任务队列、缓存)
  - PostgreSQL/SQLite(任务持久化)
- **被依赖**:
  - 所有其他模块(调度后台任务)

## 开发优先级

- **Phase 1 (中优先级)**:
  - 基础任务队列(串行执行)
  - 系统配置管理
  - 简单日志记录

- **Phase 2 (中优先级)**:
  - 完整监控系统
  - 告警通知功能
  - 并行任务调度
  - 资源限制和清理

## 测试要点

### 单元测试
- 任务调度逻辑
- 优先级队列
- 配置验证
- 告警规则

### 集成测试
- 任务创建到完成流程
- 暂停/恢复机制
- 告警触发和通知

### 性能测试
- 并发任务处理能力
- 资源占用监控准确性
- 日志写入性能

### 压力测试
- 大量并发任务
- 长时间运行稳定性
- 资源耗尽场景

## 注意事项

1. **资源隔离**: 不同类型任务资源隔离
2. **任务清理**: 定期清理历史任务记录
3. **错误恢复**: 任务失败自动重试机制
4. **告警降噪**: 避免告警风暴
5. **权限控制**: 敏感配置需要权限验证
6. **性能影响**: 监控本身不应影响系统性能
