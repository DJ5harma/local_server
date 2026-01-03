/**
 * Progress page module
 */
import { Navigation, Utils, WebSocketManager } from './shared.js';

const ProgressPage = {
    updateInterval: null,
    startingStateTime: null,

    init() {
        const abortBtn = document.getElementById('abort-test-btn');
        if (abortBtn) {
            abortBtn.addEventListener('click', () => this.handleAbortTest());
        }

        const ws = WebSocketManager.connect();
        if (ws) {
            // Set up WebSocket listeners
            ws.on('update', (data) => {
                if (data?.status && data?.data) {
                    this.stopProgressPolling();
                    this.updateProgressDisplay(data.status, data.data);
                }
            });

            ws.on('test_completed', () => {
                this.stopProgressPolling();
                Navigation.to('completion');
            });

            ws.on('disconnect', () => {
                this.startProgressPolling();
            });

            ws.on('connect_error', () => {
                this.startProgressPolling();
            });
        } else {
            this.startProgressPolling();
        }
    },

    startProgressPolling() {
        if (this.updateInterval) {
            return;
        }

        // Use setInterval with 1 second for consistent updates
        this.updateInterval = setInterval(async () => {
            try {
                await this.fetchProgressData();
            } catch (error) {
                console.error('Error fetching progress data:', error);
            }
        }, 1000);
    },

    stopProgressPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },

    async fetchProgressData() {
        const [status, data] = await Promise.all([
            Utils.apiRequest('/api/test/status'),
            Utils.apiRequest('/api/test/data')
        ]);

        // Check for stuck STARTING state
        if (status.state === 'starting') {
            const now = Date.now();
            if (!this.startingStateTime) {
                this.startingStateTime = now;
            } else if (now - this.startingStateTime > 5000) {
                // Stuck for more than 5 seconds - attempt recovery
                try {
                    await Utils.apiRequest('/api/test/recover', { method: 'POST' });
                } catch (e) {
                    console.error('Recovery failed:', e);
                }
                this.startingStateTime = null;
                return;
            }
        } else {
            this.startingStateTime = null;
        }
        
        this.updateProgressDisplay(status, data);

        // Handle state transitions
        if (status.state === 'completed') {
            this.stopProgressPolling();
            Navigation.to('completion');
        } else if (status.state === 'aborted') {
            this.stopProgressPolling();
            Navigation.to('home');
        }
    },

    updateProgressDisplay(status, data) {
        const timeRemainingEl = document.getElementById('time-remaining');
        if (timeRemainingEl && status.remaining_seconds !== undefined) {
            timeRemainingEl.textContent = Utils.formatTime(status.remaining_seconds);
        }

        const currentHeightEl = document.getElementById('current-height');
        if (currentHeightEl && data.latest_height !== undefined && data.latest_height !== null) {
            currentHeightEl.textContent = `${data.latest_height.toFixed(1)} mm`;
        }

        // Update progress bar
        this.updateProgressBar(status);
    },

    updateProgressBar(status) {
        const progressFill = document.getElementById('progress-fill');
        const progressPercentage = document.getElementById('progress-percentage');
        
        if (status.test_duration_minutes && status.elapsed_seconds !== undefined) {
            const totalSeconds = status.test_duration_minutes * 60;
            const progress = Math.min(100, (status.elapsed_seconds / totalSeconds) * 100);
            
            if (progressFill) {
                // Use width with will-change hint for smooth updates
                progressFill.style.width = `${progress}%`;
            }
            
            if (progressPercentage) {
                progressPercentage.textContent = `${Math.round(progress)}%`;
            }
        }
    },

    async handleAbortTest() {
        if (!confirm('Are you sure you want to abort the test?')) {
            return;
        }

        try {
            await Utils.apiRequest('/api/test/abort', {
                method: 'POST'
            });
            this.stopProgressPolling();
            Navigation.to('home');
        } catch (error) {
            console.error('Abort test error:', error);
            alert('Failed to abort test. Please try again.');
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    ProgressPage.init();
});
