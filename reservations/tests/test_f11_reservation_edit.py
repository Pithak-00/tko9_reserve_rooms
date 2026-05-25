"""
F-11: 予約編集 (ReservationUpdateView) の単体テスト
対象ビュー : reservations.views.ReservationUpdateView
URL name  : reservation_edit  ->  /reservations/<pk>/edit/

仕様:
  - 予約者本人または管理者が編集可
  - 会議室は変更不可（disabled フィールド）
  - 保存後は詳細画面へリダイレクト
  - 重複チェックを実行（自分自身を除外）
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


def _tomorrow_str():
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


class TestF11ReservationEdit(TestCase):
    """F-11 予約編集機能のテスト"""

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
        start = now + timedelta(days=1)
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="元のタイトル",
            start_at=start,
            end_at=start + timedelta(hours=1),
        )
        self.url = reverse("reservation_edit", kwargs={"pk": self.reservation.pk})
        self.client.login(username="test@example.com", password="TestPass123")

    def _valid_post(self, **overrides):
        data = {
            "room": self.room.id,
            "title": "更新後タイトル",
            "participants": "",
            "notes": "",
            "reserve_date": _tomorrow_str(),
            "start_time": "10:00",
            "end_time": "11:00",
        }
        data.update(overrides)
        return data

    # ------------------------------------------------------------------ 正常系

    def test_edit_get_returns_200(self):
        """正常系: 編集ページにアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_success_updates_title(self):
        """正常系: 件名を変更して保存 -> 件名が更新されること"""
        self.client.post(self.url, self._valid_post(title="更新後タイトル"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.title, "更新後タイトル")

    def test_edit_success_redirects_to_detail(self):
        """正常系: 保存成功 -> 予約詳細画面へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(
            response,
            reverse("reservation_detail", kwargs={"pk": self.reservation.pk}),
        )

    def test_edit_room_field_is_disabled(self):
        """正常系: 会議室フィールドが disabled になっていること（変更不可）"""
        response = self.client.get(self.url)
        self.assertTrue(response.context["form"].fields["room"].disabled)

    def test_edit_success_updates_times(self):
        """正常系: 日時を変更して保存 -> 開始・終了時刻が更新されること"""
        self.client.post(
            self.url,
            self._valid_post(
                reserve_date=_tomorrow_str(),
                start_time="14:00",
                end_time="15:00",
            ),
        )
        self.reservation.refresh_from_db()
        local_start = timezone.localtime(self.reservation.start_at)
        local_end = timezone.localtime(self.reservation.end_at)
        self.assertEqual(local_start.strftime("%H:%M"), "14:00")
        self.assertEqual(local_end.strftime("%H:%M"), "15:00")

    # ------------------------------------------------------------------ 異常系

    def test_edit_end_before_start_shows_error(self):
        """異常系: 終了時刻 < 開始時刻 -> バリデーションエラーになること"""
        response = self.client.post(
            self.url,
            self._valid_post(start_time="11:00", end_time="10:00"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_edit_nonexistent_id_returns_404(self):
        """異常系: 存在しない ID で編集 -> 404 が返ること"""
        url = reverse("reservation_edit", kwargs={"pk": 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next={}".format(self.url),
        )

    # ------------------------------------------------------------------ 管理者権限

    def test_other_user_cannot_edit(self):
        """異常系: 一般ユーザーは他人の予約を編集できず 403 が返ること"""
        self.client.login(username="other@example.com", password="TestPass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_others_reservation_get(self):
        """正常系: 管理者は他ユーザーの予約編集ページにアクセスできること"""
        self.client.login(username="admin@example.com", password="TestPass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_others_reservation_post(self):
        """正常系: 管理者は他ユーザーの予約を更新できること"""
        self.client.login(username="admin@example.com", password="TestPass123")
        self.client.post(self.url, self._valid_post(title="管理者による更新"))
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.title, "管理者による更新")

    def test_admin_edit_redirects_to_detail(self):
        """正常系: 管理者による更新後 -> 予約詳細画面へリダイレクトされること"""
        self.client.login(username="admin@example.com", password="TestPass123")
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(
            response,
            reverse("reservation_detail", kwargs={"pk": self.reservation.pk}),
        )
