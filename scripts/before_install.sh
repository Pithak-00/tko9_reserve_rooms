#!/bin/bash
set -e

echo "BeforeInstall started"

echo "=== Docker cleanup start ==="

docker build prune -f

echo "=== Docker cleanup done ==="

mkdir -p /home/ec2-user/test

echo "BeforeInstall completed"
