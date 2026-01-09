"""
API routes for the HMI server (Flask version).

Routes are thin wrappers that delegate to service layer.
"""
import logging
from ..utils.dateUtils import now_ist_iso_utc
from typing import Dict, Any
from flask import request, jsonify

from ..exceptions import TestStateError, DataGenerationError

logger = logging.getLogger(__name__)

# Global instances (will be injected by app)
test_service = None
socketio = None  # Will be set by websocket module


def init_routes(service, sio=None):
    """
    Initialize routes with dependencies.
    
    Args:
        service: TestService instance
        sio: SocketIO instance (optional)
    """
    global test_service, socketio
    test_service = service
    socketio = sio


def register_routes(app):
    """
    Register all routes with Flask app.
    
    Args:
        app: Flask application instance
    """
    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        logger.debug("Health check called")
        return jsonify({
            "status": "ok",
            "state": test_service.test_manager.state.value if test_service else "unknown",
            "server": "running"
        })
    
    @app.route("/api/test/ping", methods=["GET", "POST"])
    def ping():
        """Simple ping endpoint to test if routes are working"""
        logger.debug("Ping endpoint called")
        import time
        return jsonify({"message": "pong", "timestamp": time.time()})
    
    @app.route("/api/test/start", methods=["POST"])
    def start_test():
        """Start a new test cycle"""
        try:
            result = test_service.start_test()
            
            # Emit state update
            _emit_state_update()
            
            return jsonify(result)
        except TestStateError as e:
            logger.warning(f"Test start failed: {e}")
            return jsonify({"error": str(e)}), 400
        except DataGenerationError as e:
            logger.error(f"Data generation failed: {e}")
            return jsonify({"error": f"Failed to generate test data: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Error starting test: {e}")
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    
    @app.route("/api/test/status", methods=["GET"])
    def get_test_status():
        """Get current test status"""
        try:
            status = test_service.get_test_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/data", methods=["GET"])
    def get_test_data():
        """Get current test data for real-time updates"""
        try:
            data = test_service.get_test_data()
            return jsonify(data)
        except Exception as e:
            logger.error(f"Error getting test data: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/abort", methods=["POST"])
    def abort_test():
        """Abort the currently running test"""
        try:
            result = test_service.abort_test()
            _emit_state_update()
            return jsonify(result)
        except TestStateError as e:
            logger.warning(f"Test abort failed: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error aborting test: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/result", methods=["GET"])
    def get_test_result():
        """Get final test result"""
        try:
            result = test_service.get_test_result()
            return jsonify(result)
        except TestStateError as e:
            logger.warning(f"Get result failed: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Error getting test result: {e}")
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    
    @app.route("/api/test/reset", methods=["POST"])
    def reset_test():
        """Reset test state to idle"""
        try:
            result = test_service.reset_test()
            _emit_state_update()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in reset_test: {e}")
            # Try to reset anyway
            try:
                test_service.test_manager.reset_to_idle()
            except:
                pass
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/recover", methods=["POST"])
    def recover_test():
        """Recovery endpoint: reset stuck states"""
        try:
            result = test_service.recover_test()
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in recovery: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/debug/state", methods=["GET"])
    def debug_state():
        """Debug endpoint to check current state"""
        return jsonify({
            "state": test_service.test_manager.state.value,
            "has_t0_data": test_service.test_manager.get_test_data("t0_data") is not None,
            "has_t30_data": test_service.test_manager.get_test_data("t30_data") is not None,
            "height_history_count": len(test_service.test_manager.get_height_history()),
            "status": test_service.test_manager.get_status_dict()
        })
    
    @app.route("/api/debug/backend", methods=["GET"])
    def debug_backend():
        """Debug endpoint to test backend connection"""
        try:
            backend_sender = test_service.backend_sender
            backend_connected = backend_sender.connected
            backend_url = backend_sender.backend_url
            factory_code = backend_sender.factory_code
            
            # Try to send a test message
            test_sent = False
            if backend_connected:
                try:
                    # Send a test message
                    test_data = {
                        "testId": "TEST-CONNECTION",
                        "timestamp": now_ist_iso_utc(),
                        "testType": "morning",
                        "factoryCode": factory_code,
                        "t_min": 0,
                        "sludge_height_mm": 0,
                        "mixture_height_mm": 100,
                        "floc_count": 0,
                        "floc_avg_size_mm": 0
                    }
                    backend_sender.sio.emit("sludge-data", test_data)
                    test_sent = True
                except Exception as e:
                    test_sent = False
                    error_msg = str(e)
            
            return jsonify({
                "backend_url": backend_url,
                "factory_code": factory_code,
                "connected": backend_connected,
                "test_message_sent": test_sent,
                "socket_id": backend_sender.sio.sid if hasattr(backend_sender.sio, 'sid') else None
            })
        except Exception as e:
            return jsonify({
                "error": str(e),
                "backend_url": test_service.backend_sender.backend_url if test_service else "N/A"
            }), 500


def get_test_data_sync() -> Dict[str, Any]:
    """
    Get test data synchronously - for use by WebSocket and other modules.
    
    Returns:
        Dictionary with test data
    """
    if not test_service:
        return {
            "t0_data": None,
            "t30_data": None,
            "latest_height": None,
            "height_history": []
        }
    
    try:
        return test_service.get_test_data()
    except Exception as e:
        logger.warning(f"Error getting test data: {e}")
        return {
            "t0_data": None,
            "t30_data": None,
            "latest_height": None,
            "height_history": []
        }


def _emit_state_update():
    """Helper to emit state update via SocketIO"""
    if not socketio or not test_service:
        return
    
    try:
        status = test_service.get_test_status()
        test_data = get_test_data_sync()
        socketio.emit("update", {
            "status": status,
            "data": test_data
        }, namespace='/')
    except Exception as e:
        logger.warning(f"Failed to emit state update: {e}")
