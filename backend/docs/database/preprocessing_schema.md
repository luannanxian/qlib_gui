# Data Preprocessing Schema Design

## Overview

This document describes the database schema design for the Data Preprocessing feature in Qlib-UI, including models, repositories, and usage patterns.

## Database Architecture

### Technology Stack
- **Database**: MySQL 8.0
- **ORM**: SQLAlchemy 2.0 (async)
- **Migration Tool**: Alembic
- **Connection Pooling**: asyncpg/aiomysql

### Design Principles
1. **Reusability**: Templates can be saved and reused across datasets
2. **Auditability**: Complete audit trail with created_by, updated_by timestamps
3. **Soft Delete**: All records support soft delete for data recovery
4. **Scalability**: Indexed for common query patterns
5. **Flexibility**: JSON fields for extensible configuration

## Data Models

### 1. DataPreprocessingRule

**Purpose**: Store preprocessing configurations (rules) and reusable templates.

**Key Features**:
- Users can save up to 20 templates per user (enforced via unique constraint + application logic)
- System templates (user_id = NULL) available to all users
- Usage tracking for popular template discovery
- Flexible JSON configuration for different rule types

**Schema**:
```sql
CREATE TABLE preprocessing_rules (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,

    -- Core Fields
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,  -- missing_value, outlier_detection, transformation, filtering
    is_template BOOLEAN NOT NULL DEFAULT 0,
    user_id VARCHAR(255),  -- NULL for system templates

    -- Configuration (JSON)
    configuration JSON NOT NULL DEFAULT '{}',
    metadata JSON NOT NULL DEFAULT '{}',

    -- References
    dataset_id VARCHAR(36),  -- Optional reference dataset

    -- Statistics
    usage_count INT NOT NULL DEFAULT 0,

    -- Timestamps
    created_at DATETIME(6) NOT NULL DEFAULT NOW(),
    updated_at DATETIME(6) NOT NULL DEFAULT NOW() ON UPDATE NOW(),

    -- Soft Delete
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    deleted_at DATETIME(6),

    -- Audit Trail
    created_by VARCHAR(255),
    updated_by VARCHAR(255),

    -- Constraints
    CONSTRAINT check_usage_count_non_negative CHECK (usage_count >= 0),
    CONSTRAINT uq_user_template_name UNIQUE (user_id, name, is_deleted),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
);
```

**Configuration JSON Structure**:

```json
// Missing Value Rule
{
  "method": "mean_fill",
  "columns": ["price", "volume"],
  "fill_value": null  // For constant_fill method
}

// Outlier Detection Rule
{
  "detection_method": "std_dev",
  "threshold": 3.0,
  "handling": "cap",
  "columns": ["price", "returns"]
}

// Transformation Rule
{
  "type": "normalize",
  "columns": ["price", "volume"],
  "range": [0, 1]  // For normalize
}

// Filtering Rule
{
  "conditions": [
    {"column": "volume", "operator": "gt", "value": 1000},
    {"column": "date", "operator": "between", "value": ["2020-01-01", "2023-12-31"]}
  ],
  "logic": "AND"  // AND/OR
}
```

**Indexes**:
- `ix_preprocessing_rule_type_template` (rule_type, is_template)
- `ix_preprocessing_rule_user_template` (user_id, is_template, is_deleted)
- `ix_preprocessing_rule_user_type` (user_id, rule_type, is_deleted)
- `ix_preprocessing_rule_deleted_usage` (is_deleted, usage_count)

### 2. DataPreprocessingTask

**Purpose**: Track execution of preprocessing operations on datasets.

**Key Features**:
- Progress monitoring (0-100%)
- Detailed error tracking and logging
- Row-level statistics (input/output counts)
- Performance metrics (execution time)
- Links to input dataset, output dataset, and rule used

**Schema**:
```sql
CREATE TABLE preprocessing_tasks (
    -- Primary Key
    id VARCHAR(36) PRIMARY KEY,

    -- Core Fields
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',

    -- Foreign Keys
    dataset_id VARCHAR(36) NOT NULL,  -- Input dataset
    rule_id VARCHAR(36),  -- NULL for ad-hoc tasks
    output_dataset_id VARCHAR(36),  -- Output dataset

    -- Execution Details
    execution_config JSON NOT NULL DEFAULT '{}',

    -- Progress Tracking
    total_operations INT NOT NULL DEFAULT 0,
    completed_operations INT NOT NULL DEFAULT 0,
    progress_percentage FLOAT NOT NULL DEFAULT 0.0,

    -- Row Statistics
    input_row_count INT NOT NULL DEFAULT 0,
    output_row_count INT NOT NULL DEFAULT 0,
    rows_affected INT NOT NULL DEFAULT 0,

    -- Error Tracking
    error_count INT NOT NULL DEFAULT 0,
    warning_count INT NOT NULL DEFAULT 0,
    error_message TEXT,

    -- Results and Logs (JSON)
    execution_results JSON,
    execution_logs JSON,

    -- Performance
    execution_time_seconds FLOAT,

    -- User Tracking
    user_id VARCHAR(255),

    -- Timestamps, Soft Delete, Audit Trail (same as above)

    -- Constraints
    CONSTRAINT check_total_operations_non_negative CHECK (total_operations >= 0),
    CONSTRAINT check_progress_range CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES preprocessing_rules(id) ON DELETE SET NULL,
    FOREIGN KEY (output_dataset_id) REFERENCES datasets(id) ON DELETE SET NULL
);
```

**Status Flow**:
```
PENDING → RUNNING → COMPLETED
                 → FAILED
                 → PARTIAL (completed with warnings)
                 → CANCELLED
```

**Indexes**:
- `ix_preprocessing_task_status_created` (status, created_at)
- `ix_preprocessing_task_user_status` (user_id, status, is_deleted)
- `ix_preprocessing_task_dataset_status` (dataset_id, status, is_deleted)
- `ix_preprocessing_task_rule_status` (rule_id, status, is_deleted)

## Enums

### Rule-Related Enums

```python
class MissingValueMethod(str, enum.Enum):
    DELETE_ROWS = "delete_rows"
    MEAN_FILL = "mean_fill"
    MEDIAN_FILL = "median_fill"
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    CONSTANT_FILL = "constant_fill"
    INTERPOLATE = "interpolate"

class OutlierDetectionMethod(str, enum.Enum):
    STANDARD_DEVIATION = "std_dev"
    QUANTILE = "quantile"
    ISOLATION_FOREST = "isolation_forest"
    MAD = "mad"  # Median Absolute Deviation

class OutlierHandlingStrategy(str, enum.Enum):
    DELETE = "delete"
    CAP = "cap"  # Winsorization
    REPLACE_MEAN = "replace_mean"
    REPLACE_MEDIAN = "replace_median"
    KEEP = "keep"

class TransformationType(str, enum.Enum):
    NORMALIZE = "normalize"  # Min-Max 0-1
    STANDARDIZE = "standardize"  # Z-score
    LOG_TRANSFORM = "log_transform"
    SQRT_TRANSFORM = "sqrt_transform"
    BOX_COX = "box_cox"
    TYPE_CONVERSION = "type_conversion"
    ROUND = "round"

class FilterOperator(str, enum.Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "ge"
    LESS_THAN = "lt"
    LESS_EQUAL = "le"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    NOT_NULL = "not_null"
    BETWEEN = "between"

class PreprocessingRuleType(str, enum.Enum):
    MISSING_VALUE = "missing_value"
    OUTLIER_DETECTION = "outlier_detection"
    TRANSFORMATION = "transformation"
    FILTERING = "filtering"

class PreprocessingTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
```

## Repository Patterns

### PreprocessingRuleRepository

**Key Methods**:

```python
# Get user's templates (max 20)
templates = await rule_repo.get_user_templates(
    user_id="user-123",
    rule_type=PreprocessingRuleType.MISSING_VALUE
)

# Count user templates (for quota enforcement)
count = await rule_repo.count_user_templates("user-123")
if count >= 20:
    raise TemplateQuotaExceeded()

# Get rules by type (including system templates)
rules = await rule_repo.get_by_type(
    rule_type=PreprocessingRuleType.OUTLIER_DETECTION,
    include_system=True,
    user_id="user-123"
)

# Get popular templates
popular = await rule_repo.get_popular_templates(limit=10)

# Increment usage when template is used
await rule_repo.increment_usage("rule-123")

# Search templates
results = await rule_repo.search_templates("outlier", user_id="user-123")
```

### PreprocessingTaskRepository

**Key Methods**:

```python
# Get user's tasks
tasks = await task_repo.get_by_user(
    user_id="user-123",
    status=PreprocessingTaskStatus.RUNNING
)

# Get active tasks
active = await task_repo.get_active_tasks(user_id="user-123")

# Get tasks by dataset
tasks = await task_repo.get_by_dataset("dataset-123")

# Get tasks using specific rule
tasks = await task_repo.get_by_rule("rule-123")

# Get statistics
stats = await task_repo.get_task_statistics(user_id="user-123")
# Returns: {
#     "total": 100,
#     "completed": 85,
#     "failed": 10,
#     "running": 5,
#     "average_execution_time": 45.2
# }
```

## Relationships

```
Dataset (1) ─────< (N) DataPreprocessingRule
  │                      │
  │                      │ (1)
  │                      │
  │                      ▼
  │ (1)              (N) DataPreprocessingTask
  ├─────────────────────> (input)
  │ (1)
  └─────────────────────> (output)
```

## Usage Examples

### Example 1: Creating a Missing Value Template

```python
from app.database.repositories import PreprocessingRuleRepository
from app.database.models import PreprocessingRuleType

# Check quota
count = await rule_repo.count_user_templates("user-123")
if count >= 20:
    raise TemplateQuotaExceeded("Maximum 20 templates allowed")

# Create template
rule = await rule_repo.create({
    "name": "Financial Data - Mean Fill",
    "description": "Fill missing prices with mean, forward fill volume",
    "rule_type": PreprocessingRuleType.MISSING_VALUE.value,
    "is_template": True,
    "user_id": "user-123",
    "configuration": {
        "rules": [
            {"columns": ["close", "open", "high", "low"], "method": "mean_fill"},
            {"columns": ["volume"], "method": "forward_fill"}
        ]
    },
    "metadata": {
        "tags": ["finance", "stock", "price"],
        "affected_columns": ["close", "open", "high", "low", "volume"]
    }
}, user_id="user-123")
```

### Example 2: Running a Preprocessing Task

```python
from app.database.repositories import PreprocessingTaskRepository, PreprocessingRuleRepository

# Get the template
rule = await rule_repo.get("rule-123")

# Increment usage count
await rule_repo.increment_usage(rule.id)

# Create task
task = await task_repo.create({
    "task_name": "Preprocess Stock Data - 2024-Q1",
    "dataset_id": "dataset-456",
    "rule_id": rule.id,
    "execution_config": rule.configuration,  # Snapshot
    "user_id": "user-123"
}, user_id="user-123")

# Update progress during execution
task.update_progress(completed=2, total=5)
await task_repo.update(task.id, {
    "status": PreprocessingTaskStatus.RUNNING.value,
    "completed_operations": 2,
    "total_operations": 5,
    "progress_percentage": 40.0
})

# Mark as completed
await task_repo.update(task.id, {
    "status": PreprocessingTaskStatus.COMPLETED.value,
    "output_dataset_id": "dataset-789",
    "output_row_count": 9500,
    "rows_affected": 500,
    "execution_time_seconds": 12.5,
    "execution_results": {
        "operations_applied": ["mean_fill", "forward_fill"],
        "statistics": {
            "missing_values_filled": 500,
            "columns_processed": 5
        }
    }
})
```

### Example 3: Querying Task History

```python
# Get user's recent tasks
recent_tasks = await task_repo.get_by_user(
    user_id="user-123",
    skip=0,
    limit=10
)

# Get failed tasks for debugging
failed_tasks = await task_repo.get_by_status(
    status=PreprocessingTaskStatus.FAILED
)

# Get preprocessing history for a dataset
dataset_tasks = await task_repo.get_by_dataset("dataset-123")

# Get statistics
stats = await task_repo.get_task_statistics(user_id="user-123")
print(f"Success rate: {stats['completed'] / stats['total'] * 100}%")
```

## Migration

**File**: `backend/alembic/versions/20251106_0000_add_data_preprocessing_tables.py`

**Apply Migration**:
```bash
cd backend
alembic upgrade head
```

**Rollback**:
```bash
alembic downgrade -1
```

## Performance Considerations

### Query Optimization

1. **Template Retrieval**: Indexed by (user_id, is_template, is_deleted) for fast user template queries
2. **Task Monitoring**: Indexed by (status, created_at) for active task polling
3. **History Queries**: Indexed by (dataset_id, status, is_deleted) for dataset preprocessing history
4. **Popular Templates**: Indexed by (is_deleted, usage_count) for top template discovery

### Expected Query Patterns

1. **Frequent**:
   - Get user's templates
   - Get active tasks
   - Get task progress
   - Get dataset preprocessing history

2. **Moderate**:
   - Search templates
   - Get popular templates
   - Get task statistics
   - Get tasks by rule

3. **Rare**:
   - Count all tasks
   - Full text search across all templates

## Data Integrity

### Constraints

1. **Template Quota**: Enforced via application logic checking `count_user_templates()`
2. **Progress Range**: CHECK constraint ensures 0 ≤ progress_percentage ≤ 100
3. **Non-negative Counts**: All count fields have CHECK constraints ≥ 0
4. **Unique Template Names**: Per user, no duplicate template names
5. **Referential Integrity**: CASCADE on dataset delete, SET NULL on rule delete

### Soft Delete Behavior

- **Rules**: Soft deleted but relationships preserved
- **Tasks**: Soft deleted with full history maintained
- **Quota**: Soft deleted templates don't count toward 20 template limit

## Testing Considerations

### Unit Tests

```python
# Test template quota enforcement
async def test_template_quota_limit():
    # Create 20 templates
    for i in range(20):
        await rule_repo.create({...}, user_id="user-123")

    # 21st should raise exception
    count = await rule_repo.count_user_templates("user-123")
    assert count == 20
    # Application should reject creation

# Test task progress updates
async def test_task_progress_update():
    task = await task_repo.create({...})
    task.update_progress(3, 5)
    assert task.progress_percentage == 60.0
```

### Integration Tests

- End-to-end preprocessing workflow
- Template reuse across multiple datasets
- Concurrent task execution
- Error handling and recovery

## Security Considerations

1. **User Isolation**: Templates scoped by user_id
2. **Audit Trail**: created_by/updated_by for all operations
3. **Soft Delete**: Data recovery capability
4. **Input Validation**: JSON schema validation for configuration fields

## Future Enhancements

1. **Template Sharing**: Allow users to share templates with teams
2. **Template Versioning**: Track template changes over time
3. **Batch Processing**: Support batch preprocessing of multiple datasets
4. **Scheduling**: Scheduled preprocessing jobs
5. **Notifications**: Task completion notifications via WebSocket
6. **Advanced Analytics**: More detailed execution metrics and insights
