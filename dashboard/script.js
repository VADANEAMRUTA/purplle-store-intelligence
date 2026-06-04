// API Configuration
const API_BASE_URL = 'http://localhost:8080/api';
let updateInterval = null;

// DOM Elements
const occupancyEl = document.getElementById('occupancy');
const entriesEl = document.getElementById('entries');
const exitsEl = document.getElementById('exits');
const dwellTimeEl = document.getElementById('dwellTime');
const alertContainer = document.getElementById('alertContainer');
const alertMessageEl = document.getElementById('alertMessage');
const eventsBody = document.getElementById('eventsBody');
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');

// Fetch dashboard statistics
async function fetchDashboardStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // Update stats
        occupancyEl.textContent = data.occupancy || 0;
        entriesEl.textContent = data.entries || 0;
        exitsEl.textContent = data.exits || 0;
        
        const dwellMinutes = data.averageDwellMinutes || 0;
        dwellTimeEl.textContent = `${dwellMinutes} min`;
        
        // Handle alerts
        if (data.alert) {
            alertContainer.style.display = 'block';
            alertMessageEl.textContent = data.alert;
        } else {
            alertContainer.style.display = 'none';
        }
        
        // Update status
        statusIndicator.classList.remove('disconnected');
        statusText.textContent = 'Connected to API';
        
        return data;
    } catch (error) {
        console.error('Error fetching dashboard:', error);
        statusIndicator.classList.add('disconnected');
        statusText.textContent = 'API disconnected';
        return null;
    }
}

// Fetch recent events
async function fetchRecentEvents() {
    try {
        const response = await fetch(`${API_BASE_URL}/events/recent`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const events = await response.json();
        
        if (!events || events.length === 0) {
            eventsBody.innerHTML = '<tr><td colspan="5" class="loading">No events yet</td></tr>';
            return;
        }
        
        // Clear table
        eventsBody.innerHTML = '';
        
        // Add events to table
        events.forEach(event => {
            const row = eventsBody.insertRow();
            row.className = event.event === 'ENTRY' ? 'entry' : 'exit';
            
            // Format time
            const eventTime = new Date(event.timestamp);
            const formattedTime = eventTime.toLocaleTimeString();
            const formattedDate = eventTime.toLocaleDateString();
            
            row.insertCell(0).textContent = `${formattedDate} ${formattedTime}`;
            row.insertCell(1).textContent = event.personId || '-';
            row.insertCell(2).textContent = event.event || '-';
            row.insertCell(3).textContent = event.cameraId || 'ENTRANCE_01';
            row.insertCell(4).textContent = event.zoneId || 'MAIN_DOOR';
            
            // Add dwell time if available
            if (event.event === 'EXIT' && event.dwellTimeSeconds) {
                const dwellMinutes = Math.floor(event.dwellTimeSeconds / 60);
                const dwellSeconds = event.dwellTimeSeconds % 60;
                row.cells[2].title = `Dwell time: ${dwellMinutes}m ${dwellSeconds}s`;
            }
        });
        
    } catch (error) {
        console.error('Error fetching events:', error);
        eventsBody.innerHTML = '<tr><td colspan="5" class="loading">Failed to load events</td></tr>';
    }
}

// Test API connection
async function testAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('✅ API is reachable');
            return true;
        }
        console.log('❌ API returned non-ok status:', response.status);
    } catch (error) {
        console.log('❌ API not reachable:', error.message);
    }
    return false;
}

// Start auto-refresh
function startAutoRefresh() {
    if (updateInterval) clearInterval(updateInterval);
    
    fetchDashboardStats();
    fetchRecentEvents();
    
    updateInterval = setInterval(() => {
        fetchDashboardStats();
        fetchRecentEvents();
    }, 3000);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// Initialize dashboard
async function init() {
    console.log('🚀 Store Intelligence Dashboard starting...');
    
    const apiReachable = await testAPIConnection();
    if (!apiReachable) {
        statusIndicator.classList.add('disconnected');
        statusText.textContent = 'API not running - start Spring Boot backend';
        eventsBody.innerHTML = '<tr><td colspan="5" class="loading">⚠️ Backend API not available. Start Spring Boot on port 8080</td></tr>';
        return;
    }
    
    statusIndicator.classList.remove('disconnected');
    statusText.textContent = 'Connected to API';
    startAutoRefresh();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});

// Start the dashboard
init();