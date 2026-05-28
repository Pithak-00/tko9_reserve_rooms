"""
F-10: 予約詳細表示 (ReservationDetailView) の単体テスト
対象ビュー : reservations.views.ReservationDetailView
URL name  : reservation_detail  ->  /reservations/<pk>/

仕様:
  - 予約情報（会議室・日時・件名・参加者名・備考・予約者名）を表示
  - ログイン必須
  - 存在しない ID -> 404
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF10ReservationDetail(TestCase):
    """F-10 予約詳細表示機能のテスト"""

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
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        now = timezone.now()
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="テスト会議",
            participants="参加者A、参加者B",
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
        )
        self.url = reverse("reservation_detail", kwargs={"pk": self.reservation.pk})
        self.client.login(username="test@example.com", password="TestPass123")

    # ------------------------------------------------------------------ 正常系

    def test_detail_returns_200(self):
        """正常系: 予約詳細ページにアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_detail_context_has_reservation(self):
        """正常系: コンテキストに reservation オブジェクトが含まれること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["reservation"], self.reservation)

    def test_detail_shows_title(self):
        """正常系: 予約の件名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "テスト会議")

    def test_detail_shows_room_name(self):
        """正常系: 会議室名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "会議室A")

    def test_detail_shows_reserved_by(self):
        """正常系: 予約者名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "テストユーザー")

    def test_detail_shows_edit_link(self):
        """正常系: 編集ボタン（リンク）がページに存在すること"""
        response = self.client.get(self.url)
        edit_url = reverse("reservation_edit", kwargs={"pk": self.reservation.pk})
        self.assertContains(response, edit_url)

    def test_detail_shows_cancel_form(self):
        """正常系: キャンセルフォームがページに存在すること"""
        response = self.client.get(self.url)
        cancel_url = reverse("reservation_cancel", kwargs={"pk": self.reservation.pk})
        self.assertContains(response, cancel_url)

    def test_other_user_can_view_detail(self):
        """正常系: 他のユーザーも詳細ページにアクセスできること（閲覧は誰でも可）"""
        self.client.login(username="other@example.com", password="TestPass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------ 異常系

    def test_nonexistent_id_returns_404(self):
        """異常系: 存在しない ID にアクセス -> 404 が返ること"""
        url = reverse("reservation_detail", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next={}".format(self.url),
        )

    # ------------------------------------------------------------------ 追加テスト

    def test_cancelled_reservation_is_accessible(self):
        """正常系: キャンセル済み予約の詳細ページも 200 OK で表示されること"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_cancelled_reservation_shows_cancelled_badge(self):
        """正常系: キャンセル済み予約の詳細には「キャンセル済み」バッジが表示されること
        （キャンセル確認モーダルは DOM に存在するが actions エリアにキャンセルボタンはなくバッジになる）"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        response = self.client.get(self.url)
        self.assertContains(response, "キャンセル済み")

    def test_detail_shows_participants(self):
        """正常系: 参加者名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "参加者A")
