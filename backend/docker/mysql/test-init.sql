-- MySQL Test Database Initialization Script
-- This script runs when the test database container is first created

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create test database if not exists
CREATE DATABASE IF NOT EXISTS qlib_ui_test
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE qlib_ui_test;

-- Grant privileges to test user
GRANT ALL PRIVILEGES ON qlib_ui_test.* TO 'test_user'@'%';
FLUSH PRIVILEGES;

-- Optimize MySQL for testing
SET GLOBAL innodb_buffer_pool_size = 256 * 1024 * 1024;  -- 256MB
SET GLOBAL innodb_log_file_size = 128 * 1024 * 1024;     -- 128MB
SET GLOBAL max_connections = 200;

-- Set session variables for better test performance
SET SESSION transaction_isolation = 'READ-COMMITTED';
SET SESSION innodb_flush_log_at_trx_commit = 2;

SELECT 'Test database initialized successfully' AS status;
