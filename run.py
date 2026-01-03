#!/usr/bin/env python
"""
Entry point for the SV30 Test System HMI server.
"""
import sys
from src.config import Config
from src.app import app, socketio

if __name__ == "__main__":
    try:
        index_path = Config.STATIC_DIR / "index.html"
        print(f"🚀 SV30 Test System HMI starting on http://{Config.HOST}:{Config.PORT}")
        print(f"📁 Static files: {Config.STATIC_DIR}")
        print(f"📄 Index file: {'✅ Found' if index_path.exists() else '❌ Missing'}")
        print(f"✅ Backend: {Config.BACKEND_URL}")
        print(f"🏭 Factory: {Config.FACTORY_CODE}")
        print("\n💡 Press Ctrl+C to stop the server\n")
        
        # Run Flask app with SocketIO
        socketio.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            debug=False,
            allow_unsafe_werkzeug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
