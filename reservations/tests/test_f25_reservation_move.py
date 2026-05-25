"""
F-25: 予約ドラッグ&ドロップ移動（ReservationMoveView）の単体テスト
対象ビュー : reservations.views.ReservationMoveView
URL name  : reservation_move  →  PATCH /reservations/<pk>/move/
"""

import json
from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime

from accounts.models import User
from reservations.models import Reservation, Room


def make_aware_dt(d, t):
    return timezone.make_aware(datetime.combine(d, t))


class TestF25ReservationMove(TestCase):
    """F-25 予約ドラッグ&ドロップ移動のテスト"""

    def setUp(self):
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)

        self.user = User.objects.create_user(
            login_id="owner@example.com",
            name="オーナー",
            password="TestPass123",
        )
        self.other = User.objects.create_user(
            login_id="other@example.com",
            name="他ユーザー",
            password="TestPass123",
        )
        self.staff = User.objects.create_user(
            login_id="staff@example.com",
            name="管理者",
            password="TestPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.room2 = Room.objects.create(name="会議室B", capacity=5, is_active=True)

        # 当日 10:00〜11:00 の予約（オーナー所有）
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="オーナー",
            title="移動テスト会議",
            start_at=make_aware_dt(self.today, time(10, 0)),
            end_at=make_aware_dt(self.today, time(11, 0)),
            is_cancelled=False,
        )

        self.url = reverse("reservation_move", kwargs={"pk": self.reservation.pk})
        self.client.login(username="owner@example.com", password="TestPass123")

    def _patch(self, data):
        return self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type="application/json",
        )

    def _make_start_end(self, d, start_time, end_time):
        return (
            make_aware_dt(d, start_time).isoformat(),
            make_aware_dt(d, end_time).isoformat(),
        )

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_move_success_returns_200(self):
        """正常系: 移動成功 → 200 が返ること"""
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 200)

    def test_move_success_updates_start_end(self):
        """正常系: 移動後に start_at / end_at が更新されること"""
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        self._patch({"start_at": start, "end_at": end})
        self.reservation.refresh_from_db()
        self.assertEqual(localtime(self.reservation.start_at).hour, 14)
        self.assertEqual(localtime(self.reservation.end_at).hour, 15)

    def test_move_success_returns_id_and_color(self):
        """正常系: レスポンスに id と color が含まれること"""
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertIn("color", data)
        self.assertEqual(data["id"], self.reservation.pk)

    def test_move_to_different_room(self):
        """正常系: 別の会議室に移動できること"""
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        self._patch({"start_at": start, "end_at": end, "room_id": self.room2.pk})
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.room_id, self.room2.pk)

    def test_move_end_at_fallback_to_30min(self):
        """正常系: end_at 省略時は start_at の 30 分後になること"""
        start, _ = self._make_start_end(self.today, time(14, 0), time(15, 0))
        self._patch({"start_at": start})
        self.reservation.refresh_from_db()
        local_end = localtime(self.reservation.end_at)
        self.assertEqual(local_end.hour, 14)
        self.assertEqual(local_end.minute, 30)

    def test_move_to_all_day(self):
        """正常系: 終日スロットへのドロップ → is_all_day=True になること"""
        response = self._patch({"is_all_day": True, "date": self.tomorrow.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_all_day)

    def test_staff_can_move_others_reservation(self):
        """正常系: staff は他ユーザーの予約を移動できること"""
        self.client.login(username="staff@example.com", password="TestPass123")
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 200)

    # ──────────────────────────────────────────────
    # 異常系: 権限
    # ──────────────────────────────────────────────

    def test_other_user_cannot_move(self):
        """異常系: 他ユーザーの予約は移動できず 403 が返ること"""
        self.client.login(username="other@example.com", password="TestPass123")
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_returns_302(self):
        """異常系: 未ログインは 302 リダイレクトされること"""
        self.client.logout()
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_reservation_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("reservation_move", kwargs={"pk": 9999})
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self.client.patch(
            url,
            data=json.dumps({"start_at": start, "end_at": end}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    # ──────────────────────────────────────────────
    # 異常系: 重複チェック
    # ──────────────────────────────────────────────

    def test_move_conflict_with_other_reservation_returns_400(self):
        """異常系: 移動先に別の予約が重複 → 400 が返ること"""
        Reservation.objects.create(
            room=self.room,
            user=self.other,
            reserved_by="他ユーザー",
            title="既存会議",
            start_at=make_aware_dt(self.today, time(14, 0)),
            end_at=make_aware_dt(self.today, time(15, 0)),
            is_cancelled=False,
        )
        start, end = self._make_start_end(self.today, time(14, 0), time(15, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 400)

    def test_move_self_overlap_is_allowed(self):
        """正常系: 同じ時間帯への自己移動（同じ予約）は許可されること"""
        start, end = self._make_start_end(self.today, time(10, 0), time(11, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 200)

    def test_move_blocked_by_all_day_reservation(self):
        """異常系: 移動先の日に終日予約がある → 400 が返ること"""
        Reservation.objects.create(
            room=self.room,
            user=self.other,
            reserved_by="他ユーザー",
            title="終日会議",
            start_at=make_aware_dt(self.tomorrow, time(0, 0)),
            end_at=make_aware_dt(self.tomorrow, time(0, 30)),
            is_all_day=True,
            is_cancelled=False,
        )
        start, end = self._make_start_end(self.tomorrow, time(10, 0), time(11, 0))
        response = self._patch({"start_at": start, "end_at": end})
        self.assertEqual(response.status_code, 400)

    def test_move_to_all_day_blocked_by_existing_reservation(self):
        """異常系: 終日へ移動しようとする日に通常予約がある → 400 が返ること"""
        Reservation.objects.create(
            room=self.room,
            user=self.other,
            reserved_by="他ユーザー",
            title="通常会議",
            start_at=make_aware_dt(self.tomorrow, time(9, 0)),
            end_at=make_aware_dt(self.tomorrow, time(10, 0)),
            is_cancelled=False,
        )
        response = self._patch({"is_all_day": True, "date": self.tomorrow.isoformat()})
        self.assertEqual(response.status_code, 400)
