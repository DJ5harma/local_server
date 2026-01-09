"""
Send to Dashboard Module

⚠️ DEPRECATED: This module is no longer used for sending data to the backend.

Data sending is now handled by local_server/src/services/backend_client.py via
the test_service.py workflow. This ensures:
- No duplicate data sending
- Consistent data format matching backend schema
- Proper integration with the HMI test service

This module is kept for reference only. Do not call send_results() from main.py.

The correct data flow is:
1. sv30_pipeline generates results (metrics, RGB values)
2. sv30_data_provider.py reads results from pipeline
3. test_service.py calls data_provider.generate_t30_data()
4. backend_client.py sends data via Socket.IO with proper format

Author: Jan 2026
"""

import os
import sys
import json
import logging
from datetime import datetime
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def determine_test_type():
    """
    Determine test type based on current hour.
    
    Returns:
        tuple: (test_type_name, test_type_code)
    """
    hour = datetime.now().hour
    
    if 6 <= hour < 12:
        return ("morning", "M")
    elif 12 <= hour < 18:
        return ("afternoon", "A")
    else:
        return ("evening", "E")


def load_rgb_values():
    """
    Load RGB values from rgb_values.json.
    
    Returns:
        tuple: (clear_rgb, sludge_rgb) dictionaries
    """
    rgb_file = os.path.join(config.RESULTS_FOLDER, "rgb_values.json")
    
    if os.path.exists(rgb_file):
        try:
            with open(rgb_file, 'r') as f:
                rgb_data = json.load(f)
            
            clear_rgb = rgb_data['clear_zone']['rgb']
            sludge_rgb = rgb_data['sludge_zone']['rgb']
            
            logger.info(f"? Loaded RGB values from: {rgb_file}")
            logger.info(f"   Clear zone: RGB({clear_rgb['r']}, {clear_rgb['g']}, {clear_rgb['b']})")
            logger.info(f"   Sludge zone: RGB({sludge_rgb['r']}, {sludge_rgb['g']}, {sludge_rgb['b']})\n")
            
            return clear_rgb, sludge_rgb
            
        except Exception as e:
            logger.warning(f"??  Failed to load RGB data: {e}")
            logger.warning("   Using fallback RGB values\n")
    else:
        logger.warning(f"??  RGB file not found: {rgb_file}")
        logger.warning("   Using fallback RGB values\n")
    
    # Fallback RGB values
    clear_rgb = {"r": 245, "g": 250, "b": 255}
    sludge_rgb = {"r": 180, "g": 160, "b": 140}
    
    return clear_rgb, sludge_rgb


def send_results():
    """
    Send final metrics to dashboard via SocketIO.
    
    ⚠️ DEPRECATED: This function should NOT be called.
    Data sending is handled by local_server/src/services/backend_client.py
    
    This function is kept for reference only. If you need to send data,
    use the test_service.py workflow instead.
    
    Event: sludge-data
    Required fields: factoryCode, timestamp, testType, t_min, sludge_height_mm, 
                     mixture_height_mm, floc_count, floc_avg_size_mm
    """
    # Early return to prevent accidental execution
    logger.warning("⚠️ send_results() is deprecated and should not be called!")
    logger.warning("   Data sending is handled by local_server/src/services/backend_client.py")
    logger.warning("   This function returns immediately without sending data.")
    return False
    logger.info("\n" + "="*70)
    logger.info("  SEND RESULTS TO DASHBOARD")
    logger.info("="*70)
    
    # Check if SocketIO is enabled
    if not config.SOCKETIO_ENABLED:
        logger.info("??  SocketIO disabled in config")
        logger.info("   Set SOCKETIO_ENABLED = True in sv30config.py")
        return False
    
    # Check factory code
    if not hasattr(config, 'FACTORY_CODE') or not config.FACTORY_CODE:
        logger.error("? FACTORY_CODE not set in sv30config.py!")
        logger.error("   Add: FACTORY_CODE = 'factory-a'")
        return False
    
    # Load final metrics
    metrics_path = os.path.join(config.RESULTS_FOLDER, "final_metrics.json")
    
    if not os.path.exists(metrics_path):
        logger.error(f"? Metrics not found: {metrics_path}")
        logger.error("   Run: python modules/calculate_metrics.py first")
        return False
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    logger.info(f"Loaded metrics from: {metrics_path}")
    logger.info(f"Factory Code: {config.FACTORY_CODE}")
    logger.info(f"URL: {config.SOCKETIO_URL}\n")
    
    # Load RGB values
    clear_rgb, sludge_rgb = load_rgb_values()
    
    try:
        import socketio
        
        # Create SocketIO client
        sio = socketio.Client()
        
        # Track connection
        connected = [False]
        
        @sio.event
        def connect():
            logger.info("? Connected to dashboard!")
            connected[0] = True
        
        @sio.event
        def connect_error(data):
            logger.error(f"? Connection error: {data}")
        
        @sio.event
        def disconnect():
            logger.info("? Disconnected from dashboard")
        
        # Determine test type
        test_type, test_code = determine_test_type()
        test_date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate test ID
        test_id = f"SV30-{test_date}-{datetime.now().strftime('%H%M%S')}-{test_code}"
        
        # Prepare t=0 payload (EXACT format from documentation)
        t0_payload = {
            "timestamp": datetime.now().isoformat() + "Z",
            "testType": test_type,
            "factoryCode": config.FACTORY_CODE,
            "t_min": 0,
            "testId": test_id,
            "operator": "Thermax",
            "sludge_height_mm": metrics.get('sludge_height_t0_mm', 0),
            "mixture_height_mm": metrics['mixture_height_mm'],
            "floc_count": 0,  # Not calculated in our system
            "floc_avg_size_mm": 0.0,  # Not calculated in our system
            "rgb_clear_zone": clear_rgb,  # Real RGB values
            "rgb_sludge_zone": sludge_rgb  # Real RGB values
        }
        
        # Prepare t=30 payload (EXACT format from documentation)
        t30_payload = {
            "timestamp": datetime.now().isoformat() + "Z",
            "testType": test_type,
            "factoryCode": config.FACTORY_CODE,
            "t_min": int(metrics['test_duration_min']),
            "testId": test_id,
            "operator": "Thermax",
            "sludge_height_mm": metrics['sludge_height_t30_mm'],
            "mixture_height_mm": metrics['mixture_height_mm'],
            "floc_count": 0,  # Not calculated
            "floc_avg_size_mm": 0.0,  # Not calculated
            "sv30_mL_per_L": metrics['sv30_mL_per_L'],  # Already calculated
            "velocity_mm_per_min": metrics['settling_rate_mm_per_min'],
            "rgb_clear_zone": clear_rgb,  # Real RGB values
            "rgb_sludge_zone": sludge_rgb  # Real RGB values
        }
        
        logger.info("t=0 Payload:")
        logger.info(json.dumps(t0_payload, indent=2))
        logger.info("\nt=30 Payload:")
        logger.info(json.dumps(t30_payload, indent=2))
        logger.info("")
        
        # Connect
        logger.info("Connecting...")
        sio.connect(config.SOCKETIO_URL)
        
        # Wait for connection
        time.sleep(2)
        
        if not connected[0]:
            logger.error("? Failed to connect!")
            return False
        
        # Send t=0 data
        logger.info("Sending t=0 data...")
        sio.emit('sludge-data', t0_payload)
        time.sleep(1)
        
        # Send t=30 data
        logger.info("Sending t=30 data...")
        sio.emit('sludge-data', t30_payload)
        time.sleep(2)
        
        # Disconnect
        sio.disconnect()
        
        logger.info("\n? Results sent successfully!")
        logger.info("   Check dashboard for updates!")
        logger.info("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n? Failed to send: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test sending
    success = send_results()
    
    if success:
        print("\n? Dashboard send successful!")
    else:
        print("\n? Dashboard send failed!")
        sys.exit(1)
