#!/bin/bash

# -s (サイレント) -o /dev/null (出力破棄) -w "%{http_code}" でステータスコードだけを取得
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)

# 200(OK) または 302(Redirect) なら合格（Succeeded）とするロジック
if [ "$STATUS_CODE" -eq 200 ] || [ "$STATUS_CODE" -eq 302 ]; then
    echo "ValidateService Success with Status Code: $STATUS_CODE"
    exit 0
else
    echo "ValidateService Failed with Status Code: $STATUS_CODE"
    exit 1
fi