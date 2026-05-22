"""
F-05b: CalendarEventsAPI フィルター機能の単体テスト
対象ビュー : reservations.views.CalendarEventsAPI
URL name  : calendar_events  →  GET /calendar/events/

フィルターパラメータ:
  room_ids      - 会議室IDカンマ区切り（''=全OFF）
  building_ids  - 建物IDカンマ区切り
  facility_ids  - 設備IDカンマ区切り
  department_ids- 所属IDカンマ区切り
  user_ids      - ユーザーIDカンマ区切り
"""

import json
from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department, User
from reservations.models import (
    Building, DepartmentRoom, Facility, Reservation, Room, RoomFacility,
)


def make_aware_dt(d, t):
    return timezone.make_aware(datetime.combine(d, t))


class TestF05bEventsAPIFilters(TestCase):
    """F-05b CalendarEventsAPI フィルター機能のテスト"""

    def setUp(self):
        self.url = reverse("calendar_events")
        self.today = date.today()

        # 建物
        self.building_a = Building.objects.create(name="本館")
        self.building_b = Building.objects.create(name="別館")

        # 設備
        self.facility_proj = Facility.objects.create(name="プロジェクター")
        self.facility_wb   = Facility.objects.create(name="ホワイトボード")

        # 所属
        self.dept_dev = Department.objects.create(name="開発部")
        self.dept_biz = Department.objects.create(name="営業部")

        # ユーザー
        self.user1 = User.objects.create_user(
            login_id="user1@example.com", name="ユーザー1", password="Pass123",
            department=self.dept_dev,
        )
        self.user2 = User.objects.create_user(
            login_id="user2@example.com", name="ユーザー2", password="Pass123",
            department=self.dept_biz,
        )

        # 会議室
        self.room_a = Room.objects.create(
            name="会議室A", capacity=10, is_active=True, building=self.building_a,
        )
        self.room_b = Room.objects.create(
            name="会議室B", capacity=5, is_active=True, building=self.building_b,
        )

        # 設備紐づけ
        RoomFacility.objects.create(room=self.room_a, facility=self.facility_proj)
        RoomFacility.objects.create(room=self.room_b, facility=self.facility_wb)

        # 所属紐づけ
        DepartmentRoom.objects.create(department=self.dept_dev, room=self.room_a)
        DepartmentRoom.objects.create(department=self.dept_biz, room=self.room_b)

        # 予約
        self.rsv_a = Reservation.objects.create(
            room=self.room_a, user=self.user1, reserved_by="ユーザー1",
            title="会議室Aの予約",
            start_at=make_aware_dt(self.today, time(10, 0)),
            end_at=make_aware_dt(self.today, time(11, 0)),
            is_cancelled=False,
        )
        self.rsv_b = Reservation.objects.create(
            room=self.room_b, user=self.user2, reserved_by="ユーザー2",
            title="会議室Bの予約",
            start_at=make_aware_dt(self.today, time(13, 0)),
            end_at=make_aware_dt(self.today, time(14, 0)),
            is_cancelled=False,
        )

        self.client.login(username="user1@example.com", password="Pass123")

        # start / end パラメータ（当日全体）
        self.start = make_aware_dt(self.today, time(0, 0)).isoformat()
        self.end   = make_aware_dt(self.today + timedelta(days=1), time(0, 0)).isoformat()

    def _get(self, **params):
        p = {"start": self.start, "end": self.end}
        p.update(params)
        response = self.client.get(self.url, p)
        return json.loads(response.content)

    def _ids(self, events):
        return [e["id"] for e in events]

    # ──────────────────────────────────────────────
    # room_ids フィルター
    # ──────────────────────────────────────────────

    def test_room_ids_filter_returns_only_specified_room(self):
        """room_ids 指定 → 対象会議室の予約のみ返ること"""
        events = self._get(room_ids=str(self.room_a.pk))
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_room_ids_empty_returns_empty(self):
        """room_ids='' → 空配列が返ること"""
        events = self._get(room_ids="")
        self.assertEqual(events, [])

    def test_room_ids_multiple(self):
        """room_ids に複数指定 → 両方の予約が返ること"""
        events = self._get(room_ids=f"{self.room_a.pk},{self.room_b.pk}")
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertIn(self.rsv_b.pk, self._ids(events))

    # ──────────────────────────────────────────────
    # building_ids フィルター
    # ──────────────────────────────────────────────

    def test_building_filter_returns_only_that_building(self):
        """building_ids 指定 → その建物の会議室の予約のみ返ること"""
        events = self._get(building_ids=str(self.building_a.pk))
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_building_filter_empty_returns_empty(self):
        """building_ids='' → 空配列が返ること"""
        events = self._get(building_ids="")
        self.assertEqual(events, [])

    def test_building_filter_no_param_returns_all(self):
        """building_ids 未指定 → 全予約が返ること"""
        events = self._get()
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertIn(self.rsv_b.pk, self._ids(events))

    # ──────────────────────────────────────────────
    # facility_ids フィルター
    # ──────────────────────────────────────────────

    def test_facility_filter_returns_rooms_with_facility(self):
        """facility_ids 指定 → その設備を持つ会議室の予約のみ返ること"""
        events = self._get(facility_ids=str(self.facility_proj.pk))
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_facility_filter_empty_returns_empty(self):
        """facility_ids='' → 空配列が返ること"""
        events = self._get(facility_ids="")
        self.assertEqual(events, [])

    def test_facility_filter_multiple_is_or_condition(self):
        """facility_ids 複数指定 → どちらかの設備を持つ会議室の予約が返ること"""
        events = self._get(
            facility_ids=f"{self.facility_proj.pk},{self.facility_wb.pk}"
        )
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertIn(self.rsv_b.pk, self._ids(events))

    # ──────────────────────────────────────────────
    # department_ids フィルター
    # ──────────────────────────────────────────────

    def test_department_filter_returns_rooms_in_dept(self):
        """department_ids 指定 → その所属に紐づく会議室の予約のみ返ること"""
        events = self._get(department_ids=str(self.dept_dev.pk))
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_department_filter_empty_returns_empty(self):
        """department_ids='' → 空配列が返ること"""
        events = self._get(department_ids="")
        self.assertEqual(events, [])

    def test_department_filter_multiple(self):
        """department_ids 複数指定 → 両所属の会議室の予約が返ること"""
        events = self._get(
            department_ids=f"{self.dept_dev.pk},{self.dept_biz.pk}"
        )
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertIn(self.rsv_b.pk, self._ids(events))

    # ──────────────────────────────────────────────
    # user_ids フィルター
    # ──────────────────────────────────────────────

    def test_user_filter_returns_only_that_users_reservations(self):
        """user_ids 指定 → そのユーザーの予約のみ返ること"""
        events = self._get(user_ids=str(self.user1.pk))
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_user_filter_empty_returns_empty(self):
        """user_ids='' → 空配列が返ること"""
        events = self._get(user_ids="")
        self.assertEqual(events, [])

    def test_user_filter_multiple(self):
        """user_ids 複数指定 → 両ユーザーの予約が返ること"""
        events = self._get(user_ids=f"{self.user1.pk},{self.user2.pk}")
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertIn(self.rsv_b.pk, self._ids(events))

    # ──────────────────────────────────────────────
    # フィルター組み合わせ
    # ──────────────────────────────────────────────

    def test_combined_building_and_user_filter(self):
        """building_ids + user_ids 組み合わせ → 両条件を満たす予約のみ返ること"""
        events = self._get(
            building_ids=str(self.building_a.pk),
            user_ids=str(self.user1.pk),
        )
        self.assertIn(self.rsv_a.pk, self._ids(events))
        self.assertNotIn(self.rsv_b.pk, self._ids(events))

    def test_combined_filters_no_match_returns_empty(self):
        """building_ids（本館）+ user_ids（user2）→ 該当なしで空配列が返ること"""
        events = self._get(
            building_ids=str(self.building_a.pk),
            user_ids=str(self.user2.pk),
        )
        self.assertEqual(events, [])

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_unauthenticated_redirects(self):
        """未ログイン → リダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url, {"start": self.start, "end": self.end})
        self.assertEqual(response.status_code, 302)
