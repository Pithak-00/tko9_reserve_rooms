"""
E2E テスト: カレンダー表示・操作
対象機能:
  - カレンダー画面の表示
  - 前後ナビゲーション（← / 今日 / →）
  - 日/週/月ビュー切替
  - フィルターサイドバー（会議室チェック）
  - ナビメニュー開閉
  - 未ログインリダイレクト
"""

import re
from datetime import date

import pytest


pytestmark = pytest.mark.django_db(transaction=True)


# ──────────────────────────────────────────────────────────────
# カレンダー表示
# ──────────────────────────────────────────────────────────────

def test_calendar_page_loads(logged_in_page, wait_for_calendar):
    """カレンダーページが正常に表示されること"""
    wait_for_calendar(logged_in_page)
    assert "カレンダー" in logged_in_page.title()


def test_calendar_shows_today_year(logged_in_page, wait_for_calendar):
    """デフォルトで今日の年がページに含まれること"""
    wait_for_calendar(logged_in_page)
    today_year = str(date.today().year)
    assert today_year in logged_in_page.content()


def test_calendar_sidebar_shows_room_name(
    logged_in_page, calendar_url, e2e_room, wait_for_calendar
):
    """サイドバーに会議室名が表示されること（room 作成後にページ再読み込み）"""
    logged_in_page.goto(calendar_url)
    wait_for_calendar(logged_in_page)
    assert e2e_room.name in logged_in_page.content()


def test_calendar_has_create_reservation_button(logged_in_page, wait_for_calendar):
    """「＋ 予約を登録する」ボタンが表示されること"""
    wait_for_calendar(logged_in_page)
    btn = logged_in_page.locator(".sidebar-create-btn")
    assert btn.is_visible()


def test_calendar_room_legend_shows_room(
    logged_in_page, calendar_url, e2e_room, wait_for_calendar
):
    """会議室凡例バーに会議室名が表示されること"""
    logged_in_page.goto(calendar_url)
    wait_for_calendar(logged_in_page)
    legend = logged_in_page.locator("#roomLegend").inner_text()
    assert e2e_room.name in legend


# ──────────────────────────────────────────────────────────────
# ナビゲーション
# ──────────────────────────────────────────────────────────────

def test_prev_button_changes_title(logged_in_page, wait_for_calendar):
    """← ボタンで表示期間が変わること"""
    wait_for_calendar(logged_in_page)
    title_before = logged_in_page.locator("#calTitle").inner_text()
    logged_in_page.click("#btnPrev")
    logged_in_page.wait_for_timeout(800)
    title_after = logged_in_page.locator("#calTitle").inner_text()
    assert title_before != title_after


def test_next_button_changes_title(logged_in_page, wait_for_calendar):
    """→ ボタンで表示期間が変わること"""
    wait_for_calendar(logged_in_page)
    title_before = logged_in_page.locator("#calTitle").inner_text()
    logged_in_page.click("#btnNext")
    logged_in_page.wait_for_timeout(800)
    title_after = logged_in_page.locator("#calTitle").inner_text()
    assert title_before != title_after


def test_today_button_returns_to_today(logged_in_page, wait_for_calendar):
    """「今日」ボタンで今日に戻れること"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click("#btnPrev")
    logged_in_page.wait_for_timeout(500)
    logged_in_page.click("#btnToday")
    logged_in_page.wait_for_timeout(800)
    today_year = str(date.today().year)
    assert today_year in logged_in_page.locator("#calTitle").inner_text()


# ──────────────────────────────────────────────────────────────
# ビュー切替
# ──────────────────────────────────────────────────────────────

def test_switch_to_day_view(logged_in_page, wait_for_calendar):
    """「日」ボタンで日表示ビューに切替わること"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click("button.view-tab:has-text('日')")
    logged_in_page.wait_for_url(re.compile(r"view=day"), timeout=8000)
    assert "view=day" in logged_in_page.url


def test_switch_to_month_view(logged_in_page, wait_for_calendar):
    """「月」ボタンで月表示ビューに切替わること"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click("button.view-tab:has-text('月')")
    logged_in_page.wait_for_url(re.compile(r"view=month"), timeout=8000)
    assert "view=month" in logged_in_page.url


def test_switch_back_to_week_view(logged_in_page, wait_for_calendar):
    """日表示から「週」ボタンで週表示に戻れること"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click("button.view-tab:has-text('日')")
    logged_in_page.wait_for_url(re.compile(r"view=day"), timeout=8000)
    logged_in_page.click("button.view-tab:has-text('週')")
    logged_in_page.wait_for_url(re.compile(r"view=week"), timeout=8000)
    assert "view=week" in logged_in_page.url


# ──────────────────────────────────────────────────────────────
# フィルターサイドバー
# ──────────────────────────────────────────────────────────────

def test_room_checkbox_checked_by_default(
    logged_in_page, calendar_url, e2e_room, wait_for_calendar
):
    """会議室フィルターチェックボックスが初期状態でチェック済みであること"""
    logged_in_page.goto(calendar_url)
    wait_for_calendar(logged_in_page)
    checkbox = logged_in_page.locator(f'.room-checkbox[value="{e2e_room.pk}"]')
    assert checkbox.is_checked()


def test_select_all_checkbox_checks_all_rooms(
    logged_in_page, calendar_url, e2e_room, e2e_room2, wait_for_calendar
):
    """「すべて」チェックを外して再チェックすると全会議室が選択されること"""
    logged_in_page.goto(calendar_url)
    wait_for_calendar(logged_in_page)
    select_all = logged_in_page.locator("#selectAllRooms")
    select_all.uncheck()
    logged_in_page.wait_for_timeout(300)
    select_all.check()
    logged_in_page.wait_for_timeout(300)
    for room in [e2e_room, e2e_room2]:
        cb = logged_in_page.locator(f'.room-checkbox[value="{room.pk}"]')
        assert cb.is_checked()


# ──────────────────────────────────────────────────────────────
# ナビメニュー
# ──────────────────────────────────────────────────────────────

def test_nav_menu_opens_on_dots_click(logged_in_page, wait_for_calendar):
    """「•••」ボタンクリックでナビメニューが開くこと"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click(".dots-btn")
    logged_in_page.wait_for_timeout(300)
    nav = logged_in_page.locator("#navMenu")
    assert "open" in (nav.get_attribute("class") or "")


def test_nav_menu_closes_on_outside_click(logged_in_page, wait_for_calendar):
    """メニュー外クリックでナビメニューが閉じること"""
    wait_for_calendar(logged_in_page)
    logged_in_page.click(".dots-btn")
    logged_in_page.wait_for_timeout(300)
    logged_in_page.click(".fc-view-harness", position={"x": 10, "y": 10})
    logged_in_page.wait_for_timeout(300)
    nav = logged_in_page.locator("#navMenu")
    assert "open" not in (nav.get_attribute("class") or "")


# ──────────────────────────────────────────────────────────────
# 認証
# ──────────────────────────────────────────────────────────────

def test_unauthenticated_redirects_to_login(page, live_server):
    """未ログインでカレンダーにアクセスするとログイン画面にリダイレクトされること"""
    page.goto(f"{live_server.url}/calendar/")
    page.wait_for_url(re.compile(r"/accounts/login/"), timeout=8000)
    assert "/accounts/login/" in page.url
