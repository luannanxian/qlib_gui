.PHONY: help install start stop test clean build deploy

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## 显示帮助信息
	@echo "$(BLUE)Qlib-UI Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# 安装相关
# ============================================================================

install: install-backend install-frontend ## 安装所有依赖

install-backend: ## 安装后端依赖
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && python -m venv venv
	cd backend && . venv/bin/activate && pip install --upgrade pip
	cd backend && . venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

install-frontend: ## 安装前端依赖
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(NC)"

# ============================================================================
# 启动相关
# ============================================================================

start: ## 启动前后端服务(并行)
	@echo "$(BLUE)Starting services...$(NC)"
	@make -j2 start-backend start-frontend

start-backend: ## 启动后端服务
	@echo "$(BLUE)Starting backend server...$(NC)"
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --port 8000

start-frontend: ## 启动前端服务
	@echo "$(BLUE)Starting frontend server...$(NC)"
	cd frontend && npm run dev

start-celery: ## 启动Celery Worker
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	cd backend && . venv/bin/activate && celery -A app.celery_app worker --loglevel=info

start-all: ## 启动所有服务(后端+前端+Celery)
	@echo "$(BLUE)Starting all services...$(NC)"
	@make -j3 start-backend start-frontend start-celery

# ============================================================================
# 停止相关
# ============================================================================

stop: ## 停止所有服务
	@echo "$(YELLOW)Stopping services...$(NC)"
	@pkill -f "uvicorn app.main:app" || true
	@pkill -f "vite" || true
	@pkill -f "celery -A app.celery_app" || true
	@echo "$(GREEN)✓ Services stopped$(NC)"

# ============================================================================
# 测试相关
# ============================================================================

test: test-backend test-frontend ## 运行所有测试

test-backend: ## 运行后端测试
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd backend && . venv/bin/activate && pytest -v
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

test-frontend: ## 运行前端测试
	@echo "$(BLUE)Running frontend tests...$(NC)"
	cd frontend && npm test
	@echo "$(GREEN)✓ Frontend tests passed$(NC)"

test-e2e: ## 运行E2E测试
	@echo "$(BLUE)Running E2E tests...$(NC)"
	cd tests/e2e && npm test
	@echo "$(GREEN)✓ E2E tests passed$(NC)"

test-watch: ## 监听模式运行测试
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	cd backend && . venv/bin/activate && pytest-watch

coverage: ## 生成测试覆盖率报告
	@echo "$(BLUE)Generating coverage report...$(NC)"
	cd backend && . venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated at backend/htmlcov/index.html$(NC)"

# ============================================================================
# 代码质量
# ============================================================================

lint: lint-backend lint-frontend ## 运行所有代码检查

lint-backend: ## 检查后端代码
	@echo "$(BLUE)Linting backend code...$(NC)"
	cd backend && . venv/bin/activate && black --check app
	cd backend && . venv/bin/activate && isort --check-only app
	cd backend && . venv/bin/activate && flake8 app
	cd backend && . venv/bin/activate && mypy app
	@echo "$(GREEN)✓ Backend code is clean$(NC)"

lint-frontend: ## 检查前端代码
	@echo "$(BLUE)Linting frontend code...$(NC)"
	cd frontend && npm run lint
	@echo "$(GREEN)✓ Frontend code is clean$(NC)"

format: format-backend format-frontend ## 格式化所有代码

format-backend: ## 格式化后端代码
	@echo "$(BLUE)Formatting backend code...$(NC)"
	cd backend && . venv/bin/activate && black app
	cd backend && . venv/bin/activate && isort app
	@echo "$(GREEN)✓ Backend code formatted$(NC)"

format-frontend: ## 格式化前端代码
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	cd frontend && npm run format
	@echo "$(GREEN)✓ Frontend code formatted$(NC)"

# ============================================================================
# 构建相关
# ============================================================================

build: build-backend build-frontend ## 构建前后端

build-backend: ## 构建后端
	@echo "$(BLUE)Building backend...$(NC)"
	cd backend && . venv/bin/activate && python -m build
	@echo "$(GREEN)✓ Backend built$(NC)"

build-frontend: ## 构建前端
	@echo "$(BLUE)Building frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"

# ============================================================================
# Docker相关
# ============================================================================

docker-build: ## 构建Docker镜像
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## 启动Docker容器
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Docker containers started$(NC)"
	@echo "$(GREEN)Frontend: http://localhost:3000$(NC)"
	@echo "$(GREEN)Backend: http://localhost:8000$(NC)"

docker-down: ## 停止Docker容器
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

docker-logs: ## 查看Docker日志
	docker-compose logs -f

docker-clean: ## 清理Docker资源
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	docker-compose down -v
	docker system prune -af
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

# ============================================================================
# 数据库相关
# ============================================================================

init-db: ## 初始化数据库
	@echo "$(BLUE)Initializing database...$(NC)"
	cd backend && . venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Database initialized$(NC)"

migrate: ## 创建新的数据库迁移
	@echo "$(BLUE)Creating migration...$(NC)"
	@read -p "Enter migration message: " message; \
	cd backend && . venv/bin/activate && alembic revision --autogenerate -m "$$message"
	@echo "$(GREEN)✓ Migration created$(NC)"

migrate-up: ## 应用数据库迁移
	@echo "$(BLUE)Applying migrations...$(NC)"
	cd backend && . venv/bin/activate && alembic upgrade head
	@echo "$(GREEN)✓ Migrations applied$(NC)"

migrate-down: ## 回退数据库迁移
	@echo "$(YELLOW)Reverting migration...$(NC)"
	cd backend && . venv/bin/activate && alembic downgrade -1
	@echo "$(GREEN)✓ Migration reverted$(NC)"

db-reset: ## 重置数据库(危险操作!)
	@echo "$(RED)⚠ WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		cd backend && . venv/bin/activate && alembic downgrade base && alembic upgrade head; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

# ============================================================================
# 清理相关
# ============================================================================

clean: ## 清理临时文件
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-cache: ## 清理缓存目录
	@echo "$(YELLOW)Cleaning cache...$(NC)"
	rm -rf cache/*
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean-logs: ## 清理日志文件
	@echo "$(YELLOW)Cleaning logs...$(NC)"
	rm -rf logs/*
	@echo "$(GREEN)✓ Logs cleaned$(NC)"

clean-data: ## 清理临时数据(危险操作!)
	@echo "$(RED)⚠ WARNING: This will delete temporary data!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		rm -rf data/uploads/*; \
		rm -rf results/*; \
		echo "$(GREEN)✓ Data cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

# ============================================================================
# 开发工具
# ============================================================================

dev-setup: install init-db ## 开发环境一键设置
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "Run 'make start' to start the application"

shell-backend: ## 进入后端Python Shell
	@cd backend && . venv/bin/activate && python

shell-db: ## 进入数据库Shell
	@cd backend && . venv/bin/activate && python -c "from app.database import SessionLocal; db = SessionLocal(); import IPython; IPython.embed()"

logs-backend: ## 查看后端日志
	@tail -f logs/backend/*.log

logs-celery: ## 查看Celery日志
	@tail -f logs/celery/*.log

# ============================================================================
# 部署相关
# ============================================================================

deploy-dev: ## 部署到开发环境
	@echo "$(BLUE)Deploying to development...$(NC)"
	@echo "$(YELLOW)TODO: Implement deployment$(NC)"

deploy-prod: ## 部署到生产环境
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(YELLOW)TODO: Implement deployment$(NC)"

# ============================================================================
# 文档相关
# ============================================================================

docs-serve: ## 启动文档服务器
	@echo "$(BLUE)Starting documentation server...$(NC)"
	cd docs && python -m http.server 8080

docs-build: ## 构建文档
	@echo "$(BLUE)Building documentation...$(NC)"
	@echo "$(YELLOW)TODO: Implement documentation build$(NC)"

# ============================================================================
# 其他
# ============================================================================

version: ## 显示版本信息
	@echo "$(BLUE)Qlib-UI Version Information$(NC)"
	@echo "Python: $$(python --version)"
	@echo "Node: $$(node --version)"
	@echo "npm: $$(npm --version)"

info: ## 显示项目信息
	@echo "$(BLUE)Project: Qlib-UI$(NC)"
	@echo "Description: Quantitative Investment Research Platform"
	@echo "License: MIT"
	@echo ""
	@echo "$(GREEN)Documentation:$(NC)"
	@echo "  - PRD: docs/QLIB_UI_PRD.md"
	@echo "  - Modules: docs/FUNCTIONAL_MODULES.md"
	@echo "  - Structure: docs/PROJECT_STRUCTURE.md"
	@echo ""
	@echo "$(GREEN)Useful Commands:$(NC)"
	@echo "  make install   - Install dependencies"
	@echo "  make start     - Start services"
	@echo "  make test      - Run tests"
	@echo "  make help      - Show all commands"
