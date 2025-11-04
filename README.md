# Qlib-UI: 量化投资研究平台图形化界面

<div align="center">

![Qlib-UI Logo](docs/assets/logo.png)

**让量化投资研究更简单、更高效**

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0%2B-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()

[功能特性](#功能特性) • [快速开始](#快速开始) • [文档](#文档) • [技术栈](#技术栈) • [贡献](#贡献)

</div>

---

## 📖 项目简介

Qlib-UI 是基于微软 [Qlib](https://github.com/microsoft/qlib) 量化投资框架构建的图形化平台，旨在通过可视化界面降低量化投资研究的使用门槛，让没有编程背景的个人投资者也能进行专业的量化策略研究与回测。

### 核心理念

- 🎯 **降低门槛**: 无需编程,拖拽式操作完成策略构建
- ⚡ **提升效率**: 预设模板+参数优化,快速迭代验证策略
- 🔬 **专业级功能**: 完整映射Qlib核心能力,专业回测分析
- 🛡️ **安全可靠**: 本地部署,数据安全,代码执行沙箱

---

## ✨ 功能特性

### 🎓 新手友好

- **新手/专家双模式**: 根据用户水平智能切换界面复杂度
- **3步引导教程**: 从数据导入到策略验证的完整引导
- **10+经典策略模板**: 双均线、MACD、RSI等即开即用
- **指标解读卡片**: 通俗易懂的专业术语解释

### 📊 数据管理

- **多数据源支持**:
  - Qlib本地数据(中国A股、美股等)
  - CSV/Excel文件导入(批量上传,自动字段映射)
  - 第三方接口预留(架构可扩展)
- **智能数据预处理**:
  - 4种缺失值处理方式
  - 标准差/分位数异常值检测
  - 归一化/标准化转换
  - 多条件筛选+模板保存
- **专业数据可视化**:
  - K线图+成交量+均线叠加
  - MACD、RSI、KDJ等20+技术指标图
  - 自定义图表配置,多图联动

### 🎨 策略构建

- **可视化流程编辑器**:
  - 拖拽式节点连接,构建策略逻辑
  - 支持指标计算、条件判断、交易信号、仓位控制、止损止盈
  - 实时逻辑校验,错误高亮提示
- **60+技术指标库**:
  - 技术指标(MA、MACD等20+)
  - TA-Lib集成(40+专业指标)
  - 财务指标(PE、PB、ROE等10+)
- **自定义因子构建**:
  - 可视化公式编辑器
  - Python代码编写(语法高亮+代码补全)
  - 因子IC值计算+分层回测验证
- **参数优化引擎**:
  - 网格搜索/随机搜索算法
  - 多目标优化(夏普比率/最大回撤/年化收益)
  - 参数热力图+敏感性分析

### 🔬 回测分析

- **灵活回测配置**:
  - 时间范围精确到日
  - 初始资金10万-1000万可调
  - 精细化交易成本设置(手续费/印花税/滑点)
  - 涨跌停限制、流动性过滤、仓位控制
- **实时进度监控**:
  - WebSocket实时推送进度
  - 交易日志实时打印
  - 支持暂停/恢复/终止
  - 后台回测+桌面通知
- **全面结果展示**:
  - 15+核心指标(累计收益、夏普比率、最大回撤等)
  - 净值曲线、回撤曲线、月度收益图
  - 交易明细表(按盈亏排序/标的筛选)
  - 持仓分布(按行业/标的)
- **策略诊断系统**:
  - 收益分析(TOP5标的贡献、行业分布、稳定性)
  - 风险分析(最大回撤时段、波动率、尾部风险)
  - 过拟合检测(样本外测试、参数敏感性、Walk Forward)
  - 可操作优化建议

### 🔒 安全执行

- **代码沙箱**: RestrictedPython限制危险操作
- **模块白名单**: 仅允许导入安全模块
- **虚拟环境隔离**: 独立Python环境执行自定义代码
- **资源限制**: 限制内存/CPU/执行时间
- **静态检查**: AST分析检测高风险调用

---

## 🚀 快速开始

### 前置要求

- **Python**: 3.9 - 3.11
- **Node.js**: 18+
- **Redis**: 6+
- **数据库**: PostgreSQL 14+ 或 SQLite
- **Git**

### 一键安装

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/qlib-ui.git
cd qlib-ui

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件,配置数据库、Redis等

# 3. 一键安装依赖
make install

# 4. 初始化数据库
make init-db

# 5. 启动服务
make start
```

访问 http://localhost:3000 开始使用!

### 分步安装

<details>
<summary>点击展开详细步骤</summary>

#### 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --port 8000

# 启动Celery Worker(另开终端)
celery -A app.celery_app worker --loglevel=info
```

#### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

</details>

### Docker 部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 访问应用
open http://localhost:3000
```

---

## 📚 文档

- [📋 产品需求文档 (PRD)](docs/QLIB_UI_PRD.md)
- [🏗️ 功能模块划分](docs/FUNCTIONAL_MODULES.md)
- [📁 项目结构说明](docs/PROJECT_STRUCTURE.md)
- [🔌 API接口文档](docs/API_DESIGN.md)
- [💾 数据库设计](docs/DATABASE_SCHEMA.md)
- [👨‍💻 开发指南](docs/DEVELOPMENT_GUIDE.md)
- [🚀 部署指南](docs/DEPLOYMENT_GUIDE.md)

### 模块文档

每个功能模块都有独立的 `Claude.md` 文档:

- [模块1: 用户引导](backend/app/modules/user_onboarding/Claude.md)
- [模块2: 数据管理](backend/app/modules/data_management/Claude.md)
- [模块3: 策略构建](backend/app/modules/strategy_builder/Claude.md)
- [模块4: 回测分析](backend/app/modules/backtest_analysis/Claude.md)
- [模块5: 任务调度](backend/app/modules/task_scheduling/Claude.md)
- [模块6: 代码安全](backend/app/modules/code_security/Claude.md)

---

## 🛠️ 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| [Python](https://www.python.org/) | 3.9+ | 编程语言 |
| [FastAPI](https://fastapi.tiangolo.com/) | 0.100+ | Web框架 |
| [Qlib](https://github.com/microsoft/qlib) | 0.8+ | 量化框架 |
| [TA-Lib](https://ta-lib.org/) | Latest | 技术指标 |
| [Celery](https://docs.celeryq.dev/) | 5.3+ | 异步任务队列 |
| [Redis](https://redis.io/) | 6+ | 缓存&消息队列 |
| [PostgreSQL](https://www.postgresql.org/) | 14+ | 关系数据库 |
| [SQLAlchemy](https://www.sqlalchemy.org/) | 2.0+ | ORM |
| [Pydantic](https://docs.pydantic.dev/) | 2.0+ | 数据验证 |
| [pytest](https://pytest.org/) | Latest | 测试框架 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| [TypeScript](https://www.typescriptlang.org/) | 5.0+ | 编程语言 |
| [React](https://react.dev/) | 18+ | UI框架 |
| [Vite](https://vitejs.dev/) | 4+ | 构建工具 |
| [Zustand](https://zustand-demo.pmnd.rs/) | Latest | 状态管理 |
| [React Query](https://tanstack.com/query/) | 4+ | 服务端状态 |
| [React Router](https://reactrouter.com/) | 6+ | 路由 |
| [Ant Design](https://ant.design/) | 5+ | UI组件库 |
| [ECharts](https://echarts.apache.org/) | 5+ | 图表库 |
| [ReactFlow](https://reactflow.dev/) | 11+ | 流程图 |
| [Tailwind CSS](https://tailwindcss.com/) | 3+ | CSS框架 |
| [Vitest](https://vitest.dev/) | Latest | 测试框架 |

---

## 🗂️ 项目结构

```
qlib-ui/
├── backend/            # 后端代码(FastAPI + Qlib)
│   ├── app/
│   │   ├── modules/    # 7大功能模块
│   │   └── main.py     # 应用入口
│   └── tests/          # 后端测试
├── frontend/           # 前端代码(React + TypeScript)
│   ├── src/
│   │   ├── modules/    # 5大功能模块
│   │   └── App.tsx     # 应用入口
│   └── tests/          # 前端测试
├── tests/e2e/          # E2E测试
├── docs/               # 项目文档
├── infrastructure/     # 基础设施(Docker, K8s)
└── shared/             # 前后端共享代码
```

详见 [项目结构文档](docs/PROJECT_STRUCTURE.md)

---

## 📈 开发路线图

### Phase 1: MVP核心闭环 (4-6周) ✅ 进行中

- [x] 项目架构设计
- [x] 功能模块划分
- [ ] 数据导入(Qlib + 本地文件)
- [ ] 策略模板系统(3-5个经典模板)
- [ ] 策略逻辑编辑器(基础节点)
- [ ] 回测配置+执行
- [ ] 回测结果展示(核心指标+基础图表)
- [ ] UI基础布局

### Phase 2: 功能增强 (4-6周)

- [ ] 完整数据可视化
- [ ] TA-Lib指标集成(40+)
- [ ] 参数优化引擎
- [ ] 策略诊断系统
- [ ] 自定义因子构建
- [ ] 新手引导+帮助系统

### Phase 3: 优化与测试 (2-4周)

- [ ] 性能优化
- [ ] 测试覆盖率≥80%
- [ ] 文档完善
- [ ] Docker镜像构建
- [ ] CI/CD流程

### Phase 4: 未来扩展

- [ ] 模拟交易部署
- [ ] 实盘接口对接
- [ ] 策略社区(分享/评价)
- [ ] AI辅助策略生成
- [ ] 移动端适配

---

## 🧪 测试

```bash
# 运行所有测试
make test

# 后端测试
make test-backend
# 或
cd backend && pytest

# 前端测试
make test-frontend
# 或
cd frontend && npm test

# E2E测试
make test-e2e

# 测试覆盖率报告
make coverage
```

---

## 🤝 贡献

我们欢迎所有形式的贡献! 请参阅 [贡献指南](CONTRIBUTING.md)

### 如何贡献

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### Commit 规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: 新功能
fix: Bug修复
docs: 文档更新
style: 代码格式(不影响功能)
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 📊 项目统计

![GitHub Stars](https://img.shields.io/github/stars/your-org/qlib-ui?style=social)
![GitHub Forks](https://img.shields.io/github/forks/your-org/qlib-ui?style=social)
![GitHub Issues](https://img.shields.io/github/issues/your-org/qlib-ui)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/your-org/qlib-ui)

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

---

## 🙏 致谢

- [Qlib](https://github.com/microsoft/qlib) - 微软开源的量化投资框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [React](https://react.dev/) - 用于构建用户界面的JavaScript库
- 所有贡献者和支持者!

---

## 📞 联系我们

- **Issues**: [GitHub Issues](https://github.com/your-org/qlib-ui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/qlib-ui/discussions)
- **Email**: qlib-ui@example.com

---

<div align="center">

**让量化投资研究触手可及**

Made with ❤️ by Qlib-UI Team

[⬆ 回到顶部](#qlib-ui-量化投资研究平台图形化界面)

</div>
