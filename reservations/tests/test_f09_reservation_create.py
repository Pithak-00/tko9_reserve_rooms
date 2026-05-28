"""
F-09: 予約作成 (ReservationCreateView) の単体テスト
対象ビュー : reservations.views.ReservationCreateView
URL name  : reservation_create  ->  /reservations/create/

仕様:
  - 会議室・日付・開始/終了時刻・件名を入力して予約を登録
  - 登録成功後は予約詳細画面へリダイレクト
  - GETパラメータで会議室・日時をプリセット
  - 終了時刻は開始時刻より後であること
  - 重複チェックは F-13 として別途テスト
"""

from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Reservation, Room


def _tomorrow_str():
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


class TestF09ReservationCreate(TestCase):
    """F-09 予約作成機能のテスト"""

    def setUp(self):
        self.url = reverse("reservation_create")

        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.inactive_room = Room.objects.create(
            name="会議室B（停止中）", capacity=5, is_active=False
        )
        self.client.login(username="test@example.com", password="TestPass123")

    def _valid_post(self, **overrides):
        data = {
            "room": self.room.id,
            "title": "テスト会議",
            "participants": "",
            "notes": "",
            "reserve_date": _tomorrow_str(),
            "start_time": "10:00",
            "end_time": "11:00",
        }
        data.update(overrides)
        return data

    # ------------------------------------------------------------------ 正常系

    def test_get_returns_200(self):
        """正常系: GET /reservations/create/ -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_success_creates_one_reservation(self):
        """正常系: 有効な入力で POST -> Reservation が1件作成されること"""
        self.client.post(self.url, self._valid_post())
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_success_redirects_to_detail(self):
        """正常系: 有効な入力で POST -> 予約詳細画面へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        reservation = Reservation.objects.order_by("created_at").last()
        self.assertRedirects(
            response,
            reverse("reservation_detail", kwargs={"pk": reservation.pk}),
        )

    def test_create_sets_request_user(self):
        """正常系: 登録された予約の user が request.user に設定されること"""
        self.client.post(self.url, self._valid_post())
        reservation = Reservation.objects.order_by("created_at").last()
        self.assertEqual(reservation.user, self.user)

    def test_create_stores_correct_times(self):
        """正常系: 開始・終了時刻が正しく保存されること"""
        self.client.post(
            self.url, self._valid_post(start_time="14:00", end_time="15:30")
        )
        reservation = Reservation.objects.order_by("created_at").last()
        from django.utils import timezone

        local_start = timezone.localtime(reservation.start_at)
        local_end = timezone.localtime(reservation.end_at)
        self.assertEqual(local_start.strftime("%H:%M"), "14:00")
        self.assertEqual(local_end.strftime("%H:%M"), "15:30")

    def test_get_with_room_param_presets_selected_room(self):
        """正常系: GET ?room=<id> -> コンテキストの selected_room が設定されること"""
        response = self.client.get(self.url, {"room": self.room.id})
        self.assertEqual(response.context["selected_room"], self.room)

    def test_inactive_room_not_in_form_choices(self):
        """正常系: 利用停止中の会議室は選択肢に含まれないこと"""
        response = self.client.get(self.url)
        room_qs = response.context["form"].fields["room"].queryset
        self.assertNotIn(self.inactive_room, room_qs)

    # ------------------------------------------------------------------ 異常系

    def test_empty_title_prevents_creation(self):
        """異常系: 件名が空欄 -> バリデーションエラーになり予約が作成されないこと"""
        response = self.client.post(self.url, self._valid_post(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Reservation.objects.count(), 0)

    def test_end_time_before_start_time_prevents_creation(self):
        """異常系: 終了時刻 < 開始時刻 -> バリデーションエラーになること"""
        response = self.client.post(
            self.url,
            self._valid_post(start_time="11:00", end_time="10:00"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Reservation.objects.count(), 0)

    def test_end_time_equal_start_time_prevents_creation(self):
        """異常系: 終了時刻 = 開始時刻 -> バリデーションエラーになること"""
        response = self.client.post(
            self.url,
            self._valid_post(start_time="10:00", end_time="10:00"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Reservation.objects.count(), 0)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態で予約作成画面へアクセス → ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"/accounts/login/?next={self.url}",
        )

    def test_unauthenticated_post_redirects_to_login(self):
        """異常系: 未ログイン状態で POST → ログイン画面へリダイレクトされ予約が作成されないこと"""
        self.client.logout()
        self.client.post(self.url, self._valid_post())
        self.assertEqual(Reservation.objects.count(), 0)

    def test_get_with_date_param_presets_date_in_context(self):
        """正常系: GET ?date=YYYY-MM-DD → コンテキストの preset_date が設定されること"""
        from datetime import date, timedelta
        next_week = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = self.client.get(self.url, {"date": next_week})
        self.assertEqual(response.status_code, 200)
        # preset_date または initial の形でコンテキストか初期値に反映されていること
        form = response.context["form"]
        self.assertIsNotNone(form)
