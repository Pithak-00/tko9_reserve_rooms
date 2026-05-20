/* =====================================================
   room_admin.js
   会議室マスタ管理画面（S-10）専用スクリプト
   ===================================================== */

"use strict";

// ── URL 定数（HTML の data 属性から取得） ───────────────────
const _urlEl = document.getElementById("js-urls");
const ROOM_URL = {
  create: _urlEl.dataset.createUrl,
  editTemplate: _urlEl.dataset.editUrlTemplate, // 例: /admin-panel/rooms/0/edit/
};

/* =====================================================
   会議室フォームモーダル（追加 / 編集）
   ===================================================== */

/**
 * 会議室フォームモーダルを開く
 * @param {string} mode   'create' または 'edit'
 * @param {HTMLElement} [editBtn]  編集ボタン要素（mode='edit' 時に必要）
 */
function openRoomModal(mode, editBtn) {
  const modal = document.getElementById("roomFormModal");
  const form = document.getElementById("roomForm");
  const title = document.getElementById("roomFormTitle");

  // フォームを初期化（前回の値 / エラーをクリア）
  form.reset();
  modal.querySelectorAll(".error-text").forEach((el) => {
    el.textContent = "";
  });
  modal.querySelectorAll(".alert-danger").forEach((el) => {
    el.style.display = "none";
  });

  if (mode === "create") {
    title.textContent = "会議室を追加";
    form.action = ROOM_URL.create;

    // 全チェックボックスを未選択に戻す
    modal.querySelectorAll('input[name="facilities"]').forEach((cb) => {
      cb.checked = false;
    });
    modal.querySelectorAll('input[name="departments"]').forEach((cb) => {
      cb.checked = false;
    });
  } else {
    // ── 編集モード ──────────────────────────────────────
    title.textContent = "会議室を編集";

    // フォームの action URL を編集対象 pk で構築
    const roomId = editBtn.dataset.roomId;
    form.action = ROOM_URL.editTemplate.replace("/0/", "/" + roomId + "/");

    // テキスト / 数値フィールドの復元
    document.getElementById("id_name").value = editBtn.dataset.name || "";
    document.getElementById("id_capacity").value =
      editBtn.dataset.capacity || "";
    document.getElementById("id_floor").value = editBtn.dataset.floor || "";

    // 建物セレクトの復元
    document.getElementById("id_building").value =
      editBtn.dataset.buildingId || "";

    // 設備チェックボックスの復元
    const facilityIds = editBtn.dataset.facilityIds
      ? editBtn.dataset.facilityIds
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];
    modal.querySelectorAll('input[name="facilities"]').forEach((cb) => {
      cb.checked = facilityIds.includes(cb.value);
    });

    // 所属別表示設定チェックボックスの復元
    const deptIds = editBtn.dataset.departmentIds
      ? editBtn.dataset.departmentIds
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];
    modal.querySelectorAll('input[name="departments"]').forEach((cb) => {
      cb.checked = deptIds.includes(cb.value);
    });

    // カラーの復元
    const colorInput = document.getElementById("id_color");
    if (colorInput) colorInput.value = editBtn.dataset.color || "#3182CE";
  }

  modal.classList.add("open");
}

/** 会議室フォームモーダルを閉じる */
function closeRoomModal() {
  document.getElementById("roomFormModal").classList.remove("open");
}

/** オーバーレイクリックで会議室フォームモーダルを閉じる */
function closeRoomModalOnOverlay(event) {
  if (event.target === document.getElementById("roomFormModal")) {
    closeRoomModal();
  }
}

/* =====================================================
   削除確認モーダル（F-19）
   ===================================================== */

/**
 * 削除確認モーダルを開く
 * @param {HTMLElement} btn  削除ボタン要素（data-* 属性から情報を取得）
 */
function openDeleteModal(btn) {
  const name = btn.dataset.roomName;
  const count = parseInt(btn.dataset.reservationCount, 10);
  const url = btn.dataset.deleteUrl;

  document.getElementById("modalRoomName").textContent = name;
  document.getElementById("modalRoomName2").textContent = name;
  document.getElementById("deleteForm").action = url;

  const warning = document.getElementById("reservationWarning");
  if (count > 0) {
    document.getElementById("reservationCount").textContent = count;
    warning.style.display = "block";
  } else {
    warning.style.display = "none";
  }

  document.getElementById("deleteStep1").style.display = "block";
  document.getElementById("deleteStep2").style.display = "none";
  document.getElementById("deleteModal").classList.add("open");
}

/** 削除確認モーダルを閉じる */
function closeDeleteModal() {
  document.getElementById("deleteModal").classList.remove("open");
}

/** オーバーレイクリックで削除モーダルを閉じる */
function closeModalOnOverlay(event) {
  if (event.target === document.getElementById("deleteModal")) {
    closeDeleteModal();
  }
}

// 削除モーダル ステップ切り替え
document
  .getElementById("proceedToStep2")
  .addEventListener("click", function () {
    document.getElementById("deleteStep1").style.display = "none";
    document.getElementById("deleteStep2").style.display = "block";
  });

document.getElementById("backToStep1").addEventListener("click", function () {
  document.getElementById("deleteStep2").style.display = "none";
  document.getElementById("deleteStep1").style.display = "block";
});
