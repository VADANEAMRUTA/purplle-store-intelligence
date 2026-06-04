// Initialize session on page load
// Clears stale session data and ensures proper authentication flow

(function() {
  'use strict';
  
  const SESSION_KEY = 'purplleDashboardUser';
  const ROLE_KEY = 'userRole';
  
  // Check if this is a fresh browser session
  if (!sessionStorage.getItem('sessionStarted')) {
    // Fresh session - clear old login data if browser was closed
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem('userName');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userLastLogin');
    sessionStorage.setItem('sessionStarted', 'true');
  }
  
  // Redirect unauthenticated users to login
  function requireLogin() {
    const user = localStorage.getItem(SESSION_KEY);
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const loginPages = ['login.html', 'index.html'];
    
    if (!user && !loginPages.includes(currentPage)) {
      window.location.href = 'login.html';
    }
  }
  
  // Only execute if not on a login page
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', requireLogin);
  } else {
    requireLogin();
  }
  
  // Clear session on browser close
  window.addEventListener('beforeunload', function() {
    // Keep the session for tab refresh, but this helps with proper cleanup
  });
  
})();
