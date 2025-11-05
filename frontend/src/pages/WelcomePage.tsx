/**
 * Welcome Page
 *
 * Temporary landing page for the application
 */

import { Result, Button } from 'antd';
import { RocketOutlined } from '@ant-design/icons';

export default function WelcomePage() {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f0f2f5',
      }}
    >
      <Result
        icon={<RocketOutlined />}
        title="欢迎来到 Qlib-UI"
        subTitle="量化投资可视化平台 - 前端框架已就绪"
        extra={[
          <Button type="primary" key="docs" href="/docs/FRONTEND_ARCHITECTURE.md" target="_blank">
            查看架构文档
          </Button>,
        ]}
      />
    </div>
  );
}
