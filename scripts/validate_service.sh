#!/bin/bash
set -e

echo "ValidateService started"

docker ps

curl -f http://localhost:8000

echo "ValidateService completed"