"""
F-22: 設備管理 CRUD（FacilityXxxView）の単体テスト
対象ビュー : admin_panel.views.FacilityListView / CreateView / UpdateView / DeleteView
URL names : facility_list / facility_create / facility_edit / facility_delete
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Facility, Room, RoomFacility


class TestF22FacilityAdmin(TestCase):
    """F-22 設備管理 CRUD のテスト"""

    def setUp(self):
        self.staff = User.objects.create_user(
            login_id="staff@example.com", name="管理者", password="Pass123", role="admin",
        )
        self.general = User.objects.create_user(
            login_id="user@example.com", name="一般ユーザー", password="Pass123",
        )
        self.facility = Facility.objects.create(name="プロジェクター")
        self.list_url   = reverse("facility_list")
        self.create_url = reverse("facility_create")

        self.client.login(username="staff@example.com", password="Pass123")

    # ──────────────────────────────────────────────
    # 一覧
    # ──────────────────────────────────────────────

    def test_list_returns_200(self):
        """正常系: 一覧画面が 200 で返ること"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_list_shows_facility_name(self):
        """正常系: 一覧に設備名が表示されること"""
        response = self.client.get(self.list_url)
        self.assertContains(response, "プロジェクター")

    def test_list_search_filters_by_name(self):
        """正常系: 名前検索で絞り込まれること"""
        Facility.objects.create(name="ホワイトボード")
        response = self.client.get(self.list_url, {"q": "プロジェクター"})
        self.assertContains(response, "プロジェクター")
        self.assertNotContains(response, "ホワイトボード")

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
        """正常系: 設備作成成功 → 一覧にリダイレクトされること"""
        response = self.client.post(self.create_url, {"name": "テレビ会議システム"})
        self.assertRedirects(response, self.list_url)

    def test_create_success_saves_facility(self):
        """正常系: 設備が DB に保存されること"""
        self.client.post(self.create_url, {"name": "テレビ会議システム"})
        self.assertTrue(Facility.objects.filter(name="テレビ会議システム").exists())

    def test_create_empty_name_shows_error(self):
        """異常系: 名前が空 → バリデーションエラーが返ること（200 + エラー表示）"""
        response = self.client.post(self.create_url, {"name": ""})
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_name_shows_error(self):
        """異常系: 既存の名前と重複 → バリデーションエラーが返ること"""
        response = self.client.post(self.create_url, {"name": "プロジェクター"})
        self.assertEqual(response.status_code, 200)

    def test_create_get_method_not_allowed(self):
        """異常系: GET リクエストは 405 が返ること"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 405)

    def test_create_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.create_url, {"name": "新設備"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 編集
    # ──────────────────────────────────────────────

    def test_edit_success_redirects_to_list(self):
        """正常系: 設備更新成功 → 一覧にリダイレクトされること"""
        url = reverse("facility_edit", kwargs={"pk": self.facility.pk})
        response = self.client.post(url, {"name": "プロジェクター（更新）"})
        self.assertRedirects(response, self.list_url)

    def test_edit_success_updates_name(self):
        """正常系: 名前が DB に更新されること"""
        url = reverse("facility_edit", kwargs={"pk": self.facility.pk})
        self.client.post(url, {"name": "プロジェクター（更新）"})
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.name, "プロジェクター（更新）")

    def test_edit_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("facility_edit", kwargs={"pk": 9999})
        response = self.client.post(url, {"name": "名前"})
        self.assertEqual(response.status_code, 404)

    def test_edit_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("facility_edit", kwargs={"pk": self.facility.pk})
        response = self.client.post(url, {"name": "変更"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 削除
    # ──────────────────────────────────────────────

    def test_delete_success_redirects_to_list(self):
        """正常系: 設備削除成功 → 一覧にリダイレクトされること"""
        url = reverse("facility_delete", kwargs={"pk": self.facility.pk})
        response = self.client.post(url)
        self.assertRedirects(response, self.list_url)

    def test_delete_removes_facility(self):
        """正常系: 設備が DB から削除されること"""
        url = reverse("facility_delete", kwargs={"pk": self.facility.pk})
        self.client.post(url)
        self.assertFalse(Facility.objects.filter(pk=self.facility.pk).exists())

    def test_delete_cascades_room_facility(self):
        """正常系: 設備削除時に RoomFacility も CASCADE 削除されること"""
        room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        rf = RoomFacility.objects.create(room=room, facility=self.facility)
        url = reverse("facility_delete", kwargs={"pk": self.facility.pk})
        self.client.post(url)
        self.assertFalse(RoomFacility.objects.filter(pk=rf.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("facility_delete", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("facility_delete", kwargs={"pk": self.facility.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
