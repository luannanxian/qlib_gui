"""add data preprocessing tables

Revision ID: 9a2b3c4d5e6f
Revises: 8154b5851fbf
Create Date: 2025-11-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '9a2b3c4d5e6f'
down_revision: Union[str, None] = '8154b5851fbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create preprocessing_rules and preprocessing_tasks tables"""

    # Create preprocessing_rules table
    op.create_table(
        'preprocessing_rules',
        # Primary key (UUID)
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),

        # Core fields
        sa.Column('name', sa.String(length=255), nullable=False, comment='Rule/template name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Rule description'),
        sa.Column('rule_type', sa.String(length=50), nullable=False,
                  comment='Type of preprocessing rule (missing_value, outlier, transform, filter)'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='0',
                  comment='Whether this is a reusable template (vs one-time rule)'),
        sa.Column('user_id', sa.String(length=255), nullable=True,
                  comment='User who owns this template (NULL for system templates)'),

        # Configuration
        sa.Column('configuration', mysql.JSON(), nullable=False, server_default='{}',
                  comment='Rule configuration (JSON object)'),
        sa.Column('metadata', mysql.JSON(), nullable=False, server_default='{}',
                  comment='Additional rule metadata (JSON object)'),

        # Reference dataset
        sa.Column('dataset_id', sa.String(length=36), nullable=True,
                  comment='Reference dataset ID (optional)'),

        # Statistics
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of times this rule/template was used'),

        # Timestamps (from TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'), comment='Record last update timestamp'),

        # Soft delete (from SoftDeleteMixin)
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0',
                  comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Deletion timestamp'),

        # Audit trail (from AuditMixin)
        sa.Column('created_by', sa.String(length=255), nullable=True,
                  comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True,
                  comment='User ID who last updated this record'),

        # Constraints
        sa.CheckConstraint('usage_count >= 0', name='check_usage_count_non_negative'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', 'is_deleted', name='uq_user_template_name'),

        # Table metadata
        comment='Data preprocessing rules and templates',
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )

    # Create indexes for preprocessing_rules
    op.create_index('ix_preprocessing_rule_deleted_created', 'preprocessing_rules',
                    ['is_deleted', 'created_at'])
    op.create_index('ix_preprocessing_rule_deleted_usage', 'preprocessing_rules',
                    ['is_deleted', 'usage_count'])
    op.create_index('ix_preprocessing_rule_type_template', 'preprocessing_rules',
                    ['rule_type', 'is_template'])
    op.create_index('ix_preprocessing_rule_user_template', 'preprocessing_rules',
                    ['user_id', 'is_template', 'is_deleted'])
    op.create_index('ix_preprocessing_rule_user_type', 'preprocessing_rules',
                    ['user_id', 'rule_type', 'is_deleted'])
    op.create_index(op.f('ix_preprocessing_rules_is_deleted'), 'preprocessing_rules',
                    ['is_deleted'])
    op.create_index(op.f('ix_preprocessing_rules_is_template'), 'preprocessing_rules',
                    ['is_template'])
    op.create_index(op.f('ix_preprocessing_rules_name'), 'preprocessing_rules',
                    ['name'])
    op.create_index(op.f('ix_preprocessing_rules_rule_type'), 'preprocessing_rules',
                    ['rule_type'])
    op.create_index(op.f('ix_preprocessing_rules_user_id'), 'preprocessing_rules',
                    ['user_id'])
    op.create_index(op.f('ix_preprocessing_rules_dataset_id'), 'preprocessing_rules',
                    ['dataset_id'])

    # Create preprocessing_tasks table
    op.create_table(
        'preprocessing_tasks',
        # Primary key (UUID)
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),

        # Core fields
        sa.Column('task_name', sa.String(length=255), nullable=False,
                  comment='Human-readable task name'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending',
                  comment='Task execution status'),

        # Foreign keys
        sa.Column('dataset_id', sa.String(length=36), nullable=False,
                  comment='Source dataset ID to preprocess'),
        sa.Column('rule_id', sa.String(length=36), nullable=True,
                  comment='Preprocessing rule/template used (NULL for ad-hoc tasks)'),
        sa.Column('output_dataset_id', sa.String(length=36), nullable=True,
                  comment='Output dataset ID (preprocessed result)'),

        # Execution details
        sa.Column('execution_config', mysql.JSON(), nullable=False, server_default='{}',
                  comment='Execution configuration snapshot (JSON object)'),

        # Progress tracking
        sa.Column('total_operations', sa.Integer(), nullable=False, server_default='0',
                  comment='Total preprocessing operations to execute'),
        sa.Column('completed_operations', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of completed operations'),
        sa.Column('progress_percentage', sa.Float(), nullable=False, server_default='0.0',
                  comment='Progress percentage (0-100)'),

        # Row statistics
        sa.Column('input_row_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of rows in input dataset'),
        sa.Column('output_row_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of rows in output dataset'),
        sa.Column('rows_affected', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of rows modified/removed by preprocessing'),

        # Error tracking
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of errors encountered'),
        sa.Column('warning_count', sa.Integer(), nullable=False, server_default='0',
                  comment='Number of warnings generated'),
        sa.Column('error_message', sa.Text(), nullable=True,
                  comment='Error message if task failed'),

        # Results and logs
        sa.Column('execution_results', mysql.JSON(), nullable=True,
                  comment='Detailed execution results (JSON object)'),
        sa.Column('execution_logs', mysql.JSON(), nullable=True,
                  comment='Execution logs and messages (JSON array)'),

        # Performance metrics
        sa.Column('execution_time_seconds', sa.Float(), nullable=True,
                  comment='Task execution time in seconds'),

        # User tracking
        sa.Column('user_id', sa.String(length=255), nullable=True,
                  comment='User who initiated the task (optional for now)'),

        # Timestamps (from TimestampMixin)
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()'), comment='Record last update timestamp'),

        # Soft delete (from SoftDeleteMixin)
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0',
                  comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Deletion timestamp'),

        # Audit trail (from AuditMixin)
        sa.Column('created_by', sa.String(length=255), nullable=True,
                  comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True,
                  comment='User ID who last updated this record'),

        # Constraints
        sa.CheckConstraint('total_operations >= 0', name='check_total_operations_non_negative'),
        sa.CheckConstraint('completed_operations >= 0', name='check_completed_operations_non_negative'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100',
                          name='check_progress_range'),
        sa.CheckConstraint('input_row_count >= 0', name='check_input_rows_non_negative'),
        sa.CheckConstraint('output_row_count >= 0', name='check_output_rows_non_negative'),
        sa.CheckConstraint('rows_affected >= 0', name='check_affected_rows_non_negative'),
        sa.CheckConstraint('error_count >= 0', name='check_error_count_non_negative'),
        sa.CheckConstraint('warning_count >= 0', name='check_warning_count_non_negative'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['preprocessing_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['output_dataset_id'], ['datasets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),

        # Table metadata
        comment='Data preprocessing task execution tracking',
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4'
    )

    # Create indexes for preprocessing_tasks
    op.create_index('ix_preprocessing_task_dataset_status', 'preprocessing_tasks',
                    ['dataset_id', 'status', 'is_deleted'])
    op.create_index('ix_preprocessing_task_deleted_created', 'preprocessing_tasks',
                    ['is_deleted', 'created_at'])
    op.create_index('ix_preprocessing_task_deleted_updated', 'preprocessing_tasks',
                    ['is_deleted', 'updated_at'])
    op.create_index('ix_preprocessing_task_rule_status', 'preprocessing_tasks',
                    ['rule_id', 'status', 'is_deleted'])
    op.create_index('ix_preprocessing_task_status_created', 'preprocessing_tasks',
                    ['status', 'created_at'])
    op.create_index('ix_preprocessing_task_user_status', 'preprocessing_tasks',
                    ['user_id', 'status', 'is_deleted'])
    op.create_index(op.f('ix_preprocessing_tasks_dataset_id'), 'preprocessing_tasks',
                    ['dataset_id'])
    op.create_index(op.f('ix_preprocessing_tasks_is_deleted'), 'preprocessing_tasks',
                    ['is_deleted'])
    op.create_index(op.f('ix_preprocessing_tasks_output_dataset_id'), 'preprocessing_tasks',
                    ['output_dataset_id'])
    op.create_index(op.f('ix_preprocessing_tasks_rule_id'), 'preprocessing_tasks',
                    ['rule_id'])
    op.create_index(op.f('ix_preprocessing_tasks_status'), 'preprocessing_tasks',
                    ['status'])
    op.create_index(op.f('ix_preprocessing_tasks_task_name'), 'preprocessing_tasks',
                    ['task_name'])
    op.create_index(op.f('ix_preprocessing_tasks_user_id'), 'preprocessing_tasks',
                    ['user_id'])


def downgrade() -> None:
    """Drop preprocessing_tasks and preprocessing_rules tables"""

    # Drop preprocessing_tasks table (must drop first due to foreign key)
    op.drop_index(op.f('ix_preprocessing_tasks_user_id'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_task_name'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_status'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_rule_id'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_output_dataset_id'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_is_deleted'), table_name='preprocessing_tasks')
    op.drop_index(op.f('ix_preprocessing_tasks_dataset_id'), table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_user_status', table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_status_created', table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_rule_status', table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_deleted_updated', table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_deleted_created', table_name='preprocessing_tasks')
    op.drop_index('ix_preprocessing_task_dataset_status', table_name='preprocessing_tasks')
    op.drop_table('preprocessing_tasks')

    # Drop preprocessing_rules table
    op.drop_index(op.f('ix_preprocessing_rules_dataset_id'), table_name='preprocessing_rules')
    op.drop_index(op.f('ix_preprocessing_rules_user_id'), table_name='preprocessing_rules')
    op.drop_index(op.f('ix_preprocessing_rules_rule_type'), table_name='preprocessing_rules')
    op.drop_index(op.f('ix_preprocessing_rules_name'), table_name='preprocessing_rules')
    op.drop_index(op.f('ix_preprocessing_rules_is_template'), table_name='preprocessing_rules')
    op.drop_index(op.f('ix_preprocessing_rules_is_deleted'), table_name='preprocessing_rules')
    op.drop_index('ix_preprocessing_rule_user_type', table_name='preprocessing_rules')
    op.drop_index('ix_preprocessing_rule_user_template', table_name='preprocessing_rules')
    op.drop_index('ix_preprocessing_rule_type_template', table_name='preprocessing_rules')
    op.drop_index('ix_preprocessing_rule_deleted_usage', table_name='preprocessing_rules')
    op.drop_index('ix_preprocessing_rule_deleted_created', table_name='preprocessing_rules')
    op.drop_table('preprocessing_rules')
