# 后端 API 接口设计分析报告

**生成时间**: 2025-01-05
**目的**: 为前端开发提供 API 接口规范和集成指南

---

## 1. 已实现 API 端点总览

### 1.1 数据管理模块 (Data Management)

**基础路径**: `/api/datasets`

| 方法 | 端点 | 描述 | 实现状态 |
|------|------|------|---------|
| GET | `/api/datasets` | 获取数据集列表(分页+过滤) | ✅ 已实现 |
| GET | `/api/datasets/{id}` | 获取单个数据集详情 | ✅ 已实现 |
| POST | `/api/datasets` | 创建新数据集 | ✅ 已实现 |
| PUT | `/api/datasets/{id}` | 更新数据集 | ✅ 已实现 |
| DELETE | `/api/datasets/{id}` | 删除数据集(软删除/硬删除) | ✅ 已实现 |

**关键特性**:
- 分页支持: `skip`(默认0) 和 `limit`(默认100, 最大1000)
- 过滤支持: `source`, `status`, `search`(名称搜索)
- 输入验证: SQL注入防护、XSS防护、路径遍历防护
- 日志追踪: 支持 `X-Correlation-ID` 请求头
- 软删除: 默认软删除, `hard_delete=true` 时永久删除

### 1.2 用户引导模块 (User Onboarding)

**基础路径**: `/api/user`

| 方法 | 端点 | 描述 | 实现状态 |
|------|------|------|---------|
| GET | `/api/user/mode` | 获取当前用户模式 | ✅ 已实现 |
| POST | `/api/user/mode` | 切换用户模式(初学者/专家) | ✅ 已实现 |
| GET | `/api/user/preferences` | 获取用户偏好设置 | ✅ 已实现 |
| PUT | `/api/user/preferences` | 更新用户偏好设置 | ✅ 已实现 |

**关键特性**:
- 模式切换: `BEGINNER` (初学者) / `EXPERT` (专家)
- 偏好设置: 支持部分更新 (partial update)
- 内存存储: 当前使用内存字典存储 (⚠️ 生产环境需要数据库持久化)

---

## 2. 数据模型 (Schemas)

### 2.1 数据集相关 Schema

#### DatasetCreate (创建数据集请求)
```typescript
interface DatasetCreate {
  name: string;               // 数据集名称 (1-255字符, 必填)
  source: "LOCAL" | "QLIB" | "THIRDPARTY";  // 数据源类型
  file_path: string;          // 文件路径或URI (必填)
  extra_metadata?: Record<string, any>;  // 额外元数据 (可选)
}
```

#### DatasetUpdate (更新数据集请求)
```typescript
interface DatasetUpdate {
  name?: string;              // 数据集名称 (可选)
  status?: "VALID" | "INVALID" | "PENDING";  // 验证状态 (可选)
  row_count?: number;         // 行数 (≥0, 可选)
  columns?: string[];         // 列名列表 (可选)
  extra_metadata?: Record<string, any>;  // 额外元数据 (可选)
}
```

#### DatasetResponse (数据集响应)
```typescript
interface DatasetResponse {
  id: string;                 // UUID
  name: string;               // 数据集名称
  source: string;             // 数据源: "LOCAL", "QLIB", "THIRDPARTY"
  file_path: string;          // 文件路径
  status: string;             // 状态: "VALID", "INVALID", "PENDING"
  row_count: number;          // 行数
  columns: string[];          // 列名列表
  metadata: Record<string, any>;  // 元数据 (注意: API中为"metadata", 数据库中为"extra_metadata")
  created_at: string;         // ISO 8601 日期时间
  updated_at: string;         // ISO 8601 日期时间
}
```

#### DatasetListResponse (数据集列表响应)
```typescript
interface DatasetListResponse {
  total: number;              // 总数量
  items: DatasetResponse[];   // 数据集列表
}
```

### 2.2 用户模式相关 Schema

#### ModeUpdateRequest (切换模式请求)
```typescript
interface ModeUpdateRequest {
  mode: "BEGINNER" | "EXPERT";
}
```

#### ModeResponse (模式响应)
```typescript
interface ModeResponse {
  user_id: string;
  mode: "BEGINNER" | "EXPERT";
  updated_at: string;         // ISO 8601 日期时间
}
```

#### PreferencesUpdateRequest (更新偏好设置请求)
```typescript
interface PreferencesUpdateRequest {
  show_tooltips?: boolean;    // 是否显示提示 (可选)
  language?: string;          // 语言 (可选)
  completed_guides?: string[]; // 已完成的引导 (可选)
}
```

#### PreferencesResponse (偏好设置响应)
```typescript
interface PreferencesResponse {
  user_id: string;
  mode: "BEGINNER" | "EXPERT";
  completed_guides: string[];
  show_tooltips: boolean;
  language: string;
  created_at: string;
  updated_at: string;
}
```

### 2.3 通用响应包装 Schema

#### APIResponse (通用API响应)
```typescript
interface APIResponse<T> {
  success: boolean;           // 请求是否成功
  data?: T;                   // 响应数据 (成功时)
  error?: ErrorDetail;        // 错误详情 (失败时)
  timestamp: string;          // 响应时间戳
}

interface ErrorDetail {
  code: string;               // 错误码
  message: string;            // 错误消息
  details?: Record<string, any>; // 错误详情 (可选)
}
```

**使用示例**:
```typescript
// 用户模式相关API使用APIResponse包装
type ModeAPIResponse = APIResponse<ModeResponse>;
type PreferencesAPIResponse = APIResponse<PreferencesResponse>;

// 数据集API直接返回数据(不使用APIResponse包装)
type DatasetAPIResponse = DatasetResponse;
type DatasetListAPIResponse = DatasetListResponse;
```

---

## 3. API 调用示例

### 3.1 数据集管理 API 调用示例

#### 获取数据集列表
```typescript
// GET /api/datasets?skip=0&limit=20&source=LOCAL&status=VALID&search=stock
const response = await fetch(
  '/api/datasets?' + new URLSearchParams({
    skip: '0',
    limit: '20',
    source: 'LOCAL',
    status: 'VALID',
    search: 'stock'
  })
);

const data: DatasetListResponse = await response.json();
// {
//   "total": 100,
//   "items": [
//     {
//       "id": "550e8400-e29b-41d4-a716-446655440000",
//       "name": "Stock Data 2024",
//       "source": "LOCAL",
//       "file_path": "/data/stocks_2024.csv",
//       "status": "VALID",
//       "row_count": 10000,
//       "columns": ["date", "symbol", "open", "high", "low", "close", "volume"],
//       "metadata": {"description": "Daily stock data"},
//       "created_at": "2024-01-01T00:00:00Z",
//       "updated_at": "2024-01-01T00:00:00Z"
//     }
//   ]
// }
```

#### 创建数据集
```typescript
// POST /api/datasets
const response = await fetch('/api/datasets', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Correlation-ID': crypto.randomUUID() // 可选: 请求追踪ID
  },
  body: JSON.stringify({
    name: "Stock Data 2024",
    source: "LOCAL",
    file_path: "/data/stocks_2024.csv",
    extra_metadata: {
      description: "Daily stock data for 2024",
      format: "csv"
    }
  })
});

const data: DatasetResponse = await response.json();
```

#### 更新数据集
```typescript
// PUT /api/datasets/{id}
const response = await fetch(`/api/datasets/${datasetId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    status: "VALID",
    row_count: 10000,
    columns: ["date", "symbol", "open", "high", "low", "close", "volume"]
  })
});

const data: DatasetResponse = await response.json();
```

#### 删除数据集
```typescript
// DELETE /api/datasets/{id}?hard_delete=false (软删除)
const response = await fetch(
  `/api/datasets/${datasetId}?hard_delete=false`,
  { method: 'DELETE' }
);
// 返回 204 No Content

// DELETE /api/datasets/{id}?hard_delete=true (硬删除)
const response = await fetch(
  `/api/datasets/${datasetId}?hard_delete=true`,
  { method: 'DELETE' }
);
```

### 3.2 用户模式 API 调用示例

#### 获取当前模式
```typescript
// GET /api/user/mode?user_id=user123
const response = await fetch(
  '/api/user/mode?' + new URLSearchParams({ user_id: 'user123' })
);

const data: APIResponse<ModeResponse> = await response.json();
// {
//   "success": true,
//   "data": {
//     "user_id": "user123",
//     "mode": "BEGINNER",
//     "updated_at": "2024-01-01T00:00:00Z"
//   },
//   "error": null,
//   "timestamp": "2024-01-01T00:00:00Z"
// }
```

#### 切换模式
```typescript
// POST /api/user/mode?user_id=user123
const response = await fetch(
  '/api/user/mode?' + new URLSearchParams({ user_id: 'user123' }),
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: "EXPERT" })
  }
);

const data: APIResponse<ModeResponse> = await response.json();
```

#### 获取偏好设置
```typescript
// GET /api/user/preferences?user_id=user123
const response = await fetch(
  '/api/user/preferences?' + new URLSearchParams({ user_id: 'user123' })
);

const data: APIResponse<PreferencesResponse> = await response.json();
```

#### 更新偏好设置
```typescript
// PUT /api/user/preferences?user_id=user123
const response = await fetch(
  '/api/user/preferences?' + new URLSearchParams({ user_id: 'user123' }),
  {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      show_tooltips: true,
      language: "zh-CN",
      completed_guides: ["intro", "data-import"]
    })
  }
);

const data: APIResponse<PreferencesResponse> = await response.json();
```

---

## 4. 错误处理规范

### 4.1 HTTP 状态码

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| 200 OK | 成功 | GET, PUT成功 |
| 201 Created | 创建成功 | POST创建资源成功 |
| 204 No Content | 无内容 | DELETE成功 |
| 400 Bad Request | 请求错误 | 参数验证失败、输入格式错误 |
| 404 Not Found | 未找到 | 资源不存在 |
| 409 Conflict | 冲突 | 数据集名称重复、约束冲突 |
| 500 Internal Server Error | 服务器错误 | 数据库错误、未预期异常 |

### 4.2 错误响应格式

#### 数据集API错误响应 (直接返回错误详情)
```typescript
// 400 Bad Request
{
  "detail": "Invalid input in list datasets: Search term contains potentially dangerous characters"
}

// 404 Not Found
{
  "detail": "Dataset with id 550e8400-e29b-41d4-a716-446655440000 not found"
}

// 409 Conflict
{
  "detail": "Dataset with name 'Stock Data 2024' already exists"
}

// 500 Internal Server Error
{
  "detail": "Database error: Connection pool exhausted"
}
```

#### 用户模式API错误响应 (使用APIResponse包装)
```typescript
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid mode value",
    "details": {
      "field": "mode",
      "allowed_values": ["BEGINNER", "EXPERT"]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 5. 安全特性

### 5.1 已实现的安全防护

#### 输入验证 (Input Validation)
- **SQL注入防护**: 检测并阻止 `'`, `--`, `/**/`, `UNION`, `DROP` 等SQL关键字
- **XSS防护**: 检测并阻止 `<script>`, `javascript:`, `onerror=` 等XSS模式
- **路径遍历防护**: 阻止 `../`, `..\\`, `%2e%2e` 等路径遍历字符
- **JSON大小限制**: JSON字段最大1MB
- **分页限制**: 单次查询最多返回1000条记录

**示例**:
```typescript
// 以下输入会被阻止并返回400错误
const maliciousInputs = [
  "test' OR 1=1--",           // SQL注入
  "<script>alert('XSS')</script>",  // XSS攻击
  "../../etc/passwd",         // 路径遍历
  { columns: "a".repeat(2_000_000) }  // JSON过大
];
```

#### 凭证保护
- **数据库URL脱敏**: 日志中自动将密码替换为 `***`
- **强SECRET_KEY**: 要求64+字符, 混合大小写
- **环境变量隔离**: 敏感信息仅在 `.env` 中 (已加入 `.gitignore`)

#### 日志追踪
- **关联ID (Correlation ID)**: 支持 `X-Correlation-ID` 请求头
- **结构化日志**: 使用Loguru记录所有操作
- **PII过滤**: 自动过滤密码等敏感信息

### 5.2 前端安全建议

1. **HTTPS**: 生产环境必须使用HTTPS
2. **CORS**: 配置允许的前端域名
3. **认证**: 添加JWT Token到请求头 (后端未实现,需补充)
4. **请求限流**: 前端实现防抖/节流 (后端暂无限流)
5. **输入校验**: 前端也需要进行基本验证

---

## 6. 性能优化建议

### 6.1 已实现的优化

- **数据库索引**:
  - `datasets`: `(source, status)`, `(status, created_at)`, `(name, source)`, `(is_deleted, created_at)`
  - **查询性能**: 10-100倍提升
- **分页查询**: 默认100条, 最大1000条
- **连接池**: 默认pool_size=5, max_overflow=10

### 6.2 前端优化建议

1. **虚拟滚动**: 大数据集列表使用虚拟滚动 (react-window, react-virtuoso)
2. **缓存策略**: 使用React Query的缓存机制
   ```typescript
   const { data } = useQuery({
     queryKey: ['datasets', { skip, limit, source }],
     queryFn: () => fetchDatasets({ skip, limit, source }),
     staleTime: 5 * 60 * 1000, // 5分钟缓存
   });
   ```
3. **乐观更新**: 删除/更新操作使用乐观UI
4. **防抖搜索**: 搜索框使用300ms防抖
5. **分页加载**: 初始加载20-50条, 按需加载更多

---

## 7. 缺失功能 (需要Mock或待开发)

### 7.1 数据管理模块缺失API (高优先级)

| 功能 | 端点 | 状态 | 前端应对策略 |
|------|------|------|-------------|
| CSV/Excel导入 | `POST /api/data/import` | ❌ 未实现 | Mock API返回上传进度 |
| Qlib数据接入 | `POST /api/data/qlib/sync` | ❌ 未实现 | Mock API返回同步状态 |
| 数据预处理 | `POST /api/data/{id}/preprocess` | ❌ 未实现 | Mock API返回处理结果 |
| 数据可视化 | `GET /api/data/{id}/chart` | ❌ 未实现 | 前端生成模拟图表数据 |
| 技术指标计算 | `POST /api/data/{id}/indicators` | ❌ 未实现 | 前端使用TA-Lib.js本地计算 |

### 7.2 策略构建模块缺失API (中优先级)

| 功能 | 端点 | 状态 | 前端应对策略 |
|------|------|------|-------------|
| 策略模板列表 | `GET /api/strategy/templates` | ❌ 未实现 | 硬编码10+模板数据 |
| 创建策略 | `POST /api/strategy` | ❌ 未实现 | Mock API保存到localStorage |
| 因子库列表 | `GET /api/strategy/factors` | ❌ 未实现 | 硬编码40+指标列表 |
| 策略验证 | `POST /api/strategy/{id}/validate` | ❌ 未实现 | 前端基本语法检查 |

### 7.3 回测分析模块缺失API (高优先级)

| 功能 | 端点 | 状态 | 前端应对策略 |
|------|------|------|-------------|
| 创建回测 | `POST /api/backtest` | ❌ 未实现 | Mock API返回任务ID |
| 获取回测结果 | `GET /api/backtest/{id}/results` | ❌ 未实现 | 返回模拟指标数据 |
| 回测诊断 | `GET /api/backtest/{id}/diagnosis` | ❌ 未实现 | 返回模拟问题列表 |
| 参数优化 | `POST /api/backtest/{id}/optimize` | ❌ 未实现 | Mock长时间异步任务 |

---

## 8. 前端开发建议

### 8.1 API Client 封装

推荐使用 **Axios + React Query** 组合:

```typescript
// src/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器: 添加关联ID
apiClient.interceptors.request.use((config) => {
  config.headers['X-Correlation-ID'] = crypto.randomUUID();
  // 添加认证Token (待后端实现)
  // const token = localStorage.getItem('token');
  // if (token) config.headers['Authorization'] = `Bearer ${token}`;
  return config;
});

// 响应拦截器: 错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 跳转到登录页
    }
    return Promise.reject(error);
  }
);
```

### 8.2 TypeScript 类型定义

```typescript
// src/types/api.ts
export interface DatasetCreate {
  name: string;
  source: "LOCAL" | "QLIB" | "THIRDPARTY";
  file_path: string;
  extra_metadata?: Record<string, any>;
}

export interface DatasetResponse {
  id: string;
  name: string;
  source: string;
  file_path: string;
  status: string;
  row_count: number;
  columns: string[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DatasetListResponse {
  total: number;
  items: DatasetResponse[];
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  timestamp: string;
}
```

### 8.3 React Query Hooks

```typescript
// src/hooks/useDatasets.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import type { DatasetListResponse, DatasetCreate, DatasetResponse } from '@/types/api';

export function useDatasets(params: {
  skip?: number;
  limit?: number;
  source?: string;
  status?: string;
  search?: string;
}) {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: async () => {
      const { data } = await apiClient.get<DatasetListResponse>('/api/datasets', { params });
      return data;
    },
  });
}

export function useCreateDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (dataset: DatasetCreate) => {
      const { data } = await apiClient.post<DatasetResponse>('/api/datasets', dataset);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}

export function useDeleteDataset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, hardDelete }: { id: string; hardDelete: boolean }) => {
      await apiClient.delete(`/api/datasets/${id}`, { params: { hard_delete: hardDelete } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    },
  });
}
```

### 8.4 Mock API 策略

对于未实现的API, 使用 **MSW (Mock Service Worker)**:

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // Mock 数据导入API
  http.post('/api/data/import', async ({ request }) => {
    const formData = await request.formData();
    const file = formData.get('file');

    return HttpResponse.json({
      success: true,
      data: {
        task_id: crypto.randomUUID(),
        status: 'PROCESSING',
        progress: 0,
      },
    });
  }),

  // Mock 策略模板列表
  http.get('/api/strategy/templates', () => {
    return HttpResponse.json({
      total: 10,
      items: [
        { id: '1', name: 'Double MA Crossover', type: 'trend' },
        { id: '2', name: 'MACD Strategy', type: 'momentum' },
        // ... 更多模板
      ],
    });
  }),
];
```

---

## 9. 开发优先级建议

### Phase 1: 基础功能 (1-2周)
1. ✅ 数据集CRUD界面 (可立即开发, API已就绪)
2. ✅ 用户模式切换界面 (可立即开发, API已就绪)
3. 🟡 数据导入界面 (使用Mock API开发)

### Phase 2: 核心业务 (2-4周)
4. 🟡 策略构建界面 (使用Mock API + 硬编码模板)
5. 🟡 回测配置界面 (使用Mock API)
6. 🟡 结果可视化界面 (前端生成模拟数据)

### Phase 3: 集成调试 (1-2周)
7. 🔴 等待后端API完成后替换Mock
8. 🔴 端到端测试
9. 🔴 性能优化

---

## 10. 下一步行动

### 立即可做 (不依赖后端)
1. **搭建前端项目框架**: Vite + React + TypeScript + Ant Design
2. **配置路由**: React Router v6
3. **配置状态管理**: Zustand + React Query
4. **实现数据集管理页面**:
   - 列表页 (表格 + 分页 + 搜索 + 过滤)
   - 创建/编辑表单
   - 删除确认对话框
5. **实现用户模式切换组件**:
   - 顶部导航栏的模式切换开关
   - 偏好设置弹窗

### 需要Mock API (后端未实现)
1. 数据导入页面 (CSV/Excel上传)
2. 数据可视化页面 (K线图、技术指标图表)
3. 策略构建器 (拖拽式/代码式编辑器)
4. 回测配置页面
5. 回测结果分析页面

### 需要等待后端 (必须完成)
1. 用户认证/授权 (JWT Token)
2. WebSocket实时通信 (回测进度推送)
3. 完整数据处理流程
4. Qlib引擎集成
5. TA-Lib指标计算

---

## 11. 联系信息

**后端API文档**: 启动后访问 `http://localhost:8000/docs` (Swagger UI)
**数据库配置**: 见 [backend/.env](../backend/.env.example)
**项目仓库**: [项目GitHub地址]

---

**文档版本**: v1.0
**最后更新**: 2025-01-05
**维护者**: Full-Stack Development Team
