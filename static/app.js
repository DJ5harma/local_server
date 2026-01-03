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
    updateInterval: null,
    statusInterval: null,  // For home page status polling fallback
    startingStateTime: null,  // Track when we entered STARTING state
    lastUpdateTime: null  // Track last successful update for sync verification
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
document.addEventListener('DOMContentLoaded', async () => {
    initializeEventListeners();
    showPage(PAGES.LOGIN);
    
    // Check current server state on load (in case of page refresh)
    try {
        const response = await fetch('/api/test/status');
        if (response.ok) {
            const status = await response.json();
            console.log('📊 Current server state on load:', status.state);
            
            // If test is running or starting, we should be on progress page
            // But since we're on login, we'll let the user login first
            // The state will be synced after login
        }
    } catch (error) {
        console.warn('Could not check server state on load:', error);
    }
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
            
            // Check current test state and navigate accordingly
            try {
                const statusResponse = await fetch('/api/test/status');
                if (statusResponse.ok) {
                    const status = await statusResponse.json();
                    console.log('📊 Current test state after login:', status.state);
                    
                    // If test is running or starting, go to progress page
                    if (status.state === 'running' || status.state === 'starting') {
                        showPage(PAGES.PROGRESS);
                        connectWebSocket();
                        startProgressUpdates();
                    } else if (status.state === 'completed') {
                        showPage(PAGES.COMPLETION);
                    } else {
                        showPage(PAGES.HOME);
                        connectWebSocket();
                        startStatusUpdates();
                    }
                } else {
                    // Fallback to home if status check fails
                    showPage(PAGES.HOME);
                    connectWebSocket();
                    startStatusUpdates();
                }
            } catch (error) {
                console.error('Error checking test state after login:', error);
                // Fallback to home
                showPage(PAGES.HOME);
                connectWebSocket();
                startStatusUpdates();
            }
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
 * Handle test start - simplified
 */
async function handleStartTest() {
    const startBtn = document.getElementById('start-test-btn');
    if (!startBtn) return;
    
    const originalText = startBtn.textContent;
    startBtn.disabled = true;
    startBtn.textContent = 'Starting...';
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        const response = await fetch('/api/test/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Success - navigate to progress page
            showPage(PAGES.PROGRESS);
            connectWebSocket();
            startProgressUpdates();
        } else {
            // Error - show message and reset button
            alert('Failed to start test: ' + (data.error || 'Unknown error'));
            startBtn.disabled = false;
            startBtn.textContent = originalText;
        }
    } catch (error) {
        // Handle errors
        let errorMsg = 'Failed to start test';
        if (error.name === 'AbortError') {
            errorMsg = 'Request timed out. Server may be unresponsive.';
        } else if (error.message?.includes('Failed to fetch')) {
            errorMsg = 'Cannot connect to server. Is the server running?';
        }
        
        alert(errorMsg);
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
 * Connect to Socket.IO for real-time updates - simplified
 */
function connectWebSocket() {
    // Clean up existing connection
    if (AppState.websocket) {
        try {
            AppState.websocket.removeAllListeners();
            AppState.websocket.disconnect();
        } catch (e) {
            // Ignore cleanup errors
        }
        AppState.websocket = null;
    }
    
    // Fallback to polling if Socket.IO not available
    if (typeof io === 'undefined') {
        _startPollingFallback();
        return;
    }

    try {
        AppState.websocket = io({
            transports: ['polling', 'websocket'],
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000,
            forceNew: true
        });

        // Simplified event handlers
        AppState.websocket.on('connect', () => {
            AppState.websocket.emit('request_update');
            stopProgressUpdates(); // Stop polling when connected
        });

        AppState.websocket.on('update', (data) => {
            if (data?.status && data?.data) {
                // Stop polling when WebSocket is working
                stopProgressUpdates();
                // Update UI immediately
                _handleStateUpdate(data.status, data.data);
                // Store last update time for sync verification
                AppState.lastUpdateTime = Date.now();
            }
        });

        AppState.websocket.on('test_completed', () => {
            stopProgressUpdates();
            disconnectWebSocket();
            showPage(PAGES.COMPLETION);
        });

        AppState.websocket.on('disconnect', () => {
            // Immediately start polling to avoid sync gap
            _startPollingFallback();
        });

        AppState.websocket.on('connect_error', () => {
            // Start polling immediately on connection error
            _startPollingFallback();
        });

        AppState.websocket.on('reconnect', () => {
            AppState.websocket.emit('request_update');
            stopProgressUpdates();
        });

    } catch (error) {
        console.error('Socket.IO connection failed:', error);
        _startPollingFallback();
    }
}

/**
 * Helper to handle state updates - centralized
 */
function _handleStateUpdate(status, data) {
    if (AppState.currentPage === PAGES.PROGRESS) {
        updateProgressDisplay(status, data);
    } else if (AppState.currentPage === PAGES.HOME) {
        const state = status.state === 'idle' ? 'Idle' : status.state;
        updateSystemState(state);
    }
}

/**
 * Helper to start polling fallback - simplified
 * Starts immediately to minimize sync gap
 */
function _startPollingFallback() {
    // Don't poll if WebSocket is actually connected
    if (AppState.websocket?.connected) {
        return;
    }
    
    // Start polling immediately based on current page
    if (AppState.currentPage === PAGES.PROGRESS) {
        if (!AppState.updateInterval) {
            startProgressUpdates();
        }
        // Also fetch immediately to catch any missed updates
        fetchProgressData().catch(() => {}); // Ignore errors, polling will retry
    } else if (AppState.currentPage === PAGES.HOME) {
        if (!AppState.statusInterval) {
            startStatusUpdates();
        }
        // Also fetch immediately
        fetch('/api/test/status')
            .then(r => r.ok ? r.json() : null)
            .then(status => {
                if (status) {
                    const state = status.state === 'idle' ? 'Idle' : status.state;
                    updateSystemState(state);
                }
            })
            .catch(() => {}); // Ignore errors
    }
}

/**
 * Disconnect WebSocket
 */
function disconnectWebSocket() {
    if (AppState.websocket) {
        try {
            AppState.websocket.removeAllListeners();
            AppState.websocket.disconnect();
        } catch (e) {
            console.warn('Error disconnecting WebSocket:', e);
        }
        AppState.websocket = null;
    }
}

/**
 * Start polling for progress updates - simplified and robust
 */
function startProgressUpdates() {
    // Don't poll if WebSocket is connected
    if (AppState.websocket?.connected) {
        return;
    }
    
    // Don't start if already polling
    if (AppState.updateInterval) {
        return;
    }

    let errorCount = 0;
    AppState.updateInterval = setInterval(async () => {
        // Stop if not on progress page
        if (AppState.currentPage !== PAGES.PROGRESS) {
            stopProgressUpdates();
            return;
        }
        
        // Stop if WebSocket connected
        if (AppState.websocket?.connected) {
            stopProgressUpdates();
            return;
        }
        
        try {
            await fetchProgressData();
            errorCount = 0; // Reset on success
        } catch (error) {
            errorCount++;
            if (errorCount >= 5) {
                // Try recovery after 5 consecutive errors
                _attemptRecovery();
                errorCount = 0;
            }
        }
    }, 1000);
}

/**
 * Helper to attempt recovery - simplified
 */
async function _attemptRecovery() {
    try {
        const response = await fetch('/api/test/recover', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            if (data.state === 'idle') {
                stopProgressUpdates();
                disconnectWebSocket();
                showPage(PAGES.HOME);
                updateSystemState('Idle');
                alert('Test state was recovered. Please try again.');
            }
        }
    } catch (e) {
        console.error('Recovery failed:', e);
    }
}

/**
 * Stop progress updates
 */
function stopProgressUpdates() {
    if (AppState.updateInterval) {
        clearInterval(AppState.updateInterval);
        AppState.updateInterval = null;
    }
    if (AppState.statusInterval) {
        clearInterval(AppState.statusInterval);
        AppState.statusInterval = null;
    }
}

/**
 * Fetch progress data from API - simplified
 */
async function fetchProgressData() {
    const [statusResponse, dataResponse] = await Promise.all([
        fetch('/api/test/status'),
        fetch('/api/test/data')
    ]);

    if (!statusResponse.ok || !dataResponse.ok) {
        throw new Error('Failed to fetch status or data');
    }

    const status = await statusResponse.json();
    const data = await dataResponse.json();
    
    // Check for stuck STARTING state (simplified)
    if (status.state === 'starting') {
        const now = Date.now();
        if (!AppState.startingStateTime) {
            AppState.startingStateTime = now;
        } else if (now - AppState.startingStateTime > 5000) {
            // Stuck for more than 5 seconds - attempt recovery
            await _attemptRecovery();
            AppState.startingStateTime = null;
            return;
        }
    } else {
        AppState.startingStateTime = null;
    }
    
    // Update display
    updateProgressDisplay(status, data);

    // Handle state transitions
    if (status.state === 'completed' && AppState.currentPage === PAGES.PROGRESS) {
        stopProgressUpdates();
        disconnectWebSocket();
        showPage(PAGES.COMPLETION);
    } else if (status.state === 'aborted' && AppState.currentPage === PAGES.PROGRESS) {
        stopProgressUpdates();
        disconnectWebSocket();
        showPage(PAGES.HOME);
        updateSystemState('Idle');
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
 * Uses Socket.IO if available, otherwise falls back to polling
 */
function startStatusUpdates() {
    // Try Socket.IO first - connect if not already connected
    if (!AppState.websocket || !AppState.websocket.connected) {
        connectWebSocket();
    }
    
    // Fallback polling only if Socket.IO is not available
    if (typeof io === 'undefined' || (!AppState.websocket || !AppState.websocket.connected)) {
        const statusInterval = setInterval(async () => {
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
            } else {
                // Stop polling if we're not on home page
                clearInterval(statusInterval);
            }
        }, 2000); // Update every 2 seconds
        AppState.statusInterval = statusInterval;
    }
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

