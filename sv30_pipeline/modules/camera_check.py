"""
Camera Connectivity Check Module

Verifies that both cameras are accessible before starting the test.
This prevents wasted 30-minute test runs when cameras are offline.
"""

import cv2
import time
from sv30config import CAM1_URL, CAM2_URL, CAMERA_CHECK_TIMEOUT_SEC

def check_single_camera(camera_url, camera_name, timeout=10):
    """
    Check if a single camera is accessible
    
    Args:
        camera_url: RTSP URL of the camera
        camera_name: Name for logging (e.g., "CAM1")
        timeout: Timeout in seconds
    
    Returns:
        success: Boolean indicating if camera is accessible
        error: Error message if failed
    """
    try:
        # Attempt to open camera
        cap = cv2.VideoCapture(camera_url)
        
        # Set timeout
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
        
        if not cap.isOpened():
            cap.release()
            return False, f"{camera_name} could not be opened"
        
        # Try to read a frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return False, f"{camera_name} opened but cannot read frames"
        
        # Success!
        return True, None
        
    except Exception as e:
        return False, f"{camera_name} error: {str(e)}"

def check_camera_connectivity():
    """
    Check if both cameras are accessible
    
    Returns:
        cam1_ok: Boolean
        cam2_ok: Boolean
    """
    print("\n" + "="*60)
    print("  CAMERA CONNECTIVITY CHECK")
    print("="*60)
    
    # Check Camera 1
    print(f"\n[CAM1] Testing connection...")
    print(f"  URL: {CAM1_URL[:50]}...")
    
    cam1_ok, cam1_error = check_single_camera(
        CAM1_URL, 
        "CAM1", 
        CAMERA_CHECK_TIMEOUT_SEC
    )
    
    if cam1_ok:
        print(f"  Status: ✅ OK")
    else:
        print(f"  Status: ❌ FAILED")
        print(f"  Error: {cam1_error}")
    
    # Check Camera 2
    print(f"\n[CAM2] Testing connection...")
    print(f"  URL: {CAM2_URL[:50]}...")
    
    cam2_ok, cam2_error = check_single_camera(
        CAM2_URL, 
        "CAM2", 
        CAMERA_CHECK_TIMEOUT_SEC
    )
    
    if cam2_ok:
        print(f"  Status: ✅ OK")
    else:
        print(f"  Status: ❌ FAILED")
        print(f"  Error: {cam2_error}")
    
    # Summary
    print(f"\n" + "="*60)
    if cam1_ok and cam2_ok:
        print("  ✅ BOTH CAMERAS OK - Proceeding with test")
    else:
        print("  ❌ CAMERA CHECK FAILED - Aborting test")
        if not cam1_ok:
            print(f"     CAM1: {cam1_error}")
        if not cam2_ok:
            print(f"     CAM2: {cam2_error}")
    print("="*60 + "\n")
    
    return cam1_ok, cam2_ok

if __name__ == "__main__":
    # Test the camera check
    cam1_ok, cam2_ok = check_camera_connectivity()
    
    if cam1_ok and cam2_ok:
        print("\n✅ Camera check passed!")
    else:
        print("\n❌ Camera check failed!")
        exit(1)
