"""
Video Capture Module (v4.0 - USB + RTSP Support)

Supports both USB cameras and RTSP cameras for flexibility.
Captures 35-minute video and CAM2 snapshots at t=2 and t=33 minutes.
"""

import subprocess
import os
import time
from datetime import datetime
import signal
import cv2
from sv30config import (
    CAM1_TYPE,
    CAM1_USB_INDEX,
    CAM1_USB_WIDTH,
    CAM1_USB_HEIGHT,
    CAM1_USB_FPS,
    CAM1_USB_FOURCC,
    CAM1_URL,
    CAM2_URL,
    CAM2_ROTATE,
    CAM2_FLIP,
    UPLOAD_VIDEOS_FOLDER,
    UPLOAD_RAW_FOLDER,
    VIDEO_DURATION_SEC,
    VIDEO_BUFFER_SEC,
    VIDEO_CODEC,
    VIDEO_FORMAT,
    VIDEO_RTSP_TRANSPORT,
    CAM2_SNAPSHOT_T1_MIN,
    CAM2_SNAPSHOT_T2_MIN,
)

class VideoRecorder:
    def __init__(self):
        self.running = True
        self.cam2_t1_captured = False  # t=2 min snapshot
        self.cam2_t2_captured = False  # t=33 min snapshot
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n[INTERRUPT] Stopping video capture...")
        self.running = False
    
    def generate_filename(self):
        """Generate timestamped filename: ddmmyy_hhmmsstest1.mp4"""
        timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
        return f"{timestamp}test1.{VIDEO_FORMAT}"
    
    def capture_cam2_snapshot(self, label):
        """
        Capture single frame from Camera 2
        
        Args:
            label: 't2' or 't33' for filename
        
        Returns:
            Success boolean
        """
        print(f"\n[CAM2] Capturing {label} snapshot...")
        
        cap = cv2.VideoCapture(CAM2_URL, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            print(f"[CAM2 ERROR] Failed to open Camera 2")
            cap.release()
            return False
        
        # Warmup reads
        frame = None
        for _ in range(10):
            ret, f = cap.read()
            if ret and f is not None:
                frame = f
            time.sleep(0.1)
        
        cap.release()
        
        if frame is None:
            print(f"[CAM2 ERROR] Failed to capture frame")
            return False
        
        # Apply transformations if configured
        if CAM2_ROTATE is not None:
            frame = cv2.rotate(frame, CAM2_ROTATE)
        if CAM2_FLIP is not None:
            frame = cv2.flip(frame, CAM2_FLIP)
        
        # Save snapshot
        filename = f"cam2_{label}.jpg"
        filepath = os.path.join(UPLOAD_RAW_FOLDER, filename)
        
        success = cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        if success:
            print(f"[CAM2] Saved: {filename}")
        else:
            print(f"[CAM2 ERROR] Failed to save: {filename}")
        
        return success
    
    def record_video_usb(self, duration_sec):
        """
        Record video using USB camera with OpenCV
        
        Args:
            duration_sec: Recording duration in seconds
        
        Returns:
            (success, filepath, actual_duration)
        """
        filename = self.generate_filename()
        filepath = os.path.join(UPLOAD_VIDEOS_FOLDER, filename)
        
        print(f"\n[USB VIDEO] Starting recording...")
        print(f"  Device: {CAM1_USB_INDEX}")
        print(f"  Duration: {duration_sec}s ({duration_sec/60:.1f} min)")
        print(f"  Resolution: {CAM1_USB_WIDTH}x{CAM1_USB_HEIGHT}")
        print(f"  FPS: {CAM1_USB_FPS}")
        print(f"  Output: {filename}")
        
        try:
            # Open USB camera
            cap = cv2.VideoCapture(CAM1_USB_INDEX)
            
            if not cap.isOpened():
                print(f"[USB ERROR] Failed to open USB camera at index {CAM1_USB_INDEX}")
                return False, None, 0
            
            # Set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM1_USB_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM1_USB_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAM1_USB_FPS)
            
            # Set FOURCC codec
            fourcc = cv2.VideoWriter_fourcc(*CAM1_USB_FOURCC)
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            
            # Get actual properties (might differ from requested)
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = cap.get(cv2.CAP_PROP_FPS)
            
            print(f"  Actual resolution: {actual_width}x{actual_height}")
            print(f"  Actual FPS: {actual_fps}")
            
            # Create video writer
            fourcc_out = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filepath, fourcc_out, actual_fps, (actual_width, actual_height))
            
            if not out.isOpened():
                print(f"[USB ERROR] Failed to create video writer")
                cap.release()
                return False, None, 0
            
            # Record video
            start_time = time.time()
            frame_count = 0
            
            print(f"[USB VIDEO] Recording... (Press Ctrl+C to stop)")
            
            while self.running:
                elapsed = time.time() - start_time
                
                # Check if duration reached
                if elapsed >= duration_sec:
                    break
                
                # Capture CAM2 snapshots at specific times
                if not self.cam2_t1_captured and elapsed >= (CAM2_SNAPSHOT_T1_MIN * 60):
                    print(f"\n[CAM2] Capturing t={CAM2_SNAPSHOT_T1_MIN} min snapshot...")
                    self.capture_cam2_snapshot('t2')
                    self.cam2_t1_captured = True
                
                if not self.cam2_t2_captured and elapsed >= (CAM2_SNAPSHOT_T2_MIN * 60):
                    print(f"\n[CAM2] Capturing t={CAM2_SNAPSHOT_T2_MIN} min snapshot...")
                    self.capture_cam2_snapshot('t33')
                    self.cam2_t2_captured = True
                
                # Read frame
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    print(f"\n[USB ERROR] Failed to read frame at {elapsed:.1f}s")
                    continue
                
                # Write frame
                out.write(frame)
                frame_count += 1
                
                # Progress update every 60 seconds
                if frame_count % (int(actual_fps) * 60) == 0:
                    mins_elapsed = elapsed / 60
                    mins_remaining = (duration_sec - elapsed) / 60
                    print(f"  Progress: {mins_elapsed:.1f} / {duration_sec/60:.1f} min ({mins_remaining:.1f} min remaining)")
            
            actual_duration = time.time() - start_time
            
            # Cleanup
            cap.release()
            out.release()
            
            # Verify file
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000000:  # >1MB
                print(f"\n[USB VIDEO] Recording complete!")
                print(f"  Frames: {frame_count}")
                print(f"  Duration: {actual_duration:.1f}s ({actual_duration/60:.1f} min)")
                print(f"  File size: {os.path.getsize(filepath) / 1024 / 1024:.1f} MB")
                
                # Capture final CAM2 snapshot if not done
                if not self.cam2_t2_captured:
                    print(f"\n[CAM2] Capturing final t={CAM2_SNAPSHOT_T2_MIN} min snapshot...")
                    self.capture_cam2_snapshot('t33')
                    self.cam2_t2_captured = True
                
                return True, filepath, actual_duration
            else:
                print(f"[USB ERROR] File too small or missing")
                return False, None, 0
        
        except Exception as e:
            print(f"[USB ERROR] Recording failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None, 0
    
    def record_video_rtsp(self, duration_sec):
        """
        Record video using RTSP camera with FFmpeg
        
        Args:
            duration_sec: Recording duration in seconds
        
        Returns:
            (success, filepath, actual_duration)
        """
        filename = self.generate_filename()
        filepath = os.path.join(UPLOAD_VIDEOS_FOLDER, filename)
        
        print(f"\n[RTSP VIDEO] Starting recording...")
        print(f"  Duration: {duration_sec}s ({duration_sec/60:.1f} min)")
        print(f"  Output: {filename}")
        
        # FFmpeg command (optimized for Raspberry Pi)
        cmd = [
            'ffmpeg',
            '-rtsp_transport', VIDEO_RTSP_TRANSPORT,
            '-i', CAM1_URL,
            '-t', str(duration_sec),
            '-c:v', VIDEO_CODEC,
            '-c:a', 'aac',
            '-f', VIDEO_FORMAT,
            '-y',  # Overwrite
            filepath
        ]
        
        start_time = time.time()
        
        try:
            # Run FFmpeg with real-time output suppression
            process = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=duration_sec + 60  # Add 60s timeout buffer
            )
            
            actual_duration = time.time() - start_time
            
            # Verify file exists and has content
            if os.path.exists(filepath) and os.path.getsize(filepath) > 1000000:  # >1MB
                print(f"[RTSP VIDEO] Recording complete: {filepath}")
                print(f"  Actual duration: {actual_duration:.1f}s")
                return True, filepath, actual_duration
            else:
                print(f"[RTSP ERROR] File too small or missing")
                return False, None, 0
        
        except subprocess.TimeoutExpired:
            print(f"[RTSP ERROR] Recording timeout exceeded")
            return False, None, 0
        
        except subprocess.CalledProcessError as e:
            print(f"[RTSP ERROR] FFmpeg failed: {e.stderr}")
            return False, None, 0
        
        except FileNotFoundError:
            print(f"[RTSP ERROR] FFmpeg not found! Install: sudo apt install ffmpeg")
            return False, None, 0
        
        except Exception as e:
            print(f"[RTSP ERROR] Unexpected error: {e}")
            return False, None, 0
    
    def record_with_retry(self):
        """
        Record 35 minutes of video with retry logic
        Captures CAM2 snapshots at t=2 and t=33 minutes
        
        Returns:
            (success, video_path)
        """
        target_duration = VIDEO_DURATION_SEC
        max_total_time = VIDEO_DURATION_SEC + VIDEO_BUFFER_SEC
        
        # Snapshot timing (in seconds)
        t1_snapshot_sec = CAM2_SNAPSHOT_T1_MIN * 60  # t=2 min
        t2_snapshot_sec = CAM2_SNAPSHOT_T2_MIN * 60  # t=33 min
        
        total_recorded = 0
        attempt = 0
        start_time = time.time()
        
        print("\n" + "="*60)
        print("  VIDEO CAPTURE WITH RETRY")
        print("="*60)
        print(f"Camera Type: {CAM1_TYPE}")
        print(f"Target: {target_duration}s ({target_duration/60} min)")
        print(f"Max time (with buffer): {max_total_time}s ({max_total_time/60} min)")
        print(f"CAM2 snapshots: t={CAM2_SNAPSHOT_T1_MIN} min, t={CAM2_SNAPSHOT_T2_MIN} min")
        print("="*60 + "\n")
        
        video_path = None
        
        # Choose recording method based on camera type
        if CAM1_TYPE == "USB":
            # USB cameras don't need retry logic - single recording session
            print("[USB] Recording in single session...")
            success, video_path, duration = self.record_video_usb(target_duration)
            return success, video_path
        
        else:  # RTSP
            # RTSP uses retry logic (original implementation)
            while total_recorded < target_duration and self.running:
                elapsed_total = time.time() - start_time
                
                # Check if we've exceeded buffer time
                if elapsed_total > max_total_time:
                    print(f"\n[ERROR] Exceeded maximum time ({max_total_time}s)")
                    print(f"  Recorded: {total_recorded}s / {target_duration}s")
                    return False, None
                
                # Capture CAM2 at specific times during RTSP recording
                if not self.cam2_t1_captured and total_recorded >= t1_snapshot_sec:
                    print(f"\n[CAM2] Capturing t={CAM2_SNAPSHOT_T1_MIN} min snapshot...")
                    self.capture_cam2_snapshot('t2')
                    self.cam2_t1_captured = True
                
                if not self.cam2_t2_captured and total_recorded >= t2_snapshot_sec:
                    print(f"\n[CAM2] Capturing t={CAM2_SNAPSHOT_T2_MIN} min snapshot...")
                    self.capture_cam2_snapshot('t33')
                    self.cam2_t2_captured = True
                
                attempt += 1
                remaining = target_duration - total_recorded
                
                print(f"\n[ATTEMPT {attempt}] Need {remaining}s more...")
                
                success, path, duration = self.record_video_rtsp(remaining)
                
                if success:
                    total_recorded += duration
                    video_path = path
                    
                    if total_recorded >= target_duration:
                        print(f"\n[SUCCESS] Captured {total_recorded:.1f}s of video")
                        break
                    else:
                        print(f"[PARTIAL] Recorded {total_recorded:.1f}s / {target_duration}s")
                        print("[RETRY] Continuing recording...")
                        time.sleep(2)
                else:
                    print(f"[RETRY] Attempt {attempt} failed, retrying in 10s...")
                    time.sleep(10)
            
            # Capture final CAM2 snapshot if not done
            if video_path and not self.cam2_t2_captured:
                print(f"\n[CAM2] Capturing final t={CAM2_SNAPSHOT_T2_MIN} min snapshot...")
                self.capture_cam2_snapshot('t33')
                self.cam2_t2_captured = True
            
            return (video_path is not None), video_path

def capture_video_and_snapshots():
    """
    Main entry point for video capture module
    
    Returns:
        (success, video_path)
    """
    print("\n" + "="*60)
    print("  SV30 VIDEO CAPTURE MODULE (v4.0)")
    print("="*60)
    
    if CAM1_TYPE == "USB":
        print(f"Camera 1 (USB): Device {CAM1_USB_INDEX}")
        print(f"  Resolution: {CAM1_USB_WIDTH}x{CAM1_USB_HEIGHT}")
        print(f"  FPS: {CAM1_USB_FPS}")
    else:
        print(f"Camera 1 (RTSP): {CAM1_URL}")
    
    print(f"Camera 2 (RGB): {CAM2_URL}")
    print(f"Output: {UPLOAD_VIDEOS_FOLDER}")
    print("="*60 + "\n")
    
    recorder = VideoRecorder()
    success, video_path = recorder.record_with_retry()
    
    if success:
        print("\n" + "="*60)
        print("  VIDEO CAPTURE COMPLETE")
        print("="*60)
        print(f"Video: {video_path}")
        print(f"Snapshots: upload_raw/cam2_t2.jpg, cam2_t33.jpg")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("  VIDEO CAPTURE FAILED")
        print("="*60 + "\n")
    
    return success, video_path

if __name__ == "__main__":
    capture_video_and_snapshots()
