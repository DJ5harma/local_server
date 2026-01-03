/**
 * Completion page module - shows results directly
 */
import { Navigation, Utils } from './shared.js';

const CompletionPage = {
    async init() {
        const homeBtn = document.getElementById('home-from-completion-btn');
        if (homeBtn) {
            homeBtn.addEventListener('click', () => this.resetAndGoHome());
        }

        // Automatically load and display results immediately
        await this.loadResult();
    },

    async loadResult() {
        const loadingState = document.getElementById('loading-state');
        const resultSection = document.getElementById('result-section');
        const noteText = document.getElementById('note-text');
        
        try {
            const result = await Utils.apiRequest('/api/test/result');
            
            // Hide loading state and show results immediately
            if (loadingState) {
                loadingState.style.display = 'none';
            }
            if (resultSection) {
                resultSection.style.display = 'block';
            }
            if (noteText) {
                noteText.style.display = 'block';
            }
            
            // Update result display
            const sludgeHeightEl = document.getElementById('result-sludge-height');
            const sv30El = document.getElementById('result-sv30');
            const durationEl = document.getElementById('result-duration');
            
            if (sludgeHeightEl) {
                sludgeHeightEl.textContent = `${result.sludge_height_mm.toFixed(1)} mm`;
            }
            
            if (sv30El) {
                sv30El.textContent = `${result.sv30_percentage.toFixed(1)} %`;
            }
            
            if (durationEl) {
                durationEl.textContent = `${result.test_duration_minutes} minutes`;
            }
        } catch (error) {
            console.error('Error loading result:', error);
            if (loadingState) {
                loadingState.innerHTML = '<p class="message-text" style="color: var(--danger-color);">Failed to load test result. Please try again.</p>';
            }
        }
    },

    async resetAndGoHome() {
        try {
            await Utils.apiRequest('/api/test/reset', { method: 'POST' });
        } catch (error) {
            console.error('Error resetting test:', error);
        }
        
        Navigation.to('home');
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    CompletionPage.init();
});
