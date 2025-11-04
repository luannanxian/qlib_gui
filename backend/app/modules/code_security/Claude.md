# 模块 6: 代码执行安全模块 (Code Execution Security)

## 模块概述

本模块负责用户自定义代码的安全执行,提供虚拟环境隔离、代码安全检查和受控执行环境。

## 核心职责

1. **虚拟环境管理**: 创建和管理独立Python虚拟环境
2. **代码安全检查**: 静态代码分析,识别危险操作
3. **代码执行引擎**: 在沙箱环境中安全执行代码
4. **资源限制**: 限制代码执行的内存、CPU、时间

## 子模块结构

```
code_security/
├── venv/                # 虚拟环境管理子模块
│   ├── venv_manager.py      # 虚拟环境管理器
│   ├── venv_creator.py      # 虚拟环境创建
│   ├── dependency_manager.py# 依赖管理
│   └── venv_cleaner.py      # 环境清理
├── security/            # 安全检查子模块
│   ├── code_analyzer.py     # 代码分析器
│   ├── ast_checker.py       # AST检查
│   ├── import_validator.py  # 导入验证
│   ├── whitelist.py         # 模块白名单
│   └── blacklist.py         # 危险操作黑名单
├── sandbox/             # 沙箱执行子模块
│   ├── executor.py          # 代码执行器
│   ├── resource_limiter.py  # 资源限制器
│   ├── timeout_handler.py   # 超时处理
│   └── output_capturer.py   # 输出捕获
├── templates/           # 代码模板
│   ├── factor_template.py   # 因子模板
│   ├── indicator_template.py# 指标模板
│   └── examples/            # 示例代码
├── models/              # 数据模型
│   ├── execution.py
│   └── validation.py
├── services/            # 业务逻辑服务
│   ├── security_service.py
│   └── execution_service.py
├── api/                 # API端点
│   ├── security_api.py
│   └── execution_api.py
├── schemas/             # Pydantic schemas
│   └── security_schemas.py
└── Claude.md            # 本文档
```

## API 端点

### 代码验证 API
```
POST /api/code/validate                   # 验证代码安全性
POST /api/code/analyze                    # 分析代码复杂度
GET  /api/code/whitelist                  # 获取模块白名单
GET  /api/code/templates                  # 获取代码模板
GET  /api/code/examples                   # 获取示例代码
```

### 代码执行 API
```
POST /api/code/execute                    # 执行代码
POST /api/code/execute/async              # 异步执行代码
GET  /api/code/execution/{id}             # 获取执行结果
POST /api/code/execution/{id}/cancel      # 取消执行
```

### 虚拟环境 API
```
GET  /api/venv/list                       # 列出虚拟环境
POST /api/venv/create                     # 创建虚拟环境
DELETE /api/venv/{id}                     # 删除虚拟环境
GET  /api/venv/{id}/packages              # 获取已安装包
POST /api/venv/{id}/install               # 安装依赖包
```

## 数据模型

### CodeValidationResult
```python
class ValidationStatus(str, Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"

class SecurityIssue(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    line: int
    column: int
    code: str
    message: str
    suggestion: Optional[str]

class CodeValidationResult(BaseModel):
    status: ValidationStatus
    is_safe: bool
    issues: List[SecurityIssue]
    complexity: ComplexityMetrics
    imports: List[str]
    dangerous_calls: List[str]
    warnings: List[str]

class ComplexityMetrics(BaseModel):
    lines_of_code: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    nesting_depth: int
```

### CodeExecution
```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class CodeExecution(BaseModel):
    id: str
    code: str
    language: str = "python"
    venv_id: Optional[str]

    # 执行配置
    timeout: int = 30  # 秒
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0

    # 执行状态
    status: ExecutionStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[float]

    # 执行结果
    stdout: Optional[str]
    stderr: Optional[str]
    return_value: Optional[Any]
    exception: Optional[str]

    # 资源使用
    memory_used_mb: Optional[float]
    cpu_time_seconds: Optional[float]

    created_at: datetime
```

### VirtualEnvironment
```python
class VenvStatus(str, Enum):
    CREATING = "creating"
    READY = "ready"
    CORRUPTED = "corrupted"
    DELETED = "deleted"

class VirtualEnvironment(BaseModel):
    id: str
    name: str
    path: str
    python_version: str
    status: VenvStatus

    # 已安装包
    packages: List[Package]

    # 使用统计
    last_used_at: Optional[datetime]
    usage_count: int = 0

    # 元数据
    created_at: datetime
    updated_at: datetime
    size_mb: float

class Package(BaseModel):
    name: str
    version: str
    installed_at: datetime
```

## 安全机制

### 1. 静态代码分析
```python
# 使用AST分析检测危险操作
DANGEROUS_MODULES = [
    "os", "sys", "subprocess", "shutil", "socket",
    "urllib", "requests", "__import__", "eval", "exec"
]

DANGEROUS_FUNCTIONS = [
    "eval", "exec", "compile", "__import__",
    "open", "file", "input", "raw_input"
]

# 检测危险调用
def check_dangerous_calls(ast_tree):
    # 检测 os.system, subprocess.call 等
    # 检测文件系统访问
    # 检测网络请求
    # 检测动态代码执行
    pass
```

### 2. 导入模块白名单
```python
# 允许导入的模块
ALLOWED_MODULES = [
    # 数据处理
    "numpy", "pandas", "scipy",

    # Qlib相关
    "qlib", "qlib.data", "qlib.contrib",

    # 技术指标
    "talib",

    # 数学和统计
    "math", "statistics", "random",

    # 日期时间
    "datetime", "time",

    # 数据结构
    "collections", "itertools",

    # 类型提示
    "typing",
]
```

### 3. RestrictedPython 沙箱
```python
from RestrictedPython import compile_restricted, safe_globals

def execute_restricted_code(code: str):
    # 编译受限代码
    byte_code = compile_restricted(
        code,
        filename='<user_code>',
        mode='exec'
    )

    # 提供安全的全局命名空间
    safe_namespace = {
        '__builtins__': safe_globals,
        'numpy': numpy,
        'pandas': pandas,
        # ... 其他允许的模块
    }

    # 执行代码
    exec(byte_code, safe_namespace)
```

### 4. 资源限制
```python
import resource
import signal

def set_resource_limits(max_memory_mb=512, max_cpu_seconds=30):
    # 限制内存
    memory_limit = max_memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

    # 限制CPU时间
    resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, max_cpu_seconds))

    # 设置超时信号
    signal.alarm(max_cpu_seconds)
```

### 5. 文件系统隔离
```python
# 限制文件访问
ALLOWED_PATHS = [
    "/tmp/qlib-ui/sandbox/",
    "/data/qlib-ui/",
]

def check_file_access(path: str):
    abs_path = os.path.abspath(path)
    for allowed in ALLOWED_PATHS:
        if abs_path.startswith(allowed):
            return True
    raise PermissionError(f"Access denied: {path}")
```

## 技术要点

### 虚拟环境管理
- **venv模块**: 创建独立Python环境
- **pip管理**: 安装指定版本依赖
- **环境缓存**: 缓存常用环境配置
- **自动清理**: 清理长期未使用环境

### 代码安全检查
- **AST分析**: Python ast模块解析代码
- **bandit**: 安全漏洞检测
- **pylint**: 代码质量检查
- **复杂度分析**: radon计算代码复杂度

### 沙箱执行
- **RestrictedPython**: 限制Python功能
- **resource模块**: 限制系统资源
- **multiprocessing**: 进程隔离执行
- **超时控制**: signal.alarm超时终止

### 输出捕获
- **stdout/stderr重定向**: sys.stdout/stderr
- **日志收集**: 捕获print输出
- **异常捕获**: try-except捕获所有异常
- **返回值序列化**: JSON序列化返回值

## 依赖关系

- **依赖**:
  - 模块5(任务调度) - 异步执行任务
- **被依赖**:
  - 模块3(策略构建) - 自定义因子执行

## 开发优先级

- **Phase 1 (低优先级)**:
  - 基础代码验证
  - 简单沙箱执行

- **Phase 2 (高优先级)**:
  - 完整安全检查
  - 虚拟环境管理
  - 资源限制机制
  - 自定义因子支持

## 测试要点

### 单元测试
- AST分析准确性
- 危险代码检测
- 白名单/黑名单验证
- 资源限制有效性

### 安全测试
- 尝试突破沙箱
- 文件系统访问限制
- 网络访问限制
- 资源耗尽攻击

### 性能测试
- 代码验证速度
- 沙箱执行开销
- 并发执行能力

## 注意事项

1. **安全第一**: 宁可误杀不可放过危险代码
2. **用户友好**: 提供清晰的错误提示和示例
3. **性能平衡**: 安全检查不应过度影响性能
4. **白名单维护**: 及时更新允许的模块列表
5. **环境隔离**: 确保用户代码之间完全隔离
6. **日志审计**: 记录所有代码执行日志

## 代码模板示例

### 自定义因子模板
```python
from qlib.data.dataset.handler import DataHandlerLP
from qlib.contrib.data.handler import Alpha158

class MyCustomFactor(DataHandlerLP):
    def __init__(self, instruments="csi300", start_time=None, end_time=None):
        # 初始化
        pass

    def calculate(self, data):
        # 计算因子值
        # 只能使用 numpy, pandas, talib
        import pandas as pd
        import numpy as np

        # 示例: 计算5日均线与20日均线的差值
        ma5 = data['close'].rolling(5).mean()
        ma20 = data['close'].rolling(20).mean()
        factor = (ma5 - ma20) / ma20

        return factor
```

### 自定义指标模板
```python
def my_indicator(data, period=14):
    """
    自定义技术指标

    参数:
        data: DataFrame, 包含 'close', 'high', 'low', 'volume' 列
        period: int, 计算周期

    返回:
        Series, 指标值
    """
    import pandas as pd
    import numpy as np

    # 计算逻辑
    result = data['close'].rolling(period).mean()

    return result
```
