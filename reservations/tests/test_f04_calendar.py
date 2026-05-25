"""
F-04: 日次カレンダー表示 (CalendarView) の単体テスト
対象ビュー : reservations.views.CalendarView
URL name  : calendar  →  /calendar/
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from reservations.models import DepartmentRoom, Room


class TestF04CalendarView(TestCase):
    """F-04 日次カレンダー表示機能のテスト"""

    def setUp(self):
        self.url = reverse("calendar")
        self.login_url = "/accounts/login/"

        # 所属・ユーザーを作成
        self.dept = Department.objects.create(name="開発部")
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
            department=self.dept,
        )

        # 会議室を2つ作成
        self.room1 = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.room2 = Room.objects.create(name="会議室B", capacity=5, is_active=True)

        # room1 だけを開発部に紐づけ
        DepartmentRoom.objects.create(department=self.dept, room=self.room1)

        self.client.login(username="test@example.com", password="TestPass123")

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_calendar_default_shows_today(self):
        """正常系: dateパラメータなしでアクセス → 当日の日付が表示されること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_date"], date.today().isoformat())

    def test_calendar_with_date_param(self):
        """正常系: ?date=YYYY-MM-DD → 指定日のカレンダーが表示されること"""
        response = self.client.get(self.url, {"date": "2026-05-01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_date"], "2026-05-01")

    def test_calendar_target_date_in_html(self):
        """正常系: target_date が FullCalendar の data-date 属性として HTML に含まれること"""
        response = self.client.get(self.url, {"date": "2026-05-10"})
        self.assertContains(response, 'data-date="2026-05-10"')

    def test_calendar_default_view_is_week(self):
        """正常系: デフォルトビューは週表示（timeGridWeek）であること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["fc_initial_view"], "timeGridWeek")

    def test_calendar_day_view_param(self):
        """正常系: ?view=day → fc_initial_view が timeGridDay になること"""
        response = self.client.get(self.url, {"view": "day"})
        self.assertEqual(response.context["fc_initial_view"], "timeGridDay")

    def test_calendar_month_view_param(self):
        """正常系: ?view=month → fc_initial_view が dayGridMonth になること"""
        response = self.client.get(self.url, {"view": "month"})
        self.assertEqual(response.context["fc_initial_view"], "dayGridMonth")

    def test_calendar_rooms_list_contains_all_active_rooms(self):
        """正常系: rooms_list には全アクティブ会議室が含まれること（フィルタはクライアント側JS処理）"""
        response = self.client.get(self.url)
        rooms = list(response.context["rooms_list"])
        self.assertIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)

    def test_calendar_user_without_department_shows_all_rooms(self):
        """正常系: 所属なしユーザーでも全アクティブ会議室が rooms_list に含まれること"""
        user_no_dept = User.objects.create_user(
            login_id="nodept@example.com",
            name="所属なしユーザー",
            password="TestPass123",
        )
        self.client.login(username="nodept@example.com", password="TestPass123")
        response = self.client.get(self.url)
        rooms = list(response.context["rooms_list"])
        self.assertIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)

    def test_calendar_inactive_room_excluded_from_all_filter(self):
        """正常系: is_active=False の会議室は ?filter=all でも rooms_list に含まれないこと"""
        inactive_room = Room.objects.create(
            name="会議室C（停止中）", capacity=8, is_active=False
        )
        response = self.client.get(self.url, {"filter": "all"})
        rooms = list(response.context["rooms_list"])
        self.assertNotIn(inactive_room, rooms)

    def test_calendar_rooms_json_in_context(self):
        """正常系: rooms_json がコンテキストに含まれ、会議室名が含まれること"""
        response = self.client.get(self.url, {"filter": "all"})
        rooms_json = response.context["rooms_json"]
        self.assertIn("会議室A", rooms_json)
        self.assertIn("会議室B", rooms_json)

    def test_calendar_departments_in_context(self):
        """正常系: フィルタードロップダウン用に departments_list がコンテキストに含まれること"""
        response = self.client.get(self.url)
        self.assertIn(self.dept, list(response.context["departments_list"]))

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_calendar_invalid_date_falls_back_to_today(self):
        """異常系: 不正な date パラメータ → 当日にフォールバックすること"""
        response = self.client.get(self.url, {"date": "invalid-date"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target_date"], date.today().isoformat())

    def test_calendar_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス → ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{self.login_url}?next={self.url}")
