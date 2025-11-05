#!/bin/bash
# Celery Worker Startup Script

# Set working directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Celery worker with configurations
celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --queues=data_import,backtest,strategy \
    --hostname=worker@%h
