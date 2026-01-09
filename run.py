#!/usr/bin/env python
"""
Entry point for the SV30 Test System HMI server.
"""
import sys
import os
import logging
from pathlib import Path

# Set up logging early for service mode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

try:
    from src.config import Config
    from src.app import app, socketio
except Exception as e:
    logger.error(f"Failed to import modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        # Change to script directory to ensure relative paths work
        script_dir = Path(__file__).parent.absolute()
        os.chdir(script_dir)
        logger.info(f"Working directory: {os.getcwd()}")
        
        index_path = Config.STATIC_DIR / "index.html"
        logger.info(f"🚀 SV30 Test System HMI starting on http://{Config.HOST}:{Config.PORT}")
        logger.info(f"📁 Static files: {Config.STATIC_DIR}")
        logger.info(f"📄 Index file: {'✅ Found' if index_path.exists() else '❌ Missing'}")
        logger.info(f"✅ Backend: {Config.BACKEND_URL}")
        logger.info(f"🏭 Factory: {Config.FACTORY_CODE}")
        
        # Run Flask app with SocketIO
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=False,
            allow_unsafe_werkzeug=True,
            use_reloader=False,
            log_output=True
        )
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
