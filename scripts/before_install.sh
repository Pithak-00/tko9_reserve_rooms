Bash
#!/bin/bash
set -e

echo "BeforeInstall started"

APP_DIR="/home/ec2-user/test/test_app"
DATA_DIR="/home/ec2-user/persistent_data"

mkdir -p $DATA_DIR

# ファイルが物理的に存在する場合のみ、安全地帯へコピーする
if [ -f "$APP_DIR/.env" ]; then
    cp $APP_DIR/.env $DATA_DIR/.env
fi

if [ -f "$APP_DIR/db.sqlite3" ]; then
    cp $APP_DIR/db.sqlite3 $DATA_DIR/db.sqlite3
fi

echo "BeforeInstall completed"