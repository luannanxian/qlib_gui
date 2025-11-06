# MySQL测试环境迁移 - 验证清单

## 📋 文件清单

### ✅ 已创建的文件

```
backend/
├── .env.test                                      # 测试环境配置
├── docker-compose.test.yml                        # MySQL测试容器配置
├── docker/
│   └── mysql/
│       └── test-init.sql                         # MySQL初始化脚本
├── tests/
│   └── modules/
│       └── indicator/
│           └── repositories/
│               └── conftest.py                    # 更新：支持SQLite/MySQL
├── scripts/
│   ├── setup_mysql_test.sh                       # 一键设置脚本
│   └── check_mysql_compatibility.py              # 兼容性检查工具
└── docs/
    ├── MYSQL_TEST_SETUP.md                       # 详细设置指南
    ├── MYSQL_COMPATIBILITY_REPORT.md             # 兼容性分析报告
    └── MIGRATION_SUMMARY.md                      # 迁移方案总结
```

---

## ✅ 配置验证清单

### 1. 环境配置检查

- [x] `.env.test` 已创建并包含正确的数据库URL
- [x] Docker Compose配置使用独立端口（3307）
- [x] MySQL初始化脚本配置utf8mb4字符集
- [x] conftest.py正确导入所有模型

### 2. Docker环境检查

```bash
# 检查Docker是否运行
docker info

# 检查Docker Compose配置
docker-compose -f backend/docker-compose.test.yml config

# 预期：无语法错误
```

### 3. 数据库模型检查

- [x] 所有模型使用`Text`类型（长文本字段）
- [x] 所有模型配置`mysql_engine="InnoDB"`
- [x] 所有模型配置`mysql_charset="utf8mb4"`
- [x] JSON字段使用MySQL 8.0兼容的默认值
- [x] Boolean字段使用`server_default="0"`

---

## 🧪 测试验证步骤

### Step 1: SQLite测试（基线验证）

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend

# 运行Repository层测试
pytest tests/modules/indicator/repositories/ -v

# 预期结果：
# ✅ 所有测试通过
# ✅ 测试数据库: SQLite
# ✅ 执行时间: ~2.6秒
```

**预期输出**:
```
========================= test session starts ==========================
Test Database: SQLite
Database URL: sqlite+aiosqlite:///:memory:
Pool Size: N/A (StaticPool)
Echo SQL: False

tests/modules/indicator/repositories/test_custom_factor_repository.py ✓✓✓
tests/modules/indicator/repositories/test_indicator_repository.py ✓✓✓

====================== 20 passed in 2.58s ==========================
```

### Step 2: 启动MySQL测试数据库

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend

# 方法A: 使用自动化脚本（推荐）
./scripts/setup_mysql_test.sh

# 方法B: 手动启动
docker-compose -f docker-compose.test.yml up -d

# 等待MySQL就绪
docker-compose -f docker-compose.test.yml ps
# 预期状态: Up (healthy)
```

**验证MySQL连接**:
```bash
mysql -h 127.0.0.1 -P 3307 -u test_user -ptest_password -e "SHOW DATABASES;"

# 预期输出包含:
# +--------------------+
# | Database           |
# +--------------------+
# | qlib_ui_test       |
# +--------------------+
```

### Step 3: MySQL测试（兼容性验证）

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend

# 设置环境变量
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test?charset=utf8mb4

# 运行Repository层测试
pytest tests/modules/indicator/repositories/ -v

# 预期结果：
# ✅ 所有测试通过
# ✅ 测试数据库: MySQL
# ✅ 执行时间: ~5.7秒
```

**预期输出**:
```
========================= test session starts ==========================
Test Database: MySQL
Database URL: mysql+aiomysql://test_user:***@localhost:3307/qlib_ui_test
Pool Size: 5
Echo SQL: False

tests/modules/indicator/repositories/test_custom_factor_repository.py ✓✓✓
tests/modules/indicator/repositories/test_indicator_repository.py ✓✓✓

====================== 20 passed in 5.72s ==========================
```

### Step 4: 数据隔离验证

```bash
# 运行测试
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/modules/indicator/repositories/test_custom_factor_repository.py::test_count_user_factors_all -v

# 检查数据库是否为空（测试后应该清理）
docker exec -it qlib-mysql-test mysql -u test_user -ptest_password qlib_ui_test \
  -e "SELECT COUNT(*) FROM custom_factors;"

# 预期输出: 0 (测试数据已清理)
```

### Step 5: 并发测试验证（可选）

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 并行运行测试
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/modules/indicator/repositories/ -n auto -v

# 预期: 所有测试通过，执行时间缩短
```

---

## 🔍 问题检查清单

### 如果SQLite测试失败

- [ ] 检查依赖安装: `pip install aiosqlite`
- [ ] 检查模型导入: 确保conftest.py导入所有模型
- [ ] 查看详细日志: `pytest -v -s --tb=short`

### 如果MySQL连接失败

- [ ] Docker运行中: `docker info`
- [ ] 容器启动成功: `docker-compose -f docker-compose.test.yml ps`
- [ ] 容器健康检查通过: 状态显示"healthy"
- [ ] 端口未被占用: `netstat -an | grep 3307`
- [ ] 环境变量正确: `echo $DATABASE_URL_TEST`

### 如果MySQL测试失败

- [ ] 数据库字符集正确: `utf8mb4`
- [ ] 连接池配置合理: `TEST_DB_POOL_SIZE=5`
- [ ] 模型导入完整: conftest.py导入所有模型
- [ ] 测试数据清理正确: 查看fixture teardown日志
- [ ] MySQL版本正确: `docker exec qlib-mysql-test mysql --version` (应为8.0)

---

## 📊 性能基准

### SQLite性能基准

| 指标 | 预期值 | 实际值 | 状态 |
|------|--------|--------|------|
| 启动时间 | ~0.1s | _待测_ | ⏸️ |
| 测试执行 | ~2.5s | _待测_ | ⏸️ |
| 总耗时 | ~2.6s | _待测_ | ⏸️ |

### MySQL性能基准

| 指标 | 预期值 | 实际值 | 状态 |
|------|--------|--------|------|
| 容器启动 | ~15s | _待测_ | ⏸️ |
| 连接建立 | ~0.5s | _待测_ | ⏸️ |
| 测试执行 | ~4.2s | _待测_ | ⏸️ |
| 总耗时 | ~5.7s | _待测_ | ⏸️ |

---

## ✅ 最终验证检查

### 必须验证的项目

- [ ] SQLite测试全部通过（20/20）
- [ ] MySQL测试全部通过（20/20）
- [ ] 测试结果一致（SQLite和MySQL结果相同）
- [ ] 测试数据正确清理（每次测试后数据库为空）
- [ ] 环境变量切换工作正常
- [ ] Docker容器可以正常启动和停止

### 推荐验证的项目

- [ ] 性能符合预期（MySQL比SQLite慢约2倍）
- [ ] 并发测试正常（使用pytest-xdist）
- [ ] 日志记录正确（TEST_DB_ECHO_SQL=true时显示SQL）
- [ ] 连接池工作正常（无连接泄漏）

---

## 🎯 验证命令速查

```bash
# 快速验证套件
cd /Users/zhenkunliu/project/qlib-ui/backend

# 1. SQLite测试
pytest tests/modules/indicator/repositories/ -v

# 2. 启动MySQL
docker-compose -f docker-compose.test.yml up -d

# 3. MySQL测试
export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
pytest tests/modules/indicator/repositories/ -v

# 4. 查看配置
pytest tests/modules/indicator/repositories/ --co

# 5. 清理
docker-compose -f docker-compose.test.yml down
```

---

## 📝 测试报告模板

执行验证后，填写此报告：

```
MySQL测试环境验证报告
====================

日期: ___________
执行人: ___________

SQLite测试
----------
✅/❌ 测试通过: ___/20
执行时间: ___秒
问题: ___________

MySQL测试
---------
✅/❌ 测试通过: ___/20
执行时间: ___秒
问题: ___________

环境信息
--------
Docker版本: ___________
MySQL版本: 8.0
Python版本: ___________

结论
----
✅/❌ 迁移成功，可以使用MySQL进行TDD开发
✅/❌ 性能符合预期
✅/❌ 所有功能正常工作

备注: ___________
```

---

## 🚀 下一步

验证通过后：

1. ✅ 提交配置文件到版本控制
   ```bash
   git add .env.test docker-compose.test.yml docker/ tests/ scripts/ docs/
   git commit -m "feat: add MySQL test environment support"
   ```

2. ✅ 更新团队文档
   - 在README.md中添加测试环境设置说明
   - 分享MYSQL_TEST_SETUP.md给团队成员

3. ✅ 配置CI/CD
   - 在GitHub Actions中添加MySQL服务
   - 每次PR自动运行MySQL测试

4. ✅ 创建pre-commit钩子（可选）
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   docker-compose -f docker-compose.test.yml up -d
   export DATABASE_URL_TEST=mysql+aiomysql://test_user:test_password@localhost:3307/qlib_ui_test
   pytest tests/modules/indicator/repositories/ || exit 1
   docker-compose -f docker-compose.test.yml down
   ```

---

**祝测试顺利！** 🎉
