/**
 * Formatting Utilities
 */

import dayjs from 'dayjs';
import { DATE_FORMAT, DATETIME_FORMAT } from './constants';

/**
 * Format date to YYYY-MM-DD
 */
export function formatDate(date: string | Date): string {
  return dayjs(date).format(DATE_FORMAT);
}

/**
 * Format datetime to YYYY-MM-DD HH:mm:ss
 */
export function formatDateTime(date: string | Date): string {
  return dayjs(date).format(DATETIME_FORMAT);
}

/**
 * Format number to percentage (e.g., 0.1234 -> "12.34%")
 */
export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format number to currency (e.g., 1234.56 -> "¥1,234.56")
 */
export function formatCurrency(value: number, currency = '¥'): string {
  return `${currency}${value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Format large numbers with K/M/B suffixes
 */
export function formatCompactNumber(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toString();
}

/**
 * Format file size (bytes to human-readable)
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Truncate string with ellipsis
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}
