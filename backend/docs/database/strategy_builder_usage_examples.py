"""
Strategy Builder Database Usage Examples

This file demonstrates how to use the Strategy Builder models
in typical application scenarios.
"""

from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import (
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
    NodeTypeCategory,
    QuickTestStatus,
    ValidationStatus,
    SessionType,
)
from app.database.models.strategy import StrategyInstance


# ==========================================
# 1. Node Template Operations
# ==========================================

async def create_system_node_template(db: AsyncSession):
    """Create a system node template for Moving Average indicator"""

    template = NodeTemplate(
        name="simple_moving_average",
        display_name="Simple Moving Average",
        description="Calculate simple moving average over a specified period",
        node_type=NodeTypeCategory.INDICATOR.value,
        category="TREND",
        parameter_schema={
            "type": "object",
            "properties": {
                "period": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 20,
                    "description": "Number of periods for MA calculation"
                },
                "source": {
                    "type": "string",
                    "enum": ["close", "open", "high", "low", "volume"],
                    "default": "close",
                    "description": "Data source for calculation"
                }
            },
            "required": ["period"]
        },
        default_parameters={
            "period": 20,
            "source": "close"
        },
        input_ports=[
            {"name": "price_data", "type": "series", "required": True, "description": "Price series input"}
        ],
        output_ports=[
            {"name": "ma_value", "type": "series", "description": "Moving average output"}
        ],
        is_system_template=True,
        user_id=None,  # System template has no owner
        validation_rules={
            "max_connections": 10,
            "allowed_next_nodes": ["CONDITION", "SIGNAL"]
        },
        execution_hints={
            "pandas_function": "rolling.mean",
            "optimization": "vectorized"
        },
        icon="chart-line",
        color="#3b82f6",
        version="1.0.0"
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_node_templates_by_type(db: AsyncSession, node_type: str, user_id: str = None):
    """Get all node templates of a specific type (system + user's custom)"""

    query = select(NodeTemplate).where(
        NodeTemplate.node_type == node_type,
        NodeTemplate.is_deleted == False
    ).where(
        (NodeTemplate.is_system_template == True) |
        (NodeTemplate.user_id == user_id)
    ).order_by(
        NodeTemplate.is_system_template.desc(),  # System templates first
        NodeTemplate.usage_count.desc()  # Then by popularity
    )

    result = await db.execute(query)
    return result.scalars().all()


async def search_node_templates(db: AsyncSession, search_term: str, user_id: str):
    """Search node templates by name or description"""

    search_pattern = f"%{search_term}%"

    query = select(NodeTemplate).where(
        NodeTemplate.is_deleted == False,
        (
            (NodeTemplate.is_system_template == True) |
            (NodeTemplate.user_id == user_id)
        )
    ).where(
        (NodeTemplate.name.ilike(search_pattern)) |
        (NodeTemplate.display_name.ilike(search_pattern)) |
        (NodeTemplate.description.ilike(search_pattern))
    ).order_by(NodeTemplate.usage_count.desc())

    result = await db.execute(query)
    return result.scalars().all()


async def increment_node_usage(db: AsyncSession, template_id: str):
    """Increment usage count when a node is used in a strategy"""

    await db.execute(
        update(NodeTemplate)
        .where(NodeTemplate.id == template_id)
        .values(usage_count=NodeTemplate.usage_count + 1)
    )
    await db.commit()


# ==========================================
# 2. Quick Test Operations
# ==========================================

async def create_quick_test(
    db: AsyncSession,
    instance_id: str,
    user_id: str,
    test_config: dict,
    logic_flow: dict,
    parameters: dict
):
    """Create a new quick test for a strategy instance"""

    quick_test = QuickTest(
        instance_id=instance_id,
        user_id=user_id,
        test_name=f"Quick Test {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        test_config=test_config,
        logic_flow_snapshot=logic_flow,
        parameters_snapshot=parameters,
        status=QuickTestStatus.PENDING.value
    )

    db.add(quick_test)
    await db.commit()
    await db.refresh(quick_test)
    return quick_test


async def update_test_status_to_running(db: AsyncSession, test_id: str):
    """Update test status when execution starts"""

    await db.execute(
        update(QuickTest)
        .where(QuickTest.id == test_id)
        .values(
            status=QuickTestStatus.RUNNING.value,
            started_at=datetime.now()
        )
    )
    await db.commit()


async def complete_quick_test(
    db: AsyncSession,
    test_id: str,
    test_result: dict,
    metrics_summary: dict,
    execution_time: float
):
    """Complete a quick test with results"""

    await db.execute(
        update(QuickTest)
        .where(QuickTest.id == test_id)
        .values(
            status=QuickTestStatus.COMPLETED.value,
            test_result=test_result,
            metrics_summary=metrics_summary,
            execution_time=execution_time,
            completed_at=datetime.now()
        )
    )
    await db.commit()


async def get_recent_tests_for_instance(
    db: AsyncSession,
    instance_id: str,
    limit: int = 10
):
    """Get recent quick tests for a strategy instance"""

    query = select(QuickTest).where(
        QuickTest.instance_id == instance_id,
        QuickTest.is_deleted == False
    ).order_by(
        QuickTest.created_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def get_user_test_history(
    db: AsyncSession,
    user_id: str,
    status: str = None,
    limit: int = 50
):
    """Get user's test history with optional status filter"""

    query = select(QuickTest).where(
        QuickTest.user_id == user_id,
        QuickTest.is_deleted == False
    )

    if status:
        query = query.where(QuickTest.status == status)

    query = query.order_by(QuickTest.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# ==========================================
# 3. Code Generation Operations
# ==========================================

async def create_code_generation(
    db: AsyncSession,
    instance_id: str,
    user_id: str,
    logic_flow: dict,
    parameters: dict,
    generated_code: str,
    code_hash: str
):
    """Create a new code generation record"""

    code_gen = CodeGeneration(
        instance_id=instance_id,
        user_id=user_id,
        logic_flow_snapshot=logic_flow,
        parameters_snapshot=parameters,
        generated_code=generated_code,
        code_hash=code_hash,
        validation_status=ValidationStatus.PENDING.value,
        code_version="1.0.0",
        line_count=len(generated_code.splitlines()),
        generation_time=0.5  # Example: 500ms
    )

    db.add(code_gen)
    await db.commit()
    await db.refresh(code_gen)
    return code_gen


async def check_code_hash_exists(
    db: AsyncSession,
    instance_id: str,
    code_hash: str
):
    """Check if code with this hash already exists for this instance"""

    query = select(CodeGeneration).where(
        CodeGeneration.instance_id == instance_id,
        CodeGeneration.code_hash == code_hash,
        CodeGeneration.is_deleted == False
    ).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_validation_result(
    db: AsyncSession,
    code_gen_id: str,
    validation_status: str,
    validation_result: dict,
    syntax_passed: bool,
    security_passed: bool,
    complexity_score: int
):
    """Update code generation with validation results"""

    await db.execute(
        update(CodeGeneration)
        .where(CodeGeneration.id == code_gen_id)
        .values(
            validation_status=validation_status,
            validation_result=validation_result,
            syntax_check_passed=syntax_passed,
            security_check_passed=security_passed,
            complexity_score=complexity_score
        )
    )
    await db.commit()


async def get_latest_valid_code(db: AsyncSession, instance_id: str):
    """Get the most recent valid code generation for an instance"""

    query = select(CodeGeneration).where(
        CodeGeneration.instance_id == instance_id,
        CodeGeneration.validation_status == ValidationStatus.VALID.value,
        CodeGeneration.is_deleted == False
    ).order_by(
        CodeGeneration.created_at.desc()
    ).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_code_generation_history(
    db: AsyncSession,
    instance_id: str,
    limit: int = 20
):
    """Get code generation history for an instance"""

    query = select(CodeGeneration).where(
        CodeGeneration.instance_id == instance_id,
        CodeGeneration.is_deleted == False
    ).order_by(
        CodeGeneration.created_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# ==========================================
# 4. Builder Session Operations
# ==========================================

async def create_or_update_session(
    db: AsyncSession,
    user_id: str,
    instance_id: str = None,
    logic_flow: dict = None,
    parameters: dict = None,
    metadata: dict = None
):
    """Create or update user's builder session (auto-save)"""

    # Check for existing active session
    query = select(BuilderSession).where(
        BuilderSession.user_id == user_id,
        BuilderSession.instance_id == instance_id,
        BuilderSession.is_active == True,
        BuilderSession.is_deleted == False
    ).limit(1)

    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if session:
        # Update existing session
        session.draft_logic_flow = logic_flow or session.draft_logic_flow
        session.draft_parameters = parameters or session.draft_parameters
        session.draft_metadata = metadata or session.draft_metadata
        session.last_activity_at = datetime.now()
    else:
        # Create new session
        session = BuilderSession(
            instance_id=instance_id,
            user_id=user_id,
            session_type=SessionType.AUTOSAVE.value,
            draft_logic_flow=logic_flow or {},
            draft_parameters=parameters or {},
            draft_metadata=metadata or {},
            is_active=True,
            last_activity_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
        db.add(session)

    await db.commit()
    await db.refresh(session)
    return session


async def get_active_session(
    db: AsyncSession,
    user_id: str,
    instance_id: str = None
):
    """Get user's active builder session"""

    query = select(BuilderSession).where(
        BuilderSession.user_id == user_id,
        BuilderSession.is_active == True,
        BuilderSession.is_deleted == False
    )

    if instance_id:
        query = query.where(BuilderSession.instance_id == instance_id)

    query = query.order_by(BuilderSession.last_activity_at.desc()).limit(1)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def close_session(db: AsyncSession, session_id: str):
    """Close a builder session (user saved or discarded changes)"""

    await db.execute(
        update(BuilderSession)
        .where(BuilderSession.id == session_id)
        .values(is_active=False)
    )
    await db.commit()


async def cleanup_expired_sessions(db: AsyncSession):
    """Cleanup expired sessions (scheduled job)"""

    await db.execute(
        update(BuilderSession)
        .where(
            (BuilderSession.expires_at < datetime.now()) |
            (BuilderSession.last_activity_at < datetime.now() - timedelta(days=30))
        )
        .where(BuilderSession.is_active == True)
        .values(is_active=False)
    )
    await db.commit()


# ==========================================
# 5. Complex Workflow Examples
# ==========================================

async def complete_strategy_build_workflow(
    db: AsyncSession,
    user_id: str,
    instance_id: str,
    logic_flow: dict,
    parameters: dict
):
    """Complete workflow: Save session → Generate code → Run quick test"""

    # Step 1: Save session
    session = await create_or_update_session(
        db, user_id, instance_id, logic_flow, parameters
    )

    # Step 2: Generate code
    import hashlib
    generated_code = "# Generated Python code here..."  # Actual code generation logic
    code_hash = hashlib.sha256(generated_code.encode()).hexdigest()

    # Check for duplicate
    existing_code = await check_code_hash_exists(db, instance_id, code_hash)
    if existing_code:
        code_gen = existing_code
    else:
        code_gen = await create_code_generation(
            db, instance_id, user_id, logic_flow, parameters,
            generated_code, code_hash
        )

    # Step 3: Validate code
    validation_result = {
        "syntax_errors": [],
        "security_warnings": [],
        "complexity_score": 5
    }
    await update_validation_result(
        db, code_gen.id,
        ValidationStatus.VALID.value,
        validation_result,
        syntax_passed=True,
        security_passed=True,
        complexity_score=5
    )

    # Step 4: Create quick test
    test_config = {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "stock_pool": ["AAPL", "MSFT"],
        "initial_capital": 100000
    }
    quick_test = await create_quick_test(
        db, instance_id, user_id, test_config, logic_flow, parameters
    )

    # Step 5: Close session (changes saved to instance)
    await close_session(db, session.id)

    return {
        "session": session,
        "code_generation": code_gen,
        "quick_test": quick_test
    }


async def get_strategy_builder_dashboard(db: AsyncSession, user_id: str):
    """Get dashboard data for strategy builder"""

    # Recent sessions
    sessions_query = select(BuilderSession).where(
        BuilderSession.user_id == user_id,
        BuilderSession.is_deleted == False
    ).order_by(BuilderSession.last_activity_at.desc()).limit(5)
    sessions_result = await db.execute(sessions_query)
    recent_sessions = sessions_result.scalars().all()

    # Recent tests
    tests_query = select(QuickTest).where(
        QuickTest.user_id == user_id,
        QuickTest.is_deleted == False
    ).order_by(QuickTest.created_at.desc()).limit(10)
    tests_result = await db.execute(tests_query)
    recent_tests = tests_result.scalars().all()

    # Popular node templates
    templates_query = select(NodeTemplate).where(
        NodeTemplate.is_system_template == True,
        NodeTemplate.is_deleted == False
    ).order_by(NodeTemplate.usage_count.desc()).limit(10)
    templates_result = await db.execute(templates_query)
    popular_templates = templates_result.scalars().all()

    return {
        "recent_sessions": recent_sessions,
        "recent_tests": recent_tests,
        "popular_templates": popular_templates
    }


# ==========================================
# 6. Analytics Queries
# ==========================================

async def get_user_test_statistics(db: AsyncSession, user_id: str):
    """Get test statistics for a user"""

    from sqlalchemy import func

    query = select(
        func.count(QuickTest.id).label('total_tests'),
        func.sum(
            func.case((QuickTest.status == QuickTestStatus.COMPLETED.value, 1), else_=0)
        ).label('completed_tests'),
        func.avg(QuickTest.execution_time).label('avg_execution_time'),
        func.max(QuickTest.execution_time).label('max_execution_time')
    ).where(
        QuickTest.user_id == user_id,
        QuickTest.is_deleted == False
    )

    result = await db.execute(query)
    return result.one()


async def get_node_template_usage_stats(db: AsyncSession):
    """Get node template usage statistics"""

    query = select(
        NodeTemplate.node_type,
        NodeTemplate.name,
        NodeTemplate.usage_count
    ).where(
        NodeTemplate.is_system_template == True,
        NodeTemplate.is_deleted == False
    ).order_by(
        NodeTemplate.usage_count.desc()
    ).limit(20)

    result = await db.execute(query)
    return result.all()


async def get_code_validation_failure_rate(db: AsyncSession):
    """Get code validation failure rate over last 7 days"""

    from sqlalchemy import func

    seven_days_ago = datetime.now() - timedelta(days=7)

    query = select(
        CodeGeneration.validation_status,
        func.count(CodeGeneration.id).label('count')
    ).where(
        CodeGeneration.created_at >= seven_days_ago,
        CodeGeneration.is_deleted == False
    ).group_by(
        CodeGeneration.validation_status
    )

    result = await db.execute(query)
    return result.all()
