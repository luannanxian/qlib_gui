# 前端模块 2: 数据管理

## 模块概述
数据导入、预处理、可视化的前端界面和交互逻辑。

## 目录结构
```
data-management/
├── components/
│   ├── DataImport/          # 数据导入组件
│   │   ├── FileUploader.tsx
│   │   ├── QlibDataSelector.tsx
│   │   └── DataPreview.tsx
│   ├── DataPreprocessing/   # 数据预处理组件
│   │   ├── MissingValueHandler.tsx
│   │   ├── OutlierDetector.tsx
│   │   └── DataTransformer.tsx
│   └── DataVisualization/   # 数据可视化组件
│       ├── KLineChart.tsx
│       ├── IndicatorChart.tsx
│       └── CustomChart.tsx
├── hooks/
│   ├── useDataImport.ts
│   ├── usePreprocessing.ts
│   └── useCharts.ts
├── store/
│   └── dataStore.ts
├── types/
│   └── index.ts
└── Claude.md
```

## 核心组件

### FileUploader
- CSV/Excel文件上传
- 拖拽上传支持
- 批量上传(最多10个)
- 上传进度显示

### DataPreview
- 数据表格展示(前100行)
- 分页功能
- 字段映射UI
- 数据校验结果显示

### KLineChart
- 基于ECharts/TradingView
- K线图+成交量
- 均线叠加
- 交互式缩放

## Hooks示例
```typescript
export function useDataImport() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  const uploadFiles = async (files: File[]) => {
    setUploading(true);
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await fetch('/api/data/import/file', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    setUploading(false);
    return result;
  };

  return { files, uploading, datasets, uploadFiles };
}
```

## 技术栈
- **图表**: ECharts, Recharts, TradingView Lightweight Charts
- **表格**: TanStack Table (React Table v8)
- **上传**: react-dropzone
- **表单**: React Hook Form + Zod

## 注意事项
1. 大文件上传使用分片上传
2. 图表数据量过大时使用数据采样
3. 预处理操作提供预览功能
4. 支持导出处理后的数据
