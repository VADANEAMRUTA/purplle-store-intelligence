const API_BASE_URL = 'http://localhost:8080/api';
const USER_STORAGE_KEY = 'purplleDashboardUser';
let authMode = 'login';

window.addEventListener('DOMContentLoaded', () => {
  const user = getCurrentUser();
  if (user?.username) {
    redirectToRole(user.role);
    return;
  }

  document.getElementById('loginTab').addEventListener('click', () => setMode('login'));
  document.getElementById('registerTab').addEventListener('click', () => setMode('register'));
  document.getElementById('authForm').addEventListener('submit', handleSubmit);
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

function setMode(mode) {
  authMode = mode;
  document.getElementById('loginTab').classList.toggle('active', mode === 'login');
  document.getElementById('registerTab').classList.toggle('active', mode === 'register');
  document.getElementById('registerFields').style.display = mode === 'register' ? 'grid' : 'none';
  document.getElementById('submitBtn').textContent = mode === 'login' ? 'Login' : 'Register';
}

async function handleSubmit(event) {
  event.preventDefault();
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();
  const fullName = document.getElementById('fullName').value.trim();
  const role = document.getElementById('role').value;

  if (!username || !password) {
    showToast('Username and password are required.', 'error');
    return;
  }

  if (authMode === 'login') {
    await loginUser({ username, password });
  } else {
    await registerUser({ username, password, fullName, role });
  }
}

async function loginUser(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      const localUser = findLocalUser(payload.username, payload.password);
      if (localUser) {
        persistUserSession(localUser);
        showToast('Login successful (local demo account)!', 'success');
        redirectToRole(localUser.role);
        return;
      }
      showToast(data.message || 'Login failed.', 'error');
      return;
    }

    persistUserSession({
      username: data.username,
      role: data.role,
      fullName: data.fullName,
      email: data.username,
      lastLogin: data.lastLogin
    });
    showToast('Login successful!', 'success');
    redirectToRole(data.role);
  } catch (error) {
    console.error(error);
    const localUser = findLocalUser(payload.username, payload.password);
    if (localUser) {
      persistUserSession(localUser);
      showToast('Login successful (local demo account)!', 'success');
      redirectToRole(localUser.role);
      return;
    }
    showToast('Unable to reach authentication server.', 'error');
  }
}

async function registerUser(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      showToast(data.message || 'Registration failed.', 'error');
      return;
    }
    saveLocalUser({
      username: data.username,
      password: payload.password,
      role: data.role,
      fullName: data.fullName,
      email: data.username,
      lastLogin: data.lastLogin
    });
    showToast('Registration complete. Please login.', 'success');
    setMode('login');
  } catch (error) {
    console.error(error);
    saveLocalUser({
      username: payload.username,
      role: payload.role,
      fullName: payload.fullName,
      email: payload.username,
      lastLogin: new Date().toISOString()
    });
    showToast('Saved locally for demo. Please login.', 'success');
    setMode('login');
  }
}

function saveLocalUser(user) {
  const localUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
  const filtered = localUsers.filter((existing) => existing.username !== user.username);
  filtered.push(user);
  localStorage.setItem('registeredUsers', JSON.stringify(filtered));
}

function findLocalUser(username, password) {
  const localUsers = JSON.parse(localStorage.getItem('registeredUsers') || '[]');
  return localUsers.find((user) => user.username === username && user.password === password);
}

function persistUserSession(user) {
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify({
    username: user.username,
    role: user.role,
    fullName: user.fullName,
    email: user.email,
    lastLogin: user.lastLogin
  }));
  localStorage.setItem('userRole', user.role);
  localStorage.setItem('userName', user.fullName || user.username);
  localStorage.setItem('userEmail', user.email || user.username);
  localStorage.setItem('userLastLogin', user.lastLogin || new Date().toISOString());
}

function redirectToRole(role) {
  const redirectMap = {
    manager: 'manager.html',
    owner: 'owner.html',
    security: 'security.html',
    marketing: 'marketing.html'
  };
  window.location.href = redirectMap[role?.toLowerCase()] || 'manager.html';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span><button type="button">×</button>`;
  toast.querySelector('button').addEventListener('click', () => toast.remove());
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}
