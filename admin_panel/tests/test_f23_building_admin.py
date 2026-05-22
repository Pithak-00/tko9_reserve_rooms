"""
F-23: 建物管理 CRUD（BuildingXxxView）の単体テスト
対象ビュー : admin_panel.views.BuildingListView / CreateView / UpdateView / DeleteView
URL names : building_list / building_create / building_edit / building_delete
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Building, Room


class TestF23BuildingAdmin(TestCase):
    """F-23 建物管理 CRUD のテスト"""

    def setUp(self):
        self.staff = User.objects.create_user(
            login_id="staff@example.com", name="管理者", password="Pass123", role="admin",
        )
        self.general = User.objects.create_user(
            login_id="user@example.com", name="一般ユーザー", password="Pass123",
        )
        self.building = Building.objects.create(name="本館")
        self.list_url   = reverse("building_list")
        self.create_url = reverse("building_create")

        self.client.login(username="staff@example.com", password="Pass123")

    # ──────────────────────────────────────────────
    # 一覧
    # ──────────────────────────────────────────────

    def test_list_returns_200(self):
        """正常系: 一覧画面が 200 で返ること"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_list_shows_building_name(self):
        """正常系: 一覧に建物名が表示されること"""
        response = self.client.get(self.list_url)
        self.assertContains(response, "本館")

    def test_list_search_filters_by_name(self):
        """正常系: 名前検索で絞り込まれること"""
        Building.objects.create(name="別館")
        response = self.client.get(self.list_url, {"q": "本館"})
        self.assertContains(response, "本館")
        self.assertNotContains(response, "別館")

    def test_list_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

    def test_list_unauthenticated_redirects(self):
        """異常系: 未ログインはリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)

    # ──────────────────────────────────────────────
    # 作成
    # ──────────────────────────────────────────────

    def test_create_success_redirects_to_list(self):
        """正常系: 建物作成成功 → 一覧にリダイレクトされること"""
        response = self.client.post(self.create_url, {"name": "新棟"})
        self.assertRedirects(response, self.list_url)

    def test_create_success_saves_building(self):
        """正常系: 建物が DB に保存されること"""
        self.client.post(self.create_url, {"name": "新棟"})
        self.assertTrue(Building.objects.filter(name="新棟").exists())

    def test_create_empty_name_shows_error(self):
        """異常系: 名前が空 → バリデーションエラー（200 + エラー表示）"""
        response = self.client.post(self.create_url, {"name": ""})
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_name_shows_error(self):
        """異常系: 既存の名前と重複 → バリデーションエラー"""
        response = self.client.post(self.create_url, {"name": "本館"})
        self.assertEqual(response.status_code, 200)

    def test_create_get_method_not_allowed(self):
        """異常系: GET リクエストは 405 が返ること"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 405)

    def test_create_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.create_url, {"name": "新棟"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 編集
    # ──────────────────────────────────────────────

    def test_edit_success_redirects_to_list(self):
        """正常系: 建物更新成功 → 一覧にリダイレクトされること"""
        url = reverse("building_edit", kwargs={"pk": self.building.pk})
        response = self.client.post(url, {"name": "本館（改）"})
        self.assertRedirects(response, self.list_url)

    def test_edit_success_updates_name(self):
        """正常系: 名前が DB に更新されること"""
        url = reverse("building_edit", kwargs={"pk": self.building.pk})
        self.client.post(url, {"name": "本館（改）"})
        self.building.refresh_from_db()
        self.assertEqual(self.building.name, "本館（改）")

    def test_edit_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("building_edit", kwargs={"pk": 9999})
        response = self.client.post(url, {"name": "名前"})
        self.assertEqual(response.status_code, 404)

    def test_edit_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("building_edit", kwargs={"pk": self.building.pk})
        response = self.client.post(url, {"name": "変更"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 削除
    # ──────────────────────────────────────────────

    def test_delete_success_redirects_to_list(self):
        """正常系: 建物削除成功 → 一覧にリダイレクトされること"""
        url = reverse("building_delete", kwargs={"pk": self.building.pk})
        response = self.client.post(url)
        self.assertRedirects(response, self.list_url)

    def test_delete_removes_building(self):
        """正常系: 建物が DB から削除されること"""
        url = reverse("building_delete", kwargs={"pk": self.building.pk})
        self.client.post(url)
        self.assertFalse(Building.objects.filter(pk=self.building.pk).exists())

    def test_delete_sets_room_building_null(self):
        """正常系: 建物削除時に紐づく会議室の building が NULL になること"""
        room = Room.objects.create(
            name="会議室A", capacity=10, is_active=True, building=self.building,
        )
        url = reverse("building_delete", kwargs={"pk": self.building.pk})
        self.client.post(url)
        room.refresh_from_db()
        self.assertIsNone(room.building)

    def test_delete_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("building_delete", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("building_delete", kwargs={"pk": self.building.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
