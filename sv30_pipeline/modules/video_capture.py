"""
Video Capture Module - USB Camera

Captures video from USB camera for specified duration.

Author: Jan 2026
"""

import os
import sys
import time
import logging
import cv2
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def capture_video():
    """
    Capture video from USB camera.
    
    Returns:
        str: Path to captured video file, or None if failed
    """
    logger.info("="*70)
    logger.info("  VIDEO CAPTURE - USB Camera")
    logger.info("="*70)
    logger.info(f"Camera: USB device {config.CAM1_USB_INDEX}")
    logger.info(f"Duration: {config.VIDEO_DURATION_SEC/60:.0f} minutes ({config.VIDEO_DURATION_SEC} seconds)")
    logger.info("="*70)
    
    # Output file
    timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
    output_file = os.path.join(config.UPLOAD_VIDEOS_FOLDER, f"{timestamp}_test.mp4")
    
    # Open camera
    logger.info(f"\nOpening camera {config.CAM1_USB_INDEX}...")
    cap = cv2.VideoCapture(config.CAM1_USB_INDEX)
    
    if not cap.isOpened():
        logger.error(f"❌ Cannot open camera {config.CAM1_USB_INDEX}")
        logger.error("   Check: ls -l /dev/video*")
        return None
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
    
    logger.info(f"✅ Camera opened successfully")
    logger.info(f"   Resolution: {width}x{height}")
    logger.info(f"   FPS: {fps}")
    
    # Video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    if not out.isOpened():
        logger.error("❌ Cannot create video writer")
        cap.release()
        return None
    
    # Capture loop
    logger.info(f"\n🎥 Recording to: {output_file}")
    logger.info("   Press Ctrl+C to stop early\n")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while (time.time() - start_time) < config.VIDEO_DURATION_SEC:
            ret, frame = cap.read()
            
            if not ret:
                logger.warning("Frame read failed")
                break
            
            out.write(frame)
            frame_count += 1
            
            # Progress every minute
            elapsed = time.time() - start_time
            if frame_count % int(fps * 60) == 0:
                mins_elapsed = elapsed / 60
                mins_remaining = (config.VIDEO_DURATION_SEC - elapsed) / 60
                logger.info(f"  ⏱️  {mins_elapsed:.1f} min elapsed | {mins_remaining:.1f} min remaining")
    
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Recording stopped by user")
    
    # Cleanup
    cap.release()
    out.release()
    
    elapsed = time.time() - start_time
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    
    logger.info("\n" + "="*70)
    logger.info("  ✅ RECORDING COMPLETE")
    logger.info("="*70)
    logger.info(f"Frames: {frame_count}")
    logger.info(f"Duration: {elapsed/60:.1f} minutes")
    logger.info(f"File size: {file_size:.1f} MB")
    logger.info(f"Output: {output_file}")
    logger.info("="*70 + "\n")
    
    return output_file


if __name__ == "__main__":
    # Test video capture
    video_path = capture_video()
    if video_path:
        print(f"✅ Test successful: {video_path}")
    else:
        print("❌ Test failed")
        sys.exit(1)