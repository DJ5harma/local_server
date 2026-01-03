"""
WebSocket handler for real-time test updates (Flask-SocketIO version).
"""
from ..models import TestStateManager
from .routes import get_test_data_sync

# Global instance (will be injected)
test_manager: TestStateManager = None
socketio = None


def init_websocket(manager: TestStateManager, sio):
    """Initialize WebSocket handler with dependencies"""
    global test_manager, socketio
    test_manager = manager
    socketio = sio
    
    # Update routes module to have socketio reference
    from . import routes
    routes.socketio = socketio


def start_update_broadcast():
    """Start broadcasting updates periodically"""
    import time
    import threading
    
    def broadcast_loop():
        while True:
            try:
                time.sleep(1)  # Update every second
                
                if test_manager and socketio:
                    status = test_manager.get_status_dict()
                    test_data = get_test_data_sync()
                    
                    # Emit update to all connected clients
                    socketio.emit("update", {
                        "status": status,
                        "data": test_data
                    }, namespace='/')
                    
                    # Check if test completed
                    if status["state"] == "completed":
                        socketio.emit("test_completed", {"type": "test_completed"})
            except Exception as e:
                print(f"⚠️  Error in broadcast loop: {e}")
                time.sleep(1)
    
    thread = threading.Thread(target=broadcast_loop, daemon=True)
    thread.start()
