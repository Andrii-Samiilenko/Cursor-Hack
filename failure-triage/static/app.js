/**
 * Failure Triage Bot — client UI (vanilla JS).
 * Calls POST /api/triage and GET /api/demo/:id; same origin when served by FastAPI.
 */

const $ = (id) => document.getElementById(id);

const apiBase = "";

function setLoading(isLoading) {
  const out = $("output-section");
  $("loading").hidden = !isLoading;
  $("submit").disabled = isLoading;
  out.setAttribute("aria-busy", isLoading ? "true" : "false");
}

function showError(message) {
  const el = $("error");
  el.textContent = message;
  el.hidden = false;
  $("placeholder").hidden = true;
  $("result").hidden = true;
}

function hideError() {
  $("error").hidden = true;
}

function renderResult(data) {
  $("placeholder").hidden = true;
  hideError();
  const root = $("result");
  root.hidden = false;

  const reproHtml = (data.repro_commands || [])
    .map((c) => `<pre>${escapeHtml(c)}</pre>`)
    .join("");

  const hyp = (data.hypothesis || []).map((h) => `<li>${escapeHtml(h)}</li>`).join("");
  const fixItems = (data.fix_plan || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  const assum = (data.assumptions || []).map((a) => `<li>${escapeHtml(a)}</li>`).join("");

  const where = (data.where_to_look || [])
    .map(
      (w) =>
        `<div class="where-item"><code>${escapeHtml(w.path)}</code> — ${escapeHtml(w.reason)}</div>`
    )
    .join("");

  const trunc = data.truncated_note
    ? `<div class="truncated-note">${escapeHtml(data.truncated_note)}</div>`
    : "";

  const sig = data.extracted_signals || {};
  const sigHtml = `
    <details class="signals">
      <summary>Extracted signals</summary>
      <pre>${escapeHtml(JSON.stringify(sig, null, 2))}</pre>
    </details>
  `;

  const conf = data.confidence || "low";

  root.innerHTML = `
    ${trunc}
    <section>
      <h3>Summary</h3>
      <p class="summary">${escapeHtml(data.summary || "")}</p>
      <p><span class="confidence ${escapeAttr(conf)}">${escapeHtml(conf)}</span></p>
    </section>
    <section>
      <h3>Hypothesis</h3>
      <ul>${hyp || "<li>(none)</li>"}</ul>
    </section>
    <section>
      <h3>Where to look</h3>
      ${where || "<p class=\"muted\">(none)</p>"}
    </section>
    <section>
      <h3>Fix plan</h3>
      <ol>${fixItems || "<li>(none)</li>"}</ol>
    </section>
    <section class="repro">
      <h3>Repro commands</h3>
      ${reproHtml || "<p>(none)</p>"}
    </section>
    <section>
      <h3>Assumptions</h3>
      <ul>${assum || "<li>(none)</li>"}</ul>
    </section>
    <section class="issue-block">
      <h3>Issue export</h3>
      <pre id="issue-md">${escapeHtml(data.issue_markdown || "")}</pre>
      <div class="copy-row">
        <button type="button" class="copy-btn">Copy issue markdown</button>
      </div>
    </section>
    ${sigHtml}
  `;

  const issueMd = data.issue_markdown || "";
  root.querySelector(".copy-btn")?.addEventListener("click", () => {
    copyToClipboard(issueMd);
  });
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  return String(s || "").replace(/[^a-z0-9_-]/gi, "");
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    /* ignore */
  }
}

async function submitTriage() {
  const log = $("log").value.trim();
  if (!log) {
    showError("Paste a log first.");
    return;
  }
  hideError();
  $("result").hidden = true;
  $("placeholder").hidden = true;
  setLoading(true);

  const body = {
    log,
    framework: $("framework").value,
    language: $("language").value,
    context: null,
  };
  const note = $("note").value.trim();
  if (note) {
    body.context = { branch: null, note };
  }

  try {
    const res = await fetch(`${apiBase}/api/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    renderResult(data);
  } catch (e) {
    showError(e.message || "Request failed");
  } finally {
    setLoading(false);
  }
}

async function loadDemo(fixtureId) {
  hideError();
  $("result").hidden = true;
  $("placeholder").hidden = true;
  setLoading(true);
  try {
    const det = await fetch(`${apiBase}/api/fixtures/${encodeURIComponent(fixtureId)}`);
    if (!det.ok) throw new Error(`HTTP ${det.status}`);
    const detail = await det.json();
    $("log").value = detail.log || "";

    const res = await fetch(`${apiBase}/api/demo/${encodeURIComponent(fixtureId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderResult(data);
  } catch (e) {
    showError(e.message || "Demo load failed");
  } finally {
    setLoading(false);
  }
}

async function loadFixtureList() {
  const container = $("fixture-buttons");
  try {
    const res = await fetch(`${apiBase}/api/fixtures`);
    if (!res.ok) return;
    const list = await res.json();
    container.innerHTML = "";
    list.forEach((f) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = f.title;
      b.addEventListener("click", () => loadDemo(f.id));
      container.appendChild(b);
    });
  } catch {
    /* offline */
  }
}

function clearAll() {
  $("log").value = "";
  $("note").value = "";
  $("result").hidden = true;
  $("placeholder").hidden = false;
  hideError();
}

$("submit").addEventListener("click", submitTriage);
$("clear").addEventListener("click", clearAll);
loadFixtureList();
