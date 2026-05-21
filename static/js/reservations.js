document.addEventListener("DOMContentLoaded", function () {
  initRoomSelect();
  initCancelModal();
  initErrorClear();
});

/* ===== 会議室選択 ===== */
function initRoomSelect() {
  const roomSelect = document.getElementById("roomSelect");
  if (!roomSelect) return;

  function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  function update() {
    const opt   = roomSelect.options[roomSelect.selectedIndex];
    const empty = !opt || !opt.value;

    if (empty) {
      const nameEl = document.getElementById("dispRoomName");
      if (nameEl) {
        nameEl.innerHTML = '<span class="selected-room-placeholder">会議室を選択してください</span>';
      }
      setText("dispRoomBuilding",    "");
      setText("dispRoomFloor",       "");
      setText("dispRoomCapacity",    "");
      setText("dispRoomFacilities",  "");
      setText("dispRoomDepartments", "");
      const colorEl = document.getElementById("dispRoomColor");
      if (colorEl) colorEl.textContent = "";
      return;
    }

    setText("dispRoomName",        opt.dataset.name        || "");
    setText("dispRoomBuilding",    opt.dataset.building    || "―");
    setText("dispRoomFloor",       opt.dataset.floor       ? opt.dataset.floor + "階" : "―");
    setText("dispRoomCapacity",    opt.dataset.capacity    ? opt.dataset.capacity + "名" : "―");
    setText("dispRoomFacilities",  opt.dataset.facilities  || "―");
    setText("dispRoomDepartments", opt.dataset.departments || "―");

    // カラー：スウォッチ＋テキスト
    const color   = opt.dataset.color || "#3182CE";
    const colorEl = document.getElementById("dispRoomColor");
    if (colorEl) {
      colorEl.innerHTML =
        `<span class="sri-color-swatch" style="background:${color};"></span>${color}`;
    }
  }

  roomSelect.addEventListener("change", update);
  update();
}

/* ===== キャンセルモーダル ===== */
function initCancelModal() {
  const openBtn = document.getElementById("openCancelModal");
  const closeBtn = document.getElementById("closeCancelModal");
  const modal = document.getElementById("cancelModal");

  if (!openBtn || !closeBtn || !modal) return;

  openBtn.addEventListener("click", () => {
    modal.hidden = false;
  });

  closeBtn.addEventListener("click", () => {
    modal.hidden = true;
  });

  modal.addEventListener("click", function (e) {
    if (e.target === modal) {
      modal.hidden = true;
    }
  });
}

/* ===== エラー削除 ===== */
function initErrorClear() {
  clearError('[name="title"]');
  clearError('[name="reserve_date"]');
  clearError("#roomSelect");
}

function clearError(selector) {
  const el = document.querySelector(selector);
  if (!el) return;

  el.addEventListener("input", function () {
    const block = el.closest(".field-block");
    if (!block) return;

    const error = block.querySelector(".field-error");
    const errorArea = block.querySelector(".field-error-area");

    if (error) error.remove();
    if (errorArea) errorArea.innerHTML = "";
  });
}
