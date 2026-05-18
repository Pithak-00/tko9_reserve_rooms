/* =====================================================
   common.js
   全ページ共通スクリプト
   ===================================================== */

/* ── トースト自動非表示 ── */
document.addEventListener("DOMContentLoaded", function () {
  const toast = document.querySelector(".toast.show");
  if (!toast) return;

  toast.addEventListener("click", function () {
    toast.classList.add("hide");
    setTimeout(function () { toast.remove(); }, 500);
  });

  setTimeout(function () {
    toast.classList.add("hide");
    setTimeout(function () { toast.remove(); }, 500);
  }, 3000);
});

/* ── カスタム確認ダイアログ（window.confirm の代替） ──
   iOS Safari では window.confirm() がブロック・無視されることがあるため、
   モーダル形式のカスタムダイアログを使用する。
   ─────────────────────────────────────────────────── */

/**
 * カスタム確認ダイアログを表示する
 * @param {string}   message          - ダイアログに表示するメッセージ
 * @param {Function} onOk             - OK ボタン押下時に呼ばれるコールバック
 * @param {Function} [onCancel]       - キャンセル時に呼ばれるコールバック（省略可）
 * @param {string}   [okLabel='確認'] - OK ボタンのラベル（省略可）
 */
function showConfirm(message, onOk, onCancel, okLabel) {
  const btnLabel = okLabel || '確認';
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay open';
  overlay.style.zIndex = '9999';
  overlay.innerHTML =
    "<div class='modal-box' style='max-width:420px;padding:28px 32px;'>" +
      "<p style='margin:0 0 20px;font-size:15px;line-height:1.6;color:#333;'>" +
        message.replace(/\n/g, '<br>') +
      "</p>" +
      "<div class='modal-footer'>" +
        "<button id='_cfm_cancel' class='btn btn-light btn-md'>キャンセル</button>" +
        "<button id='_cfm_ok'     class='btn btn-danger btn-md'>" + btnLabel + "</button>" +
      "</div>" +
    "</div>";

  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  function close(cancelled) {
    document.body.removeChild(overlay);
    document.body.style.overflow = '';
    if (cancelled && typeof onCancel === 'function') onCancel();
  }

  overlay.querySelector('#_cfm_ok').addEventListener('click', function () {
    document.body.removeChild(overlay);
    document.body.style.overflow = '';
    onOk();
  });
  overlay.querySelector('#_cfm_cancel').addEventListener('click', function () { close(true); });
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) close(true);
  });
}

/* ── data-confirm-msg 属性を持つボタンに削除確認を自動登録 ──
   ※ このスクリプトは </body> 直前で読み込むため、
      DOMContentLoaded を使わず即時実行する。
   使い方:
     <form id="del-form-1" method="post" action="..." class="logout-form">{% csrf_token %}</form>
     <button type="button"
             data-confirm-msg="本当に削除しますか？"
             data-form="del-form-1">削除</button>
   ─────────────────────────────────────────────────────────── */
(function () {
  document.querySelectorAll('[data-confirm-msg]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var msg  = btn.dataset.confirmMsg;
      var form = document.getElementById(btn.dataset.form);
      if (!form) {
        console.error('showConfirm: form not found:', btn.dataset.form);
        return;
      }
      showConfirm(msg, function () { form.submit(); });
    });
  });
}());

/* ===== カレンダー共通ユーティリティ（F-04 追加分） ===== */

// CSRF トークン取得
function getCsrfToken() {
  return document.cookie.split(';')
    .map(c => c.trim()).find(c => c.startsWith('csrftoken='))
    ?.split('=')[1] ?? '';
}

// 成功・エラートースト
function showToast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className = 'toast show top-right';
  t.style.backgroundColor = type === 'error' ? '#c0392b' : '#27ae60';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => { t.classList.add('hide'); setTimeout(() => t.remove(), 500); }, 3000);
}

// 「元に戻す」付きトースト（5秒）
function showUndoToast(msg, onUndo) {
  const t = document.createElement('div');
  t.className = 'toast show top-right';
  t.style.backgroundColor = '#2563eb';
  t.innerHTML = `${msg} <button style='margin-left:12px;background:none;border:1px solid #fff;
    color:#fff;cursor:pointer;border-radius:4px;padding:2px 8px;'>元に戻す</button>`;
  document.body.appendChild(t);
  const btn = t.querySelector('button');
  let done = false;
  btn.addEventListener('click', () => { if (!done) { done = true; onUndo(); t.remove(); } });
  setTimeout(() => { if (!done) { t.classList.add('hide'); setTimeout(() => t.remove(), 500); } }, 5000);
}

// 日付フォーマット（例：5月14日(水) 10:00）
function formatDate(dt) {
  const days = ['日','月','火','水','木','金','土'];
  return `${dt.getMonth()+1}月${dt.getDate()}日(${days[dt.getDay()]})`;
}

// 時刻フォーマット（例：10:00）
function formatTime(dt) {
  if (!dt) return '';
  return dt.toTimeString().slice(0, 5);
}