/**
 * Shared utilities module for SV30 Test System HMI
 */

export const WebSocketManager = {
    websocket: null,

    connect() {
        // If already connected, don't reconnect
        if (this.websocket && this.websocket.connected) {
            return this.websocket;
        }
        
        // Fallback to polling if Socket.IO not available
        if (typeof io === 'undefined') {
            return null;
        }

        // Only create new connection if we don't have one or it's disconnected
        if (!this.websocket || !this.websocket.connected) {
            try {
                // If we have a disconnected socket, clean it up first
                if (this.websocket) {
                    try {
                        this.websocket.removeAllListeners();
                    } catch (e) {
                        // Ignore cleanup errors
                    }
                }
                
                this.websocket = io({
                    transports: ['polling', 'websocket'],
                    reconnection: true,
                    reconnectionAttempts: Infinity,
                    reconnectionDelay: 1000,
                    reconnectionDelayMax: 5000,
                    timeout: 20000,
                    forceNew: false
                });

                this.websocket.on('connect', () => {
                    this.websocket.emit('request_update');
                });

                this.websocket.on('disconnect', () => {
                    console.log('WebSocket disconnected');
                });

                this.websocket.on('connect_error', () => {
                    console.log('WebSocket connection error');
                });

                this.websocket.on('reconnect', () => {
                    this.websocket.emit('request_update');
                });

            } catch (error) {
                console.error('Socket.IO connection failed:', error);
            }
        }
        
        return this.websocket;
    },

    disconnect() {
        if (this.websocket) {
            try {
                this.websocket.removeAllListeners();
                this.websocket.disconnect();
            } catch (e) {
                console.warn('Error disconnecting WebSocket:', e);
            }
            this.websocket = null;
        }
    },

    getInstance() {
        return this.websocket;
    }
};

export const Navigation = {
    to(page) {
        window.location.href = `/${page}`;
    }
};

export const Utils = {
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    },

    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    },

    showError(elementId, message) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
        }
    },

    clearError(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = '';
        }
    }
};

