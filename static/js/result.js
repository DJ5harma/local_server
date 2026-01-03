/**
 * Result page module
 */
import { Navigation, Utils } from './shared.js';

const ResultPage = {
    async init() {
        const homeBtn = document.getElementById('home-from-result-btn');
        if (homeBtn) {
            homeBtn.addEventListener('click', () => this.resetAndGoHome());
        }

        await this.loadResult();
    },

    async loadResult() {
        try {
            const result = await Utils.apiRequest('/api/test/result');
            
            const sludgeHeightEl = document.getElementById('result-sludge-height');
            const sv30El = document.getElementById('result-sv30');
            
            if (sludgeHeightEl) {
                sludgeHeightEl.textContent = `${result.sludge_height_mm.toFixed(1)} mm`;
            }
            
            if (sv30El) {
                sv30El.textContent = `${result.sv30_percentage.toFixed(1)} %`;
            }
        } catch (error) {
            console.error('Error loading result:', error);
            alert('Failed to load test result. Please try again.');
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
    ResultPage.init();
});
