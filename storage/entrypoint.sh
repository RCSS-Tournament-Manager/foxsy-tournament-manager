#!/bin/sh

# Use shell parameter expansion to set defaults
: "${DATA_DIR:=/app/data}"
: "${LOG_DIR:=/app/logs}"
: "${API_KEY:=api-key}"

cd app
exec python -m main --data-dir "$DATA_DIR" --log-dir "$LOG_DIR" --api-key "$API_KEY" "$@"
