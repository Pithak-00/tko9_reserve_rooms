/* =====================================================
   building_admin.js
   建物管理（F-23）専用スクリプト
   共通関数（showConfirm / data-confirm-msg）は common.js を参照
   ===================================================== */

const _buiUrls = document.getElementById('js-building-urls');

/**
 * 建物追加・編集モーダルを開く
 * @param {'create'|'edit'} mode
 * @param {HTMLElement} [btn] - 編集ボタン要素（edit モード時に使用）
 */
function openBuildingModal(mode, btn) {
  const modal     = document.getElementById('buildingFormModal');
  const title     = document.getElementById('buildingFormTitle');
  const form      = document.getElementById('buildingForm');
  const submit    = document.getElementById('buildingFormSubmit');
  const nameInput = form.querySelector('input[name="name"]');

  if (mode === 'create') {
    title.textContent  = '建物を追加';
    submit.textContent = '追加';
    form.action = _buiUrls.dataset.createUrl;
    if (nameInput) nameInput.value = '';
  } else {
    title.textContent  = '建物を編集';
    submit.textContent = '保存する';
    const pk  = btn.dataset.buildingId;
    const tpl = _buiUrls.dataset.editUrlTemplate;
    // URL テンプレートの "/0/" を実際の pk で置換
    form.action = tpl.replace('/0/', '/' + pk + '/');
    if (nameInput) nameInput.value = btn.dataset.name;
  }

  modal.classList.add('open');
  setTimeout(function () { if (nameInput) nameInput.focus(); }, 50);
}

/**
 * 建物追加・編集モーダルを閉じる
 */
function closeBuildingModal() {
  document.getElementById('buildingFormModal').classList.remove('open');
}

/**
 * オーバーレイ部分クリックでモーダルを閉じる
 * @param {MouseEvent} event
 */
function closeBuildingModalOnOverlay(event) {
  if (event.target === document.getElementById('buildingFormModal')) {
    closeBuildingModal();
  }
}
