# 前端模块 3: 策略构建

## 模块概述
策略模板选择、指标组件拖拽、策略逻辑可视化编辑、参数优化UI。

## 目录结构
```
strategy-builder/
├── components/
│   ├── TemplateGallery/     # 策略模板画廊
│   │   ├── TemplateCard.tsx
│   │   └── TemplateDetail.tsx
│   ├── IndicatorLibrary/    # 指标组件库
│   │   ├── IndicatorList.tsx
│   │   └── IndicatorConfig.tsx
│   ├── StrategyEditor/      # 策略编辑器
│   │   ├── FlowCanvas.tsx       # ReactFlow画布
│   │   ├── NodePalette.tsx      # 节点面板
│   │   ├── NodeConfig.tsx       # 节点配置
│   │   └── LogicValidator.tsx   # 逻辑验证
│   └── Optimization/        # 参数优化
│       ├── ParameterForm.tsx
│       ├── OptimizationResult.tsx
│       └── HeatmapChart.tsx
├── hooks/
│   ├── useStrategy.ts
│   ├── useFlowEditor.ts
│   └── useOptimization.ts
├── store/
│   └── strategyStore.ts
└── Claude.md
```

## 核心组件

### FlowCanvas (ReactFlow)
```typescript
import ReactFlow, { Node, Edge } from 'reactflow';

export function FlowCanvas() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const nodeTypes = {
    indicator: IndicatorNode,
    condition: ConditionNode,
    signal: SignalNode,
    position: PositionNode,
    stopLoss: StopLossNode
  };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={setNodes}
      onEdgesChange={setEdges}
      fitView
    />
  );
}
```

### ParameterOptimization
- 参数范围设置
- 优化算法选择
- 实时进度显示
- 结果热力图
- 敏感性分析图表

## 状态管理
```typescript
interface StrategyState {
  currentStrategy: Strategy | null;
  templates: Template[];
  indicators: Indicator[];
  optimizationTask: OptimizationTask | null;
}
```

## 技术栈
- **流程图**: ReactFlow / X6
- **拖拽**: dnd-kit
- **代码编辑**: Monaco Editor (自定义因子)
- **图表**: ECharts (参数热力图)

## 注意事项
1. 支持撤销/重做(快照机制)
2. 自动保存草稿
3. 节点连接规则校验
4. 参数优化提供耗时估算
5. 支持导出Qlib代码
