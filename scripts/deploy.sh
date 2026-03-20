#!/usr/bin/env bash
set -e  # при любой ошибки скрипт остановится 

APP_DIR="/opt/tg-bot-yt-downloader"
CONTAINER_NAME="tg-bot-yt-downloader"
IMAGE_NAME="tg-bot-yt-downloader:latest"
BRANCH="main"

echo "==> Go to app dir"
cd "$APP_DIR" 

echo "==> Update code"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "==> Build image"
docker build -t "$IMAGE_NAME" .

echo "==> Stop old container"
docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true

echo "==> Start new container"
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  #--env-file .env \
  "$IMAGE_NAME"

echo "==> Done"
docker ps