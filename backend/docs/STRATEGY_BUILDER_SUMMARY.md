# Strategy Builder 架构设计总结

## 执行摘要

Strategy Builder是qlib-ui项目Strategy模块的重要扩展,旨在为用户提供可视化策略构建、代码生成和快速测试能力。本文档总结了完整的架构设计和实施计划。

---

## 1. 关键决策

### 架构决策: 扩展现有Strategy模块

**不创建独立模块,而是扩展现有Strategy模块**

**优势:**
- 利用现有90%的基础设施 (Logic Flow, Template, Instance管理)
- 避免数据结构重复
- 降低模块间耦合
- 开发周期缩短50%

**现有功能 (无需重新开发):**
- Strategy Template CRUD
- Strategy Instance管理
- Logic Flow数据结构
- 版本管理 (快照和恢复)
- 基础验证服务

**新增功能 (本次开发):**
- 因子库集成API
- 策略代码生成
- 代码验证
- 快速回测集成
- 节点模板库
- 策略导入/导出

---

## 2. 核心功能概览

### 2.1 功能优先级

#### P0 (必须实现)
1. **因子库集成** - 从Indicator模块获取可用因子
2. **代码生成器** - Logic Flow转Qlib Python代码
3. **代码验证** - 语法检查 + 安全扫描

#### P1 (重要)
4. **快速测试** - 与Backtest模块集成
5. **节点模板库** - 预定义常用节点配置
6. **逻辑验证增强** - 实时错误提示

#### P2 (可选)
7. **策略导入/导出** - JSON/YAML格式
8. **模板克隆** - 快速修改系统模板
9. **参数优化建议** - 基于历史数据

### 2.2 API端点清单 (14个新增端点)

**Builder Components (3个)**
- `GET /api/builder/factors` - 获取因子列表
- `GET /api/builder/factors/{id}` - 因子详情
- `GET /api/builder/node-templates` - 节点模板

**Code Generation (3个)**
- `POST /api/builder/strategies/{id}/generate-code` - 生成代码
- `POST /api/builder/validate-code` - 验证代码
- `POST /api/builder/preview-logic` - 预览执行

**Quick Testing (2个)**
- `POST /api/builder/strategies/{id}/quick-test` - 快速回测
- `GET /api/builder/quick-tests/{task_id}` - 获取结果

**Enhanced Templates (3个)**
- `POST /api/builder/templates/{id}/clone` - 克隆模板
- `GET /api/builder/strategies/{id}/export` - 导出策略
- `POST /api/builder/strategies/import` - 导入策略

---

## 3. 数据库设计

### 决策: 不需要新表

**现有表已足够:**
- `strategy_templates` - 存储模板 (包括节点模板)
- `strategy_instances` - 存储策略实例
- `template_ratings` - 模板评分

**可选扩展字段 (StrategyInstance表):**
```sql
ALTER TABLE strategy_instances
ADD COLUMN generated_code TEXT NULL;
ADD COLUMN code_hash VARCHAR(64) NULL;
ADD COLUMN last_code_generated_at TIMESTAMP NULL;
```

**缓存策略:**
- 生成的代码缓存在Redis (1小时TTL)
- 因子列表缓存在内存 (5分钟TTL)
- 快速测试结果由Backtest模块管理

---

## 4. 模块集成架构

```
┌──────────────────────────────────────────────────┐
│          Frontend (React + React Flow)           │
│  - Visual Flow Editor                            │
│  - Code Preview Panel                            │
│  - Test Results Dashboard                        │
└────────────────┬─────────────────────────────────┘
                 │ REST API / WebSocket
                 ↓
┌──────────────────────────────────────────────────┐
│         Strategy Module (扩展层)                  │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │ BuilderService                             │ │
│  │ - get_available_factors()                  │ │
│  │ - get_node_templates()                     │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │ CodeGeneratorService                       │ │
│  │ - generate_strategy_code()                 │ │
│  │ - validate_code()                          │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
│  ┌────────────────────────────────────────────┐ │
│  │ QuickTestService                           │ │
│  │ - submit_quick_test()                      │ │
│  │ - get_test_results()                       │ │
│  └────────────────────────────────────────────┘ │
│                                                   │
└───┬──────────────────┬─────────────────┬────────┘
    │                  │                 │
    ↓                  ↓                 ↓
┌──────────┐   ┌──────────────┐   ┌────────────┐
│Indicator │   │   Backtest   │   │Code Security│
│  Module  │   │    Module    │   │   Module   │
└──────────┘   └──────────────┘   └────────────┘
```

### 集成点

**Indicator模块:**
- 提供因子列表和详情
- 参数定义和默认值
- 使用统计

**Backtest模块:**
- 接收生成的策略代码
- 执行异步回测任务
- 返回结果和性能指标

**Code Security模块:**
- 代码安全扫描
- 禁止危险操作检测
- Import白名单验证

---

## 5. 代码生成器设计

### 5.1 节点类型映射

| 节点类型 | 功能 | 生成代码示例 |
|---------|------|------------|
| INDICATOR | 技术指标计算 | `data['sma'] = data['close'].rolling(20).mean()` |
| CONDITION | 条件判断 | `condition = data['close'] > data['sma']` |
| SIGNAL | 交易信号 | `signals = np.where(condition, 1, 0)` |
| POSITION | 仓位管理 | `positions = signals * 0.5` |
| STOP_LOSS | 止损策略 | `stop_loss = data['close'] * 0.95` |
| STOP_PROFIT | 止盈策略 | `stop_profit = data['close'] * 1.10` |

### 5.2 生成流程

```
Logic Flow (JSON)
    ↓
1. 解析节点和边
    ↓
2. 按类型分组节点
    ↓
3. 节点 → 代码片段 (NodeConverter)
    ↓
4. 组装完整代码 (Jinja2模板)
    ↓
5. 格式化 (Black)
    ↓
6. 验证 (AST + Security)
    ↓
Generated Code (Python)
```

### 5.3 代码模板 (Qlib格式)

```python
import pandas as pd
import numpy as np
from qlib.strategy import BaseStrategy

class GeneratedStrategy(BaseStrategy):
    """自动生成的Qlib策略"""

    def __init__(self, **kwargs):
        super().__init__()
        # 参数初始化
        self.param1 = kwargs.get('param1', default1)
        ...

    def generate_signals(self, data):
        """生成交易信号"""
        signals = pd.Series(0, index=data.index)

        # 1. 计算指标
        data['sma'] = data['close'].rolling(20).mean()
        ...

        # 2. 判断条件
        condition = data['close'] > data['sma']
        ...

        # 3. 生成信号
        signals = np.where(condition, 1, 0)
        ...

        # 4. 计算仓位
        positions = signals * 0.5
        ...

        return positions
```

---

## 6. 关键技术选型

### 6.1 后端技术栈

**现有 (无需改动):**
- FastAPI - REST API框架
- SQLAlchemy - ORM
- Pydantic - 数据验证
- MySQL - 数据存储

**新增依赖:**
```python
# 代码生成和格式化
black==24.0.0           # Python代码格式化
jinja2==3.1.0           # 代码模板引擎
astroid==3.0.0          # AST分析

# 缓存
redis==5.0.0            # 代码缓存

# HTTP客户端
httpx==0.27.0           # 异步HTTP调用
```

### 6.2 前端技术栈 (建议)

```json
{
  "react-flow-renderer": "^10.3.0",  // 可视化流程图编辑器
  "monaco-editor": "^0.44.0",        // 代码编辑器 (VS Code内核)
  "recharts": "^2.10.0",              // 图表库
  "zustand": "^4.4.0",                // 轻量级状态管理
  "react-query": "^5.0.0"             // 数据获取和缓存
}
```

---

## 7. 性能和安全考虑

### 7.1 性能优化

**代码生成缓存:**
```python
# Redis缓存键: strategy_code:{strategy_id}:{logic_flow_hash}
# TTL: 1小时
# 命中率目标: >80%
```

**因子列表缓存:**
```python
# 内存LRU缓存
# TTL: 5分钟
# 缓存大小: 128条记录
```

**异步任务:**
```python
# 使用Celery处理耗时操作
# - 代码生成 (>2秒)
# - 快速测试 (>5秒)
```

### 7.2 安全措施

**代码生成安全:**
- Import白名单: pandas, numpy, qlib, talib
- 禁止操作: os.system, exec, eval, __import__
- AST分析检测危险代码

**代码执行沙箱:**
- 资源限制: CPU 2核, 内存 512MB
- 时间限制: 最长5分钟
- 网络隔离

**访问控制:**
- 策略只能被所有者访问
- 代码生成需要认证
- 快速测试频率限制: 10次/小时

---

## 8. 实施计划

### 时间线: 5周

| 阶段 | 时间 | 任务 | 交付物 |
|-----|------|------|--------|
| **阶段1** | Week 1 | 基础设施搭建 | Builder Schema, BuilderService |
| **阶段2** | Week 2 | 代码生成器实现 | CodeGenerator, 节点转换器 |
| **阶段3** | Week 2-3 | API端点实现 | 14个REST端点 |
| **阶段4** | Week 3 | 快速测试集成 | QuickTestService, Backtest集成 |
| **阶段5** | Week 4-5 | 测试和优化 | 单元测试, 集成测试, 文档 |

### 关键里程碑

- **Week 1结束**: 因子库集成可用
- **Week 2结束**: 代码生成器可用 (支持所有节点类型)
- **Week 3结束**: 快速测试可用
- **Week 4结束**: 所有功能完成,进入测试阶段
- **Week 5结束**: 上线发布

---

## 9. 验收标准

### 9.1 功能验收

- [ ] 用户可以从因子库选择指标并添加到策略
- [ ] 用户可以配置节点参数
- [ ] 生成的代码语法正确且可执行
- [ ] 代码验证能检测出语法错误和安全问题
- [ ] 快速测试能在5分钟内返回结果
- [ ] 测试结果包含关键指标 (收益率、夏普、最大回撤)
- [ ] 策略可以导出和导入

### 9.2 质量验收

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖所有核心流程
- [ ] API响应时间 < 500ms (P95)
- [ ] 代码生成成功率 > 95%
- [ ] 快速测试成功率 > 90%
- [ ] 无P0/P1级别bug

### 9.3 文档验收

- [ ] API文档完整 (OpenAPI规范)
- [ ] 用户手册完整 (包含示例)
- [ ] 开发者文档完整 (架构、设计决策)
- [ ] 部署文档完整

---

## 10. 风险和挑战

### 10.1 技术风险

**风险1: 代码生成复杂度**
- **影响**: 某些复杂Logic Flow可能难以生成正确代码
- **缓解**: 从简单节点开始,逐步增加复杂度;提供代码预览功能

**风险2: Backtest模块性能**
- **影响**: 快速测试可能因回测性能问题变慢
- **缓解**: 限制测试数据范围 (默认3个月);使用任务队列异步处理

**风险3: 前后端协作**
- **影响**: 前端可视化编辑器与后端Logic Flow格式不匹配
- **缓解**: 提前定义好数据格式;提供Mock数据进行前端开发

### 10.2 业务风险

**风险1: 用户学习曲线**
- **影响**: 用户可能不理解如何使用可视化构建器
- **缓解**: 提供预定义模板;提供交互式教程

**风险2: 生成代码质量**
- **影响**: 自动生成的代码可能性能不佳
- **缓解**: 提供代码优化建议;允许用户手动修改代码

---

## 11. 下一步行动

### 立即开始 (本周)

1. **审查和确认架构设计**
   - 与团队review架构文档
   - 确认技术选型
   - 明确优先级

2. **环境准备**
   - 安装新增依赖 (black, jinja2, httpx等)
   - 配置Redis缓存
   - 准备开发环境

3. **开始实施**
   - 创建目录结构
   - 实现Builder Schema
   - 开始BuilderService开发

### 第一个Sprint (Week 1-2)

**目标**: 完成P0功能的基础版本

**任务清单**:
- [ ] Builder Schema实现 (2天)
- [ ] BuilderService实现 - 因子库集成 (3天)
- [ ] CodeGenerator基础框架 (2天)
- [ ] INDICATOR和CONDITION节点代码生成 (3天)

**验收**: 能够从因子库选择指标并生成基础代码

---

## 12. 相关文档

### 架构设计
- `STRATEGY_BUILDER_ARCHITECTURE.md` - 完整架构设计文档
- `strategy_builder_api.yaml` - OpenAPI规范

### 实施计划
- `STRATEGY_BUILDER_IMPLEMENTATION_PLAN.md` - 详细实施计划

### 现有模块文档
- `backend/app/modules/strategy/` - 现有Strategy模块代码
- `backend/app/modules/indicator/` - Indicator模块
- `backend/app/modules/backtest/` - Backtest模块

---

## 13. 联系方式

**架构设计负责人**: Backend Architect
**实施负责人**: [待定]
**产品负责人**: [待定]

**问题反馈**:
- 技术问题: 提交Issue到项目仓库
- 设计问题: 发起Architecture Discussion

---

## 附录: 快速参考

### A. 节点类型总览

| 类型 | 用途 | 必填字段 | 可选字段 |
|-----|------|---------|---------|
| INDICATOR | 计算技术指标 | indicator, parameters | label |
| CONDITION | 条件判断 | condition | label |
| SIGNAL | 生成交易信号 | signal_type | label |
| POSITION | 仓位管理 | position_type, position_value | label |
| STOP_LOSS | 止损策略 | stop_loss_type, stop_loss_value | label |
| STOP_PROFIT | 止盈策略 | stop_profit_type, stop_profit_value | label |

### B. API端点速查

| 功能 | 方法 | 端点 | 说明 |
|-----|------|------|------|
| 获取因子 | GET | /api/builder/factors | 因子列表 |
| 因子详情 | GET | /api/builder/factors/{id} | 因子详细信息 |
| 节点模板 | GET | /api/builder/node-templates | 预定义节点 |
| 生成代码 | POST | /api/builder/strategies/{id}/generate-code | 生成策略代码 |
| 验证代码 | POST | /api/builder/validate-code | 验证代码 |
| 快速测试 | POST | /api/builder/strategies/{id}/quick-test | 运行回测 |
| 测试结果 | GET | /api/builder/quick-tests/{task_id} | 获取结果 |
| 导出策略 | GET | /api/builder/strategies/{id}/export | 导出JSON |
| 导入策略 | POST | /api/builder/strategies/import | 导入JSON |

### C. 错误码速查

| 错误码 | 说明 | 解决方法 |
|-------|------|---------|
| 400 | 请求参数错误 | 检查请求体格式 |
| 404 | 资源不存在 | 确认ID正确 |
| 422 | 验证失败 | 检查Logic Flow结构 |
| 500 | 代码生成失败 | 查看详细错误信息 |
| 503 | Backtest服务不可用 | 稍后重试 |

---

**文档版本**: v1.0
**最后更新**: 2025-01-09
**状态**: 待审批
