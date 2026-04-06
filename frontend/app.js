const customerTable = document.getElementById("customerTable");
const totalCustomersEl = document.getElementById("totalCustomers");
const highRiskCountEl = document.getElementById("highRiskCount");
const contactedCountEl = document.getElementById("contactedCount");
const riskFilterBtn = document.getElementById("riskFilter");
const searchInput = document.getElementById("searchInput");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const toast = document.getElementById("toast");
const customDropdown = document.querySelector(".custom-dropdown");
const dropdownItems = document.querySelectorAll(".dropdown-item");

let customerData = [];
let selectedRisk = "All";

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(window.toastTimeout);
  window.toastTimeout = setTimeout(() => {
    toast.classList.add("hidden");
  }, 2200);
}

function formatRiskClass(risk) {
  if (risk === "High") return "status-high";
  if (risk === "Medium") return "status-medium";
  return "status-low";
}

function buildTableRows(customers) {
  customerTable.innerHTML = "";

  if (!customers.length) {
    customerTable.innerHTML = "<tr><td colspan='6' class='empty-state'>No customers match your search.</td></tr>";
    return;
  }

  customers.forEach((customer) => {
    const row = document.createElement("tr");
    row.className = `row-risk-${customer.risk_level.toLowerCase()}`;

    const actionButton = document.createElement("button");
    actionButton.className = "action-btn";
    actionButton.textContent = customer.contacted_this_week ? "Contacted" : "Send Retention Email";
    actionButton.disabled = customer.contacted_this_week;
    actionButton.addEventListener("click", () => sendAction(customer.id, actionButton));

    row.innerHTML = `
      <td>${customer.name}</td>
      <td>${customer.email}</td>
      <td>${new Date(customer.last_purchase_date).toLocaleDateString()}</td>
      <td>${customer.days_since_last_purchase}</td>
      <td><span class="status-pill ${formatRiskClass(customer.risk_level)}">${customer.risk_level}</span></td>
      <td></td>
    `;

    const actionCell = row.querySelector("td:last-child");
    actionCell.appendChild(actionButton);

    customerTable.appendChild(row);
  });
}

function updateSummary(summary) {
  totalCustomersEl.textContent = summary.total_customers;
  highRiskCountEl.textContent = summary.high_risk_customers;
  contactedCountEl.textContent = summary.contacted_this_week;
}

function filterCustomers() {
  const searchValue = searchInput.value.trim().toLowerCase();

  return customerData.filter((customer) => {
    const matchesRisk = selectedRisk === "All" || customer.risk_level === selectedRisk;
    const matchesSearch =
      customer.name.toLowerCase().includes(searchValue) ||
      customer.email.toLowerCase().includes(searchValue);
    return matchesRisk && matchesSearch;
  });
}

async function fetchCustomers() {
  try {
    const response = await fetch("/customers");
    const data = await response.json();
    customerData = data.customers;
    const highRiskCount = customerData.filter((customer) => customer.risk_level === "High").length;
    data.summary.high_risk_customers = highRiskCount;
    updateSummary(data.summary);
    buildTableRows(filterCustomers());
  } catch (error) {
    showToast("Unable to load customers.");
    console.error(error);
  }
}

async function sendAction(customerId, button) {
  try {
    button.disabled = true;
    button.textContent = "Sending...";
    const response = await fetch("/actions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: customerId, action_type: "Retention Email" }),
    });

    if (!response.ok) {
      throw new Error("Action failed");
    }

    showToast("Retention email logged");
    await fetchCustomers();
  } catch (error) {
    showToast("Failed to log action");
    button.disabled = false;
    button.textContent = "Send Retention Email";
    console.error(error);
  }
}

exportCsvBtn.addEventListener("click", () => {
  window.location.href = "/export/csv";
});

// Custom dropdown functionality
riskFilterBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  customDropdown.toggleAttribute("data-open");
  riskFilterBtn.setAttribute("aria-expanded", customDropdown.hasAttribute("data-open"));
});

dropdownItems.forEach((item) => {
  item.addEventListener("click", () => {
    const value = item.dataset.value;
    selectedRisk = value;
    riskFilterBtn.textContent = item.textContent;
    dropdownItems.forEach((i) => i.removeAttribute("aria-selected"));
    item.setAttribute("aria-selected", "true");
    customDropdown.removeAttribute("data-open");
    riskFilterBtn.setAttribute("aria-expanded", "false");
    buildTableRows(filterCustomers());
  });
});

document.addEventListener("click", () => {
  customDropdown.removeAttribute("data-open");
  riskFilterBtn.setAttribute("aria-expanded", "false");
});

searchInput.addEventListener("input", () => buildTableRows(filterCustomers()));
window.addEventListener("DOMContentLoaded", fetchCustomers);
