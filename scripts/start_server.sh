#!/bin/bash
set -xe

echo "ApplicationStart started"

APP_DIR="/home/ec2-user/test/test_app"
DATA_DIR="/home/ec2-user/persistent_data"

cd "$APP_DIR"

# 1. 古いコンテナを確実に破壊
sudo -E -u root /usr/bin/docker compose down || true

# 2. 過去のデプロイで置き去りにされた古いコンテナの残骸と不要なイメージを overlay2 から完全一掃
# ※ 新しいコンテナをビルドする前に、使われていないゴミを根こそぎ消去してディスクを最大開放する
sudo -E -u root /usr/bin/docker system prune -a -f

# 3. 安全地帯から永続データをアプリフォルダに復元
sudo cp $DATA_DIR/.env $APP_DIR/.env
sudo cp $DATA_DIR/db.sqlite3 $APP_DIR/db.sqlite3

# 4. キャッシュの全削除をビルド前に実行（二重の防衛網）
sudo -E -u root /usr/bin/docker builder prune -a -f

# 5. 最新コードで完璧にビルドおよびコンテナ起動
sudo -E -u root /usr/bin/docker compose up -d --build

# 6. 【最後の仕上げ】権限を ec2-user に一括クリーン変換
sudo chown -R ec2-user:ec2-user $APP_DIR
sudo chmod -R 755 $APP_DIR

sleep 5

echo "ApplicationStart completed successfully"