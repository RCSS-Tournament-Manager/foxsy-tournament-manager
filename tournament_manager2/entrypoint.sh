#!/bin/sh

# Use shell parameter expansion to set defaults

: "${DATA_DIR:=/app/data}"
: "${LOG_DIR:=/app/data/logs}"
: "${DB:=example.db}"
: "${API_KEY:=api-key}"
: "${FAST_API_PORT:=8085}"
: "${RABBITMQ_HOST:=localhost}"
: "${RABBITMQ_PORT:=5672}"
: "${RABBITMQ_USERNAME:=guest}"
: "${RABBITMQ_PASSWORD:=guest1234}"
: "${TO_RUNNER_QUEUE:=to-runner}"
: "${MINIO_ENDPOINT:=localhost:9000}"
: "${MINIO_ACCESS_KEY:=guest}"
: "${MINIO_SECRET_KEY:=guest1234}"
: "${SERVER_BUCKET_NAME:=server}"
: "${BASE_TEAM_BUCKET_NAME:=baseteam}"
: "${TEAM_CONFIG_BUCKET_NAME:=teamconfig}"
: "${GAME_LOG_BUCKET_NAME:=gamelog}"
: "${TMP_GAME_LOG_DIR:=/app/tmp_game_log}"

cd /app
mkdir -p "$DATA_DIR" "$LOG_DIR" "$TMP_GAME_LOG_DIR"


exec uv run python /app/app/main.py \
    --data-dir "$DATA_DIR" \
    --log-dir "$LOG_DIR" \
    --db "$DB" \
    --api "$API_KEY" \
    --fast-api-port "$FAST_API_PORT" \
    --rabbitmq-host "$RABBITMQ_HOST" \
    --rabbitmq-port "$RABBITMQ_PORT" \
    --rabbitmq-username "$RABBITMQ_USERNAME" \
    --rabbitmq-password "$RABBITMQ_PASSWORD" \
    --to-runner-queue "$TO_RUNNER_QUEUE" \
    --minio-endpoint "$MINIO_ENDPOINT" \
    --minio-access-key "$MINIO_ACCESS_KEY" \
    --minio-secret-key "$MINIO_SECRET_KEY" \
    --server-bucket-name "$SERVER_BUCKET_NAME" \
    --base-team-bucket-name "$BASE_TEAM_BUCKET_NAME" \
    --team-config-bucket-name "$TEAM_CONFIG_BUCKET_NAME" \
    --game-log-bucket-name "$GAME_LOG_BUCKET_NAME" \
    --tmp-game-log-dir "$TMP_GAME_LOG_DIR"