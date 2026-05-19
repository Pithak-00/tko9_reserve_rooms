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

/* ── data-confirm-msg 属性を持つボタンに削除確認を自動登録 ── */
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

// ── カスタムスクロールバー（Safari対応） ──
document.addEventListener('DOMContentLoaded', function () {
  const scroll = document.querySelector('.table-scroll');
  if (!scroll) return;

  // 横スクロールバー（テーブルの下）
  const hBar = document.createElement('div');
  const hThumb = document.createElement('div');
  hBar.style.cssText = `
    width: 100%;
    height: 8px;
    background: #ddd;
    border-radius: 4px;
    margin-top: 6px;
    position: relative;
    cursor: pointer;
  `;
  hThumb.style.cssText = `
    height: 100%;
    background: #888;
    border-radius: 4px;
    position: absolute;
    top: 0;
  `;
  hBar.appendChild(hThumb);
  scroll.parentNode.insertBefore(hBar, scroll.nextSibling);

  // 縦スクロールバー（テーブルの右）
  const vBar = document.createElement('div');
  const vThumb = document.createElement('div');
  vBar.style.cssText = `
    width: 8px;
    background: #ddd;
    border-radius: 4px;
    position: absolute;
    right: 0;
    top: 0;
    cursor: pointer;
  `;
  vThumb.style.cssText = `
    width: 100%;
    background: #888;
    border-radius: 4px;
    position: absolute;
    left: 0;
  `;
  vBar.appendChild(vThumb);
  scroll.style.position = 'relative';
  scroll.parentNode.style.position = 'relative';
  scroll.parentNode.appendChild(vBar);

  // 位置を更新する関数
  function update() {
    const hRatio = scroll.clientWidth / scroll.scrollWidth;
    hThumb.style.width = (hRatio * 100) + '%';
    hThumb.style.left = (scroll.scrollLeft / scroll.scrollWidth * 100) + '%';

    vBar.style.height = scroll.clientHeight + 'px';
    const vRatio = scroll.clientHeight / scroll.scrollHeight;
    vThumb.style.height = (vRatio * 100) + '%';
    vThumb.style.top = (scroll.scrollTop / scroll.scrollHeight * 100) + '%';
  }

  scroll.addEventListener('scroll', update);
  window.addEventListener('resize', update);
  update();
});