"""
WebSocket handler for real-time test updates (Flask-SocketIO version).
"""
import logging
import time
import threading
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global instances (will be injected)
test_service = None
socketio: Optional[object] = None


def init_websocket(service, sio):
    """
    Initialize WebSocket handler with dependencies.
    
    Args:
        service: TestService instance
        sio: SocketIO instance
    """
    global test_service, socketio
    test_service = service
    socketio = sio
    
    # Update routes module to have socketio reference
    from . import routes
    routes.socketio = socketio


def start_update_broadcast():
    """Start broadcasting updates periodically"""
    def broadcast_loop():
        last_state = None
        while True:
            try:
                time.sleep(1)  # Update every second for smooth updates
                
                if test_service and socketio:
                    status = test_service.get_test_status()
                    # Import lazily to avoid circular import
                    from .routes import get_test_data_sync
                    test_data = get_test_data_sync()
                    current_state = status.get("state", "unknown")
                    
                    # Always emit update, but log state changes
                    if current_state != last_state:
                        logger.info(f"State changed: {last_state} -> {current_state}")
                        last_state = current_state
                    
                    # Emit update to all connected clients (broadcast by default in Flask-SocketIO)
                    try:
                        socketio.emit("update", {
                            "status": status,
                            "data": test_data
                        }, namespace='/')
                    except Exception as e:
                        logger.warning(f"Error emitting update: {e}")
                    
                    # Check if test completed
                    if current_state == "completed":
                        try:
                            socketio.emit("test_completed", {"type": "test_completed"}, namespace='/')
                        except Exception as e:
                            logger.warning(f"Error emitting completion: {e}")
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                time.sleep(1)
    
    thread = threading.Thread(target=broadcast_loop, daemon=True)
    thread.start()
    logger.info("Started WebSocket broadcast thread")
