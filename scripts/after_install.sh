#!/bin/bash
set -e

echo "AfterInstall started"

chown -R root:root /home/ec2-user/test/test_app
chmod -R 755 /home/ec2-user/test/test_app

cp /home/ec2-user/persistent_data/.env  "$(pwd)/.env"
cp /home/ec2-user/persistent_data/db.sqlite3 "$(pwd)/db.sqlite3"

echo "AfterInstall completed"
