#!/bin/bash
set -xe

echo "ApplicationStart started"

APP_DIR="/home/ec2-user/test/test_app"
DATA_DIR="/home/ec2-user/persistent_data"

cd "$APP_DIR"

# 1. ホストルートの完全な資格で、古いコンテナを確実に破壊
sudo -E -u root /usr/bin/docker compose down || true

# 2. ここで安全地帯からデータをアプリフォルダに戻す
sudo cp $DATA_DIR/.env $APP_DIR/.env
sudo cp $DATA_DIR/db.sqlite3 $APP_DIR/db.sqlite3

# 3. キャッシュの全削除をビルド前に実行
sudo -E -u root /usr/bin/docker builder prune -a -f

# 4. ホストルートのパワーで完璧にビルドおよびコンテナ起動
sudo -E -u root /usr/bin/docker compose up -d --build

# 5. 【最後の仕上げ】コンテナ起動が完了した後に、全員まとめて ec2-user に一括変換
sudo chown -R ec2-user:ec2-user $APP_DIR
sudo chmod -R 755 $APP_DIR

sleep 5
echo "ApplicationStart completed"