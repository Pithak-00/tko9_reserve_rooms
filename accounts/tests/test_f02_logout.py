"""
F-02: ログアウト (LogoutView) の単体テスト
対象ビュー : django.contrib.auth.views.LogoutView
URL name  : logout  →  /accounts/logout/
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class TestF02Logout(TestCase):
    """F-02 ログアウト機能のテスト"""

    def setUp(self):
        self.logout_url = reverse("logout")
        self.login_url = "/accounts/login/"
        self.calendar_url = "/calendar/"
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )

    def _login(self):
        """テストヘルパー: ユーザーをログイン状態にする"""
        self.client.login(username="test@example.com", password="TestPass123")

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_logout_redirects_to_login(self):
        """正常系: ログアウト（POST）→ ログイン画面へリダイレクトされること"""
        self._login()
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_logout_destroys_session(self):
        """正常系: ログアウト後はカレンダー画面にアクセスできないこと（ログイン画面へリダイレクト）"""
        self._login()
        self.client.post(self.logout_url)
        response = self.client.get(self.calendar_url)
        self.assertRedirects(
            response,
            f"{self.login_url}?next={self.calendar_url}",
        )

    # ──────────────────────────────────────────────
    # 追加テスト
    # ──────────────────────────────────────────────

    def test_logout_unauthenticated_still_redirects_to_login(self):
        """正常系: 未ログイン状態でログアウト POST → ログイン画面へリダイレクトされること"""
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)

    def test_logout_twice_is_safe(self):
        """正常系: 二重ログアウトしてもエラーにならないこと"""
        self._login()
        self.client.post(self.logout_url)
        response = self.client.post(self.logout_url)
        self.assertRedirects(response, self.login_url)
