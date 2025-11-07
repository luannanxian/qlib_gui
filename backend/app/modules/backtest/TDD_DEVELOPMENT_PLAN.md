# 回测模块 TDD 开发计划

## 📊 项目概述

**目标**: 基于测试驱动开发（TDD）方法，从零构建完整的回测模块

**当前状态**: 5% 完成（仅基础设施）
**目标覆盖率**: 95%+
**开发方法**: 红-绿-重构循环

---

## 🎯 Phase 1: 核心功能（2-3周）

### Phase 1.1: 数据库模型和测试 ✅ 当前阶段

**TDD 步骤**:
1. **红**: 编写模型测试（预期失败）
2. **绿**: 实现最小可行模型
3. **重构**: 优化模型设计

**测试文件**: `tests/test_backtest/models/test_backtest_models.py`

**测试用例**:
- ✅ `test_create_backtest_config` - 创建回测配置
- ✅ `test_backtest_config_validation` - 配置验证
- ✅ `test_backtest_config_relationships` - 关系映射
- ✅ `test_create_backtest_result` - 创建回测结果
- ✅ `test_backtest_result_metrics` - 结果指标
- ✅ `test_backtest_status_transitions` - 状态转换
- ✅ `test_backtest_soft_delete` - 软删除

**实现文件**: `app/database/models/backtest.py`

**模型定义**:
```python
class BacktestStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class BacktestConfig(BaseDBModel):
    """回测配置模型"""
    strategy_id: str  # FK to StrategyInstance
    dataset_id: str   # FK to Dataset
    start_date: date
    end_date: date
    initial_capital: Decimal
    commission_rate: Decimal
    slippage: Decimal
    config_params: JSON

class BacktestResult(BaseDBModel):
    """回测结果模型"""
    config_id: str    # FK to BacktestConfig
    status: BacktestStatus
    total_return: Decimal
    annual_return: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    win_rate: Decimal
    metrics: JSON
    trades: JSON
```

**验收标准**:
- [ ] 所有模型测试通过
- [ ] 模型关系正确建立
- [ ] 数据验证规则生效
- [ ] 软删除功能正常

---

### Phase 1.2: Repository 层和测试

**TDD 步骤**:
1. **红**: 编写 Repository 测试
2. **绿**: 实现 Repository 方法
3. **重构**: 优化查询性能

**测试文件**: `tests/test_backtest/repositories/test_backtest_repository.py`

**测试用例**:
- `test_create_backtest_config`
- `test_get_backtest_by_id`
- `test_get_backtest_by_strategy`
- `test_get_backtest_by_status`
- `test_update_backtest_status`
- `test_get_backtest_results`
- `test_soft_delete_backtest`
- `test_get_backtest_history`

**实现文件**: `app/database/repositories/backtest.py`

**验收标准**:
- [ ] 100% Repository 测试覆盖率
- [ ] 所有 CRUD 操作正常
- [ ] 查询性能优化
- [ ] 事务处理正确

---

### Phase 1.3: 配置服务和测试

**TDD 步骤**:
1. **红**: 编写配置服务测试
2. **绿**: 实现配置管理逻辑
3. **重构**: 优化配置验证

**测试文件**: `tests/test_backtest/services/test_config_service.py`

**测试用例**:
- `test_create_backtest_config`
- `test_validate_config_params`
- `test_validate_date_range`
- `test_validate_capital_constraints`
- `test_get_config_by_id`
- `test_update_config`
- `test_delete_config`
- `test_config_with_invalid_strategy`
- `test_config_with_invalid_dataset`

**实现文件**: `app/modules/backtest/services/config_service.py`

**验收标准**:
- [ ] 95%+ Service 测试覆盖率
- [ ] 配置验证完整
- [ ] 错误处理健壮
- [ ] 业务逻辑正确

---

### Phase 1.4: 执行服务和测试

**TDD 步骤**:
1. **红**: 编写执行服务测试
2. **绿**: 实现回测执行逻辑
3. **重构**: 优化执行性能

**测试文件**: `tests/test_backtest/services/test_execution_service.py`

**测试用例**:
- `test_start_backtest`
- `test_pause_backtest`
- `test_resume_backtest`
- `test_cancel_backtest`
- `test_backtest_progress_tracking`
- `test_backtest_with_qlib_engine`
- `test_backtest_error_handling`
- `test_backtest_timeout`
- `test_concurrent_backtests`

**实现文件**:
- `app/modules/backtest/services/execution_service.py`
- `app/modules/backtest/services/qlib_engine.py`

**验收标准**:
- [ ] 95%+ Service 测试覆盖率
- [ ] Qlib 集成正常
- [ ] 进度跟踪准确
- [ ] 异常处理完善

---

### Phase 1.5: API 端点和测试

**TDD 步骤**:
1. **红**: 编写 API 测试
2. **绿**: 实现 API 端点
3. **重构**: 优化响应格式

**测试文件**: `tests/test_backtest/api/test_backtest_api.py`

**测试用例**:
- `test_create_backtest_endpoint`
- `test_get_backtest_endpoint`
- `test_list_backtests_endpoint`
- `test_start_backtest_endpoint`
- `test_pause_backtest_endpoint`
- `test_cancel_backtest_endpoint`
- `test_get_backtest_results_endpoint`
- `test_get_backtest_metrics_endpoint`
- `test_api_authentication`
- `test_api_authorization`
- `test_api_validation_errors`
- `test_api_rate_limiting`

**实现文件**: `app/modules/backtest/api/backtest_api.py`

**API 端点**:
```
POST   /api/backtest/config          - 创建配置
GET    /api/backtest/config/{id}     - 获取配置
PUT    /api/backtest/config/{id}     - 更新配置
DELETE /api/backtest/config/{id}     - 删除配置
POST   /api/backtest/{id}/start      - 开始回测
POST   /api/backtest/{id}/pause      - 暂停回测
POST   /api/backtest/{id}/resume     - 恢复回测
POST   /api/backtest/{id}/cancel     - 取消回测
GET    /api/backtest/{id}/status     - 获取状态
GET    /api/backtest/{id}/results    - 获取结果
GET    /api/backtest/{id}/metrics    - 获取指标
GET    /api/backtest                 - 列表查询
```

**验收标准**:
- [ ] 所有 API 测试通过
- [ ] OpenAPI 文档完整
- [ ] 错误响应规范
- [ ] 性能满足要求

---

### Phase 1.6: 集成测试和端到端测试

**测试文件**: `tests/test_backtest/integration/test_backtest_flow.py`

**测试场景**:
- `test_complete_backtest_flow` - 完整回测流程
- `test_backtest_with_real_strategy` - 真实策略回测
- `test_backtest_with_real_data` - 真实数据回测
- `test_concurrent_backtests` - 并发回测
- `test_backtest_error_recovery` - 错误恢复
- `test_backtest_performance` - 性能测试

**验收标准**:
- [ ] 端到端流程通过
- [ ] 性能指标达标（5年200股票<10分钟）
- [ ] 并发处理正常
- [ ] 错误恢复机制有效

---

## 🚀 Phase 2: 高级功能（2-3周）

### Phase 2.1: 结果分析服务

**功能**:
- 指标计算（收益率、夏普比率、最大回撤等）
- 交易分析（胜率、盈亏比、持仓时间等）
- 图表生成（收益曲线、回撤曲线、持仓分布等）

### Phase 2.2: 诊断服务

**功能**:
- 收益分析（收益来源、收益分布）
- 风险分析（波动率、VaR、CVaR）
- 过拟合检测（样本内外对比、稳定性分析）
- 优化建议（参数调优、策略改进）

### Phase 2.3: WebSocket 实时进度

**功能**:
- 实时进度推送
- 实时日志推送
- 实时指标更新

### Phase 2.4: 报告导出

**功能**:
- PDF 报告生成
- Excel 数据导出
- 图表导出

---

## 🎨 Phase 3: 优化和完善（1-2周）

### Phase 3.1: 性能优化

**优化项**:
- 数据库查询优化
- 缓存策略
- 异步任务优化
- 内存管理

### Phase 3.2: 文档完善

**文档**:
- API 文档
- 用户指南
- 开发者文档
- 架构设计文档

### Phase 3.3: 监控和日志

**功能**:
- 性能监控
- 错误追踪
- 审计日志
- 告警机制

---

## 📊 测试覆盖率目标

| 层级 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| Models | 100% | 0% |
| Repositories | 100% | 0% |
| Services | 95%+ | 0% |
| API | 95%+ | 0% |
| Integration | 90%+ | 0% |
| **总体** | **95%+** | **0%** |

---

## 🔄 TDD 工作流程

### 红-绿-重构循环

```
1. 红 (Red) - 编写失败的测试
   ├── 定义测试用例
   ├── 编写测试代码
   └── 运行测试（预期失败）

2. 绿 (Green) - 实现最小可行代码
   ├── 编写实现代码
   ├── 运行测试（预期通过）
   └── 验证功能正确

3. 重构 (Refactor) - 优化代码质量
   ├── 重构实现代码
   ├── 重构测试代码
   ├── 运行测试（保持通过）
   └── 代码审查
```

---

## ✅ 验收标准

### Phase 1 完成标准:
- [ ] 所有核心功能测试通过
- [ ] 测试覆盖率达到 95%+
- [ ] API 文档完整
- [ ] 性能测试通过
- [ ] 代码审查通过

### 最终验收标准:
- [ ] 所有功能测试通过
- [ ] 总体覆盖率 95%+
- [ ] 性能指标达标
- [ ] 文档完整
- [ ] 安全审计通过
- [ ] 用户验收测试通过

---

## 📅 时间线

| 阶段 | 预计时间 | 里程碑 |
|------|---------|--------|
| Phase 1.1 | 2天 | 模型完成 |
| Phase 1.2 | 2天 | Repository 完成 |
| Phase 1.3 | 3天 | 配置服务完成 |
| Phase 1.4 | 5天 | 执行服务完成 |
| Phase 1.5 | 3天 | API 完成 |
| Phase 1.6 | 2天 | 集成测试完成 |
| **Phase 1 总计** | **17天** | **核心功能完成** |
| Phase 2 | 15天 | 高级功能完成 |
| Phase 3 | 8天 | 优化完善 |
| **总计** | **40天** | **模块完成** |

---

## 🛠️ 技术栈

- **框架**: FastAPI
- **ORM**: SQLAlchemy (async)
- **测试**: pytest + pytest-asyncio
- **回测引擎**: Qlib
- **任务队列**: Celery
- **数据库**: MySQL/SQLite
- **缓存**: Redis
- **WebSocket**: FastAPI WebSocket

---

## 📝 注意事项

1. **严格遵循 TDD**: 先写测试，再写实现
2. **保持高覆盖率**: 每个阶段都要达到目标覆盖率
3. **持续集成**: 每次提交都要通过所有测试
4. **代码审查**: 每个 PR 都要经过审查
5. **文档同步**: 代码和文档同步更新
6. **性能监控**: 持续监控性能指标

---

## 🎯 下一步行动

**立即开始**: Phase 1.1 - 数据库模型和测试

1. 创建测试文件 `tests/test_backtest/models/test_backtest_models.py`
2. 编写模型测试用例（红）
3. 运行测试（预期失败）
4. 创建模型文件 `app/database/models/backtest.py`
5. 实现模型（绿）
6. 运行测试（预期通过）
7. 重构优化
8. 提交代码

**让我们开始吧！** 🚀
