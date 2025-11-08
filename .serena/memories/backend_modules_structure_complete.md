# Backend Module Structure - Complete Overview

## Quick Reference: 9 Functional Modules

### Active Modules (Production):
1. **USER_ONBOARDING** - User mode selection and preferences
2. **DATA_MANAGEMENT** - Dataset, import, preprocessing, charting
3. **STRATEGY** - Strategy templates, instances, ratings, validation
4. **INDICATOR** - Custom factors, predefined indicators, validation, user libraries
5. **BACKTEST** - Strategy execution engine with real-time WebSocket progress
6. **TASK_SCHEDULING** - Async task queue, progress tracking, monitoring
7. **CODE_SECURITY** - Safe code execution in sandbox
8. **COMMON** - Cross-cutting utilities (logging, errors, validation, schemas)

### Stub Module (Not Yet Implemented):
9. **STRATEGY_BUILDER** - Visual strategy composition (documentation only)

## Module Locations
- Feature modules: `/backend/app/modules/{module_name}/`
- Database layer: `/backend/app/database/`
- Main app: `/backend/app/main.py`
- Tests: `/backend/tests/`

## Standard Module Structure
Each module has:
- `api/` - FastAPI routers
- `services/` - Business logic
- `schemas/` - Pydantic validation
- `exceptions.py` - Module-specific errors
- `Claude.md` - Documentation (optional)
- Database models in `/backend/app/database/models/`
- Repositories in `/backend/app/database/repositories/`

## Architecture Pattern
Layered architecture: API → Services → Repositories → ORM (SQLAlchemy) → Database

## Key Files by Module
- User_Onboarding: mode_api.py, mode_service.py, user_preferences.py
- Data_Management: dataset_api.py, import_api.py, preprocessing_api.py, chart_api.py
- Strategy: strategy_api.py, template_service.py, instance_service.py
- Indicator: indicator_api.py, custom_factor_api.py, user_library_api.py
- Backtest: backtest_api.py, websocket_api.py, execution_service.py, analysis_service.py
- Task_Scheduling: task_api.py, task_service.py, task.py (model)
- Code_Security: simple_executor.py
- Common: Logging (8+ files), Exceptions, Constants, Schemas, Utils

## Dependencies
All modules → Database Layer → PostgreSQL/SQLite
Background tasks: Celery + Redis/RabbitMQ
Common utilities used by all modules

## Testing
- New structure: `/backend/tests/modules/` (mirrored to app structure)
- Legacy tests: `/backend/tests/test_*/` (being migrated)
- Total test files: 100+

## Database Models (in database/models/):
- UserPreferences, Task, Dataset, Chart, ImportTask, Preprocessing
- Strategy (StrategyTemplate, StrategyInstance, TemplateRating)
- Indicator (IndicatorComponent, CustomFactor, FactorValidationResult, UserFactorLibrary)
- Backtest (BacktestConfig, BacktestResult)
