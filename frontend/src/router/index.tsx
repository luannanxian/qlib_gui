/**
 * Router Configuration
 *
 * Application routing with React Router v6
 */

import { createBrowserRouter, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Spin } from 'antd';

// Lazy load pages
const WelcomePage = lazy(() => import('../pages/WelcomePage'));

// Loading component
function PageLoading() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
      }}
    >
      <Spin size="large" tip="加载中..." />
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <Suspense fallback={<PageLoading />}>
        <WelcomePage />
      </Suspense>
    ),
  },
  {
    path: '/datasets',
    element: <Navigate to="/" replace />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
