"""
Send to Dashboard Module

Sends final results to Thermax dashboard via SocketIO.
Uses exact format from backend documentation.

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


def send_results():
    """
    Send final metrics to dashboard via SocketIO.
    
    Event: sludge-data
    Required fields: factoryCode, timestamp, testType, t_min, sludge_height_mm, 
                     mixture_height_mm, floc_count, floc_avg_size_mm
    """
    logger.info("\n" + "="*70)
    logger.info("  SEND RESULTS TO DASHBOARD")
    logger.info("="*70)
    
    # Check if SocketIO is enabled
    if not config.SOCKETIO_ENABLED:
        logger.info("⚠️  SocketIO disabled in config")
        logger.info("   Set SOCKETIO_ENABLED = True in sv30config.py")
        return False
    
    # Check factory code
    if not hasattr(config, 'FACTORY_CODE') or not config.FACTORY_CODE:
        logger.error("❌ FACTORY_CODE not set in sv30config.py!")
        logger.error("   Add: FACTORY_CODE = 'factory-a'")
        return False
    
    # Load final metrics
    metrics_path = os.path.join(config.RESULTS_FOLDER, "final_metrics.json")
    
    if not os.path.exists(metrics_path):
        logger.error(f"❌ Metrics not found: {metrics_path}")
        logger.error("   Run: python modules/calculate_metrics.py first")
        return False
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    logger.info(f"Loaded metrics from: {metrics_path}")
    logger.info(f"Factory Code: {config.FACTORY_CODE}")
    logger.info(f"URL: {config.SOCKETIO_URL}\n")
    
    try:
        import socketio
        
        # Create SocketIO client
        sio = socketio.Client()
        
        # Track connection
        connected = [False]
        
        @sio.event
        def connect():
            logger.info("✅ Connected to dashboard!")
            connected[0] = True
        
        @sio.event
        def connect_error(data):
            logger.error(f"❌ Connection error: {data}")
        
        @sio.event
        def disconnect():
            logger.info("🔌 Disconnected from dashboard")
        
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
            "rgb_clear_zone": {"r": 245, "g": 250, "b": 255},
            "rgb_sludge_zone": {"r": 180, "g": 160, "b": 140}
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
            "sv30_mL_per_L": metrics['sv30_pct'] * 10,  # Convert % to mL/L
            "velocity_mm_per_min": metrics['settling_rate_mm_per_min'],
            "rgb_clear_zone": {"r": 245, "g": 250, "b": 255},
            "rgb_sludge_zone": {"r": 180, "g": 160, "b": 140}
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
            logger.error("❌ Failed to connect!")
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
        
        logger.info("\n✅ Results sent successfully!")
        logger.info("   Check dashboard for updates!")
        logger.info("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Failed to send: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test sending
    success = send_results()
    
    if success:
        print("\n✅ Dashboard send successful!")
    else:
        print("\n❌ Dashboard send failed!")
        sys.exit(1)