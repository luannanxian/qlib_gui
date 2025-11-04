# 前端模块 4: 回测分析

## 模块概述
回测配置界面、实时进度监控、结果可视化展示、策略诊断报告。

## 目录结构
```
backtest-analysis/
├── components/
│   ├── BacktestConfig/      # 回测配置
│   │   ├── ConfigForm.tsx
│   │   ├── StockPoolSelector.tsx
│   │   └── CostSettings.tsx
│   ├── BacktestMonitor/     # 回测监控
│   │   ├── ProgressBar.tsx
│   │   ├── LogViewer.tsx
│   │   └── ControlButtons.tsx
│   ├── ResultDashboard/     # 结果仪表盘
│   │   ├── MetricsTable.tsx
│   │   ├── EquityCurve.tsx
│   │   ├── DrawdownChart.tsx
│   │   ├── TradeList.tsx
│   │   └── HoldingsChart.tsx
│   └── Diagnosis/           # 策略诊断
│       ├── RevenueAnalysis.tsx
│       ├── RiskAnalysis.tsx
│       ├── OverfittingDetection.tsx
│       └── Suggestions.tsx
├── hooks/
│   ├── useBacktest.ts
│   ├── useWebSocket.ts
│   └── useDiagnosis.ts
└── Claude.md
```

## 核心组件

### BacktestMonitor
```typescript
export function BacktestMonitor({ backtestId }: { backtestId: string }) {
  const { progress, logs, status } = useWebSocket(`/ws/backtest/${backtestId}`);

  return (
    <div className="backtest-monitor">
      <ProgressBar percentage={progress.percentage} eta={progress.eta} />
      <div className="status">状态: {status}</div>
      <LogViewer logs={logs} />
      <ControlButtons
        onPause={() => api.pauseBacktest(backtestId)}
        onResume={() => api.resumeBacktest(backtestId)}
        onTerminate={() => api.terminateBacktest(backtestId)}
      />
    </div>
  );
}
```

### ResultDashboard
- 核心指标卡片(15+指标)
- 净值曲线(ECharts)
- 回撤曲线
- 月度收益柱状图
- 交易明细表格(TanStack Table)
- 持仓分布饼图

### WebSocket Hook
```typescript
export function useWebSocket(url: string) {
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };
    ws.onerror = () => setConnected(false);
    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, [url]);

  return { data, connected };
}
```

## 技术栈
- **图表**: ECharts (净值/回撤曲线)
- **表格**: TanStack Table v8
- **WebSocket**: 原生WebSocket / Socket.io
- **导出**: jsPDF, ExcelJS

## 注意事项
1. WebSocket断线重连
2. 大量日志使用虚拟滚动
3. 图表数据过多时使用数据采样
4. 支持多策略对比
5. 诊断建议可操作化
