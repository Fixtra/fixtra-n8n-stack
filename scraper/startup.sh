#!/bin/bash
# startup.sh - Run by the container on startup
set -e

# Wait for PostgreSQL to become available
echo "Waiting for PostgreSQL to start..."
until PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing SQL script"
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f init.sql

# Start the application
echo "Starting the application..."
exec uvicorn app:app --host 0.0.0.0 --port 5000