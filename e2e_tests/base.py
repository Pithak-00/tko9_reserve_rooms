"""
E2E テスト共通ベースクラス・ヘルパー

使い方:
    class MyE2ETest(E2ETestBase):
        def test_something(self):
            page = self.new_page()
            self.login(page)
            page.goto(self.url("/calendar/"))
            ...
"""

from datetime import date, datetime, time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from playwright.sync_api import sync_playwright

from accounts.models import Department, User
from reservations.models import (
    Building, DepartmentRoom, Facility, Reservation, Room, RoomFacility,
)


class E2ETestBase(StaticLiveServerTestCase):
    """
    Playwright E2E テストの共通ベースクラス。
    各テストメソッドで self.new_page() を呼ぶとブラウザページが得られる。
    """

    # ヘッドレスモード（CI は True 推奨、デバッグ時は False にすると画面表示）
    HEADLESS = True
    # ブラウザの待機タイムアウト（ms）
    TIMEOUT = 15_000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=cls.HEADLESS)

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self._context = self._browser.new_context()
        self._context.set_default_timeout(self.TIMEOUT)

    def tearDown(self):
        self._context.close()
        super().tearDown()

    # ──────────────────────────────────────────────
    # ページ・URL ヘルパー
    # ──────────────────────────────────────────────

    def new_page(self):
        """新しいブラウザページを返す"""
        return self._context.new_page()

    def url(self, path):
        """テストサーバーの絶対 URL を返す"""
        return f"{self.live_server_url}{path}"

    # ──────────────────────────────────────────────
    # 認証ヘルパー
    # ──────────────────────────────────────────────

    def login(self, page, login_id="e2e_user@example.com", password="E2EPass123"):
        """ブラウザ経由でログインする"""
        page.goto(self.url("/accounts/login/"))
        page.fill('input[name="username"]', login_id)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{self.live_server_url}/calendar/**")

    def login_as_staff(self, page):
        """管理者としてログインする"""
        self.login(page, login_id="e2e_staff@example.com", password="E2EPass123")

    # ──────────────────────────────────────────────
    # テストデータ作成ヘルパー
    # ──────────────────────────────────────────────

    def create_user(self, login_id="e2e_user@example.com", name="E2Eユーザー",
                    password="E2EPass123", role="general", department=None):
        return User.objects.create_user(
            login_id=login_id, name=name, password=password,
            role=role, department=department,
        )

    def create_staff(self, login_id="e2e_staff@example.com", name="E2E管理者",
                     password="E2EPass123"):
        return User.objects.create_user(
            login_id=login_id, name=name, password=password, role="admin",
        )

    def create_room(self, name="テスト会議室", capacity=10):
        return Room.objects.create(name=name, capacity=capacity, is_active=True)

    def create_reservation(self, room, user, title="テスト会議",
                           start_hour=10, end_hour=11, day_offset=0):
        target = date.today()
        if day_offset:
            from datetime import timedelta
            target = target + timedelta(days=day_offset)
        start_at = timezone.make_aware(datetime.combine(target, time(start_hour, 0)))
        end_at   = timezone.make_aware(datetime.combine(target, time(end_hour, 0)))
        return Reservation.objects.create(
            room=room, user=user, reserved_by=user.name,
            title=title, start_at=start_at, end_at=end_at,
            is_cancelled=False,
        )

    # ──────────────────────────────────────────────
    # 待機ヘルパー
    # ──────────────────────────────────────────────

    def wait_for_calendar(self, page):
        """FullCalendar のグリッドが描画されるまで待機する"""
        page.wait_for_selector(".fc-view-harness", state="visible")

    def wait_for_toast(self, page):
        """トースト通知が表示されるまで待機する"""
        page.wait_for_selector(".toast.show", state="visible")
