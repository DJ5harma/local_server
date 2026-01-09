"""
Backend client for sending data to the backend server via Socket.IO.
Matches the data format from backend/scripts/dataSender.ts
"""
import logging
import socketio
import socketio.exceptions
from typing import Dict, Any, Optional
from ..config import Config
from ..utils.results_storage import save_sludge_data, save_height_update
from ..utils.dateUtils import now_ist_iso_utc

logger = logging.getLogger(__name__)


class BackendSender:
    """Socket.IO client for sending data to backend"""
    
    def __init__(self, backend_url: Optional[str] = None, factory_code: Optional[str] = None):
        """
        Initialize backend sender.
        
        Args:
            backend_url: Backend server URL (default: from Config)
            factory_code: Factory identifier (default: from Config)
        """
        self.backend_url = backend_url or Config.BACKEND_URL
        self.factory_code = factory_code or Config.FACTORY_CODE
        self.sio = socketio.Client()
        self.connected = False
        
        # Setup event handlers
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('error', self._on_error)
        
    def _on_connect(self):
        """Handle connection event"""
        self.connected = True
        logger.info(f"Connected to backend at {self.backend_url}")
        logger.info(f"   Socket ID: {self.sio.sid if hasattr(self.sio, 'sid') else 'N/A'}")
    
    def _on_disconnect(self):
        """Handle disconnection event"""
        self.connected = False
        logger.warning("Disconnected from backend")
    
    def _on_error(self, error):
        """Handle error event"""
        logger.error(f"Backend connection error: {error}")
    
    def connect(self) -> bool:
        """
        Connect to backend server (non-blocking, quick timeout).
        
        Returns:
            True if already connected, False otherwise (doesn't wait for connection)
        """
        if self.connected:
            return True
        
        # Don't block - just try to initiate connection
        # Connection will complete asynchronously
        try:
            # Determine transport based on URL
            is_production = self.backend_url.startswith("https://")
            transports = ["websocket", "polling"] if is_production else ["polling", "websocket"]
            
            # Use very short timeout - don't block
            # Note: python-socketio Client.connect() doesn't accept reconnection params
            # Reconnection is handled automatically by the client
            self.sio.connect(
                self.backend_url,
                transports=transports,
                wait_timeout=1  # Very short - just initiate, don't wait
            )
            # Note: connected flag will be set by _on_connect callback
            return True
        except Exception as e:
            # Connection failed - that's OK, we'll try again later
            logger.warning(f"Backend connection attempt failed (non-critical): {e}")
            return False
    
    def disconnect(self):
        """Disconnect from backend server"""
        if self.connected:
            self.sio.disconnect()
            self.connected = False
    
    def send_sludge_data(self, data: Dict[str, Any]) -> bool:
        """
        Send sludge data (t=30 final data) via 'sludge-data' event.
        
        NOTE: Only t=30 (final) data should be sent to backend. Backend stores
        one record per factory/date/testType and replaces the entire data field
        on update. Sending t=0 data is redundant as it gets overwritten.
        
        Non-blocking - returns False if backend unavailable but doesn't raise.
        
        Args:
            data: SludgeData dictionary matching backend format (should be t=30 final data)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Ensure factoryCode is included
            data_with_factory = {
                **data,
                "factoryCode": self.factory_code
            }
            
            # Save to local results folder (always save locally, even if backend fails)
            save_sludge_data(data_with_factory)
            logger.info(f"Saved sludge-data locally: t={data.get('t_min', '?')}min, testId={data.get('testId', 'N/A')}")
            
            # Try to connect if not connected
            if not self.connected:
                logger.info(f"Attempting to connect to backend at {self.backend_url}...")
                try:
                    is_production = self.backend_url.startswith("https://")
                    # For production HTTPS, prefer polling (more reliable through proxies)
                    # For local HTTP, try websocket first
                    transports = ["polling", "websocket"] if is_production else ["websocket", "polling"]
                    
                    # Try to connect with a reasonable timeout
                    self.sio.connect(
                        self.backend_url,
                        transports=transports,
                        wait_timeout=3  # Reduced timeout - don't block too long
                    )
                    
                    # Wait a moment for connection callback to fire
                    import time
                    time.sleep(0.3)
                    
                    if not self.connected:
                        logger.warning("Backend connection timeout - connection not established")
                        logger.info("   Data saved locally and will be retried on next connection")
                        return False
                except socketio.exceptions.ConnectionError as e:
                    # Connection failed - this is expected if backend is down
                    logger.warning(f"Backend connection failed: {str(e)}")
                    logger.info("   Data saved locally and will be retried on next connection")
                    return False
                except Exception as e:
                    # Other errors (network, SSL, etc.)
                    logger.warning(f"Backend connection error: {str(e)}")
                    logger.info("   Data saved locally and will be retried on next connection")
                    return False
            
            # If connected, try to send
            if self.connected:
                logger.info("Emitting sludge-data event to backend...")
                logger.debug(f"   Data keys: {list(data_with_factory.keys())}")
                logger.debug(f"   Test ID: {data_with_factory.get('testId', 'N/A')}")
                logger.debug(f"   t_min: {data_with_factory.get('t_min', 'N/A')}")
                logger.debug(f"   Factory: {data_with_factory.get('factoryCode', 'N/A')}")
                
                # Log RGB values before sending
                rgb_clear = data_with_factory.get('rgb_clear_zone')
                rgb_sludge = data_with_factory.get('rgb_sludge_zone')
                if rgb_clear:
                    logger.info(f"📤 Sending clear zone RGB: {{r: {rgb_clear.get('r', 'N/A')}, g: {rgb_clear.get('g', 'N/A')}, b: {rgb_clear.get('b', 'N/A')}}}")
                else:
                    logger.warning("⚠️  No clear zone RGB in data to send")
                
                if rgb_sludge:
                    logger.info(f"📤 Sending sludge zone RGB: {{r: {rgb_sludge.get('r', 'N/A')}, g: {rgb_sludge.get('g', 'N/A')}, b: {rgb_sludge.get('b', 'N/A')}}}")
                else:
                    logger.warning("⚠️  No sludge zone RGB in data to send")
                
                try:
                    self.sio.emit("sludge-data", data_with_factory)
                    logger.info(f"Sent sludge-data to backend: t={data.get('t_min', '?')}min, testId={data.get('testId', 'N/A')}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to emit data (connection may have dropped): {str(e)}")
                    self.connected = False  # Mark as disconnected
                    return False
            else:
                logger.warning("Not connected to backend - data saved locally only")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error sending sludge-data: {str(e)}")
            return False
    
    def send_height_update(self, height_mm: float, timestamp: Optional[str] = None, test_type: Optional[str] = None) -> bool:
        """
        Send periodic height update via 'sludge-height-update' event.
        
        Args:
            height_mm: Current sludge height in millimeters
            timestamp: ISO timestamp (default: current time)
            test_type: Test type - "morning", "afternoon", or "evening" (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            if timestamp is None:
                # Use IST time converted to UTC ISO format
                timestamp = now_ist_iso_utc()
            
            update_data = {
                "factoryCode": self.factory_code,
                "sludge_height_mm": height_mm,
                "timestamp": timestamp
            }
            
            if test_type:
                update_data["testType"] = test_type
            
            # Save to local results folder
            save_height_update(height_mm, timestamp, test_type, self.factory_code)
            
            # NOTE: Periodic updates to production backend are disabled
            # Only t=0 and t=30 data are sent to backend
            # Uncomment below to re-enable periodic backend updates:
            # self.sio.emit("sludge-height-update", update_data)
            
            # Still return True since local save succeeded
            return True
        except Exception as e:
            logger.error(f"Failed to send height update: {e}")
            return False
    
    def send_test_warning(self, message: str, error_details: Optional[str] = None, 
                         date: Optional[str] = None, test_type: Optional[str] = None) -> bool:
        """
        Send test warning via 'test-warning' event.
        
        Args:
            message: Human-readable warning message
            error_details: Technical error details (optional)
            date: Date in YYYY-MM-DD format (default: today)
            test_type: Test type - "morning", "afternoon", or "evening" (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected:
            if not self.connect():
                return False
        
        try:
            if date is None:
                from ..utils.dateUtils import format_date_ist
                date = format_date_ist()
            
            warning_data = {
                "factoryCode": self.factory_code,
                "date": date,
                "status": "failed",  # Only failures are stored
                "message": message
            }
            
            if error_details:
                warning_data["errorDetails"] = error_details
            
            if test_type:
                warning_data["testType"] = test_type
            
            self.sio.emit("test-warning", warning_data)
            logger.warning(f"Sent test warning: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send test warning: {e}")
            return False


# Global instance (will be initialized in app.py)
_backend_sender: Optional[BackendSender] = None


def get_backend_sender() -> BackendSender:
    """Get or create global backend sender instance"""
    global _backend_sender
    if _backend_sender is None:
        _backend_sender = BackendSender()
    return _backend_sender

