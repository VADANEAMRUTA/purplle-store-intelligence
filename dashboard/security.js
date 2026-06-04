const API_SECURITY = 'http://localhost:8080/api';
const USER_STORAGE_KEY = 'purplleDashboardUser';
const STORAGE_SECURITY = 'dashboardState_security';
let soundEnabled = true;
let cameraCanvas = null;
let ctx = null;
let people = [];
let zones = [];
let incidentData = [];

window.addEventListener('DOMContentLoaded', async () => {
  const user = requireAuth('security');
  if (!user) return;

  configureRoleNavigation(user.role);
  cameraCanvas = document.getElementById('cameraFeed');
  ctx = cameraCanvas.getContext('2d');
  restoreState();
  initializeSimulation();
  bindSecurityUI();
  await fetchSecurityData();
  setInterval(fetchSecurityData, 3000);
  requestAnimationFrame(stepSimulation);
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
    // Role mismatch - force re-login
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
    const saved = localStorage.getItem(STORAGE_SECURITY);
    if (saved) {
      const state = JSON.parse(saved);
      soundEnabled = state.soundEnabled ?? true;
    }
  } catch (error) {
    console.warn(error);
  }
}

function persistState() {
  localStorage.setItem(STORAGE_SECURITY, JSON.stringify({ soundEnabled }));
}

function bindSecurityUI() {
  document.getElementById('soundToggleBtn').addEventListener('click', toggleSound);
  document.getElementById('screenshotBtn').addEventListener('click', captureSnapshot);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  const switchBtn = document.getElementById('switchUserBtn');
  if (switchBtn) switchBtn.addEventListener('click', switchUser);
}

function initializeSimulation() {
  for (let i = 0; i < 10; i += 1) {
    people.push({
      id: 100 + i,
      x: 80 + Math.random() * 760,
      y: 60 + Math.random() * 220,
      vx: (Math.random() - 0.5) * 2,
      vy: (Math.random() - 0.5) * 2,
      loiter: 0,
      zone: ''
    });
  }
  zones = ['Entrance', 'Aisle', 'Checkout', 'Fitting'];
}

function stepSimulation() {
  ctx.clearRect(0, 0, cameraCanvas.width, cameraCanvas.height);
  ctx.fillStyle = '#0d1225';
  ctx.fillRect(0, 0, cameraCanvas.width, cameraCanvas.height);
  drawZones();
  people.forEach((person) => {
    person.x += person.vx;
    person.y += person.vy;
    if (person.x < 40 || person.x > cameraCanvas.width - 40) person.vx *= -1;
    if (person.y < 40 || person.y > cameraCanvas.height - 40) person.vy *= -1;
    person.zone = zones[Math.floor((person.x / cameraCanvas.width) * zones.length)];
    person.loiter += 0.03;
    drawPerson(person);
  });
  requestAnimationFrame(stepSimulation);
}

function drawZones() {
  const zoneWidth = cameraCanvas.width / zones.length;
  zones.forEach((zone, index) => {
    ctx.fillStyle = index % 2 === 0 ? 'rgba(255, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';
    ctx.fillRect(zoneWidth * index, 0, zoneWidth, cameraCanvas.height);
    ctx.fillStyle = 'rgba(255,255,255,0.18)';
    ctx.font = '14px Inter';
    ctx.fillText(zone, zoneWidth * index + 14, 26);
  });
}

function drawPerson(person) {
  ctx.beginPath();
  ctx.fillStyle = '#4caf50';
  ctx.arc(person.x, person.y, 14, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = '#fff';
  ctx.font = '11px Inter';
  ctx.fillText(`ID ${person.id}`, person.x - 20, person.y - 18);
  if (person.loiter > 8) {
    ctx.strokeStyle = '#ffeb3b';
    ctx.lineWidth = 2;
    ctx.strokeRect(person.x - 22, person.y - 22, 44, 44);
  }
}

async function fetchSecurityData(retry = 0) {
  try {
    const response = await fetch(`${API_SECURITY}/dashboard/security`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    incidentData = Array.isArray(data.incidents) ? data.incidents : [];
    updateSecurityMetrics(data);
    renderIncidentTimeline(incidentData);
    setConnectionStatus(true);
    document.getElementById('lastUpdate').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    console.error('API Error:', error);
    if (retry < 2) return setTimeout(() => fetchSecurityData(retry + 1), 1000 * Math.pow(2, retry));
    setConnectionStatus(false);
    showError('Unable to load security metrics. Using mock data.');
    loadMockData();
  }
}

function updateSecurityMetrics(data) {
  document.getElementById('currentOccupancy').textContent = data.currentOccupancy ?? 0;
  const suspicious = Array.isArray(data.suspiciousPersons) ? data.suspiciousPersons.length : 0;
  document.getElementById('suspiciousCount').textContent = suspicious;
  document.getElementById('blacklistMatches').textContent = Math.min(suspicious, 3);
  document.getElementById('alertSummary').textContent = suspicious ? 'Suspicious activity detected.' : 'No critical incidents.';
  document.getElementById('distanceStatus').textContent = `Estimated social distance score: ${randomScore()}%`;
  document.getElementById('loiteringStatus').textContent = `Loitering events: ${incidentData.filter((item) => item.severity && item.severity !== 'Info').length}`;
}

function renderIncidentTimeline(incidents) {
  const body = document.getElementById('incidentBody');
  if (!body) return;
  if (!incidents.length) {
    body.innerHTML = '<tr><td colspan="4" class="mini-text">No incidents reported.</td></tr>';
    return;
  }
  body.innerHTML = incidents.slice(0, 10).map((incident) => `<tr><td>${formatTime(incident.timestamp)}</td><td>${incident.type || 'Unknown'}</td><td>${incident.personId ?? 'Unknown'}</td><td>${incident.severity ?? 'Info'}</td></tr>`).join('');
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  persistState();
  const button = document.getElementById('soundToggleBtn');
  button.innerHTML = `<i class="fas fa-bell"></i> ${soundEnabled ? 'Sound Alerts On' : 'Sound Alerts Off'}`;
  if (soundEnabled) playTone();
}

function playTone() {
  try {
    const audio = new Audio('data:audio/wav;base64,UklGRiIAAABXQVZFZm10IBAAAAABAAEAESsAABErAAABAAgAZGF0YQAAAAA=');
    audio.volume = 0.25;
    audio.play();
  } catch (error) {
    console.warn('Unable to play sound', error);
  }
}

function captureSnapshot() {
  const snapshot = cameraCanvas.toDataURL('image/png');
  const preview = window.open('', '_blank');
  preview.document.write(`<html><body style="margin:0;background:#08111f;"><img src="${snapshot}" style="width:100%;height:auto;display:block;" /></body></html>`);
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
  console.warn('Loading mock security fallback data.');
  const mock = {
    currentOccupancy: 0,
    suspiciousPersons: [],
    incidents: []
  };
  updateSecurityMetrics(mock);
  renderIncidentTimeline([]);
}

function formatTime(timestamp) {
  return timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--';
}

function randomScore() {
  return Math.floor(75 + Math.random() * 20);
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
