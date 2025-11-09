# Strategy Builder Backend Architecture - Executive Summary

## Document Overview

This document provides an executive summary of the complete backend architecture design for the **Strategy Builder** feature in Qlib-UI.

**Design Date**: January 15, 2025
**Backend Architect**: Claude (Anthropic)
**Project**: Qlib-UI Quantitative Investment Platform

---

## 1. Project Context

### Background
Qlib-UI is expanding its Strategy module with a visual strategy building capability. The existing infrastructure (90% complete) includes:
- Database models defined in `strategy_builder.py`
- FastAPI backend with async/await patterns
- SQLAlchemy 2.0 ORM with Repository pattern
- JWT authentication
- Integration with Indicator and Backtest modules

### Objectives
Design comprehensive backend service architecture for:
1. Visual logic flow → Python code generation
2. Quick lightweight backtest execution
3. Session auto-save for draft protection
4. Node template library management
5. Code security validation

---

## 2. Architecture Overview

### Technology Stack
- **Framework**: FastAPI (async)
- **ORM**: SQLAlchemy 2.0
- **Database**: MySQL 8.0
- **Task Queue**: Existing task_scheduling module (Celery/RQ)
- **Code Generation**: Jinja2 templates
- **Code Validation**: Python AST module
- **Caching**: Redis (optional, Phase 6)

### Architectural Layers

```
┌─────────────────────────────────────────────┐
│           Client (React)                    │
│     Strategy Builder Visual Editor         │
└─────────────────┬───────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────────┐
│           API Layer (FastAPI)               │
│  - Node Template API                        │
│  - Code Generation API                      │
│  - Quick Test API                           │
│  - Session API                              │
│  - Factor Integration API                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│          Service Layer                      │
│  - BuilderService                           │
│  - CodeGeneratorService                     │
│  - ValidationService                        │
│  - QuickTestService                         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        Repository Layer                     │
│  - NodeTemplateRepository                   │
│  - CodeGenerationRepository                 │
│  - QuickTestRepository                      │
│  - BuilderSessionRepository                 │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Database Layer (MySQL)              │
│  - node_templates                           │
│  - code_generations                         │
│  - quick_tests                              │
│  - builder_sessions                         │
│  - strategy_instances (existing)            │
└─────────────────────────────────────────────┘
```

### Integration Points

**Indicator Module** → Provides factor library for INDICATOR nodes
**Backtest Module** → Executes quick backtests
**Task Scheduling Module** → Background async execution
**Code Security Module** → Future sandboxed code execution

---

## 3. API Design Summary

### 14 RESTful Endpoints

#### Node Templates (4 endpoints)
- `GET /api/strategy-builder/node-templates` - List templates with filters
- `POST /api/strategy-builder/node-templates` - Create custom template
- `GET /api/strategy-builder/node-templates/{id}` - Get template details
- `PUT /api/strategy-builder/node-templates/{id}` - Update custom template

#### Factors Integration (1 endpoint)
- `GET /api/strategy-builder/factors` - Get available factors from Indicator module

#### Code Generation (3 endpoints)
- `POST /api/strategy-builder/generate-code` - Generate Python code from logic flow
- `POST /api/strategy-builder/validate-code` - Validate code security
- `GET /api/strategy-builder/code-history/{instance_id}` - Code generation history

#### Quick Test (3 endpoints)
- `POST /api/strategy-builder/quick-test` - Execute quick backtest (async)
- `GET /api/strategy-builder/quick-test/{test_id}` - Get test result
- `GET /api/strategy-builder/quick-test/history` - Test history

#### Session Management (3 endpoints)
- `POST /api/strategy-builder/sessions` - Create/update session (upsert)
- `GET /api/strategy-builder/sessions/{session_id}` - Get session
- `DELETE /api/strategy-builder/sessions/{session_id}` - Delete session

### Authentication
All endpoints require JWT Bearer token authentication.

### Response Format
Unified `APIResponse<T>` wrapper:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## 4. Service Layer Design

### 4.1 BuilderService
**Responsibilities**: Node templates, logic flow validation, session management, factor integration

**Key Methods**:
- `get_node_templates()` - List/filter templates
- `create_node_template()` - Create custom template
- `validate_logic_flow()` - Multi-layer validation
- `detect_circular_dependency()` - Topological sort
- `get_available_factors()` - Integrate with Indicator module
- `create_or_update_session()` - Upsert session for auto-save
- `cleanup_expired_sessions()` - Background cleanup task

### 4.2 CodeGeneratorService
**Responsibilities**: Logic flow → Python code conversion, template management, deduplication

**Key Methods**:
- `generate_code()` - Main orchestrator
- `generate_node_code()` - Per-node code generation
- `render_template()` - Jinja2 template rendering
- `calculate_code_hash()` - SHA-256 for deduplication
- `check_code_duplicate()` - Avoid storing duplicates
- `get_code_history()` - Historical code generations

**Code Generation Engine**: **Jinja2** templates
- Base strategy template
- Per-node-type templates (INDICATOR, CONDITION, SIGNAL, POSITION, STOP_LOSS, STOP_PROFIT)
- Macro library for common patterns

### 4.3 ValidationService
**Responsibilities**: Code security, syntax validation, complexity analysis

**Key Methods**:
- `validate_code()` - Multi-layer validation
- `validate_syntax()` - Python AST parsing
- `validate_security()` - Import/function whitelist/blacklist
- `analyze_imports()` - Categorize allowed/forbidden
- `calculate_complexity()` - Cyclomatic/cognitive complexity

**Security Strategy**: **Whitelist > Blacklist**
- Allowed: numpy, pandas, qlib, talib, math, datetime, collections, typing
- Forbidden: os, sys, subprocess, eval, exec, file I/O, network access

### 4.4 QuickTestService
**Responsibilities**: Quick backtest execution, integration with Backtest module

**Key Methods**:
- `execute_quick_test()` - Create test + submit to queue (async)
- `get_quick_test_result()` - Retrieve test result
- `complete_quick_test()` - Worker callback with results
- `build_backtest_config()` - Map simplified config to full backtest config
- `extract_metrics_summary()` - Key metrics extraction

**Execution Pattern**: **Asynchronous with Background Queue**
1. API creates QuickTest record (status=PENDING)
2. Submit task to queue (returns immediately)
3. Background worker executes backtest
4. Client polls for results

---

## 5. Repository Layer Design

All repositories extend `BaseRepository<ModelType>` with specialized query methods.

### NodeTemplateRepository
- `get_by_filters()` - Multi-filter queries
- `get_system_templates()` - System templates only
- `get_user_templates()` - User custom templates
- `increment_usage_count()` - Track template popularity

### CodeGenerationRepository
- `get_by_code_hash()` - Deduplication lookup
- `get_latest_valid_code()` - Latest validated code
- `get_by_validation_status()` - Filter by validation result

### QuickTestRepository
- `get_pending_tests()` - For background worker
- `get_running_tests()` - Timeout detection
- `update_status()` - Status transitions

### BuilderSessionRepository
- `get_active_by_instance_and_user()` - Find active session
- `get_expired_sessions()` - For cleanup task
- `create_or_update_by_instance()` - Upsert logic
- `update_activity()` - Auto-save updates

---

## 6. Key Architecture Decisions (ADRs)

### ADR-001: Jinja2 for Code Generation
**Decision**: Use Jinja2 template engine
**Rationale**: Mature, readable, extensible, team familiar
**Trade-off**: Templates need maintenance vs deterministic output

### ADR-002: Async Quick Test Execution
**Decision**: Background task queue with HTTP 202 Accepted
**Rationale**: Better UX, scalable, non-blocking
**Trade-off**: Client polling complexity vs immediate response

### ADR-003: Multi-Layer Validation
**Decision**: Schema → Graph → Types → Parameters → Semantic
**Rationale**: Early error detection, clear messages, fail-fast
**Trade-off**: Additional latency (~100ms) vs robustness

### ADR-004: 30-Second Auto-Save
**Decision**: Client-driven auto-save every 30 seconds
**Rationale**: Balances data freshness (max 30s loss) vs server load
**Trade-off**: Potential 30s data loss vs server efficiency

### ADR-005: Whitelist Security + AST
**Decision**: Import whitelist + AST analysis
**Rationale**: Defense in depth, safe by default
**Trade-off**: May block advanced uses vs security guarantee

### ADR-006: SHA-256 Code Deduplication
**Decision**: Hash-based duplicate detection
**Rationale**: Saves space, fast lookups, deterministic
**Trade-off**: Hash calculation overhead (~100ms) vs storage savings

---

## 7. Critical Data Flows

### 7.1 Code Generation Flow
```
Client → API → CodeGeneratorService
  ├→ BuilderService.validate_logic_flow()
  ├→ Topological sort nodes
  ├→ For each node: render_template()
  ├→ Combine code
  ├→ Calculate SHA-256 hash
  ├→ Check duplicate (return if exists)
  ├→ ValidationService.validate_code()
  └→ Store CodeGeneration record
```

**Latency**: ~250ms (avg), ~500ms (p95)

### 7.2 Quick Test Execution Flow
```
Client → API → QuickTestService
  ├→ Create QuickTest record (PENDING)
  ├→ Submit to TaskQueue
  └→ Return 202 Accepted

Background Worker
  ├→ Update status → RUNNING
  ├→ BacktestExecutionService.execute()
  ├→ Extract metrics
  └→ Update status → COMPLETED/FAILED

Client polls /quick-test/{id} every 2s
```

**Execution Time**: 10-30 seconds (typical)

### 7.3 Session Auto-Save Flow
```
Client (debounced 2s after edit)
  ↓
POST /sessions
  ├→ BuilderService.create_or_update_session()
  ├→ Check existing active session
  ├→ If exists: UPDATE (last_activity_at, draft_logic_flow)
  ├→ If not: INSERT new session
  └→ Return session

Background Cleanup (hourly cron)
  ├→ Find sessions with last_activity_at < NOW() - 24h
  └→ Soft delete expired sessions
```

**Auto-Save Latency**: <100ms

---

## 8. Database Schema Summary

### node_templates
- System and custom template definitions
- Parameter schemas (JSON Schema)
- Input/output port definitions
- Usage statistics

**Indexes**: `node_type`, `is_system_template`, `user_id`, `category`

### code_generations
- Generated Python code
- SHA-256 hash for deduplication
- Validation results (syntax, security)
- Complexity metrics

**Indexes**: `instance_id`, `code_hash`, `validation_status`, `user_id`

### quick_tests
- Backtest execution records
- Test configuration snapshots
- Performance metrics summary
- Execution status tracking

**Indexes**: `instance_id`, `user_id`, `status`, `completed_at`

### builder_sessions
- Draft auto-save storage
- User session state
- Expiration timestamps
- Collaborative editing support (future)

**Indexes**: `instance_id`, `user_id`, `is_active`, `last_activity_at`

---

## 9. Implementation Plan Summary

### Timeline: 15-18 days (1 senior backend developer)

**Phase 1 (Days 1-3)**: Foundation Layer
- Repository implementations
- Pydantic schemas
- Exception classes
- Database migration

**Phase 2 (Days 4-7)**: Core Services
- ValidationService (1 day)
- BuilderService (2 days)
- CodeGeneratorService (2 days)
- QuickTestService (1.5 days)

**Phase 3 (Days 8-10)**: API Layer
- 14 RESTful endpoints
- API integration tests
- Router registration

**Phase 4 (Days 11-13)**: Integration & Testing
- Indicator module integration
- Backtest module integration
- Task scheduling integration
- End-to-end testing

**Phase 5 (Days 14-15)**: Documentation & Deployment
- Code documentation
- System template seeding
- Deployment configuration

**Phase 6 (Days 16-18)** [OPTIONAL]: Polish & Optimization
- Redis caching
- Monitoring dashboards
- Security hardening
- Performance optimization

---

## 10. Testing Strategy

### Coverage Targets
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All module integrations
- **API Tests**: All 14 endpoints
- **E2E Tests**: Critical user flows

### Performance Benchmarks
- Code generation: <500ms (p95)
- Quick test submission: <200ms (p95)
- Session auto-save: <100ms (p95)
- System handles 100 concurrent users

### Security Testing
- AST validation edge cases
- Code injection attempt detection
- Whitelist/blacklist verification
- Import restriction enforcement

---

## 11. Deliverables Summary

All design documents are located in `/Users/zhenkunliu/project/qlib-ui/backend/docs/`:

1. **strategy-builder-api.yaml**
   - Complete OpenAPI 3.1 specification
   - 14 endpoints with full request/response schemas
   - Error response formats
   - Authentication configuration

2. **strategy-builder-services.py**
   - Service layer interface definitions
   - Complete method signatures with type hints
   - Custom exception classes
   - Background task definitions

3. **strategy-builder-repositories.py**
   - Repository layer implementations
   - Specialized query methods
   - Extends BaseRepository pattern

4. **strategy-builder-adr.md**
   - 6 Architecture Decision Records
   - Rationale for key technical choices
   - Trade-off analysis
   - Implementation notes

5. **strategy-builder-flows.md**
   - 10+ Mermaid diagrams
   - Data flow sequences
   - State transitions
   - System architecture overview

6. **strategy-builder-implementation-plan.md**
   - 6-phase implementation plan
   - Task breakdown with effort estimates
   - Dependency graph
   - Risk assessment
   - Testing strategy
   - Deployment checklist

7. **strategy-builder-architecture-summary.md** (this document)
   - Executive summary
   - Architecture overview
   - Key design decisions
   - Implementation roadmap

---

## 12. Success Criteria

### Functional Requirements ✓
- [x] 14 API endpoints designed
- [x] Code generation architecture defined
- [x] Quick test execution flow designed
- [x] Session auto-save mechanism specified
- [x] Security validation approach documented

### Non-Functional Requirements ✓
- [x] Performance targets defined (<500ms code gen, <200ms test submit, <100ms auto-save)
- [x] Scalability architecture (async execution, stateless services)
- [x] Security-first approach (whitelist, AST validation, defense in depth)
- [x] Maintainability (clear separation of concerns, comprehensive docs)

### Quality Requirements ✓
- [x] Complete API specification (OpenAPI 3.1)
- [x] Service interfaces with type annotations
- [x] Repository pattern consistent with existing code
- [x] Architecture decision rationale documented
- [x] Data flow diagrams for critical paths
- [x] Implementation plan with realistic estimates

---

## 13. Next Steps

### Immediate Actions
1. **Stakeholder Review**: Review architecture design with product team
2. **Technical Review**: Review with backend team for feasibility
3. **Resource Allocation**: Assign backend developer(s)
4. **Project Setup**: Create tasks in project management tool
5. **Kickoff Phase 1**: Begin Foundation Layer implementation

### Development Workflow
1. Follow 6-phase implementation plan
2. Daily standups to track progress
3. Weekly demos of completed features
4. Continuous integration testing
5. Code review for all PRs
6. Documentation updates as features complete

### Risk Mitigation
1. Early integration testing with Indicator/Backtest modules
2. Security review at each phase
3. Performance testing before optimization phase
4. User feedback collection during development

---

## 14. Key Architectural Strengths

1. **RESTful Best Practices**: Consistent API design, proper HTTP methods, status codes
2. **Async-First**: Non-blocking operations, background tasks, scalable architecture
3. **Security-First**: Defense in depth, whitelist approach, AST validation
4. **Separation of Concerns**: Clear layer boundaries (API → Service → Repository → Database)
5. **Testability**: Dependency injection, mockable services, comprehensive test strategy
6. **Maintainability**: Well-documented, follows existing patterns, easy to extend
7. **Performance**: Optimized queries, caching strategy, deduplication, async execution
8. **User Experience**: Auto-save, quick feedback, clear error messages, async processing

---

## 15. Alignment with Existing Architecture

### Follows Project Conventions ✓
- FastAPI async patterns
- SQLAlchemy 2.0 with Repository pattern
- Service layer business logic
- Pydantic schemas for validation
- Unified error handling (custom exceptions)
- Structured logging with correlation IDs
- JWT authentication

### Integration Strategy ✓
- **Indicator Module**: Service-to-service calls for factor data
- **Backtest Module**: Background task integration
- **Task Scheduling Module**: Existing queue infrastructure
- **Strategy Module**: Extends existing StrategyInstance model

### Code Quality Standards ✓
- Type hints on all methods
- Docstrings with examples
- Unit test coverage >= 90%
- Integration tests for all modules
- API tests for all endpoints
- E2E tests for critical flows

---

## 16. Conclusion

This comprehensive backend architecture design for Strategy Builder provides:

✅ **Complete API Specification** - 14 endpoints with full OpenAPI 3.1 documentation
✅ **Service Layer Design** - 4 services with clear responsibilities and interfaces
✅ **Repository Pattern** - 4 repositories extending BaseRepository
✅ **Architecture Decisions** - 6 ADRs with rationale and trade-offs
✅ **Data Flow Diagrams** - 10+ Mermaid diagrams illustrating critical workflows
✅ **Implementation Plan** - 6-phase plan with 15-18 day timeline

The architecture is:
- **Production-Ready**: Built on proven patterns and technologies
- **Scalable**: Async execution, stateless services, background workers
- **Secure**: Whitelist-based validation, AST analysis, defense in depth
- **Maintainable**: Clear separation of concerns, comprehensive documentation
- **Testable**: High coverage targets, multiple testing layers
- **Aligned**: Consistent with existing Qlib-UI architecture

**Ready for Implementation**: All design documents complete, development can begin immediately following the 6-phase implementation plan.

---

**Document Version**: 1.0
**Last Updated**: January 15, 2025
**Status**: Ready for Review
**Next Review**: Post-Implementation (Week 3)
