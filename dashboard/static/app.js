/**
 * app.js — Dashboard JavaScript
 * Socket.IO real-time updates + Chart.js rendering
 */

const socket = io();
const i18n = window.I18N || {};

const algoColors = {
  "Q-Learning": "#6366f1",
  "SARSA":      "#38bdf8",
  "DQN":        "#f59e0b",
  "PPO":        "#10b981",
  "A2C":        "#f43f5e",
  "Unknown":    "#94a3b8"
};

// ── Chart setup ──────────────────────────────────────────────────────────────
const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  animation: { duration: 300 },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(15,22,40,.95)',
      borderColor: 'rgba(99,102,241,.3)',
      borderWidth: 1,
      titleColor: '#e2e8f0',
      bodyColor: '#94a3b8',
    },
  },
  scales: {
    x: {
      ticks: { color: '#475569', maxTicksLimit: 8 },
      grid:  { color: 'rgba(255,255,255,.04)' },
    },
    y: {
      ticks: { color: '#475569' },
      grid:  { color: 'rgba(255,255,255,.04)' },
    },
  },
};

function makeLineDataset(label, color, data) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: color + '18',
    fill: true,
    tension: 0.4,
    borderWidth: 2,
    pointRadius: 0,
    pointHoverRadius: 4,
  };
}

const rewardChart = new Chart(document.getElementById('chart-reward'), {
  type: 'line',
  data: { labels: [], datasets: [] },
  options: { ...chartDefaults },
});

const foodChart = new Chart(document.getElementById('chart-food'), {
  type: 'line',
  data: { labels: [], datasets: [] },
  options: { ...chartDefaults },
});

// ── Smooth helper ─────────────────────────────────────────────────────────────
function smooth(arr, w = 10) {
  if (arr.length < w) return arr;
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    const start = Math.max(0, i - w + 1);
    const slice = arr.slice(start, i + 1);
    out.push(slice.reduce((a, b) => a + b, 0) / slice.length);
  }
  return out;
}

// ── Update functions ──────────────────────────────────────────────────────────
function updateMetrics(data) {
  document.getElementById('m-episode').textContent = data.episode;
  document.getElementById('ep-value').textContent   = data.episode;
  document.getElementById('m-food').textContent     = data.world?.food_count ?? '—';
  document.getElementById('m-step').textContent     = data.world?.step ?? '—';
  document.getElementById('m-eaten').textContent    = data.world?.food_eaten ?? '—';
}

function updateCharts(data) {
  if (!data.rewards || Object.keys(data.rewards).length === 0) return;
  
  // Find max length for labels
  const maxLen = Math.max(...Object.values(data.rewards).map(a => a.length));
  const labels = Array.from({ length: maxLen }, (_, i) => i + 1);

  // Update legends
  const algos = Object.keys(data.rewards);
  const legendHtml = algos.map(algo => {
      const color = algoColors[algo] || algoColors["Unknown"];
      return `<span class="legend-dot" style="background:${color}"></span><span>${algo}</span>`;
  }).join('');
  document.getElementById('legend-reward').innerHTML = legendHtml;
  document.getElementById('legend-food').innerHTML = legendHtml;

  // Update datasets dynamically
  const rewardDatasets = algos.map(algo => 
      makeLineDataset(algo, algoColors[algo] || algoColors["Unknown"], smooth(data.rewards[algo], 15))
  );
  const foodDatasets = algos.map(algo => 
      makeLineDataset(algo, algoColors[algo] || algoColors["Unknown"], smooth(data.foods[algo], 15))
  );

  rewardChart.data.labels = labels;
  rewardChart.data.datasets = rewardDatasets;
  rewardChart.update('none');

  foodChart.data.labels = labels;
  foodChart.data.datasets = foodDatasets;
  foodChart.update('none');
}

function updateAgents(agents) {
  const grid = document.getElementById('agents-grid');
  if (!agents || agents.length === 0) return;

  grid.innerHTML = agents.map(a => {
    const algo  = a.type;
    const color = algoColors[algo] || algoColors["Unknown"];
    const pct   = Math.max(0, Math.min(100, (a.energy / 100) * 100)).toFixed(0);
    const alive = a.alive;
    const energyColor = pct > 50 ? '#10b981' : pct > 25 ? '#f59e0b' : '#f43f5e';

    return `
      <div class="agent-card ${alive ? '' : 'dead'}" style="border-top-color: ${color}">
        <div class="agent-header">
          <span class="agent-name">
            ${alive ? '🟢' : '💀'} Agent ${a.id}
          </span>
          <span class="agent-type-badge" style="background:${color}20; color:${color}">${algo}</span>
        </div>
        <div class="agent-energy-bar">
          <div class="agent-energy-fill"
               style="width:${pct}%; background:${energyColor}"></div>
        </div>
        <div class="agent-stats">
          <div class="agent-stat">
            <div class="stat-key">⚡ ${i18n.agent_energy || "Energy"}</div>
            <div class="stat-val">${Number(a.energy).toFixed(1)}</div>
          </div>
          <div class="agent-stat">
            <div class="stat-key">🍎 ${i18n.agent_food || "Food"}</div>
            <div class="stat-val">${a.food_eaten}</div>
          </div>
          <div class="agent-stat">
            <div class="stat-key">🏅 ${i18n.agent_score || "Score"}</div>
            <div class="stat-val">${Number(a.score).toFixed(0)}</div>
          </div>
          <div class="agent-stat">
            <div class="stat-key">🎲 ${i18n.agent_epsilon || "Epsilon"}</div>
            <div class="stat-val">${Number(a.epsilon).toFixed(3)}</div>
          </div>
          <div class="agent-stat">
            <div class="stat-key">👣 ${i18n.agent_steps || "Steps"}</div>
            <div class="stat-val">${a.steps_alive}</div>
          </div>
          <div class="agent-stat">
            <div class="stat-key">💰 ${i18n.agent_reward || "Reward"}</div>
            <div class="stat-val">${Number(a.total_reward).toFixed(1)}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function updateStatus(running) {
  const badge = document.getElementById('status-badge');
  const text  = document.getElementById('status-text');
  badge.className = 'status-badge' + (running ? '' : ' offline');
  text.textContent = running ? (i18n.status_active || 'Training Active') : (i18n.status_waiting || 'Waiting...');
}

// ── Socket events ─────────────────────────────────────────────────────────────
socket.on('connect', () => {
  console.log('[Dashboard] Connected to server');
  updateStatus(false);
});

socket.on('disconnect', () => {
  updateStatus(false);
});

socket.on('update', (data) => {
  updateMetrics(data);
  updateCharts(data);
  updateAgents(data.agents);
  updateStatus(data.running);
});

// ── Initial fetch ─────────────────────────────────────────────────────────────
fetch('/api/state')
  .then(r => r.json())
  .then(data => {
    updateMetrics(data);
    updateCharts(data);
    updateAgents(data.agents);
    updateStatus(data.running);
  })
  .catch(err => console.warn('[Dashboard] API fetch failed:', err));
