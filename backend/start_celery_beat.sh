#!/bin/bash
# Celery Beat Scheduler Startup Script
# Used for periodic tasks

# Set working directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Celery beat scheduler
celery -A app.celery_app beat \
    --loglevel=info \
    --schedule=/tmp/celerybeat-schedule \
    --pidfile=/tmp/celerybeat.pid
