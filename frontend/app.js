// State
let allAccounts = [];
let filteredAccounts = [];
let currentAccount = null;
let currentSegmentFilter = '';
let currentRiskFilter = '';
let activeGovernanceMode = 'Day 90+: Full Autonomous';

// Chart instances
let shapChart = null;
let survivalChart = null;
let telemetryChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  await refreshData();
  calculateROI();

  // Periodic refresh every 15 seconds
  setInterval(async () => {
    await refreshData(true);
  }, 15000);
});

async function refreshData(silent = false) {
  try {
    await Promise.all([loadOverview(), loadAccounts(), loadDispatches()]);
    if (!silent) {
      lucide.createIcons();
    }
  } catch (err) {
    console.error("Error refreshing data:", err);
  }
}

async function loadOverview() {
  const res = await fetch('/api/overview');
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpi-monitored-arr').textContent = `$${data.total_arr_monitored.toLocaleString('en-US')}`;
  document.getElementById('kpi-arr-at-risk').textContent = `$${data.total_arr_at_risk.toLocaleString('en-US')}`;
  document.getElementById('kpi-prevented-arr').textContent = `$${data.prevented_churn_arr.toLocaleString('en-US')}`;
  document.getElementById('kpi-avg-risk').textContent = `${data.avg_churn_risk_pct}%`;
  document.getElementById('kpi-critical-count').textContent = `${data.critical_risk_accounts} Critical`;

  activeGovernanceMode = data.active_governance_mode;
  updateGovernanceButtons(activeGovernanceMode);
}

async function loadAccounts() {
  const res = await fetch('/api/accounts');
  if (!res.ok) return;
  allAccounts = await res.json();
  filterAccounts();
  populateSimAccountSelect();
}

function populateSimAccountSelect() {
  const select = document.getElementById('sim-account-select');
  const currentVal = select.value;
  select.innerHTML = '';
  allAccounts.forEach(acc => {
    const opt = document.createElement('option');
    opt.value = acc.id;
    opt.textContent = `${acc.name} (${acc.tier}) - Risk: ${acc.latest_prediction ? acc.latest_prediction.risk_score : 0}%`;
    select.appendChild(opt);
  });
  if (currentVal && allAccounts.some(a => a.id === currentVal)) {
    select.value = currentVal;
  }
}

function filterAccounts() {
  const search = (document.getElementById('account-search-input').value || '').toLowerCase();
  
  filteredAccounts = allAccounts.filter(acc => {
    // Segment filter
    if (currentSegmentFilter && acc.tier !== currentSegmentFilter) return false;

    // Risk level filter
    if (currentRiskFilter && acc.latest_prediction) {
      if (acc.latest_prediction.risk_level.toLowerCase() !== currentRiskFilter.toLowerCase()) return false;
    }

    // Search query
    if (search) {
      const matchName = acc.name.toLowerCase().includes(search);
      const matchDomain = acc.domain.toLowerCase().includes(search);
      const matchCsm = (acc.csm_assigned || '').toLowerCase().includes(search);
      const matchDriver = (acc.latest_prediction?.cluster || '').toLowerCase().includes(search);
      if (!matchName && !matchDomain && !matchCsm && !matchDriver) return false;
    }

    return true;
  });

  renderAccountsTable(filteredAccounts);
}

function renderAccountsTable(accounts) {
  const tbody = document.getElementById('accounts-table-body');
  tbody.innerHTML = '';

  if (accounts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No matching accounts found.</td></tr>`;
    return;
  }

  accounts.forEach(acc => {
    const pred = acc.latest_prediction || { risk_score: 0, risk_level: 'Low', cluster: 'Healthy & Stable', estimated_ttc_days: 90 };
    const tr = document.createElement('tr');

    // Tier badge class
    let tierBadgeClass = 'badge-plg';
    if (acc.tier === 'Enterprise VIP') tierBadgeClass = 'badge-vip';
    else if (acc.tier === 'Mid-Market') tierBadgeClass = 'badge-mid';

    // Risk fill class
    let fillClass = 'fill-low';
    let riskBadgeClass = 'badge-low';
    if (pred.risk_level === 'Critical') {
      fillClass = 'fill-critical';
      riskBadgeClass = 'badge-critical';
    } else if (pred.risk_level === 'High') {
      fillClass = 'fill-high';
      riskBadgeClass = 'badge-high';
    } else if (pred.risk_level === 'Medium') {
      fillClass = 'fill-medium';
      riskBadgeClass = 'badge-medium';
    }

    const initials = acc.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    const nbaTitle = pred.next_best_action ? pred.next_best_action.action_title : 'Nominal Monitoring';
    const nbaChannel = pred.next_best_action ? pred.next_best_action.channel : 'System';

    tr.innerHTML = `
      <td>
        <div class="acc-cell">
          <div class="acc-avatar">${initials}</div>
          <div class="acc-details">
            <span class="acc-name">${acc.name} ${acc.is_at_risk_flag ? '<span class="badge badge-critical" style="font-size:0.6rem; padding:1px 4px;">AT-RISK</span>' : ''}</span>
            <span class="acc-domain">${acc.domain} &bull; <span class="badge ${tierBadgeClass}" style="font-size:0.62rem; padding:1px 4px;">${acc.tier}</span></span>
          </div>
        </div>
      </td>
      <td>
        <div style="font-weight:700;">$${acc.arr.toLocaleString('en-US')}</div>
        <div style="font-size:0.75rem; color:var(--text-muted);">Renewal in ${acc.contract_renewal_days}d</div>
      </td>
      <td>
        <div class="risk-score-wrap">
          <span class="risk-num" style="color:${getRiskColor(pred.risk_score)}">${pred.risk_score}%</span>
          <div class="risk-mini-track">
            <div class="risk-mini-fill ${fillClass}" style="width: ${pred.risk_score}%;"></div>
          </div>
          <span class="badge ${riskBadgeClass}" style="font-size:0.65rem;">${pred.risk_level}</span>
        </div>
      </td>
      <td>
        <span class="badge badge-neutral">${pred.cluster}</span>
      </td>
      <td>
        <span style="font-weight:700; color:${pred.estimated_ttc_days < 35 ? '#f87171' : 'var(--text-primary)'};">${pred.estimated_ttc_days} Days</span>
      </td>
      <td>
        <div style="font-weight:600; font-size:0.8rem; color:#93c5fd;">${nbaChannel}</div>
        <div style="font-size:0.72rem; color:var(--text-secondary); max-width:220px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${nbaTitle}">${nbaTitle}</div>
      </td>
      <td class="text-right">
        <button class="btn btn-outline btn-sm" onclick="openAccountModal('${acc.id}')">
          <i data-lucide="eye"></i> Inspect
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  lucide.createIcons();
}

function getRiskColor(score) {
  if (score >= 75) return '#f87171';
  if (score >= 50) return '#fbbf24';
  if (score >= 25) return '#fde047';
  return '#34d399';
}

function setSegmentFilter(btn, segment) {
  document.querySelectorAll('[data-segment]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentSegmentFilter = segment;
  filterAccounts();
}

function setRiskFilter(btn, risk) {
  document.querySelectorAll('[data-risk]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentRiskFilter = risk;
  filterAccounts();
}

// MODAL / INSPECTOR
async function openAccountModal(accountId) {
  const res = await fetch(`/api/accounts/${accountId}`);
  if (!res.ok) return;
  currentAccount = await res.json();
  const acc = currentAccount;
  const pred = acc.latest_prediction;

  document.getElementById('modal-avatar').textContent = acc.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  document.getElementById('modal-account-name').textContent = acc.name;
  document.getElementById('modal-domain-csm').textContent = `${acc.domain} • CSM: ${acc.csm_assigned} • ARR: $${acc.arr.toLocaleString('en-US')}`;

  // Badges
  const tierBadge = document.getElementById('modal-tier-badge');
  tierBadge.textContent = acc.tier;
  tierBadge.className = `badge ${acc.tier === 'Enterprise VIP' ? 'badge-vip' : acc.tier === 'Mid-Market' ? 'badge-mid' : 'badge-plg'}`;

  const riskBadge = document.getElementById('modal-risk-badge');
  riskBadge.textContent = `${pred.risk_level} Risk (${pred.risk_score}%)`;
  riskBadge.className = `badge ${pred.risk_level === 'Critical' ? 'badge-critical' : pred.risk_level === 'High' ? 'badge-high' : pred.risk_level === 'Medium' ? 'badge-medium' : 'badge-low'}`;

  document.getElementById('modal-cluster-badge').textContent = `Driver: ${pred.cluster}`;

  // Gauge & TTC
  document.getElementById('modal-risk-score').textContent = pred.risk_score;
  document.getElementById('modal-risk-score').style.color = getRiskColor(pred.risk_score);
  document.getElementById('modal-risk-bar').style.width = `${pred.risk_score}%`;
  document.getElementById('modal-ttc-days').textContent = pred.estimated_ttc_days;

  // NBA Card
  const nba = pred.next_best_action;
  document.getElementById('modal-nba-channel').textContent = nba.channel;
  document.getElementById('modal-nba-title').textContent = nba.action_title;
  document.getElementById('modal-nba-desc').textContent = nba.action_description;
  document.getElementById('modal-payload-json').textContent = JSON.stringify(nba.recommended_payload, null, 2);

  // Ticket snippets
  const snippetsList = document.getElementById('modal-ticket-snippets');
  snippetsList.innerHTML = '';
  const snippets = pred.sentiment_analysis.ticket_snippets || [];
  snippets.forEach(s => {
    const div = document.createElement('div');
    div.className = 'ticket-item';
    div.textContent = s;
    snippetsList.appendChild(div);
  });

  const nlpBadge = document.getElementById('modal-nlp-badge');
  nlpBadge.textContent = `${pred.sentiment_analysis.sentiment_label} (${pred.sentiment_analysis.sentiment_score})`;
  nlpBadge.className = `badge ${pred.sentiment_analysis.sla_tier_override_needed ? 'badge-critical' : 'badge-neutral'}`;

  // Render Charts
  renderShapChart(pred.shap_attributions);
  renderSurvivalChart(pred.survival_curve, pred.estimated_ttc_days);
  renderTelemetryChart(acc.telemetry.historical_90d_decay || []);

  document.getElementById('account-modal').classList.add('open');
  lucide.createIcons();
}

function closeModal() {
  document.getElementById('account-modal').classList.remove('open');
}

function closeModalOnBackdrop(e) {
  if (e.target.id === 'account-modal') {
    closeModal();
  }
}

// CHARTS RENDERING
function renderShapChart(attributions) {
  const ctx = document.getElementById('shapChart').getContext('2d');
  if (shapChart) shapChart.destroy();

  const top6 = (attributions || []).slice(0, 6);
  const labels = top6.map(a => a.feature_name);
  const data = top6.map(a => a.impact_score);
  const colors = data.map(val => val >= 0 ? '#ef4444' : '#10b981');

  shapChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'SHAP Risk Contribution',
        data: data,
        backgroundColor: colors,
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const item = top6[context.dataIndex];
              return `${item.impact_score > 0 ? '+' : ''}${item.impact_score} (${item.explanation})`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#9ca3af', font: { size: 10 } }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#e5e7eb', font: { size: 10, weight: 600 } }
        }
      }
    }
  });
}

function renderSurvivalChart(survivalCurve, ttc) {
  const ctx = document.getElementById('survivalChart').getContext('2d');
  if (survivalChart) survivalChart.destroy();

  const labels = (survivalCurve || []).map(p => `Day ${p.day}`);
  const data = (survivalCurve || []).map(p => (p.survival_probability * 100).toFixed(1));

  survivalChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Survival Probability S(t) %',
          data: data,
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `Survival: ${context.parsed.y}%`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#9ca3af', font: { size: 10 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#9ca3af', font: { size: 10 } }
        }
      }
    }
  });
}

function renderTelemetryChart(historicalPoints) {
  const ctx = document.getElementById('telemetryChart').getContext('2d');
  if (telemetryChart) telemetryChart.destroy();

  const labels = historicalPoints.map(p => `-${p.day}d`);
  const apiCalls = historicalPoints.map(p => p.api_calls);
  const coreUsage = historicalPoints.map(p => p.core_feature_events);
  const sessionMins = historicalPoints.map(p => p.session_minutes);

  telemetryChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'API Calls',
          data: apiCalls,
          borderColor: '#3b82f6',
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
          yAxisID: 'y'
        },
        {
          label: 'Core Feature Events',
          data: coreUsage,
          borderColor: '#06b6d4',
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
          yAxisID: 'y1'
        },
        {
          label: 'Avg Session Mins',
          data: sessionMins,
          borderColor: '#f59e0b',
          borderWidth: 1.5,
          borderDash: [4, 4],
          pointRadius: 1,
          tension: 0.3,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', font: { size: 11 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#9ca3af', font: { size: 10 } }
        },
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: 'rgba(255,255,255,0.06)' },
          ticks: { color: '#3b82f6', font: { size: 10 } }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { display: false },
          ticks: { color: '#06b6d4', font: { size: 10 } }
        }
      }
    }
  });
}

// ACTIONS
async function dispatchCurrentNba() {
  if (!currentAccount) return;
  const res = await fetch('/api/orchestration/dispatch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: currentAccount.id })
  });

  if (res.ok) {
    const data = await res.json();
    showToast(data.message, 'success');
    await refreshData();
    openAccountModal(currentAccount.id);
  }
}

async function triggerClosedLoopSuccess() {
  if (!currentAccount) return;
  const res = await fetch('/api/closed-loop/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: currentAccount.id, outcome_status: 'Accepted & Retained' })
  });

  if (res.ok) {
    const data = await res.json();
    showToast(data.message, 'success');
    await refreshData();
    openAccountModal(currentAccount.id);
  }
}

async function injectDecayScenario(scenarioType) {
  const accountId = document.getElementById('sim-account-select').value;
  if (!accountId) {
    showToast('Please select a target account', 'warning');
    return;
  }

  const res = await fetch('/api/simulation/decay-event', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId, scenario_type: scenarioType })
  });

  if (res.ok) {
    const data = await res.json();
    showToast(data.message, 'info');
    await refreshData();
    populateSimAccountSelect();
  }
}

async function setGovernanceMode(mode) {
  const res = await fetch('/api/governance/mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: mode })
  });

  if (res.ok) {
    activeGovernanceMode = mode;
    updateGovernanceButtons(mode);
    showToast(`Phased Deployment Matrix updated: ${mode}`, 'info');
    await refreshData();
  }
}

function updateGovernanceButtons(activeMode) {
  document.querySelectorAll('.gov-mode-btn').forEach(btn => {
    if (btn.dataset.mode === activeMode) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

async function togglePiiMasking(enabled) {
  const res = await fetch('/api/governance/pii-masking', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled: enabled })
  });

  if (res.ok) {
    showToast(`PII Tokenization ${enabled ? 'Enabled (GDPR Mode)' : 'Disabled'}`, 'info');
    await refreshData();
  }
}

async function loadDispatches() {
  const res = await fetch('/api/dispatches');
  if (!res.ok) return;
  const dispatches = await res.json();
  const tbody = document.getElementById('dispatches-table-body');
  tbody.innerHTML = '';

  if (dispatches.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 1.5rem; color:var(--text-muted);">No dispatches recorded yet.</td></tr>`;
    return;
  }

  dispatches.forEach(d => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="font-family:'JetBrains Mono', monospace; font-size:0.75rem;">${d.timestamp}</td>
      <td>
        <span class="badge badge-mid" style="margin-right:0.3rem;">${d.channel}</span>
        <span style="font-size:0.75rem; color:var(--text-secondary);">${d.target_destination}</span>
      </td>
      <td><span style="font-weight:600;">${d.action_taken}</span></td>
      <td><span class="badge badge-neutral" style="font-size:0.65rem;">${d.mode}</span></td>
      <td><span class="badge ${d.status.includes('Suppressed') ? 'badge-medium' : 'badge-low'}">${d.status}</span></td>
      <td><pre style="font-size:0.65rem; color:#38bdf8; max-width:260px; overflow:hidden; text-overflow:ellipsis;">${JSON.stringify(d.payload)}</pre></td>
    `;
    tbody.appendChild(tr);
  });
}

function switchView(viewName) {
  document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

  document.getElementById(`view-${viewName}`).classList.add('active');
  event.currentTarget.classList.add('active');
}

// ROI CALCULATOR (Slide 7)
function calculateROI() {
  const customers = parseInt(document.getElementById('input-customers').value, 10);
  const avgArr = parseFloat(document.getElementById('input-avg-arr').value);
  const churnPct = parseFloat(document.getElementById('input-churn-pct').value);
  const liftPct = parseFloat(document.getElementById('input-lift-pct').value);

  document.getElementById('val-customers').textContent = customers;
  document.getElementById('val-avg-arr').textContent = `$${avgArr.toLocaleString('en-US')}`;
  document.getElementById('val-churn-pct').textContent = `${churnPct.toFixed(1)}%`;
  document.getElementById('val-lift-pct').textContent = `${liftPct.toFixed(1)}%`;

  const totalArr = customers * avgArr;
  const baselineChurnArr = totalArr * (churnPct / 100.0);
  const arrSaved = baselineChurnArr * (liftPct / 100.0);
  const accountsSaved = (customers * (churnPct / 100.0)) * (liftPct / 100.0);

  const anchorCost = 45000.0;
  const netRoi = (arrSaved / anchorCost).toFixed(1);
  const paybackMonths = arrSaved > 0 ? ((anchorCost / (arrSaved / 12.0))).toFixed(1) : 0;

  document.getElementById('roi-arr-saved').textContent = `$${Math.round(arrSaved).toLocaleString('en-US')}`;
  document.getElementById('roi-multiple').textContent = `${netRoi}x`;
  document.getElementById('roi-payback').textContent = `${paybackMonths} months`;
  document.getElementById('roi-accounts-saved').textContent = `${accountsSaved.toFixed(1)} accounts/yr`;
}

// TOAST NOTIFICATIONS
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<i data-lucide="bell"></i> <span>${msg}</span>`;
  container.appendChild(toast);
  lucide.createIcons();

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
