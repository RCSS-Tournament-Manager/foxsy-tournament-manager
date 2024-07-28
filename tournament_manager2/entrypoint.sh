#!/bin/sh

# Use shell parameter expansion to set defaults

: "${DATA_DIR:=/home/appuser/app/data}"
: "${LOG_DIR:=/home/appuser/app/data/logs}"
: "${DB:=example.db}"
: "${API_KEY:=api-key}"
: "${FAST_API_PORT:=8085}"
: "${RABBITMQ_HOST:=localhost}"
: "${RABBITMQ_PORT:=5672}"
: "${RABBITMQ_USERNAME:=guest}"
: "${RABBITMQ_PASSWORD:=guest1234}"
: "${TO_RUNNER_QUEUE:=to-runner}"

cd app

exec python -m main --data-dir "$DATA_DIR" --log-dir "$LOG_DIR" --db "$DB" \
    --api "$API_KEY" --fast-api-port "$FAST_API_PORT" \
    --rabbitmq-host "$RABBITMQ_HOST" --rabbitmq-port "$RABBITMQ_PORT" \
    --rabbitmq-username "$RABBITMQ_USERNAME" --rabbitmq-password "$RABBITMQ_PASSWORD" \
    --to-runner-queue "$TO_RUNNER_QUEUE"