/* =====================================================
   department_admin.js
   所属管理（F-24）専用スクリプト
   共通関数（showConfirm / data-confirm-msg）は common.js を参照
   ===================================================== */

const _depUrls = document.getElementById('js-department-urls');

/**
 * 所属追加・編集モーダルを開く
 * @param {'create'|'edit'} mode
 * @param {HTMLElement} [btn] - 編集ボタン要素（edit モード時に使用）
 */
function openDepartmentModal(mode, btn) {
  const modal     = document.getElementById('departmentFormModal');
  const title     = document.getElementById('departmentFormTitle');
  const form      = document.getElementById('departmentForm');
  const submit    = document.getElementById('departmentFormSubmit');
  const nameInput = form.querySelector('input[name="name"]');

  if (mode === 'create') {
    title.textContent  = '所属を追加';
    submit.textContent = '追加';
    form.action = _depUrls.dataset.createUrl;
    if (nameInput) nameInput.value = '';
  } else {
    title.textContent  = '所属を編集';
    submit.textContent = '保存する';
    const pk  = btn.dataset.departmentId;
    const tpl = _depUrls.dataset.editUrlTemplate;
    // URL テンプレートの "/0/" を実際の pk で置換
    form.action = tpl.replace('/0/', '/' + pk + '/');
    if (nameInput) nameInput.value = btn.dataset.name;
  }

  modal.classList.add('open');
  setTimeout(function () { if (nameInput) nameInput.focus(); }, 50);
}

/**
 * 所属追加・編集モーダルを閉じる
 */
function closeDepartmentModal() {
  document.getElementById('departmentFormModal').classList.remove('open');
}

/**
 * オーバーレイ部分クリックでモーダルを閉じる
 * @param {MouseEvent} event
 */
function closeDepartmentModalOnOverlay(event) {
  if (event.target === document.getElementById('departmentFormModal')) {
    closeDepartmentModal();
  }
}
