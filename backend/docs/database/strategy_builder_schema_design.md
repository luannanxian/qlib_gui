# Strategy Builder Database Schema Design

## Overview

This document describes the database schema extensions for the Strategy Builder functionality, which extends the existing Strategy module with visual logic flow building capabilities.

## Architecture Summary

The Strategy Builder system consists of 4 new tables that extend the existing `StrategyTemplate` and `StrategyInstance` tables:

1. **node_templates** - Reusable node templates for visual logic flow
2. **quick_tests** - Quick backtest execution and results
3. **code_generations** - Logic flow to Python code conversion history
4. **builder_sessions** - User session management for draft auto-save

## Entity Relationship Diagram

```
┌─────────────────────┐
│ strategy_templates  │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐
│ strategy_instances  │◄────────┐
└──────────┬──────────┘         │
           │ 1                  │
           │                    │
           ├────────────────┐   │
           │ N              │ N │ N
┌──────────▼──────────┐ ┌──▼───▼──────────┐ ┌──────────▼──────────┐
│   quick_tests       │ │code_generations │ │ builder_sessions    │
└─────────────────────┘ └─────────────────┘ └─────────────────────┘

┌─────────────────────┐
│  node_templates     │ (Referenced by logic_flow JSON in templates/instances)
└─────────────────────┘
```

---

## Table Schemas

### 1. node_templates

Stores reusable node templates for the visual logic flow builder.

**Purpose:**
- Define predefined node types (indicators, conditions, signals, etc.)
- Provide parameter schemas with validation rules
- Support both system and user-defined templates
- Enable consistent node behavior across strategies

**Key Fields:**
- `name` - Unique identifier for the node template
- `display_name` - Human-readable name for UI
- `node_type` - Category (INDICATOR, CONDITION, SIGNAL, POSITION, STOP_LOSS, STOP_PROFIT, RISK_MANAGEMENT, CUSTOM)
- `parameter_schema` - JSON Schema for parameter validation
- `input_ports` / `output_ports` - Connection point definitions
- `is_system_template` - System vs user-defined flag
- `usage_count` - Track popularity for recommendations

**Sample Data:**
```json
{
  "name": "moving_average_crossover",
  "display_name": "Moving Average Crossover",
  "node_type": "INDICATOR",
  "category": "TREND",
  "parameter_schema": {
    "type": "object",
    "properties": {
      "fast_period": {"type": "integer", "minimum": 1, "maximum": 200, "default": 10},
      "slow_period": {"type": "integer", "minimum": 1, "maximum": 200, "default": 30}
    },
    "required": ["fast_period", "slow_period"]
  },
  "input_ports": [
    {"name": "price", "type": "series", "required": true}
  ],
  "output_ports": [
    {"name": "signal", "type": "boolean"}
  ]
}
```

### 2. quick_tests

Stores quick backtest configurations and results for rapid strategy validation.

**Purpose:**
- Enable fast iteration on strategy development
- Store historical test runs for comparison
- Track performance metrics over time
- Support A/B testing of strategy variations

**Key Fields:**
- `instance_id` - Foreign key to strategy_instances
- `test_config` - Test parameters (date range, stock pool, initial capital)
- `logic_flow_snapshot` - Logic flow at test time (version control)
- `status` - Execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
- `test_result` - Complete backtest results
- `metrics_summary` - Key performance metrics
- `execution_time` - Performance tracking

**Sample Data:**
```json
{
  "test_config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "stock_pool": ["AAPL", "MSFT", "GOOGL"],
    "initial_capital": 100000,
    "benchmark": "SPY"
  },
  "metrics_summary": {
    "total_return": 0.15,
    "sharpe_ratio": 1.8,
    "max_drawdown": -0.12,
    "win_rate": 0.62,
    "profit_factor": 2.1
  }
}
```

### 3. code_generations

Tracks the history of converting visual logic flows to executable Python code.

**Purpose:**
- Maintain code generation history for audit trails
- Store validation results (syntax, security checks)
- Enable code deduplication via hash
- Support rollback and version comparison

**Key Fields:**
- `instance_id` - Foreign key to strategy_instances
- `logic_flow_snapshot` - Logic flow that was converted
- `generated_code` - Resulting Python code
- `code_hash` - SHA-256 hash for deduplication
- `validation_status` - Validation result (PENDING, VALID, SYNTAX_ERROR, SECURITY_ERROR, RUNTIME_ERROR)
- `syntax_check_passed` / `security_check_passed` - Individual check results
- `complexity_score` - Cyclomatic complexity for code quality

**Sample Data:**
```json
{
  "validation_result": {
    "syntax_errors": [],
    "security_warnings": [],
    "lint_warnings": [
      {"line": 15, "message": "Variable 'result' is not used", "severity": "warning"}
    ],
    "complexity_score": 8,
    "line_count": 120
  }
}
```

### 4. builder_sessions

Manages user sessions for draft auto-save and future collaborative editing.

**Purpose:**
- Auto-save unsaved work to prevent data loss
- Store temporary drafts before strategy creation
- Support session recovery after browser crashes
- Future: Enable collaborative editing

**Key Fields:**
- `instance_id` - Optional FK to strategy_instances (NULL for new strategies)
- `session_type` - DRAFT, AUTOSAVE, COLLABORATIVE
- `draft_logic_flow` / `draft_parameters` - Unsaved changes
- `is_active` - Session status for cleanup
- `last_activity_at` - Stale session detection
- `expires_at` - Auto-cleanup timestamp
- `collaborator_ids` / `lock_info` - Future collaborative features

**Sample Data:**
```json
{
  "draft_metadata": {
    "viewport": {"zoom": 1.0, "pan_x": 0, "pan_y": 0},
    "selected_nodes": ["node_123"],
    "cursor_position": {"x": 400, "y": 300}
  },
  "lock_info": {
    "locked_by": "user_456",
    "locked_at": "2025-01-09T10:30:00Z",
    "lock_type": "editing"
  }
}
```

---

## Index Strategy

### Performance Optimization Principles

1. **Read-Heavy Workload**: Strategy builder involves frequent reads (browsing templates, viewing history)
2. **User Isolation**: Most queries filter by `user_id`
3. **Time-Based Queries**: Recent activity is accessed more frequently
4. **Status Filtering**: Active sessions, completed tests, etc.

### Detailed Index Analysis

#### node_templates

**Single-Column Indexes:**
- `ix_node_templates_name` - Node template search
- `ix_node_templates_node_type` - Filter by category
- `ix_node_templates_is_system_template` - System vs custom templates
- `ix_node_templates_user_id` - User's custom templates
- `ix_node_templates_is_deleted` - Soft delete filter

**Composite Indexes:**
- `ix_node_type_system (node_type, is_system_template)`
  - Use Case: "Show all system indicator nodes"
  - Query: `WHERE node_type='INDICATOR' AND is_system_template=true`

- `ix_node_user_type (user_id, node_type)`
  - Use Case: "Show user's custom signal nodes"
  - Query: `WHERE user_id='xxx' AND node_type='SIGNAL'`

- `ix_node_category_type (category, node_type)`
  - Use Case: "Show all TREND indicators"
  - Query: `WHERE category='TREND' AND node_type='INDICATOR'`

- `ix_node_deleted_created (is_deleted, created_at)`
  - Use Case: "Recent active templates"
  - Query: `WHERE is_deleted=false ORDER BY created_at DESC`

#### quick_tests

**Single-Column Indexes:**
- `ix_quick_tests_instance_id` - All tests for a strategy
- `ix_quick_tests_user_id` - User's test history
- `ix_quick_tests_status` - Filter by execution status
- `ix_quick_tests_completed_at` - Recent completions

**Composite Indexes:**
- `ix_quicktest_instance_status (instance_id, status)`
  - Use Case: "Show completed tests for this strategy"
  - Query: `WHERE instance_id='xxx' AND status='COMPLETED'`

- `ix_quicktest_user_created (user_id, created_at)`
  - Use Case: "User's recent test history"
  - Query: `WHERE user_id='xxx' ORDER BY created_at DESC`

- `ix_quicktest_status_created (status, created_at)`
  - Use Case: "Recently failed tests across all users"
  - Query: `WHERE status='FAILED' ORDER BY created_at DESC`

- `ix_quicktest_user_instance (user_id, instance_id)`
  - Use Case: "User's tests for a specific strategy"
  - Query: `WHERE user_id='xxx' AND instance_id='yyy'`

#### code_generations

**Single-Column Indexes:**
- `ix_code_generations_code_hash` - Deduplication lookups
- `ix_code_generations_validation_status` - Filter by validation result

**Composite Indexes:**
- `ix_codegen_instance_created (instance_id, created_at)`
  - Use Case: "Code generation history for strategy"
  - Query: `WHERE instance_id='xxx' ORDER BY created_at DESC`

- `ix_codegen_hash_instance (code_hash, instance_id)`
  - Use Case: "Check if this code was already generated for this strategy"
  - Query: `WHERE code_hash='xxx' AND instance_id='yyy'`

- `ix_codegen_validation_status (validation_status, created_at)`
  - Use Case: "Recent validation failures"
  - Query: `WHERE validation_status='SECURITY_ERROR' ORDER BY created_at DESC`

#### builder_sessions

**Single-Column Indexes:**
- `ix_builder_sessions_is_active` - Active session filter
- `ix_builder_sessions_last_activity_at` - Stale session cleanup
- `ix_builder_sessions_expires_at` - Session expiration

**Composite Indexes:**
- `ix_session_user_active (user_id, is_active)`
  - Use Case: "User's active sessions"
  - Query: `WHERE user_id='xxx' AND is_active=true`

- `ix_session_user_activity (user_id, last_activity_at)`
  - Use Case: "User's recent sessions"
  - Query: `WHERE user_id='xxx' ORDER BY last_activity_at DESC`

- `ix_session_expires (expires_at, is_active)`
  - Use Case: "Cleanup expired sessions"
  - Query: `WHERE expires_at < NOW() AND is_active=true`

---

## Query Optimization Recommendations

### 1. High-Frequency Queries

**Query: Get User's Active Builder Session**
```sql
SELECT * FROM builder_sessions
WHERE user_id = ? AND is_active = true
ORDER BY last_activity_at DESC LIMIT 1;
```
- Uses: `ix_session_user_active (user_id, is_active)`
- Optimization: Covering index could include `last_activity_at`

**Query: Recent Quick Tests for Strategy**
```sql
SELECT * FROM quick_tests
WHERE instance_id = ? AND is_deleted = false
ORDER BY created_at DESC LIMIT 10;
```
- Uses: `ix_quicktest_instance_status (instance_id, status)` + soft delete filter
- Optimization: Consider covering index with `created_at`

**Query: Search Node Templates by Type and Category**
```sql
SELECT * FROM node_templates
WHERE node_type = ? AND category = ? AND is_deleted = false
ORDER BY usage_count DESC;
```
- Uses: `ix_node_category_type (category, node_type)`
- Optimization: Add `usage_count` to index for index-only scan

### 2. Batch Operations

**Cleanup Expired Sessions (Scheduled Job)**
```sql
UPDATE builder_sessions
SET is_active = false
WHERE expires_at < NOW() AND is_active = true;
```
- Uses: `ix_session_expires (expires_at, is_active)`
- Run: Every 15 minutes
- Performance: Index scan, minimal overhead

**Increment Node Template Usage Count**
```sql
UPDATE node_templates
SET usage_count = usage_count + 1
WHERE id = ?;
```
- Uses: Primary key index
- Consider: Batch updates or async increment

### 3. Analytics Queries

**Popular Node Templates**
```sql
SELECT node_type, name, usage_count
FROM node_templates
WHERE is_system_template = true AND is_deleted = false
ORDER BY usage_count DESC LIMIT 20;
```
- Uses: `ix_node_type_system (node_type, is_system_template)` + `usage_count` index
- Optimization: Covering index for read-only analytics

**User's Test Success Rate**
```sql
SELECT
    user_id,
    COUNT(*) as total_tests,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as successful_tests
FROM quick_tests
WHERE user_id = ? AND is_deleted = false
GROUP BY user_id;
```
- Uses: `ix_quicktest_user_created (user_id, created_at)`
- Optimization: Consider materialized view for dashboard

### 4. Joining with Strategy Tables

**Get Strategy with Latest Code Generation**
```sql
SELECT
    si.id, si.name, si.status,
    cg.generated_code, cg.validation_status
FROM strategy_instances si
LEFT JOIN LATERAL (
    SELECT * FROM code_generations
    WHERE instance_id = si.id
    ORDER BY created_at DESC
    LIMIT 1
) cg ON true
WHERE si.user_id = ?;
```
- Uses: `ix_codegen_instance_created (instance_id, created_at)`
- PostgreSQL: LATERAL join for efficient latest record
- MySQL: Alternative with subquery or window function

---

## Data Retention and Archival

### Retention Policies

1. **builder_sessions**
   - Active sessions: Keep until `expires_at`
   - Inactive sessions: Keep for 30 days after `last_activity_at`
   - Auto-delete: Sessions older than 30 days

2. **quick_tests**
   - Keep all tests for active/testing strategies
   - Archive tests for archived strategies after 1 year
   - Delete tests for deleted instances after 90 days (soft delete cascade)

3. **code_generations**
   - Keep all successful generations indefinitely
   - Keep failed generations for 90 days for debugging
   - Deduplicate based on `code_hash`

4. **node_templates**
   - System templates: Never delete
   - User templates: Soft delete when user deletes
   - Check for dependencies before deletion

### Scheduled Cleanup Jobs

**Session Cleanup (Every 15 minutes)**
```sql
UPDATE builder_sessions
SET is_active = false, updated_at = NOW()
WHERE (expires_at < NOW() OR last_activity_at < NOW() - INTERVAL 30 DAY)
AND is_active = true;
```

**Test Result Archival (Daily)**
```sql
UPDATE quick_tests qt
SET is_deleted = true, deleted_at = NOW()
WHERE qt.instance_id IN (
    SELECT id FROM strategy_instances
    WHERE status = 'ARCHIVED' AND updated_at < NOW() - INTERVAL 1 YEAR
);
```

---

## JSON Field Schemas

### node_templates.parameter_schema

JSON Schema format for validating node parameters:

```json
{
  "type": "object",
  "properties": {
    "period": {
      "type": "integer",
      "minimum": 1,
      "maximum": 200,
      "default": 20,
      "description": "MA period"
    },
    "source": {
      "type": "string",
      "enum": ["close", "open", "high", "low"],
      "default": "close"
    }
  },
  "required": ["period"]
}
```

### quick_tests.test_config

Test configuration structure:

```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "stock_pool": ["AAPL", "MSFT", "GOOGL"],
  "initial_capital": 100000,
  "commission_rate": 0.001,
  "slippage": 0.0005,
  "benchmark": "SPY",
  "frequency": "1d"
}
```

### code_generations.validation_result

Validation result structure:

```json
{
  "syntax_errors": [
    {"line": 10, "message": "SyntaxError: invalid syntax"}
  ],
  "security_warnings": [
    {"severity": "high", "message": "Potential code injection detected"}
  ],
  "lint_warnings": [
    {"line": 15, "rule": "unused-variable", "message": "Variable 'x' is not used"}
  ],
  "imports_used": ["pandas", "numpy", "qlib"],
  "forbidden_imports": [],
  "complexity_score": 8,
  "line_count": 120
}
```

---

## Migration Strategy

### Step 1: Create Tables (Alembic Migration)

```bash
# Generate migration
alembic revision --autogenerate -m "add_strategy_builder_tables"

# Review and edit migration file
# Apply migration
alembic upgrade head
```

### Step 2: Seed System Node Templates

Create initial system templates for common nodes:

```python
from app.database.models.strategy_builder import NodeTemplate, NodeTypeCategory

system_templates = [
    {
        "name": "sma",
        "display_name": "Simple Moving Average",
        "node_type": NodeTypeCategory.INDICATOR,
        "category": "TREND",
        "parameter_schema": {...},
        "is_system_template": True,
    },
    # ... more templates
]

for template_data in system_templates:
    db.add(NodeTemplate(**template_data))
db.commit()
```

### Step 3: Update Application Models

Import new models in `__init__.py`:

```python
from .strategy_builder import (
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
)
```

### Step 4: Create Repository Layer

```python
class NodeTemplateRepository:
    async def get_system_templates(self, node_type: str = None):
        query = select(NodeTemplate).where(
            NodeTemplate.is_system_template == True,
            NodeTemplate.is_deleted == False
        )
        if node_type:
            query = query.where(NodeTemplate.node_type == node_type)
        return await self.db.execute(query)

    async def increment_usage_count(self, template_id: str):
        await self.db.execute(
            update(NodeTemplate)
            .where(NodeTemplate.id == template_id)
            .values(usage_count=NodeTemplate.usage_count + 1)
        )
```

---

## Testing Considerations

### Unit Tests

1. **Model Validation**
   - Test constraint violations (negative usage_count, invalid status)
   - Test JSON field serialization/deserialization
   - Test relationship loading (lazy vs eager)

2. **Repository Tests**
   - Test index usage (EXPLAIN ANALYZE)
   - Test pagination and sorting
   - Test filter combinations

### Integration Tests

1. **Complete Workflow**
   - Create session → Build logic flow → Generate code → Run quick test
   - Test version tracking across code generations
   - Test session expiration and cleanup

2. **Performance Tests**
   - Bulk insert node templates
   - Concurrent session updates
   - Large result set pagination

### Sample Test Data

```python
# Create test node template
template = NodeTemplate(
    name="test_ma",
    display_name="Test MA",
    node_type=NodeTypeCategory.INDICATOR,
    parameter_schema={"type": "object"},
    default_parameters={},
    input_ports=[],
    output_ports=[],
    is_system_template=False,
    user_id="test_user"
)

# Create test quick test
quick_test = QuickTest(
    instance_id=instance.id,
    user_id="test_user",
    test_config={"start_date": "2023-01-01"},
    logic_flow_snapshot={},
    parameters_snapshot={},
    status=QuickTestStatus.PENDING
)
```

---

## Security Considerations

### Code Generation Security

1. **Validation Layers**
   - Syntax check: `ast.parse()` to validate Python syntax
   - Security scan: Block dangerous imports (`os`, `subprocess`, `eval`, `exec`)
   - Sandbox execution: Use restricted Python environment for code validation

2. **Code Hash Deduplication**
   - Use SHA-256 hash to prevent duplicate code storage
   - Check hash before saving new code generation
   - Can save storage and improve retrieval speed

### Session Security

1. **Session Expiration**
   - Set reasonable `expires_at` (default: 24 hours)
   - Auto-cleanup stale sessions
   - Invalidate sessions on logout

2. **Draft Data Protection**
   - Encrypt sensitive parameters in `draft_parameters`
   - Validate user ownership before session access
   - Log session access for audit trails

### Access Control

1. **User Isolation**
   - All queries must filter by `user_id` (except admins)
   - Soft delete instead of hard delete for audit trail
   - Verify ownership in repository layer

2. **Template Permissions**
   - System templates: Read-only for all users
   - User templates: Owner can CRUD, others read-only (if shared)
   - Admin templates: Managed by administrators only

---

## Monitoring and Observability

### Key Metrics to Track

1. **Performance Metrics**
   - Average quick test execution time
   - Code generation time by complexity
   - Session save latency

2. **Usage Metrics**
   - Most used node templates (by `usage_count`)
   - Test success rate by user
   - Code validation failure rate

3. **System Health**
   - Active session count
   - Session cleanup job execution time
   - Database query slow log

### Recommended Alerts

1. **Quick Test Stuck**
   - Alert if test is in RUNNING state for > 10 minutes
   - Check for test jobs that failed to update status

2. **Code Validation Failures**
   - Alert if validation failure rate > 20%
   - May indicate issues with code generation logic

3. **Session Overflow**
   - Alert if active session count > 10,000
   - May indicate cleanup job failure

### Database Monitoring Queries

```sql
-- Active sessions by user
SELECT user_id, COUNT(*) as session_count
FROM builder_sessions
WHERE is_active = true
GROUP BY user_id
ORDER BY session_count DESC;

-- Test execution time percentiles
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time) as p50,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time) as p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time) as p99
FROM quick_tests
WHERE status = 'COMPLETED' AND execution_time IS NOT NULL;

-- Code validation failure breakdown
SELECT validation_status, COUNT(*)
FROM code_generations
WHERE created_at > NOW() - INTERVAL 7 DAY
GROUP BY validation_status;
```

---

## Future Enhancements

### 1. Collaborative Editing

- Real-time synchronization via WebSocket
- Operational Transform (OT) or CRDT for conflict resolution
- Lock management for concurrent edits
- Presence awareness (show who's editing)

**Schema Changes:**
- `collaborator_ids` - Array of user IDs
- `lock_info` - Lock holder and timestamp
- `edit_history` - Track all collaborative edits

### 2. Template Marketplace

- Share user templates publicly
- Template ratings and reviews
- Template versioning and updates
- Template categories and tags

**New Tables:**
- `template_marketplace` - Public template listings
- `template_downloads` - Download tracking
- `template_reviews` - User reviews and ratings

### 3. A/B Testing Framework

- Compare multiple strategy variations
- Statistical significance testing
- Automated parameter optimization
- Multi-armed bandit allocation

**Schema Enhancements:**
- Link multiple quick_tests as experiment group
- Store experiment metadata and results
- Track champion/challenger strategies

### 4. Code Optimization Suggestions

- Analyze generated code complexity
- Suggest performance improvements
- Detect common anti-patterns
- Recommend node template alternatives

**New Fields:**
- `optimization_suggestions` JSON in code_generations
- Store AST analysis results
- Track improvement acceptance rate

---

## Conclusion

This schema design provides a solid foundation for the Strategy Builder feature with:

- Efficient indexing for common query patterns
- Flexible JSON schemas for evolving requirements
- Comprehensive audit trails and version control
- Scalability for future enhancements
- Security and access control built-in

The design prioritizes developer experience, query performance, and maintainability while remaining extensible for future collaborative and marketplace features.
