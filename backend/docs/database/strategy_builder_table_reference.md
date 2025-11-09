# Strategy Builder Tables - Quick Reference

## Table Summary

| Table | Rows (Est.) | Storage (Est.) | Key Indexes | Relationships |
|-------|-------------|----------------|-------------|---------------|
| **node_templates** | 100-500 | Small (< 10MB) | 10 indexes | Standalone, referenced in JSON |
| **quick_tests** | 10K-1M+ | Large (GB) | 10 indexes | → strategy_instances (FK) |
| **code_generations** | 1K-100K | Medium (100MB-1GB) | 11 indexes | → strategy_instances (FK) |
| **builder_sessions** | 1K-10K | Small (10-100MB) | 11 indexes | → strategy_instances (FK, nullable) |

---

## node_templates

**Purpose**: Reusable node library for visual logic flow builder

### Schema

| Column | Type | Nullable | Default | Index | Description |
|--------|------|----------|---------|-------|-------------|
| id | VARCHAR(36) | NO | UUID | PK | Primary key |
| name | VARCHAR(255) | NO | - | YES | Unique identifier |
| display_name | VARCHAR(255) | NO | - | NO | UI display name |
| description | TEXT | YES | NULL | NO | Usage guide |
| node_type | VARCHAR(50) | NO | - | YES | INDICATOR/CONDITION/SIGNAL/etc |
| category | VARCHAR(100) | YES | NULL | YES | Sub-category (TREND/MOMENTUM) |
| parameter_schema | JSON | NO | {} | NO | JSON Schema validation |
| default_parameters | JSON | NO | {} | NO | Default values |
| input_ports | JSON | NO | [] | NO | Input definitions |
| output_ports | JSON | NO | [] | NO | Output definitions |
| is_system_template | BOOLEAN | NO | FALSE | YES | System vs custom |
| user_id | VARCHAR(255) | YES | NULL | YES | Owner (NULL for system) |
| validation_rules | JSON | YES | NULL | NO | Connection rules |
| execution_hints | JSON | YES | NULL | NO | Code gen hints |
| usage_count | INTEGER | NO | 0 | NO | Usage tracking |
| icon | VARCHAR(100) | YES | NULL | NO | Icon identifier |
| color | VARCHAR(50) | YES | NULL | NO | Color code |
| version | VARCHAR(50) | NO | 1.0.0 | NO | Template version |
| created_at | DATETIME | NO | now() | NO | Creation time |
| updated_at | DATETIME | NO | now() | NO | Update time |
| is_deleted | BOOLEAN | NO | FALSE | YES | Soft delete |
| deleted_at | DATETIME | YES | NULL | NO | Deletion time |
| created_by | VARCHAR(255) | YES | NULL | NO | Creator |
| updated_by | VARCHAR(255) | YES | NULL | NO | Last updater |

### Indexes

1. `PRIMARY KEY (id)`
2. `ix_node_templates_name (name)`
3. `ix_node_templates_node_type (node_type)`
4. `ix_node_templates_category (category)`
5. `ix_node_templates_is_system_template (is_system_template)`
6. `ix_node_templates_user_id (user_id)`
7. `ix_node_templates_is_deleted (is_deleted)`
8. `ix_node_type_system (node_type, is_system_template)` ⭐
9. `ix_node_user_type (user_id, node_type)` ⭐
10. `ix_node_category_type (category, node_type)` ⭐
11. `ix_node_deleted_created (is_deleted, created_at)` ⭐
12. `ix_node_unique_system_name (name, is_system_template)`

### Common Queries

```sql
-- Get all system INDICATOR nodes
WHERE node_type = 'INDICATOR' AND is_system_template = TRUE;
-- Uses: ix_node_type_system

-- Get user's custom SIGNAL nodes
WHERE user_id = ? AND node_type = 'SIGNAL';
-- Uses: ix_node_user_type

-- Search by category and type
WHERE category = 'TREND' AND node_type = 'INDICATOR';
-- Uses: ix_node_category_type

-- Most popular templates
WHERE is_deleted = FALSE ORDER BY usage_count DESC;
-- Uses: ix_node_deleted_created + sort
```

---

## quick_tests

**Purpose**: Quick backtest execution and results storage

### Schema

| Column | Type | Nullable | Default | Index | Description |
|--------|------|----------|---------|-------|-------------|
| id | VARCHAR(36) | NO | UUID | PK | Primary key |
| instance_id | VARCHAR(36) | NO | - | YES | FK to strategy_instances |
| user_id | VARCHAR(255) | NO | - | YES | Test initiator |
| test_name | VARCHAR(255) | YES | NULL | NO | Optional name |
| test_config | JSON | NO | - | NO | Test parameters |
| logic_flow_snapshot | JSON | NO | - | NO | Logic flow version |
| parameters_snapshot | JSON | NO | {} | NO | Parameters version |
| status | VARCHAR(50) | NO | PENDING | YES | PENDING/RUNNING/COMPLETED/FAILED |
| test_result | JSON | YES | NULL | NO | Complete results |
| metrics_summary | JSON | YES | NULL | NO | Key metrics |
| error_message | TEXT | YES | NULL | NO | Failure reason |
| execution_time | FLOAT | YES | NULL | NO | Seconds |
| started_at | DATETIME | YES | NULL | NO | Start time |
| completed_at | DATETIME | YES | NULL | YES | Completion time |
| created_at | DATETIME | NO | now() | NO | Creation time |
| updated_at | DATETIME | NO | now() | NO | Update time |
| is_deleted | BOOLEAN | NO | FALSE | YES | Soft delete |
| deleted_at | DATETIME | YES | NULL | NO | Deletion time |
| created_by | VARCHAR(255) | YES | NULL | NO | Creator |
| updated_by | VARCHAR(255) | YES | NULL | NO | Last updater |

### Indexes

1. `PRIMARY KEY (id)`
2. `FOREIGN KEY (instance_id) REFERENCES strategy_instances(id) ON DELETE CASCADE`
3. `ix_quick_tests_instance_id (instance_id)`
4. `ix_quick_tests_user_id (user_id)`
5. `ix_quick_tests_status (status)`
6. `ix_quick_tests_completed_at (completed_at)`
7. `ix_quick_tests_is_deleted (is_deleted)`
8. `ix_quicktest_instance_status (instance_id, status)` ⭐
9. `ix_quicktest_user_created (user_id, created_at)` ⭐
10. `ix_quicktest_status_created (status, created_at)` ⭐
11. `ix_quicktest_user_instance (user_id, instance_id)` ⭐
12. `ix_quicktest_deleted_completed (is_deleted, completed_at)` ⭐

### Common Queries

```sql
-- Get completed tests for strategy
WHERE instance_id = ? AND status = 'COMPLETED';
-- Uses: ix_quicktest_instance_status

-- User's recent test history
WHERE user_id = ? ORDER BY created_at DESC LIMIT 10;
-- Uses: ix_quicktest_user_created

-- Failed tests in last 24h
WHERE status = 'FAILED' AND created_at > NOW() - INTERVAL 1 DAY;
-- Uses: ix_quicktest_status_created

-- User's tests for specific strategy
WHERE user_id = ? AND instance_id = ?;
-- Uses: ix_quicktest_user_instance
```

---

## code_generations

**Purpose**: Logic flow to Python code conversion history

### Schema

| Column | Type | Nullable | Default | Index | Description |
|--------|------|----------|---------|-------|-------------|
| id | VARCHAR(36) | NO | UUID | PK | Primary key |
| instance_id | VARCHAR(36) | NO | - | YES | FK to strategy_instances |
| user_id | VARCHAR(255) | NO | - | YES | Code requester |
| logic_flow_snapshot | JSON | NO | - | NO | Logic flow version |
| parameters_snapshot | JSON | NO | {} | NO | Parameters version |
| generated_code | TEXT | NO | - | NO | Python code |
| code_hash | VARCHAR(64) | NO | - | YES | SHA-256 hash |
| validation_status | VARCHAR(50) | NO | PENDING | YES | VALID/SYNTAX_ERROR/etc |
| validation_result | JSON | YES | NULL | NO | Validation details |
| syntax_check_passed | BOOLEAN | YES | NULL | NO | Syntax check result |
| security_check_passed | BOOLEAN | YES | NULL | NO | Security scan result |
| code_version | VARCHAR(50) | NO | 1.0.0 | NO | Generator version |
| line_count | INTEGER | YES | NULL | NO | Code lines |
| complexity_score | INTEGER | YES | NULL | NO | Cyclomatic complexity |
| generation_time | FLOAT | YES | NULL | NO | Seconds |
| created_at | DATETIME | NO | now() | NO | Creation time |
| updated_at | DATETIME | NO | now() | NO | Update time |
| is_deleted | BOOLEAN | NO | FALSE | YES | Soft delete |
| deleted_at | DATETIME | YES | NULL | NO | Deletion time |
| created_by | VARCHAR(255) | YES | NULL | NO | Creator |
| updated_by | VARCHAR(255) | YES | NULL | NO | Last updater |

### Indexes

1. `PRIMARY KEY (id)`
2. `FOREIGN KEY (instance_id) REFERENCES strategy_instances(id) ON DELETE CASCADE`
3. `ix_code_generations_instance_id (instance_id)`
4. `ix_code_generations_user_id (user_id)`
5. `ix_code_generations_code_hash (code_hash)`
6. `ix_code_generations_validation_status (validation_status)`
7. `ix_code_generations_is_deleted (is_deleted)`
8. `ix_codegen_instance_created (instance_id, created_at)` ⭐
9. `ix_codegen_user_created (user_id, created_at)` ⭐
10. `ix_codegen_validation_status (validation_status, created_at)` ⭐
11. `ix_codegen_user_instance (user_id, instance_id)` ⭐
12. `ix_codegen_hash_instance (code_hash, instance_id)` ⭐
13. `ix_codegen_deleted_created (is_deleted, created_at)` ⭐

### Common Queries

```sql
-- Code generation history for strategy
WHERE instance_id = ? ORDER BY created_at DESC;
-- Uses: ix_codegen_instance_created

-- Check for duplicate code
WHERE code_hash = ? AND instance_id = ?;
-- Uses: ix_codegen_hash_instance

-- Recent validation failures
WHERE validation_status = 'SECURITY_ERROR' ORDER BY created_at DESC;
-- Uses: ix_codegen_validation_status

-- User's code generations
WHERE user_id = ? ORDER BY created_at DESC;
-- Uses: ix_codegen_user_created
```

---

## builder_sessions

**Purpose**: User session management for draft auto-save

### Schema

| Column | Type | Nullable | Default | Index | Description |
|--------|------|----------|---------|-------|-------------|
| id | VARCHAR(36) | NO | UUID | PK | Primary key |
| instance_id | VARCHAR(36) | YES | NULL | YES | FK (nullable for new) |
| user_id | VARCHAR(255) | NO | - | YES | Session owner |
| session_type | VARCHAR(50) | NO | DRAFT | YES | DRAFT/AUTOSAVE/COLLABORATIVE |
| session_name | VARCHAR(255) | YES | NULL | NO | Optional name |
| draft_logic_flow | JSON | NO | - | NO | Draft data |
| draft_parameters | JSON | NO | {} | NO | Draft params |
| draft_metadata | JSON | YES | NULL | NO | UI state |
| is_active | BOOLEAN | NO | TRUE | YES | Active flag |
| last_activity_at | DATETIME | NO | CURRENT_TIMESTAMP | YES | Last activity |
| expires_at | DATETIME | YES | NULL | YES | Expiration |
| collaborator_ids | JSON | YES | NULL | NO | Collaborators (future) |
| lock_info | JSON | YES | NULL | NO | Lock data (future) |
| created_at | DATETIME | NO | now() | NO | Creation time |
| updated_at | DATETIME | NO | now() | NO | Update time |
| is_deleted | BOOLEAN | NO | FALSE | YES | Soft delete |
| deleted_at | DATETIME | YES | NULL | NO | Deletion time |
| created_by | VARCHAR(255) | YES | NULL | NO | Creator |
| updated_by | VARCHAR(255) | YES | NULL | NO | Last updater |

### Indexes

1. `PRIMARY KEY (id)`
2. `FOREIGN KEY (instance_id) REFERENCES strategy_instances(id) ON DELETE CASCADE`
3. `ix_builder_sessions_instance_id (instance_id)`
4. `ix_builder_sessions_user_id (user_id)`
5. `ix_builder_sessions_session_type (session_type)`
6. `ix_builder_sessions_is_active (is_active)`
7. `ix_builder_sessions_last_activity_at (last_activity_at)`
8. `ix_builder_sessions_expires_at (expires_at)`
9. `ix_builder_sessions_is_deleted (is_deleted)`
10. `ix_session_user_active (user_id, is_active)` ⭐
11. `ix_session_user_activity (user_id, last_activity_at)` ⭐
12. `ix_session_type_active (session_type, is_active)` ⭐
13. `ix_session_expires (expires_at, is_active)` ⭐
14. `ix_session_instance_user (instance_id, user_id)` ⭐
15. `ix_session_deleted_activity (is_deleted, last_activity_at)` ⭐

### Common Queries

```sql
-- User's active sessions
WHERE user_id = ? AND is_active = TRUE;
-- Uses: ix_session_user_active

-- User's recent sessions
WHERE user_id = ? ORDER BY last_activity_at DESC;
-- Uses: ix_session_user_activity

-- Expired sessions cleanup
WHERE expires_at < NOW() AND is_active = TRUE;
-- Uses: ix_session_expires

-- Session for specific strategy
WHERE instance_id = ? AND user_id = ?;
-- Uses: ix_session_instance_user
```

---

## Relationship Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    EXISTING TABLES                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  strategy_templates (id, name, logic_flow, ...)             │
│         │                                                     │
│         │ 1:N (template_id, nullable)                        │
│         ↓                                                     │
│  strategy_instances (id, template_id, logic_flow, ...)      │
│         │                                                     │
└─────────┼─────────────────────────────────────────────────────┘
          │
          │ Foreign Keys (ON DELETE CASCADE)
          │
          ├─────────────────┬─────────────────┬─────────────────┐
          │                 │                 │                 │
┌─────────▼──────────┐ ┌────▼─────────────┐ ┌▼────────────────┐│
│  quick_tests       │ │ code_generations │ │builder_sessions ││
├────────────────────┤ ├──────────────────┤ ├─────────────────┤│
│ instance_id (FK)   │ │ instance_id (FK) │ │ instance_id (FK)││
│ user_id            │ │ user_id          │ │ user_id         ││
│ test_config (JSON) │ │ generated_code   │ │ draft_logic_flow││
│ test_result (JSON) │ │ code_hash        │ │ is_active       ││
│ status             │ │ validation_status│ │ last_activity_at││
└────────────────────┘ └──────────────────┘ └─────────────────┘│
                                                               ││
┌──────────────────────────────────────────────────────────────┘│
│                                                                │
│  node_templates (standalone, referenced in logic_flow JSON)   │
│  - name, node_type, parameter_schema, input/output ports      │
│  - is_system_template, user_id                                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Storage Estimates

### Small Deployment (100 users, 1K strategies)

| Table | Rows | Avg Size | Total |
|-------|------|----------|-------|
| node_templates | 200 | 5 KB | 1 MB |
| quick_tests | 10,000 | 50 KB | 500 MB |
| code_generations | 5,000 | 20 KB | 100 MB |
| builder_sessions | 500 | 10 KB | 5 MB |
| **TOTAL** | | | **~600 MB** |

### Medium Deployment (1K users, 10K strategies)

| Table | Rows | Avg Size | Total |
|-------|------|----------|-------|
| node_templates | 500 | 5 KB | 2.5 MB |
| quick_tests | 100,000 | 50 KB | 5 GB |
| code_generations | 50,000 | 20 KB | 1 GB |
| builder_sessions | 2,000 | 10 KB | 20 MB |
| **TOTAL** | | | **~6 GB** |

### Large Deployment (10K users, 100K strategies)

| Table | Rows | Avg Size | Total |
|-------|------|----------|-------|
| node_templates | 1,000 | 5 KB | 5 MB |
| quick_tests | 1,000,000 | 50 KB | 50 GB |
| code_generations | 500,000 | 20 KB | 10 GB |
| builder_sessions | 10,000 | 10 KB | 100 MB |
| **TOTAL** | | | **~60 GB** |

---

## Data Retention Policies

| Table | Active | Archive | Delete |
|-------|--------|---------|--------|
| **node_templates** | Forever | N/A | Only when user requests |
| **quick_tests** | 90 days | 1 year | After 1 year (archived strategies) |
| **code_generations** | Forever (VALID) | N/A | 90 days (FAILED) |
| **builder_sessions** | Until `expires_at` | N/A | 30 days after `last_activity_at` |

---

## Index Performance Impact

### Write Performance

- **node_templates**: Low impact (12 indexes, rare writes)
- **quick_tests**: Medium impact (12 indexes, frequent writes)
- **code_generations**: Medium impact (13 indexes, moderate writes)
- **builder_sessions**: Low impact (15 indexes, infrequent writes)

### Read Performance

- Composite indexes provide 3-5x faster query execution
- Index-only scans avoid table lookups
- Covering indexes reduce I/O by 50-80%

### Maintenance

- Index size: ~20-30% of table size
- Rebuild recommended: Every 6 months
- Statistics update: Weekly for large tables

---

## Backup Recommendations

### Full Backup (Daily)

```bash
mysqldump --single-transaction \
  --tables node_templates quick_tests code_generations builder_sessions \
  > strategy_builder_backup_$(date +%Y%m%d).sql
```

### Incremental Backup (Hourly)

- Use binary log for point-in-time recovery
- Replicate to standby server for high availability

### Critical Data

1. **node_templates**: System templates are irreplaceable
2. **code_generations**: Valid code is version history
3. **quick_tests**: Results for audit and compliance
4. **builder_sessions**: Can be recreated (less critical)

---

## Migration Checklist

- [ ] Backup production database
- [ ] Review migration script: `20251109_0000_add_strategy_builder_tables.py`
- [ ] Test on staging environment
- [ ] Run `alembic upgrade head`
- [ ] Verify 4 tables created: `SHOW TABLES LIKE '%node_templates%'`
- [ ] Verify 48 total indexes created
- [ ] Seed system node templates
- [ ] Test foreign key constraints
- [ ] Monitor query performance
- [ ] Update application code to use new models

---

## Quick Commands

```bash
# Show all Strategy Builder tables
mysql> SHOW TABLES LIKE '%node_templates%';
mysql> SHOW TABLES LIKE '%quick_tests%';
mysql> SHOW TABLES LIKE '%code_generations%';
mysql> SHOW TABLES LIKE '%builder_sessions%';

# Check indexes
mysql> SHOW INDEX FROM node_templates;
mysql> SHOW INDEX FROM quick_tests;

# Table statistics
mysql> SELECT table_name, table_rows, data_length, index_length
       FROM information_schema.tables
       WHERE table_name IN ('node_templates', 'quick_tests', 'code_generations', 'builder_sessions');

# Active sessions count
mysql> SELECT COUNT(*) FROM builder_sessions WHERE is_active = true;

# Recent tests
mysql> SELECT COUNT(*) FROM quick_tests WHERE created_at > NOW() - INTERVAL 24 HOUR;
```
