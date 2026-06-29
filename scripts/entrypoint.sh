#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for database port to open..."
python -c "
import socket
import time
import os
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/approval_db')
# Normalize asyncpg prefix if present
if db_url.startswith('postgresql+asyncpg://'):
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

u = urlparse(db_url)
host = u.hostname or 'db'
port = u.port or 5432

for i in range(30):
    try:
        with socket.create_connection((host, port), timeout=1):
            print('Database is ready!')
            break
    except Exception:
        print(f'Database port {host}:{port} not ready yet... ({i+1}/30)')
        time.sleep(1)
else:
    print('Database port did not open in time, exiting.')
    exit(1)
"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
