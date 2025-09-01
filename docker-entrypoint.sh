#!/bin/sh
set -e
mkdir -p /app/databases /app/data
if [ ! -f /app/databases/app.db ] && [ -f /app/seed/app.db ]; then
  cp /app/seed/app.db /app/databases/app.db
fi
exec "$@"
