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
        """Start a new test cycle"""
        print("=" * 50)
        print("🚀 START TEST ENDPOINT CALLED")
        print("=" * 50)
        import sys
        sys.stdout.flush()  # Force flush output
        
        try:
            print("📍 Step 1: Checking test_manager...")
            sys.stdout.flush()
            if test_manager is None:
                print("❌ test_manager is None!")
                return jsonify({"error": "Test manager not initialized"}), 500
            
            print("📍 Step 2: Getting current state...")
            sys.stdout.flush()
            current_state = test_manager.state
            print(f"📊 Current state: {current_state}")
            sys.stdout.flush()
            
            if current_state != TestState.IDLE:
                print(f"⚠️  Test not in IDLE state: {current_state}")
                return jsonify({"error": "Test already running or not in idle state"}), 400
            
            print("✅ State check passed, starting test...")
            sys.stdout.flush()
            print("📍 Step 3: Calling test_manager.start_test()...")
            sys.stdout.flush()
            start_result = test_manager.start_test()
            print(f"📍 Step 3 result: {start_result}")
            sys.stdout.flush()
            
            if not start_result:
                print("❌ test_manager.start_test() returned False")
                return jsonify({"error": "Failed to start test"}), 400
            
            print("✅ test_manager.start_test() succeeded")
            sys.stdout.flush()
            
            # Generate t=0 data
            print("📍 Step 4: Generating t=0 data...")
            sys.stdout.flush()
            try:
                t0_data = generate_t0_data()
                print(f"✅ Generated t=0 data: {list(t0_data.keys())}")
                sys.stdout.flush()
            except Exception as e:
                print(f"❌ Error generating t=0 data: {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                raise
            
            print("📍 Step 5: Storing t=0 data...")
            sys.stdout.flush()
            test_manager.set_test_data("t0_data", t0_data)
            print("✅ Stored t=0 data")
            sys.stdout.flush()
            
            # Send t=0 data to backend (non-blocking)
            def send_t0_data_async():
                try:
                    print("📤 Sending t=0 data to backend...")
                    backend_sender.send_sludge_data(t0_data)
                except Exception as e:
                    print(f"⚠️  Failed to send t=0 data to backend (non-critical): {e}")
            
            # Send in background thread to avoid blocking
            send_thread = threading.Thread(target=send_t0_data_async, daemon=True)
            send_thread.start()
            print("✅ Started background thread for backend send")
            
            # Confirm test start
            print("📍 Step 6: Confirming test start...")
            sys.stdout.flush()
            test_manager.confirm_start()
            print(f"✅ Test confirmed, state: {test_manager.state}")
            sys.stdout.flush()
            
            # Prepare response FIRST before starting any background tasks
            print("📍 Step 7: Preparing response...")
            sys.stdout.flush()
            result = {"success": True, "state": test_manager.state.value}
            print(f"✅ Response data prepared: {result}")
            sys.stdout.flush()
            
            # Start background task to send periodic height updates (don't wait for it)
            print("📍 Step 8: Starting background threads...")
            sys.stdout.flush()
            print("🔄 Starting periodic updates thread...")
            sys.stdout.flush()
            try:
                thread = threading.Thread(target=send_periodic_updates, args=(t0_data,), daemon=True)
                thread.start()
                print("✅ Periodic updates thread started (non-blocking)")
                sys.stdout.flush()
            except Exception as e:
                print(f"⚠️  Failed to start periodic updates thread (non-critical): {e}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
            
            # Create response and return immediately
            print("📍 Step 9: Creating JSON response...")
            sys.stdout.flush()
            response = jsonify(result)
            print("📤 Response created, about to return...")
            sys.stdout.flush()
            print("=" * 50)
            print("🚀 RETURNING RESPONSE NOW")
            print("=" * 50)
            sys.stdout.flush()
            return response
        except Exception as e:
            print(f"❌ Error starting test: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 50)
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
        """Abort the currently running test"""
        if test_manager.state not in [TestState.STARTING, TestState.RUNNING]:
            return jsonify({"error": "No test running to abort"}), 400
        
        if test_manager.abort_test():
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
        """Reset test state to idle (after viewing results)"""
        test_manager.reset_to_idle()
        return jsonify({"success": True, "state": test_manager.state.value})
    
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
    """Send periodic height updates during test"""
    try:
        print(f"🔄 [BACKGROUND] Starting periodic updates thread for test")
        print(f"🔄 [BACKGROUND] Generating height history...")
        height_history = generate_height_history(
            initial_data, 
            Config.TEST_DURATION_MINUTES, 
            interval_seconds=10
        )
        print(f"📊 [BACKGROUND] Generated {len(height_history)} height history entries")
    except Exception as e:
        print(f"❌ [BACKGROUND] Error generating height history: {e}")
        import traceback
        traceback.print_exc()
        return
    start_time = time.time()
    
    for i, entry in enumerate(height_history):
        if test_manager.state != TestState.RUNNING:
            print(f"⏹️  Test stopped, ending periodic updates")
            break
        
        # Calculate when this entry should be sent (every 10 seconds)
        target_time = start_time + (i * 10)
        current_time = time.time()
        wait_seconds = target_time - current_time
        
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        if test_manager.state == TestState.RUNNING:
            # Store height entry
            test_manager.add_height_entry(entry)
            print(f"📏 Height update {i+1}/{len(height_history)}: {entry['height']:.2f}mm")
            
            # Send to backend
            backend_sender.send_height_update(
                entry["height"],
                entry["dateTime"],
                entry.get("testType")
            )
            
            # Emit via SocketIO if available
            if socketio:
                try:
                    socketio.emit("height_update", {
                        "height": entry["height"],
                        "timestamp": entry["dateTime"]
                    })
                except Exception as e:
                    print(f"⚠️  Error emitting height update: {e}")
    
    # Note: t30 data generation is handled by monitor_test() to avoid duplicates
    # This function only sends periodic height updates during the test


def get_test_data_sync() -> Dict[str, Any]:
    """Synchronous version for WebSocket"""
    t0_data = test_manager.get_test_data("t0_data")
    t30_data = test_manager.get_test_data("t30_data")
    height_history = test_manager.get_height_history()
    
    latest_height = None
    if height_history:
        latest_height = height_history[-1]["height"]
    
    return {
        "t0_data": t0_data,
        "t30_data": t30_data,
        "latest_height": latest_height,
        "height_history": height_history[-10:] if height_history else []
    }
