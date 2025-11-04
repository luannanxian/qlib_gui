# 前端模块 7: UI交互

## 模块概述
全局布局、路由管理、状态管理、错误处理、通知系统。

## 目录结构
```
ui-interaction/
├── layout/
│   ├── AppLayout.tsx        # 应用整体布局
│   ├── Header.tsx           # 顶部导航栏
│   ├── Sidebar.tsx          # 左侧工具栏
│   ├── ContentArea.tsx      # 中间工作区
│   └── PropertyPanel.tsx    # 右侧属性面板
├── routing/
│   ├── AppRouter.tsx        # 路由配置
│   └── ProtectedRoute.tsx   # 受保护路由
├── state/
│   ├── globalStore.ts       # 全局状态
│   └── apiClient.ts         # API客户端
├── components/
│   ├── ErrorBoundary.tsx    # 错误边界
│   ├── Loading.tsx          # 加载组件
│   ├── Toast.tsx            # 通知组件
│   └── ConfirmDialog.tsx    # 确认对话框
└── Claude.md
```

## 核心组件

### AppLayout
```typescript
export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <Header />
      <div className="app-body">
        <Sidebar />
        <ContentArea>{children}</ContentArea>
        <PropertyPanel />
      </div>
    </div>
  );
}
```

### AppRouter
```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/data" element={<DataManagementPage />} />
        <Route path="/strategy" element={<StrategyBuilderPage />} />
        <Route path="/backtest" element={<BacktestPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### ErrorBoundary
```typescript
export class ErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

## 状态管理

### 全局Store (Zustand)
```typescript
interface GlobalState {
  user: User | null;
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  notifications: Notification[];
  
  setUser: (user: User | null) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
}

export const useGlobalStore = create<GlobalState>((set) => ({
  user: null,
  theme: 'light',
  sidebarCollapsed: false,
  notifications: [],
  
  setUser: (user) => set({ user }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  addNotification: (notification) => set((state) => ({
    notifications: [...state.notifications, notification]
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter(n => n.id !== id)
  }))
}));
```

## API客户端

```typescript
class APIClient {
  private baseURL = '/api';

  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers
      }
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: any) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  put<T>(endpoint: string, data: any) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new APIClient();
```

## Toast通知

```typescript
import { toast } from 'sonner'; // 或 react-hot-toast

export const notify = {
  success: (message: string) => toast.success(message),
  error: (message: string) => toast.error(message),
  info: (message: string) => toast.info(message),
  warning: (message: string) => toast.warning(message),
  loading: (message: string) => toast.loading(message)
};
```

## 技术栈
- **路由**: React Router v6
- **状态**: Zustand + React Query
- **通知**: Sonner / React Hot Toast
- **UI库**: Ant Design / shadcn/ui
- **样式**: Tailwind CSS

## 注意事项
1. 全局错误捕获和上报
2. Loading状态统一管理
3. 路由懒加载优化
4. 响应式布局适配
5. 主题切换(明亮/暗黑)
