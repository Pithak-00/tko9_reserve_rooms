#!/bin/bash
set -e

echo "AfterInstall started"

APP_DIR="/home/ec2-user/test/test_app"

# 権限設定
chown -R ec2-user:ec2-user $APP_DIR
chmod -R 755 $APP_DIR

# .env と DB をアプリディレクトリにコピー
cp /home/ec2-user/persistent_data/.env $APP_DIR/.env
cp /home/ec2-user/persistent_data/db.sqlite3 $APP_DIR/db.sqlite3

echo "AfterInstall completed"
