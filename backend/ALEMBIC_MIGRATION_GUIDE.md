# Alembic Database Migration Guide

This document explains how to use Alembic for database schema migrations in the qlib-ui backend.

## Overview

Alembic is configured to work with our async SQLAlchemy setup and automatically tracks changes to our database models.

## Configuration

- **Configuration file**: `alembic.ini`
- **Environment setup**: `alembic/env.py`
- **Migration scripts**: `alembic/versions/`

The database URL is automatically loaded from `app.config.settings.DATABASE_URL`, so you don't need to configure it manually.

## Common Commands

### 1. Create a New Migration

After modifying database models, generate a new migration:

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration for manual edits
alembic revision -m "description of changes"
```

### 2. Apply Migrations

```bash
# Upgrade to the latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade <revision_id>
```

### 3. Downgrade Migrations

```bash
# Downgrade by one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade to base (remove all migrations)
alembic downgrade base
```

### 4. Check Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Migration Workflow

### Typical Development Workflow

1. **Modify Models**: Update SQLAlchemy models in `app/database/models/`

2. **Generate Migration**:
   ```bash
   alembic revision --autogenerate -m "add user_role column"
   ```

3. **Review Migration**: Check the generated file in `alembic/versions/`
   - Verify the upgrade() function
   - Verify the downgrade() function
   - Ensure data migrations are handled correctly

4. **Test Migration**:
   ```bash
   # Apply migration
   alembic upgrade head

   # Test downgrade
   alembic downgrade -1

   # Re-apply
   alembic upgrade head
   ```

5. **Commit Migration**: Add the migration file to git

### Production Deployment Workflow

1. **Backup Database**: Always backup before applying migrations

2. **Check Current State**:
   ```bash
   alembic current
   alembic history
   ```

3. **Apply Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Verify**: Check application functionality

5. **Rollback if needed**:
   ```bash
   alembic downgrade -1
   ```

## Migration File Structure

Migration files follow this naming pattern:
```
YYYYMMDD_HHMM_<revision>_<description>.py
```

Example: `20251105_1903_8154b5851fbf_initial_database_schema.py`

Each migration file contains:

```python
def upgrade() -> None:
    """Apply migration changes"""
    # Add your upgrade logic here
    pass

def downgrade() -> None:
    """Revert migration changes"""
    # Add your downgrade logic here
    pass
```

## Best Practices

### 1. Always Auto-generate First
Use `--autogenerate` to let Alembic detect changes, then review and modify if needed.

### 2. Review Generated Migrations
Auto-generated migrations may not be perfect. Always review:
- Data type changes
- Index additions/removals
- Foreign key constraints
- Default values

### 3. Test Both Directions
Always test both `upgrade` and `downgrade` to ensure reversibility.

### 4. Handle Data Migrations
For schema changes that affect data:

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add column
    op.add_column('users', sa.Column('status', sa.String(20)))

    # Migrate existing data
    op.execute("UPDATE users SET status = 'active'")

    # Make column non-nullable
    op.alter_column('users', 'status', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'status')
```

### 5. Use Batch Operations for SQLite

For SQLite compatibility (used in tests):

```python
with op.batch_alter_table('users') as batch_op:
    batch_op.add_column(sa.Column('status', sa.String(20)))
```

### 6. Document Complex Migrations

Add comments explaining complex migration logic:

```python
def upgrade() -> None:
    """
    This migration:
    1. Adds is_active column
    2. Migrates existing active users
    3. Removes old status column
    """
    # Migration logic here
```

## Troubleshooting

### Issue: Migration Conflicts

**Problem**: Multiple developers create migrations with same revision base

**Solution**:
```bash
# Merge migration heads
alembic merge <rev1> <rev2> -m "merge migrations"
```

### Issue: Manual Schema Changes

**Problem**: Database schema doesn't match Alembic's expected state

**Solution**:
```bash
# Mark specific version as current without running migrations
alembic stamp <revision>

# Or stamp to head
alembic stamp head
```

### Issue: Rollback Failed

**Problem**: Downgrade fails due to data constraints

**Solution**:
- Review the downgrade() function
- May need to manually handle data before downgrade
- Consider if full rollback is necessary

## Integration with Application

### Automatic Migrations on Startup (Optional)

Add to `app/main.py`:

```python
from alembic import command
from alembic.config import Config

@app.on_event("startup")
async def run_migrations():
    """Run migrations on application startup"""
    if settings.AUTO_MIGRATE:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
```

**Warning**: Only use auto-migration in development. In production, run migrations manually with proper backup and testing.

## Common Migration Scenarios

### 1. Adding a New Column

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'email')
```

### 2. Adding an Index

```python
def upgrade() -> None:
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade() -> None:
    op.drop_index('ix_users_email', 'users')
```

### 3. Adding a Foreign Key

```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_orders_user_id',
        'orders',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
```

### 4. Renaming a Column

```python
def upgrade() -> None:
    op.alter_column('users', 'name', new_column_name='full_name')

def downgrade() -> None:
    op.alter_column('users', 'full_name', new_column_name='name')
```

## Testing Migrations

### Unit Test Migrations

```python
import pytest
from alembic import command
from alembic.config import Config

def test_migration_upgrade_downgrade():
    """Test that migration can upgrade and downgrade"""
    alembic_cfg = Config("alembic.ini")

    # Upgrade
    command.upgrade(alembic_cfg, "head")

    # Downgrade
    command.downgrade(alembic_cfg, "-1")

    # Re-upgrade
    command.upgrade(alembic_cfg, "head")
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Async SQLAlchemy with Alembic](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)

## Initial Setup Complete

The initial database schema migration has been created:
- Migration file: `20251105_1903_8154b5851fbf_initial_database_schema.py`
- Includes all current models: Dataset, ChartConfig, UserPreferences, ImportTask
- Includes all indexes from recent optimization work

To apply the migration to your database:
```bash
alembic upgrade head
```
