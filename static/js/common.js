document.addEventListener("DOMContentLoaded", function () {
  const toast = document.getElementById("toast");
  if (!toast) return;

  toast.addEventListener("click", function () {
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 500);
  });

  setTimeout(function () {
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 500);
  }, 3000);
});

/**			
 * カスタム確認ダイアログを表示する（window.confirm の代替）			
 * @param {string} message  - ダイアログに表示するメッセージ			
 * @param {Function} onOk   - OK 押下時のコールバック関数			
 */			
function showConfirm(message, onOk) {			
  // 既存の .modal-overlay / .modal-box を動的に生成			
  const overlay = document.createElement('div');			
  overlay.className = 'modal-overlay open';			
  overlay.innerHTML = `			
    <div class='modal-box' style='max-width:400px;'>			
      <p style='margin:0 0 20px;font-size:15px;line-height:1.6;'>${message}</p>			
      <div class='modal-footer'>			
        <button id='_cfm_cancel'			
                class='btn btn-secondary btn-md'>			
          キャンセル			
        </button>			
        <button id='_cfm_ok'			
                class='btn btn-danger btn-md'>			
          OK			
        </button>			
      </div>			
    </div>`;			
			
  document.body.appendChild(overlay);			
  // body スクロールを停止（既存モーダルと同様）			
  document.body.style.overflow = 'hidden';			
			
  const close = () => {			
    document.body.removeChild(overlay);			
    document.body.style.overflow = '';			
  };			
			
  overlay.querySelector('#_cfm_ok').addEventListener('click', () => {			
    close();			
    onOk();			
  });			
  overlay.querySelector('#_cfm_cancel').addEventListener('click', close);			
  // オーバーレイクリックでもキャンセル			
  overlay.addEventListener('click', (e) => {			
    if (e.target === overlay) close();			
  });			
}			

/**			
 * data-confirm-msg 属性を持つボタンに確認ダイアログを自動登録			
 * HTML 側の変更：			
 *   - onclick="return confirm('...')" を削除			
 *   - data-confirm-msg="確認メッセージ" を追加			
 *   - data-form="フォームのid" を追加			
 */			
document.addEventListener('DOMContentLoaded', function () {			
  document.querySelectorAll('[data-confirm-msg]').forEach(function (btn) {			
    btn.addEventListener('click', function (e) {			
      e.preventDefault();			
      const msg    = btn.dataset.confirmMsg;			
      const formId = btn.dataset.form;			
      const form   = document.getElementById(formId);			
      if (!form) {			
        console.error('showConfirm: form not found:', formId);			
        return;			
      }			
      showConfirm(msg, function () {			
        form.submit();			
      });			
    });			
  });			
});			

// ── カスタムスクロールバー（Safari対応） ──
document.addEventListener('DOMContentLoaded', function () {
  const scroll = document.querySelector('.table-scroll');
  if (!scroll) return;

  // 横スクロールバー（テーブルの上）
  const hBar = document.createElement('div');
  const hThumb = document.createElement('div');
  hBar.style.cssText = `
    width: 100%;
    height: 8px;
    background: #ddd;
    border-radius: 4px;
    margin-bottom: 0px;
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
