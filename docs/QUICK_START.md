# Qlib-UI 快速开始指南

## 📚 阅读顺序

如果你是第一次接触这个项目,建议按以下顺序阅读文档:

1. **[README.md](../README.md)** ⭐ 必读
   - 项目简介和功能特性
   - 快速开始步骤
   - 技术栈概览

2. **[QLIB_UI_PRD.md](QLIB_UI_PRD.md)** ⭐ 必读
   - 完整的产品需求文档
   - 用户画像和使用场景
   - 详细功能需求

3. **[FUNCTIONAL_MODULES.md](FUNCTIONAL_MODULES.md)** ⭐ 必读
   - 7大功能模块详细设计
   - API接口规范
   - 数据模型定义

4. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)**
   - 项目目录结构说明
   - 命名规范
   - 开发工作流

5. **[DIRECTORY_SETUP_COMPLETE.md](DIRECTORY_SETUP_COMPLETE.md)**
   - 目录设置完成情况
   - 下一步开发建议

6. **模块文档 (Claude.md)**
   - 每个功能模块的详细说明
   - 根据需要查阅特定模块

## 🚀 5分钟快速上手

### 1. 环境准备

```bash
# 检查环境
python --version  # 需要 3.9+
node --version    # 需要 18+
redis-cli ping    # 确认 Redis 运行

# 克隆项目
git clone <repository-url>
cd qlib-ui
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件,至少配置以下项:
# DATABASE_URL=sqlite:///./qlib_ui.db  (开发环境用SQLite即可)
# REDIS_URL=redis://localhost:6379/0
# SECRET_KEY=your-secret-key-here
```

### 3. 一键安装与启动

```bash
# 安装所有依赖
make install

# 初始化数据库
make init-db

# 启动服务(前后端并行启动)
make start
```

等待服务启动后:
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- API文档: http://localhost:8000/docs

### 4. 验证安装

```bash
# 运行测试
make test

# 检查代码质量
make lint
```

## 📁 项目结构概览

```
qlib-ui/
├── backend/            # 后端(Python + FastAPI)
│   └── app/modules/    # 7个功能模块
├── frontend/           # 前端(React + TypeScript)
│   └── src/modules/    # 5个功能模块
├── tests/              # 测试代码
├── docs/               # 项目文档
├── infrastructure/     # Docker/K8s配置
├── data/               # 数据存储
├── results/            # 回测结果
└── logs/               # 日志文件
```

## 🧩 7大功能模块

### 后端模块

1. **用户引导与模式管理** ([文档](../backend/app/modules/user_onboarding/Claude.md))
   - 新手/专家模式切换
   - 引导流程管理

2. **数据管理** ([文档](../backend/app/modules/data_management/Claude.md))
   - 数据导入(Qlib/本地文件)
   - 数据预处理
   - 数据可视化

3. **策略构建** ([文档](../backend/app/modules/strategy_builder/Claude.md))
   - 策略模板
   - 指标组件库(60+)
   - 策略逻辑编辑
   - 参数优化

4. **回测分析** ([文档](../backend/app/modules/backtest_analysis/Claude.md))
   - 回测执行
   - 结果展示(15+指标)
   - 策略诊断

5. **任务调度** ([文档](../backend/app/modules/task_scheduling/Claude.md))
   - 任务队列管理
   - 系统配置
   - 日志监控

6. **代码安全** ([文档](../backend/app/modules/code_security/Claude.md))
   - 虚拟环境隔离
   - 代码安全检查
   - 沙箱执行

7. **公共模块** ([文档](../backend/app/modules/common/Claude.md))
   - 基础模型
   - 工具函数
   - 中间件

### 前端模块

1. **用户引导UI** ([文档](../frontend/src/modules/user-onboarding/Claude.md))
2. **数据管理UI** ([文档](../frontend/src/modules/data-management/Claude.md))
3. **策略构建UI** ([文档](../frontend/src/modules/strategy-builder/Claude.md))
4. **回测分析UI** ([文档](../frontend/src/modules/backtest-analysis/Claude.md))
5. **UI交互** ([文档](../frontend/src/modules/ui-interaction/Claude.md))

## 🛠️ 常用命令

```bash
# 开发
make start              # 启动前后端
make start-backend      # 仅启动后端
make start-frontend     # 仅启动前端
make start-celery       # 启动Celery Worker

# 测试
make test               # 运行所有测试
make test-backend       # 后端测试
make test-frontend      # 前端测试
make coverage           # 生成覆盖率报告

# 代码质量
make lint               # 代码检查
make format             # 代码格式化

# 数据库
make init-db            # 初始化数据库
make migrate            # 创建迁移
make migrate-up         # 应用迁移

# Docker
make docker-up          # 启动容器
make docker-down        # 停止容器

# 清理
make clean              # 清理临时文件
make clean-cache        # 清理缓存

# 帮助
make help               # 查看所有命令
```

## 🔧 开发工具推荐

### VSCode 扩展
- **Python**: Python, Pylance
- **TypeScript**: ESLint, Prettier
- **其他**: GitLens, Docker, REST Client

### 浏览器扩展
- React Developer Tools
- Redux DevTools

## 📖 学习资源

### 技术栈文档
- [FastAPI](https://fastapi.tiangolo.com/)
- [Qlib](https://qlib.readthedocs.io/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [ECharts](https://echarts.apache.org/)

### 项目相关
- PRD文档: 了解产品需求
- 功能模块文档: 了解系统设计
- Claude.md: 了解各模块实现

## ❓ 常见问题

### Q1: 启动后无法访问前端页面?
**A**: 检查端口是否被占用,可修改 .env 中的 FRONTEND_PORT

### Q2: 后端连接数据库失败?
**A**: 检查 DATABASE_URL 配置,开发环境建议使用SQLite

### Q3: Celery任务执行失败?
**A**: 确认Redis已启动,检查 CELERY_BROKER_URL 配置

### Q4: 如何添加新的策略模板?
**A**: 参考 `backend/app/modules/strategy_builder/templates/` 目录

### Q5: 前端如何调用后端API?
**A**: 查看 `frontend/src/modules/*/api/` 目录的示例代码

## 🤝 参与贡献

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 📞 获取帮助

- **GitHub Issues**: 报告Bug或提出功能请求
- **GitHub Discussions**: 技术讨论和问答
- **Email**: qlib-ui@example.com

## 🎯 下一步

完成快速开始后,建议:

1. **运行示例** - 尝试导入示例数据,运行内置策略模板
2. **阅读模块文档** - 深入了解感兴趣的模块
3. **编写第一个功能** - 从简单的功能开始实践
4. **运行测试** - 学习如何编写测试用例
5. **参与贡献** - 提交你的第一个PR

---

**Happy Coding!** 🚀
