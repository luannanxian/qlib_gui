# InstanceService 测试用例完整清单

## 测试统计
- **总测试数**: 52个
- **测试类**: 7个
- **覆盖方法**: 7个公开方法
- **格式**: 所有测试均使用 AAA 模式 (Arrange-Act-Assert)

---

## TestCreateFromTemplate (12个测试)

### 创建功能测试
- [ ] `test_create_with_default_parameters` - 使用模板默认参数创建策略实例
- [ ] `test_create_with_custom_parameters` - 使用自定义参数覆盖默认值
- [ ] `test_create_with_empty_parameters` - 提供空参数字典时使用默认值
- [ ] `test_create_with_none_parameters` - 提供None时使用默认值
- [ ] `test_partial_parameter_override` - 部分参数覆盖，其他使用默认值

### 模板功能测试
- [ ] `test_increment_usage_count` - 创建实例时模板使用计数递增1
- [ ] `test_multiple_instances_increment_count` - 创建多个实例时计数递增多次

### 错误处理测试
- [ ] `test_invalid_template_id` - 不存在的模板ID应抛出ValueError

### 深度复制验证
- [ ] `test_deep_copy_logic_flow` - 修改实例逻辑流不影响模板
- [ ] `test_deep_copy_parameters` - 修改实例参数不影响模板默认值

### 复杂场景测试
- [ ] `test_complex_template_with_many_parameters` - 处理包含多个参数的复杂模板
- [ ] `test_create_multiple_from_same_template` - 从同一模板创建多个独立实例

---

## TestCreateCustom (6个测试)

### 基础功能测试
- [ ] `test_create_custom_strategy` - 创建没有模板的自定义策略
- [ ] `test_custom_strategy_default_status` - 新策略默认状态为DRAFT
- [ ] `test_custom_strategy_no_template_id` - 自定义策略的template_id为None

### 边界情况测试
- [ ] `test_create_custom_with_empty_logic_flow` - 允许创建空逻辑流的策略
- [ ] `test_create_custom_with_complex_logic_flow` - 处理复杂的逻辑流结构

### 独立性测试
- [ ] `test_create_multiple_custom_strategies` - 创建多个独立的自定义策略

---

## TestDuplicateStrategy (8个测试)

### 基础功能测试
- [ ] `test_duplicate_existing_strategy` - 复制现有策略创建副本
- [ ] `test_duplicate_custom_strategy` - 复制自定义策略（无模板）

### 深度复制验证
- [ ] `test_duplicate_preserves_deep_copy` - 修改副本不影响原件

### 权限验证测试
- [ ] `test_duplicate_unauthorized_user` - 其他用户无法复制策略
- [ ] `test_duplicate_nonexistent_strategy` - 非存在策略无法复制

### 功能测试
- [ ] `test_duplicate_with_different_name` - 复制时支持更改名称
- [ ] `test_duplicate_multiple_times` - 可多次复制同一策略

---

## TestSaveSnapshot (7个测试)

### 基础功能测试
- [ ] `test_save_first_snapshot` - 保存首个快照并设置正确的版本号
- [ ] `test_save_multiple_snapshots` - 保存多个快照时版本号递增

### 深度复制测试
- [ ] `test_save_snapshot_deep_copy` - 快照保存后修改策略不影响快照

### 限制验证测试
- [ ] `test_max_five_versions_limit` - 超过5个快照时删除最旧的
- [ ] `test_snapshot_preserves_strategy_status` - 快照保存策略状态

### 权限和错误处理
- [ ] `test_snapshot_unauthorized_user` - 其他用户无法保存快照
- [ ] `test_snapshot_nonexistent_strategy` - 非存在策略无法保存快照

---

## TestRestoreSnapshot (8个测试)

### 基础功能测试
- [ ] `test_restore_from_snapshot` - 从快照恢复策略参数和状态
- [ ] `test_restore_logic_flow` - 恢复逻辑流和参数两部分内容
- [ ] `test_restore_multiple_times` - 可多次从不同快照恢复

### 权限验证测试
- [ ] `test_restore_unauthorized_strategy` - 其他用户无法恢复策略
- [ ] `test_restore_unauthorized_snapshot` - 无法使用他人的快照

### 错误处理测试
- [ ] `test_restore_invalid_snapshot` - 非存在快照应抛出错误
- [ ] `test_restore_mismatched_snapshot` - 快照不属于该策略时应抛出错误

---

## TestGetVersions (7个测试)

### 检索功能测试
- [ ] `test_get_version_history` - 检索策略的所有快照版本
- [ ] `test_get_versions_empty` - 无快照时返回空列表
- [ ] `test_get_versions_many` - 检索多个快照版本

### 排序验证测试
- [ ] `test_versions_sorted_by_created_at` - 版本按创建时间降序排列（最新优先）
- [ ] `test_version_attributes` - 版本具有正确的属性（version, parent_version_id等）

### 权限验证测试
- [ ] `test_get_versions_unauthorized` - 其他用户无法访问版本历史
- [ ] `test_get_versions_nonexistent_strategy` - 非存在策略无法获取版本

---

## TestIntegrationScenarios (4个集成测试)

### 完整生命周期
- [ ] `test_complete_lifecycle` - 完整的策略生命周期（创建→快照→复制→版本查询）
- [ ] `test_snapshot_restore_workflow` - 快照保存和恢复的完整工作流
- [ ] `test_custom_strategy_snapshot_workflow` - 自定义策略的快照工作流

### 多用户隔离
- [ ] `test_multiple_users_isolation` - 不同用户的策略相互隔离

### 系统限制
- [ ] `test_version_limit_enforcement` - 强制执行最多5个版本的限制

### 模板独立性
- [ ] `test_create_from_different_templates` - 从不同模板创建实例的独立性

---

## 测试覆盖矩阵

| 方法 | 测试数 | 基础功能 | 边界情况 | 错误处理 | 集成测试 |
|-----|------|--------|--------|--------|--------|
| create_from_template | 12 | 5 | 4 | 1 | 2 |
| create_custom | 6 | 3 | 2 | 1 | 0 |
| duplicate_strategy | 8 | 3 | 2 | 2 | 1 |
| save_snapshot | 7 | 2 | 2 | 2 | 1 |
| restore_snapshot | 8 | 3 | 1 | 3 | 1 |
| get_versions | 7 | 3 | 2 | 2 | 0 |
| 集成场景 | 4 | - | - | - | 4 |

---

## 测试执行检查清单

### 前置条件
- [ ] 设置 DATABASE_URL 环境变量
- [ ] 设置 SECRET_KEY 环境变量
- [ ] 确保测试数据库可访问
- [ ] 确保 AsyncSession fixture 正常工作

### 执行命令
```bash
# 运行全部测试
pytest backend/tests/test_strategy/test_instance_service.py -v

# 运行特定测试类
pytest backend/tests/test_strategy/test_instance_service.py::TestCreateFromTemplate -v

# 生成覆盖率报告
pytest backend/tests/test_strategy/test_instance_service.py --cov --cov-report=html
```

### 成功标准
- [ ] 所有52个测试通过
- [ ] 无警告或错误信息
- [ ] instance_service.py 代码覆盖率 >= 80%
- [ ] 所有关键路径覆盖率 = 100%

---

## 测试数据流

### 测试数据准备流
```
Fixtures:
├── db_session - 异步数据库会话
├── instance_service - InstanceService 实例
├── sample_template - MA Cross 简单模板
└── complex_template - RSI 复杂模板（多参数）
```

### 典型测试流程
```
1. Arrange (准备)
   └── 使用 fixtures 创建初始数据

2. Act (执行)
   └── 调用 instance_service 的方法

3. Assert (验证)
   └── 验证返回值、状态变化、错误
```

---

## 关键测试特点

### AAA 模式严格遵守
每个测试都明确划分为三个部分：
- **Arrange**: 设置测试条件
- **Act**: 执行被测试的操作
- **Assert**: 验证结果

### 完整的错误场景覆盖
- 权限错误（用户隔离）
- 资源不存在（404场景）
- 无效操作（快照不匹配）
- 数据冲突（版本限制）

### 深度复制验证
- 所有创建操作都验证深度复制
- 修改副本不影响原件
- 各字段（逻辑流、参数）独立存储

### 用户隔离严格验证
- 每个操作都检查用户权限
- 跨用户操作都会失败
- 权限错误消息清晰

---

## 性能考虑

| 场景 | 注意事项 |
|-----|---------|
| 版本限制 | 第6个快照会触发删除最旧版本的操作 |
| 多用户 | 用户隔离通过 user_id 检查实现 |
| 深度复制 | JSON 结构的深度复制可能影响性能 |
| 数据库 | 所有操作都需要异步数据库访问 |

---

## 扩展建议

未来可添加的测试：
- [ ] 并发测试（多用户同时操作同一策略）
- [ ] 性能测试（大量快照创建）
- [ ] 参数验证测试（非法参数值验证）
- [ ] API 集成测试（与HTTP端点集成）
- [ ] 数据库约束验证
- [ ] 事务一致性验证

---

## 文件信息

| 文件 | 路径 |
|-----|------|
| 源文件 | `/Users/zhenkunliu/project/qlib-ui/backend/app/modules/strategy/services/instance_service.py` |
| 测试文件 | `/Users/zhenkunliu/project/qlib-ui/backend/tests/test_strategy/test_instance_service.py` |
| 覆盖报告 | `/Users/zhenkunliu/project/qlib-ui/backend/htmlcov/app_modules_strategy_services_instance_service_py.html` |

---

## 快速参考

### 常用命令
```bash
# 运行所有测试
pytest backend/tests/test_strategy/test_instance_service.py -v

# 运行特定测试
pytest backend/tests/test_strategy/test_instance_service.py::TestCreateFromTemplate::test_create_with_default_parameters -v

# 显示覆盖率
pytest backend/tests/test_strategy/test_instance_service.py --cov=app.modules.strategy.services.instance_service

# 生成HTML覆盖率报告
pytest backend/tests/test_strategy/test_instance_service.py --cov=app.modules.strategy.services.instance_service --cov-report=html
```

### 调试技巧
```bash
# 显示打印输出
pytest backend/tests/test_strategy/test_instance_service.py -v -s

# 停在第一个失败处
pytest backend/tests/test_strategy/test_instance_service.py -x

# 显示最慢的10个测试
pytest backend/tests/test_strategy/test_instance_service.py --durations=10
```

---

**总结**: 该测试套件提供了对 InstanceService 全方位的测试覆盖，包括功能测试、边界情况、错误处理和集成场景，预计代码覆盖率可达 80%+ 目标。
