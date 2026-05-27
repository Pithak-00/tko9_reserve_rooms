#!/bin/bash
set -e

echo "BeforeInstall started"

APP_DIR="/home/ec2-user/test/test_app"
DATA_DIR="/home/ec2-user/persistent_data"

# 1. 安全地帯フォルダが万が一無かった時のために作成
mkdir -p $DATA_DIR

# 2. 今アプリフォルダにある本物のデータを、安全地帯へ上書き避難（コピー）
cp $APP_DIR/.env $DATA_DIR/.env
cp $APP_DIR/db.sqlite3 $DATA_DIR/db.sqlite3

echo "BeforeInstall completed"