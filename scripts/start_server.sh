#!/bin/bash
set -e

echo "ApplicationStart started"

APP_DIR="/home/ec2-user/test/test_app"
CONTAINER_NAME="test-app"
IMAGE_NAME="test-app"

cd "$APP_DIR"

echo "Move directory completed"

docker stop "$CONTAINER_NAME" || true
docker rm "$CONTAINER_NAME" || true
docker rmi "$IMAGE_NAME" || true

echo "Old container cleanup completed"

docker build --no-cache -t "$IMAGE_NAME" .

echo "Docker build completed"

docker run -d \
  --name "$CONTAINER_NAME" \
  -p 8000:8000 \
  "$IMAGE_NAME"

echo "Docker container start completed"

# 🔥 ここが追加ポイント（アプリ起動待ち）
sleep 5

echo "ApplicationStart completed"
