# InstanceService 测试快速启动指南

## 项目概况

本项目为 `instance_service.py` 创建了一个完整的测试套件，包含：
- **52个测试用例** 覆盖所有7个公开方法
- **100% 方法覆盖率** 的测试
- **AAA 模式** 所有测试都遵循 Arrange-Act-Assert 模式
- **预期代码覆盖率 80%+**

## 文件结构

```
backend/
├── app/modules/strategy/services/
│   └── instance_service.py (426行)          # 被测试的源文件
├── tests/test_strategy/
│   ├── test_instance_service.py (1250行)    # 完整的测试套件
│   └── conftest.py                          # pytest 配置
├── TEST_COVERAGE_REPORT.md                  # 详细覆盖率报告
├── TEST_CASES_CHECKLIST.md                  # 完整的测试用例清单
└── TESTING_QUICKSTART.md                    # 本文件
```

## 快速开始

### 1. 环境设置

#### 方式 A: 使用 .env 文件
```bash
# 复制 .env 示例文件
cp backend/.env.example backend/.env

# 编辑 .env，设置以下变量
DATABASE_URL=mysql+aiomysql://username:password@host:3306/qlib_ui_test?charset=utf8mb4
SECRET_KEY=<生成安全的密钥>
```

#### 方式 B: 使用环境变量（推荐用于CI/CD）
```bash
# 生成安全的 SECRET_KEY
python -c 'import secrets; print(secrets.token_urlsafe(64))'
# 输出示例: 38G2jvAK18ogDxgCAuW4KGAdIjXI24fmu7hbY5t0yl6gMKKjsPS1ampd0Z6pQC3cDcgd5wSbe4hsYqyXidftoA

# 设置环境变量
export DATABASE_URL="mysql+aiomysql://remote:remote123456@192.168.3.46:3306/qlib_ui_test?charset=utf8mb4"
export SECRET_KEY="38G2jvAK18ogDxgCAuW4KGAdIjXI24fmu7hbY5t0yl6gMKKjsPS1ampd0Z6pQC3cDcgd5wSbe4hsYqyXidftoA"
```

### 2. 运行测试

#### 基础命令
```bash
# 进入backend目录
cd backend

# 运行所有测试（详细输出）
pytest tests/test_strategy/test_instance_service.py -v

# 快速测试（只显示摘要）
pytest tests/test_strategy/test_instance_service.py
```

#### 运行特定测试
```bash
# 运行特定的测试类
pytest tests/test_strategy/test_instance_service.py::TestCreateFromTemplate -v

# 运行特定的单个测试
pytest tests/test_strategy/test_instance_service.py::TestCreateFromTemplate::test_create_with_default_parameters -v

# 运行所有包含"snapshot"的测试
pytest tests/test_strategy/test_instance_service.py -k snapshot -v
```

### 3. 生成覆盖率报告

```bash
# 生成终端报告
pytest tests/test_strategy/test_instance_service.py --cov=app.modules.strategy.services.instance_service --cov-report=term-missing

# 生成 HTML 报告
pytest tests/test_strategy/test_instance_service.py --cov=app.modules.strategy.services.instance_service --cov-report=html

# 打开 HTML 报告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
# 或
start htmlcov/index.html  # Windows
```

### 4. 调试和分析

```bash
# 显示测试的输出（print语句）
pytest tests/test_strategy/test_instance_service.py -v -s

# 在第一个失败处停止
pytest tests/test_strategy/test_instance_service.py -x

# 显示最详细的错误信息
pytest tests/test_strategy/test_instance_service.py -vv --tb=long

# 显示最慢的10个测试
pytest tests/test_strategy/test_instance_service.py --durations=10

# 显示覆盖率缺失的行
pytest tests/test_strategy/test_instance_service.py --cov=app.modules.strategy.services.instance_service --cov-report=term-missing
```

## 测试套件概览

### 测试统计
- **总测试数**: 52个
- **测试类数**: 7个
- **覆盖方法**: 7个

### 测试类分布
| 类名 | 测试数 | 覆盖方法 |
|-----|------|--------|
| TestCreateFromTemplate | 12 | create_from_template() |
| TestCreateCustom | 6 | create_custom() |
| TestDuplicateStrategy | 8 | duplicate_strategy() |
| TestSaveSnapshot | 7 | save_snapshot() |
| TestRestoreSnapshot | 8 | restore_snapshot() |
| TestGetVersions | 7 | get_versions() |
| TestIntegrationScenarios | 4 | 集成场景 |

### 覆盖的功能场景
✓ 参数处理（默认、自定义、合并）
✓ 模板使用计数
✓ 策略复制和克隆
✓ 快照创建和版本管理
✓ 快照恢复
✓ 版本历史查询
✓ 用户隔离和权限检查
✓ 错误处理和异常

## 测试执行流程

### 典型测试执行
```
1. pytest 启动
   ├── 加载 conftest.py
   ├── 初始化 database fixtures
   └── 创建 AsyncSession

2. 运行每个测试
   ├── Arrange: 准备测试数据
   ├── Act: 执行被测试方法
   └── Assert: 验证结果

3. 清理
   ├── 事务回滚
   ├── 关闭数据库连接
   └── 生成报告
```

## 常见问题和解决方案

### 问题 1: "Table already exists"
**原因**: 数据库表创建冲突
**解决方案**:
```bash
# 清空测试数据库
mysql -u remote -p remote123456 -h 192.168.3.46 -e "DROP DATABASE IF EXISTS qlib_ui_test; CREATE DATABASE qlib_ui_test;"

# 重新运行测试
pytest tests/test_strategy/test_instance_service.py -v
```

### 问题 2: "Connection refused"
**原因**: 数据库连接失败
**解决方案**:
```bash
# 检查数据库连接
mysql -u remote -p -h 192.168.3.46 -e "SELECT 1"

# 验证环境变量
echo $DATABASE_URL

# 确保 DATABASE_URL 格式正确
# 应该类似: mysql+aiomysql://user:pass@host:3306/db?charset=utf8mb4
```

### 问题 3: "SECRET_KEY too weak"
**原因**: SECRET_KEY 不够安全
**解决方案**:
```bash
# 生成新的安全密钥
python -c 'import secrets; print(secrets.token_urlsafe(64))'

# 设置生成的密钥
export SECRET_KEY="<生成的密钥>"
```

### 问题 4: 测试超时
**原因**: 数据库查询缓慢
**解决方案**:
```bash
# 增加超时时间（修改 pytest.ini）
# 添加: timeout = 600

# 或运行时指定
pytest tests/test_strategy/test_instance_service.py --timeout=600
```

## 性能建议

### 运行时间预期
- 单个测试: ~50-100ms
- 全部 52 个测试: ~30-60秒
- 包含覆盖率报告: ~60-120秒

### 优化建议
```bash
# 使用多进程并行执行（需要 pytest-xdist）
pytest tests/test_strategy/test_instance_service.py -n auto

# 只运行失败的测试
pytest tests/test_strategy/test_instance_service.py --lf

# 首先运行可能失败的测试
pytest tests/test_strategy/test_instance_service.py --ff
```

## 测试质量指标

### 目标值
- **代码覆盖率**: >= 80% ✓
- **方法覆盖率**: 100% ✓
- **测试通过率**: 100% ✓
- **平均测试时间**: < 100ms ✓

### 验证质量
```bash
# 生成详细的覆盖率报告
pytest tests/test_strategy/test_instance_service.py \
  --cov=app.modules.strategy.services.instance_service \
  --cov-report=term-missing \
  --cov-report=html

# 查看 htmlcov/index.html 获得可视化的覆盖率
```

## CI/CD 集成

### GitHub Actions 示例
```yaml
name: Test Instance Service

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: qlib_ui_test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
        ports:
          - 3306:3306

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt

      - name: Run tests
        env:
          DATABASE_URL: mysql+aiomysql://root:root@localhost:3306/qlib_ui_test
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
        run: |
          cd backend
          pytest tests/test_strategy/test_instance_service.py -v --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./backend/coverage.xml
```

## 测试维护和更新

### 添加新测试
1. 在相应的 TestXxx 类中添加方法
2. 遵循 AAA 模式
3. 使用清晰的测试名称
4. 添加文档字符串

### 更新现有测试
1. 确保向后兼容
2. 更新相关文档
3. 验证覆盖率未下降
4. 运行完整的测试套件

### 检查清单
- [ ] 所有测试通过
- [ ] 覆盖率 >= 80%
- [ ] 没有 TODO 或 SKIP
- [ ] 代码风格符合项目规范
- [ ] 文档已更新

## 相关文件和文档

| 文件 | 描述 |
|-----|------|
| `test_instance_service.py` | 完整的测试套件（1250行） |
| `TEST_COVERAGE_REPORT.md` | 详细的覆盖率分析报告 |
| `TEST_CASES_CHECKLIST.md` | 52个测试用例的完整清单 |
| `TESTING_QUICKSTART.md` | 本快速启动指南 |
| `instance_service.py` | 被测试的源文件（426行） |

## 源代码结构

```
instance_service.py
├── InstanceService 类
│   ├── __init__(db: AsyncSession)
│   ├── create_from_template()        [12个测试]
│   ├── create_custom()               [6个测试]
│   ├── duplicate_strategy()          [8个测试]
│   ├── save_snapshot()               [7个测试]
│   ├── restore_snapshot()            [8个测试]
│   └── get_versions()                [7个测试]
└── 集成场景                           [4个测试]
```

## 下一步

1. **运行测试**
   ```bash
   cd backend
   pytest tests/test_strategy/test_instance_service.py -v
   ```

2. **查看覆盖率**
   ```bash
   pytest tests/test_strategy/test_instance_service.py --cov --cov-report=html
   open htmlcov/index.html
   ```

3. **阅读文档**
   - 详细覆盖率: `TEST_COVERAGE_REPORT.md`
   - 测试清单: `TEST_CASES_CHECKLIST.md`

4. **自定义配置**
   - 修改 `pytest.ini` 调整配置
   - 修改 `.env` 设置环境
   - 修改 `conftest.py` 调整 fixtures

## 支持和帮助

### 常见命令速查

| 需求 | 命令 |
|-----|-----|
| 运行全部测试 | `pytest tests/test_strategy/test_instance_service.py -v` |
| 运行特定测试 | `pytest tests/test_strategy/test_instance_service.py::TestCreateFromTemplate -v` |
| 显示覆盖率 | `pytest tests/test_strategy/test_instance_service.py --cov` |
| 生成覆盖率报告 | `pytest tests/test_strategy/test_instance_service.py --cov-report=html` |
| 调试模式 | `pytest tests/test_strategy/test_instance_service.py -v -s` |
| 快速失败 | `pytest tests/test_strategy/test_instance_service.py -x` |

---

**快速开始完成！现在您可以运行测试套件了。** ✓

有任何问题，请参考相关文档或查看源代码注释。
