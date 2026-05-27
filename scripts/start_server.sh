#!/bin/bash
set -xe

echo "ApplicationStart started"

APP_DIR="/home/ec2-user/test/test_app"

cd "$APP_DIR"

echo "Move directory completed"

/usr/bin/docker compose down || true

echo "Old container cleanup completed"

/usr/bin/docker builder prune -a -f

/usr/bin/docker compose up -d --build

echo "Docker compose up completed"

echo "Docker build cache cleanup completed"

sleep 5

echo "ApplicationStart completed"
