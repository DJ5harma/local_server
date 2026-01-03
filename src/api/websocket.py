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
        last_state = None
        while True:
            try:
                time.sleep(1)  # Update every second
                
                if test_manager and socketio:
                    status = test_manager.get_status_dict()
                    test_data = get_test_data_sync()
                    current_state = status.get("state", "unknown")
                    
                    # Always emit update, but log state changes
                    if current_state != last_state:
                        print(f"🔄 State changed: {last_state} -> {current_state}")
                        last_state = current_state
                    
                    # Emit update to all connected clients (broadcast by default in Flask-SocketIO)
                    try:
                        socketio.emit("update", {
                            "status": status,
                            "data": test_data
                        }, namespace='/')
                    except Exception as e:
                        print(f"⚠️  Error emitting update: {e}")
                    
                    # Check if test completed
                    if current_state == "completed":
                        try:
                            socketio.emit("test_completed", {"type": "test_completed"}, namespace='/')
                        except Exception as e:
                            print(f"⚠️  Error emitting completion: {e}")
            except Exception as e:
                print(f"⚠️  Error in broadcast loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
    
    thread = threading.Thread(target=broadcast_loop, daemon=True)
    thread.start()
    print("✅ Started WebSocket broadcast thread")
