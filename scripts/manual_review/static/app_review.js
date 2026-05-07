const DEFAULT_REVIEWER = "reviewer1";
const RECORD_PAGE_SIZE = 240;
const ZOOM_MODES = ["actual", "fit", "double"];

const state = {
  meta: null,
  records: [],
  record: null,
  recordsTotal: 0,
  recordOffset: Number(localStorage.getItem("unipcb.recordOffset") || 0),
  reviewer: localStorage.getItem("unipcb.reviewer") || DEFAULT_REVIEWER,
  recordIndex: Number(localStorage.getItem("unipcb.recordIndex") || 0),
  qaIndex: Number(localStorage.getItem("unipcb.qaIndex") || 0),
  imageIndex: 0,
  zoomMode: "actual",
};

const els = {
  datasetLine: document.getElementById("datasetLine"),
  summary: document.getElementById("summary"),
  reviewerInput: document.getElementById("reviewerInput"),
  switchReviewerBtn: document.getElementById("switchReviewerBtn"),
  recordInput: document.getElementById("recordInput"),
  jumpRecordBtn: document.getElementById("jumpRecordBtn"),
  prevPageBtn: document.getElementById("prevPageBtn"),
  nextPageBtn: document.getElementById("nextPageBtn"),
  recordPageText: document.getElementById("recordPageText"),
  recordGrid: document.getElementById("recordGrid"),
  imageTabs: document.getElementById("imageTabs"),
  imageStage: document.getElementById("imageStage"),
  imageCanvas: document.getElementById("imageCanvas"),
  mainImage: document.getElementById("mainImage"),
  overlay: document.getElementById("overlay"),
  zoomHint: document.getElementById("zoomHint"),
  prevBtn: document.getElementById("prevBtn"),
  nextBtn: document.getElementById("nextBtn"),
  progressText: document.getElementById("progressText"),
  qaList: document.getElementById("qaList"),
  typeLine: document.getElementById("typeLine"),
  questionText: document.getElementById("questionText"),
  correctOption: document.getElementById("correctOption"),
  optionsBlock: document.getElementById("optionsBlock"),
  optionsList: document.getElementById("optionsList"),
  boxesBlock: document.getElementById("boxesBlock"),
  boxesList: document.getElementById("boxesList"),
  noteInput: document.getElementById("noteInput"),
  problemBtn: document.getElementById("problemBtn"),
  okBtn: document.getElementById("okBtn"),
  clearBtn: document.getElementById("clearBtn"),
  statusLine: document.getElementById("statusLine"),
};

async function fetchJson(url, options) {
  const response = await fetch(urlWithReviewer(url), options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || response.statusText);
  }
  return payload;
}

function urlWithReviewer(url) {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}reviewer=${encodeURIComponent(state.reviewer)}`;
}

async function loadMeta() {
  state.meta = await fetchJson("/api/meta");
  renderSummary();
}

async function loadRecords() {
  state.recordOffset = clamp(
    state.recordOffset,
    0,
    maxRecordOffset(),
  );
  const payload = await fetchJson(`/api/records?offset=${state.recordOffset}&limit=${RECORD_PAGE_SIZE}`);
  state.records = payload.records || [];
  state.recordsTotal = payload.total || state.meta?.records || state.records.length;
  state.meta = payload.summary || state.meta;
  localStorage.setItem("unipcb.recordOffset", String(state.recordOffset));
  renderSummary();
  renderRecordGrid();
}

async function loadRecord(recordIndex = state.recordIndex, qaIndex = 0) {
  state.recordIndex = clamp(recordIndex, 0, Math.max(0, (state.meta?.records || 1) - 1));
  state.record = await fetchJson(`/api/record/${state.recordIndex}`);
  state.qaIndex = clamp(qaIndex, 0, Math.max(0, state.record.conversation.length - 1));
  state.imageIndex = preferredImageIndex();
  state.zoomMode = "actual";
  ensureRecordPageContains(state.recordIndex);
  persistPosition();
  render();
}

function render() {
  renderSummary();
  renderHeader();
  renderRecordGrid();
  renderImageTabs();
  renderQaList();
  renderQa();
  renderImage();
}

function renderSummary() {
  if (!state.meta) return;
  const parts = [
    `审核人 ${state.meta.reviewer || state.reviewer}`,
    `记录 ${state.meta.records}`,
    `问答 ${state.meta.qa_total}`,
    `已审 ${state.meta.reviewed}`,
    `正常 ${state.meta.ok}`,
    `问题 ${state.meta.problem}`,
  ];
  els.summary.innerHTML = parts.map((part) => `<span>${escapeHtml(part)}</span>`).join("");
}

function renderHeader() {
  const r = state.record;
  els.datasetLine.textContent = `${r.dataset || "-"} / ${r.dataset_type || "-"} / ${r.language || "-"} / ${r.image_size?.join(" x ") || "-"}`;
  els.progressText.textContent = `图像 ${r.record_index + 1}/${r.record_count} · 问答 ${state.qaIndex + 1}/${r.conversation.length}`;
  els.recordInput.value = String(r.record_index + 1);
  els.prevBtn.disabled = r.record_index === 0 && state.qaIndex === 0;
  els.nextBtn.disabled = r.record_index + 1 === r.record_count && state.qaIndex + 1 === r.conversation.length;
}

function renderRecordGrid() {
  if (!state.records.length) return;
  const activeIndex = state.record?.record_index ?? state.recordIndex;
  const pageStart = state.recordOffset + 1;
  const pageEnd = Math.min(state.recordOffset + RECORD_PAGE_SIZE, state.recordsTotal || state.meta?.records || 0);
  els.recordPageText.textContent = `${pageStart}-${pageEnd}`;
  els.prevPageBtn.disabled = state.recordOffset <= 0;
  els.nextPageBtn.disabled = pageEnd >= (state.recordsTotal || 0);
  els.recordGrid.innerHTML = "";
  state.records.forEach((record) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(record.record_index + 1);
    btn.className = [record.status, record.record_index === activeIndex ? "active" : ""].join(" ");
    btn.title = `${record.dataset || "-"} / ${record.language || "-"} / ${record.reviewed}/${record.qa_total}`;
    btn.addEventListener("click", () => loadRecord(record.record_index, 0));
    els.recordGrid.appendChild(btn);
  });
}

function renderImageTabs() {
  els.imageTabs.innerHTML = "";
  state.record.images.forEach((image, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = index === state.imageIndex ? "active" : "";
    btn.textContent = `${index + 1}. ${image.path.split("/").slice(-2).join("/")}${image.exists ? "" : " (缺失)"}`;
    btn.addEventListener("click", () => {
      state.imageIndex = index;
      state.zoomMode = "actual";
      renderImage();
      renderImageTabs();
    });
    els.imageTabs.appendChild(btn);
  });
}

function renderQaList() {
  els.qaList.innerHTML = "";
  state.record.conversation.forEach((qa, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = String(index + 1);
    btn.className = [index === state.qaIndex ? "active" : "", qa.review?.status || ""].join(" ");
    btn.title = `${qa.type || ""}${qa.review?.note ? `: ${qa.review.note}` : ""}`;
    btn.addEventListener("click", () => {
      state.qaIndex = index;
      state.imageIndex = preferredImageIndex(qa);
      state.zoomMode = "actual";
      persistPosition();
      render();
    });
    els.qaList.appendChild(btn);
  });
}

function renderQa() {
  const qa = currentQa();
  els.typeLine.textContent = qa.type || "-";
  els.questionText.textContent = qa.question || "";
  els.correctOption.textContent = qa.correct_option || "";
  els.noteInput.value = qa.review?.note || "";
  els.statusLine.textContent = qa.review ? `当前状态：${qa.review.status === "ok" ? "无问题" : "存在问题"}` : "当前状态：未审核";

  if (Array.isArray(qa.options) && qa.options.length) {
    els.optionsBlock.hidden = false;
    els.optionsList.innerHTML = "";
    qa.options.forEach((option) => {
      const div = document.createElement("div");
      div.className = option.startsWith(`${qa.correct_answer_letter}.`) ? "option correct" : "option";
      div.textContent = option;
      els.optionsList.appendChild(div);
    });
  } else {
    els.optionsBlock.hidden = true;
  }

  if (Array.isArray(qa.boxes) && qa.boxes.length) {
    els.boxesBlock.hidden = false;
    els.boxesList.innerHTML = "";
    qa.boxes.forEach((box, index) => {
      const div = document.createElement("div");
      div.className = "boxItem";
      div.textContent = `${index + 1}. ${box.label}: [${box.x1}, ${box.y1}, ${box.x2}, ${box.y2}]`;
      els.boxesList.appendChild(div);
    });
  } else {
    els.boxesBlock.hidden = true;
  }
}

function renderImage() {
  const image = state.record.images[state.imageIndex];
  els.mainImage.src = image ? image.url : "";
  els.mainImage.onload = () => {
    applyZoom();
    drawBoxes();
  };
  applyZoom();
  drawBoxes();
}

function applyZoom() {
  const naturalWidth = els.mainImage.naturalWidth || state.record?.image_size?.[0] || 1;
  const naturalHeight = els.mainImage.naturalHeight || state.record?.image_size?.[1] || 1;
  const stage = els.imageStage.getBoundingClientRect();
  const fitScale = Math.min(stage.width / naturalWidth, stage.height / naturalHeight, 1);
  const scale = state.zoomMode === "actual" ? 1 : state.zoomMode === "double" ? 2 : fitScale;
  const width = Math.max(1, Math.round(naturalWidth * scale));
  const height = Math.max(1, Math.round(naturalHeight * scale));

  els.imageCanvas.style.width = `${width}px`;
  els.imageCanvas.style.height = `${height}px`;
  els.mainImage.style.width = `${width}px`;
  els.mainImage.style.height = `${height}px`;
  els.overlay.style.width = `${width}px`;
  els.overlay.style.height = `${height}px`;
  els.overlay.setAttribute("width", width);
  els.overlay.setAttribute("height", height);
  els.overlay.setAttribute("viewBox", `0 0 ${width} ${height}`);
  els.mainImage.style.cursor = state.zoomMode === "double" ? "zoom-out" : "zoom-in";
  els.zoomHint.textContent = `缩放：${zoomLabel()} · 点击图像切换`;
}

function drawBoxes() {
  const qa = currentQa();
  const boxes = qa?.boxes || [];
  const naturalWidth = els.mainImage.naturalWidth || state.record?.image_size?.[0] || 0;
  const naturalHeight = els.mainImage.naturalHeight || state.record?.image_size?.[1] || 0;
  const width = els.mainImage.clientWidth;
  const height = els.mainImage.clientHeight;

  els.overlay.innerHTML = "";
  if (!boxes.length || !naturalWidth || !naturalHeight || !width || !height) return;

  const sx = width / naturalWidth;
  const sy = height / naturalHeight;
  boxes.forEach((box, index) => {
    const x = Math.min(box.x1, box.x2) * sx;
    const y = Math.min(box.y1, box.y2) * sy;
    const boxWidth = Math.abs(box.x2 - box.x1) * sx;
    const boxHeight = Math.abs(box.y2 - box.y1) * sy;
    const group = svgEl("g");
    const rectEl = svgEl("rect", {
      x,
      y,
      width: boxWidth,
      height: boxHeight,
      fill: "rgba(255, 204, 0, 0.08)",
      stroke: "#ffcc00",
      "stroke-width": 2,
    });
    const labelBg = svgEl("rect", {
      x,
      y: Math.max(0, y - 22),
      width: Math.max(42, String(box.label).length * 8 + 24),
      height: 22,
      fill: "rgba(17, 24, 32, 0.82)",
    });
    const text = svgEl("text", {
      x: x + 6,
      y: Math.max(16, y - 7),
      fill: "#fff",
      "font-size": 13,
      "font-family": "system-ui, sans-serif",
    });
    text.textContent = `${index + 1} ${box.label}`;
    group.append(rectEl, labelBg, text);
    els.overlay.appendChild(group);
  });
}

async function saveReview(status) {
  const qa = currentQa();
  const note = els.noteInput.value.trim();
  if (status === "problem" && !note) {
    els.statusLine.textContent = "请先填写问题说明。";
    els.noteInput.focus();
    return;
  }
  const result = await fetchJson("/api/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      record_index: state.record.record_index,
      qa_index: qa.qa_index,
      status,
      note,
    }),
  });
  state.meta = result.summary;
  ensureRecordPageContains(state.recordIndex);
  await loadRecords();
  await loadRecord(state.recordIndex, state.qaIndex);
  if (status === "ok") {
    await goNext();
  }
}

async function clearReview() {
  const qa = currentQa();
  const result = await fetchJson("/api/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      record_index: state.record.record_index,
      qa_index: qa.qa_index,
      status: "unreviewed",
      note: "",
    }),
  });
  state.meta = result.summary;
  ensureRecordPageContains(state.recordIndex);
  await loadRecords();
  await loadRecord(state.recordIndex, state.qaIndex);
}

async function goNext() {
  if (state.qaIndex + 1 < state.record.conversation.length) {
    state.qaIndex += 1;
    state.imageIndex = preferredImageIndex();
    state.zoomMode = "actual";
    persistPosition();
    render();
    return;
  }
  if (state.recordIndex + 1 < state.record.record_count) {
    await loadRecord(state.recordIndex + 1, 0);
  }
}

async function goPrev() {
  if (state.qaIndex > 0) {
    state.qaIndex -= 1;
    state.imageIndex = preferredImageIndex();
    state.zoomMode = "actual";
    persistPosition();
    render();
    return;
  }
  if (state.recordIndex > 0) {
    const previous = await fetchJson(`/api/record/${state.recordIndex - 1}`);
    state.record = previous;
    state.recordIndex -= 1;
    state.qaIndex = Math.max(0, previous.conversation.length - 1);
    state.imageIndex = preferredImageIndex();
    state.zoomMode = "actual";
    persistPosition();
    render();
  }
}

async function jumpRecord() {
  const target = Number(els.recordInput.value) - 1;
  if (Number.isFinite(target)) {
    ensureRecordPageContains(target);
    await loadRecords();
    await loadRecord(target, 0);
  }
}

async function changeRecordPage(direction) {
  state.recordOffset = clamp(
    state.recordOffset + direction * RECORD_PAGE_SIZE,
    0,
    maxRecordOffset(),
  );
  await loadRecords();
}

async function switchReviewer() {
  const next = els.reviewerInput.value.trim() || DEFAULT_REVIEWER;
  state.reviewer = next;
  localStorage.setItem("unipcb.reviewer", next);
  await loadMeta();
  await loadRecords();
  await loadRecord(state.recordIndex, state.qaIndex);
}

function cycleZoom() {
  const current = ZOOM_MODES.indexOf(state.zoomMode);
  state.zoomMode = ZOOM_MODES[(current + 1) % ZOOM_MODES.length];
  applyZoom();
  drawBoxes();
}

function ensureRecordPageContains(recordIndex) {
  if (recordIndex < state.recordOffset || recordIndex >= state.recordOffset + RECORD_PAGE_SIZE) {
    state.recordOffset = Math.floor(recordIndex / RECORD_PAGE_SIZE) * RECORD_PAGE_SIZE;
    localStorage.setItem("unipcb.recordOffset", String(state.recordOffset));
  }
}

function maxRecordOffset() {
  const total = state.recordsTotal || state.meta?.records || 1;
  return Math.floor(Math.max(0, total - 1) / RECORD_PAGE_SIZE) * RECORD_PAGE_SIZE;
}

function preferredImageIndex(qa = currentQa()) {
  if ((qa?.boxes || []).length && state.record.images.length > 1) {
    return 1;
  }
  return state.record.images.length > 1 ? 1 : 0;
}

function zoomLabel() {
  if (state.zoomMode === "actual") return "原始尺寸";
  if (state.zoomMode === "double") return "2倍";
  return "适应窗口";
}

function currentQa() {
  return state.record.conversation[state.qaIndex];
}

function persistPosition() {
  localStorage.setItem("unipcb.recordIndex", String(state.recordIndex));
  localStorage.setItem("unipcb.qaIndex", String(state.qaIndex));
  localStorage.setItem("unipcb.recordOffset", String(state.recordOffset));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function svgEl(name, attrs = {}) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  return el;
}

els.prevBtn.addEventListener("click", goPrev);
els.nextBtn.addEventListener("click", goNext);
els.jumpRecordBtn.addEventListener("click", jumpRecord);
els.prevPageBtn.addEventListener("click", () => changeRecordPage(-1));
els.nextPageBtn.addEventListener("click", () => changeRecordPage(1));
els.recordInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") jumpRecord();
});
els.switchReviewerBtn.addEventListener("click", switchReviewer);
els.reviewerInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") switchReviewer();
});
els.problemBtn.addEventListener("click", () => saveReview("problem"));
els.okBtn.addEventListener("click", () => saveReview("ok"));
els.clearBtn.addEventListener("click", clearReview);
els.mainImage.addEventListener("click", cycleZoom);
window.addEventListener("resize", () => {
  applyZoom();
  drawBoxes();
});

(async function init() {
  try {
    els.reviewerInput.value = state.reviewer;
    await loadMeta();
    await loadRecords();
    await loadRecord(state.recordIndex, state.qaIndex);
  } catch (error) {
    els.datasetLine.textContent = `加载失败：${error.message}`;
  }
})();
