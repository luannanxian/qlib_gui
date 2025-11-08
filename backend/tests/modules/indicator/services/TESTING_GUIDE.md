# CustomFactorService 测试执行指南

## 快速开始

### 环境配置

确保已安装必需的依赖：
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock sqlalchemy
```

### 数据库配置

设置测试数据库环境变量（.env.test）：
```bash
# MySQL配置（推荐）
DATABASE_URL_TEST=mysql+aiomysql://remote:remote123456@192.168.3.46:3306/qlib_ui_test?charset=utf8mb4

# 或 SQLite（快速本地测试）
DATABASE_URL_TEST=sqlite+aiosqlite:///:memory:
```

## 测试执行

### 1. 运行所有测试
```bash
cd /Users/zhenkunliu/project/qlib-ui

# 运行所有CustomFactorService测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -v

# 带覆盖率报告
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  -v \
  --cov=app.modules.indicator.services.custom_factor_service \
  --cov-report=html \
  --cov-report=term-missing
```

### 2. 运行特定测试类
```bash
# 只运行创建因子的测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py::TestCustomFactorServiceCreate -v

# 只运行更新因子的测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py::TestCustomFactorServiceUpdate -v

# 只运行授权和安全测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py::TestCustomFactorServiceAuthorizationAndSecurity -v
```

### 3. 运行特定测试方法
```bash
# 运行特定的单个测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py::TestCustomFactorServiceCreate::test_create_factor_with_valid_data -v

# 运行包含特定关键字的所有测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -k "authorization" -v
```

### 4. 调试模式
```bash
# 显示print输出
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -v -s

# 在第一个失败处停止
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -x

# 显示最慢的10个测试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -v --durations=10

# 进入pdb调试
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -v --pdb
```

## 测试结构详解

### 测试类与方法映射

```
test_custom_factor_service.py
├── TestCustomFactorServiceCreate (7个测试)
│   ├── test_create_factor_with_valid_data
│   ├── test_create_factor_with_minimal_data
│   ├── test_create_factor_missing_required_fields
│   ├── test_create_factor_invalid_formula_language
│   ├── test_create_factor_user_id_override_prevention
│   ├── test_create_factor_with_all_languages
│   └── ... (创建相关的所有测试)
│
├── TestCustomFactorServiceUpdate (10个测试)
│   ├── test_update_factor_by_owner
│   ├── test_update_factor_formula
│   ├── test_update_factor_formula_language
│   └── ... (更新相关的所有测试)
│
├── TestCustomFactorServiceGetDetail (2个测试)
│   ├── test_get_factor_detail_existing
│   └── test_get_factor_detail_nonexistent
│
├── TestCustomFactorServicePublish (6个测试)
│   ├── test_publish_factor_by_owner
│   └── ... (发布相关的所有测试)
│
├── TestCustomFactorServiceMakePublic (5个测试)
│   └── ... (公开化相关的所有测试)
│
├── TestCustomFactorServiceClone (9个测试)
│   ├── test_clone_public_factor
│   ├── test_clone_non_public_factor
│   └── ... (克隆相关的所有测试)
│
├── TestCustomFactorServiceDelete (7个测试)
│   ├── test_delete_factor_by_owner
│   ├── test_delete_factor_hard_delete
│   └── ... (删除相关的所有测试)
│
└── ... (共16个测试类，79个测试方法)
```

### Fixture使用说明

从conftest.py继承的重要fixture：

```python
# 数据库session
db_session: AsyncSession  # 测试数据库会话

# 仓库fixtures
custom_factor_repo: CustomFactorRepository

# 服务fixture
custom_factor_service: CustomFactorService  # 主要使用

# 测试数据fixtures
sample_indicator: IndicatorComponent
sample_custom_factor: CustomFactor  # 私有因子
sample_public_factor: CustomFactor  # 公开因子
```

## 常见测试场景

### 测试场景1: 创建因子工作流
```python
# 使用示例
async def test_create_factor():
    # 1. ARRANGE - 准备测试数据
    factor_data = {
        "factor_name": "我的因子",
        "formula": "close",
        "formula_language": "qlib_alpha"
    }
    user_id = "user123"

    # 2. ACT - 执行被测试代码
    result = await custom_factor_service.create_factor(factor_data, user_id)

    # 3. ASSERT - 验证结果
    assert result["factor"]["factor_name"] == "我的因子"
    assert result["factor"]["user_id"] == user_id
```

### 测试场景2: 授权检查
```python
# 用户只能修改自己的因子
async def test_authorization():
    # 用户A的因子
    factor = CustomFactor(
        factor_name="A的因子",
        user_id="user_a",
        formula="close",
        formula_language="qlib_alpha"
    )

    # 用户B尝试修改（应该失败）
    with pytest.raises(AuthorizationError):
        await custom_factor_service.update_factor(
            factor.id,
            {"factor_name": "修改"},
            "user_b"
        )
```

### 测试场景3: 数据验证
```python
# 验证必填字段
async def test_validation():
    # 缺少必填字段
    with pytest.raises(ValidationError) as exc:
        await custom_factor_service.create_factor(
            {"factor_name": "测试"},  # 缺少formula和formula_language
            "user123"
        )

    assert "Missing required fields" in str(exc.value)
```

### 测试场景4: 异常处理
```python
# 使用Mock测试异常处理
async def test_exception_handling():
    from unittest.mock import patch

    with patch.object(
        custom_factor_service.custom_factor_repo,
        'create',
        side_effect=Exception("Database error")
    ):
        with pytest.raises(Exception) as exc:
            await custom_factor_service.create_factor(
                {"factor_name": "test", "formula": "close", "formula_language": "qlib_alpha"},
                "user123"
            )
        assert "Database error" in str(exc.value)
```

## 测试覆盖情况查看

### 生成HTML覆盖率报告
```bash
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  --cov=app.modules.indicator.services.custom_factor_service \
  --cov-report=html

# 打开报告
open htmlcov/index.html
```

### 查看命令行覆盖率
```bash
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  --cov=app.modules.indicator.services.custom_factor_service \
  --cov-report=term-missing
```

## 日志和调试

### 启用SQL日志
```bash
export TEST_DB_ECHO_SQL=true
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py -v
```

### 查看测试执行时间
```bash
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  -v \
  --durations=0
```

### 显示详细的assertion差异
```bash
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  -v \
  -vv
```

## CI/CD集成

### GitHub Actions示例
```yaml
name: Test CustomFactorService

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: password
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt

      - name: Run tests with coverage
        env:
          DATABASE_URL_TEST: mysql+aiomysql://root:password@localhost/qlib_ui_test
        run: |
          pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
            --cov=app.modules.indicator.services.custom_factor_service \
            --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 常见问题解决

### 问题1: 数据库连接错误
```
错误: ERROR: Can't connect to MySQL server on '192.168.3.46'
解决: 检查DATABASE_URL_TEST环境变量和数据库服务
```

### 问题2: 异步事件循环错误
```
错误: RuntimeError: Event loop is closed
解决: 确保使用pytest-asyncio和@pytest.mark.asyncio
```

### 问题3: 测试数据未清理
```
错误: IntegrityError: Duplicate entry
解决: 测试应该使用独立的db_session，每次测试自动清理
```

### 问题4: Mock不生效
```
错误: Mock对象没有被调用
解决: 确保Mock的位置正确 - patch在被测试方法调用的位置
```

## 最佳实践

### 1. 测试命名规范
```python
# 好的命名
def test_create_factor_with_valid_data()
def test_update_factor_by_non_owner()
def test_delete_factor_raises_authorization_error()

# 避免的命名
def test_create()  # 太宽泛
def test_func()    # 不清楚
def test_bug123()  # 不描述性
```

### 2. AAA模式
```python
async def test_something():
    # ARRANGE - 准备
    data = {"key": "value"}

    # ACT - 执行
    result = await service.method(data)

    # ASSERT - 验证
    assert result is not None
```

### 3. 一个测试一个概念
```python
# 好的 - 一个概念
async def test_create_factor_with_valid_data():
    result = await service.create_factor(...)
    assert result["factor"]["id"] is not None

# 避免 - 多个概念
async def test_create_and_update_and_delete():
    # 测试太复杂了
    pass
```

### 4. 适当使用Fixture
```python
# 使用Fixture避免重复
@pytest.fixture
async def sample_factor(db_session):
    factor = CustomFactor(...)
    db_session.add(factor)
    await db_session.commit()
    return factor

# 在测试中使用
async def test_something(sample_factor):
    result = await service.get_factor_detail(sample_factor.id)
    assert result is not None
```

## 性能指标

### 目标性能
- 单个测试: < 100ms
- 整个测试套件: < 30s
- 覆盖率生成: < 60s

### 监控性能
```bash
pytest backend/tests/modules/indicator/services/test_custom_factor_service.py \
  --durations=10 \
  -v
```

## 维护与更新

### 添加新测试的步骤
1. 在合适的测试类中添加新的test_* 方法
2. 遵循AAA模式
3. 使用有意义的名称
4. 添加docstring说明测试意图
5. 运行测试验证
6. 更新本文档（如需要）

### 修改现有测试
1. 确保修改不破坏其他测试
2. 运行完整测试套件
3. 检查覆盖率
4. 更新文档（如需要）

## 联系与支持

如有测试相关问题，请：
1. 检查TEST_COVERAGE_REPORT.md的详细说明
2. 查看代码中的docstring
3. 运行测试的verbose模式了解详情
4. 查看conftest.py了解可用的fixture
