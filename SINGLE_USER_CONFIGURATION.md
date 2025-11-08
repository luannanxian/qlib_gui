# 个人单用户模式配置指南

**适用场景**: 个人本地使用,无需复杂的多用户认证系统

---

## 📋 概述

qlib-ui 后端已经完成了 Week 1 的重要修复工作,但这些修复是面向多用户生产环境的。对于个人单独使用的场景,我们可以大幅简化配置。

---

## 🎯 当前状态

### Week 1 完成的工作
✅ USER_ONBOARDING - 数据持久化(解决了重启丢失数据问题)
✅ CODE_SECURITY - 完整的 REST API 层
✅ 认证依赖注入框架(但使用的是 mock 认证)

### 当前认证实现
```python
# backend/app/modules/user_onboarding/api/dependencies.py
def get_current_user_id() -> str:
    """
    Temporary: Return a mock user ID until authentication is implemented.

    Returns:
        Mock user ID

    Note:
        This should be replaced with actual JWT/OAuth authentication
        that extracts the user ID from the authentication token.
    """
    return "user123"  # 固定返回单一用户ID
```

---

## ✅ 个人使用推荐配置

对于个人单独使用,**当前的 mock 认证已经完全够用**,无需额外配置!

### 为什么当前实现适合个人使用?

1. **固定用户ID**: 所有请求都使用 `"user123"` 作为用户标识
2. **数据隔离**: 虽然是单用户,但数据结构完整,支持未来扩展
3. **无需登录**: 不需要输入密码或Token,开箱即用
4. **功能完整**: 所有功能(偏好设置、代码执行等)都正常工作

---

## 🔧 可选的个性化配置

如果您想自定义用户ID或添加简单的用户识别,可以修改以下文件:

### 方案1: 自定义固定用户ID

**文件**: `backend/app/modules/user_onboarding/api/dependencies.py`

```python
def get_current_user_id() -> str:
    """个人使用 - 返回固定的用户ID"""
    return "my_personal_account"  # 改成您喜欢的名称
```

### 方案2: 从环境变量读取用户ID

**文件**: `backend/app/modules/user_onboarding/api/dependencies.py`

```python
import os

def get_current_user_id() -> str:
    """个人使用 - 从环境变量读取用户ID"""
    return os.getenv("QLIB_USER_ID", "default_user")
```

**设置环境变量**:
```bash
# 在 .env 文件中添加
QLIB_USER_ID=your_username
```

### 方案3: 从配置文件读取

**文件**: `backend/config/user.yaml` (新建)

```yaml
# 个人用户配置
user:
  id: "personal_user"
  name: "我的名字"
  email: "my@email.com"
```

**修改依赖**:
```python
import yaml

def get_current_user_id() -> str:
    """个人使用 - 从配置文件读取"""
    try:
        with open("config/user.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config.get("user", {}).get("id", "default_user")
    except:
        return "default_user"
```

---

## 🚫 不推荐的操作

### ❌ 不要完全移除认证依赖
即使是个人使用,也建议保留当前的依赖注入结构,因为:
- 提供了请求追踪(correlation ID)
- 支持审计日志
- 便于未来升级

### ❌ 不要禁用数据库持久化
Week 1 已经修复了数据丢失问题,保持数据库持久化可以:
- 防止重启后设置丢失
- 保留历史记录
- 支持数据备份

---

## 📊 当前可用的功能

所有以下功能在个人模式下都可以正常使用:

### USER_ONBOARDING 模块
- ✅ GET `/api/user/mode` - 获取用户模式(初学者/专家)
- ✅ POST `/api/user/mode` - 切换用户模式
- ✅ GET `/api/user/preferences` - 获取用户偏好设置
- ✅ PUT `/api/user/preferences` - 更新偏好设置
  - 语言设置
  - 工具提示显示
  - 已完成引导

### CODE_SECURITY 模块
- ✅ POST `/api/security/execute` - 执行Python代码
  - 超时保护(1-300秒)
  - 内存限制(64-2048MB)
  - 沙箱隔离
- ✅ GET `/api/security/health` - 健康检查
- ✅ GET `/api/security/limits` - 查看执行限制

### 其他已实现模块
- ✅ STRATEGY - 策略管理
- ✅ INDICATOR - 指标因子
- ✅ BACKTEST - 回测引擎
- ✅ DATA_MANAGEMENT - 数据管理
- ✅ TASK_SCHEDULING - 任务调度

---

## 🧪 测试个人模式

### 1. 启动后端服务
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 2. 访问 API 文档
打开浏览器访问: http://localhost:8000/docs

### 3. 测试用户偏好设置
```bash
# 获取当前模式
curl http://localhost:8000/api/user/mode

# 切换到专家模式
curl -X POST http://localhost:8000/api/user/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "expert"}'

# 获取偏好设置
curl http://localhost:8000/api/user/preferences

# 更新偏好设置
curl -X PUT http://localhost:8000/api/user/preferences \
  -H "Content-Type: application/json" \
  -d '{"language": "zh", "show_tooltips": true}'
```

### 4. 测试代码执行
```bash
# 执行简单的Python代码
curl -X POST http://localhost:8000/api/security/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import pandas as pd\nprint(pd.__version__)",
    "timeout": 30,
    "max_memory_mb": 512
  }'
```

---

## 💾 数据存储位置

所有用户数据都存储在数据库中:

### 用户偏好设置
- **表**: `user_preferences`
- **用户ID**: 固定为 `"user123"` (或您自定义的ID)
- **包含**: 模式、语言、工具提示、已完成引导等

### 数据库配置
检查 `.env` 文件中的数据库连接:
```bash
# MySQL 配置示例
DATABASE_URL=mysql+aiomysql://username:password@localhost:3306/qlib_ui
```

---

## 🔄 数据备份建议

即使是个人使用,也建议定期备份:

### 备份数据库
```bash
# MySQL备份
mysqldump -u username -p qlib_ui > backup_$(date +%Y%m%d).sql

# 恢复
mysql -u username -p qlib_ui < backup_20251108.sql
```

### 备份配置文件
```bash
# 备份环境变量
cp .env .env.backup

# 备份用户配置(如果使用了方案3)
cp config/user.yaml config/user.yaml.backup
```

---

## 📈 性能优化建议

对于个人使用,可以调整以下配置以提升性能:

### 1. 代码执行限制
**文件**: `backend/app/modules/code_security/api/security_api.py`

```python
# 个人使用可以放宽限制
DEFAULT_TIMEOUT = 60  # 从30秒增加到60秒
DEFAULT_MAX_MEMORY_MB = 1024  # 从512MB增加到1GB
MAX_TIMEOUT = 600  # 从300秒增加到10分钟
MAX_MEMORY_MB = 4096  # 从2GB增加到4GB
```

### 2. 数据库连接池
**文件**: `backend/app/database/session.py`

```python
# 个人使用可以减少连接池大小
engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=2,  # 从5降到2
    max_overflow=3,  # 从10降到3
)
```

---

## 🎓 进阶配置(可选)

### 添加简单的Web界面认证

如果未来想添加简单的密码保护,可以使用 HTTP Basic Auth:

**文件**: `backend/app/modules/common/middleware/simple_auth.py` (新建)

```python
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

PERSONAL_USERNAME = "admin"  # 您的用户名
PERSONAL_PASSWORD = "your_secure_password"  # 您的密码

def verify_credentials(credentials: HTTPBasicCredentials):
    """简单的用户名密码验证"""
    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"),
        PERSONAL_USERNAME.encode("utf8")
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        PERSONAL_PASSWORD.encode("utf8")
    )

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
```

**在API中使用**:
```python
from fastapi import Depends
from app.modules.common.middleware.simple_auth import security, verify_credentials

@router.get("/protected-endpoint")
async def protected_endpoint(
    username: str = Depends(verify_credentials)
):
    # 您的代码
    pass
```

---

## 📞 常见问题

### Q1: 为什么看到 "TODO: Replace with real authentication"?
**A**: 这是为多用户生产环境准备的注释,个人使用可以忽略。当前的 mock 认证对单用户场景完全够用。

### Q2: 需要修改前端代码吗?
**A**: 不需要。前端调用API时不需要传递认证Token,直接调用即可。

### Q3: 数据会丢失吗?
**A**: 不会。Week 1 已经修复了数据丢失问题,所有数据都持久化到数据库中。

### Q4: 可以有多个配置文件吗?
**A**: 可以。您可以创建不同的用户配置文件,在启动时选择使用哪个。

### Q5: 如何重置所有设置?
**A**: 直接删除数据库中 `user_preferences` 表的记录,或者修改用户ID。

---

## 🎯 总结

### 推荐方案(最简单)
**什么都不用改!** 当前的实现已经完全适合个人使用:
- ✅ 固定用户ID `"user123"`
- ✅ 数据库持久化
- ✅ 所有功能正常工作
- ✅ 无需登录即可使用

### 如果想个性化
只需修改一个文件中的一行代码:
```python
# backend/app/modules/user_onboarding/api/dependencies.py
def get_current_user_id() -> str:
    return "my_custom_id"  # 改成您喜欢的ID
```

### Week 1 的价值
即使是个人使用,Week 1 的修复也很有价值:
- ✅ 防止重启丢失数据
- ✅ 完整的审计日志
- ✅ 规范的代码结构
- ✅ 便于未来扩展

---

**配置完成!** 🎉

您现在可以直接使用系统,无需额外的认证配置。所有功能都已就绪!
