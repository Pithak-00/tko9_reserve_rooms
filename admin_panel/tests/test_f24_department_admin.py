"""
F-24: 所属管理 CRUD（DepartmentXxxView）の単体テスト
対象ビュー : admin_panel.views.DepartmentListView / CreateView / UpdateView / DeleteView
URL names : department_list / department_create / department_edit / department_delete
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from reservations.models import DepartmentRoom, Room


class TestF24DepartmentAdmin(TestCase):
    """F-24 所属管理 CRUD のテスト"""

    def setUp(self):
        self.staff = User.objects.create_user(
            login_id="staff@example.com", name="管理者", password="Pass123", role="admin",
        )
        self.general = User.objects.create_user(
            login_id="user@example.com", name="一般ユーザー", password="Pass123",
        )
        self.dept = Department.objects.create(name="開発部")
        self.list_url   = reverse("department_list")
        self.create_url = reverse("department_create")

        self.client.login(username="staff@example.com", password="Pass123")

    # ──────────────────────────────────────────────
    # 一覧
    # ──────────────────────────────────────────────

    def test_list_returns_200(self):
        """正常系: 一覧画面が 200 で返ること"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_list_shows_department_name(self):
        """正常系: 一覧に所属名が表示されること"""
        response = self.client.get(self.list_url)
        self.assertContains(response, "開発部")

    def test_list_search_filters_by_name(self):
        """正常系: 名前検索で絞り込まれること"""
        Department.objects.create(name="営業部")
        response = self.client.get(self.list_url, {"q": "開発部"})
        self.assertContains(response, "開発部")
        self.assertNotContains(response, "営業部")

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
        """正常系: 所属作成成功 → 一覧にリダイレクトされること"""
        response = self.client.post(self.create_url, {"name": "総務部"})
        self.assertRedirects(response, self.list_url)

    def test_create_success_saves_department(self):
        """正常系: 所属が DB に保存されること"""
        self.client.post(self.create_url, {"name": "総務部"})
        self.assertTrue(Department.objects.filter(name="総務部").exists())

    def test_create_empty_name_shows_error(self):
        """異常系: 名前が空 → バリデーションエラー（200 + エラー表示）"""
        response = self.client.post(self.create_url, {"name": ""})
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_name_shows_error(self):
        """異常系: 既存の名前と重複 → バリデーションエラー"""
        response = self.client.post(self.create_url, {"name": "開発部"})
        self.assertEqual(response.status_code, 200)

    def test_create_get_method_not_allowed(self):
        """異常系: GET リクエストは 405 が返ること"""
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 405)

    def test_create_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.create_url, {"name": "新部署"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 編集
    # ──────────────────────────────────────────────

    def test_edit_success_redirects_to_list(self):
        """正常系: 所属更新成功 → 一覧にリダイレクトされること"""
        url = reverse("department_edit", kwargs={"pk": self.dept.pk})
        response = self.client.post(url, {"name": "開発部（改）"})
        self.assertRedirects(response, self.list_url)

    def test_edit_success_updates_name(self):
        """正常系: 名前が DB に更新されること"""
        url = reverse("department_edit", kwargs={"pk": self.dept.pk})
        self.client.post(url, {"name": "開発部（改）"})
        self.dept.refresh_from_db()
        self.assertEqual(self.dept.name, "開発部（改）")

    def test_edit_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("department_edit", kwargs={"pk": 9999})
        response = self.client.post(url, {"name": "名前"})
        self.assertEqual(response.status_code, 404)

    def test_edit_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("department_edit", kwargs={"pk": self.dept.pk})
        response = self.client.post(url, {"name": "変更"})
        self.assertEqual(response.status_code, 403)

    # ──────────────────────────────────────────────
    # 削除
    # ──────────────────────────────────────────────

    def test_delete_success_redirects_to_list(self):
        """正常系: 所属削除成功 → 一覧にリダイレクトされること"""
        url = reverse("department_delete", kwargs={"pk": self.dept.pk})
        response = self.client.post(url)
        self.assertRedirects(response, self.list_url)

    def test_delete_removes_department(self):
        """正常系: 所属が DB から削除されること"""
        url = reverse("department_delete", kwargs={"pk": self.dept.pk})
        self.client.post(url)
        self.assertFalse(Department.objects.filter(pk=self.dept.pk).exists())

    def test_delete_sets_user_department_null(self):
        """正常系: 所属削除時に紐づくユーザーの department が NULL になること"""
        user = User.objects.create_user(
            login_id="member@example.com", name="部員", password="Pass123",
            department=self.dept,
        )
        url = reverse("department_delete", kwargs={"pk": self.dept.pk})
        self.client.post(url)
        user.refresh_from_db()
        self.assertIsNone(user.department)

    def test_delete_cascades_department_room(self):
        """正常系: 所属削除時に DepartmentRoom も CASCADE 削除されること"""
        room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        dr = DepartmentRoom.objects.create(department=self.dept, room=room)
        url = reverse("department_delete", kwargs={"pk": self.dept.pk})
        self.client.post(url)
        self.assertFalse(DepartmentRoom.objects.filter(pk=dr.pk).exists())

    def test_delete_nonexistent_returns_404(self):
        """異常系: 存在しない pk → 404 が返ること"""
        url = reverse("department_delete", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_non_admin_gets_403(self):
        """異常系: 一般ユーザーは 403 が返ること"""
        self.client.login(username="user@example.com", password="Pass123")
        url = reverse("department_delete", kwargs={"pk": self.dept.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
