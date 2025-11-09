# Strategy Builder Database Schema - Implementation Guide

## Quick Links

- **Models**: `/Users/zhenkunliu/project/qlib-ui/backend/app/database/models/strategy_builder.py`
- **Migration**: `/Users/zhenkunliu/project/qlib-ui/backend/alembic/versions/20251109_0000_add_strategy_builder_tables.py`
- **Documentation**: `/Users/zhenkunliu/project/qlib-ui/backend/docs/database/strategy_builder_schema_design.md`
- **Examples**: `/Users/zhenkunliu/project/qlib-ui/backend/docs/database/strategy_builder_usage_examples.py`

---

## Overview

This package extends the Strategy module with visual logic flow builder capabilities, adding 4 new tables:

| Table | Purpose | Key Features |
|-------|---------|--------------|
| **node_templates** | Reusable node library | System & user templates, parameter schemas, I/O ports |
| **quick_tests** | Rapid strategy validation | Backtest configs, results, performance metrics |
| **code_generations** | Logic flow → Python code | Code history, validation, security checks |
| **builder_sessions** | Draft auto-save | Session management, collaboration ready |

---

## Quick Start

### 1. Run Database Migration

```bash
cd /Users/zhenkunliu/project/qlib-ui/backend

# Review migration
alembic history

# Apply migration
alembic upgrade head

# Verify tables created
mysql -u your_user -p your_database -e "SHOW TABLES LIKE '%node_templates%';"
```

### 2. Import Models

```python
from app.database.models.strategy_builder import (
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
    # Enums
    NodeTypeCategory,
    QuickTestStatus,
    ValidationStatus,
    SessionType,
)
```

### 3. Basic Usage Example

```python
from sqlalchemy.ext.asyncio import AsyncSession

# Create a node template
template = NodeTemplate(
    name="moving_average",
    display_name="Moving Average",
    node_type=NodeTypeCategory.INDICATOR.value,
    parameter_schema={"type": "object", "properties": {...}},
    is_system_template=True
)
db.add(template)
await db.commit()

# Create a quick test
test = QuickTest(
    instance_id="instance-uuid",
    user_id="user-123",
    test_config={"start_date": "2023-01-01", ...},
    logic_flow_snapshot={...},
    status=QuickTestStatus.PENDING.value
)
db.add(test)
await db.commit()
```

---

## Table Relationships

```
StrategyTemplate (existing)
    ↓ 1:N
StrategyInstance (existing) ←┐
    ↓ 1:N                    │
    ├─→ QuickTest            │
    ├─→ CodeGeneration       │
    └─→ BuilderSession ──────┘ (optional)

NodeTemplate (standalone, referenced in logic_flow JSON)
```

---

## Key Design Decisions

### 1. No Modification to Existing Tables

All changes are additive - existing `strategy_templates` and `strategy_instances` tables remain unchanged. This ensures backward compatibility and minimal risk.

### 2. Foreign Key Relationships

- **CASCADE DELETE**: `quick_tests`, `code_generations`, `builder_sessions` are deleted when parent `strategy_instance` is deleted
- **SET NULL**: Optional relationships (e.g., `builder_sessions.instance_id` for new unsaved strategies)
- **Soft Delete**: All tables inherit `is_deleted` flag from `BaseDBModel`

### 3. JSON Field Usage

JSON fields store flexible, evolving schemas:

- `parameter_schema` - JSON Schema validation rules
- `logic_flow_snapshot` - Version control for logic flows
- `test_result` - Complex backtest results
- `validation_result` - Detailed validation messages

### 4. Index Strategy

**Composite Indexes for High-Frequency Queries:**

- `(user_id, is_active)` - User's active sessions
- `(instance_id, status)` - Strategy's completed tests
- `(node_type, is_system_template)` - System indicator nodes
- `(code_hash, instance_id)` - Code deduplication

**Time-Based Indexes:**

- `(created_at, is_deleted)` - Recent active records
- `(last_activity_at, is_active)` - Session cleanup

---

## Migration Checklist

### Pre-Migration

- [ ] Review migration file: `20251109_0000_add_strategy_builder_tables.py`
- [ ] Backup database
- [ ] Test migration on staging environment
- [ ] Verify no conflicts with existing tables

### Migration

- [ ] Run `alembic upgrade head`
- [ ] Verify all 4 tables created
- [ ] Check all indexes created (40+ indexes total)
- [ ] Test foreign key constraints

### Post-Migration

- [ ] Seed system node templates (see below)
- [ ] Update `__init__.py` to import new models
- [ ] Create repository layer for new models
- [ ] Update API endpoints to use new tables

---

## Seeding System Templates

After migration, populate system node templates:

```python
# backend/scripts/seed_node_templates.py

from app.database.models.strategy_builder import NodeTemplate, NodeTypeCategory

SYSTEM_TEMPLATES = [
    {
        "name": "sma",
        "display_name": "Simple Moving Average",
        "node_type": NodeTypeCategory.INDICATOR.value,
        "category": "TREND",
        "parameter_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 20
                }
            }
        },
        "default_parameters": {"period": 20},
        "input_ports": [{"name": "price", "type": "series"}],
        "output_ports": [{"name": "ma", "type": "series"}],
        "is_system_template": True,
        "icon": "chart-line",
        "color": "#3b82f6"
    },
    {
        "name": "ema",
        "display_name": "Exponential Moving Average",
        "node_type": NodeTypeCategory.INDICATOR.value,
        "category": "TREND",
        # ... similar structure
    },
    {
        "name": "rsi",
        "display_name": "Relative Strength Index",
        "node_type": NodeTypeCategory.INDICATOR.value,
        "category": "MOMENTUM",
        # ... similar structure
    },
    # Add more templates...
]

async def seed_templates(db: AsyncSession):
    for template_data in SYSTEM_TEMPLATES:
        template = NodeTemplate(**template_data)
        db.add(template)
    await db.commit()
```

Run seeding:

```bash
python -m scripts.seed_node_templates
```

---

## Common Query Patterns

### 1. Get User's Active Session

```python
session = await db.execute(
    select(BuilderSession)
    .where(
        BuilderSession.user_id == user_id,
        BuilderSession.is_active == True
    )
    .order_by(BuilderSession.last_activity_at.desc())
    .limit(1)
)
```

Uses index: `ix_session_user_active (user_id, is_active)`

### 2. Recent Quick Tests for Strategy

```python
tests = await db.execute(
    select(QuickTest)
    .where(
        QuickTest.instance_id == instance_id,
        QuickTest.is_deleted == False
    )
    .order_by(QuickTest.created_at.desc())
    .limit(10)
)
```

Uses index: `ix_quicktest_instance_status (instance_id, status)`

### 3. Search Node Templates

```python
templates = await db.execute(
    select(NodeTemplate)
    .where(
        NodeTemplate.node_type == "INDICATOR",
        NodeTemplate.is_deleted == False
    )
    .where(
        (NodeTemplate.is_system_template == True) |
        (NodeTemplate.user_id == user_id)
    )
    .order_by(NodeTemplate.usage_count.desc())
)
```

Uses index: `ix_node_type_system (node_type, is_system_template)`

### 4. Check for Duplicate Code

```python
existing = await db.execute(
    select(CodeGeneration)
    .where(
        CodeGeneration.code_hash == code_hash,
        CodeGeneration.instance_id == instance_id
    )
    .limit(1)
)
```

Uses index: `ix_codegen_hash_instance (code_hash, instance_id)`

---

## Scheduled Jobs

### 1. Session Cleanup (Every 15 minutes)

```python
async def cleanup_expired_sessions():
    await db.execute(
        update(BuilderSession)
        .where(
            (BuilderSession.expires_at < datetime.now()) |
            (BuilderSession.last_activity_at < datetime.now() - timedelta(days=30))
        )
        .where(BuilderSession.is_active == True)
        .values(is_active=False)
    )
```

### 2. Test Result Archival (Daily)

```python
async def archive_old_tests():
    # Archive tests for archived strategies older than 1 year
    await db.execute(
        update(QuickTest)
        .where(
            QuickTest.instance_id.in_(
                select(StrategyInstance.id)
                .where(
                    StrategyInstance.status == "ARCHIVED",
                    StrategyInstance.updated_at < datetime.now() - timedelta(days=365)
                )
            )
        )
        .values(is_deleted=True, deleted_at=datetime.now())
    )
```

---

## Testing

### Unit Tests

```python
# tests/database/test_strategy_builder.py

async def test_create_node_template(db_session):
    template = NodeTemplate(
        name="test_node",
        display_name="Test Node",
        node_type=NodeTypeCategory.INDICATOR.value,
        parameter_schema={},
        default_parameters={},
        input_ports=[],
        output_ports=[],
        is_system_template=False,
        user_id="test_user"
    )
    db_session.add(template)
    await db_session.commit()

    assert template.id is not None
    assert template.usage_count == 0


async def test_quick_test_cascade_delete(db_session):
    # Create instance
    instance = StrategyInstance(...)
    db_session.add(instance)

    # Create quick test
    test = QuickTest(instance_id=instance.id, ...)
    db_session.add(test)
    await db_session.commit()

    # Delete instance should cascade to test
    await db_session.delete(instance)
    await db_session.commit()

    # Test should be deleted
    result = await db_session.get(QuickTest, test.id)
    assert result is None
```

### Integration Tests

```python
async def test_complete_workflow(db_session):
    # Create session → Generate code → Run test
    session = await create_or_update_session(...)
    code_gen = await create_code_generation(...)
    quick_test = await create_quick_test(...)

    assert session.is_active == True
    assert code_gen.validation_status == "PENDING"
    assert quick_test.status == "PENDING"
```

---

## Performance Optimization

### 1. Use Eager Loading for Relationships

```python
# Bad: N+1 queries
tests = await db.execute(select(QuickTest))
for test in tests:
    print(test.instance.name)  # Triggers separate query

# Good: Eager loading
tests = await db.execute(
    select(QuickTest).options(selectinload(QuickTest.instance))
)
for test in tests:
    print(test.instance.name)  # No extra query
```

### 2. Batch Operations

```python
# Increment multiple template usage counts
template_ids = ["id1", "id2", "id3"]

await db.execute(
    update(NodeTemplate)
    .where(NodeTemplate.id.in_(template_ids))
    .values(usage_count=NodeTemplate.usage_count + 1)
)
```

### 3. Pagination

```python
# Use offset/limit with index
page = 1
page_size = 20
offset = (page - 1) * page_size

tests = await db.execute(
    select(QuickTest)
    .where(QuickTest.user_id == user_id)
    .order_by(QuickTest.created_at.desc())
    .offset(offset)
    .limit(page_size)
)
```

---

## Security Considerations

### 1. Code Validation Pipeline

```python
async def validate_generated_code(code: str) -> dict:
    """Multi-stage validation"""

    # 1. Syntax check
    try:
        ast.parse(code)
        syntax_passed = True
    except SyntaxError as e:
        return {"status": "SYNTAX_ERROR", "error": str(e)}

    # 2. Security scan
    forbidden_imports = ["os", "subprocess", "eval", "exec"]
    if any(imp in code for imp in forbidden_imports):
        return {"status": "SECURITY_ERROR", "error": "Forbidden import"}

    # 3. Complexity analysis
    complexity = calculate_complexity(code)
    if complexity > 20:
        return {"status": "VALID", "warning": "High complexity"}

    return {"status": "VALID"}
```

### 2. User Isolation

```python
# Always filter by user_id
async def get_user_templates(db: AsyncSession, user_id: str):
    return await db.execute(
        select(NodeTemplate)
        .where(
            (NodeTemplate.user_id == user_id) |
            (NodeTemplate.is_system_template == True)
        )
    )
```

### 3. Session Security

- Set reasonable `expires_at` (24 hours)
- Invalidate on logout
- Encrypt sensitive data in `draft_parameters`

---

## Monitoring

### Key Metrics

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
WHERE status = 'COMPLETED';

-- Code validation failure breakdown
SELECT validation_status, COUNT(*)
FROM code_generations
WHERE created_at > NOW() - INTERVAL 7 DAY
GROUP BY validation_status;
```

### Alerts

- Test stuck in RUNNING > 10 minutes
- Validation failure rate > 20%
- Active session count > 10,000

---

## Troubleshooting

### Problem: Migration Fails with Foreign Key Error

**Solution**: Check that parent tables exist:

```sql
SHOW TABLES LIKE 'strategy_instances';
```

If missing, run earlier migrations first.

### Problem: Duplicate Key Error on node_templates

**Solution**: Check for existing template with same name:

```sql
SELECT * FROM node_templates WHERE name = 'template_name';
```

Either use different name or update existing template.

### Problem: Slow Query on quick_tests

**Solution**: Verify indexes exist:

```sql
SHOW INDEX FROM quick_tests;
```

Should see 10+ indexes. If missing, re-run migration.

### Problem: Session Not Auto-Saving

**Solution**: Check `last_activity_at` is being updated:

```python
session.last_activity_at = datetime.now()
await db.commit()
```

---

## Next Steps

### Phase 1: Core Implementation (Week 1-2)

- [x] Database schema design
- [x] Model definitions
- [x] Migration script
- [ ] Repository layer implementation
- [ ] API endpoints for CRUD operations
- [ ] Unit tests

### Phase 2: Business Logic (Week 3-4)

- [ ] Code generation engine
- [ ] Code validation pipeline
- [ ] Quick test execution service
- [ ] Session auto-save mechanism
- [ ] Integration tests

### Phase 3: Frontend Integration (Week 5-6)

- [ ] Node template library UI
- [ ] Visual logic flow builder
- [ ] Quick test results display
- [ ] Code viewer with validation hints
- [ ] Session recovery UI

### Phase 4: Advanced Features (Week 7-8)

- [ ] Collaborative editing (WebSocket)
- [ ] Template marketplace
- [ ] A/B testing framework
- [ ] Performance optimization
- [ ] Production deployment

---

## Resources

- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org/en/20/
- **Alembic Docs**: https://alembic.sqlalchemy.org/
- **JSON Schema**: https://json-schema.org/
- **Code AST Analysis**: https://docs.python.org/3/library/ast.html

---

## Support

For questions or issues:

1. Check `/docs/database/strategy_builder_schema_design.md` for detailed design
2. Review `/docs/database/strategy_builder_usage_examples.py` for code patterns
3. Run tests: `pytest tests/database/test_strategy_builder.py`
4. Contact: Database architecture team

---

## Changelog

### 2025-11-09 - Initial Release

- Added 4 new tables: `node_templates`, `quick_tests`, `code_generations`, `builder_sessions`
- Created 40+ indexes for query optimization
- Implemented soft delete and audit trails
- Added comprehensive documentation and examples
- Migration script: `20251109_0000_add_strategy_builder_tables.py`
