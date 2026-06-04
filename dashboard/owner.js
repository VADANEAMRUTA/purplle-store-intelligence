const API_OWNER = 'http://localhost:8080/api';
const USER_STORAGE_KEY = 'purplleDashboardUser';
let dualAxisChart = null;
let storePieChart = null;
let stackedChart = null;
const STORAGE_OWNER = 'dashboardState_owner';
let ownerState = { marketingSpend: 120 };
let ownerApiData = null;

window.addEventListener('DOMContentLoaded', async () => {
  const user = requireAuth('owner');
  if (!user) return;

  configureRoleNavigation(user.role);
  restoreState();
  bindOwnerUI();
  initializeOwnerCharts();
  await fetchOwnerData();
  setInterval(fetchOwnerData, 3000);
});

function getCurrentUser() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
    const role = localStorage.getItem('userRole');
    if (!role) return null;
    return {
      username: localStorage.getItem('userEmail') || '',
      fullName: localStorage.getItem('userName') || '',
      role,
      lastLogin: localStorage.getItem('userLastLogin') || ''
    };
  } catch (error) {
    return null;
  }
}

function requireAuth(expectedRole) {
  const user = getCurrentUser();
  if (!user?.username) {
    window.location.href = 'login.html';
    return null;
  }
  if (user.role?.toLowerCase() !== expectedRole) {
    // Role mismatch: force re-authentication
    window.location.href = 'login.html';
    return null;
  }
  const badge = document.getElementById('userBadge');
  if (badge) {
    badge.textContent = `${user.fullName || user.username} · ${capitalize(user.role)}`;
  }
  return user;
}

function capitalize(value) {
  if (!value) return '';
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function configureRoleNavigation(currentRole) {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach((link) => {
    const href = link.getAttribute('href') || '';
    const page = href.replace('.html', '');
    if (!page || page === 'login') return;
    if (page === currentRole) {
      link.classList.add('active');
      link.classList.remove('disabled');
      link.removeAttribute('aria-disabled');
      link.removeAttribute('tabindex');
      link.style.display = '';
    } else {
      link.classList.remove('active');
      link.style.display = 'none';
    }
  });
}

function restoreState() {
  try {
    const saved = localStorage.getItem(STORAGE_OWNER);
    if (saved) ownerState = JSON.parse(saved);
  } catch (error) {
    console.warn(error);
  }
}

function persistOwnerState() {
  localStorage.setItem(STORAGE_OWNER, JSON.stringify(ownerState));
}

function bindOwnerUI() {
  const slider = document.getElementById('marketingSpend');
  slider.value = ownerState.marketingSpend;
  slider.addEventListener('input', (event) => {
    ownerState.marketingSpend = Number(event.target.value);
    persistOwnerState();
    updateRoiCalculator();
  });
  document.getElementById('logoutBtn').addEventListener('click', logout);
  const switchBtn = document.getElementById('switchUserBtn');
  if (switchBtn) switchBtn.addEventListener('click', switchUser);
  document.getElementById('exportBtn').addEventListener('click', exportOwnerReport);
}

async function fetchOwnerData(retry = 0) {
  try {
    const response = await fetch(`${API_OWNER}/dashboard/owner`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    ownerApiData = data;
    updateOwnerDashboard(data);
    setConnectionStatus(true);
    document.getElementById('lastUpdate').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    console.error('API Error:', error);
    if (retry < 2) return setTimeout(() => fetchOwnerData(retry + 1), 1000 * Math.pow(2, retry));
    setConnectionStatus(false);
    showError('Unable to fetch owner metrics. Using mock data.');
    loadMockData();
  }
}

function updateOwnerDashboard(data) {
  const weeklyData = Array.isArray(data.weeklyData) ? data.weeklyData : [];
  const labels = weeklyData.map((item) => item.day || 'Day');
  const revenueData = weeklyData.map((item) => Number(item.revenue ?? 0));
  const footfallData = weeklyData.map((item) => Number(item.footfall ?? 0));
  const revenueMonth = Number(data.totalRevenue ?? revenueData.reduce((sum, value) => sum + value, 0));
  const revenueToday = revenueData.length ? revenueData[revenueData.length - 1] : 0;
  const footfallToday = footfallData.length ? footfallData[footfallData.length - 1] : 0;
  const avgTicket = Number(data.avgTicketSize ?? (footfallToday ? Math.round(revenueToday / footfallToday) : 0));
  const growth = Number(data.growthRate ?? 0);
  const conversionRate = Number(data.conversionRate ?? 0);

  document.getElementById('revenueToday').innerText = formatCurrency(revenueToday);
  document.getElementById('revenueMonth').innerText = formatCurrency(revenueMonth);
  document.getElementById('growthRate').innerText = `${growth.toFixed(1)}%`;
  document.getElementById('avgTicket').innerText = formatCurrency(avgTicket);
  document.getElementById('revenueTodayDelta').innerText = `Conversion rate ${conversionRate.toFixed(1)}%`;
  document.getElementById('revenueMonthDelta').innerText = `Growth ${growth.toFixed(1)}%`;

  updateDualAxisChart(labels, footfallData, revenueData);
  updateStorePieChart(data.storeComparison || {});
  updateStackedBarChart(labels, footfallData, revenueData);
  renderHeatmap(weeklyData);
  renderYoYTable(revenueMonth, revenueMonth * 0.92, growth);
  updateRoiCalculator();
}

function initializeOwnerCharts() {
  const dualCtx = document.getElementById('dualAxisChart').getContext('2d');
  dualAxisChart = new Chart(dualCtx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        { label: 'Revenue', data: [], backgroundColor: 'rgba(142, 68, 173, 0.7)', yAxisID: 'y1' },
        { label: 'Footfall', data: [], type: 'line', borderColor: '#42a5f5', backgroundColor: 'rgba(66, 165, 245, 0.18)', yAxisID: 'y', tension: 0.4, pointRadius: 4 }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: '#cfd8dc' } },
        y: { position: 'left', grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#cfd8dc' }, title: { display: true, text: 'Footfall', color: '#cfd8dc' } },
        y1: { position: 'right', grid: { display: false }, ticks: { color: '#cfd8dc' }, title: { display: true, text: 'Revenue', color: '#cfd8dc' } }
      },
      plugins: { legend: { labels: { color: '#fff' } } }
    }
  });

  const pieCtx = document.getElementById('storePieChart').getContext('2d');
  storePieChart = new Chart(pieCtx, {
    type: 'doughnut',
    data: { labels: ['Downtown', 'Mall', 'Plaza'], datasets: [{ data: [1, 1, 1], backgroundColor: ['#8e44ad', '#9b59b6', '#b39ddb'] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#fff' } } } }
  });

  const stackedCtx = document.getElementById('stackedChart').getContext('2d');
  stackedChart = new Chart(stackedCtx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'Footfall', data: [], backgroundColor: '#7e57c2' }, { label: 'Revenue', data: [], backgroundColor: '#d1c4e9' }] },
    options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true, ticks: { color: '#cfd8dc' } }, y: { stacked: true, ticks: { color: '#cfd8dc' }, grid: { color: 'rgba(255,255,255,0.08)' } } }, plugins: { legend: { labels: { color: '#fff' } } } }
  });
}

function updateDualAxisChart(labels, footfall, revenue) {
  dualAxisChart.data.labels = Array.isArray(labels) ? labels : [];
  dualAxisChart.data.datasets[0].data = Array.isArray(revenue) ? revenue : [];
  dualAxisChart.data.datasets[1].data = Array.isArray(footfall) ? footfall : [];
  dualAxisChart.update();
}

function updateStorePieChart(storeComparison) {
  const labels = Object.keys(storeComparison);
  const values = Object.values(storeComparison);
  storePieChart.data.labels = labels.length ? labels : ['Store A', 'Store B', 'Store C'];
  storePieChart.data.datasets[0].data = values.length ? values : [40, 35, 25];
  storePieChart.update();
}

function updateStackedBarChart(labels, footfall, revenue) {
  const safeLabels = Array.isArray(labels) ? labels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const safeFootfall = Array.isArray(footfall) ? footfall : [];
  const safeRevenue = Array.isArray(revenue) ? revenue : [];
  stackedChart.data.labels = safeLabels.slice(0, Math.max(safeFootfall.length, safeRevenue.length, 7));
  stackedChart.data.datasets[0].data = safeFootfall;
  stackedChart.data.datasets[1].data = safeRevenue.map((value) => Math.round(value / 20));
  stackedChart.update();
}

function renderHeatmap(weeklyData) {
  const container = document.getElementById('heatmapGrid');
  container.innerHTML = '';
  const values = Array.isArray(weeklyData) ? weeklyData : [];
  const maxValue = values.length ? Math.max(...values.map((item) => Number(item.footfall ?? 0))) : 1;

  values.forEach((item, index) => {
    const value = Number(item.footfall ?? 0);
    const label = item.day || `Day ${index + 1}`;
    const intensity = Math.min(100, Math.max(20, Math.round((value / Math.max(maxValue, 1)) * 100)));
    const cell = document.createElement('div');
    cell.className = 'heatmap-cell';
    cell.innerHTML = `<strong>${label}</strong><span>${Math.round(value)} visits</span><div style="margin-top:12px; height:10px; border-radius:999px; background: rgba(255,255,255,0.08); overflow:hidden;"><div style="width:${intensity}%; height:100%; background: linear-gradient(135deg,#8e44ad,#ab47bc);"></div></div>`;
    container.appendChild(cell);
  });

  if (!values.length) {
    container.innerHTML = '<p class="mini-text">No heatmap data available.</p>';
  }
}

function renderYoYTable(current, previous, growth) {
  const body = document.getElementById('yoyTableBody');
  body.innerHTML = `
    <tr><td>Total Revenue</td><td>${formatCurrency(current)}</td><td>${formatCurrency(previous)}</td><td>${growth.toFixed(1)}%</td></tr>
    <tr><td>Footfall</td><td>${Math.round(current / 8)}</td><td>${Math.round(previous / 8)}</td><td>${growth.toFixed(1)}%</td></tr>
    <tr><td>Ticket Size</td><td>${formatCurrency(current ? Math.round(current / Math.max(1, current / 50)) : 0)}</td><td>${formatCurrency(previous ? Math.round(previous / Math.max(1, previous / 50)) : 0)}</td><td>${growth.toFixed(1)}%</td></tr>
  `;
}

function updateRoiCalculator() {
  const revenueMonth = Number(document.getElementById('revenueMonth').innerText.replace(/[^0-9]/g, '')) || 0;
  const marketingSpend = ownerState.marketingSpend;
  const roi = revenueMonth ? Math.max(0, ((revenueMonth - marketingSpend) / Math.max(marketingSpend, 1)) * 100).toFixed(1) : 0;
  document.getElementById('roiValue').innerText = `${roi}%`;
}

function setConnectionStatus(connected) {
  const dot = document.getElementById('connectionDot');
  if (dot) dot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
}

function showError(message) {
  console.error('Dashboard UI Error:', message);
  if (typeof showToast === 'function') {
    showToast(message, 'error');
  }
}

function loadMockData() {
  console.warn('Loading mock owner fallback data.');
  if (typeof updateOwnerDashboard === 'function') {
    updateOwnerDashboard({
      weeklyData: [],
      totalRevenue: 0,
      avgTicketSize: 0,
      growthRate: 0,
      conversionRate: 0,
      storeComparison: {},
      topHours: []
    });
  }
}

function formatCurrency(value) {
  return `₹${Number(value).toLocaleString('en-IN')}`;
}

function exportOwnerReport() {
  const rows = [
    { Metric: 'Revenue Today', Value: document.getElementById('revenueToday').innerText },
    { Metric: 'Revenue Month', Value: document.getElementById('revenueMonth').innerText },
    { Metric: 'Footfall Growth', Value: document.getElementById('growthRate').innerText },
    { Metric: 'Avg Ticket', Value: document.getElementById('avgTicket').innerText }
  ];
  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Owner Metrics');
  XLSX.writeFile(workbook, `purplle_owner_${new Date().toISOString().slice(0, 10)}.xlsx`);
  showToast('Owner report exported successfully.', 'success');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span><button class="toast-close" type="button">×</button>`;
  toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

function logout() {
  if (confirm('Logout and return to login?')) {
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem('userRole');
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userLastLogin');
    window.location.href = 'login.html';
  }
}

function switchUser() {
  localStorage.removeItem(USER_STORAGE_KEY);
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('userLastLogin');
  window.location.href = 'login.html';
}
