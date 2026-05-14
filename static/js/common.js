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
 * @param {string}   message - ダイアログに表示するメッセージ
 * @param {Function} onOk    - OK ボタン押下時に呼ばれるコールバック
 */
function showConfirm(message, onOk) {
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
        "<button id='_cfm_ok'     class='btn btn-danger btn-md'>削除する</button>" +
      "</div>" +
    "</div>";

  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  function close() {
    document.body.removeChild(overlay);
    document.body.style.overflow = '';
  }

  overlay.querySelector('#_cfm_ok').addEventListener('click', function () {
    close();
    onOk();
  });
  overlay.querySelector('#_cfm_cancel').addEventListener('click', close);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) close();
  });
}

/* ── data-confirm-msg 属性を持つボタンに削除確認を自動登録 ──
   使い方:
     <form id="del-form-1" method="post" action="..." class="logout-form">{% csrf_token %}</form>
     <button type="button"
             data-confirm-msg="本当に削除しますか？"
             data-form="del-form-1">削除</button>
   ─────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
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
});
