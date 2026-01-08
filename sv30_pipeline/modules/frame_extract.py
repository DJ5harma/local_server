"""
Frame Extraction Module

Extracts frames from video at regular intervals.

Author: Jan 2026
"""

import os
import sys
import cv2
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


def extract_frames(video_path):
    """
    Extract frames from video at regular intervals.
    
    Args:
        video_path: Path to video file
        
    Returns:
        int: Number of frames extracted
    """
    logger.info("="*70)
    logger.info("  FRAME EXTRACTION")
    logger.info("="*70)
    logger.info(f"Video: {video_path}")
    logger.info(f"Output: {config.RAW_FOLDER}")
    logger.info(f"Interval: {config.FRAME_INTERVAL_SEC} seconds")
    logger.info("="*70 + "\n")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"❌ Cannot open video: {video_path}")
        return 0
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    logger.info(f"Video properties:")
    logger.info(f"  FPS: {fps}")
    logger.info(f"  Total frames: {total_frames}")
    logger.info(f"  Duration: {duration/60:.1f} minutes\n")
    
    # Calculate frame interval
    frame_interval = int(fps * config.FRAME_INTERVAL_SEC)
    expected_frames = total_frames // frame_interval
    
    logger.info(f"Extraction settings:")
    logger.info(f"  Frame interval: {frame_interval} frames")
    logger.info(f"  Expected output: ~{expected_frames} frames\n")
    
    # Extract frames
    frame_num = 0
    extracted = 0
    
    logger.info("Extracting frames...")
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Extract frame at intervals
        if frame_num % frame_interval == 0:
            # Calculate time
            time_sec = frame_num / fps
            
            # Save frame
            output_file = os.path.join(
                config.RAW_FOLDER,
                f"frame{extracted:04d}_t{int(time_sec)}s.png"
            )
            cv2.imwrite(output_file, frame)
            extracted += 1
            
            # Progress
            if extracted % 10 == 0:
                logger.info(f"  Extracted {extracted} frames...")
        
        frame_num += 1
    
    cap.release()
    
    logger.info("\n" + "="*70)
    logger.info("  EXTRACTION COMPLETE")
    logger.info("="*70)
    logger.info(f"Extracted: {extracted} frames")
    logger.info(f"Output: {config.RAW_FOLDER}")
    logger.info("="*70 + "\n")
    
    if not config.DEV_MODE:
        try:
            logger.info(f"[PROD MODE] Deleting video: {video_path}")
            os.remove(video_path)
        except Exception as e:
            logger.warning(f"  [WARN] Could not delete video: {e}")
            
    return extracted


if __name__ == "__main__":
    # Test with a video file
    import sys
    if len(sys.argv) < 2:
        print("Usage: python frame_extract.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    count = extract_frames(video_path)
    print(f"✅ Extracted {count} frames")
