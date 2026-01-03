"""
Main Flask application for SV30 Test System HMI.
"""
import threading
from flask import Flask, send_from_directory, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from .config import Config
from .models import TestStateManager, TestState
from .services import get_backend_sender
from .api.routes import init_routes, register_routes
from .api.websocket import init_websocket, start_update_broadcast

# Validate configuration
Config.validate()

# Initialize Flask app
app = Flask(__name__, static_folder=str(Config.STATIC_DIR))
CORS(app)  # Enable CORS for all routes

# Disable caching for development
@app.after_request
def after_request(response):
    """Add headers to prevent caching"""
    if request.path == '/' or request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Initialize SocketIO for WebSocket support
# Use 'threading' mode for compatibility, allow both websocket and polling
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Initialize test state manager
test_manager = TestStateManager(test_duration_minutes=Config.TEST_DURATION_MINUTES)

# Initialize backend sender (don't connect yet - will connect on first use)
backend_sender = get_backend_sender()
print(f"📡 Backend sender initialized")
print(f"   Backend URL: {Config.BACKEND_URL}")
print(f"   Factory Code: {Config.FACTORY_CODE}")
print(f"   (Will connect when sending first data)")

# Root route - serve index.html
@app.route("/")
def root():
    """Serve the main HMI interface"""
    try:
        print(f"📄 Serving index.html from {Config.STATIC_DIR}")
        response = send_from_directory(Config.STATIC_DIR, "index.html")
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        print(f"❌ Error serving index.html: {e}")
        import traceback
        traceback.print_exc()
        return Response(f"Error loading page: {str(e)}", status=500, mimetype='text/plain')


# Background task for test monitoring
def monitor_test():
    """Background task to monitor test progress and trigger completion"""
    import time
    while True:
        try:
            time.sleep(1)  # Check every second
            
            if test_manager.state == TestState.RUNNING:
                if test_manager.is_test_complete():
                    test_manager.complete_test()
                    print("✅ Test completed after 30 minutes")
                    
                    # Generate and send t30 data to backend
                    t0_data = test_manager.get_test_data("t0_data")
                    if t0_data:
                        def generate_and_send_t30():
                            try:
                                # Use absolute imports to avoid relative import issues in threads
                                from src.services import generate_t30_data
                                from src.services import get_backend_sender
                                from src.config import Config
                                
                                print("🔬 Generating t=30 data after completion...")
                                t30_data = generate_t30_data(t0_data, Config.TEST_DURATION_MINUTES)
                                test_manager.set_test_data("t30_data", t30_data)
                                
                                print("📤 Sending t=30 data to backend...")
                                sender = get_backend_sender()
                                sender.send_sludge_data(t30_data)
                                print("✅ t=30 data sent to backend")
                            except Exception as e:
                                print(f"⚠️  Error generating/sending t=30 data: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        # Send in background thread
                        t30_thread = threading.Thread(target=generate_and_send_t30, daemon=True)
                        t30_thread.start()
                    
                    # Emit completion event via SocketIO
                    socketio.emit("test_completed", {"type": "test_completed"})
        except Exception as e:
            print(f"⚠️  Error in monitor_test: {e}")
            time.sleep(1)


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print("✅ WebSocket client connected")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print("⚠️  WebSocket client disconnected")


@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    from .api.routes import get_test_data_sync
    status = test_manager.get_status_dict()
    test_data = get_test_data_sync()
    
    emit('update', {
        "status": status,
        "data": test_data
    })


# Initialize routes and websocket with dependencies (after route definitions)
init_routes(test_manager, backend_sender)
init_websocket(test_manager, socketio)
register_routes(app, test_manager, backend_sender)
start_update_broadcast()

# Start background monitoring thread
monitor_thread = threading.Thread(target=monitor_test, daemon=True)
monitor_thread.start()


if __name__ == "__main__":
    index_path = Config.STATIC_DIR / "index.html"
    print(f"🚀 SV30 Test System HMI starting on http://{Config.HOST}:{Config.PORT}")
    print(f"📁 Static files: {Config.STATIC_DIR}")
    print(f"📄 Index file: {'✅ Found' if index_path.exists() else '❌ Missing'}")
    print(f"✅ Backend: {Config.BACKEND_URL}")
    print(f"🏭 Factory: {Config.FACTORY_CODE}")
    
    # Run Flask app with SocketIO
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=False,
        allow_unsafe_werkzeug=True
    )
