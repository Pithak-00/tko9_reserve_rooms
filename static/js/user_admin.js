/* =====================================================
   user_admin.js
   ユーザー管理画面（S-08）専用スクリプト
   ===================================================== */

"use strict";

// ── URL 定数（HTML の data 属性から取得） ───────────────────
const _userUrlEl = document.getElementById("js-user-urls");
const USER_URL = {
  create: _userUrlEl.dataset.createUrl,
  editTemplate: _userUrlEl.dataset.editUrlTemplate,       // 例: /admin-panel/users/0/edit/
  pwResetTemplate: _userUrlEl.dataset.pwResetUrlTemplate, // 例: /admin-panel/users/0/reset-password/
};

/* =====================================================
   ユーザーフォームモーダル（追加 / 編集）
   ===================================================== */

/**
 * ユーザーフォームモーダルを開く
 * @param {string}      mode     'create' または 'edit'
 * @param {HTMLElement} [editBtn] 編集ボタン要素（mode='edit' 時に必要）
 */
function openUserModal(mode, editBtn) {
  const modal = document.getElementById("userFormModal");
  const form = document.getElementById("userForm");
  const title = document.getElementById("userFormTitle");
  const submitBtn = document.getElementById("userFormSubmit");
  const divInput = document.getElementById("div-login-id-input");
  const divDisplay = document.getElementById("div-login-id-display");
  const loginIdText = document.getElementById("login-id-text");

  // 前回のエラー表示をクリア
  modal.querySelectorAll(".error-text").forEach((el) => {
    el.textContent = "";
  });
  modal.querySelectorAll(".alert-danger").forEach((el) => {
    el.style.display = "none";
  });

  if (mode === "create") {
    title.textContent = "ユーザーを追加";
    submitBtn.textContent = "追加";
    form.action = USER_URL.create;

    // login_id: 入力欄を表示、表示欄を非表示
    divInput.style.display = "";
    divDisplay.style.display = "none";

    // フィールドをクリア
    const loginIdInput = document.getElementById("id_modal_login_id");
    if (loginIdInput) loginIdInput.value = "";
    document.getElementById("id_name").value = "";
    document.getElementById("id_role").value = "user";
    document.getElementById("id_department").value = "";
  } else {
    // ── 編集モード ──────────────────────────────────────
    const userId = editBtn.dataset.userId;
    const loginId = editBtn.dataset.loginId;
    const name = editBtn.dataset.name;
    const role = editBtn.dataset.role;
    const deptId = editBtn.dataset.departmentId;

    title.textContent = "ユーザーを編集";
    submitBtn.textContent = "保存する";
    form.action = USER_URL.editTemplate.replace("/0/", "/" + userId + "/");

    // login_id: 入力欄を非表示、表示欄を表示
    divInput.style.display = "none";
    divDisplay.style.display = "";
    loginIdText.textContent = loginId;

    // フィールドに現在値をセット
    document.getElementById("id_name").value = name;
    document.getElementById("id_role").value = role;
    document.getElementById("id_department").value = deptId || "";
  }

  modal.classList.add("open");
}

/** ユーザーフォームモーダルを閉じる */
function closeUserModal() {
  document.getElementById("userFormModal").classList.remove("open");
}

/** オーバーレイクリックでモーダルを閉じる */
function closeUserModalOnOverlay(event) {
  if (event.target === document.getElementById("userFormModal")) {
    closeUserModal();
  }
}

/* =====================================================
   パスワードリセットモーダル
   ===================================================== */

/**
 * パスワードリセットモーダルを開く
 * @param {number} userId  対象ユーザーの pk
 * @param {string} userName 対象ユーザーの氏名
 */
function openPasswordResetModal(userId, userName) {
  const modal = document.getElementById("passwordResetModal");
  const form  = document.getElementById("passwordResetForm");

  // フォームの action を対象ユーザーの URL に設定
  form.action = USER_URL.pwResetTemplate.replace("/0/", "/" + userId + "/");

  // 対象ユーザー名を表示
  document.getElementById("passwordResetTarget").textContent =
    "対象ユーザー：" + userName;

  // フィールドとエラーをリセット
  document.getElementById("id_new_password").value = "";
  document.getElementById("id_confirm_password").value = "";
  ["err_new_password", "err_confirm_password", "passwordResetErrors"].forEach(function (id) {
    const el = document.getElementById(id);
    if (el) { el.textContent = ""; el.style.display = "none"; }
  });

  modal.classList.add("open");
}

/** パスワードリセットモーダルを閉じる */
function closePasswordResetModal() {
  document.getElementById("passwordResetModal").classList.remove("open");
}

/** オーバーレイクリックで閉じる */
function closePasswordResetModalOnOverlay(event) {
  if (event.target === document.getElementById("passwordResetModal")) {
    closePasswordResetModal();
  }
}

/** クライアントサイドバリデーション（送信前チェック） */
document.getElementById("passwordResetForm").addEventListener("submit", function (e) {
  const pw      = document.getElementById("id_new_password").value;
  const confirm = document.getElementById("id_confirm_password").value;
  let hasError  = false;

  const errPw  = document.getElementById("err_new_password");
  const errCon = document.getElementById("err_confirm_password");
  errPw.textContent  = ""; errPw.style.display  = "none";
  errCon.textContent = ""; errCon.style.display = "none";

  if (pw.length < 8) {
    errPw.textContent = "パスワードは8文字以上で入力してください。";
    errPw.style.display = "block";
    hasError = true;
  }
  if (pw !== confirm) {
    errCon.textContent = "パスワードが一致しません。";
    errCon.style.display = "block";
    hasError = true;
  }

  if (hasError) e.preventDefault();
});
