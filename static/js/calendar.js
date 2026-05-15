/* ===== ナビゲーションメニュー ===== */
function toggleNavMenu(e) {
  e.stopPropagation();
  document.getElementById("navMenu").classList.toggle("open");
}

function toggleAdminSubmenu(e) {
  // 親メニューへの伝播を止めてメニューが閉じないようにする
  e.stopPropagation();
  const submenu = document.getElementById("adminSubmenu");
  const arrow = document.getElementById("adminArrow");
  if (submenu) submenu.classList.toggle("open");
  if (arrow) arrow.classList.toggle("open");
}

// メニュー外クリック時のみ閉じる（contains チェックで内部クリックを除外）
document.addEventListener("click", function (e) {
  const navMenu = document.getElementById("navMenu");
  const dotsBtn = document.querySelector(".dots-btn");

  // クリック対象がメニュー内・dots-btn内であれば何もしない
  if (
    (navMenu && navMenu.contains(e.target)) ||
    (dotsBtn && dotsBtn.contains(e.target))
  ) {
    return;
  }

  // メニュー外クリック → すべて閉じる
  if (navMenu) navMenu.classList.remove("open");
  const submenu = document.getElementById("adminSubmenu");
  const arrow = document.getElementById("adminArrow");
  if (submenu) submenu.classList.remove("open");
  if (arrow) arrow.classList.remove("open");
});

/* ===== 予約詳細モーダル ===== */
function showReservationModal(el) {
  document.getElementById("modal-title").textContent = el.dataset.title;
  document.getElementById("modal-reserved-by").textContent =
    el.dataset.reservedBy;
  document.getElementById("modal-time").textContent =
    el.dataset.start + " 〜 " + el.dataset.end;
  document.getElementById("modal-detail-link").href =
    "/reservations/" + el.dataset.reservationId + "/";
  document.getElementById("reservationModal").classList.add("open");
}

function closeModal() {
  document.getElementById("reservationModal").classList.remove("open");
}

function closeModalOnOverlay(e) {
  if (e.target === document.getElementById("reservationModal")) closeModal();
}

document.addEventListener('DOMContentLoaded', function () {
  const el = document.getElementById('fullcalendar');
  const rooms = JSON.parse(el.dataset.rooms || '[]');
  const fcView = el.dataset.fcView || 'timeGridWeek';
  const initialDate = el.dataset.date || new Date().toISOString().slice(0,10);

  // 会議室フィルタ（localStorage から復元）
  const selectedIds = getSelectedRoomIds();

  const calendar = new FullCalendar.Calendar(el, {
    locale: 'ja',
    initialView: fcView,
    initialDate: initialDate,
    firstDay: 1,  // 月曜始まり
    slotMinTime: '00:00:00',
    slotMaxTime: '24:00:00',
    slotDuration: '00:30:00',
    scrollTime: '08:00:00',
    nowIndicator: true,
    dayMaxEvents: 2,
    editable: true,
    selectable: true,
    headerToolbar: false,  // カスタムツールバー使用
    eventSources: [{ url: '/reservations/events/',
      extraParams: () => ({
        room_ids: getSelectedRoomIds().join(',') }),
    }],
    eventClick: handleEventClick,
    eventDrop: handleEventDrop,
    eventResize: handleEventDrop,  // 同ロジック
    dateClick: handleDateClick,
    select: handleSelect,
    eventDidMount: (info) => {
      // is_owner=false の場合は DnD を無効化
      if (!info.event.extendedProps.editable) {
        info.el.setAttribute('draggable', 'false');
      }
    },
  });
  calendar.render();
});

// DnD コールバック（eventDrop / eventResize 共通）
function handleEventDrop(info) {
  const res = info.event;
  const newStart = res.start.toISOString();
  const newEnd   = res.end   ? res.end.toISOString() : null;
  const msg = `${formatDate(res.start)} に移動しますか？`;

  showConfirm(msg, () => {  // 確認 OK
    fetch(`/reservations/${res.id}/move/`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()},
      body: JSON.stringify({
        start_at: newStart, end_at: newEnd,
        room_id: res.extendedProps.room_id
      })
    })
    .then(r => {
      if (!r.ok) {
        return r.json().then(d => { throw new Error(d.error); });
      }
      // 成功：「元に戻す」トーストを5秒表示
      showUndoToast('予約を移動しました', () => {
        // 元に戻す：info.revert() + PATCH で元の値を送信
        info.revert();
      });
    })
    .catch(err => {
      showToast(err.message || '移動に失敗しました', 'error');
      info.revert();
    });
  }, () => {  // キャンセル
    info.revert();
  });
}

// eventClick コールバック — ポップオーバー表示
function handleEventClick(info) {
  const ev = info.event;
  const ep = ev.extendedProps;
  const po = document.querySelector('.reservation-popover');

  // 内容を更新
  po.querySelector('.popover-title').textContent = ev.title;
  po.querySelector('.popover-title').style.backgroundColor = ev.backgroundColor;
  po.querySelector('[data-field="datetime"]').textContent =
    `${formatDate(ev.start)} ${formatTime(ev.start)}〜${formatTime(ev.end)}`;
  po.querySelector('[data-field="room"]').textContent = ep.room_name;
  po.querySelector('[data-field="reserver"]').textContent = ep.reserved_by;

  // 権限に応じてボタン表示
  const editBtn   = po.querySelector('.btn-edit');
  const cancelBtn = po.querySelector('.btn-cancel');
  editBtn.hidden   = !ep.editable;
  cancelBtn.hidden = !ep.editable;
  editBtn.href   = `/reservations/${ev.id}/edit/`;
  cancelBtn.href = `/reservations/${ev.id}/cancel/`;

  // 位置を調整して表示
  po.style.left = `${info.jsEvent.pageX + 10}px`;
  po.style.top  = `${info.jsEvent.pageY + 10}px`;
  po.hidden = false;

  info.jsEvent.stopPropagation();
}

// 外クリックで閉じる
document.addEventListener('click', () => {
  document.querySelector('.reservation-popover').hidden = true;
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape')
    document.querySelector('.reservation-popover').hidden = true;
});

// 会議室選択状態の localStorage 連携
const STORAGE_KEY = 'calendar_room_selection';

function getSelectedRoomIds() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : getRoomIds(); // 未保存は全室
  } catch { return getRoomIds(); }
}

function saveSelectedRoomIds(ids) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

// チェックボックス変更時
document.querySelectorAll('.room-checkbox').forEach(cb => {
  cb.addEventListener('change', () => {
    const ids = Array.from(
      document.querySelectorAll('.room-checkbox:checked'),
      el => parseInt(el.value)
    );
    saveSelectedRoomIds(ids);
    calendar.refetchEvents();  // FullCalendar に反映
  });
});

// RRULE 生成ユーティリティ
function buildRRule(pattern, days, endType, endValue) {
  const DAY_MAP = {mon:'MO',tue:'TU',wed:'WE',thu:'TH',fri:'FR',sat:'SA',sun:'SU'};
  let rule = '';
  if      (pattern === 'daily')   rule = 'FREQ=DAILY';
  else if (pattern === 'weekly') {
    const byDay = days.map(d => DAY_MAP[d]).join(',');
    rule = `FREQ=WEEKLY;BYDAY=${byDay}`;
  }
  else if (pattern === 'monthly') rule = 'FREQ=MONTHLY';
  if (endType === 'count') rule += `;COUNT=${endValue}`;
  if (endType === 'until') {
    const dt = endValue.replace(/-/g,'') + 'T000000Z';
    rule += `;UNTIL=${dt}`;
  }
  return rule;  // 例: FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10
}

// 輝度計算ユーティリティ（F-04-R04）
// 参考: WCAG 2.1 相対輝度 https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
function getTextColor(hexColor) {
  // HEX → RGB（0〜255）
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);

  // 線形化（ガンマ補正を除去）
  const toLinear = (c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };

  // 相対輝度 L = 0.2126R + 0.7152G + 0.0722B
  const L = 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);

  // 閾値 0.179 を境に白 or 黒を返す
  return L > 0.179 ? '#1A1A2E' : '#FFFFFF';
}

// 使用例：FullCalendar eventDidMount で適用
eventDidMount: (info) => {
  const bgColor = info.event.backgroundColor;
  info.el.style.color = getTextColor(bgColor);
  if (!info.event.extendedProps.editable) {
    info.el.setAttribute('draggable', 'false');
  }
},

// Google 同期トグル・連携解除（calendar.js 追記）

// 同期 ON/OFF トグル
document.getElementById('google-sync-toggle')?.addEventListener('change', function () {
  fetch('/auth/google/sync-toggle/', {
    method: 'PATCH',
    headers: {'X-CSRFToken': getCsrfToken(), 'Content-Type': 'application/json'},
    body: JSON.stringify({})
  })
  .then(r => r.json())
  .then(data => {
    const label = document.getElementById('sync-status-label');
    if (label) label.textContent = data.sync_enabled ? '同期中' : '一時停止中';
    showToast(data.sync_enabled ? 'Google 同期を有効にしました' : 'Google 同期を一時停止しました');
  })
  .catch(() => showToast('エラーが発生しました', 'error'));
});

// 連携解除
document.getElementById('google-disconnect-btn')?.addEventListener('click', function () {
  showConfirm('Google カレンダーとの連携を解除しますか？\n解除後は新規予約の同期が停止されます。', () => {
    fetch('/auth/google/disconnect/', {
      method: 'POST',
      headers: {'X-CSRFToken': getCsrfToken()}
    })
    .then(r => { if (r.ok) location.reload(); })
    .catch(() => showToast('連携解除に失敗しました', 'error'));
  });
});