/**
 * Frontend logic for SV30 Test System HMI
 * Manages page navigation, API calls, WebSocket connection, and real-time updates
 */

// Application state
const AppState = {
    currentPage: 'login',
    authenticated: false,
    websocket: null,
    testStatus: null,
    testData: null,
    updateInterval: null
};

// Page IDs
const PAGES = {
    LOGIN: 'page-login',
    HOME: 'page-home',
    START: 'page-start',
    PROGRESS: 'page-progress',
    COMPLETION: 'page-completion',
    RESULT: 'page-result'
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    showPage(PAGES.LOGIN);
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Login page
    document.getElementById('login-btn').addEventListener('click', handleLogin);
    document.getElementById('password-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });

    // Home page
    document.getElementById('new-cycle-btn').addEventListener('click', () => {
        showPage(PAGES.START);
    });

    // Start page
    document.getElementById('start-test-btn').addEventListener('click', handleStartTest);
    document.getElementById('cancel-start-btn').addEventListener('click', () => {
        showPage(PAGES.HOME);
    });

    // Progress page
    document.getElementById('abort-test-btn').addEventListener('click', handleAbortTest);

    // Completion page
    document.getElementById('home-from-completion-btn').addEventListener('click', () => {
        resetAndGoHome();
    });
    document.getElementById('view-result-btn').addEventListener('click', async () => {
        await loadResult();
        showPage(PAGES.RESULT);
    });

    // Result page
    document.getElementById('home-from-result-btn').addEventListener('click', () => {
        resetAndGoHome();
    });
}

/**
 * Show a specific page and hide others
 */
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });

    // Show target page
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
        AppState.currentPage = pageId;
    }
}

/**
 * Handle login
 */
async function handleLogin() {
    const passwordInput = document.getElementById('password-input');
    const password = passwordInput.value;
    const errorDiv = document.getElementById('login-error');

    if (!password) {
        errorDiv.textContent = 'Please enter a password';
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            AppState.authenticated = true;
            errorDiv.textContent = '';
            passwordInput.value = '';
            showPage(PAGES.HOME);
            startStatusUpdates();
        } else {
            errorDiv.textContent = 'Invalid password';
            passwordInput.value = '';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Connection error. Please try again.';
    }
}

/**
 * Handle test start
 */
async function handleStartTest() {
    console.log('🚀 Starting test...');
    const startBtn = document.getElementById('start-test-btn');
    if (!startBtn) {
        console.error('❌ Start button not found!');
        return;
    }
    
    const originalText = startBtn.textContent;
    startBtn.disabled = true;
    startBtn.textContent = 'Starting...';
    
    try {
        console.log('📡 Sending POST to /api/test/start');
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch('/api/test/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        console.log('📥 Response received:', response.status, response.statusText);
        
        let data;
        try {
            data = await response.json();
            console.log('📊 Response data:', data);
        } catch (e) {
            console.error('❌ Failed to parse JSON:', e);
            const text = await response.text();
            console.error('Response text:', text);
            throw new Error('Invalid response from server');
        }
        
        if (response.ok && data.success) {
            console.log('✅ Test started successfully, state:', data.state);
            showPage(PAGES.PROGRESS);
            // Small delay to ensure page is shown
            setTimeout(() => {
                connectWebSocket();
                startProgressUpdates();
            }, 100);
        } else {
            const errorMsg = data.error || data.detail || 'Unknown error';
            console.error('❌ Failed to start test:', errorMsg);
            console.error('Response status:', response.status);
            console.error('Response data:', data);
            alert('Failed to start test: ' + errorMsg);
            startBtn.disabled = false;
            startBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('❌ Start test error:', error);
        console.error('Error details:', error.message);
        
        let errorMsg = error.message;
        if (error.name === 'AbortError') {
            errorMsg = 'Request timed out. Server may be unresponsive.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMsg = 'Cannot connect to server. Is the server running?';
        }
        
        alert('Failed to start test: ' + errorMsg + '\n\nCheck browser console and server logs for details.');
        startBtn.disabled = false;
        startBtn.textContent = originalText;
    }
}

/**
 * Handle test abort
 */
async function handleAbortTest() {
    if (!confirm('Are you sure you want to abort the test?')) {
        return;
    }

    try {
        const response = await fetch('/api/test/abort', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            disconnectWebSocket();
            stopProgressUpdates();
            showPage(PAGES.HOME);
            updateSystemState('Idle');
        } else {
            alert('Failed to abort test. Please try again.');
        }
    } catch (error) {
        console.error('Abort test error:', error);
        alert('Failed to abort test. Please try again.');
    }
}

/**
 * Connect to Socket.IO for real-time updates
 */
function connectWebSocket() {
    // Use Socket.IO client library (fallback to polling if not available)
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded, using polling fallback');
        startProgressUpdates();
        return;
    }

    try {
        console.log('Connecting to Socket.IO...');
        AppState.websocket = io({
            transports: ['polling', 'websocket'],  // Try polling first, then websocket
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000,
            forceNew: false,
            upgrade: true
        });

        AppState.websocket.on('connect', () => {
            console.log('✅ Socket.IO connected');
            // Request initial update
            AppState.websocket.emit('request_update');
        });

        AppState.websocket.on('update', (data) => {
            console.log('📊 Received update:', data);
            // Data comes directly from server
            if (data && data.status && data.data) {
                updateProgressDisplay(data.status, data.data);
            } else {
                console.warn('Invalid update data format:', data);
            }
        });

        AppState.websocket.on('test_completed', () => {
            // Test completed via Socket.IO
            stopProgressUpdates();
            disconnectWebSocket();
            showPage(PAGES.COMPLETION);
        });

        AppState.websocket.on('connected', (data) => {
            console.log('Socket.IO connected:', data);
        });

        AppState.websocket.on('disconnect', () => {
            console.log('Socket.IO disconnected');
            // Fallback to polling
            if (AppState.currentPage === PAGES.PROGRESS && !AppState.updateInterval) {
                startProgressUpdates();
            }
        });

        AppState.websocket.on('connect_error', (error) => {
            console.error('Socket.IO connection error:', error);
            // Fallback to polling if Socket.IO fails
            if (!AppState.updateInterval) {
                startProgressUpdates();
            }
        });
    } catch (error) {
        console.error('Failed to create Socket.IO connection:', error);
        // Fallback to polling
        startProgressUpdates();
    }
}

/**
 * Disconnect WebSocket
 */
function disconnectWebSocket() {
    if (AppState.websocket) {
        AppState.websocket.close();
        AppState.websocket = null;
    }
}

/**
 * Start polling for progress updates (fallback if WebSocket unavailable)
 */
function startProgressUpdates() {
    if (AppState.updateInterval) return;

    AppState.updateInterval = setInterval(async () => {
        if (AppState.currentPage === PAGES.PROGRESS) {
            await fetchProgressData();
        }
    }, 1000); // Update every second
}

/**
 * Stop progress updates
 */
function stopProgressUpdates() {
    if (AppState.updateInterval) {
        clearInterval(AppState.updateInterval);
        AppState.updateInterval = null;
    }
}

/**
 * Fetch progress data from API
 */
async function fetchProgressData() {
    try {
        const [statusResponse, dataResponse] = await Promise.all([
            fetch('/api/test/status'),
            fetch('/api/test/data')
        ]);

        if (statusResponse.ok && dataResponse.ok) {
            const status = await statusResponse.json();
            const data = await dataResponse.json();
            updateProgressDisplay(status, data);

            // Check if test completed
            if (status.state === 'completed' && AppState.currentPage === PAGES.PROGRESS) {
                stopProgressUpdates();
                disconnectWebSocket();
                showPage(PAGES.COMPLETION);
            }
        }
    } catch (error) {
        console.error('Error fetching progress data:', error);
    }
}

/**
 * Update progress display with current status and data
 */
function updateProgressDisplay(status, data) {
    AppState.testStatus = status;
    AppState.testData = data;

    // Update time remaining
    const timeRemainingEl = document.getElementById('time-remaining');
    if (timeRemainingEl && status.remaining_seconds !== undefined) {
        const minutes = Math.floor(status.remaining_seconds / 60);
        const seconds = Math.floor(status.remaining_seconds % 60);
        timeRemainingEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    // Update current height
    const currentHeightEl = document.getElementById('current-height');
    if (currentHeightEl && data.latest_height !== undefined && data.latest_height !== null) {
        currentHeightEl.textContent = `${data.latest_height.toFixed(1)} mm`;
    }
}

/**
 * Start status updates for home page
 */
function startStatusUpdates() {
    setInterval(async () => {
        if (AppState.currentPage === PAGES.HOME) {
            try {
                const response = await fetch('/api/test/status');
                if (response.ok) {
                    const status = await response.json();
                    updateSystemState(status.state === 'idle' ? 'Idle' : status.state);
                }
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }
    }, 2000); // Update every 2 seconds
}

/**
 * Update system state display
 */
function updateSystemState(state) {
    const stateEl = document.getElementById('system-state');
    if (stateEl) {
        stateEl.textContent = state.charAt(0).toUpperCase() + state.slice(1);
    }
}

/**
 * Load and display test result
 */
async function loadResult() {
    try {
        const response = await fetch('/api/test/result');
        if (response.ok) {
            const result = await response.json();
            
            // Update result display
            const sludgeHeightEl = document.getElementById('result-sludge-height');
            const sv30El = document.getElementById('result-sv30');
            
            if (sludgeHeightEl) {
                sludgeHeightEl.textContent = `${result.sludge_height_mm.toFixed(1)} mm`;
            }
            
            if (sv30El) {
                sv30El.textContent = `${result.sv30_percentage.toFixed(1)} %`;
            }
        } else {
            alert('Failed to load test result. Please try again.');
        }
    } catch (error) {
        console.error('Error loading result:', error);
        alert('Failed to load test result. Please try again.');
    }
}

/**
 * Reset test and go to home
 */
async function resetAndGoHome() {
    try {
        await fetch('/api/test/reset', { method: 'POST' });
    } catch (error) {
        console.error('Error resetting test:', error);
    }
    
    disconnectWebSocket();
    stopProgressUpdates();
    updateSystemState('Idle');
    showPage(PAGES.HOME);
}

