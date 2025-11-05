# Qlib-UI Frontend

量化投资可视化平台 - 前端应用

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 5
- **UI库**: Ant Design 5
- **状态管理**: Zustand + React Query
- **路由**: React Router v6
- **图表**: ECharts, Recharts, Lightweight Charts
- **Mock API**: MSW (Mock Service Worker)

## 项目结构

```
frontend/
├── src/
│   ├── api/                  # API客户端
│   ├── components/           # 共享组件
│   ├── modules/              # 业务模块
│   ├── hooks/                # 自定义Hooks
│   ├── store/                # 全局状态
│   ├── types/                # TypeScript类型
│   ├── utils/                # 工具函数
│   ├── styles/               # 全局样式
│   ├── router/               # 路由配置
│   ├── mocks/                # Mock API
│   └── main.tsx              # 应用入口
├── public/                   # 静态资源
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 开发指南

### 环境要求

- Node.js 18+
- npm 9+ / pnpm 8+

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 类型检查

```bash
npm run type-check
```

### 运行测试

```bash
npm test
```

## 环境配置

复制 `.env.example` 为 `.env`:

```bash
cp .env.example .env
```

配置项说明:

- `VITE_API_BASE_URL`: 后端API地址 (默认: http://localhost:8000)
- `VITE_WS_BASE_URL`: WebSocket地址 (默认: ws://localhost:8000/ws)
- `VITE_ENABLE_MOCK`: 是否启用Mock API (开发环境)

## 开发状态

### ✅ 已完成

- [x] 项目初始化
- [x] TypeScript配置
- [x] Vite配置
- [x] API类型定义
- [x] API客户端 (Axios)
- [x] 全局状态管理 (Zustand)
- [x] 路由配置
- [x] 基础样式

### 🚧 进行中

- [ ] 数据管理模块
- [ ] 用户引导模块
- [ ] 策略构建模块 (Mock)
- [ ] 回测分析模块 (Mock)

### 📋 待开发

- [ ] 布局组件
- [ ] 图表组件
- [ ] 表单组件
- [ ] Mock API实现
- [ ] 单元测试
- [ ] E2E测试

## 文档

- [前端架构设计](../docs/FRONTEND_ARCHITECTURE.md)
- [后端API分析](../docs/BACKEND_API_ANALYSIS.md)
- [项目结构文档](../docs/PROJECT_STRUCTURE.md)
- [PRD文档](../docs/QLIB_UI_PRD.md)

## 脚本命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run lint` | 代码检查 |
| `npm run type-check` | TypeScript类型检查 |
| `npm test` | 运行测试 |
| `npm run test:ui` | 测试UI界面 |
| `npm run test:coverage` | 测试覆盖率 |

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License
