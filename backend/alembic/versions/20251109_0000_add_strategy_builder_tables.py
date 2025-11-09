"""add_strategy_builder_tables

Revision ID: b1c2d3e4f5a6
Revises: 8043d0765021
Create Date: 2025-11-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '8043d0765021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Strategy Builder extension tables"""

    # ========================================
    # 1. Create node_templates table
    # ========================================
    op.create_table(
        'node_templates',
        sa.Column('name', sa.String(length=255), nullable=False, comment='Node template name'),
        sa.Column('display_name', sa.String(length=255), nullable=False, comment='Display name for UI'),
        sa.Column('description', sa.Text(), nullable=True, comment='Node description and usage guide'),
        sa.Column('node_type', sa.String(length=50), nullable=False, comment='Node category type (INDICATOR, CONDITION, SIGNAL, etc.)'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='Sub-category for better organization (e.g., TREND, MOMENTUM)'),
        sa.Column('parameter_schema', sa.JSON(), server_default='{}', nullable=False, comment='JSON Schema for node parameters with validation rules'),
        sa.Column('default_parameters', sa.JSON(), server_default='{}', nullable=False, comment='Default parameter values'),
        sa.Column('input_ports', sa.JSON(), server_default='[]', nullable=False, comment='Input port definitions (type, name, required)'),
        sa.Column('output_ports', sa.JSON(), server_default='[]', nullable=False, comment='Output port definitions (type, name)'),
        sa.Column('is_system_template', sa.Boolean(), server_default='0', nullable=False, comment='True for built-in templates, False for custom'),
        sa.Column('user_id', sa.String(length=255), nullable=True, comment='User ID for custom node templates (NULL for system templates)'),
        sa.Column('validation_rules', sa.JSON(), nullable=True, comment='Additional validation rules for node connections and parameters'),
        sa.Column('execution_hints', sa.JSON(), nullable=True, comment='Hints for code generation and execution optimization'),
        sa.Column('usage_count', sa.Integer(), server_default='0', nullable=False, comment='Number of times template has been used'),
        sa.Column('icon', sa.String(length=100), nullable=True, comment='Icon identifier or SVG for UI display'),
        sa.Column('color', sa.String(length=50), nullable=True, comment='Color code for node display in builder UI'),
        sa.Column('version', sa.String(length=50), server_default='1.0.0', nullable=False, comment='Template version for compatibility tracking'),
        # BaseDBModel columns
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Deletion timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User ID who last updated this record'),
        # Constraints
        sa.CheckConstraint('usage_count >= 0', name='check_node_usage_count_non_negative'),
        sa.PrimaryKeyConstraint('id'),
        comment='Node template storage for strategy builder',
        mysql_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    # Indexes for node_templates
    op.create_index(op.f('ix_node_templates_name'), 'node_templates', ['name'], unique=False)
    op.create_index(op.f('ix_node_templates_node_type'), 'node_templates', ['node_type'], unique=False)
    op.create_index(op.f('ix_node_templates_category'), 'node_templates', ['category'], unique=False)
    op.create_index(op.f('ix_node_templates_is_system_template'), 'node_templates', ['is_system_template'], unique=False)
    op.create_index(op.f('ix_node_templates_user_id'), 'node_templates', ['user_id'], unique=False)
    op.create_index(op.f('ix_node_templates_is_deleted'), 'node_templates', ['is_deleted'], unique=False)
    # Composite indexes
    op.create_index('ix_node_type_system', 'node_templates', ['node_type', 'is_system_template'], unique=False)
    op.create_index('ix_node_user_type', 'node_templates', ['user_id', 'node_type'], unique=False)
    op.create_index('ix_node_category_type', 'node_templates', ['category', 'node_type'], unique=False)
    op.create_index('ix_node_deleted_created', 'node_templates', ['is_deleted', 'created_at'], unique=False)
    op.create_index('ix_node_unique_system_name', 'node_templates', ['name', 'is_system_template'], unique=False)

    # ========================================
    # 2. Create quick_tests table
    # ========================================
    op.create_table(
        'quick_tests',
        sa.Column('instance_id', sa.String(length=36), nullable=False, comment='Reference to strategy instance being tested'),
        sa.Column('user_id', sa.String(length=255), nullable=False, comment='User who initiated the test'),
        sa.Column('test_name', sa.String(length=255), nullable=True, comment='Optional name for the test run'),
        sa.Column('test_config', sa.JSON(), nullable=False, comment='Test configuration (date range, stock pool, initial capital, etc.)'),
        sa.Column('logic_flow_snapshot', sa.JSON(), nullable=False, comment='Snapshot of logic flow at test time (for version tracking)'),
        sa.Column('parameters_snapshot', sa.JSON(), server_default='{}', nullable=False, comment='Snapshot of parameters at test time'),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False, comment='Test execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)'),
        sa.Column('test_result', sa.JSON(), nullable=True, comment='Test results including metrics, trades, and performance data'),
        sa.Column('metrics_summary', sa.JSON(), nullable=True, comment='Summary metrics (returns, sharpe, max drawdown, win rate, etc.)'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if test failed'),
        sa.Column('execution_time', sa.Float(), nullable=True, comment='Test execution time in seconds'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='Test start timestamp'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='Test completion timestamp'),
        # BaseDBModel columns
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Deletion timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User ID who last updated this record'),
        # Constraints
        sa.CheckConstraint('execution_time IS NULL OR execution_time >= 0', name='check_execution_time_non_negative'),
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Quick test execution and results storage',
        mysql_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    # Indexes for quick_tests
    op.create_index(op.f('ix_quick_tests_instance_id'), 'quick_tests', ['instance_id'], unique=False)
    op.create_index(op.f('ix_quick_tests_user_id'), 'quick_tests', ['user_id'], unique=False)
    op.create_index(op.f('ix_quick_tests_status'), 'quick_tests', ['status'], unique=False)
    op.create_index(op.f('ix_quick_tests_completed_at'), 'quick_tests', ['completed_at'], unique=False)
    op.create_index(op.f('ix_quick_tests_is_deleted'), 'quick_tests', ['is_deleted'], unique=False)
    # Composite indexes
    op.create_index('ix_quicktest_instance_status', 'quick_tests', ['instance_id', 'status'], unique=False)
    op.create_index('ix_quicktest_user_created', 'quick_tests', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_quicktest_status_created', 'quick_tests', ['status', 'created_at'], unique=False)
    op.create_index('ix_quicktest_user_instance', 'quick_tests', ['user_id', 'instance_id'], unique=False)
    op.create_index('ix_quicktest_deleted_completed', 'quick_tests', ['is_deleted', 'completed_at'], unique=False)

    # ========================================
    # 3. Create code_generations table
    # ========================================
    op.create_table(
        'code_generations',
        sa.Column('instance_id', sa.String(length=36), nullable=False, comment='Reference to strategy instance'),
        sa.Column('user_id', sa.String(length=255), nullable=False, comment='User who requested code generation'),
        sa.Column('logic_flow_snapshot', sa.JSON(), nullable=False, comment='Logic flow data at generation time'),
        sa.Column('parameters_snapshot', sa.JSON(), server_default='{}', nullable=False, comment='Parameters at generation time'),
        sa.Column('generated_code', sa.Text(), nullable=False, comment='Generated Python code from logic flow'),
        sa.Column('code_hash', sa.String(length=64), nullable=False, comment='SHA-256 hash of generated code for deduplication'),
        sa.Column('validation_status', sa.String(length=50), server_default='PENDING', nullable=False, comment='Validation status (PENDING, VALID, SYNTAX_ERROR, SECURITY_ERROR, RUNTIME_ERROR)'),
        sa.Column('validation_result', sa.JSON(), nullable=True, comment='Detailed validation results including errors and warnings'),
        sa.Column('syntax_check_passed', sa.Boolean(), nullable=True, comment='Whether syntax check passed'),
        sa.Column('security_check_passed', sa.Boolean(), nullable=True, comment='Whether security scan passed'),
        sa.Column('code_version', sa.String(length=50), server_default='1.0.0', nullable=False, comment='Version of code generation engine used'),
        sa.Column('line_count', sa.Integer(), nullable=True, comment='Number of lines in generated code'),
        sa.Column('complexity_score', sa.Integer(), nullable=True, comment='Cyclomatic complexity score'),
        sa.Column('generation_time', sa.Float(), nullable=True, comment='Code generation time in seconds'),
        # BaseDBModel columns
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Deletion timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User ID who last updated this record'),
        # Constraints
        sa.CheckConstraint('generation_time IS NULL OR generation_time >= 0', name='check_generation_time_non_negative'),
        sa.CheckConstraint('line_count IS NULL OR line_count >= 0', name='check_line_count_non_negative'),
        sa.CheckConstraint('complexity_score IS NULL OR complexity_score >= 0', name='check_complexity_score_non_negative'),
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Code generation history and validation results',
        mysql_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    # Indexes for code_generations
    op.create_index(op.f('ix_code_generations_instance_id'), 'code_generations', ['instance_id'], unique=False)
    op.create_index(op.f('ix_code_generations_user_id'), 'code_generations', ['user_id'], unique=False)
    op.create_index(op.f('ix_code_generations_code_hash'), 'code_generations', ['code_hash'], unique=False)
    op.create_index(op.f('ix_code_generations_validation_status'), 'code_generations', ['validation_status'], unique=False)
    op.create_index(op.f('ix_code_generations_is_deleted'), 'code_generations', ['is_deleted'], unique=False)
    # Composite indexes
    op.create_index('ix_codegen_instance_created', 'code_generations', ['instance_id', 'created_at'], unique=False)
    op.create_index('ix_codegen_user_created', 'code_generations', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_codegen_validation_status', 'code_generations', ['validation_status', 'created_at'], unique=False)
    op.create_index('ix_codegen_user_instance', 'code_generations', ['user_id', 'instance_id'], unique=False)
    op.create_index('ix_codegen_hash_instance', 'code_generations', ['code_hash', 'instance_id'], unique=False)
    op.create_index('ix_codegen_deleted_created', 'code_generations', ['is_deleted', 'created_at'], unique=False)

    # ========================================
    # 4. Create builder_sessions table
    # ========================================
    op.create_table(
        'builder_sessions',
        sa.Column('instance_id', sa.String(length=36), nullable=True, comment='Reference to strategy instance (NULL for new unsaved strategies)'),
        sa.Column('user_id', sa.String(length=255), nullable=False, comment='User who owns this session'),
        sa.Column('session_type', sa.String(length=50), server_default='DRAFT', nullable=False, comment='Session type (DRAFT, AUTOSAVE, COLLABORATIVE)'),
        sa.Column('session_name', sa.String(length=255), nullable=True, comment='Optional session name for user identification'),
        sa.Column('draft_logic_flow', sa.JSON(), nullable=False, comment='Draft logic flow data'),
        sa.Column('draft_parameters', sa.JSON(), server_default='{}', nullable=False, comment='Draft parameter values'),
        sa.Column('draft_metadata', sa.JSON(), nullable=True, comment='Additional draft metadata (cursor position, zoom level, etc.)'),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False, comment='Whether session is currently active'),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='Last user activity timestamp for session cleanup'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Session expiration timestamp'),
        sa.Column('collaborator_ids', sa.JSON(), nullable=True, comment='List of collaborator user IDs (for future collaborative editing)'),
        sa.Column('lock_info', sa.JSON(), nullable=True, comment='Locking information for collaborative editing'),
        # BaseDBModel columns
        sa.Column('id', sa.String(length=36), nullable=False, comment='Primary key (UUID)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.Column('is_deleted', sa.Boolean(), server_default='0', nullable=False, comment='Soft delete flag'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Deletion timestamp'),
        sa.Column('created_by', sa.String(length=255), nullable=True, comment='User ID who created this record'),
        sa.Column('updated_by', sa.String(length=255), nullable=True, comment='User ID who last updated this record'),
        # Constraints
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Builder session management for draft auto-save',
        mysql_charset='utf8mb4',
        mysql_engine='InnoDB'
    )

    # Indexes for builder_sessions
    op.create_index(op.f('ix_builder_sessions_instance_id'), 'builder_sessions', ['instance_id'], unique=False)
    op.create_index(op.f('ix_builder_sessions_user_id'), 'builder_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_builder_sessions_session_type'), 'builder_sessions', ['session_type'], unique=False)
    op.create_index(op.f('ix_builder_sessions_is_active'), 'builder_sessions', ['is_active'], unique=False)
    op.create_index(op.f('ix_builder_sessions_last_activity_at'), 'builder_sessions', ['last_activity_at'], unique=False)
    op.create_index(op.f('ix_builder_sessions_expires_at'), 'builder_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_builder_sessions_is_deleted'), 'builder_sessions', ['is_deleted'], unique=False)
    # Composite indexes
    op.create_index('ix_session_user_active', 'builder_sessions', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_session_user_activity', 'builder_sessions', ['user_id', 'last_activity_at'], unique=False)
    op.create_index('ix_session_type_active', 'builder_sessions', ['session_type', 'is_active'], unique=False)
    op.create_index('ix_session_expires', 'builder_sessions', ['expires_at', 'is_active'], unique=False)
    op.create_index('ix_session_instance_user', 'builder_sessions', ['instance_id', 'user_id'], unique=False)
    op.create_index('ix_session_deleted_activity', 'builder_sessions', ['is_deleted', 'last_activity_at'], unique=False)


def downgrade() -> None:
    """Remove Strategy Builder extension tables"""

    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('builder_sessions')
    op.drop_table('code_generations')
    op.drop_table('quick_tests')
    op.drop_table('node_templates')
