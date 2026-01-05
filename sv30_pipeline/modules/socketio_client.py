"""
Socket.IO Client Module (Updated v2.0)

Handles real-time communication with the SV30 dashboard backend.

Features:
- Send test data (t=0 and t=30)
- Send real-time sludge height updates
- Send test warnings (AWS upload failures, errors)
- Automatic reconnection
"""

import socketio
import time
from datetime import datetime
from sv30config import (
    SOCKETIO_ENABLED,
    SOCKETIO_URL,
    FACTORY_CODE,
    MORNING_TEST_HOUR,
    AFTERNOON_TEST_HOUR,
    EVENING_TEST_HOUR,
)

# Global Socket.IO client
sio = None

def connect_socketio():
    """
    Connect to Socket.IO dashboard backend
    
    Returns:
        sio: Socket.IO client instance or None if failed
    """
    if not SOCKETIO_ENABLED:
        return None
    
    global sio
    
    try:
        sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            logger=False,
            engineio_logger=False
        )
        
        @sio.on('connect')
        def on_connect():
            print(f"[SOCKETIO] ✅ Connected to {SOCKETIO_URL}")
        
        @sio.on('disconnect')
        def on_disconnect():
            print(f"[SOCKETIO] ⚠️  Disconnected from dashboard")
        
        @sio.on('connect_error')
        def on_connect_error(data):
            print(f"[SOCKETIO] ❌ Connection error: {data}")
        
        # Connect with timeout
        sio.connect(SOCKETIO_URL, wait_timeout=10)
        
        return sio
        
    except Exception as e:
        print(f"[SOCKETIO] ❌ Failed to connect: {e}")
        return None

def determine_test_type():
    """
    Determine test type based on current hour
    
    Returns:
        test_type: "morning" | "afternoon" | "evening"
    """
    hour = datetime.now().hour
    
    if hour >= 4 and hour < 12:
        return "morning"
    elif hour >= 12 and hour < 20:
        return "afternoon"
    else:
        return "evening"

def send_sludge_data(
    t_min,
    sludge_height_mm,
    mixture_height_mm,
    floc_count=0,
    floc_avg_size_mm=0,
    sv30_mL_per_L=None,
    velocity_mm_per_min=None,
    rgb_clear_zone=None,
    rgb_sludge_zone=None,
    test_id=None,
    operator="Thermax"
):
    """
    Send test data to dashboard (t=0 or t=30)
    
    Args:
        t_min: Time in minutes (0 or 30)
        sludge_height_mm: Sludge height in mm
        mixture_height_mm: Mixture height in mm
        floc_count: Number of flocs detected
        floc_avg_size_mm: Average floc size in mm
        sv30_mL_per_L: SV30 value (only for t=30)
        velocity_mm_per_min: Settling velocity (only for t=30)
        rgb_clear_zone: RGB dict for clear zone
        rgb_sludge_zone: RGB dict for sludge zone
        test_id: Unique test identifier
        operator: Operator name
    
    Returns:
        success: Boolean
    """
    if not sio or not sio.connected:
        print("[SOCKETIO] Not connected - cannot send data")
        return False
    
    try:
        test_type = determine_test_type()
        
        data = {
            "timestamp": datetime.now().isoformat() + "Z",
            "testType": test_type,
            "factoryCode": FACTORY_CODE,
            "t_min": t_min,
            "sludge_height_mm": sludge_height_mm,
            "mixture_height_mm": mixture_height_mm,
            "floc_count": floc_count,
            "floc_avg_size_mm": floc_avg_size_mm,
        }
        
        # Add optional fields
        if test_id:
            data["testId"] = test_id
        if operator:
            data["operator"] = operator
        if sv30_mL_per_L is not None:
            data["sv30_mL_per_L"] = sv30_mL_per_L
        if velocity_mm_per_min is not None:
            data["velocity_mm_per_min"] = velocity_mm_per_min
        if rgb_clear_zone:
            data["rgb_clear_zone"] = rgb_clear_zone
        if rgb_sludge_zone:
            data["rgb_sludge_zone"] = rgb_sludge_zone
        
        sio.emit("sludge-data", data)
        print(f"[SOCKETIO] ✅ Sent {test_type} t={t_min} data")
        return True
        
    except Exception as e:
        print(f"[SOCKETIO] ❌ Failed to send data: {e}")
        return False

def send_sludge_height_update(sludge_height_mm):
    """
    Send real-time sludge height update during test
    
    Args:
        sludge_height_mm: Current sludge height in mm
    
    Returns:
        success: Boolean
    """
    if not sio or not sio.connected:
        return False
    
    try:
        test_type = determine_test_type()
        
        data = {
            "factoryCode": FACTORY_CODE,
            "sludge_height_mm": sludge_height_mm,
            "timestamp": datetime.now().isoformat() + "Z",
            "testType": test_type,
        }
        
        sio.emit("sludge-height-update", data)
        return True
        
    except Exception as e:
        print(f"[SOCKETIO] Failed to send height update: {e}")
        return False

def send_test_warning(test_type=None, message="", error_details=""):
    """
    Send test warning to dashboard (AWS upload failure, errors, etc.)
    
    Args:
        test_type: "morning" | "afternoon" | "evening" (auto-detect if None)
        message: Warning message
        error_details: Technical error details
    
    Returns:
        success: Boolean
    """
    if not sio or not sio.connected:
        print("[SOCKETIO] Not connected - cannot send warning")
        return False
    
    try:
        if test_type is None:
            test_type = determine_test_type()
        
        warning_data = {
            "factoryCode": FACTORY_CODE,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "testType": test_type,
            "status": "failed",
            "message": message,
            "errorDetails": error_details
        }
        
        sio.emit("test-warning", warning_data)
        print(f"[SOCKETIO] ⚠️  Warning sent: {message}")
        return True
        
    except Exception as e:
        print(f"[SOCKETIO] ❌ Failed to send warning: {e}")
        return False

def send_test_results(metrics, rgb):
    """
    Send complete test results to dashboard (LEGACY - for compatibility)
    
    Args:
        metrics: Dict with SV30 metrics
        rgb: Dict with RGB values
    
    Returns:
        success: Boolean
    """
    # This now calls send_sludge_data with t=30
    return send_sludge_data(
        t_min=30,
        sludge_height_mm=metrics.get("sludge_height_mm", 0),
        mixture_height_mm=metrics.get("mixture_height_mm", 0),
        sv30_mL_per_L=metrics.get("sv30_pct", 0) * 10,  # Convert % to mL/L
        velocity_mm_per_min=metrics.get("avg_velocity", 0),
        rgb_clear_zone=rgb.get("clear_zone"),
        rgb_sludge_zone=rgb.get("sludge_zone"),
    )

def disconnect_socketio():
    """Disconnect from Socket.IO dashboard"""
    global sio
    
    if sio and sio.connected:
        try:
            sio.disconnect()
            print("[SOCKETIO] Disconnected")
        except:
            pass
    
    sio = None

if __name__ == "__main__":
    # Test Socket.IO connection
    print("Testing Socket.IO connection...")
    
    client = connect_socketio()
    
    if client:
        print("\n✅ Connected successfully!")
        
        # Test sending data
        success = send_sludge_data(
            t_min=0,
            sludge_height_mm=125.0,
            mixture_height_mm=125.0,
            test_id="TEST-001"
        )
        
        if success:
            print("✅ Test data sent!")
        
        time.sleep(2)
        disconnect_socketio()
    else:
        print("\n❌ Connection failed!")
