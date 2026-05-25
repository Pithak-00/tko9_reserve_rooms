"""
Locust 高負荷テスト
===================
使い方:
  # サーバー起動（別ターミナル）
  python manage.py runserver 0.0.0.0:8000

  # ヘッドレス実行（60秒・同時10ユーザー・最大毎秒2人追加）
  locust -f locustfile.py --host=http://localhost:8000 \
         --headless -u 10 -r 2 -t 60s \
         --html=load_test_report.html

  # Web UI で実行（ブラウザで http://localhost:8089 を開く）
  locust -f locustfile.py --host=http://localhost:8000

シナリオ:
  - ReservationUser  : 一般ユーザー操作（カレンダー閲覧・予約作成・詳細確認）
  - AdminUser        : 管理者操作（全予約一覧・ユーザー一覧・操作ログ）
"""
import json
import random
from datetime import date, timedelta

from locust import HttpUser, task, between, events


# ─── 共通ヘルパー ─────────────────────────────────────────────

def get_csrftoken(client):
    """セッションの CSRF トークンを取得"""
    return client.cookies.get("csrftoken", "")


def login(client, username, password):
    """Django ログイン。成功すれば True を返す"""
    # GET でトークンを取得
    client.get("/accounts/login/")
    csrftoken = get_csrftoken(client)
    resp = client.post(
        "/accounts/login/",
        data={"username": username, "password": password},
        headers={"X-CSRFToken": csrftoken, "Referer": client.base_url + "/accounts/login/"},
        allow_redirects=True,
        name="POST /accounts/login/",
    )
    return resp.status_code == 200


# ─── 一般ユーザーシナリオ ─────────────────────────────────────

class ReservationUser(HttpUser):
    """
    一般ユーザーの典型的な操作フロー
    weight=3 なので AdminUser より 3 倍多くスポーン
    """
    weight = 3
    wait_time = between(1, 3)  # タスク間の待機 1〜3 秒

    def on_start(self):
        """ユーザー起動時にログイン"""
        # テスト用ユーザー（事前に manage.py shell で作成しておく）
        # login_id / password を環境に合わせて変更すること
        ok = login(self.client, "testuser@example.com", "TestPass123")
        if not ok:
            # ログイン失敗時は全タスクをスキップ
            self.environment.runner.quit()

    # ── 閲覧系（高頻度） ──────────────────────────────────────

    @task(5)
    def view_calendar(self):
        """カレンダートップ"""
        self.client.get("/calendar/", name="GET /calendar/")

    @task(5)
    def fetch_events_api(self):
        """カレンダーイベント API（最も頻繁に叩かれるエンドポイント）"""
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        week_end   = (today + timedelta(days=7)).isoformat()
        self.client.get(
            f"/reservations/events/?start={week_start}&end={week_end}",
            name="GET /reservations/events/",
        )

    @task(3)
    def view_my_reservations(self):
        self.client.get("/reservations/my/", name="GET /reservations/my/")

    @task(2)
    def view_create_form(self):
        """予約作成フォームを開く"""
        today = date.today() + timedelta(days=1)
        self.client.get(
            f"/reservations/create/?date={today.isoformat()}&time=10:00&end_time=11:00",
            name="GET /reservations/create/",
        )

    # ── 書き込み系（低頻度） ─────────────────────────────────

    @task(1)
    def create_reservation(self):
        """予約作成 POST"""
        # 毎回ランダムな日時で重複を避ける
        future_date = date.today() + timedelta(days=random.randint(1, 30))
        hour = random.choice(["09", "10", "11", "13", "14", "15"])
        end_hour = str(int(hour) + 1).zfill(2)

        self.client.get("/reservations/create/")
        csrftoken = get_csrftoken(self.client)

        self.client.post(
            "/reservations/create/",
            data={
                "room":         1,         # 要: DB に room pk=1 が存在すること
                "title":        f"負荷テスト予約 {random.randint(1000, 9999)}",
                "reserve_date": future_date.isoformat(),
                "start_time":   f"{hour}:00",
                "end_time":     f"{end_hour}:00",
                "is_all_day":   "",
            },
            headers={
                "X-CSRFToken": csrftoken,
                "Referer": self.client.base_url + "/reservations/create/",
            },
            allow_redirects=False,
            name="POST /reservations/create/",
        )


# ─── 管理者シナリオ ───────────────────────────────────────────

class AdminUser(HttpUser):
    """
    管理者ユーザーの操作フロー
    weight=1 なので ReservationUser より少なくスポーン
    """
    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        ok = login(self.client, "admin@example.com", "AdminPass123")
        if not ok:
            self.environment.runner.quit()

    @task(3)
    def view_all_reservations(self):
        self.client.get("/admin-panel/reservations/", name="GET /admin-panel/reservations/")

    @task(2)
    def view_operation_log(self):
        self.client.get("/admin-panel/operation-log/", name="GET /admin-panel/operation-log/")

    @task(2)
    def view_user_list(self):
        self.client.get("/admin-panel/users/", name="GET /admin-panel/users/")

    @task(1)
    def view_room_list(self):
        self.client.get("/admin-panel/rooms/", name="GET /admin-panel/rooms/")


# ─── カスタムレポートコールバック ──────────────────────────────

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """テスト終了時に簡易サマリーを出力"""
    stats = environment.runner.stats.total
    print("\n" + "="*60)
    print("【高負荷テスト結果サマリー】")
    print(f"  総リクエスト数  : {stats.num_requests:,}")
    print(f"  失敗数          : {stats.num_failures:,}")
    print(f"  失敗率          : {stats.fail_ratio * 100:.1f}%")
    print(f"  平均レスポンス  : {stats.avg_response_time:.0f} ms")
    print(f"  中央値(50%ile)  : {stats.get_response_time_percentile(0.50):.0f} ms")
    print(f"  95%ile          : {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"  99%ile          : {stats.get_response_time_percentile(0.99):.0f} ms")
    print(f"  最大レスポンス  : {stats.max_response_time:.0f} ms")
    print(f"  スループット    : {stats.current_rps:.1f} req/s")
    print("="*60)
