// Frontend logic for the DBTL Multi-Agent Lab.
// It talks to the FastAPI backend on the same origin (/api/...).

const $ = (sel) => document.querySelector(sel);

let AGENTS = [];

// ---------- Load the agent pipeline on page load ----------
async function loadAgents() {
  const res = await fetch("/api/agents");
  const data = await res.json();
  AGENTS = data.agents;

  const pipeline = $("#pipeline");
  const select = $("#singleAgent");
  pipeline.innerHTML = "";
  select.innerHTML = "";

  AGENTS.forEach((a, i) => {
    // Pipeline card
    const div = document.createElement("div");
    div.className = "agent";
    div.id = "agent-" + a.id;
    div.innerHTML = `
      <div class="phase">Step ${i + 1} · ${a.phase}</div>
      <h3>${a.name}</h3>
      <p>${a.tagline}</p>`;
    pipeline.appendChild(div);

    // Dropdown option
    const opt = document.createElement("option");
    opt.value = a.id;
    opt.textContent = a.name;
    select.appendChild(opt);
  });
}

// ---------- Upload a dataset ----------
async function uploadDataset() {
  const input = $("#fileInput");
  if (!input.files.length) {
    setStatus("Choose a file first.");
    return;
  }
  const fd = new FormData();
  fd.append("file", input.files[0]);
  setStatus("Uploading & summarizing…");

  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();

  const summary = $("#datasetSummary");
  summary.textContent = data.summary;
  summary.classList.remove("hidden");
  setStatus("Dataset ready: " + data.filename);
}

// ---------- Run one agent ----------
async function runSingle() {
  const agentId = $("#singleAgent").value;
  const message = $("#objective").value.trim() || "Proceed with your phase.";
  const useDataset = $("#useDataset").checked;

  clearResults();
  markAgents([agentId], "active");
  setStatus(`Running ${agentId}…`);
  disableButtons(true);

  try {
    const res = await fetch(`/api/agent/${agentId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, use_dataset: useDataset }),
    });
    const data = await res.json();
    addResult(data);
    markAgents([agentId], "done");
    setStatus("Done.");
  } catch (e) {
    setStatus("Error: " + e.message);
  } finally {
    disableButtons(false);
  }
}

// ---------- Run the full DBTL cycle ----------
async function runCycle() {
  const objective = $("#objective").value.trim();
  if (!objective) {
    setStatus("Enter an objective for the cycle first.");
    return;
  }
  const useDataset = $("#useDataset").checked;

  clearResults();
  setStatus("Running the full Design → Build → Test → Learn cycle… (this can take a bit)");
  disableButtons(true);

  // Visually walk through the phases while we wait for the response.
  AGENTS.forEach((a) => markAgents([a.id], ""));

  try {
    const res = await fetch("/api/cycle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ objective, use_dataset: useDataset }),
    });
    const data = await res.json();
    data.steps.forEach((step, i) => {
      addResult(step);
      const id = AGENTS[i] ? AGENTS[i].id : null;
      if (id) markAgents([id], "done");
    });
    setStatus("Cycle complete.");
  } catch (e) {
    setStatus("Error: " + e.message);
  } finally {
    disableButtons(false);
  }
}

// ---------- UI helpers ----------
function addResult(step) {
  const div = document.createElement("div");
  div.className = "result";
  div.innerHTML = `
    <div class="phase-tag">${step.phase} phase</div>
    <h4>${step.agent}</h4>
    <pre></pre>`;
  div.querySelector("pre").textContent = step.output;
  $("#results").appendChild(div);
}

function clearResults() {
  $("#results").innerHTML = "";
  AGENTS.forEach((a) => {
    const el = $("#agent-" + a.id);
    if (el) el.className = "agent";
  });
}

function markAgents(ids, cls) {
  ids.forEach((id) => {
    const el = $("#agent-" + id);
    if (el) el.className = "agent" + (cls ? " " + cls : "");
  });
}

function setStatus(msg) {
  $("#status").textContent = msg;
}

function disableButtons(disabled) {
  ["#cycleBtn", "#singleBtn", "#uploadBtn"].forEach((s) => {
    $(s).disabled = disabled;
  });
}

// ---------- Wire up ----------
$("#uploadBtn").addEventListener("click", uploadDataset);
$("#cycleBtn").addEventListener("click", runCycle);
$("#singleBtn").addEventListener("click", runSingle);
loadAgents();
