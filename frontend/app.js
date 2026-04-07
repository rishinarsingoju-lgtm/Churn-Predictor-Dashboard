const state = {
  filters: {
    risk: [], 
    segment: "all",
    min_days: null,
    max_days: null,
    sort_by: "days_inactive",
    order: "desc"
  },
  selectedIds: [],
  allCustomers: []
};

function formatRiskClass(risk) {
  if (risk === "High") return "high";
  if (risk === "Medium") return "medium";
  if (risk === "Low") return "low";
  return "safe";
}

function formatSegClass(segment) {
  if (segment === "High Spender") return "high-spender";
  if (segment === "Loyal") return "loyal";
  if (segment === "Regular") return "regular";
  return "one-time";
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 3000);
}

function buildQueryString(overrideRisk = null) {
  const params = new URLSearchParams();
  const risk = overrideRisk !== null ? overrideRisk : state.filters.risk.join(",");
  if (risk) params.set("risk", risk);
  else params.set("risk", "all");
  
  params.set("segment", state.filters.segment);
  if (state.filters.min_days !== null) params.set("min_days", state.filters.min_days);
  if (state.filters.max_days !== null) params.set("max_days", state.filters.max_days);
  params.set("sort_by", state.filters.sort_by);
  params.set("order", state.filters.order);
  return params.toString();
}

async function fetchCustomers() {
  const qs = buildQueryString();
  const res = await fetch(`/customers?${qs}`);
  const data = await res.json();
  state.allCustomers = data;
  state.selectedIds = [];
  document.getElementById("selectAllCb").checked = false;
  renderTable(data);
  updateMetrics(data);
  toggleBulkBar();
}

function renderTable(data) {
  const tbody = document.getElementById("tableBody");
  tbody.innerHTML = "";
  data.forEach(c => {
    let daysStr = c.days_inactive;
    if (daysStr === null || daysStr === undefined || isNaN(daysStr)) daysStr = "—";
    
    let statusStr = "";
    if (c.recovered) statusStr = "<span class='status-recovered'>✓ Recovered</span>";
    else if (c.contacted) statusStr = "<span class='status-contacted'>✓ Contacted</span>";
    
    let btnHtml = "";
    if (c.contacted) {
       btnHtml = `<button class="btn btn-secondary" disabled>✓ Contacted</button>`;
    } else {
       btnHtml = `<button class="btn btn-secondary btn-action" data-id="${c.id}" data-name="${c.name.replace(/"/g, '&quot;')}">Take Action</button>`;
    }

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="row-cb" value="${c.id}"></td>
      <td>${c.name}</td>
      <td>${c.email}</td>
      <td><span class="badge-seg ${formatSegClass(c.segment)}">${c.segment}</span></td>
      <td>${daysStr}</td>
      <td><span class="badge-risk ${formatRiskClass(c.risk_level)}">${c.risk_level}</span></td>
      <td>${c.suggested_action}</td>
      <td>${statusStr}</td>
      <td>${btnHtml}</td>
    `;
    tbody.appendChild(tr);
  });
  
  document.querySelectorAll(".row-cb").forEach(cb => {
    cb.addEventListener("change", e => {
      const id = parseInt(e.target.value);
      if (e.target.checked) state.selectedIds.push(id);
      else state.selectedIds = state.selectedIds.filter(x => x !== id);
      toggleBulkBar();
    });
  });

  document.querySelectorAll(".btn-action").forEach(btn => {
    btn.addEventListener("click", e => {
       const id = parseInt(e.target.dataset.id);
       const name = e.target.dataset.name;
       singleAction(id, name);
    });
  });
}

function updateMetrics(data) {
  document.getElementById("metricTotal").textContent = data.length;
  document.getElementById("metricHighRisk").textContent = data.filter(c => c.risk_level === "High").length;
  document.getElementById("metricContacted").textContent = data.filter(c => c.contacted).length;
  document.getElementById("metricRecovered").textContent = data.filter(c => c.recovered).length;
}

function applyFilters() {
  const riskCbs = Array.from(document.querySelectorAll(".risk-cb"));
  state.filters.risk = riskCbs.filter(cb => cb.checked).map(cb => cb.value);
  state.filters.segment = document.getElementById("segmentFilter").value;
  
  const min = document.getElementById("minDays").value;
  state.filters.min_days = min ? parseInt(min) : null;
  const max = document.getElementById("maxDays").value;
  state.filters.max_days = max ? parseInt(max) : null;
  
  state.filters.sort_by = document.getElementById("sortBy").value;
  state.filters.order = document.getElementById("sortOrder").value;
  
  fetchCustomers();
}

function clearFilters() {
  document.querySelectorAll(".risk-cb").forEach(cb => cb.checked = false);
  document.getElementById("segmentFilter").value = "all";
  document.getElementById("minDays").value = "";
  document.getElementById("maxDays").value = "";
  document.getElementById("sortBy").value = "days_inactive";
  document.getElementById("sortOrder").value = "desc";
  applyFilters();
  showToast("Filters cleared");
}

function toggleBulkBar() {
  const bar = document.getElementById("bulkActionBar");
  const txt = document.getElementById("bulkActionText");
  if (state.selectedIds.length > 0) {
    txt.textContent = `${state.selectedIds.length} customers selected`;
    bar.classList.remove("hidden");
  } else {
    bar.classList.add("hidden");
  }
}

document.getElementById("selectAllCb").addEventListener("change", e => {
  const checked = e.target.checked;
  const checkboxes = document.querySelectorAll(".row-cb");
  state.selectedIds = [];
  checkboxes.forEach(cb => {
    cb.checked = checked;
    if (checked) state.selectedIds.push(parseInt(cb.value));
  });
  toggleBulkBar();
});

document.getElementById("applyFiltersBtn").addEventListener("click", applyFilters);
document.getElementById("clearFiltersBtn").addEventListener("click", clearFilters);

async function bulkAction() {
  if (!window.confirm(`Send offer to ${state.selectedIds.length} customers?`)) return;
  await postActions(state.selectedIds, "bulk_offer");
}
document.getElementById("bulkActionBtn").addEventListener("click", bulkAction);

async function singleAction(id, name) {
  if (!window.confirm(`Send retention email to ${name}?`)) return;
  await postActions([id], "retention_email");
}

async function postActions(ids, type) {
  const res = await fetch("/actions", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({customer_ids: ids, action_type: type})
  });
  if (res.ok) {
    showToast(`Email queued for ${ids.length} customers`);
    // Optimistic update
    ids.forEach(id => {
      const c = state.allCustomers.find(x => x.id === id);
      if (c) c.contacted = true;
    });
    state.selectedIds = [];
    document.getElementById("selectAllCb").checked = false;
    renderTable(state.allCustomers);
    updateMetrics(state.allCustomers);
    toggleBulkBar();
  }
}

document.querySelectorAll("[data-export]").forEach(link => {
  link.addEventListener("click", e => {
    e.preventDefault();
    const type = e.target.dataset.export;
    let riskParams = null;
    if (type === "high") riskParams = "High";
    else if (type === "high_medium") riskParams = "High,Medium";
    else if (type === "all") riskParams = "all";
    exportData(riskParams);
  });
});

function exportData(riskOverride) {
  const qs = buildQueryString(riskOverride);
  window.location.href = `/export/csv?${qs}`;
}

document.getElementById("csvUploadInput").addEventListener("change", async e => {
  const file = e.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  
  showToast("Uploading CSV...");
  const res = await fetch("/upload/csv", {
    method: "POST",
    body: formData
  });
  
  if (res.ok) {
    const data = await res.json();
    if(data.success) {
      showToast(`${data.imported} customers imported successfully`);
      fetchCustomers();
    }
  } else {
    showToast("Upload failed");
  }
  e.target.value = "";
});

const logPanel = document.getElementById("actionLogPanel");
const logOverlay = document.getElementById("actionLogOverlay");
const toggleLogBtn = document.getElementById("toggleLogBtn");
const closeLogBtn = document.getElementById("closeLogBtn");
const logContent = document.getElementById("actionLogContent");

async function fetchActionLog() {
  const res = await fetch("/actions/log");
  const data = await res.json();
  logContent.innerHTML = "";
  if(data.length === 0) {
    logContent.innerHTML = "<p>No actions logged yet.</p>";
    return;
  }
  data.forEach(log => {
      const div = document.createElement("div");
      div.className = "log-item";
      let d = new Date(log.taken_at).toLocaleString();
      div.innerHTML = `
        <p><strong>${log.customer_name}</strong> (${log.email})</p>
        <p>Action: ${log.action_type}</p>
        <div class="log-date">${d}</div>
      `;
      logContent.appendChild(div);
  });
}

function openLog() {
  fetchActionLog();
  logPanel.classList.add("open");
  logOverlay.classList.add("open");
}
function closeLog() {
  logPanel.classList.remove("open");
  logOverlay.classList.remove("open");
}

toggleLogBtn.addEventListener("click", openLog);
closeLogBtn.addEventListener("click", closeLog);
logOverlay.addEventListener("click", closeLog);

document.addEventListener("DOMContentLoaded", fetchCustomers);
