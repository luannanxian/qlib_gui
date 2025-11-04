# Qlib-UI 项目结构文档

## 项目目录树

```
qlib-ui/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── main.py             # FastAPI应用入口
│   │   ├── modules/            # 功能模块
│   │   │   ├── user_onboarding/    # 模块1: 用户引导
│   │   │   ├── data_management/    # 模块2: 数据管理
│   │   │   ├── strategy_builder/   # 模块3: 策略构建
│   │   │   ├── backtest_analysis/  # 模块4: 回测分析
│   │   │   ├── task_scheduling/    # 模块5: 任务调度
│   │   │   ├── code_security/      # 模块6: 代码安全
│   │   │   └── common/             # 公共模块
│   │   └── config.py           # 配置文件
│   ├── requirements.txt        # Python依赖
│   └── pytest.ini              # pytest配置
│
├── frontend/                   # 前端代码
│   ├── public/                 # 静态资源
│   ├── src/
│   │   ├── modules/            # 功能模块
│   │   │   ├── user-onboarding/    # 模块1: 用户引导
│   │   │   ├── data-management/    # 模块2: 数据管理
│   │   │   ├── strategy-builder/   # 模块3: 策略构建
│   │   │   ├── backtest-analysis/  # 模块4: 回测分析
│   │   │   └── ui-interaction/     # 模块7: UI交互
│   │   ├── components/         # 共享组件
│   │   ├── hooks/              # 共享Hooks
│   │   ├── utils/              # 工具函数
│   │   ├── types/              # TypeScript类型
│   │   ├── styles/             # 全局样式
│   │   ├── assets/             # 资源文件
│   │   ├── App.tsx             # 应用入口
│   │   └── main.tsx            # 主入口
│   ├── package.json            # npm依赖
│   ├── tsconfig.json           # TypeScript配置
│   └── vite.config.ts          # Vite配置
│
├── tests/                      # 测试代码
│   ├── backend/                # 后端测试
│   │   ├── unit/               # 单元测试
│   │   └── integration/        # 集成测试
│   ├── frontend/               # 前端测试
│   │   ├── unit/               # 单元测试
│   │   └── integration/        # 集成测试
│   └── e2e/                    # E2E测试
│
├── shared/                     # 前后端共享代码
│   ├── types/                  # 共享类型定义
│   ├── utils/                  # 共享工具函数
│   └── constants/              # 共享常量
│
├── infrastructure/             # 基础设施
│   ├── docker/                 # Docker相关
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── docker-compose.yml
│   ├── k8s/                    # Kubernetes配置
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── scripts/                # 脚本
│       ├── start.sh            # 启动脚本
│       ├── test.sh             # 测试脚本
│       └── deploy.sh           # 部署脚本
│
├── docs/                       # 文档
│   ├── QLIB_UI_PRD.md          # 产品需求文档
│   ├── FUNCTIONAL_MODULES.md   # 功能模块划分
│   ├── PROJECT_STRUCTURE.md    # 项目结构文档(本文件)
│   ├── API_DESIGN.md           # API设计文档
│   ├── DATABASE_SCHEMA.md      # 数据库设计
│   ├── DEVELOPMENT_GUIDE.md    # 开发指南
│   └── DEPLOYMENT_GUIDE.md     # 部署指南
│
├── .gitignore                  # Git忽略文件
├── .env.example                # 环境变量示例
├── README.md                   # 项目说明
├── Makefile                    # Make命令
└── LICENSE                     # 许可证
```

## 模块目录结构规范

### 后端模块标准结构

```
module_name/
├── models/              # 数据模型(ORM/Pydantic)
│   └── *.py
├── services/            # 业务逻辑服务
│   └── *_service.py
├── api/                 # API端点(FastAPI路由)
│   └── *_api.py
├── schemas/             # Pydantic Schemas(请求/响应)
│   └── *_schemas.py
├── utils/               # 模块内工具函数
│   └── *.py
├── tests/               # 模块测试
│   └── test_*.py
├── __init__.py          # 模块初始化
└── Claude.md            # 模块说明文档
```

### 前端模块标准结构

```
module-name/
├── components/          # UI组件
│   ├── ComponentName.tsx
│   └── ComponentName.module.css
├── hooks/               # React Hooks
│   └── use*.ts
├── store/               # 状态管理(Zustand/Redux)
│   └── *Store.ts
├── api/                 # API调用
│   └── *Api.ts
├── types/               # TypeScript类型
│   └── index.ts
├── utils/               # 工具函数
│   └── *.ts
├── constants/           # 常量
│   └── *.ts
├── tests/               # 组件测试
│   └── *.test.tsx
└── Claude.md            # 模块说明文档
```

## 命名规范

### 文件命名
- **Python**: 小写+下划线 `user_service.py`
- **TypeScript组件**: PascalCase `UserProfile.tsx`
- **TypeScript非组件**: camelCase `useAuth.ts`, `api Client.ts`
- **CSS模块**: 与组件同名 `UserProfile.module.css`
- **测试文件**: `test_*.py` 或 `*.test.tsx`

### 变量命名
- **Python变量/函数**: snake_case
- **Python类**: PascalCase
- **TypeScript变量/函数**: camelCase
- **TypeScript类/接口**: PascalCase
- **常量**: UPPER_SNAKE_CASE

### API端点命名
- RESTful风格,使用名词复数
- 示例: `/api/data/datasets`, `/api/strategy/templates`
- 操作: GET(查询), POST(创建), PUT(更新), DELETE(删除)

## 技术栈对应

### 后端 (backend/)
- **语言**: Python 3.9+
- **框架**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **数据库**: PostgreSQL / SQLite
- **缓存**: Redis
- **任务队列**: Celery
- **测试**: pytest, pytest-cov
- **量化**: Qlib, TA-Lib, pandas, numpy

### 前端 (frontend/)
- **语言**: TypeScript
- **框架**: React 18+ / Next.js 13+
- **构建**: Vite
- **状态**: Zustand + React Query
- **路由**: React Router v6
- **UI库**: Ant Design / shadcn/ui
- **图表**: ECharts, Recharts, TradingView
- **流程图**: ReactFlow
- **测试**: Vitest, React Testing Library

### 基础设施 (infrastructure/)
- **容器**: Docker, Docker Compose
- **编排**: Kubernetes (可选)
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana (可选)
- **日志**: ELK Stack (可选)

## 环境配置

### 开发环境要求
- Python 3.9-3.11
- Node.js 18+
- Redis 6+
- PostgreSQL 14+ / SQLite
- Git

### 环境变量 (.env)
```bash
# 后端配置
DATABASE_URL=postgresql://user:password@localhost:5432/qlib_ui
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
QLIB_DATA_DIR=./data/qlib

# 前端配置
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/ws

# 任务队列
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## 启动命令

### 一键启动(推荐)
```bash
make start  # 同时启动前后端
```

### 分别启动

#### 后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 前端
```bash
cd frontend
npm install
npm run dev  # 默认端口3000
```

#### Celery Worker
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

## 数据存储位置

```
qlib-ui/
├── data/                   # 数据目录
│   ├── qlib/               # Qlib数据
│   ├── uploads/            # 用户上传文件
│   └── datasets/           # 处理后数据集
├── results/                # 回测结果
│   ├── backtests/          # 回测输出
│   └── optimizations/      # 参数优化结果
├── logs/                   # 日志文件
│   ├── backend/            # 后端日志
│   └── celery/             # Celery日志
└── cache/                  # 缓存目录
    └── temp/               # 临时文件
```

## 开发工作流

### 1. 获取代码
```bash
git clone <repository-url>
cd qlib-ui
```

### 2. 环境设置
```bash
cp .env.example .env
# 编辑.env文件配置环境变量
```

### 3. 安装依赖
```bash
make install  # 同时安装前后端依赖
```

### 4. 运行测试
```bash
make test     # 运行所有测试
make test-backend   # 仅后端测试
make test-frontend  # 仅前端测试
```

### 5. 代码检查
```bash
make lint     # 代码风格检查
make format   # 代码格式化
```

### 6. 构建生产版本
```bash
make build    # 构建前后端
```

## 部署方式

### Docker Compose (推荐)
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f infrastructure/k8s/
```

### 传统部署
参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 模块间通信

### 前端 → 后端
- REST API (HTTP/HTTPS)
- WebSocket (实时数据)

### 后端模块间
- 直接函数调用 (同进程)
- Celery任务队列 (异步任务)
- Redis Pub/Sub (事件通知)

### 数据流
```
用户操作 → 前端UI → API请求 → 后端路由 → 服务层 → 数据层 → 数据库/Qlib
         ↑                                               ↓
         ← WebSocket推送 ← Celery任务 ← 业务逻辑 ← 数据处理 ←
```

## 扩展指南

### 添加新模块

#### 后端
1. 在 `backend/app/modules/` 创建模块目录
2. 按标准结构创建文件
3. 在 `main.py` 注册路由
4. 编写 `Claude.md` 文档
5. 添加测试

#### 前端
1. 在 `frontend/src/modules/` 创建模块目录
2. 按标准结构创建文件
3. 在路由中注册页面
4. 编写 `Claude.md` 文档
5. 添加测试

### 添加新API
1. 定义Pydantic Schema
2. 实现Service层逻辑
3. 创建API路由
4. 编写单元测试
5. 更新API文档

## 文档更新规范

每个模块的 `Claude.md` 应包含:
1. 模块概述
2. 核心职责
3. 目录结构
4. 核心组件/函数
5. API端点(后端)
6. 数据模型
7. 技术要点
8. 依赖关系
9. 开发优先级
10. 测试要点
11. 注意事项

## 相关文档

- [PRD文档](QLIB_UI_PRD.md) - 产品需求
- [功能模块划分](FUNCTIONAL_MODULES.md) - 详细的模块设计
- [API设计文档](API_DESIGN.md) - API规范
- [数据库设计](DATABASE_SCHEMA.md) - 数据库表结构
- [开发指南](DEVELOPMENT_GUIDE.md) - 开发流程和规范
- [部署指南](DEPLOYMENT_GUIDE.md) - 部署和运维

## 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### Commit消息规范
使用 Conventional Commits:
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式(不影响代码运行)
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例: `feat(data-management): add CSV import validation`

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](../LICENSE) 文件
