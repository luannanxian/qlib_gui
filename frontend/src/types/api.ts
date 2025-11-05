/**
 * API Type Definitions
 *
 * This file contains all TypeScript types and interfaces for API requests and responses.
 * Generated based on backend API analysis (see docs/BACKEND_API_ANALYSIS.md)
 */

// ============================================================================
// Common Types
// ============================================================================

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: ErrorDetail;
  timestamp: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// ============================================================================
// Dataset Types
// ============================================================================

export type DataSource = 'LOCAL' | 'QLIB' | 'THIRDPARTY';
export type DatasetStatus = 'VALID' | 'INVALID' | 'PENDING';

export interface DatasetCreate {
  name: string;
  source: DataSource;
  file_path: string;
  extra_metadata?: Record<string, any>;
}

export interface DatasetUpdate {
  name?: string;
  status?: DatasetStatus;
  row_count?: number;
  columns?: string[];
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

export interface DatasetQueryParams extends PaginationParams {
  source?: string;
  status?: string;
  search?: string;
}

// ============================================================================
// User Mode Types
// ============================================================================

export type UserMode = 'BEGINNER' | 'EXPERT';

export interface ModeUpdateRequest {
  mode: UserMode;
}

export interface ModeResponse {
  user_id: string;
  mode: UserMode;
  updated_at: string;
}

export interface PreferencesUpdateRequest {
  show_tooltips?: boolean;
  language?: string;
  completed_guides?: string[];
}

export interface PreferencesResponse {
  user_id: string;
  mode: UserMode;
  completed_guides: string[];
  show_tooltips: boolean;
  language: string;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Strategy Types (Mock)
// ============================================================================

export type StrategyType = 'trend' | 'momentum' | 'mean_reversion' | 'arbitrage' | 'custom';
export type StrategyDifficulty = 'beginner' | 'intermediate' | 'advanced';

export interface StrategyTemplate {
  id: string;
  name: string;
  type: StrategyType;
  description: string;
  difficulty: StrategyDifficulty;
  tags: string[];
  code_template?: string;
}

export interface StrategyCreate {
  name: string;
  template_id?: string;
  code: string;
  description?: string;
}

export interface StrategyResponse {
  id: string;
  name: string;
  type: StrategyType;
  code: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Backtest Types (Mock)
// ============================================================================

export type BacktestStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface BacktestConfig {
  strategy_id: string;
  dataset_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  commission_rate: number;
}

export interface BacktestMetrics {
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
}

export interface EquityCurvePoint {
  date: string;
  equity: number;
}

export interface Trade {
  date: string;
  symbol: string;
  action: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  profit?: number;
}

export interface BacktestResult {
  backtest_id: string;
  status: BacktestStatus;
  metrics: BacktestMetrics;
  equity_curve: EquityCurvePoint[];
  trades: Trade[];
}

// ============================================================================
// Chart Types
// ============================================================================

export type ChartType = 'KLINE' | 'LINE' | 'BAR' | 'SCATTER' | 'HEATMAP';

export interface ChartConfig {
  id: string;
  name: string;
  chart_type: ChartType;
  dataset_id: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CandlestickData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LineData {
  date: string;
  value: number;
  [key: string]: string | number;
}

export interface BarData {
  name: string;
  value: number;
  [key: string]: string | number;
}

// ============================================================================
// Indicator Types
// ============================================================================

export type IndicatorCategory = 'trend' | 'momentum' | 'volatility' | 'volume' | 'custom';

export interface Indicator {
  id: string;
  name: string;
  category: IndicatorCategory;
  description: string;
  parameters: IndicatorParameter[];
}

export interface IndicatorParameter {
  name: string;
  type: 'number' | 'string' | 'boolean';
  default: any;
  min?: number;
  max?: number;
  options?: string[];
}
