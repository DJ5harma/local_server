/**
 * Start page module
 */
import { Navigation, Utils } from './shared.js';

const StartPage = {
    init() {
        const startBtn = document.getElementById('start-test-btn');
        const cancelBtn = document.getElementById('cancel-start-btn');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.handleStartTest());
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                Navigation.to('home');
            });
        }
    },

    async handleStartTest() {
        const startBtn = document.getElementById('start-test-btn');
        if (!startBtn) return;
        
        if (startBtn.disabled) {
            return;
        }
        
        const originalText = startBtn.textContent;
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            const data = await Utils.apiRequest('/api/test/start', {
                method: 'POST',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (data.success) {
                Navigation.to('progress');
            } else {
                alert('Failed to start test: ' + (data.error || 'Unknown error'));
                this.resetStartButton();
            }
        } catch (error) {
            let errorMsg = 'Failed to start test';
            if (error.name === 'AbortError') {
                errorMsg = 'Request timed out. Server may be unresponsive.';
            } else if (error.message?.includes('Failed to fetch')) {
                errorMsg = 'Cannot connect to server. Is the server running?';
            }
            
            alert(errorMsg);
            this.resetStartButton();
        }
    },

    resetStartButton() {
        const startBtn = document.getElementById('start-test-btn');
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.textContent = 'YES – Start Test';
        }
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    StartPage.init();
});
