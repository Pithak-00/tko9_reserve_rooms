"""
高負荷テスト（requests + concurrent.futures 版）
================================================
使い方:
  # Django サーバーを先に起動しておく
  python manage.py runserver 0.0.0.0:8000

  # 実行
  python scripts/load_test.py [--host http://localhost:8000] [--users 20] [--duration 30]
"""
import argparse
import json
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests

# ─── 設定 ──────────────────────────────────────────────────────
DEFAULT_HOST     = "http://localhost:8000"
DEFAULT_USERS    = 20
DEFAULT_DURATION = 30   # 秒
ROOM_PK          = 1    # テスト対象会議室 pk

USERS = [
    {"username": "testuser@example.com", "password": "TestPass123", "role": "user"},
    {"username": "admin@example.com",    "password": "AdminPass123", "role": "admin"},
]


# ─── HTTP クライアント ─────────────────────────────────────────

class SessionClient:
    def __init__(self, host, user_info):
        self.host    = host
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "LoadTest/1.0"})
        self.role    = user_info["role"]
        self._login(user_info["username"], user_info["password"])

    def _login(self, username, password):
        r = self.session.get(f"{self.host}/accounts/login/")
        csrftoken = self.session.cookies.get("csrftoken", "")
        self.session.post(
            f"{self.host}/accounts/login/",
            data={"username": username, "password": password},
            headers={"X-CSRFToken": csrftoken, "Referer": f"{self.host}/accounts/login/"},
        )

    def get(self, path, **kwargs):
        t0 = time.perf_counter()
        try:
            r = self.session.get(f"{self.host}{path}", timeout=10, **kwargs)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return r.status_code, elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return 0, elapsed_ms

    def post(self, path, data, **kwargs):
        csrftoken = self.session.cookies.get("csrftoken", "")
        t0 = time.perf_counter()
        try:
            r = self.session.post(
                f"{self.host}{path}", data=data,
                headers={"X-CSRFToken": csrftoken, "Referer": f"{self.host}{path}"},
                allow_redirects=False, timeout=10, **kwargs
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return r.status_code, elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return 0, elapsed_ms


# ─── シナリオ ──────────────────────────────────────────────────

def user_scenario(client, results, stop_at):
    """一般ユーザー：カレンダー閲覧 → イベントAPI → 予約作成"""
    today = date.today()
    while time.time() < stop_at:
        # カレンダー閲覧
        status, ms = client.get("/calendar/")
        results.append(("GET /calendar/", status, ms))

        # イベント API（一番頻繁に叩かれる）
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        week_end   = (today + timedelta(days=7)).isoformat()
        status, ms = client.get(f"/reservations/events/?start={week_start}&end={week_end}")
        results.append(("GET /events/", status, ms))

        # 自分の予約一覧
        status, ms = client.get("/reservations/my/")
        results.append(("GET /my/", status, ms))

        # 予約作成フォーム取得
        future = (today + timedelta(days=random.randint(1, 60))).isoformat()
        status, ms = client.get(f"/reservations/create/?date={future}&time=10:00&end_time=11:00")
        results.append(("GET /create/", status, ms))

        # 予約作成 POST（ランダム日時で重複を減らす）
        hour    = random.randint(8, 17)
        date_ok = (today + timedelta(days=random.randint(60, 180))).isoformat()
        status, ms = client.post("/reservations/create/", data={
            "room":         ROOM_PK,
            "title":        f"負荷テスト{random.randint(10000,99999)}",
            "reserve_date": date_ok,
            "start_time":   f"{hour:02d}:00",
            "end_time":     f"{hour+1:02d}:00",
            "is_all_day":   "",
        })
        results.append(("POST /create/", status, ms))

        time.sleep(random.uniform(0.5, 1.5))


def admin_scenario(client, results, stop_at):
    """管理者：各管理画面を巡回"""
    while time.time() < stop_at:
        for path, name in [
            ("/admin-panel/reservations/", "GET /admin/reservations/"),
            ("/admin-panel/operation-log/", "GET /admin/operation-log/"),
            ("/admin-panel/users/",         "GET /admin/users/"),
            ("/admin-panel/rooms/",         "GET /admin/rooms/"),
        ]:
            status, ms = client.get(path)
            results.append((name, status, ms))
        time.sleep(random.uniform(1.0, 2.0))


# ─── 集計・レポート ─────────────────────────────────────────────

def print_report(all_results, total_duration):
    from collections import defaultdict

    by_endpoint = defaultdict(list)
    for name, status, ms in all_results:
        by_endpoint[name].append((status, ms))

    total_req = len(all_results)
    total_fail = sum(1 for _, s, _ in all_results if s not in (200, 302))
    all_ms = [ms for _, _, ms in all_results]

    print("\n" + "=" * 68)
    print("【高負荷テスト結果】")
    print(f"  実行時間        : {total_duration:.1f} s")
    print(f"  総リクエスト数  : {total_req:,}")
    print(f"  失敗数          : {total_fail:,}  ({total_fail/total_req*100:.1f}%)" if total_req else "  失敗数: -")
    print(f"  スループット    : {total_req/total_duration:.1f} req/s")
    print()

    if all_ms:
        s = sorted(all_ms)
        n = len(s)
        print(f"  レスポンスタイム（全体）")
        print(f"    平均   : {statistics.mean(s):.0f} ms")
        print(f"    中央値 : {statistics.median(s):.0f} ms")
        print(f"    90%ile : {s[int(n*0.90)]:.0f} ms")
        print(f"    95%ile : {s[int(n*0.95)]:.0f} ms")
        print(f"    99%ile : {s[int(n*0.99)]:.0f} ms")
        print(f"    最大   : {max(s):.0f} ms")

    print()
    print(f"  {'エンドポイント':<30} {'件数':>6}  {'成功率':>7}  {'平均ms':>7}  {'95%ile':>7}")
    print(f"  {'-'*30} {'-'*6}  {'-'*7}  {'-'*7}  {'-'*7}")
    for name, items in sorted(by_endpoint.items()):
        cnt     = len(items)
        ok      = sum(1 for s, _ in items if s in (200, 302))
        ms_list = sorted(m for _, m in items)
        avg_ms  = statistics.mean(ms_list)
        p95_ms  = ms_list[int(len(ms_list)*0.95)] if ms_list else 0
        print(f"  {name:<30} {cnt:>6}  {ok/cnt*100:>6.1f}%  {avg_ms:>7.0f}  {p95_ms:>7.0f}")

    print("=" * 68)


# ─── メイン ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Django 高負荷テスト")
    parser.add_argument("--host",     default=DEFAULT_HOST)
    parser.add_argument("--users",    type=int, default=DEFAULT_USERS)
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION)
    args = parser.parse_args()

    print(f"[負荷テスト開始]  host={args.host}  users={args.users}  duration={args.duration}s")

    stop_at = time.time() + args.duration
    all_results = []
    threads_results = [[] for _ in range(args.users)]

    def worker(idx):
        user_info = USERS[idx % len(USERS)]
        client    = SessionClient(args.host, user_info)
        if user_info["role"] == "admin":
            admin_scenario(client, threads_results[idx], stop_at)
        else:
            user_scenario(client, threads_results[idx], stop_at)

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.users) as ex:
        futures = [ex.submit(worker, i) for i in range(args.users)]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  [worker error] {e}")
    t_end = time.perf_counter()

    for r in threads_results:
        all_results.extend(r)

    print_report(all_results, t_end - t_start)


if __name__ == "__main__":
    main()
