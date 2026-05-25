"""
E2E テスト: 予約操作
対象機能:
  - スロットクリック → 予約作成画面遷移（時刻・終日）
  - 予約作成フォームの入力・送信
  - 予約イベントクリック → ポップオーバー表示
  - ポップオーバーの「詳細を見る」「編集」リンク
  - ポップオーバーの「キャンセル」操作
  - ドラッグ&ドロップによる予約移動
"""

import re
from datetime import date, datetime, time

import pytest
from django.utils import timezone


pytestmark = pytest.mark.django_db(transaction=True)


# ──────────────────────────────────────────────────────────────
# 予約作成画面への遷移
# ──────────────────────────────────────────────────────────────

def test_click_time_slot_navigates_to_create(
    logged_in_page, calendar_url, e2e_room, wait_for_calendar
):
    """時間スロットクリック → 予約作成画面に遷移すること"""
    logged_in_page.goto(calendar_url + "?view=day")
    wait_for_calendar(logged_in_page)
    # 10:00 スロット（lane = 実際のクリック領域）をクリック
    slot = logged_in_page.locator(".fc-timegrid-slot-lane[data-time='10:00:00']").first
    slot.click()
    logged_in_page.wait_for_url(re.compile(r"/reservations/create/"), timeout=8000)
    assert "/reservations/create/" in logged_in_page.url
    assert "date=" in logged_in_page.url


def test_click_allday_slot_sets_allday_flag(
    logged_in_page, calendar_url, e2e_room, wait_for_calendar
):
    """終日スロットクリック → URL に all_day=1 が付くこと"""
    logged_in_page.goto(calendar_url + "?view=day")
    wait_for_calendar(logged_in_page)
    # 終日行をクリック
    allday_slot = logged_in_page.locator(".fc-daygrid-day-frame, .fc-timegrid-allday-cushion").first
    allday_slot.click()
    logged_in_page.wait_for_url(re.compile(r"/reservations/create/"), timeout=8000)
    assert "all_day=1" in logged_in_page.url


def test_create_button_navigates_to_create(logged_in_page, wait_for_calendar):
    """「＋ 予約を登録する」ボタンで予約作成画面に遷移すること"""
    wait_for_calendar(logged_in_page)
    # サイドバーがスクロールコンテナ内にあるため JS で操作する
    logged_in_page.evaluate("document.querySelector('.sidebar-create-btn').click()")
    logged_in_page.wait_for_url(re.compile(r"/reservations/create/"), timeout=8000)
    assert "/reservations/create/" in logged_in_page.url


# ──────────────────────────────────────────────────────────────
# 予約作成フォーム
# ──────────────────────────────────────────────────────────────

def test_reservation_create_form_submits_successfully(
    logged_in_page, live_server, e2e_room, e2e_user
):
    """予約作成フォームに入力して送信 → 詳細画面にリダイレクトされること"""
    today_str = date.today().strftime("%Y-%m-%d")
    logged_in_page.goto(
        f"{live_server.url}/reservations/create/"
        f"?date={today_str}&time=14:00&room={e2e_room.pk}"
    )
    logged_in_page.wait_for_selector("#roomSelect", state="visible")
    # 件名を入力
    logged_in_page.fill('input[name="title"]', "E2E テスト予約")
    logged_in_page.click('button.btn-primary[type="submit"]')
    # 予約詳細画面にリダイレクト
    logged_in_page.wait_for_url(re.compile(r"/reservations/\d+/$"), timeout=8000)
    assert "/reservations/" in logged_in_page.url
    assert "E2E テスト予約" in logged_in_page.content()


def test_reservation_create_allday_shows_no_time_fields(
    logged_in_page, live_server, e2e_room
):
    """終日フラグ付き予約作成画面では時間フィールドが非表示になること"""
    today_str = date.today().strftime("%Y-%m-%d")
    logged_in_page.goto(
        f"{live_server.url}/reservations/create/?date={today_str}&all_day=1"
    )
    logged_in_page.wait_for_selector("#isAllDay", state="visible")
    # 終日チェックボックスがチェック済み
    assert logged_in_page.locator("#isAllDay").is_checked()
    # 時間フィールドが非表示
    assert not logged_in_page.locator("#timeFields").is_visible()


def test_reservation_create_cancel_returns_to_calendar(
    logged_in_page, live_server, e2e_room
):
    """予約作成画面のキャンセルボタンでカレンダーに戻れること"""
    today_str = date.today().strftime("%Y-%m-%d")
    logged_in_page.goto(f"{live_server.url}/reservations/create/?date={today_str}")
    logged_in_page.wait_for_selector("a.btn-light", state="visible")
    logged_in_page.click("a.btn-light")  # キャンセルボタン
    logged_in_page.wait_for_url(re.compile(r"/calendar/"), timeout=8000)
    assert "/calendar/" in logged_in_page.url


# ──────────────────────────────────────────────────────────────
# 予約ポップオーバー
# ──────────────────────────────────────────────────────────────

def test_event_click_shows_popover(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """予約イベントをクリックするとポップオーバーが表示されること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    # FullCalendar イベントが描画されるまで待機
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    popover = logged_in_page.locator(".reservation-popover")
    assert not popover.get_attribute("hidden")


def test_popover_shows_reservation_title(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """ポップオーバーに予約タイトルが表示されること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    popover = logged_in_page.locator(".reservation-popover")
    assert e2e_reservation.title in popover.inner_text()


def test_popover_detail_link_navigates_to_detail(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """ポップオーバーの「詳細を見る」で予約詳細画面に遷移すること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    logged_in_page.click(".btn-detail")
    logged_in_page.wait_for_url(
        re.compile(rf"/reservations/{e2e_reservation.pk}/"), timeout=8000
    )
    assert f"/reservations/{e2e_reservation.pk}/" in logged_in_page.url


def test_popover_edit_link_navigates_to_edit(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """ポップオーバーの「編集」ボタンで予約編集画面に遷移すること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    logged_in_page.click(".btn-edit")
    logged_in_page.wait_for_url(
        re.compile(rf"/reservations/{e2e_reservation.pk}/edit/"), timeout=8000
    )
    assert f"/reservations/{e2e_reservation.pk}/edit/" in logged_in_page.url


def test_popover_cancel_sets_reservation_cancelled(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """ポップオーバーの「キャンセル」ボタンで予約がキャンセルされること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    logged_in_page.click(".btn-cancel")
    # showConfirm ダイアログが表示されるので「確認」ボタンをクリック
    logged_in_page.wait_for_selector("#_cfm_ok", state="visible", timeout=5000)
    logged_in_page.click("#_cfm_ok")
    logged_in_page.wait_for_timeout(1500)
    # DB でキャンセル済みを確認
    e2e_reservation.refresh_from_db()
    assert e2e_reservation.is_cancelled


def test_popover_closes_on_outside_click(
    logged_in_page, calendar_url, e2e_reservation, wait_for_calendar
):
    """ポップオーバー外クリックでポップオーバーが閉じること"""
    logged_in_page.goto(f"{calendar_url}?view=day")
    wait_for_calendar(logged_in_page)
    event = logged_in_page.locator(".fc-event").first
    event.wait_for(state="visible", timeout=10000)
    event.click()
    logged_in_page.wait_for_timeout(500)
    # カレンダー本体の空き領域をクリック
    logged_in_page.click(".fc-view-harness", position={"x": 5, "y": 5})
    logged_in_page.wait_for_timeout(500)
    popover = logged_in_page.locator(".reservation-popover")
    assert popover.get_attribute("hidden") is not None


# ──────────────────────────────────────────────────────────────
# 予約詳細・編集画面
# ──────────────────────────────────────────────────────────────

def test_reservation_detail_page_shows_info(
    logged_in_page, live_server, e2e_reservation
):
    """予約詳細画面に予約情報が表示されること"""
    logged_in_page.goto(
        f"{live_server.url}/reservations/{e2e_reservation.pk}/"
    )
    logged_in_page.wait_for_selector(".rsv-content", state="visible")
    content = logged_in_page.content()
    assert e2e_reservation.title in content
    assert e2e_reservation.room.name in content


def test_reservation_edit_page_loads(
    logged_in_page, live_server, e2e_reservation
):
    """予約編集画面が表示されること"""
    logged_in_page.goto(
        f"{live_server.url}/reservations/{e2e_reservation.pk}/edit/"
    )
    logged_in_page.wait_for_selector('button.btn-primary[type="submit"]', state="visible")
    assert "編集" in logged_in_page.content()


def test_reservation_detail_cancel_modal_opens(
    logged_in_page, live_server, e2e_reservation
):
    """予約詳細画面の「予約をキャンセル」ボタンでモーダルが開くこと"""
    logged_in_page.goto(
        f"{live_server.url}/reservations/{e2e_reservation.pk}/"
    )
    logged_in_page.wait_for_selector("#openCancelModal", state="visible")
    logged_in_page.click("#openCancelModal")
    logged_in_page.wait_for_timeout(300)
    modal = logged_in_page.locator("#cancelModal")
    # モーダルは hidden 属性で表示制御（open クラスではない）
    assert modal.get_attribute("hidden") is None
