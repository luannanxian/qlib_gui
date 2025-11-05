# 前端组件架构设计

**生成时间**: 2025-01-05
**技术栈**: React 18 + TypeScript + Vite + Ant Design + Zustand + React Query

---

## 1. 整体架构

```
frontend/
├── public/                       # 静态资源
│   ├── favicon.ico
│   └── assets/                   # 图片、图标等
│
├── src/
│   ├── main.tsx                  # 应用入口
│   ├── App.tsx                   # 根组件
│   ├── vite-env.d.ts             # Vite类型声明
│   │
│   ├── modules/                  # 业务模块 (按功能划分)
│   │   ├── data-management/      # 数据管理模块
│   │   ├── user-onboarding/      # 用户引导模块
│   │   ├── strategy-builder/     # 策略构建模块 (Mock)
│   │   ├── backtest-analysis/    # 回测分析模块 (Mock)
│   │   └── ui-interaction/       # UI交互模块
│   │
│   ├── components/               # 共享组件
│   │   ├── layout/               # 布局组件
│   │   ├── charts/               # 图表组件
│   │   ├── forms/                # 表单组件
│   │   └── common/               # 通用组件
│   │
│   ├── hooks/                    # 自定义Hooks
│   │   ├── useDatasets.ts
│   │   ├── useUserMode.ts
│   │   └── useDebounce.ts
│   │
│   ├── api/                      # API客户端
│   │   ├── client.ts             # Axios配置
│   │   ├── datasets.ts           # 数据集API
│   │   ├── userMode.ts           # 用户模式API
│   │   └── mock/                 # Mock API (MSW)
│   │
│   ├── store/                    # 全局状态管理 (Zustand)
│   │   ├── useUserStore.ts
│   │   ├── useAppStore.ts
│   │   └── index.ts
│   │
│   ├── types/                    # TypeScript类型
│   │   ├── api.ts                # API类型
│   │   ├── models.ts             # 业务模型类型
│   │   └── index.ts
│   │
│   ├── utils/                    # 工具函数
│   │   ├── format.ts             # 格式化工具
│   │   ├── validation.ts         # 验证工具
│   │   └── constants.ts          # 常量定义
│   │
│   ├── styles/                   # 全局样式
│   │   ├── global.css
│   │   ├── variables.css         # CSS变量
│   │   └── theme.ts              # Ant Design主题配置
│   │
│   └── router/                   # 路由配置
│       ├── index.tsx
│       └── routes.tsx
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
└── README.md
```

---

## 2. 技术栈选型

### 2.1 核心框架

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **React** | 18.3+ | UI框架 | 组件化、生态完善 |
| **TypeScript** | 5.0+ | 类型系统 | 类型安全、开发体验 |
| **Vite** | 5.0+ | 构建工具 | 快速启动、HMR |

### 2.2 UI库

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **Ant Design** | 5.x | 组件库 | 企业级、中文友好 |
| **Ant Design Pro Components** | 2.x | 高级组件 | ProTable、ProForm等 |
| **@ant-design/icons** | 5.x | 图标库 | 与Ant Design配套 |

### 2.3 图表库

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **ECharts** | 5.x | 通用图表 | 功能强大、性能好 |
| **Lightweight Charts** | 4.x | 金融K线图 | TradingView出品 |
| **Recharts** | 2.x | React图表 | 声明式、易用 |

### 2.4 状态管理

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **Zustand** | 4.x | 全局状态 | 轻量、简单 |
| **React Query** | 5.x | 服务端状态 | 缓存、重试、乐观更新 |

### 2.5 路由

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **React Router** | 6.x | 路由管理 | 标准方案 |

### 2.6 工具库

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **Axios** | 1.x | HTTP客户端 | 拦截器、取消请求 |
| **Day.js** | 1.x | 日期处理 | 轻量、API友好 |
| **Lodash-es** | 4.x | 工具函数 | 防抖、节流等 |
| **Zod** | 3.x | 运行时验证 | 类型安全验证 |

### 2.7 Mock工具

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **MSW** | 2.x | Mock API | Service Worker拦截 |

### 2.8 测试工具

| 技术 | 版本 | 用途 | 理由 |
|------|------|------|------|
| **Vitest** | 1.x | 单元测试 | Vite原生支持 |
| **@testing-library/react** | 14.x | 组件测试 | 用户行为测试 |
| **@testing-library/user-event** | 14.x | 用户交互 | 模拟真实操作 |

---

## 3. 模块架构设计

### 3.1 数据管理模块 (data-management)

```
data-management/
├── components/
│   ├── DatasetList/              # 数据集列表
│   │   ├── index.tsx
│   │   ├── DatasetTable.tsx      # 表格组件
│   │   ├── FilterBar.tsx         # 过滤栏
│   │   └── SearchInput.tsx       # 搜索框
│   │
│   ├── DatasetForm/              # 数据集表单
│   │   ├── index.tsx
│   │   ├── BasicInfo.tsx         # 基本信息
│   │   ├── SourceSelector.tsx    # 数据源选择
│   │   └── MetadataEditor.tsx    # 元数据编辑
│   │
│   ├── DataImport/               # 数据导入 (Mock)
│   │   ├── index.tsx
│   │   ├── FileUploader.tsx      # 文件上传
│   │   ├── ProgressTracker.tsx   # 进度追踪
│   │   └── PreviewTable.tsx      # 数据预览
│   │
│   └── DataVisualization/        # 数据可视化 (Mock)
│       ├── index.tsx
│       ├── KLineChart.tsx        # K线图
│       ├── IndicatorChart.tsx    # 指标图
│       └── ChartControls.tsx     # 图表控制
│
├── hooks/
│   ├── useDatasets.ts            # 数据集CRUD
│   ├── useDataImport.ts          # 数据导入 (Mock)
│   └── useChartData.ts           # 图表数据
│
├── api/
│   ├── datasets.ts               # 数据集API
│   └── dataImport.ts             # 导入API (Mock)
│
├── types/
│   └── index.ts                  # 模块类型定义
│
└── pages/
    ├── DatasetListPage.tsx       # 列表页
    ├── DatasetDetailPage.tsx     # 详情页
    └── DataImportPage.tsx        # 导入页
```

#### 核心组件设计

**DatasetList 组件**
```typescript
interface DatasetListProps {
  mode: 'beginner' | 'expert';  // 根据用户模式调整UI复杂度
}

// 功能:
// - 分页表格展示数据集
// - 搜索、过滤 (source, status)
// - 批量操作 (删除)
// - 创建、编辑、删除操作
// - 软删除提示
```

**DatasetForm 组件**
```typescript
interface DatasetFormProps {
  initialValues?: Partial<DatasetCreate>;
  onSubmit: (values: DatasetCreate) => Promise<void>;
  mode?: 'create' | 'edit';
}

// 功能:
// - 表单验证 (前端 + 后端)
// - 数据源选择: LOCAL / QLIB / THIRDPARTY
// - 文件路径输入 (带路径遍历验证)
// - 元数据编辑器 (JSON编辑器)
// - 保存、取消操作
```

### 3.2 用户引导模块 (user-onboarding)

```
user-onboarding/
├── components/
│   ├── ModeSwitch/               # 模式切换
│   │   ├── index.tsx
│   │   └── ModeSwitchButton.tsx
│   │
│   ├── GuideTour/                # 引导教程
│   │   ├── index.tsx
│   │   ├── TourStep.tsx
│   │   └── tourSteps.ts          # 步骤配置
│   │
│   ├── PreferencesPanel/         # 偏好设置
│   │   ├── index.tsx
│   │   ├── LanguageSelector.tsx
│   │   └── ThemeSelector.tsx
│   │
│   └── BeginnerHelp/             # 初学者帮助
│       ├── index.tsx
│       ├── Tooltips.tsx          # 工具提示
│       └── HelpDrawer.tsx        # 帮助抽屉
│
├── hooks/
│   ├── useUserMode.ts            # 模式管理
│   ├── usePreferences.ts         # 偏好设置
│   └── useTour.ts                # 引导教程
│
├── api/
│   └── userMode.ts               # 用户模式API
│
└── store/
    └── userStore.ts              # 用户状态
```

#### 核心组件设计

**ModeSwitch 组件**
```typescript
interface ModeSwitchProps {
  userId: string;
  onChange?: (mode: UserMode) => void;
}

// 功能:
// - 顶部导航栏的切换开关
// - 初学者模式: 显示帮助提示、简化操作
// - 专家模式: 隐藏提示、展示高级功能
// - 切换时确认对话框
// - 自动保存到后端
```

**GuideTour 组件**
```typescript
interface GuideTourProps {
  steps: TourStep[];
  onComplete?: () => void;
  autoStart?: boolean;
}

// 功能:
// - 使用 Ant Design Tour 组件
// - 多步骤引导
// - 支持跳过、上一步、下一步
// - 完成后标记为已完成
// - 可重新触发
```

### 3.3 策略构建模块 (strategy-builder) - Mock

```
strategy-builder/
├── components/
│   ├── StrategyList/             # 策略列表
│   │   └── index.tsx
│   │
│   ├── TemplateSelector/         # 模板选择器
│   │   ├── index.tsx
│   │   ├── TemplateCard.tsx      # 模板卡片
│   │   └── templates.ts          # 硬编码模板数据
│   │
│   ├── FactorLibrary/            # 因子库
│   │   ├── index.tsx
│   │   ├── FactorTree.tsx        # 因子树
│   │   └── factors.ts            # 硬编码因子数据
│   │
│   └── StrategyEditor/           # 策略编辑器
│       ├── index.tsx
│       ├── CodeEditor.tsx        # 代码编辑器 (Monaco)
│       ├── VisualEditor.tsx      # 可视化编辑器 (ReactFlow)
│       └── PreviewPanel.tsx      # 预览面板
│
├── hooks/
│   ├── useStrategies.ts          # 策略CRUD (Mock)
│   ├── useTemplates.ts           # 模板列表 (Mock)
│   └── useFactors.ts             # 因子库 (Mock)
│
└── api/
    └── mock.ts                   # Mock API
```

#### 核心组件设计 (Mock)

**TemplateSelector 组件**
```typescript
interface TemplateSelectorProps {
  onSelect: (template: StrategyTemplate) => void;
}

// 功能:
// - 硬编码10+模板: 双均线、MACD、布林带等
// - 卡片式展示 (名称、描述、标签)
// - 搜索、分类过滤
// - 点击预览模板代码
```

**StrategyEditor 组件**
```typescript
interface StrategyEditorProps {
  mode: 'code' | 'visual';
  initialCode?: string;
  onSave: (code: string) => void;
}

// 功能:
// - 代码模式: Monaco Editor (Python语法高亮)
// - 可视化模式: ReactFlow (拖拽节点)
// - 保存到 localStorage (暂无后端)
// - 基本语法检查
```

### 3.4 回测分析模块 (backtest-analysis) - Mock

```
backtest-analysis/
├── components/
│   ├── BacktestConfig/           # 回测配置
│   │   ├── index.tsx
│   │   ├── ParameterForm.tsx     # 参数表单
│   │   └── DatasetSelector.tsx   # 数据集选择
│   │
│   ├── BacktestResults/          # 回测结果
│   │   ├── index.tsx
│   │   ├── MetricsPanel.tsx      # 指标面板
│   │   ├── EquityCurve.tsx       # 权益曲线
│   │   ├── TradeList.tsx         # 交易列表
│   │   └── DrawdownChart.tsx     # 回撤图
│   │
│   └── Diagnosis/                # 诊断分析
│       ├── index.tsx
│       ├── IssueList.tsx         # 问题列表
│       └── Suggestions.tsx       # 优化建议
│
├── hooks/
│   ├── useBacktest.ts            # 回测CRUD (Mock)
│   ├── useResults.ts             # 结果查询 (Mock)
│   └── useDiagnosis.ts           # 诊断分析 (Mock)
│
└── api/
    └── mock.ts                   # Mock API
```

#### 核心组件设计 (Mock)

**BacktestConfig 组件**
```typescript
interface BacktestConfigProps {
  strategyId: string;
  onSubmit: (config: BacktestConfig) => Promise<void>;
}

// 功能:
// - 时间范围选择
// - 初始资金、手续费率等参数
// - 数据集选择
// - 提交后返回Mock任务ID
```

**BacktestResults 组件**
```typescript
interface BacktestResultsProps {
  backtestId: string;
}

// 功能:
// - 显示模拟指标: 收益率、夏普比率、最大回撤等
// - 权益曲线图 (ECharts折线图)
// - 交易列表表格
// - 前端生成模拟数据
```

### 3.5 UI交互模块 (ui-interaction)

```
ui-interaction/
├── components/
│   ├── Layout/                   # 布局组件
│   │   ├── MainLayout.tsx        # 主布局
│   │   ├── Sidebar.tsx           # 侧边栏
│   │   ├── Header.tsx            # 顶部导航
│   │   └── Footer.tsx            # 底部
│   │
│   ├── Navigation/               # 导航组件
│   │   ├── TabNavigation.tsx     # 标签导航
│   │   └── Breadcrumb.tsx        # 面包屑
│   │
│   └── Feedback/                 # 反馈组件
│       ├── Loading.tsx           # 加载状态
│       ├── ErrorBoundary.tsx     # 错误边界
│       └── Notification.tsx      # 通知组件
│
└── hooks/
    ├── useNavigation.ts          # 导航逻辑
    └── useResponsive.ts          # 响应式布局
```

---

## 4. 共享组件设计

### 4.1 布局组件 (components/layout)

```typescript
// MainLayout.tsx
interface MainLayoutProps {
  children: React.ReactNode;
  mode: 'beginner' | 'expert';
}

// 功能:
// - 固定顶部导航 (Logo, 模式切换, 用户菜单)
// - 可折叠侧边栏 (菜单导航)
// - 主内容区 (children)
// - 底部信息
```

### 4.2 图表组件 (components/charts)

```typescript
// KLineChart.tsx - K线图
interface KLineChartProps {
  data: CandlestickData[];
  indicators?: Indicator[];
  height?: number;
}

// LineChart.tsx - 折线图
interface LineChartProps {
  data: LineData[];
  xField: string;
  yField: string;
  smooth?: boolean;
}

// BarChart.tsx - 柱状图
interface BarChartProps {
  data: BarData[];
  xField: string;
  yField: string;
}
```

### 4.3 表单组件 (components/forms)

```typescript
// JsonEditor.tsx - JSON编辑器
interface JsonEditorProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  height?: number;
}

// FileUpload.tsx - 文件上传
interface FileUploadProps {
  accept: string[];
  maxSize: number;
  onUpload: (file: File) => Promise<void>;
}

// SearchBar.tsx - 搜索栏
interface SearchBarProps {
  placeholder: string;
  onSearch: (value: string) => void;
  debounce?: number;  // 默认300ms
}
```

### 4.4 通用组件 (components/common)

```typescript
// ConfirmDialog.tsx - 确认对话框
interface ConfirmDialogProps {
  title: string;
  content: string;
  onConfirm: () => void;
  onCancel: () => void;
  type?: 'info' | 'warning' | 'danger';
}

// EmptyState.tsx - 空状态
interface EmptyStateProps {
  description: string;
  action?: {
    text: string;
    onClick: () => void;
  };
}

// StatusTag.tsx - 状态标签
interface StatusTagProps {
  status: 'VALID' | 'INVALID' | 'PENDING' | 'PROCESSING';
}
```

---

## 5. 状态管理设计

### 5.1 全局状态 (Zustand)

```typescript
// store/useUserStore.ts
interface UserStore {
  // 状态
  userId: string | null;
  mode: 'BEGINNER' | 'EXPERT';
  preferences: UserPreferences | null;

  // 操作
  setUserId: (id: string) => void;
  setMode: (mode: UserMode) => void;
  setPreferences: (prefs: UserPreferences) => void;
  reset: () => void;
}

// store/useAppStore.ts
interface AppStore {
  // 状态
  theme: 'light' | 'dark';
  language: 'zh-CN' | 'en-US';
  sidebarCollapsed: boolean;

  // 操作
  toggleTheme: () => void;
  setLanguage: (lang: string) => void;
  toggleSidebar: () => void;
}
```

### 5.2 服务端状态 (React Query)

```typescript
// hooks/useDatasets.ts
export function useDatasets(params: DatasetQueryParams) {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: () => fetchDatasets(params),
    staleTime: 5 * 60 * 1000,  // 5分钟缓存
    gcTime: 10 * 60 * 1000,    // 10分钟垃圾回收
  });
}

export function useCreateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      message.success('数据集创建成功');
    },
    onError: (error) => {
      message.error(`创建失败: ${error.message}`);
    },
  });
}
```

---

## 6. 路由设计

```typescript
// router/routes.tsx
const routes = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/datasets" replace />,
      },
      {
        path: 'datasets',
        children: [
          { index: true, element: <DatasetListPage /> },
          { path: 'import', element: <DataImportPage /> },
          { path: ':id', element: <DatasetDetailPage /> },
        ],
      },
      {
        path: 'strategies',
        children: [
          { index: true, element: <StrategyListPage /> },
          { path: 'new', element: <StrategyEditorPage /> },
          { path: ':id/edit', element: <StrategyEditorPage /> },
        ],
      },
      {
        path: 'backtests',
        children: [
          { index: true, element: <BacktestListPage /> },
          { path: 'new', element: <BacktestConfigPage /> },
          { path: ':id/results', element: <BacktestResultsPage /> },
        ],
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
    ],
  },
  {
    path: '/login',
    element: <LoginPage />,  // 待实现
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
];

export default createBrowserRouter(routes);
```

---

## 7. API客户端设计

### 7.1 Axios配置

```typescript
// api/client.ts
import axios from 'axios';
import { message } from 'antd';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加关联ID
    config.headers['X-Correlation-ID'] = crypto.randomUUID();

    // 添加认证Token (待后端实现)
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      message.error('未授权,请重新登录');
      // 跳转到登录页
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      message.error('无权限访问');
    } else if (error.response?.status >= 500) {
      message.error('服务器错误,请稍后重试');
    } else if (error.response?.data?.detail) {
      message.error(error.response.data.detail);
    } else {
      message.error('请求失败');
    }

    return Promise.reject(error);
  }
);
```

### 7.2 API函数封装

```typescript
// api/datasets.ts
import { apiClient } from './client';
import type {
  DatasetCreate,
  DatasetUpdate,
  DatasetResponse,
  DatasetListResponse,
} from '@/types/api';

export const datasetsApi = {
  // 获取列表
  list: async (params: {
    skip?: number;
    limit?: number;
    source?: string;
    status?: string;
    search?: string;
  }): Promise<DatasetListResponse> => {
    const { data } = await apiClient.get<DatasetListResponse>('/api/datasets', { params });
    return data;
  },

  // 获取单个
  get: async (id: string): Promise<DatasetResponse> => {
    const { data } = await apiClient.get<DatasetResponse>(`/api/datasets/${id}`);
    return data;
  },

  // 创建
  create: async (dataset: DatasetCreate): Promise<DatasetResponse> => {
    const { data } = await apiClient.post<DatasetResponse>('/api/datasets', dataset);
    return data;
  },

  // 更新
  update: async (id: string, dataset: DatasetUpdate): Promise<DatasetResponse> => {
    const { data } = await apiClient.put<DatasetResponse>(`/api/datasets/${id}`, dataset);
    return data;
  },

  // 删除
  delete: async (id: string, hardDelete = false): Promise<void> => {
    await apiClient.delete(`/api/datasets/${id}`, { params: { hard_delete: hardDelete } });
  },
};
```

---

## 8. Mock API设计

### 8.1 MSW配置

```typescript
// api/mock/handlers.ts
import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  // Mock 数据导入API
  http.post('/api/data/import', async ({ request }) => {
    await delay(1000);  // 模拟网络延迟

    const formData = await request.formData();
    const file = formData.get('file');

    return HttpResponse.json({
      task_id: crypto.randomUUID(),
      status: 'PROCESSING',
      progress: 0,
      message: '正在解析文件...',
    });
  }),

  // Mock 策略模板列表
  http.get('/api/strategy/templates', async () => {
    await delay(500);

    return HttpResponse.json({
      total: 10,
      items: [
        {
          id: '1',
          name: '双均线策略',
          type: 'trend',
          description: '使用短期和长期移动平均线的交叉信号',
          difficulty: 'beginner',
          tags: ['趋势跟踪', '移动平均'],
        },
        {
          id: '2',
          name: 'MACD策略',
          type: 'momentum',
          description: '基于MACD指标的动量策略',
          difficulty: 'intermediate',
          tags: ['动量', 'MACD'],
        },
        // ... 更多模板
      ],
    });
  }),

  // Mock 回测结果
  http.get('/api/backtest/:id/results', async ({ params }) => {
    await delay(1000);

    return HttpResponse.json({
      backtest_id: params.id,
      status: 'COMPLETED',
      metrics: {
        total_return: 0.352,       // 35.2% 收益率
        annual_return: 0.283,      // 28.3% 年化收益率
        sharpe_ratio: 1.85,        // 夏普比率
        max_drawdown: -0.156,      // 15.6% 最大回撤
        win_rate: 0.612,           // 61.2% 胜率
        total_trades: 234,         // 总交易次数
      },
      equity_curve: generateMockEquityCurve(),  // 生成模拟权益曲线
      trades: generateMockTrades(234),          // 生成模拟交易记录
    });
  }),
];

// Mock数据生成函数
function generateMockEquityCurve() {
  const points = [];
  let equity = 100000;  // 初始资金10万

  for (let i = 0; i < 365; i++) {
    const date = new Date();
    date.setDate(date.getDate() - (365 - i));

    // 随机波动 ±2%
    equity *= (1 + (Math.random() - 0.5) * 0.04);

    points.push({
      date: date.toISOString().split('T')[0],
      equity: Math.round(equity),
    });
  }

  return points;
}
```

### 8.2 Mock启用

```typescript
// main.tsx
async function enableMocking() {
  if (import.meta.env.MODE === 'development') {
    const { worker } = await import('./api/mock/browser');
    return worker.start({
      onUnhandledRequest: 'bypass',  // 未处理的请求放行
    });
  }
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
```

---

## 9. 响应式设计

### 9.1 断点定义

```typescript
// utils/responsive.ts
export const breakpoints = {
  xs: 480,   // 手机
  sm: 576,   // 平板
  md: 768,   // 平板横屏
  lg: 992,   // 笔记本
  xl: 1200,  // 桌面
  xxl: 1600, // 大屏
};

export function useResponsive() {
  const [screen, setScreen] = useState({
    xs: false,
    sm: false,
    md: false,
    lg: false,
    xl: false,
    xxl: false,
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      setScreen({
        xs: width < breakpoints.sm,
        sm: width >= breakpoints.sm && width < breakpoints.md,
        md: width >= breakpoints.md && width < breakpoints.lg,
        lg: width >= breakpoints.lg && width < breakpoints.xl,
        xl: width >= breakpoints.xl && width < breakpoints.xxl,
        xxl: width >= breakpoints.xxl,
      });
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return screen;
}
```

### 9.2 响应式布局示例

```typescript
// components/layout/MainLayout.tsx
export function MainLayout({ children }: MainLayoutProps) {
  const screen = useResponsive();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 侧边栏: 手机端自动隐藏 */}
      {!screen.xs && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          width={screen.md ? 200 : 250}
        >
          <Menu />
        </Sider>
      )}

      <Layout>
        <Header>
          {/* 手机端显示抽屉菜单按钮 */}
          {screen.xs && <MenuButton />}
          <Logo />
          <ModeSwitch />
          <UserMenu />
        </Header>

        <Content style={{ padding: screen.xs ? 16 : 24 }}>
          {children}
        </Content>

        <Footer />
      </Layout>
    </Layout>
  );
}
```

---

## 10. 性能优化策略

### 10.1 代码分割

```typescript
// router/routes.tsx
import { lazy, Suspense } from 'react';

// 懒加载页面组件
const DatasetListPage = lazy(() => import('@/modules/data-management/pages/DatasetListPage'));
const StrategyListPage = lazy(() => import('@/modules/strategy-builder/pages/StrategyListPage'));

// 路由配置中使用Suspense
{
  path: 'datasets',
  element: (
    <Suspense fallback={<PageLoading />}>
      <DatasetListPage />
    </Suspense>
  ),
}
```

### 10.2 虚拟滚动

```typescript
// components/DatasetList/DatasetTable.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

export function DatasetTable({ data }: DatasetTableProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,  // 行高
    overscan: 10,  // 预渲染行数
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <DatasetRow data={data[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 10.3 图片懒加载

```typescript
// components/common/LazyImage.tsx
export function LazyImage({ src, alt }: LazyImageProps) {
  return (
    <img
      src={src}
      alt={alt}
      loading="lazy"  // 原生懒加载
      decoding="async"
    />
  );
}
```

### 10.4 缓存策略

```typescript
// hooks/useDatasets.ts
export function useDatasets(params: DatasetQueryParams) {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: () => fetchDatasets(params),
    staleTime: 5 * 60 * 1000,     // 5分钟内数据视为新鲜
    gcTime: 10 * 60 * 1000,       // 10分钟后垃圾回收
    refetchOnWindowFocus: false,  // 窗口聚焦时不自动重新获取
    retry: 2,                     // 失败重试2次
  });
}
```

---

## 11. 测试策略

### 11.1 单元测试

```typescript
// modules/data-management/components/DatasetList/__tests__/DatasetTable.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DatasetTable } from '../DatasetTable';

describe('DatasetTable', () => {
  it('should render dataset list', () => {
    const mockData = [
      { id: '1', name: 'Dataset 1', source: 'LOCAL', status: 'VALID' },
    ];

    render(<DatasetTable data={mockData} />);

    expect(screen.getByText('Dataset 1')).toBeInTheDocument();
    expect(screen.getByText('LOCAL')).toBeInTheDocument();
  });

  it('should handle delete action', async () => {
    const mockOnDelete = vi.fn();
    const user = userEvent.setup();

    render(<DatasetTable data={mockData} onDelete={mockOnDelete} />);

    const deleteButton = screen.getByRole('button', { name: /删除/ });
    await user.click(deleteButton);

    // 确认对话框
    const confirmButton = screen.getByRole('button', { name: /确认/ });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledWith('1');
    });
  });
});
```

### 11.2 集成测试

```typescript
// modules/data-management/__tests__/integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DatasetListPage } from '../pages/DatasetListPage';

describe('Dataset Management Integration', () => {
  it('should complete full CRUD workflow', async () => {
    const queryClient = new QueryClient();
    const user = userEvent.setup();

    render(
      <QueryClientProvider client={queryClient}>
        <DatasetListPage />
      </QueryClientProvider>
    );

    // 1. 创建数据集
    const createButton = screen.getByRole('button', { name: /新建/ });
    await user.click(createButton);

    await user.type(screen.getByLabelText(/名称/), 'Test Dataset');
    await user.click(screen.getByRole('button', { name: /保存/ }));

    // 2. 验证创建成功
    await waitFor(() => {
      expect(screen.getByText('Test Dataset')).toBeInTheDocument();
    });

    // 3. 更新数据集
    const editButton = screen.getByRole('button', { name: /编辑/ });
    await user.click(editButton);

    // ... 更多步骤
  });
});
```

---

## 12. 下一步行动

### 12.1 立即开始 (Phase 3-4)

1. **初始化前端项目**
   ```bash
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   npm install
   npm install antd @ant-design/icons
   npm install zustand @tanstack/react-query
   npm install axios react-router-dom
   npm install dayjs lodash-es zod
   npm install -D msw vitest @testing-library/react
   ```

2. **创建基础结构**
   - 创建 `src/` 下的所有目录
   - 配置路由 `router/index.tsx`
   - 配置API客户端 `api/client.ts`
   - 配置全局状态 `store/`

3. **实现第一个模块: 数据管理**
   - 数据集列表页面
   - 数据集表单
   - API集成

4. **实现第二个模块: 用户引导**
   - 模式切换组件
   - 偏好设置面板

### 12.2 后续阶段 (Phase 5-7)

5. **实现Mock模块**
   - 策略构建器 (使用MSW)
   - 回测分析 (使用MSW)

6. **添加测试覆盖**
   - 单元测试 (≥80%)
   - 集成测试

7. **性能优化和部署准备**
   - 代码分割
   - 虚拟滚动
   - 生产构建

---

**文档版本**: v1.0
**最后更新**: 2025-01-05
**下一步**: 初始化前端项目并实现数据管理模块
