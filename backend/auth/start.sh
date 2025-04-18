#!/bin/sh

set -e

echo "Waiting for DB..."
/auth/wait-for-it.sh db:5432 --timeout=30 --strict -- echo "DB is up!"

echo "Verifying DB connection..."
MAX_TRIES=10
TRIES=0
until pg_isready -h db -p 5432 -U "$POSTGRES_USER"; do
  TRIES=$((TRIES+1))
  if [ "$TRIES" -ge "$MAX_TRIES" ]; then
    echo "DB Connection Failed - exiting!"
    exit 1
  fi
  echo "DB not ready yet... retrying in 1s"
  sleep 1
done

echo "Starting FastAPI with uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port 80
