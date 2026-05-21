#!/bin/bash
set -xe

echo "ApplicationStart started"

APP_DIR="/home/ec2-user/test/test_app"
CONTAINER_NAME="test-app"
IMAGE_NAME="test-app"

cd "$APP_DIR"

echo "Move directory completed"

/usr/bin/docker stop "$CONTAINER_NAME" || true
/usr/bin/docker rm "$CONTAINER_NAME" || true
/usr/bin/docker rmi "$IMAGE_NAME" || true

echo "Old container cleanup completed"

/usr/bin/docker build --no-cache -t "$IMAGE_NAME" .

echo "Docker build completed"

/usr/bin/docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -p 80:8000 \
  "$IMAGE_NAME"

echo "Docker container start completed"


sleep 5

echo "ApplicationStart completed"
