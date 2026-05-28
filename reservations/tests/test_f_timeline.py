"""
タイムライン画面 (ReservationTimelineView) の単体テスト
対象ビュー : reservations.views.ReservationTimelineView
URL name  : reservation_timeline  →  /reservations/timeline/

仕様:
  - ログイン必須
  - ?date=YYYY-MM-DD で指定日のタイムラインを表示
  - date 省略・不正値は当日へフォールバック
  - is_active=True の会議室のみ表示（room_data）
  - キャンセル済み予約は表示しない
  - 指定日以外の予約は表示しない
  - コンテキスト: target / today / room_data / hours / hour_width / total_minutes / total_width
  - hours は HOUR_START〜HOUR_END-1 のリスト（デフォルト 8〜21）
  - 予約の left_px / width_px がタイムライン座標として計算されていること
"""

from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


def _make_aware(d, t):
    return timezone.make_aware(datetime.combine(d, t))


class TestReservationTimeline(TestCase):
    """タイムライン画面の基本テスト"""

    def setUp(self):
        self.url = reverse("reservation_timeline")
        self.login_url = "/accounts/login/"
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)

        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.active_room = Room.objects.create(
            name="会議室A", capacity=10, is_active=True
        )
        self.inactive_room = Room.objects.create(
            name="会議室B（停止中）", capacity=5, is_active=False
        )

        # 当日 10:00〜11:00 の予約
        self.reservation = Reservation.objects.create(
            room=self.active_room,
            user=self.user,
            reserved_by="テストユーザー",
            title="タイムラインテスト会議",
            start_at=_make_aware(self.today, time(10, 0)),
            end_at=_make_aware(self.today, time(11, 0)),
            is_cancelled=False,
        )

        self.client.login(username="test@example.com", password="TestPass123")

    # ──────────────────────────────────────────────
    # 正常系: アクセス・基本表示
    # ──────────────────────────────────────────────

    def test_timeline_returns_200(self):
        """正常系: /reservations/timeline/ にアクセス → 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_timeline_default_is_today(self):
        """正常系: date パラメータなし → target が当日になること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["target"], self.today)

    def test_timeline_with_date_param(self):
        """正常系: ?date=YYYY-MM-DD → target が指定日になること"""
        response = self.client.get(self.url, {"date": self.tomorrow.isoformat()})
        self.assertEqual(response.context["target"], self.tomorrow)

    def test_timeline_invalid_date_falls_back_to_today(self):
        """正常系: 不正な date パラメータ → 当日へフォールバックすること"""
        response = self.client.get(self.url, {"date": "not-a-date"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["target"], self.today)

    # ──────────────────────────────────────────────
    # 正常系: コンテキスト構造
    # ──────────────────────────────────────────────

    def test_context_has_required_keys(self):
        """正常系: コンテキストに必須キーが含まれること"""
        response = self.client.get(self.url)
        for key in ("target", "today", "room_data", "hours", "hour_width",
                    "total_minutes", "total_width", "prev_date", "next_date"):
            self.assertIn(key, response.context, msg=f"context key '{key}' missing")

    def test_hours_list_starts_at_8(self):
        """正常系: hours リストが 8 始まりであること（HOUR_START=8）"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["hours"][0], 8)

    def test_hours_list_ends_at_21(self):
        """正常系: hours リストが 21 終わりであること（HOUR_END=22 なので range で 21 まで）"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["hours"][-1], 21)

    def test_hour_width_is_80(self):
        """正常系: hour_width が 80px であること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["hour_width"], 80)

    def test_total_minutes_is_840(self):
        """正常系: total_minutes が 840（14時間×60分）であること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_minutes"], 840)

    def test_total_width_is_1120(self):
        """正常系: total_width が 1120px（14時間×80px）であること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_width"], 1120)

    def test_today_context_is_today(self):
        """正常系: today コンテキストが date.today() と等しいこと"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["today"], date.today())

    def test_prev_date_is_day_before_target(self):
        """正常系: prev_date が target の前日であること"""
        response = self.client.get(self.url, {"date": self.tomorrow.isoformat()})
        self.assertEqual(response.context["prev_date"], self.today)

    def test_next_date_is_day_after_target(self):
        """正常系: next_date が target の翌日であること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["next_date"], self.today + timedelta(days=1))

    # ──────────────────────────────────────────────
    # 正常系: room_data の内容
    # ──────────────────────────────────────────────

    def test_only_active_rooms_in_room_data(self):
        """正常系: room_data には is_active=True の会議室のみ含まれること"""
        response = self.client.get(self.url)
        room_names = [rd["room"].name for rd in response.context["room_data"]]
        self.assertIn("会議室A", room_names)
        self.assertNotIn("会議室B（停止中）", room_names)

    def test_reservation_appears_in_room_data(self):
        """正常系: 当日の予約が room_data 内の対応会議室に含まれること"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res_ids = [r["id"] for r in room_a_data["reservations"]]
        self.assertIn(self.reservation.pk, res_ids)

    def test_reservation_has_correct_start_str(self):
        """正常系: 予約の start_str が '10:00' であること"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next(r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk)
        self.assertEqual(res["start_str"], "10:00")

    def test_reservation_has_correct_end_str(self):
        """正常系: 予約の end_str が '11:00' であること"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next(r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk)
        self.assertEqual(res["end_str"], "11:00")

    def test_reservation_left_px_is_correct(self):
        """正常系: 10:00 開始の予約の left_px が 160px であること（(10-8)×60×80/60=160）"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next(r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk)
        self.assertEqual(res["left_px"], 160)

    def test_reservation_width_px_is_correct(self):
        """正常系: 1時間の予約の width_px が 80px であること（60分×80/60=80）"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next(r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk)
        self.assertEqual(res["width_px"], 80)

    def test_owner_can_edit_own_reservation(self):
        """正常系: 予約者自身の予約は can_edit=True であること"""
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next(r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk)
        self.assertTrue(res["can_edit"])

    def test_other_user_cannot_edit_reservation(self):
        """正常系: 他ユーザーがログイン中 → can_edit=False になること"""
        other = User.objects.create_user(
            login_id="other@example.com", name="他ユーザー", password="TestPass123"
        )
        self.client.login(username="other@example.com", password="TestPass123")
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next((r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk), None)
        self.assertIsNotNone(res)
        self.assertFalse(res["can_edit"])

    # ──────────────────────────────────────────────
    # 正常系: 日付フィルター
    # ──────────────────────────────────────────────

    def test_other_day_reservation_not_in_room_data(self):
        """正常系: 指定日以外の予約は room_data に含まれないこと"""
        # 翌日の予約を作成
        other_day_rsv = Reservation.objects.create(
            room=self.active_room,
            user=self.user,
            reserved_by="テストユーザー",
            title="翌日の会議",
            start_at=_make_aware(self.tomorrow, time(10, 0)),
            end_at=_make_aware(self.tomorrow, time(11, 0)),
            is_cancelled=False,
        )
        # 当日で検索
        response = self.client.get(self.url, {"date": self.today.isoformat()})
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res_ids = [r["id"] for r in room_a_data["reservations"]]
        self.assertNotIn(other_day_rsv.pk, res_ids)

    def test_cancelled_reservation_not_in_room_data(self):
        """正常系: キャンセル済み予約は room_data に含まれないこと"""
        cancelled_rsv = Reservation.objects.create(
            room=self.active_room,
            user=self.user,
            reserved_by="テストユーザー",
            title="キャンセル済み会議",
            start_at=_make_aware(self.today, time(14, 0)),
            end_at=_make_aware(self.today, time(15, 0)),
            is_cancelled=True,
        )
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res_ids = [r["id"] for r in room_a_data["reservations"]]
        self.assertNotIn(cancelled_rsv.pk, res_ids)

    # ──────────────────────────────────────────────
    # 正常系: 終日予約
    # ──────────────────────────────────────────────

    def test_all_day_reservation_has_is_all_day_true(self):
        """正常系: 終日予約は is_all_day=True・start_str='終日' で含まれること"""
        all_day_rsv = Reservation.objects.create(
            room=self.active_room,
            user=self.user,
            reserved_by="テストユーザー",
            title="終日会議",
            start_at=_make_aware(self.today, time(0, 0)),
            end_at=_make_aware(self.today, time(0, 30)),
            is_all_day=True,
            is_cancelled=False,
        )
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        all_day_entry = next(
            (r for r in room_a_data["reservations"] if r["id"] == all_day_rsv.pk), None
        )
        self.assertIsNotNone(all_day_entry)
        self.assertTrue(all_day_entry["is_all_day"])
        self.assertEqual(all_day_entry["start_str"], "終日")

    # ──────────────────────────────────────────────
    # 正常系: 管理者
    # ──────────────────────────────────────────────

    def test_admin_can_edit_all_reservations(self):
        """正常系: 管理者は他ユーザーの予約も can_edit=True であること"""
        admin = User.objects.create_user(
            login_id="admin@example.com", name="管理者", password="AdminPass123",
            role="admin",
        )
        self.client.login(username="admin@example.com", password="AdminPass123")
        response = self.client.get(self.url)
        room_data = response.context["room_data"]
        room_a_data = next(rd for rd in room_data if rd["room"] == self.active_room)
        res = next((r for r in room_a_data["reservations"] if r["id"] == self.reservation.pk), None)
        self.assertIsNotNone(res)
        self.assertTrue(res["can_edit"])

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス → ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"{self.login_url}?next={self.url}",
        )
