const state = {
  meta: null,
  record: null,
  recordIndex: Number(localStorage.getItem("unipcb.recordIndex") || 0),
  qaIndex: Number(localStorage.getItem("unipcb.qaIndex") || 0),
  imageIndex: 0,
};

const els = {
  datasetLine: document.getElementById("datasetLine"),
  summary: document.getElementById("summary"),
  imageTabs: document.getElementById("imageTabs"),
  imageStage: document.getElementById("imageStage"),
  mainImage: document.getElementById("mainImage"),
  overlay: document.getElementById("overlay"),
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
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || response.statusText);
  }
  return payload;
}

async function loadMeta() {
  state.meta = await fetchJson("/api/meta");
  renderSummary();
}

async function loadRecord(recordIndex = state.recordIndex, qaIndex = 0) {
  state.recordIndex = clamp(recordIndex, 0, Math.max(0, (state.meta?.records || 1) - 1));
  state.record = await fetchJson(`/api/record/${state.recordIndex}`);
  state.qaIndex = clamp(qaIndex, 0, Math.max(0, state.record.conversation.length - 1));
  state.imageIndex = state.record.images.length > 1 ? 1 : 0;
  persistPosition();
  render();
}

function render() {
  renderSummary();
  renderHeader();
  renderImageTabs();
  renderQaList();
  renderQa();
  renderImage();
}

function renderSummary() {
  if (!state.meta) return;
  const parts = [
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
    btn.title = qa.type || "";
    btn.addEventListener("click", () => {
      state.qaIndex = index;
      if ((qa.boxes || []).length && state.record.images.length > 1) {
        state.imageIndex = 1;
      }
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
  els.mainImage.onload = drawBoxes;
  drawBoxes();
}

function drawBoxes() {
  const qa = currentQa();
  const boxes = qa?.boxes || [];
  const imageSize = state.record?.image_size || [];
  const naturalWidth = els.mainImage.naturalWidth || imageSize[0] || 0;
  const naturalHeight = els.mainImage.naturalHeight || imageSize[1] || 0;
  const rect = els.mainImage.getBoundingClientRect();
  const stageRect = els.imageStage.getBoundingClientRect();

  els.overlay.innerHTML = "";
  els.overlay.style.left = `${rect.left - stageRect.left + els.imageStage.scrollLeft}px`;
  els.overlay.style.top = `${rect.top - stageRect.top + els.imageStage.scrollTop}px`;
  els.overlay.setAttribute("width", rect.width);
  els.overlay.setAttribute("height", rect.height);
  els.overlay.setAttribute("viewBox", `0 0 ${rect.width} ${rect.height}`);

  if (!boxes.length || !naturalWidth || !naturalHeight || !rect.width || !rect.height) return;

  const sx = rect.width / naturalWidth;
  const sy = rect.height / naturalHeight;
  boxes.forEach((box, index) => {
    const x = Math.min(box.x1, box.x2) * sx;
    const y = Math.min(box.y1, box.y2) * sy;
    const width = Math.abs(box.x2 - box.x1) * sx;
    const height = Math.abs(box.y2 - box.y1) * sy;
    const group = svgEl("g");
    const rectEl = svgEl("rect", {
      x,
      y,
      width,
      height,
      fill: "rgba(255, 204, 0, 0.08)",
      stroke: "var(--mark)",
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
  const payload = {
    record_index: state.record.record_index,
    qa_index: qa.qa_index,
    status,
    note,
  };
  const result = await fetchJson("/api/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  state.meta = result.summary;
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
  await loadRecord(state.recordIndex, state.qaIndex);
}

async function goNext() {
  if (state.qaIndex + 1 < state.record.conversation.length) {
    state.qaIndex += 1;
    if ((currentQa().boxes || []).length && state.record.images.length > 1) {
      state.imageIndex = 1;
    }
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
    if ((currentQa().boxes || []).length && state.record.images.length > 1) {
      state.imageIndex = 1;
    }
    persistPosition();
    render();
    return;
  }
  if (state.recordIndex > 0) {
    const previous = await fetchJson(`/api/record/${state.recordIndex - 1}`);
    state.record = previous;
    state.recordIndex -= 1;
    state.qaIndex = Math.max(0, previous.conversation.length - 1);
    state.imageIndex = previous.images.length > 1 ? 1 : 0;
    persistPosition();
    render();
  }
}

function currentQa() {
  return state.record.conversation[state.qaIndex];
}

function persistPosition() {
  localStorage.setItem("unipcb.recordIndex", String(state.recordIndex));
  localStorage.setItem("unipcb.qaIndex", String(state.qaIndex));
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
els.problemBtn.addEventListener("click", () => saveReview("problem"));
els.okBtn.addEventListener("click", () => saveReview("ok"));
els.clearBtn.addEventListener("click", clearReview);
window.addEventListener("resize", drawBoxes);
els.imageStage.addEventListener("scroll", drawBoxes);

(async function init() {
  try {
    await loadMeta();
    await loadRecord(state.recordIndex, state.qaIndex);
  } catch (error) {
    els.datasetLine.textContent = `加载失败：${error.message}`;
  }
})();
