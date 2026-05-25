"""
E2E テスト用 pytest conftest
pytest-django の live_server fixture と pytest-playwright を組み合わせる
"""

import os
import pytest
from datetime import date, datetime, time

from django.utils import timezone

# pytest-playwright が asyncio イベントループを起動するため、
# Django の同期 DB 呼び出しを許可する
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


# ── テストデータ fixture ───────────────────────────────────────

@pytest.fixture
def e2e_user(db):
    from accounts.models import User
    return User.objects.create_user(
        login_id="e2e_user@example.com",
        name="E2Eユーザー",
        password="E2EPass123",
    )


@pytest.fixture
def e2e_staff(db):
    from accounts.models import User
    return User.objects.create_user(
        login_id="e2e_staff@example.com",
        name="E2E管理者",
        password="E2EPass123",
        role="admin",
    )


@pytest.fixture
def e2e_room(db):
    from reservations.models import Room
    return Room.objects.create(name="テスト会議室", capacity=10, is_active=True)


@pytest.fixture
def e2e_room2(db):
    from reservations.models import Room
    return Room.objects.create(name="会議室β", capacity=5, is_active=True)


@pytest.fixture
def e2e_reservation(db, e2e_room, e2e_user):
    from reservations.models import Reservation
    today = date.today()
    return Reservation.objects.create(
        room=e2e_room,
        user=e2e_user,
        reserved_by=e2e_user.name,
        title="E2Eテスト会議",
        start_at=timezone.make_aware(datetime.combine(today, time(10, 0))),
        end_at=timezone.make_aware(datetime.combine(today, time(11, 0))),
        is_cancelled=False,
    )


# ── ログイン済みページ fixture ─────────────────────────────────

@pytest.fixture
def logged_in_page(page, live_server, e2e_user):
    """
    ログイン済みの Playwright ページを返す。
    ページは /calendar/ にいるが、テストで room 等の fixture を使う場合は
    page.reload() または page.goto(calendar_url) を呼んでページを再取得すること。
    （fixture の解決順序の関係で room 等は login 後に作られる場合がある）
    """
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill('input[name="username"]', "e2e_user@example.com")
    page.fill('input[name="password"]', "E2EPass123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{live_server.url}/calendar/**")
    page.set_default_timeout(15000)
    return page


@pytest.fixture
def logged_in_staff_page(page, live_server, e2e_staff):
    """管理者でログイン済みの Playwright ページを返す"""
    page.goto(f"{live_server.url}/accounts/login/")
    page.fill('input[name="username"]', "e2e_staff@example.com")
    page.fill('input[name="password"]', "E2EPass123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{live_server.url}/calendar/**")
    page.set_default_timeout(15000)
    return page


@pytest.fixture
def calendar_url(live_server):
    """カレンダーページの URL を返す"""
    return f"{live_server.url}/calendar/"


# ── 共通ヘルパー fixture ──────────────────────────────────────

@pytest.fixture
def wait_for_calendar():
    """FullCalendar グリッドが描画されるまで待機するヘルパーを返す"""
    def _wait(page):
        page.wait_for_selector(".fc-view-harness", state="visible", timeout=15000)
    return _wait
