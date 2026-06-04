const API_BASE = 'http://localhost:8080/api';
const ROLE = 'manager';
const STORAGE_KEY = 'dashboardState_manager';
const USER_STORAGE_KEY = 'purplleDashboardUser';
let trendChart = null;
let occupancyGauge = null;
let refreshTimer = null;
let allEvents = [];
let currentData = null;
let alertAcknowledged = false;
let audioAlertPlaying = false;
let pageState = {
  dateRange: 'today',
  startDate: '',
  endDate: '',
  eventFilter: 'all',
  eventSearch: '',
  currentPage: 1
};
const PAGE_SIZE = 8;

document.addEventListener('DOMContentLoaded', async () => {
  const user = requireAuth('manager');
  if (!user) return;

  configureRoleNavigation(user.role);
  restoreState();
  bindUI();
  initializeCharts();
  await fetchDashboardData();
  checkOvercrowding();
  startAutoRefresh();
  setInterval(checkOvercrowding, 3000);
  updateRealTimeClock();
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
    // Role mismatch: force re-authentication at login
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

function bindUI() {
  document.getElementById('dateRange').value = pageState.dateRange;
  document.getElementById('eventFilter').value = pageState.eventFilter;
  document.getElementById('eventSearch').value = pageState.eventSearch;

  document.getElementById('dateRange').addEventListener('change', handleRangeChange);
  document.getElementById('applyDateRange').addEventListener('click', applyCustomRange);
  document.getElementById('eventFilter').addEventListener('change', handleFilterChange);
  document.getElementById('eventSearch').addEventListener('input', debounce(handleSearchInput, 250));
  document.getElementById('exportBtn').addEventListener('click', exportToExcel);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  const switchBtn = document.getElementById('switchUserBtn');
  if (switchBtn) switchBtn.addEventListener('click', switchUser);
  const acknowledgeBtn = document.getElementById('acknowledgeBtn');
  if (acknowledgeBtn) acknowledgeBtn.addEventListener('click', acknowledgeAlert);
  if ('Notification' in window) {
    Notification.requestPermission().catch(() => {});
  }
}

function restoreState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      Object.assign(pageState, JSON.parse(saved));
    }
  } catch (error) {
    console.warn('Unable to restore state', error);
  }
}

function persistState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(pageState));
  } catch (error) {
    console.warn('Unable to persist state', error);
  }
}

function handleRangeChange(event) {
  const value = event.target.value;
  pageState.dateRange = value;
  persistState();

  const startInput = document.getElementById('startDate');
  const endInput = document.getElementById('endDate');
  if (value === 'custom') {
    startInput.classList.remove('hide');
    endInput.classList.remove('hide');
    const today = new Date().toISOString().slice(0, 10);
    if (!startInput.value) startInput.value = today;
    if (!endInput.value) endInput.value = today;
  } else {
    startInput.classList.add('hide');
    endInput.classList.add('hide');
  }
}

function applyCustomRange() {
  const dateRange = document.getElementById('dateRange').value;
  if (dateRange === 'custom') {
    pageState.startDate = document.getElementById('startDate').value;
    pageState.endDate = document.getElementById('endDate').value;
  }
  pageState.currentPage = 1;
  persistState();
  showToast('Date range updated', 'success');
}

function handleFilterChange(event) {
  pageState.eventFilter = event.target.value;
  pageState.currentPage = 1;
  persistState();
  renderEventsTable();
}

function handleSearchInput(event) {
  pageState.eventSearch = event.target.value.trim();
  pageState.currentPage = 1;
  persistState();
  renderEventsTable();
}

async function fetchDashboardData(retryCount = 0) {
  showLoading(true);
  try {
    const response = await fetch(`${API_BASE}/dashboard/${ROLE}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    currentData = data;
    updateDashboard(data);
    setConnectionStatus(true);
    updateLastUpdate();
  } catch (error) {
    console.error('API Error:', error);
    if (retryCount < 2) {
      await delay(1000 * Math.pow(2, retryCount));
      return fetchDashboardData(retryCount + 1);
    }
    setConnectionStatus(false);
    showError('Unable to load dashboard data. Using mock data.');
    loadMockData();
  } finally {
    showLoading(false);
  }
}

function showLoading(isLoading) {
  const main = document.querySelector('.main-panel');
  if (!main) return;
  let overlay = document.getElementById('loadingOverlay');
  if (isLoading) {
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'loadingOverlay';
      overlay.className = 'loading-overlay';
      overlay.innerHTML = '<div class="loading-skeleton"></div>';
      main.appendChild(overlay);
    }
  } else if (overlay) {
    overlay.remove();
  }
}

function updateDashboard(data) {
  updateKPIs(data);
  updateCharts(data);
  renderEvents(data.recentEvents || []);
  updateStaffRecommendation(data);
  renderAlerts(data);
}

function updateKPIs(data) {
  document.getElementById('occupancy').innerText = data.currentOccupancy ?? 0;
  document.getElementById('entries').innerText = data.todayEntries ?? 0;
  document.getElementById('exits').innerText = data.todayExits ?? 0;
  document.getElementById('conversion').innerText = data.conversionRate ?? '0%';

  const occupancyPercent = Math.min(100, Math.max(0, ((data.currentOccupancy ?? 0) / 50) * 100));
  const conversionPercent = Math.min(100, Math.max(0, parseFloat((data.conversionRate ?? '0').toString())));

  document.getElementById('capacityFill').style.width = `${occupancyPercent}%`;
  document.getElementById('conversionFill').style.width = `${conversionPercent}%`;
  document.getElementById('conversionFill').style.background = conversionPercent > 70 ? '#4caf50' : conversionPercent > 40 ? '#ffb300' : '#f44336';

  document.getElementById('occupancyAlert').innerText = data.staffAlert ?? 'No alerts at the moment';
  document.getElementById('entriesTrend').innerText = `Entries: ${data.todayEntries ?? 0} today`;
  document.getElementById('exitsTrend').innerText = `Exits: ${data.todayExits ?? 0} today`;
}

function initializeCharts() {
  const trendCtx = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(trendCtx, {
    type: 'line',
    data: {
      labels: Array.from({ length: 12 }, (_, index) => `${(new Date().getHours() - 11 + index + 24) % 24}:00`),
      datasets: [{ label: 'Footfall', data: Array(12).fill(0), borderColor: '#42a5f5', backgroundColor: 'rgba(66,165,245,0.18)', fill: true, tension: 0.4, pointRadius: 4 }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#cfd8dc' } },
        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.08)' }, ticks: { color: '#cfd8dc' } }
      },
      interaction: { intersect: false, mode: 'index' }
    }
  });

  const gaugeCtx = document.getElementById('occupancyGauge').getContext('2d');
  occupancyGauge = new Chart(gaugeCtx, {
    type: 'doughnut',
    data: { labels: ['Occupancy', 'Remaining'], datasets: [{ data: [0, 50], backgroundColor: ['#2196F3', 'rgba(255,255,255,0.12)'], borderWidth: 0 }] },
    options: { cutout: '68%', responsive: true, maintainAspectRatio: true, plugins: { legend: { display: false } } }
  });
}

function updateCharts(data) {
  if (!trendChart || !occupancyGauge) return;
  const hourly = Array.isArray(data.hourlyTrends) ? data.hourlyTrends.slice(-12) : Array(12).fill(0);
  trendChart.data.datasets[0].data = hourly.length ? hourly : Array(12).fill(0);
  trendChart.update();

  const occupancy = Math.min(50, Math.max(0, data.currentOccupancy ?? 0));
  occupancyGauge.data.datasets[0].data = [occupancy, Math.max(0, 50 - occupancy)];
  occupancyGauge.update();
}

function renderEvents(events) {
  allEvents = events.map((event) => ({
    timestamp: event.timestamp,
    personId: event.personId ?? 'unknown',
    eventType: (event.event || event.eventType || 'UNKNOWN').toString(),
    dwellTimeSeconds: event.dwellTimeSeconds ?? 0
  }));
  pageState.currentPage = 1;
  persistState();
  renderEventsTable();
}

function renderEventsTable() {
  const searchTerm = pageState.eventSearch.toLowerCase();
  const filtered = allEvents.filter((item) => {
    const matchesSearch = item.personId.toString().toLowerCase().includes(searchTerm) || item.eventType.toLowerCase().includes(searchTerm);
    const matchesFilter = pageState.eventFilter === 'all' || item.eventType.toUpperCase() === pageState.eventFilter;
    return matchesSearch && matchesFilter;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  pageState.currentPage = Math.min(pageState.currentPage, totalPages);
  persistState();

  const start = (pageState.currentPage - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(start, start + PAGE_SIZE);

  const body = document.getElementById('eventsTableBody');
  if (!body) return;

  if (!pageItems.length) {
    body.innerHTML = '<tr><td colspan="5" class="mini-text">No matching events found.</td></tr>';
  } else {
    body.innerHTML = pageItems
      .map((item) => `<tr class="fade-up"><td>${formatTimestamp(item.timestamp)}</td><td>${item.personId}</td><td><span class="badge-pill ${item.eventType.toLowerCase()}">${item.eventType}</span></td><td>${formatDwell(item.dwellTimeSeconds)}</td><td><button class="action-button" onclick="showPersonDetails('${item.personId}')">View</button></td></tr>`)
      .join('');
  }

  renderPagination(filtered.length, totalPages);
}

function renderPagination(totalItems, totalPages) {
  const container = document.getElementById('pagination');
  if (!container) return;
  container.innerHTML = '';

  for (let page = 1; page <= totalPages; page += 1) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `page-button${page === pageState.currentPage ? ' active' : ''}`;
    button.textContent = page;
    button.addEventListener('click', () => {
      pageState.currentPage = page;
      persistState();
      renderEventsTable();
    });
    container.appendChild(button);
  }
}

function updateStaffRecommendation(data) {
  const container = document.getElementById('staffRecommendation');
  if (!container) return;

  const occupancy = data.currentOccupancy ?? 0;
  const recommendation = occupancy > 40 ? 'Add two or more staff members immediately.' : occupancy > 30 ? 'Add one staff member to checkout.' : occupancy > 20 ? 'Staffing is balanced for peak traffic.' : 'Current staff levels are sufficient.';
  const meterValue = Math.min(100, Math.max(0, (occupancy / 50) * 100));

  container.innerHTML = `
    <div class="staff-recommendation">
      <h4>Recommended Action</h4>
      <p>${recommendation}</p>
      <div class="staff-meter"><div class="meter-fill" style="width:${meterValue}%"></div></div>
      <div class="progress-labels"><span>${Math.ceil(occupancy / 5)} staff suggested</span><span>${meterValue.toFixed(0)}%</span></div>
    </div>
  `;
}

function renderAlerts(data) {
  const feed = document.getElementById('alertFeed');
  if (!feed) return;

  const alerts = [];
  if ((data.currentOccupancy ?? 0) > 40) {
    alerts.push({ label: 'High occupancy detected', severity: 'alert' });
  }
  if (data.staffAlert) {
    alerts.push({ label: data.staffAlert, severity: 'alert' });
  }
  if (!alerts.length) {
    feed.innerHTML = '<p class="mini-text">No active alerts at this moment.</p>';
    return;
  }

  feed.innerHTML = alerts.map((item) => `<div class="alert-pill"><span>${item.label}</span></div>`).join('');
}

function checkOvercrowding() {
  fetch(`${API_BASE}/alerts/overcrowding`)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((alert) => {
      updateAlertUI(alert);
      if (!alertAcknowledged) {
        if (alert.level === 'CRITICAL') {
          playAlertSound();
          showNotification('⚠️ OVERCROWDING ALERT! Store capacity exceeded!', 'critical');
        } else if (alert.level === 'WARNING') {
          playWarningSound();
        }
      }
    })
    .catch((error) => {
      console.error('Alert check failed:', error);
    });
}

function updateAlertUI(alert) {
  const fill = document.getElementById('occupancyMeterFill');
  if (fill) {
    const percentage = Math.min(100, Math.max(0, (Number(alert.currentOccupancy || 0) / Number(alert.maxCapacity || 50)) * 100));
    fill.style.width = `${percentage}%`;
    fill.style.backgroundColor = alert.color || 'green';
  }

  const currentEl = document.getElementById('currentOccupancyAlert');
  const maxEl = document.getElementById('maxCapacity');
  const safeEl = document.getElementById('safeSpace');
  const messageEl = document.getElementById('alertMessage');
  const actionEl = document.getElementById('alertAction');
  const badge = document.getElementById('alertLevel');
  const acknowledgeBtn = document.getElementById('acknowledgeBtn');

  if (currentEl) currentEl.innerText = alert.currentOccupancy ?? 0;
  if (maxEl) maxEl.innerText = alert.maxCapacity ?? 50;
  if (safeEl) safeEl.innerText = alert.safeSpace ?? 0;
  if (messageEl) {
    messageEl.innerText = alert.message || 'No current overcrowding alerts.';
    messageEl.className = `alert-message ${alert.level?.toLowerCase() ?? 'normal'}`;
  }
  if (actionEl) {
    actionEl.innerHTML = `<i class="fas fa-bullhorn"></i> Recommended Action: ${alert.action || 'Continue normal operations'}`;
  }
  if (badge) {
    badge.innerText = alert.level ?? 'NORMAL';
    badge.className = `alert-badge ${alert.level?.toLowerCase() ?? 'normal'}`;
  }

  if (alert.level !== 'NORMAL') {
    if (acknowledgeBtn) acknowledgeBtn.style.display = 'block';
  } else if (acknowledgeBtn) {
    acknowledgeBtn.style.display = 'none';
    alertAcknowledged = false;
  }
}

function playAlertSound() {
  if (audioAlertPlaying) return;
  audioAlertPlaying = true;

  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  oscillator.frequency.value = 880;
  gainNode.gain.value = 0.5;
  oscillator.start();
  setTimeout(() => {
    oscillator.stop();
    audioAlertPlaying = false;
  }, 1000);
}

function playWarningSound() {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const oscillator = audioContext.createOscillator();
  const gainNode = audioContext.createGain();

  oscillator.connect(gainNode);
  gainNode.connect(audioContext.destination);
  oscillator.frequency.value = 440;
  gainNode.gain.value = 0.3;
  oscillator.start();
  setTimeout(() => oscillator.stop(), 500);
}

function acknowledgeAlert() {
  alertAcknowledged = true;
  const acknowledgeBtn = document.getElementById('acknowledgeBtn');
  if (acknowledgeBtn) acknowledgeBtn.style.display = 'none';
  showToast('Alert acknowledged. Monitoring continues.', 'info');

  fetch(`${API_BASE}/alerts/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acknowledged: true, timestamp: new Date().toISOString() })
  }).catch((error) => console.error('Acknowledge failed:', error));
}

function showNotification(message, type) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('Purplle Alert', { body: message });
  }
  showToast(message, type);
}

function setConnectionStatus(connected) {
  const dot = document.getElementById('connectionDot');
  if (!dot) return;
  dot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
}

function showError(message) {
  console.error('Dashboard UI Error:', message);
  if (typeof showToast === 'function') {
    showToast(message, 'error');
  }
}

function loadMockData() {
  console.warn('Loading mock dashboard fallback data.');
  if (typeof updateDashboard === 'function') {
    updateDashboard({
      currentOccupancy: 0,
      todayEntries: 0,
      todayExits: 0,
      conversionRate: '0%',
      recentEvents: [],
      staffAlert: 'No alerts available.'
    });
  }
}

function updateLastUpdate() {
  const element = document.getElementById('lastUpdate');
  if (!element) return;
  element.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
}

function updateRealTimeClock() {
  setInterval(() => updateLastUpdate(), 1000);
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(fetchDashboardData, 3000);
}

function formatTimestamp(timestamp) {
  return timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--';
}

function formatDwell(seconds) {
  const mins = Math.floor(seconds / 60);
  return `${mins} min`;
}

function showPersonDetails(personId) {
  showToast(`Person details view opened for ${personId}`, 'info');
}

function exportToExcel() {
  if (!currentData) {
    showToast('No data available to export.', 'error');
    return;
  }

  const rows = allEvents.map((event) => ({
    time: formatTimestamp(event.timestamp),
    personId: event.personId,
    event: event.eventType,
    dwellTime: formatDwell(event.dwellTimeSeconds)
  }));

  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Events');
  XLSX.writeFile(workbook, `purplle_manager_${new Date().toISOString().slice(0, 10)}.xlsx`);
  showToast('Export completed successfully.', 'success');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button class="toast-close" type="button">×</button>
  `;
  toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function debounce(fn, wait) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), wait);
  };
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
