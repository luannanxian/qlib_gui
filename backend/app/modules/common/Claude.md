# 公共模块 (Common Module)

## 模块概述

本模块提供跨模块的公共功能、工具类、基础模型和中间件,是所有业务模块的基础设施。

## 核心职责

1. **基础模型**: 所有模块共享的数据模型
2. **工具函数**: 通用工具类和辅助函数
3. **中间件**: 认证、权限、日志、错误处理中间件
4. **异常定义**: 统一的异常类型定义
5. **常量定义**: 系统级常量和枚举

## 子模块结构

```
common/
├── models/              # 基础数据模型
│   ├── base.py          # 基础模型类
│   ├── user.py          # 用户模型
│   └── pagination.py    # 分页模型
├── middleware/          # 中间件
│   ├── auth.py          # 认证中间件
│   ├── cors.py          # CORS中间件
│   ├── logging.py       # 日志中间件
│   ├── error_handler.py # 错误处理中间件
│   └── rate_limit.py    # 限流中间件
├── exceptions/          # 异常定义
│   ├── base.py          # 基础异常
│   ├── http.py          # HTTP异常
│   └── business.py      # 业务异常
├── utils/               # 工具函数
│   ├── datetime_utils.py    # 日期时间工具
│   ├── file_utils.py        # 文件操作工具
│   ├── hash_utils.py        # 哈希工具
│   ├── json_utils.py        # JSON工具
│   ├── pagination_utils.py  # 分页工具
│   └── validation_utils.py  # 验证工具
├── constants/           # 常量定义
│   ├── api.py           # API相关常量
│   ├── system.py        # 系统常量
│   └── error_codes.py   # 错误码
├── dependencies/        # FastAPI依赖
│   ├── auth.py          # 认证依赖
│   ├── database.py      # 数据库依赖
│   └── cache.py         # 缓存依赖
├── schemas/             # 通用Schemas
│   ├── response.py      # 响应模式
│   └── request.py       # 请求模式
└── Claude.md            # 本文档
```

## 核心组件

### 1. 基础模型 (Base Models)

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class BaseDBModel(TimestampMixin):
    """数据库基础模型"""
    id: str
    is_deleted: bool = False

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size

class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
```

### 2. 统一响应格式

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    details: Optional[dict] = None

# 使用示例
def success_response(data: T) -> APIResponse[T]:
    return APIResponse(success=True, data=data)

def error_response(code: str, message: str, details: dict = None) -> APIResponse:
    return APIResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details)
    )
```

### 3. 异常定义

```python
class QlibUIException(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ValidationError(QlibUIException):
    """验证错误"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundException(QlibUIException):
    """资源未找到"""
    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} with id {resource_id} not found"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "id": resource_id})

class PermissionDeniedException(QlibUIException):
    """权限拒绝"""
    def __init__(self, action: str, resource: str):
        message = f"Permission denied for action '{action}' on '{resource}'"
        super().__init__(message, "PERMISSION_DENIED", {"action": action, "resource": resource})

class DataImportException(QlibUIException):
    """数据导入异常"""
    pass

class BacktestException(QlibUIException):
    """回测异常"""
    pass

class CodeExecutionException(QlibUIException):
    """代码执行异常"""
    pass
```

### 4. 中间件

#### 认证中间件
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过公开路径
        if request.url.path in ["/api/health", "/api/docs"]:
            return await call_next(request)

        # 验证token
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Missing authentication token")

        # 验证逻辑...

        response = await call_next(request)
        return response
```

#### 日志中间件
```python
import time
from loguru import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        # 记录响应
        duration = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"Duration: {duration:.3f}s"
        )

        return response
```

#### 错误处理中间件
```python
from fastapi import Request
from fastapi.responses import JSONResponse

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except QlibUIException as e:
        return JSONResponse(
            status_code=400,
            content=error_response(e.code, e.message, e.details).dict()
        )
    except Exception as e:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content=error_response("INTERNAL_ERROR", str(e)).dict()
        )
```

### 5. 工具函数

#### 日期时间工具
```python
from datetime import datetime, date, timedelta
from typing import Optional

def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> date:
    """解析日期字符串"""
    return datetime.strptime(date_str, fmt).date()

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    return dt.strftime(fmt)

def get_date_range(start: date, end: date) -> list[date]:
    """获取日期范围"""
    delta = end - start
    return [start + timedelta(days=i) for i in range(delta.days + 1)]

def is_trading_day(date: date) -> bool:
    """判断是否交易日"""
    # 实现交易日判断逻辑
    pass
```

#### 文件工具
```python
import os
import shutil
from pathlib import Path

def ensure_dir(path: str) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_size_mb(file_path: str) -> float:
    """获取文件大小(MB)"""
    return os.path.getsize(file_path) / (1024 * 1024)

def clean_temp_files(directory: str, older_than_days: int = 7):
    """清理临时文件"""
    cutoff = datetime.now() - timedelta(days=older_than_days)
    for file in Path(directory).glob("*"):
        if file.stat().st_mtime < cutoff.timestamp():
            file.unlink()
```

### 6. 常量定义

```python
# API相关常量
class APIConstants:
    API_PREFIX = "/api"
    API_VERSION = "v1"
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE_SIZE = 20

# 系统常量
class SystemConstants:
    DEFAULT_TIMEZONE = "Asia/Shanghai"
    MAX_UPLOAD_SIZE_MB = 100
    TASK_TIMEOUT_SECONDS = 3600

# 错误码
class ErrorCode:
    # 通用错误
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # 数据相关
    DATA_IMPORT_FAILED = "DATA_IMPORT_FAILED"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"

    # 策略相关
    STRATEGY_NOT_FOUND = "STRATEGY_NOT_FOUND"
    STRATEGY_VALIDATION_FAILED = "STRATEGY_VALIDATION_FAILED"

    # 回测相关
    BACKTEST_FAILED = "BACKTEST_FAILED"
    BACKTEST_TIMEOUT = "BACKTEST_TIMEOUT"

    # 代码执行
    CODE_EXECUTION_FAILED = "CODE_EXECUTION_FAILED"
    CODE_SECURITY_VIOLATION = "CODE_SECURITY_VIOLATION"
```

### 7. FastAPI 依赖

```python
from fastapi import Depends
from sqlalchemy.orm import Session

# 数据库依赖
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis缓存依赖
def get_cache():
    return redis_client

# 当前用户依赖
def get_current_user(token: str = Depends(oauth2_scheme)):
    # 解析token获取用户
    return user
```

## 技术要点

### 日志配置
```python
from loguru import logger

logger.add(
    "logs/qlib-ui_{time}.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)
```

### 配置管理
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str

    # Redis配置
    REDIS_URL: str

    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Qlib配置
    QLIB_DATA_DIR: str

    class Config:
        env_file = ".env"

settings = Settings()
```

## 使用示例

### 1. 使用统一响应
```python
from fastapi import APIRouter
from common.schemas.response import APIResponse, success_response, error_response

router = APIRouter()

@router.get("/data/datasets", response_model=APIResponse[list[Dataset]])
async def get_datasets():
    try:
        datasets = await dataset_service.get_all()
        return success_response(datasets)
    except Exception as e:
        return error_response("DATA_FETCH_FAILED", str(e))
```

### 2. 使用分页
```python
@router.get("/data/datasets", response_model=APIResponse[PaginatedResponse])
async def get_datasets(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    items = db.query(Dataset).offset(pagination.offset).limit(pagination.limit).all()
    total = db.query(Dataset).count()

    return success_response(PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=(total + pagination.page_size - 1) // pagination.page_size
    ))
```

### 3. 使用异常
```python
from common.exceptions import NotFoundException, ValidationError

def get_dataset_by_id(dataset_id: str):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise NotFoundException("Dataset", dataset_id)
    return dataset

def validate_dataset(data: dict):
    if not data.get("name"):
        raise ValidationError("Dataset name is required", {"field": "name"})
```

## 测试要点

- 中间件功能测试
- 工具函数单元测试
- 异常处理流程测试
- 日志格式验证

## 注意事项

1. 保持模块纯净,避免业务逻辑
2. 工具函数需要充分的单元测试
3. 常量定义清晰,避免魔法数字
4. 异常定义明确,便于问题排查
5. 响应格式统一,便于前端处理
