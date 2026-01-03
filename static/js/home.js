/**
 * Home page module
 */
import { Navigation, Utils, WebSocketManager } from './shared.js';

const HomePage = {
    statusInterval: null,

    init() {
        const newCycleBtn = document.getElementById('new-cycle-btn');
        if (newCycleBtn) {
            newCycleBtn.addEventListener('click', () => {
                Navigation.to('start');
            });
        }

        // Connect WebSocket and start status updates
        WebSocketManager.connect();
        this.startStatusUpdates();
    },

    startStatusUpdates() {
        const ws = WebSocketManager.getInstance();
        if (ws?.connected) {
            // Set up update listener
            ws.on('update', (data) => {
                if (data?.status) {
                    this.updateSystemState(data.status.state);
                }
            });
            return;
        }
        this.startStatusPolling();
    },

    startStatusPolling() {
        if (this.statusInterval) {
            return;
        }

        // Poll less frequently to save resources
        this.statusInterval = setInterval(async () => {
            try {
                const status = await Utils.apiRequest('/api/test/status');
                let displayState = status.state === 'idle' ? 'Idle' : status.state;
                if (displayState !== 'Idle') {
                    displayState = displayState.charAt(0).toUpperCase() + displayState.slice(1);
                }
                this.updateSystemState(displayState);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }, 3000); // Increased from 2000ms to 3000ms
    },

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    },

    updateSystemState(state) {
        const stateEl = document.getElementById('system-state');
        if (stateEl) {
            stateEl.textContent = state.charAt(0).toUpperCase() + state.slice(1);
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    HomePage.init();
});
