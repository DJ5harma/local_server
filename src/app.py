"""
Main Flask application for SV30 Test System HMI.

This module sets up the Flask application, initializes services,
and configures routes. It uses dependency injection to wire
components together.
"""
import logging
from flask import Flask, send_from_directory, request, Response, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from .config import Config
from .models import TestStateManager
from .services import get_backend_sender
from .services.sv30_data_provider import SV30DataProvider
import os
from .services.test_service import TestService
from .services.test_monitor import TestMonitor
from .api.routes import init_routes, register_routes
from .api.websocket import init_websocket, start_update_broadcast
from .constants import (
    WEBSOCKET_PING_TIMEOUT,
    WEBSOCKET_PING_INTERVAL,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    ping_timeout=WEBSOCKET_PING_TIMEOUT,
    ping_interval=WEBSOCKET_PING_INTERVAL
)

# Initialize core components
test_manager = TestStateManager(test_duration_minutes=Config.TEST_DURATION_MINUTES)
backend_sender = get_backend_sender()

# Initialize data provider (can be easily swapped with ML model implementation)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sv30_path = os.path.join(BASE_DIR, "sv30_pipeline")
# To use SV30 data provider instead, uncomment the line below and comment out the dummy provider:
# data_provider = SV30DataProvider(sv30_path=sv30_path)
from .services.dummy_data_provider import DummyDataProvider
data_provider = DummyDataProvider()

# Initialize test service
test_service = TestService(
    test_manager=test_manager,
    data_provider=data_provider,
    backend_sender=backend_sender
)

# Initialize test monitor
test_monitor = TestMonitor(
    test_manager=test_manager,
    test_service=test_service,
    socketio=socketio
)

logger.info("Backend sender initialized")
logger.info(f"   Backend URL: {Config.BACKEND_URL}")
logger.info(f"   Factory Code: {Config.FACTORY_CODE}")
logger.info("   (Will connect when sending first data)")

# Root route - redirect to home
@app.route("/")
def root():
    """Root route - redirect to home page"""
    return redirect("/home")

# Route for serving HTML pages
@app.route("/<page>")
def serve_page(page: str):
    """
    Serve HTML pages for the HMI interface.
    
    Args:
        page: Page name (home, start, progress, completion, result)
    """
    valid_pages = ["home", "start", "progress", "completion", "result"]
    
    if page not in valid_pages:
        return Response(f"Page not found: {page}", status=404, mimetype='text/plain')
    
    try:
        # Serve individual HTML files
        html_file = f"{page}.html"
        response = send_from_directory(Config.STATIC_DIR, html_file)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"Error serving page {page}: {e}")
        return Response(f"Error loading page: {str(e)}", status=500, mimetype='text/plain')

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info("WebSocket client connected")
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info("WebSocket client disconnected")


@socketio.on('request_update')
def handle_update_request():
    """Handle update request from client"""
    try:
        status = test_service.get_test_status()
        test_data = test_service.get_test_data()
        
        emit('update', {
            "status": status,
            "data": test_data
        })
    except Exception as e:
        logger.error(f"Error handling update request: {e}")

# Initialize routes and websocket with dependencies
init_routes(test_service, socketio)
init_websocket(test_service, socketio)
register_routes(app)

# Start background services
test_monitor.start()
start_update_broadcast()

logger.info("Application initialized successfully")


if __name__ == "__main__":
    index_path = Config.STATIC_DIR / "index.html"
    logger.info(f"SV30 Test System HMI starting on http://{Config.HOST}:{Config.PORT}")
    logger.info(f"Static files: {Config.STATIC_DIR}")
    logger.info(f"Index file: {'Found' if index_path.exists() else 'Missing'}")
    logger.info(f"Backend: {Config.BACKEND_URL}")
    logger.info(f"Factory: {Config.FACTORY_CODE}")
    
    # Run Flask app with SocketIO
    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=False,
        allow_unsafe_werkzeug=True,
        use_reloader=False
    )
