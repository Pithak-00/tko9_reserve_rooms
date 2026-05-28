"""
F-12: 予約キャンセル (reservation_cancel) の単体テスト
対象ビュー : reservations.views.reservation_cancel
URL name  : reservation_cancel  ->  /reservations/<pk>/cancel/

仕様:
  - POST のみ受付（@require_POST）
  - ログイン必須（@login_required）
  - 予約者本人または管理者がキャンセル可
  - キャンセル = is_cancelled=True に更新（論理削除）
  - 成功後はカレンダー画面へリダイレクト
  - 一般ユーザーが他人の予約をキャンセルしようとすると 403
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF12ReservationCancel(TestCase):
    """F-12 予約キャンセル機能のテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.other_user = User.objects.create_user(
            login_id="other@example.com",
            name="他のユーザー",
            password="TestPass123",
        )
        self.admin_user = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="TestPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        now = timezone.now()
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="テスト会議",
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
            is_cancelled=False,
        )
        self.url = reverse("reservation_cancel", kwargs={"pk": self.reservation.pk})
        self.client.login(username="test@example.com", password="TestPass123")

    # ------------------------------------------------------------------ 正常系

    def test_cancel_sets_is_cancelled_true(self):
        """正常系: 予約者本人がキャンセル -> is_cancelled=True になること"""
        self.client.post(self.url)
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_cancelled)

    def test_cancel_redirects_to_calendar(self):
        """正常系: キャンセル成功後 -> カレンダー画面へリダイレクトされること"""
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("calendar"))

    # ------------------------------------------------------------------ 異常系

    def test_cancel_by_non_owner_does_not_cancel(self):
        """異常系: 他のユーザーがキャンセルしようとしても is_cancelled が変化しないこと"""
        self.client.login(username="other@example.com", password="TestPass123")
        self.client.post(self.url)
        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.is_cancelled)

    def test_cancel_by_non_owner_returns_403(self):
        """異常系: 他のユーザーのキャンセル試行 -> 403 Forbidden が返ること"""
        self.client.login(username="other@example.com", password="TestPass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_method_not_allowed(self):
        """異常系: GET リクエスト -> 405 Method Not Allowed が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態で POST -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next={}".format(self.url),
        )

    def test_nonexistent_reservation_returns_404(self):
        """異常系: 存在しない ID にキャンセル POST -> 404 が返ること"""
        url = reverse("reservation_cancel", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    # ------------------------------------------------------------------ 管理者権限

    def test_admin_can_cancel_others_reservation(self):
        """正常系: 管理者は他ユーザーの予約をキャンセルできること"""
        self.client.login(username="admin@example.com", password="TestPass123")
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("calendar"))
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_cancelled)

    def test_admin_cancel_sets_is_cancelled_true(self):
        """正常系: 管理者によるキャンセル -> is_cancelled=True になること"""
        self.client.login(username="admin@example.com", password="TestPass123")
        self.client.post(self.url)
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_cancelled)

    # ------------------------------------------------------------------ 追加テスト

    def test_cancel_already_cancelled_reservation_keeps_state(self):
        """正常系: すでにキャンセル済みの予約を再度キャンセルしても is_cancelled=True のままであること"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        self.client.post(self.url)
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_cancelled)

    def test_cancel_count_does_not_increase_when_already_cancelled(self):
        """正常系: すでにキャンセル済みの予約を再度キャンセルしても Reservation 件数が変わらないこと"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        before = self.reservation.is_cancelled
        self.client.post(self.url)
        self.reservation.refresh_from_db()
        self.assertEqual(before, self.reservation.is_cancelled)
