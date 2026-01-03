"""
API routes for the HMI server (Flask version).
"""
import threading
import time
from datetime import datetime
from typing import Dict, Any
from flask import request, jsonify

from ..config import Config
from ..models import TestStateManager, TestState
from ..services import generate_t0_data, generate_t30_data, generate_height_history
from ..utils.auth import verify_password

# Global instances (will be injected by app)
test_manager: TestStateManager = None
backend_sender = None
socketio = None  # Will be set by websocket module


def init_routes(manager: TestStateManager, sender):
    """Initialize routes with dependencies"""
    global test_manager, backend_sender
    test_manager = manager
    backend_sender = sender


def register_routes(app, manager: TestStateManager, sender):
    """Register all routes with Flask app"""
    global test_manager, backend_sender
    test_manager = manager
    backend_sender = sender
    
    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        print("🏥 Health check called")
        return jsonify({
            "status": "ok",
            "state": test_manager.state.value if test_manager else "unknown",
            "server": "running"
        })
    
    @app.route("/api/test/ping", methods=["GET", "POST"])
    def ping():
        """Simple ping endpoint to test if routes are working"""
        print("🏓 Ping endpoint called")
        import sys
        sys.stdout.flush()
        response = jsonify({"message": "pong", "timestamp": time.time()})
        print("🏓 Ping response created, returning...")
        sys.stdout.flush()
        return response
    
    @app.route("/api/login", methods=["POST"])
    def login():
        """Authenticate user with password"""
        try:
            data = request.get_json()
            password = data.get("password", "") if data else ""
            
            if verify_password(password):
                return jsonify({"success": True, "session_id": "authenticated"})
            else:
                return jsonify({"error": "Invalid password"}), 401
        except Exception as e:
            print(f"❌ Login error: {e}")
            return jsonify({"error": "Internal error"}), 500
    
    @app.route("/api/test/start", methods=["POST"])
    def start_test():
        """Start a new test cycle - simplified and robust"""
        try:
            # Validate manager
            if not test_manager:
                return jsonify({"error": "Test manager not initialized"}), 500
            
            # Check state - must be IDLE
            if test_manager.state != TestState.IDLE:
                return jsonify({
                    "error": f"Test already running or not in idle state (current: {test_manager.state.value})"
                }), 400
            
            # Start test (sets state to STARTING)
            if not test_manager.start_test():
                return jsonify({"error": "Failed to start test"}), 400
            
            # Generate and store t=0 data
            try:
                t0_data = generate_t0_data()
                test_manager.set_test_data("t0_data", t0_data)
            except Exception as e:
                test_manager.reset_to_idle()
                return jsonify({"error": f"Failed to generate test data: {str(e)}"}), 500
            
            # Transition to RUNNING
            test_manager.confirm_start()
            
            # Start background tasks (non-blocking, errors are non-critical)
            def background_tasks():
                try:
                    # Send t=0 data to backend
                    backend_sender.send_sludge_data(t0_data)
                except Exception as e:
                    print(f"⚠️  Backend send failed (non-critical): {e}")
                
                try:
                    # Start periodic height updates
                    send_periodic_updates(t0_data)
                except Exception as e:
                    print(f"⚠️  Periodic updates failed (non-critical): {e}")
            
            threading.Thread(target=background_tasks, daemon=True).start()
            
            # Emit state update
            _emit_state_update()
            
            # Return success immediately
            return jsonify({
                "success": True,
                "state": test_manager.state.value
            })
            
        except Exception as e:
            # Reset state on any error
            try:
                if test_manager and test_manager.state == TestState.STARTING:
                    test_manager.reset_to_idle()
            except:
                pass
            
            print(f"❌ Error starting test: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    
    @app.route("/api/test/status", methods=["GET"])
    def get_test_status():
        """Get current test status"""
        try:
            status = test_manager.get_status_dict()
            return jsonify(status)
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/data", methods=["GET"])
    def get_test_data():
        """Get current test data for real-time updates"""
        try:
            t0_data = test_manager.get_test_data("t0_data")
            t30_data = test_manager.get_test_data("t30_data")
            height_history = test_manager.get_height_history()
            
            # Get latest height from history
            latest_height = None
            if height_history:
                latest_height = height_history[-1]["height"]
            
            return jsonify({
                "t0_data": t0_data,
                "t30_data": t30_data,
                "latest_height": latest_height,
                "height_history": height_history[-10:] if height_history else []
            })
        except Exception as e:
            print(f"❌ Error getting test data: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/test/abort", methods=["POST"])
    def abort_test():
        """Abort the currently running test - simplified"""
        if test_manager.state not in [TestState.STARTING, TestState.RUNNING]:
            return jsonify({"error": "No test running to abort"}), 400
        
        if test_manager.abort_test():
            _emit_state_update()
            return jsonify({"success": True, "state": test_manager.state.value})
        else:
            return jsonify({"error": "Failed to abort test"}), 400
    
    @app.route("/api/test/result", methods=["GET"])
    def get_test_result():
        """Get final test result"""
        try:
            if test_manager.state != TestState.COMPLETED:
                return jsonify({"error": "Test not completed"}), 400
            
            t0_data = test_manager.get_test_data("t0_data")
            t30_data = test_manager.get_test_data("t30_data")
            
            if not t30_data:
                # Generate t30 data if not already generated
                if t0_data:
                    print("🔬 Generating t=30 data for result...")
                    t30_data = generate_t30_data(t0_data, Config.TEST_DURATION_MINUTES)
                    test_manager.set_test_data("t30_data", t30_data)
                    
                    # Send t30 data to backend (non-blocking)
                    def send_t30_data_async():
                        try:
                            print("📤 Sending t=30 data to backend...")
                            backend_sender.send_sludge_data(t30_data)
                            print("✅ t=30 data sent to backend")
                        except Exception as e:
                            print(f"⚠️  Failed to send t=30 data to backend (non-critical): {e}")
                    
                    send_thread = threading.Thread(target=send_t30_data_async, daemon=True)
                    send_thread.start()
                else:
                    return jsonify({"error": "Initial test data not found"}), 404
            
            if not t30_data:
                return jsonify({"error": "Test data not found"}), 404
            
            # Calculate SV30 percentage
            sludge_height = t30_data.get("sludge_height_mm", 0)
            mixture_height = t30_data.get("mixture_height_mm", 1)
            sv30_percentage = (sludge_height / mixture_height) * 100 if mixture_height > 0 else 0
            
            return jsonify({
                "test_status": "Completed",
                "test_duration_minutes": round(Config.TEST_DURATION_MINUTES, 2),
                "sludge_height_mm": round(sludge_height, 2),
                "sv30_percentage": round(sv30_percentage, 2),
                "sv30_mL_per_L": t30_data.get("sv30_mL_per_L", 0),
                "t0_data": t0_data,
                "t30_data": t30_data
            })
        except Exception as e:
            print(f"❌ Error getting test result: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"Internal error: {str(e)}"}), 500
    
    @app.route("/api/test/reset", methods=["POST"])
    def reset_test():
        """Reset test state to idle - simplified"""
        test_manager.reset_to_idle()
        _emit_state_update()
        return jsonify({"success": True, "state": test_manager.state.value})
    
    @app.route("/api/test/recover", methods=["POST"])
    def recover_test():
        """Recovery endpoint: reset stuck states"""
        try:
            current_state = test_manager.state
            
            # If stuck in STARTING, reset to IDLE
            if current_state == TestState.STARTING:
                print("🔄 Recovering from stuck STARTING state")
                test_manager.reset_to_idle()
                return jsonify({
                    "success": True,
                    "message": "Recovered from stuck STARTING state",
                    "state": test_manager.state.value
                })
            
            # If in RUNNING but no test data, something is wrong
            if current_state == TestState.RUNNING:
                t0_data = test_manager.get_test_data("t0_data")
                if not t0_data:
                    print("🔄 Recovering from RUNNING state without data")
                    test_manager.reset_to_idle()
                    return jsonify({
                        "success": True,
                        "message": "Recovered from invalid RUNNING state",
                        "state": test_manager.state.value
                    })
            
            return jsonify({
                "success": True,
                "message": "No recovery needed",
                "state": current_state.value
            })
        except Exception as e:
            print(f"❌ Error in recovery: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/debug/state", methods=["GET"])
    def debug_state():
        """Debug endpoint to check current state"""
        return jsonify({
            "state": test_manager.state.value,
            "has_t0_data": test_manager.get_test_data("t0_data") is not None,
            "has_t30_data": test_manager.get_test_data("t30_data") is not None,
            "height_history_count": len(test_manager.get_height_history()),
            "status": test_manager.get_status_dict()
        })
    
    @app.route("/api/debug/backend", methods=["GET"])
    def debug_backend():
        """Debug endpoint to test backend connection"""
        try:
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
                        "timestamp": datetime.now().isoformat() + "Z",
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
                "backend_url": backend_sender.backend_url if backend_sender else "N/A"
            }), 500


def send_periodic_updates(initial_data: Dict[str, Any]):
    """Send periodic height updates during test - simplified and robust"""
    try:
        # Generate height history once
        height_history = generate_height_history(
            initial_data, 
            Config.TEST_DURATION_MINUTES, 
            interval_seconds=10
        )
        print(f"📊 Generated {len(height_history)} height history entries")
    except Exception as e:
        print(f"❌ Error generating height history: {e}")
        return
    
    start_time = time.time()
    
    # Send updates every 10 seconds
    for i, entry in enumerate(height_history):
        # Check if test is still running
        if test_manager.state != TestState.RUNNING:
            break
        
        # Wait until it's time for this update
        target_time = start_time + (i * 10)
        wait_seconds = max(0, target_time - time.time())
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        # Double-check state before storing
        if test_manager.state == TestState.RUNNING:
            test_manager.add_height_entry(entry)
            
            # Emit via SocketIO (non-critical if it fails)
            if socketio:
                try:
                    socketio.emit("height_update", {
                        "height": entry.get("height"),
                        "timestamp": entry.get("dateTime")
                    }, namespace='/', broadcast=True)
                except Exception:
                    pass  # Non-critical


def get_test_data_sync() -> Dict[str, Any]:
    """Get test data synchronously - simplified and robust"""
    try:
        t0_data = test_manager.get_test_data("t0_data")
        t30_data = test_manager.get_test_data("t30_data")
        height_history = test_manager.get_height_history()
        
        latest_height = None
        if height_history:
            latest_height = height_history[-1].get("height")
        
        return {
            "t0_data": t0_data,
            "t30_data": t30_data,
            "latest_height": latest_height,
            "height_history": height_history[-10:] if height_history else []
        }
    except Exception as e:
        print(f"⚠️  Error getting test data: {e}")
        return {
            "t0_data": None,
            "t30_data": None,
            "latest_height": None,
            "height_history": []
        }


def _emit_state_update():
    """Helper to emit state update via SocketIO - simplified and robust"""
    if not socketio or not test_manager:
        return
    
    try:
        status = test_manager.get_status_dict()
        test_data = get_test_data_sync()
        socketio.emit("update", {
            "status": status,
            "data": test_data
        }, namespace='/', broadcast=True)
    except Exception as e:
        print(f"⚠️  Failed to emit state update: {e}")
