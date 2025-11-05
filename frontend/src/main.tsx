import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import App from './App.tsx';
import './styles/global.css';

// Configure dayjs
dayjs.locale('zh-cn');

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Enable MSW (Mock Service Worker) in development
async function enableMocking() {
  if (import.meta.env.MODE === 'development' && import.meta.env.VITE_ENABLE_MOCK === 'true') {
    try {
      const { worker } = await import('./mocks/browser');
      return worker.start({
        onUnhandledRequest: 'bypass', // Allow unhandled requests to pass through
      });
    } catch (error) {
      console.warn('MSW not initialized:', error);
    }
  }
  return Promise.resolve();
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          locale={zhCN}
          theme={{
            token: {
              colorPrimary: '#1890ff',
              borderRadius: 6,
            },
          }}
        >
          <App />
        </ConfigProvider>
      </QueryClientProvider>
    </React.StrictMode>
  );
});
