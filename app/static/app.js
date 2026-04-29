const state = {
  documentId: null,
  filename: null,
};

const elements = {
  aiBaseUrl: document.querySelector("#aiBaseUrl"),
  aiConfigured: document.querySelector("#aiConfigured"),
  aiLastCall: document.querySelector("#aiLastCall"),
  aiModel: document.querySelector("#aiModel"),
  chatLog: document.querySelector("#chatLog"),
  chunkCount: document.querySelector("#chunkCount"),
  currentDocument: document.querySelector("#currentDocument"),
  documentCount: document.querySelector("#documentCount"),
  fileName: document.querySelector("#fileName"),
  pdfInput: document.querySelector("#pdfInput"),
  queryInput: document.querySelector("#queryInput"),
  refreshButton: document.querySelector("#refreshButton"),
  reportForm: document.querySelector("#reportForm"),
  topicCount: document.querySelector("#topicCount"),
  topicState: document.querySelector("#topicState"),
  topicsList: document.querySelector("#topicsList"),
  uploadButton: document.querySelector("#uploadButton"),
  uploadState: document.querySelector("#uploadState"),
};

elements.pdfInput.addEventListener("change", () => {
  const file = elements.pdfInput.files[0];
  elements.fileName.textContent = file ? file.name : "Choose a PDF file";
});

elements.uploadButton.addEventListener("click", uploadDocument);
elements.refreshButton.addEventListener("click", refreshDashboard);
elements.reportForm.addEventListener("submit", createReport);

init();

async function init() {
  await Promise.all([refreshAiStatus(), refreshDashboard()]);
}

async function uploadDocument() {
  const file = elements.pdfInput.files[0];
  if (!file) {
    setState(elements.uploadState, "Choose file", "warn");
    return;
  }

  setBusy(elements.uploadButton, true);
  setState(elements.uploadState, "Uploading", "");

  try {
    const formData = new FormData();
    formData.append("file", file);

    const document = await request("/v1/documents", {
      method: "POST",
      body: formData,
    });

    state.documentId = document.document_id;
    state.filename = document.filename;
    elements.currentDocument.textContent = `${document.filename} (${document.document_id})`;
    setState(
      elements.uploadState,
      document.agent?.agent_used === "llm" ? "AI parsed" : "Fallback parsed",
      document.agent?.agent_used === "llm" ? "ok" : "warn",
    );

    addMessage("assistant", `업로드 완료: ${document.filename}\n문서 ID: ${document.document_id}`);
    await Promise.all([loadTopics(document.document_id), refreshDashboard(), refreshAiStatus()]);
  } catch (error) {
    setState(elements.uploadState, "Failed", "error");
    addMessage("assistant", `업로드 실패: ${error.message}`);
  } finally {
    setBusy(elements.uploadButton, false);
  }
}

async function loadTopics(documentId) {
  elements.topicState.textContent = "Loading topics";
  elements.topicsList.innerHTML = "";

  try {
    const data = await request(`/v1/documents/${encodeURIComponent(documentId)}/topics`);
    elements.topicState.textContent = `${data.topic_count} topics`;
    elements.topicsList.innerHTML = data.topics.map(renderTopic).join("");
  } catch (error) {
    elements.topicState.textContent = "Failed to load topics";
    elements.topicsList.innerHTML = `<div class="topic-item"><p>${escapeHtml(error.message)}</p></div>`;
  }
}

async function createReport(event) {
  event.preventDefault();
  const query = elements.queryInput.value.trim();
  if (!query) {
    return;
  }

  addMessage("user", query);
  elements.queryInput.value = "";
  const pending = addMessage("assistant", "분석 중입니다...");

  try {
    const report = await request("/v1/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 8 }),
    });
    pending.innerHTML = renderReport(report);
    await refreshAiStatus();
  } catch (error) {
    pending.innerHTML = `<p>리포트 생성 실패: ${escapeHtml(error.message)}</p>`;
  }
}

async function refreshDashboard() {
  try {
    const data = await request("/v1/dashboard/refresh", { method: "POST" });
    elements.documentCount.textContent = data.document_count;
    elements.topicCount.textContent = data.topic_count;
    elements.chunkCount.textContent = data.chunk_count;
  } catch (error) {
    elements.documentCount.textContent = "-";
    elements.topicCount.textContent = "-";
    elements.chunkCount.textContent = "-";
  }
}

async function refreshAiStatus() {
  try {
    const status = await request("/v1/ai/status");
    elements.aiModel.textContent = status.model || "-";
    elements.aiBaseUrl.textContent = status.base_url || "Not configured";
    elements.aiLastCall.textContent = status.last_call
      ? `${status.last_call.task} / ${status.last_call.mode}`
      : "None";
    setState(elements.aiConfigured, status.configured ? "Configured" : "Fallback", status.configured ? "ok" : "warn");
  } catch (error) {
    setState(elements.aiConfigured, "Error", "error");
    elements.aiLastCall.textContent = error.message;
  }
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.detail || data.message || response.statusText);
  }
  return data;
}

function renderTopic(topic) {
  const keywords = (topic.keywords || [])
    .map((keyword) => `<span class="keyword">${escapeHtml(keyword)}</span>`)
    .join("");
  return `
    <article class="topic-item">
      <h3>${escapeHtml(topic.topic || "Untitled topic")}</h3>
      <p>${escapeHtml(topic.summary || "No summary")}</p>
      <p>Pages ${escapeHtml(String(topic.page_start))}-${escapeHtml(String(topic.page_end))}</p>
      <div class="keyword-row">${keywords}</div>
    </article>
  `;
}

function renderReport(report) {
  const sources = (report.source_chunks || [])
    .map((source) => {
      const topic = source.topic || source.metadata?.topic || "No topic";
      return `<li>${escapeHtml(topic)} · ${escapeHtml(source.document_id)} · pages ${escapeHtml(
        String(source.page_start),
      )}-${escapeHtml(String(source.page_end))}</li>`;
    })
    .join("");

  return `
    <p>${escapeHtml(report.answer)}</p>
    <div class="sources">
      <h4>Sources</h4>
      <ul>${sources || "<li>No sources</li>"}</ul>
    </div>
  `;
}

function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerHTML = `<p>${escapeHtml(text)}</p>`;
  elements.chatLog.appendChild(message);
  elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
  return message;
}

function setBusy(button, busy) {
  button.disabled = busy;
  button.textContent = busy ? "Working..." : "Upload and parse";
}

function setState(element, text, tone) {
  element.textContent = text;
  element.className = `state ${tone || ""}`.trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
