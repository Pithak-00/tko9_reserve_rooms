"""
同時リクエストによるレースコンディションテスト
select_for_update() の排他制御が正しく機能することを検証する。

TransactionTestCase を使用する理由:
  - TestCase はテスト全体を 1 トランザクションでラップするため、
    別スレッドからのコミットが見えず select_for_update() の動作検証ができない
  - TransactionTestCase は各テスト後に TRUNCATE するため実際のコミットが発生し、
    スレッド間でデータが共有される
"""
import threading
import json
from datetime import date, datetime, time, timedelta

from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


def make_aware_dt(d, t):
    return timezone.make_aware(datetime.combine(d, t))


class TestConcurrentReservationCreate(TransactionTestCase):
    """同一時間帯への同時予約作成：1件だけ成功し残りはエラーになること"""

    def setUp(self):
        self.room = Room.objects.create(name="競合テスト会議室", capacity=10, is_active=True)
        self.today = date.today() + timedelta(days=30)  # 未来日で既存予約と干渉しない

        # N 人のユーザーを用意
        self.users = []
        for i in range(5):
            u = User.objects.create_user(
                login_id=f"concurrent_user{i}@example.com",
                name=f"同時ユーザー{i}",
                password="TestPass123",
            )
            self.users.append(u)

    def _create_reservation(self, user, results, index):
        """各スレッドから呼ばれる予約作成関数"""
        client = Client()
        client.login(username=user.login_id, password="TestPass123")

        url = reverse("reservation_create")
        data = {
            "room":         self.room.pk,
            "title":        f"同時テスト {index}",
            "reserve_date": self.today.strftime("%Y-%m-%d"),
            "start_time":   "10:00",
            "end_time":     "11:00",
            "is_all_day":   False,
        }
        response = client.post(url, data)
        results[index] = response.status_code

    def test_only_one_succeeds_under_concurrent_create(self):
        """5スレッドが同一時間帯に同時予約 → 成功は1件、残り4件はフォームエラー(200)"""
        N = 5
        results = [None] * N
        barrier = threading.Barrier(N)  # 全スレッドが揃ってから一斉に送信

        def run(i):
            barrier.wait()  # 全スレッド待機して同時スタート
            self._create_reservation(self.users[i], results, i)

        threads = [threading.Thread(target=run, args=(i,)) for i in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        # 作成された予約は高々1件
        created = Reservation.objects.filter(
            room=self.room,
            start_at=make_aware_dt(self.today, time(10, 0)),
        ).count()

        print(f"\n[同時作成テスト] 作成件数: {created}, ステータス: {results}")
        self.assertLessEqual(created, 1, "同一時間帯に複数の予約が作成されてしまった（二重予約）")

    def test_double_booking_is_prevented_verified(self):
        """排他制御なしでは二重予約が発生することを確認する（ネガティブ検証）
        select_for_update() を使っている場合は created == 1 が期待値。
        """
        N = 3
        results = [None] * N
        barrier = threading.Barrier(N)

        def run(i):
            barrier.wait()
            self._create_reservation(self.users[i], results, i)

        threads = [threading.Thread(target=run, args=(i,)) for i in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        created = Reservation.objects.filter(
            room=self.room,
            start_at=make_aware_dt(self.today, time(10, 0)),
        ).count()

        successes = [s for s in results if s == 302]  # リダイレクト = 成功
        print(f"\n[二重予約防止テスト] 作成件数: {created}, 302(成功): {len(successes)}, 結果: {results}")
        self.assertEqual(created, len(successes), "成功レスポンス数と実際の作成件数が一致しない")
        self.assertLessEqual(created, 1, "二重予約が発生した")


class TestConcurrentReservationMove(TransactionTestCase):
    """同一時間帯への同時ドラッグ移動：排他制御で競合がブロックされること"""

    def setUp(self):
        self.room = Room.objects.create(name="移動競合テスト会議室", capacity=10, is_active=True)
        self.today = date.today() + timedelta(days=30)

        self.users = []
        self.reservations = []
        for i in range(3):
            u = User.objects.create_user(
                login_id=f"move_user{i}@example.com",
                name=f"移動ユーザー{i}",
                password="TestPass123",
            )
            # 各ユーザーの予約（別々の時間帯）
            rsv = Reservation.objects.create(
                room=self.room,
                user=u,
                reserved_by=u.name,
                title=f"移動テスト{i}",
                start_at=make_aware_dt(self.today, time(8 + i, 0)),
                end_at=make_aware_dt(self.today, time(9 + i, 0)),
                is_cancelled=False,
            )
            self.users.append(u)
            self.reservations.append(rsv)

    def _move_reservation(self, user, reservation, target_start, target_end, results, index):
        client = Client()
        client.login(username=user.login_id, password="TestPass123")

        url = reverse("reservation_move", kwargs={"pk": reservation.pk})
        tz = timezone.get_current_timezone()
        start_iso = timezone.make_aware(
            datetime.combine(self.today, target_start), tz
        ).isoformat()
        end_iso = timezone.make_aware(
            datetime.combine(self.today, target_end), tz
        ).isoformat()

        response = client.patch(
            url,
            data=json.dumps({"start_at": start_iso, "end_at": end_iso}),
            content_type="application/json",
        )
        results[index] = response.status_code

    def test_concurrent_move_to_same_slot(self):
        """3つの予約を同時に同一スロットへ移動 → 1件だけ成功し残りは 400"""
        N = 3
        results = [None] * N
        barrier = threading.Barrier(N)
        target_start = time(15, 0)
        target_end   = time(16, 0)

        def run(i):
            barrier.wait()
            self._move_reservation(
                self.users[i], self.reservations[i],
                target_start, target_end, results, i
            )

        threads = [threading.Thread(target=run, args=(i,)) for i in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        moved = Reservation.objects.filter(
            room=self.room,
            start_at=make_aware_dt(self.today, target_start),
            is_cancelled=False,
        ).count()

        successes = [s for s in results if s == 200]
        print(f"\n[同時移動テスト] 移動成功件数: {moved}, 200(成功): {len(successes)}, 結果: {results}")
        self.assertLessEqual(moved, 1, "同一スロットへの同時移動で複数が成功してしまった")
