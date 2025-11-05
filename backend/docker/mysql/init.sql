-- MySQL Initialization Script
-- This script runs when the MySQL container is first created

-- Set character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Use the database
USE qlib_ui;

-- Create initial database schema (will be managed by Alembic migrations)
-- Note: This is just for reference. Use Alembic migrations for schema management.

-- Show database info
SELECT 'MySQL initialized successfully' AS status;
SELECT VERSION() AS mysql_version;
SELECT DATABASE() AS current_database;
