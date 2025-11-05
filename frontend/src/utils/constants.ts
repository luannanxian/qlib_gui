/**
 * Application Constants
 */

// Data Source Options
export const DATA_SOURCE_OPTIONS = [
  { label: '本地文件', value: 'LOCAL' },
  { label: 'Qlib数据', value: 'QLIB' },
  { label: '第三方数据', value: 'THIRDPARTY' },
] as const;

// Dataset Status Options
export const DATASET_STATUS_OPTIONS = [
  { label: '有效', value: 'VALID', color: 'success' },
  { label: '无效', value: 'INVALID', color: 'error' },
  { label: '待验证', value: 'PENDING', color: 'processing' },
] as const;

// User Mode Options
export const USER_MODE_OPTIONS = [
  { label: '初学者模式', value: 'BEGINNER', icon: '🎓' },
  { label: '专家模式', value: 'EXPERT', icon: '⚡' },
] as const;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
export const MAX_PAGE_SIZE = 1000;

// File Upload
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const ALLOWED_FILE_TYPES = ['.csv', '.xlsx', '.xls', '.json'];

// Date Format
export const DATE_FORMAT = 'YYYY-MM-DD';
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss';

// Chart Types
export const CHART_TYPE_OPTIONS = [
  { label: 'K线图', value: 'KLINE' },
  { label: '折线图', value: 'LINE' },
  { label: '柱状图', value: 'BAR' },
  { label: '散点图', value: 'SCATTER' },
  { label: '热力图', value: 'HEATMAP' },
] as const;

// Strategy Types
export const STRATEGY_TYPE_OPTIONS = [
  { label: '趋势跟踪', value: 'trend' },
  { label: '动量策略', value: 'momentum' },
  { label: '均值回归', value: 'mean_reversion' },
  { label: '套利策略', value: 'arbitrage' },
  { label: '自定义', value: 'custom' },
] as const;

// Backtest Status
export const BACKTEST_STATUS_OPTIONS = [
  { label: '待执行', value: 'PENDING', color: 'default' },
  { label: '运行中', value: 'RUNNING', color: 'processing' },
  { label: '已完成', value: 'COMPLETED', color: 'success' },
  { label: '失败', value: 'FAILED', color: 'error' },
] as const;
