# 模块 1: 用户引导与模式管理 (User Onboarding & Mode Management)

## 模块概述

本模块负责提供新手/专家模式切换功能和用户引导流程，是系统的全局UI状态管理中心。

## 核心职责

1. **模式管理**: 新手模式和专家模式的状态管理与切换
2. **用户引导**: 提供3步快速上手教程和引导式操作流程
3. **帮助系统**: 功能说明、操作示例、常见问题解答
4. **用户偏好**: 持久化用户设置和偏好

## 子模块结构

```
user_onboarding/
├── models/              # 数据模型
│   ├── user_mode.py     # 用户模式模型
│   └── preferences.py   # 用户偏好模型
├── services/            # 业务逻辑
│   ├── mode_service.py  # 模式切换服务
│   └── guide_service.py # 引导流程服务
├── api/                 # API端点
│   ├── mode_api.py      # 模式管理API
│   └── help_api.py      # 帮助系统API
├── schemas/             # Pydantic schemas
│   └── mode_schemas.py  # 请求/响应模式
└── Claude.md            # 本文档
```

## API 端点

### 模式管理
- `GET /api/user/mode` - 获取当前用户模式
- `POST /api/user/mode` - 切换用户模式
- `GET /api/user/preferences` - 获取用户偏好设置
- `PUT /api/user/preferences` - 更新用户偏好设置

### 引导系统
- `GET /api/guide/steps` - 获取引导步骤
- `POST /api/guide/progress` - 更新引导进度
- `GET /api/guide/status` - 获取引导完成状态

### 帮助系统
- `GET /api/help/topics` - 获取帮助主题列表
- `GET /api/help/topics/{topic_id}` - 获取特定帮助内容
- `GET /api/help/faq` - 获取常见问题解答

## 数据模型

### UserMode
```python
class UserMode(str, Enum):
    BEGINNER = "beginner"  # 新手模式
    EXPERT = "expert"      # 专家模式

class UserPreferences(BaseModel):
    user_id: str
    mode: UserMode
    completed_guides: List[str]
    show_tooltips: bool = True
    language: str = "zh-CN"
    created_at: datetime
    updated_at: datetime
```

## 技术要点

- **状态管理**: 使用Redis缓存用户模式和偏好
- **持久化**: SQLite/PostgreSQL存储用户设置
- **验证**: Pydantic进行请求/响应验证
- **日志**: 记录模式切换和引导完成事件

## 依赖关系

- **被依赖**: 被所有其他模块依赖，提供全局用户状态
- **依赖**: 无外部模块依赖

## 开发优先级

- **Phase 1 (中优先级)**: 基础模式切换功能
- **Phase 2 (中优先级)**: 完整引导系统和帮助文档

## 测试要点

- 模式切换逻辑正确性
- 用户偏好持久化
- 引导进度追踪
- API端点集成测试
- 并发用户场景测试

## 注意事项

1. 确保模式切换不影响用户当前工作流
2. 引导流程应该可跳过且可重复
3. 帮助内容需要支持多语言
4. 用户偏好应该跨设备同步(未来扩展)
