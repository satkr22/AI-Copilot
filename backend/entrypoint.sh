#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until pg_isready \
    -h postgres \
    -p 5432 \
    -U "$POSTGRES_USER"
do
    sleep 2
done

echo "PostgreSQL is ready"

echo "Creating tables..."
python -m app.db.init_db

echo "Starting FastAPI..."

exec "$@"