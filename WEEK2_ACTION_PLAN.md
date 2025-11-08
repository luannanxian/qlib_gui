# Week 2 高优先级任务行动计划

**日期**: 2025-11-08
**Sprint**: Week 2 后端模块改进
**环境**: Anaconda qlib 虚拟环境

---

## 📋 Week 1 成果回顾

✅ **已完成**:
- USER_ONBOARDING 数据持久化修复 (40% → 90% 生产就绪)
- CODE_SECURITY 完整 REST API 层创建 (60% → 95% 生产就绪)
- 单用户配置指南编写

🔴 **遗留问题**:
- DATA_MANAGEMENT 测试覆盖率低 (dataset_api: 18%, preprocessing_api: 17%)
- 数据库表结构问题导致测试失败
- BACKTEST WebSocket 测试覆盖率 28%
- STRATEGY_BUILDER 模块完全缺失

---

## 🎯 Week 2 优先级任务

### 优先级 1: 修复 DATA_MANAGEMENT 模块 (高优先级)

#### 任务 1.1: 解决数据库表结构问题

**问题诊断**:
```bash
# 错误信息
sqlite3.OperationalError: no such table: datasets
```

**原因分析**:
1. 测试使用 SQLite,但迁移可能只针对 MySQL
2. Alembic 迁移未正确应用到测试数据库
3. 测试 fixture 未创建必要的表

**解决方案**:

**步骤 1: 检查当前迁移状态**
```bash
# 激活 qlib 虚拟环境
conda activate qlib

# 检查迁移文件
cd /Users/zhenkunliu/project/qlib-ui/backend
ls -la alembic/versions/

# 检查当前版本
alembic current

# 查看迁移历史
alembic history
```

**步骤 2: 创建缺失的数据库表**

需要创建的表:
- `datasets` - 数据集元信息
- `preprocessing_tasks` - 预处理任务
- `import_tasks` - 导入任务
- 其他 DATA_MANAGEMENT 相关表

**步骤 3: 修复测试 fixture**

文件: `backend/tests/modules/data_management/api/conftest.py`

确保测试前创建所有必要的表:
```python
@pytest.fixture(scope="function")
async def setup_database(test_db_session):
    """在每个测试前创建表结构"""
    from app.database.models import Base

    async with test_db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

**步骤 4: 创建新的迁移(如果需要)**
```bash
# 生成新的迁移文件
alembic revision --autogenerate -m "add_datasets_tables"

# 检查生成的迁移文件
cat alembic/versions/<newest_file>.py

# 应用迁移
alembic upgrade head
```

**验证步骤**:
```bash
# 运行 DATA_MANAGEMENT 测试
pytest tests/modules/data_management/api/test_dataset_api.py -v

# 检查测试覆盖率
pytest tests/modules/data_management/api/ --cov=app/modules/data_management/api --cov-report=html
```

---

#### 任务 1.2: 提升 dataset_api 测试覆盖率 (18% → 70%+)

**当前状态**:
- 测试文件: `backend/tests/modules/data_management/api/test_dataset_api.py`
- 覆盖率: 18%
- 未覆盖: 140 行代码

**需要添加的测试**:

1. **成功场景测试**:
   - ✅ 创建数据集
   - ✅ 获取数据集
   - ✅ 更新数据集
   - ✅ 删除数据集
   - ✅ 列出数据集(带分页)
   - ✅ 搜索数据集

2. **错误场景测试**:
   - ❌ 创建重复数据集
   - ❌ 获取不存在的数据集
   - ❌ 更新不存在的数据集
   - ❌ 删除不存在的数据集
   - ❌ 无效的参数验证
   - ❌ 数据库错误处理

3. **边界条件测试**:
   - ❌ 空列表返回
   - ❌ 大量数据分页
   - ❌ 特殊字符处理
   - ❌ 并发操作

**实施步骤**:
```bash
# 1. 运行现有测试查看失败情况
pytest tests/modules/data_management/api/test_dataset_api.py -v --tb=short

# 2. 修复数据库问题后,添加缺失的测试用例

# 3. 验证覆盖率提升
pytest tests/modules/data_management/api/test_dataset_api.py --cov=app/modules/data_management/api/dataset_api --cov-report=term-missing
```

---

#### 任务 1.3: 提升 preprocessing_api 测试覆盖率 (17% → 70%+)

**当前状态**:
- 测试文件: 需要创建 `backend/tests/modules/data_management/api/test_preprocessing_api.py`
- 覆盖率: 17%
- 未覆盖: 219 行代码

**需要创建的测试类**:

```python
class TestPreprocessingAPI:
    """预处理 API 测试"""

    async def test_create_preprocessing_task(self):
        """测试创建预处理任务"""
        pass

    async def test_list_preprocessing_tasks(self):
        """测试列出预处理任务"""
        pass

    async def test_get_preprocessing_task(self):
        """测试获取单个任务"""
        pass

    async def test_start_preprocessing(self):
        """测试启动预处理"""
        pass

    async def test_preprocessing_with_invalid_config(self):
        """测试无效配置"""
        pass

    async def test_preprocessing_error_handling(self):
        """测试错误处理"""
        pass
```

---

#### 任务 1.4: 提升 preprocessing_service 测试覆盖率 (7% → 80%+)

**当前状态**:
- 服务层几乎未测试
- 核心业务逻辑未验证

**需要创建**: `backend/tests/modules/data_management/services/test_preprocessing_service.py`

**关键测试场景**:
1. 数据清洗逻辑
2. 数据转换逻辑
3. 错误处理
4. 边界条件

---

### 优先级 2: 提升 BACKTEST WebSocket 测试覆盖率 (中优先级)

**当前状态**:
- 文件: `backend/app/modules/backtest/services/websocket_service.py`
- 覆盖率: 28%
- 目标: 80%+

**需要测试的功能**:
1. WebSocket 连接建立
2. 消息发送和接收
3. 进度更新推送
4. 错误处理
5. 连接断开和重连
6. 多客户端并发

**实施步骤**:
```bash
# 1. 检查现有测试
cat backend/tests/test_backtest/services/test_websocket_service.py

# 2. 添加 WebSocket 测试用例(使用 pytest-asyncio 和 websockets 库)

# 3. 验证覆盖率
pytest tests/test_backtest/services/test_websocket_service.py --cov=app/modules/backtest/services/websocket_service --cov-report=html
```

**WebSocket 测试模板**:
```python
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

@pytest.mark.asyncio
async def test_websocket_connection():
    """测试 WebSocket 连接"""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/backtest") as websocket:
            # 发送消息
            websocket.send_json({"task_id": "test-123"})

            # 接收响应
            data = websocket.receive_json()
            assert data["status"] == "connected"
```

---

### 优先级 3: STRATEGY_BUILDER 需求分析 (准备阶段)

**当前状态**:
- 设计文档: 存在
- 实现代码: 0%
- 优先级: 关键

**Week 2 任务**: 完成详细需求分析和技术设计

**步骤 1: 阅读现有设计文档**
```bash
# 查找设计文档
find /Users/zhenkunliu/project/qlib-ui -name "*strategy*builder*" -o -name "*builder*"

# 如果有文档,阅读并总结
```

**步骤 2: 定义功能范围**

核心功能:
1. 可视化策略构建器
2. 拖拽式组件组合
3. 策略模板管理
4. 代码生成
5. 策略验证

**步骤 3: 技术栈选择**

后端:
- FastAPI 端点
- 策略 DSL 设计
- 代码生成引擎

前端:
- React Flow 或类似的图形库
- 拖拽界面
- 实时预览

**步骤 4: 数据库设计**

需要的表:
- `strategy_builder_templates` - 构建器模板
- `strategy_builder_components` - 可用组件
- `strategy_builder_projects` - 用户项目
- `strategy_builder_versions` - 版本历史

**交付物**:
- 详细需求文档
- 技术架构设计
- 数据库 Schema
- API 接口设计
- 时间估算 (预计 2-3 周开发)

---

## 📅 时间计划

### Week 2 第 1-2 天 (周一-周二)
- ✅ 诊断并修复数据库表结构问题
- ✅ 运行所有 DATA_MANAGEMENT 测试
- 🔄 开始添加 dataset_api 测试用例

### Week 2 第 3-4 天 (周三-周四)
- 🔄 完成 dataset_api 测试覆盖率提升
- 🔄 完成 preprocessing_api 测试覆盖率提升
- 🔄 完成 preprocessing_service 测试覆盖率提升

### Week 2 第 5 天 (周五)
- 🔄 提升 BACKTEST WebSocket 测试覆盖率
- 📝 完成 STRATEGY_BUILDER 需求分析文档

---

## 🛠️ 开发环境设置

### 激活虚拟环境
```bash
# 激活 qlib 环境
conda activate qlib

# 验证环境
which python
python --version
```

### 安装必要的测试依赖
```bash
# 安装测试相关包
pip install pytest pytest-asyncio pytest-cov pytest-mock

# 安装 WebSocket 测试依赖
pip install websockets

# 安装数据库测试依赖
pip install aiosqlite  # 用于测试的 SQLite 异步驱动
```

### 运行测试的常用命令
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/modules/data_management/

# 运行并生成覆盖率报告
pytest --cov=app/modules/data_management --cov-report=html

# 运行特定测试文件
pytest tests/modules/data_management/api/test_dataset_api.py -v

# 运行并显示详细输出
pytest tests/modules/data_management/api/ -v --tb=short

# 仅运行失败的测试
pytest --lf

# 运行特定标记的测试
pytest -m "not slow"
```

---

## 📊 成功标准

### DATA_MANAGEMENT 模块
- ✅ 所有测试通过 (当前 12/37 失败 → 37/37 通过)
- ✅ dataset_api 覆盖率: 18% → 70%+
- ✅ preprocessing_api 覆盖率: 17% → 70%+
- ✅ preprocessing_service 覆盖率: 7% → 80%+
- ✅ 数据库表问题解决

### BACKTEST 模块
- ✅ WebSocket 服务测试覆盖率: 28% → 80%+
- ✅ 所有连接场景测试通过
- ✅ 错误处理验证

### STRATEGY_BUILDER 模块
- ✅ 需求分析文档完成
- ✅ 技术架构设计完成
- ✅ 数据库 Schema 设计完成
- ✅ API 接口设计完成
- ✅ 开发时间估算完成

---

## 🔍 问题诊断清单

### DATA_MANAGEMENT 测试失败诊断

**问题 1: 数据库表不存在**
- [ ] 检查 Alembic 迁移文件是否包含 datasets 表
- [ ] 检查测试 fixture 是否创建了必要的表
- [ ] 检查 SQLite vs MySQL 兼容性问题

**问题 2: 测试 fixture 配置**
- [ ] 检查 conftest.py 中的 database fixture
- [ ] 验证 Base.metadata.create_all() 是否执行
- [ ] 检查测试数据库连接字符串

**问题 3: Model 定义**
- [ ] 检查 Dataset model 是否正确定义
- [ ] 检查是否继承 BaseDBModel
- [ ] 检查字段类型和约束

---

## 📝 相关文件清单

### 需要修改的文件
- `backend/tests/modules/data_management/api/conftest.py` - 测试配置
- `backend/tests/modules/data_management/api/test_dataset_api.py` - 数据集 API 测试
- `backend/tests/modules/data_management/api/test_preprocessing_api.py` - 预处理 API 测试 (新建)
- `backend/tests/modules/data_management/services/test_preprocessing_service.py` - 预处理服务测试 (新建)
- `backend/tests/test_backtest/services/test_websocket_service.py` - WebSocket 测试
- `backend/alembic/versions/*.py` - 可能需要新的迁移

### 需要参考的文件
- `backend/app/modules/data_management/api/dataset_api.py` - 数据集 API 实现
- `backend/app/modules/data_management/api/preprocessing_api.py` - 预处理 API 实现
- `backend/app/modules/data_management/services/preprocessing_service.py` - 预处理服务
- `backend/app/modules/backtest/services/websocket_service.py` - WebSocket 服务
- `backend/app/database/models/*.py` - 数据库模型

---

## 🎯 下一步行动

### 立即执行 (今天)
1. 激活 qlib 虚拟环境
2. 运行 DATA_MANAGEMENT 测试查看完整错误信息
3. 诊断数据库表缺失的根本原因
4. 修复测试 fixture 或创建缺失的迁移

### 本周执行
1. 完成 DATA_MANAGEMENT 所有测试修复
2. 提升测试覆盖率到目标值
3. 完成 BACKTEST WebSocket 测试
4. 编写 STRATEGY_BUILDER 需求文档

### 下周准备
1. 开始 STRATEGY_BUILDER 实现
2. 考虑其他模块的优化
3. 准备集成测试

---

**文档创建时间**: 2025-11-08
**预计完成时间**: 2025-11-15 (Week 2 结束)
**责任人**: Backend Development Team
**状态**: 📋 **计划中** - 等待执行
