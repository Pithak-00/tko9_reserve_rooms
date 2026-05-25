"""
高負荷テスト用のユーザー・データをセットアップするスクリプト
実行: python manage.py shell < scripts/create_load_test_users.py
"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User
from reservations.models import Room

# ── 一般ユーザー ──────────────────────────────────────────────
if not User.objects.filter(login_id="testuser@example.com").exists():
    User.objects.create_user(
        login_id="testuser@example.com",
        name="負荷テストユーザー",
        password="TestPass123",
    )
    print("✓ testuser@example.com 作成")
else:
    print("- testuser@example.com は既に存在")

# ── 管理者ユーザー ────────────────────────────────────────────
if not User.objects.filter(login_id="admin@example.com").exists():
    User.objects.create_user(
        login_id="admin@example.com",
        name="負荷テスト管理者",
        password="AdminPass123",
        role="admin",
        is_staff=True,
    )
    print("✓ admin@example.com 作成")
else:
    print("- admin@example.com は既に存在")

# ── 会議室（pk=1 が存在しない場合のみ作成） ───────────────────
if not Room.objects.filter(pk=1).exists():
    Room.objects.create(name="負荷テスト会議室A", capacity=10, is_active=True)
    print("✓ 会議室 pk=1 作成")
else:
    print(f"- 会議室 pk=1 は既に存在: {Room.objects.get(pk=1).name}")

print("\nセットアップ完了。以下のコマンドで負荷テストを実行してください：")
print()
print("  # ヘッドレス（60秒・同時10ユーザー）")
print("  locust -f locustfile.py --host=http://localhost:8000 \\")
print("         --headless -u 10 -r 2 -t 60s --html=load_test_report.html")
print()
print("  # Web UI")
print("  locust -f locustfile.py --host=http://localhost:8000")
print("  → ブラウザで http://localhost:8089 を開く")
