#!/bin/sh

# Use shell parameter expansion to set defaults
: "${DATA_DIR:=/app/data}"
: "${LOG_DIR:=/app/data/logs}"
: "${API_KEY:=api-key}"
: "${MAX_GAMES_COUNT:=5}"
: "${USE_FAST_API:=true}"
: "${FAST_API_IP:=127.0.0.1}"
: "${FAST_API_PORT:=8082}"
: "${USE_RABBITMQ:=true}"
: "${RABBITMQ_HOST:=localhost}"
: "${RABBITMQ_PORT:=5672}"
: "${RABBITMQ_USERNAME:=guest}"
: "${RABBITMQ_PASSWORD:=guest1234}"
: "${TO_RUNNER_QUEUE:=to-runner}"
: "${CONNECT_TO_TOURNAMENT_MANAGER:=false}"
: "${TOURNAMENT_MANAGER_IP:=localhost}"
: "${TOURNAMENT_MANAGER_PORT:=8085}"
: "${TOURNAMENT_MANAGER_API_KEY:=api-key}"
: "${USE_MINIO:=true}"
: "${MINIO_ENDPOINT:=localhost:9000}"
: "${MINIO_ACCESS_KEY:=guest}"
: "${MINIO_SECRET_KEY:=guest1234}"
: "${SERVER_BUCKET_NAME:=server}"
: "${BASE_TEAM_BUCKET_NAME:=baseteam}"
: "${TEAM_CONFIG_BUCKET_NAME:=teamconfig}"
: "${GAME_LOG_BUCKET_NAME:=gamelog}"

cd app

exec python -m main \
    --data-dir "$DATA_DIR" \
    --log-dir "$LOG_DIR" \
    --api-key "$API_KEY" \
    --max-games-count "$MAX_GAMES_COUNT" \
    --use-fast-api "$USE_FAST_API" \
    --fast-api-port "$FAST_API_PORT" \
    --fast-api-ip "$FAST_API_IP" \
    --use-rabbitmq "$USE_RABBITMQ" \
    --rabbitmq-host "$RABBITMQ_HOST" \
    --rabbitmq-port "$RABBITMQ_PORT" \
    --rabbitmq-username "$RABBITMQ_USERNAME" \
    --rabbitmq-password "$RABBITMQ_PASSWORD" \
    --connect-to-tournament-manager "$CONNECT_TO_TOURNAMENT_MANAGER" \
    --tournament-manager-ip "$TOURNAMENT_MANAGER_IP" \
    --tournament-manager-port "$TOURNAMENT_MANAGER_PORT" \
    --tournament-manager-api-key "$TOURNAMENT_MANAGER_API_KEY" \
    --use-minio "$USE_MINIO" \
    --minio-endpoint "$MINIO_ENDPOINT" \
    --minio-access-key "$MINIO_ACCESS_KEY" \
    --minio-secret-key "$MINIO_SECRET_KEY" \
    --server-bucket-name "$SERVER_BUCKET_NAME" \
    --base-team-bucket-name "$BASE_TEAM_BUCKET_NAME" \
    --team-config-bucket-name "$TEAM_CONFIG_BUCKET_NAME" \
    --game-log-bucket-name "$GAME_LOG_BUCKET_NAME" \
    --to-runner-queue "$TO_RUNNER_QUEUE"

