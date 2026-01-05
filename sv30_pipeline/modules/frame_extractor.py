import cv2
import os
from sv30config import (
    RAW_FOLDER,
    FRAME_INTERVAL_SEC,
)

def extract_frames_from_video(video_path, output_folder=RAW_FOLDER, interval_sec=FRAME_INTERVAL_SEC):
    """
    Extract frames from video at specified intervals
    
    Args:
        video_path: Path to input video file
        output_folder: Where to save extracted frames
        interval_sec: Time interval between frames (seconds)
    
    Returns:
        (success, frame_count, error_message)
    """
    print("\n" + "="*60)
    print("  FRAME EXTRACTION")
    print("="*60)
    print(f"Video: {video_path}")
    print(f"Output: {output_folder}")
    print(f"Interval: {interval_sec}s")
    print("="*60 + "\n")
    
    # Verify video file exists
    if not os.path.exists(video_path):
        error_msg = f"Video file not found: {video_path}"
        print(f"[ERROR] {error_msg}")
        return False, 0, error_msg
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Open video
    video = cv2.VideoCapture(video_path)
    
    if not video.isOpened():
        error_msg = f"Failed to open video: {video_path}"
        print(f"[ERROR] {error_msg}")
        return False, 0, error_msg
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"[INFO] Video FPS: {fps:.2f}")
    print(f"[INFO] Total frames: {total_frames}")
    print(f"[INFO] Duration: {duration:.2f}s ({duration/60:.2f} min)")
    
    if fps <= 0 or total_frames <= 0:
        error_msg = "Invalid video properties (FPS or frame count)"
        print(f"[ERROR] {error_msg}")
        video.release()
        return False, 0, error_msg
    
    # Calculate frame interval
    frame_interval = int(fps * interval_sec)
    expected_frames = int(duration / interval_sec) + 1
    
    print(f"[INFO] Frame interval: {frame_interval} frames")
    print(f"[INFO] Expected output: ~{expected_frames} frames\n")
    
    # Extract frames
    frame_number = 0
    count = 0
    failed_count = 0
    
    while True:
        # Seek to specific frame
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = video.read()
        
        if not success:
            break
        
        # Generate filename with timestamp
        time_sec = frame_number / fps
        minutes = int(time_sec // 60)
        seconds = int(time_sec % 60)
        
        # Format: cam1_DDMMYY_HHMMSS.jpg
        # We'll use frame index to maintain order
        output_filename = f"cam1_frame{count:04d}_{minutes:02d}m{seconds:02d}s.jpg"
        output_path = os.path.join(output_folder, output_filename)
        
        # Save frame
        write_success = cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if write_success:
            count += 1
            if count % 10 == 0:
                print(f"[PROGRESS] Extracted {count} frames...")
        else:
            failed_count += 1
            print(f"[WARN] Failed to save: {output_filename}")
        
        # Move to next frame
        frame_number += frame_interval
    
    video.release()
    
    print(f"\n[COMPLETE] Extracted {count} frames")
    if failed_count > 0:
        print(f"[WARN] Failed: {failed_count} frames")
    
    print("="*60 + "\n")
    
    if count == 0:
        return False, 0, "No frames extracted"
    
    return True, count, None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python frame_extractor.py <video_path>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    success, count, error = extract_frames_from_video(video_path)
    
    if success:
        print(f"SUCCESS: Extracted {count} frames")
        sys.exit(0)
    else:
        print(f"FAILED: {error}")
        sys.exit(1)
