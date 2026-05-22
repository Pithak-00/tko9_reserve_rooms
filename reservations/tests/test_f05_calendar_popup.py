"""
F-05: カレンダーの予約表示・ポップアップ の単体テスト

現在の実装では予約データは JavaScript（FullCalendar）が
CalendarEventsAPI（/calendar/events/）を呼び出して取得する。

本テストでは以下を検証する:
  1. CalendarEventsAPI が正しい予約データを返すこと
  2. キャンセル済み予約が API から返されないこと
  3. カレンダーページにポップアップ用 HTML 構造が含まれること
  4. カレンダーページに予約作成 URL が含まれること
"""

import json
from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF05CalendarPopup(TestCase):
    """F-05 カレンダー予約表示・ポップアップ機能のテスト"""

    def setUp(self):
        self.calendar_url = reverse("calendar")
        self.events_url = reverse("calendar_events")
        self.today = date.today()

        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)

        # 当日 10:00〜11:00 の予約
        start_at = timezone.make_aware(datetime.combine(self.today, time(10, 0)))
        end_at = timezone.make_aware(datetime.combine(self.today, time(11, 0)))
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="テスト会議",
            start_at=start_at,
            end_at=end_at,
            is_cancelled=False,
        )

        self.client.login(username="test@example.com", password="TestPass123")

        # CalendarEventsAPI に渡す start/end パラメータ（当日全体）
        self.start_param = timezone.make_aware(
            datetime.combine(self.today, time(0, 0))
        ).isoformat()
        self.end_param = timezone.make_aware(
            datetime.combine(self.today + timedelta(days=1), time(0, 0))
        ).isoformat()

    def _get_events(self, **extra_params):
        params = {"start": self.start_param, "end": self.end_param}
        params.update(extra_params)
        return self.client.get(self.events_url, params)

    # ──────────────────────────────────────────────
    # 正常系: CalendarEventsAPI
    # ──────────────────────────────────────────────

    def test_events_api_returns_200(self):
        """正常系: イベント API が 200 を返すこと"""
        response = self._get_events()
        self.assertEqual(response.status_code, 200)

    def test_events_api_returns_reservation(self):
        """正常系: 予約が JSON 配列として返されること"""
        response = self._get_events()
        events = json.loads(response.content)
        ids = [e["id"] for e in events]
        self.assertIn(self.reservation.id, ids)

    def test_events_api_reservation_has_title(self):
        """正常系: 返された予約に title（件名）が含まれること"""
        response = self._get_events()
        events = json.loads(response.content)
        event = next(e for e in events if e["id"] == self.reservation.id)
        self.assertEqual(event["title"], "テスト会議")

    def test_events_api_reservation_has_reserved_by(self):
        """正常系: 返された予約に reserved_by（予約者名）が含まれること"""
        response = self._get_events()
        events = json.loads(response.content)
        event = next(e for e in events if e["id"] == self.reservation.id)
        self.assertEqual(event["reserved_by"], "テストユーザー")

    def test_events_api_reservation_has_start_and_end(self):
        """正常系: 返された予約に start / end（時刻）が含まれること"""
        response = self._get_events()
        events = json.loads(response.content)
        event = next(e for e in events if e["id"] == self.reservation.id)
        self.assertIn("start", event)
        self.assertIn("end", event)
        self.assertIn("10:00", event["start"])
        self.assertIn("11:00", event["end"])

    # ──────────────────────────────────────────────
    # 異常系: CalendarEventsAPI
    # ──────────────────────────────────────────────

    def test_cancelled_reservation_not_returned_by_api(self):
        """異常系: キャンセル済み予約は API から返されないこと"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        response = self._get_events()
        events = json.loads(response.content)
        ids = [e["id"] for e in events]
        self.assertNotIn(self.reservation.id, ids)

    def test_events_api_invalid_params_returns_400(self):
        """異常系: start/end パラメータ不正 → 400 が返ること"""
        response = self.client.get(self.events_url, {"start": "invalid", "end": "invalid"})
        self.assertEqual(response.status_code, 400)

    # ──────────────────────────────────────────────
    # 正常系: カレンダーページ HTML 構造
    # ──────────────────────────────────────────────

    def test_calendar_page_has_popover_structure(self):
        """正常系: カレンダーページにポップアップ用 HTML 構造が含まれること"""
        response = self.client.get(self.calendar_url)
        self.assertContains(response, "reservation-popover")

    def test_calendar_page_has_detail_link(self):
        """正常系: カレンダーページにポップアップの「詳細を見る」リンク要素が含まれること"""
        response = self.client.get(self.calendar_url)
        self.assertContains(response, "btn-detail")
        self.assertContains(response, "詳細を見る")

    def test_calendar_page_has_reservation_create_url(self):
        """正常系: カレンダーページに予約作成画面への URL が含まれること"""
        response = self.client.get(self.calendar_url)
        self.assertContains(response, "/reservations/create/")
