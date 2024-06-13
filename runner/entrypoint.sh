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
: "${TO_RUNNER_QUEUE:=to-runner-queue}"
: "${TO_RUNNER_MANAGER_QUEUE:=to-runner-manager-queue}"
: "${RUNNER_MANAGER_IP:=localhost}"
: "${RUNNER_MANAGER_PORT:=5672}"
: "${MINIO_ENDPOINT:=localhost:9000}"
: "${MINIO_ACCESS_KEY:=minioadmin}"
: "${MINIO_SECRET_KEY:=minioadmin}"
: "${SERVER_BUCKET_NAME:=server}"
: "${BASE_TEAM_BUCKET_NAME:=baseteam}"
: "${TEAM_CONFIG_BUCKET_NAME:=teamconfig}"
: "${GAME_LOG_BUCKET_NAME:=gamelog}"

cd app

exec python -m main --data-dir "$DATA_DIR" --log-dir "$LOG_DIR" --api-key "$API_KEY" --max-games-count "$MAX_GAMES_COUNT" \
    --use-fast-api "$USE_FAST_API" --fast-api-port "$FAST_API_PORT" --use-rabbitmq "$USE_RABBITMQ" --rabbitmq-host "$RABBITMQ_HOST" \
    --rabbitmq-port "$RABBITMQ_PORT" --runner-manager-ip "$RUNNER_MANAGER_IP" --runner-manager-port "$RUNNER_MANAGER_PORT" \
    --minio-endpoint "$MINIO_ENDPOINT" --minio-access-key "$MINIO_ACCESS_KEY" --minio-secret-key "$MINIO_SECRET_KEY" \
    --server-bucket-name "$SERVER_BUCKET_NAME" --base-team-bucket-name "$BASE_TEAM_BUCKET_NAME" --team-config-bucket-name "$TEAM_CONFIG_BUCKET_NAME" \
    --game-log-bucket-name "$GAME_LOG_BUCKET_NAME" --to-runner-queue "$TO_RUNNER_QUEUE" --to-runner-manager-queue "$TO_RUNNER_MANAGER_QUEUE"
