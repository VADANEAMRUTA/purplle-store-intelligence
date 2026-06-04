const API_MARKETING = 'http://localhost:8080/api';
const USER_STORAGE_KEY = 'purplleDashboardUser';
const STORAGE_MARKETING = 'dashboardState_marketing';
let campaignChart = null;
let segmentChart = null;
let forecastChart = null;
let marketingState = { boostLevel: 12 };
let campaignData = null;

window.addEventListener('DOMContentLoaded', async () => {
  const user = requireAuth('marketing');
  if (!user) return;

  configureRoleNavigation(user.role);
  restoreState();
  bindMarketingUI();
  initializeMarketingCharts();
  await fetchMarketingData();
  setInterval(fetchMarketingData, 3000);
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
    // Role mismatch - force login
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
    const saved = localStorage.getItem(STORAGE_MARKETING);
    if (saved) marketingState = JSON.parse(saved);
  } catch (error) {
    console.warn(error);
  }
}

function persistState() {
  localStorage.setItem(STORAGE_MARKETING, JSON.stringify(marketingState));
}

function bindMarketingUI() {
  const slider = document.getElementById('roiSlider');
  slider.value = marketingState.boostLevel;
  slider.addEventListener('input', (event) => {
    marketingState.boostLevel = Number(event.target.value);
    persistState();
    updateCampaignInfluence();
  });
  document.getElementById('logoutBtn').addEventListener('click', logout);
  const switchBtn = document.getElementById('switchUserBtn');
  if (switchBtn) switchBtn.addEventListener('click', switchUser);
  document.getElementById('exportBtn').addEventListener('click', exportMarketingReport);
}

async function fetchMarketingData(retry = 0) {
  try {
    const response = await fetch(`${API_MARKETING}/dashboard/marketing`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    campaignData = data;
    updateMarketingDashboard(data);
    setConnectionStatus(true);
    document.getElementById('lastUpdate').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    console.error('API Error:', error);
    if (retry < 2) return setTimeout(() => fetchMarketingData(retry + 1), 1000 * Math.pow(2, retry));
    setConnectionStatus(false);
    showError('Unable to load marketing data. Using mock data.');
    loadMockData();
  }
}

function initializeMarketingCharts() {
  const campaignCtx = document.getElementById('campaignChart').getContext('2d');
  campaignChart = new Chart(campaignCtx, {
    type: 'bar',
    data: { labels: ['Before', 'During', 'After'], datasets: [{ label: 'Conversion Impact', data: [0, 0, 0], backgroundColor: ['#4caf50', '#81c784', '#a5d6a7'] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#cfd8dc' } }, y: { ticks: { color: '#cfd8dc' }, grid: { color: 'rgba(255,255,255,0.08)' } } } }
  });

  const segmentCtx = document.getElementById('segmentChart').getContext('2d');
  segmentChart = new Chart(segmentCtx, {
    type: 'doughnut',
    data: { labels: ['New', 'Returning'], datasets: [{ data: [0, 0], backgroundColor: ['#4caf50', '#81c784'] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#fff' } } } }
  });

  const forecastCtx = document.getElementById('forecastChart').getContext('2d');
  forecastChart = new Chart(forecastCtx, {
    type: 'line',
    data: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], datasets: [{ label: 'Forecast', data: [0, 0, 0, 0, 0, 0, 0], borderColor: '#4caf50', backgroundColor: 'rgba(76,175,80,0.16)', fill: true, tension: 0.4 }] },
    options: { responsive: true, maintainAspectRatio: false, scales: { x: { ticks: { color: '#cfd8dc' } }, y: { ticks: { color: '#cfd8dc' }, grid: { color: 'rgba(255,255,255,0.08)' } } }, plugins: { legend: { display: false } } }
  });
}

function updateMarketingDashboard(data) {
  document.getElementById('newCustomers').innerText = data.newCustomers ?? 0;
  document.getElementById('returningCustomers').innerText = data.returningCustomers ?? 0;
  document.getElementById('promotionROI').innerText = data.promotionROI ?? '0%';
  document.getElementById('bestHours').innerText = (data.topHours || []).join(', ') || '--';

  const impact = data.campaignImpact || { before: 0, during: 0, after: 0 };
  campaignChart.data.datasets[0].data = [impact.before, impact.during, impact.after];
  campaignChart.update();

  segmentChart.data.datasets[0].data = [data.newCustomers ?? 0, data.returningCustomers ?? 0];
  segmentChart.update();

  renderHeatmap(data.heatmapData || []);
  renderWeatherCards(data.weatherCorrelation || {});
  renderForecast(data.topHours || []);
  updateCampaignInfluence();
}

function renderHeatmap(rows) {
  const container = document.getElementById('heatmapGrid');
  container.innerHTML = '';
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const values = Array.isArray(rows) ? rows : [];
  const maxValue = values.length ? Math.max(...values) : 1;

  if (!values.length) {
    container.innerHTML = '<p class="mini-text">No heatmap data available.</p>';
    return;
  }

  values.slice(0, 7).forEach((value, index) => {
    const intensity = Math.min(100, Math.max(20, Math.round((value / Math.max(maxValue, 1)) * 100)));
    const cell = document.createElement('div');
    cell.className = 'heatmap-cell';
    cell.innerHTML = `<strong>${days[index]}</strong><span>${Math.round(value)} impressions</span><div style="margin-top: 10px; height: 10px; background: rgba(255,255,255,0.08); border-radius: 999px;"><div style="width:${intensity}%;height:100%;background: linear-gradient(135deg, #4caf50, #81c784);"></div></div>`;
    container.appendChild(cell);
  });
}

function renderWeatherCards(weather) {
  const container = document.getElementById('weatherCards');
  container.innerHTML = '';
  const entries = Object.entries(weather);
  if (!entries.length) {
    container.innerHTML = '<p class="mini-text">No weather correlation data available.</p>';
    return;
  }
  entries.forEach(([condition, effect]) => {
    const card = document.createElement('div');
    card.className = 'weather-card';
    card.innerHTML = `<h4>${condition}</h4><p>${effect} impact on footfall</p>`;
    container.appendChild(card);
  });
}

function renderForecast(hours) {
  const ongoing = Array.isArray(hours) ? hours : [];
  forecastChart.data.datasets[0].data = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((_, index) => 60 + index * 5 + (ongoing[index] ? 5 : 0));
  forecastChart.update();
}

function updateCampaignInfluence() {
  const boost = marketingState.boostLevel;
  const impact = campaignData?.campaignImpact || { before: 0, during: 0, after: 0 };
  campaignChart.data.datasets[0].data = [
    Math.round(impact.before * (1 + boost / 100) * 1.05),
    Math.round(impact.during * (1 + boost / 100) * 1.08),
    Math.round(impact.after * (1 + boost / 100) * 1.03)
  ];
  campaignChart.update();
  document.getElementById('promotionROI').innerText = `${Math.max(0, 12 + boost * 0.4).toFixed(1)}%`;
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
  console.warn('Loading mock marketing fallback data.');
  if (typeof updateMarketingDashboard === 'function') {
    updateMarketingDashboard({
      newCustomers: 0,
      returningCustomers: 0,
      promotionROI: '0%',
      topHours: [],
      campaignImpact: { before: 0, during: 0, after: 0 },
      heatmapData: [],
      weatherCorrelation: {}
    });
  }
}

function exportMarketingReport() {
  if (!campaignData) {
    showToast('Please wait for the dashboard to load.', 'warning');
    return;
  }
  const report = [
    { Metric: 'New Customers', Value: campaignData.newCustomers ?? 0 },
    { Metric: 'Returning Customers', Value: campaignData.returningCustomers ?? 0 },
    { Metric: 'Promotional ROI', Value: campaignData.promotionROI ?? '0%' },
    { Metric: 'Best Hours', Value: (campaignData.topHours || []).join(', ') }
  ];
  const worksheet = XLSX.utils.json_to_sheet(report);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Marketing Metrics');
  XLSX.writeFile(workbook, `purplle_marketing_${new Date().toISOString().slice(0, 10)}.xlsx`);
  showToast('Marketing export complete.', 'success');
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
