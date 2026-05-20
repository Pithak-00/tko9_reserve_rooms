#!/bin/bash
set -e

echo "AfterInstall started"

chown -R root:root /home/ec2-user/test/test_app
chmod -R 755 /home/ec2-user/test/test_app

echo "AfterInstall completed"
