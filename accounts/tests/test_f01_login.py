"""
F-01: ログイン (CustomLoginView) の単体テスト
対象ビュー : accounts.views.CustomLoginView
URL name  : login  →  /accounts/login/
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class TestF01Login(TestCase):
    """F-01 ログイン機能のテスト"""

    def setUp(self):
        self.url = reverse("login")
        # LOGIN_REDIRECT_URL = "/reservations/timeline/"（settings.py）
        self.login_redirect_url = "/reservations/timeline/"
        # カレンダー画面（ログイン必須ページとして未認証リダイレクトのテストに使用）
        self.calendar_url = "/calendar/"
        # テスト用ユーザー（login_id はメールアドレス形式）
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_login_success_redirects_to_timeline(self):
        """正常系: 有効なID・PWでログイン → タイムライン画面（LOGIN_REDIRECT_URL）へリダイレクト"""
        response = self.client.post(
            self.url,
            {
                "username": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.assertRedirects(response, self.login_redirect_url)

    def test_unauthenticated_access_redirects_to_login(self):
        """正常系: 未ログイン状態でカレンダーにアクセス → ログイン画面へリダイレクト"""
        response = self.client.get(self.calendar_url)
        self.assertRedirects(
            response,
            f"{self.url}?next={self.calendar_url}",
        )

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_login_wrong_user_id_shows_error(self):
        """異常系: 存在しないユーザーIDでログイン → エラーメッセージが表示されること"""
        response = self.client.post(
            self.url,
            {
                "username": "nobody@example.com",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ユーザーIDまたはパスワードが正しくありません。")

    def test_login_wrong_password_shows_error(self):
        """異常系: パスワード不一致でログイン → エラーメッセージが表示されること"""
        response = self.client.post(
            self.url,
            {
                "username": "test@example.com",
                "password": "WrongPassword",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ユーザーIDまたはパスワードが正しくありません。")

    def test_login_inactive_user_shows_error(self):
        """異常系: is_active=False のユーザーでログイン → エラーメッセージが表示されること"""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            self.url,
            {
                "username": "test@example.com",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ユーザーIDまたはパスワードが正しくありません。")

    def test_login_empty_username_shows_validation_error(self):
        """異常系: ユーザーID空欄でフォーム送信 → バリデーションエラーが表示されること"""
        response = self.client.post(
            self.url,
            {
                "username": "",
                "password": "TestPass123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "このフィールドは必須です。")

    # ──────────────────────────────────────────────
    # 追加テスト
    # ──────────────────────────────────────────────

    def test_login_get_returns_200(self):
        """正常系: GET /accounts/login/ → 200 OK でログインフォームが表示されること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_login_get_contains_form(self):
        """正常系: GET ログイン画面 → username / password フィールドが含まれること"""
        response = self.client.get(self.url)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_already_authenticated_user_sees_login_form(self):
        """正常系: 既にログイン済みの状態でログイン画面へアクセス → 200 OK でフォームが表示されること
        （CustomLoginView は redirect_authenticated_user=False のためリダイレクトしない）"""
        self.client.login(username="test@example.com", password="TestPass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
