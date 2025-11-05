/**
 * API Client Configuration
 *
 * Axios-based HTTP client with:
 * - Request/Response interceptors
 * - Correlation ID tracking
 * - Error handling
 * - Authentication support (when implemented)
 */

import axios, { AxiosError } from 'axios';
import { message } from 'antd';

// Create axios instance
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add correlation ID for request tracking
    config.headers['X-Correlation-ID'] = crypto.randomUUID();

    // Add authentication token (when implemented)
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    // Handle different error status codes
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 400:
          message.error(data.detail || '请求参数错误');
          break;
        case 401:
          message.error('未授权,请重新登录');
          // Clear token and redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          break;
        case 403:
          message.error('无权限访问');
          break;
        case 404:
          message.error(data.detail || '资源不存在');
          break;
        case 409:
          message.error(data.detail || '资源冲突');
          break;
        case 500:
          message.error('服务器错误,请稍后重试');
          break;
        default:
          message.error(data.detail || '请求失败');
      }
    } else if (error.request) {
      // Network error
      message.error('网络连接失败,请检查网络设置');
    } else {
      message.error('请求失败');
    }

    return Promise.reject(error);
  }
);
