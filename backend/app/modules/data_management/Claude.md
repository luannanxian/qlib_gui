# 模块 2: 数据管理模块 (Data Management Module)

## 模块概述

本模块负责数据的导入、预处理、存储和可视化生成，是整个量化研究平台的数据基础设施。

## 核心职责

1. **数据导入**: 支持本地文件、Qlib数据源导入
2. **数据预处理**: 缺失值处理、异常值处理、数据转换、数据筛选
3. **数据存储**: 管理数据集的存储和版本控制
4. **数据可视化**: 生成K线图、技术指标图表、自定义图表

## 子模块结构

```
data_management/
├── import/              # 数据导入子模块
│   ├── file_importer.py    # 本地文件导入
│   ├── qlib_importer.py    # Qlib数据源导入
│   └── validator.py        # 数据校验
├── preprocessing/       # 数据预处理子模块
│   ├── missing_handler.py  # 缺失值处理
│   ├── outlier_handler.py  # 异常值处理
│   ├── transformer.py      # 数据转换
│   └── filter.py           # 数据筛选
├── visualization/       # 数据可视化子模块
│   ├── chart_generator.py  # 图表生成器
│   ├── kline.py            # K线图
│   ├── indicators.py       # 技术指标图
│   └── custom_charts.py    # 自定义图表
├── storage/             # 数据存储子模块
│   ├── dataset_manager.py  # 数据集管理
│   └── cache_manager.py    # 缓存管理
├── models/              # 数据模型
│   ├── dataset.py       # 数据集模型
│   └── chart.py         # 图表配置模型
├── services/            # 业务逻辑服务
│   ├── import_service.py
│   ├── preprocess_service.py
│   └── visualization_service.py
├── api/                 # API端点
│   ├── import_api.py
│   ├── preprocess_api.py
│   └── visualization_api.py
├── schemas/             # Pydantic schemas
│   └── data_schemas.py
└── Claude.md            # 本文档
```

## API 端点

### 数据导入 API
```
POST /api/data/import/file          # 本地文件导入
POST /api/data/import/qlib          # Qlib数据源导入
GET  /api/data/preview/{dataset_id} # 数据预览
POST /api/data/validate/{dataset_id}# 数据校验
POST /api/data/repair/{dataset_id}  # 一键修复
GET  /api/data/datasets             # 获取数据集列表
DELETE /api/data/datasets/{id}      # 删除数据集
```

### 数据预处理 API
```
POST /api/data/preprocess/missing      # 缺失值处理
POST /api/data/preprocess/outliers     # 异常值处理
POST /api/data/preprocess/transform    # 数据转换
POST /api/data/preprocess/filter       # 数据筛选
GET  /api/data/preprocess/templates    # 获取预处理模板
POST /api/data/preprocess/templates    # 保存预处理模板
```

### 数据可视化 API
```
POST /api/visualization/chart/basic      # 生成基础图表
POST /api/visualization/chart/indicator  # 生成技术指标图表
POST /api/visualization/chart/custom     # 生成自定义图表
POST /api/visualization/export           # 导出图表数据
GET  /api/visualization/charts/{id}      # 获取图表配置
```

## 数据模型

### Dataset
```python
class DataSource(str, Enum):
    LOCAL = "local"
    QLIB = "qlib"
    THIRDPARTY = "thirdparty"

class DatasetStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"

class Dataset(BaseModel):
    id: str
    name: str
    source: DataSource
    import_date: datetime
    row_count: int
    columns: List[DataColumn]
    status: DatasetStatus
    validation_results: List[ValidationResult]
    file_path: Optional[str]
    metadata: Dict[str, Any]
```

### ChartConfig
```python
class ChartType(str, Enum):
    KLINE = "kline"
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"

class ChartConfig(BaseModel):
    id: str
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any]
    created_at: datetime
```

## 技术要点

### 数据导入
- **文件解析**: pandas读取CSV/Excel
- **批量上传**: 异步处理多文件上传
- **字段映射**: 自动识别+手动映射
- **数据校验**: 缺失值检测、格式验证、重复检测

### 数据预处理
- **缺失值**: 4种处理方式(删除/均值/中位数/前向填充)
- **异常值**: 标准差法、分位数法
- **转换**: Min-Max归一化、Z-Score标准化
- **筛选**: 多条件组合筛选，支持模板保存

### 数据可视化
- **图表库**: 使用ECharts/Plotly生成图表
- **缓存策略**: Redis缓存图表配置
- **异步生成**: 大数据集图表异步生成
- **导出格式**: PNG/SVG/JSON

### 性能优化
- **分块读取**: 大文件分块处理
- **异步任务**: Celery处理耗时操作
- **缓存策略**: 频繁访问数据集缓存
- **懒加载**: 数据预览按需加载

## 依赖关系

- **依赖**:
  - Qlib库(数据源集成)
  - Pandas/NumPy(数据处理)
  - TA-Lib(技术指标计算)
- **被依赖**:
  - 模块3(策略构建) - 使用处理后的数据
  - 模块4(回测分析) - 使用数据进行回测

## 开发优先级

- **Phase 1 (高优先级)**:
  - 数据导入(本地文件 + Qlib)
  - 基础预处理功能
  - 简单数据预览
- **Phase 2 (高优先级)**:
  - 完整可视化功能
  - 高级预处理功能
  - 图表导出

## 测试要点

### 单元测试
- 各种文件格式解析
- 缺失值/异常值处理算法
- 数据转换正确性
- 筛选条件逻辑

### 集成测试
- 完整导入流程
- 预处理管道
- 图表生成端到端

### 性能测试
- 50万+行数据处理 < 30秒
- 并发导入稳定性
- 大数据集可视化性能

## 注意事项

1. **数据安全**: 用户上传数据需要隔离存储
2. **内存管理**: 大文件处理注意内存释放
3. **错误处理**: 提供友好的错误提示
4. **数据版本**: 支持数据集版本管理(未来扩展)
5. **格式兼容**: 支持多种日期格式自动识别
