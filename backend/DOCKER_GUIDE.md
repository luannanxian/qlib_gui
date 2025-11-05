# Docker Deployment Guide

This document explains how to deploy the qlib-ui backend using Docker and Docker Compose.

## Overview

The Docker setup includes:
- **Backend**: FastAPI application with Uvicorn
- **MySQL**: Database server
- **Redis**: Cache and message broker
- **Celery Worker**: Async task processing
- **Celery Beat**: Periodic task scheduler
- **Flower**: Celery monitoring UI (optional)

## Prerequisites

1. **Docker**: Version 20.10 or higher
2. **Docker Compose**: Version 2.0 or higher

Install Docker and Docker Compose:
```bash
# macOS (with Homebrew)
brew install docker docker-compose

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Or install Docker Desktop (includes Compose)
# https://www.docker.com/products/docker-desktop
```

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and set secure values for:
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `SECRET_KEY` (generate with: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`)

### 2. Build and Start Services

```bash
# Build images and start all services
docker-compose up -d

# Or build first, then start
docker-compose build
docker-compose up -d
```

### 3. Run Database Migrations

```bash
# Run Alembic migrations
docker-compose exec backend alembic upgrade head
```

### 4. Access Services

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery UI)**: http://localhost:5555
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

## Docker Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d backend mysql redis

# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: deletes data!)
docker-compose down -v

# Restart a specific service
docker-compose restart backend

# View service status
docker-compose ps
```

### Logs

```bash
# View logs for all services
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs backend
docker-compose logs celery-worker

# Tail last 100 lines
docker-compose logs --tail=100 -f backend
```

### Execute Commands

```bash
# Run shell in backend container
docker-compose exec backend bash

# Run Alembic migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Run Python shell
docker-compose exec backend python

# Check Celery worker status
docker-compose exec celery-worker celery -A app.celery_app inspect active
```

### Building and Updating

```bash
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild without cache
docker-compose build --no-cache

# Pull latest base images
docker-compose pull
```

## Service Configuration

### Backend Service

**Image**: Built from `Dockerfile`
**Port**: 8000
**Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

**Volumes**:
- `./app:/app/app` - Live code reloading in development
- `./data:/app/data` - Persistent data storage
- `./logs:/app/logs` - Application logs
- `./cache:/app/cache` - Cache directory
- `./results:/app/results` - Results storage

**Environment Variables**: See `.env.docker`

### MySQL Service

**Image**: mysql:8.0
**Port**: 3306
**Volume**: `mysql_data:/var/lib/mysql`

**Configuration**:
- Character set: utf8mb4
- Collation: utf8mb4_unicode_ci
- Authentication: mysql_native_password

### Redis Service

**Image**: redis:7-alpine
**Port**: 6379
**Volume**: `redis_data:/data`

**Configuration**:
- Persistence: AOF (Append Only File) enabled

### Celery Worker

**Image**: Same as backend
**Command**: `celery -A app.celery_app worker --loglevel=info --concurrency=4`

**Queues**: data_import, backtest, strategy

### Celery Beat

**Image**: Same as backend
**Command**: `celery -A app.celery_app beat --loglevel=info`

**Volume**: `celery_beat_data:/app/celerybeat`

### Flower (Monitoring)

**Image**: Same as backend
**Port**: 5555
**Command**: `celery -A app.celery_app flower --port=5555`

## Development Workflow

### 1. Make Code Changes

With the default configuration, code changes are automatically reloaded:
- Backend: Uvicorn with `--reload` flag
- Celery Worker: Restart service for changes

```bash
# Restart Celery worker after code changes
docker-compose restart celery-worker celery-beat
```

### 2. Database Schema Changes

```bash
# 1. Modify models in app/database/models/

# 2. Generate migration
docker-compose exec backend alembic revision --autogenerate -m "add new field"

# 3. Review migration file in alembic/versions/

# 4. Apply migration
docker-compose exec backend alembic upgrade head

# 5. Rollback if needed
docker-compose exec backend alembic downgrade -1
```

### 3. Add New Dependencies

```bash
# 1. Update requirements.txt

# 2. Rebuild images
docker-compose build backend celery-worker celery-beat

# 3. Restart services
docker-compose up -d
```

## Production Deployment

### 1. Production Configuration

Create `.env.docker.prod`:
```bash
APP_ENV=production
DEBUG=false
MYSQL_ROOT_PASSWORD=<strong-password>
MYSQL_PASSWORD=<strong-password>
SECRET_KEY=<64-char-secret>
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20
```

### 2. Production Docker Compose

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    env_file: .env.docker.prod
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 3. Use Secrets (Recommended)

Instead of environment variables, use Docker secrets:

```yaml
services:
  backend:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

### 4. Enable SSL/TLS

Use a reverse proxy (Nginx/Traefik) with Let's Encrypt:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 5. Resource Limits

Set resource limits for production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### 6. Health Checks

Health checks are already configured in `docker-compose.yml`:

- **MySQL**: `mysqladmin ping`
- **Redis**: `redis-cli ping`
- **Backend**: `curl http://localhost:8000/api/health`

### 7. Logging

Configure log drivers for centralized logging:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Monitoring

### Flower Dashboard

Access at http://localhost:5555 to monitor:
- Active tasks
- Task history
- Worker status
- Queue lengths
- Task statistics

### Container Metrics

```bash
# View resource usage
docker stats

# View specific container
docker stats qlib-backend
```

### Application Logs

```bash
# Backend logs
docker-compose logs -f backend

# Celery worker logs
docker-compose logs -f celery-worker

# MySQL logs
docker-compose logs -f mysql

# All logs
docker-compose logs -f
```

## Backup and Restore

### Database Backup

```bash
# Backup database
docker-compose exec mysql mysqldump -u root -p qlib_ui > backup_$(date +%Y%m%d_%H%M%S).sql

# Or using environment variables
docker-compose exec mysql sh -c 'mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE}' > backup.sql
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T mysql mysql -u root -p qlib_ui < backup.sql
```

### Volume Backup

```bash
# Backup MySQL data volume
docker run --rm \
  -v qlib-ui_mysql_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mysql_backup.tar.gz -C /data .

# Restore MySQL data volume
docker run --rm \
  -v qlib-ui_mysql_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mysql_backup.tar.gz -C /data
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Inspect container
docker inspect qlib-backend
```

### Database Connection Issues

```bash
# Check MySQL is running
docker-compose ps mysql

# Test connection
docker-compose exec backend python -c "from app.database.session import db_manager; import asyncio; asyncio.run(db_manager.init())"

# Check MySQL logs
docker-compose logs mysql
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Or change port in .env.docker
BACKEND_PORT=8001
```

### Out of Memory

```bash
# Check container memory
docker stats

# Increase Docker Desktop memory allocation
# Or add resource limits in docker-compose.yml
```

### Rebuild After Major Changes

```bash
# Complete rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Cleanup

### Remove Containers

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all
```

### Remove Unused Resources

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build image
        run: docker build -t qlib-backend:${{ github.sha }} .

      - name: Run tests
        run: docker-compose -f docker-compose.test.yml run backend pytest

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push qlib-backend:${{ github.sha }}
```

## Best Practices

1. **Never commit .env files** - Use .env.example as template
2. **Use secrets in production** - Don't use environment variables for sensitive data
3. **Set resource limits** - Prevent containers from consuming all resources
4. **Enable health checks** - Ensure services are running correctly
5. **Use multi-stage builds** - Reduce image size
6. **Regular backups** - Backup data volumes and databases
7. **Monitor logs** - Use centralized logging in production
8. **Keep images updated** - Regularly update base images for security
9. **Use .dockerignore** - Reduce build context size
10. **Tag images properly** - Use semantic versioning

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Celery in Docker](https://docs.celeryproject.org/en/stable/userguide/deployment.html)
