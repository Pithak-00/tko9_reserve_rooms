/* =====================================================
   facility_admin.js
   設備管理（F-22）専用スクリプト
   共通関数（showConfirm / data-confirm-msg）は common.js を参照
   ===================================================== */

const _facUrls = document.getElementById('js-facility-urls');

/**
 * 設備追加・編集モーダルを開く
 * @param {'create'|'edit'} mode
 * @param {HTMLElement} [btn] - 編集ボタン要素（edit モード時に使用）
 */
function openFacilityModal(mode, btn) {
  const modal     = document.getElementById('facilityFormModal');
  const title     = document.getElementById('facilityFormTitle');
  const form      = document.getElementById('facilityForm');
  const submit    = document.getElementById('facilityFormSubmit');
  const nameInput = form.querySelector('input[name="name"]');

  if (mode === 'create') {
    title.textContent  = '設備を追加';
    submit.textContent = '追加';
    form.action = _facUrls.dataset.createUrl;
    if (nameInput) nameInput.value = '';
  } else {
    title.textContent  = '設備を編集';
    submit.textContent = '保存する';
    const pk  = btn.dataset.facilityId;
    const tpl = _facUrls.dataset.editUrlTemplate;
    // URL テンプレートの "/0/" を実際の pk で置換
    form.action = tpl.replace('/0/', '/' + pk + '/');
    if (nameInput) nameInput.value = btn.dataset.name;
  }

  modal.classList.add('open');
  setTimeout(function () { if (nameInput) nameInput.focus(); }, 50);
}

/**
 * 設備追加・編集モーダルを閉じる
 */
function closeFacilityModal() {
  document.getElementById('facilityFormModal').classList.remove('open');
}

/**
 * オーバーレイ部分クリックでモーダルを閉じる
 * @param {MouseEvent} event
 */
function closeFacilityModalOnOverlay(event) {
  if (event.target === document.getElementById('facilityFormModal')) {
    closeFacilityModal();
  }
}
