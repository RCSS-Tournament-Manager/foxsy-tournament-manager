#!/bin/sh

# Use shell parameter expansion to set defaults
: "${DATA_DIR:=/app/data}"
: "${LOG_DIR:=/app/logs}"
: "${API_KEY:=api-key}"
: "${MAX_GAMES_COUNT:=5}"
: "${USE_FAST_API:=true}"
: "${FAST_API_PORT:=8082}"
: "${USE_RABBITMQ:=false}"
: "${RABBITMQ_HOST:=localhost}"
: "${RABBITMQ_PORT:=5672}"
: "${RUNNER_MANAGER_IP:=localhost}"
: "${RUNNER_MANAGER_PORT:=5672}"
: "${STORAGE_IP:=localhost}"
: "${STORAGE_PORT:=5672}"

cd app

exec python -m main --data-dir "$DATA_DIR" --log-dir "$LOG_DIR" --api-key "$API_KEY" --max-games-count "$MAX_GAMES_COUNT" \
    --use-fast-api "$USE_FAST_API" --fast-api-port "$FAST_API_PORT" --use-rabbitmq "$USE_RABBITMQ" --rabbitmq-host "$RABBITMQ_HOST" \
    --rabbitmq-port "$RABBITMQ_PORT" --runner-manager-ip "$RUNNER_MANAGER_IP" --runner-manager-port "$RUNNER_MANAGER_PORT" \
    --storage-ip "$STORAGE_IP" --storage-port "$STORAGE_PORT"
