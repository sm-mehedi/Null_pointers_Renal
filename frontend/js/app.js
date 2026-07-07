const API_BASE = (window.KIDNEY_AI_CONFIG && window.KIDNEY_AI_CONFIG.API_BASE_URL) || "";
const state = { name: "", phone: "", file: null, isAnalyzing: false, page: 1, pageSize: 10, total: 0 };
const diseaseCopy = {
  "Normal": "No kidney disease pattern was predicted by the AI model for this scan.",
  "Kidney Stone": "The model detected visual patterns consistent with kidney stone cases in the training classes.",
  "Kidney Cyst": "The model detected cyst-like visual patterns in the CT scan class output.",
  "Kidney Tumor": "The model detected tumor-like visual patterns in the CT scan class output. Clinical review is essential."
};
const $ = (id) => document.getElementById(id);

function showToast(message, type = "info") {
  const toast = $("toast");
  toast.textContent = message;
  toast.style.background = type === "error" ? "#dc2626" : type === "success" ? "#0f766e" : "#102033";
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3200);
}

function api(path) { return `${API_BASE}${path}`; }
function setStep(step) {
  ["stepOnePill", "stepTwoPill", "stepThreePill"].forEach((id, index) => $(id).classList.toggle("active", index + 1 === step));
}
function resetSessionUi() {
  state.name = ""; state.phone = ""; state.file = null; state.isAnalyzing = false;
  $("patientForm").reset(); $("uploadForm").reset();
  $("uploadForm").classList.add("hidden"); $("previewWrap").classList.add("hidden");
  $("resultCard").classList.add("hidden"); $("loadingState").classList.add("hidden");
  setStep(1);
}
function validatePhone(phone) { return /^\+?[0-9][0-9\-\s()]{6,30}$/.test(phone.trim()); }
function validateImage(file) {
  if (!file) return "Choose a CT image first.";
  if (!["image/jpeg", "image/png"].includes(file.type)) return "Only JPG, JPEG, and PNG images are supported.";
  if (file.size > 10 * 1024 * 1024) return "Image must be 10MB or smaller.";
  return "";
}
function renderPreview(file) {
  const reader = new FileReader();
  reader.onload = () => { $("previewImage").src = reader.result; $("previewWrap").classList.remove("hidden"); };
  reader.readAsDataURL(file);
}
function setFile(file) {
  const error = validateImage(file);
  if (error) { showToast(error, "error"); return; }
  state.file = file;
  renderPreview(file);
}
function downloadDataUrl(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}
function renderProbabilities(probabilities) {
  const container = $("probabilityBars");
  container.innerHTML = "";
  Object.entries(probabilities).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "prob-row";
    row.innerHTML = `<strong>${label}</strong><div class="bar"><span style="width:${Math.max(0, Math.min(100, value))}%"></span></div><span>${value.toFixed(2)}%</span>`;
    container.appendChild(row);
  });
}
function renderResult(data) {
  $("diseaseName").textContent = data.prediction;
  $("confidenceBadge").textContent = `${data.confidence.toFixed(2)}%`;
  $("originalResultImage").src = data.original_image;
  $("heatmapResultImage").src = data.heatmap_image;
  $("predictionTime").textContent = new Date(data.timestamp).toLocaleString();
  $("modelName").textContent = data.model_name;
  $("diseaseCard").textContent = diseaseCopy[data.prediction] || "The model generated a prediction for this CT image.";
  $("downloadOriginal").onclick = () => downloadDataUrl(data.original_image, "original-ct-scan.png");
  $("downloadHeatmap").onclick = () => downloadDataUrl(data.heatmap_image, "gradcam-heatmap.png");
  renderProbabilities(data.probabilities);
  $("resultCard").classList.remove("hidden");
  setStep(3);
}
async function analyze(event) {
  event.preventDefault();
  if (state.isAnalyzing) return;
  const error = validateImage(state.file);
  if (error) { showToast(error, "error"); return; }
  state.isAnalyzing = true;
  $("loadingState").classList.remove("hidden");
  $("resultCard").classList.add("hidden");
  $("analyzeButton").disabled = true;
  const form = new FormData();
  form.append("name", state.name); form.append("phone", state.phone); form.append("file", state.file);
  try {
    const response = await fetch(api("/api/predict"), { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Prediction failed.");
    renderResult(payload); showToast("Prediction saved to database.", "success");
  } catch (error) {
    showToast(error.message || "Internet or server error.", "error");
  } finally {
    state.isAnalyzing = false; $("loadingState").classList.add("hidden"); $("analyzeButton").disabled = false;
  }
}
async function loadHistory() {
  const search = encodeURIComponent($("historySearch").value.trim());
  const response = await fetch(api(`/api/history?page=${state.page}&page_size=${state.pageSize}&search=${search}`));
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Could not load history.");
  state.total = data.total;
  const body = $("historyBody"); body.innerHTML = "";
  if (!data.items.length) body.innerHTML = `<tr><td colspan="6">No records found.</td></tr>`;
  data.items.forEach((item) => {
    const date = new Date(item.timestamp);
    const row = document.createElement("tr");
    row.innerHTML = `<td>${item.name}</td><td>${item.phone}</td><td>${item.prediction}</td><td>${item.confidence.toFixed(2)}%</td><td>${date.toLocaleDateString()}</td><td>${date.toLocaleTimeString()}</td>`;
    body.appendChild(row);
  });
  const pages = Math.max(1, Math.ceil(state.total / state.pageSize));
  $("pageInfo").textContent = `Page ${state.page} of ${pages}`;
  $("prevPage").disabled = state.page <= 1;
  $("nextPage").disabled = state.page >= pages;
}
async function loadSamples() {
  const grid = $("sampleGrid"); grid.innerHTML = "";
  try {
    const response = await fetch(api("/api/sample-images"));
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not load sample images.");
    data.categories.forEach((category) => {
      const card = document.createElement("article");
      card.className = "sample-card glass-panel";
      const preview = category.preview
        ? `<img src="${api(category.preview)}" alt="${category.label} CT sample preview" loading="lazy" />`
        : `<span>CT</span>`;
      const files = category.files.length
        ? category.files.slice(0, 8).map((file) => `<a href="${api(file.download_url)}" download>${file.name}</a>`).join("")
        : "<span>No sample files placed yet.</span>";
      const archiveButton = category.archive_url
        ? `<a class="button secondary sample-zip" href="${api(category.archive_url)}" download>Download ${category.label} ZIP</a>`
        : `<span class="sample-note">ZIP will appear after samples are added.</span>`;
      card.innerHTML = `
        <div class="sample-preview">${preview}</div>
        <div class="sample-card-head">
          <h3>${category.label}</h3>
          <span>${category.count} image${category.count === 1 ? "" : "s"}</span>
        </div>
        <p>${category.description}</p>
        <div class="sample-actions">${archiveButton}</div>
        <div class="sample-files">${files}</div>
      `;
      grid.appendChild(card);
    });
  } catch (error) {
    showToast(error.message, "error");
  }
}
function activateSection(id) {
  document.querySelectorAll(".page-section").forEach((section) => section.classList.toggle("active-section", section.id === id));
  document.querySelectorAll(".nav-link").forEach((link) => link.classList.toggle("active", link.dataset.section === id));
  $("navMenu").classList.remove("open");
  if (id === "history") loadHistory().catch((error) => showToast(error.message, "error"));
  if (id === "samples") loadSamples();
}

document.addEventListener("DOMContentLoaded", () => {
  resetSessionUi();
  $("patientForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const name = $("nameInput").value.trim(); const phone = $("phoneInput").value.trim();
    if (name.length < 2) return showToast("Enter the patient name.", "error");
    if (!validatePhone(phone)) return showToast("Enter a valid phone number.", "error");
    state.name = name; state.phone = phone; $("uploadForm").classList.remove("hidden"); setStep(2);
  });
  $("browseButton").addEventListener("click", () => $("fileInput").click());
  $("fileInput").addEventListener("change", (event) => setFile(event.target.files[0]));
  ["dragenter", "dragover"].forEach((name) => $("dropZone").addEventListener(name, (event) => { event.preventDefault(); $("dropZone").classList.add("drag-over"); }));
  ["dragleave", "drop"].forEach((name) => $("dropZone").addEventListener(name, (event) => { event.preventDefault(); $("dropZone").classList.remove("drag-over"); }));
  $("dropZone").addEventListener("drop", (event) => setFile(event.dataTransfer.files[0]));
  $("removeImageButton").addEventListener("click", () => { state.file = null; $("fileInput").value = ""; $("previewWrap").classList.add("hidden"); });
  $("uploadForm").addEventListener("submit", analyze);
  document.querySelectorAll(".nav-link").forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); activateSection(link.dataset.section || "home"); }));
  $("menuToggle").addEventListener("click", () => $("navMenu").classList.toggle("open"));
  $("themeToggle").addEventListener("click", () => document.body.classList.toggle("dark"));
  $("historySearchButton").addEventListener("click", () => { state.page = 1; loadHistory().catch((error) => showToast(error.message, "error")); });
  $("historySearch").addEventListener("keydown", (event) => { if (event.key === "Enter") { state.page = 1; loadHistory().catch((error) => showToast(error.message, "error")); } });
  $("prevPage").addEventListener("click", () => { if (state.page > 1) { state.page -= 1; loadHistory().catch((error) => showToast(error.message, "error")); } });
  $("nextPage").addEventListener("click", () => { if (state.page * state.pageSize < state.total) { state.page += 1; loadHistory().catch((error) => showToast(error.message, "error")); } });
  $("downloadAllSamples").addEventListener("click", () => { window.location.href = api("/api/sample-images/download-all"); });
});

