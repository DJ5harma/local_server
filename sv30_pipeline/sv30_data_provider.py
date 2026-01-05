"""
SV30 Data Provider for HMI Integration

This module implements the DataProvider interface required by the HMI server.
It bridges the HMI system with the SV30 pipeline, allowing the HMI to start
tests and receive real-time data from the actual SV30 analysis system.

Usage in HMI:
    # In src/app.py of HMI server:
    from sv30_data_provider import SV30DataProvider
    data_provider = SV30DataProvider()
"""

import sys
import os
import time
import threading
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Add sv30 project to path
sv30_path = Path(__file__).parent
sys.path.insert(0, str(sv30_path))

# Import SV30 modules
from sv30config import (
    VIDEO_DURATION_SEC,
    CAM2_SNAPSHOT_T1_MIN,
    CAM2_SNAPSHOT_T2_MIN,
    UPLOAD_RAW_FOLDER,
    RESULTS_FOLDER,
)

# Import SV30 pipeline functions
from modules.video_capture import capture_video_and_snapshots
from modules.frame_extractor import extract_frames_from_video
from modules.preprocess import run_batch as preprocess_batch
from modules.mask_beaker import process_all as mask_batch
from modules.sludge_detect import run_batch as sludge_mask_batch
from modules.detect_geometry import run_batch as geometry_batch
from modules.sv30metrics import run_stage as metrics_batch, get_final_metrics
from modules.rgb_analysis import run_rgb_analysis, get_rgb_results
from modules.graph_generator import generate_graphs

logger = logging.getLogger(__name__)


class SV30DataProvider:
    """
    SV30 Pipeline Data Provider for HMI.
    
    Implements the DataProvider interface expected by the HMI server.
    Runs the actual SV30 analysis pipeline and returns results in HMI format.
    """
    
    def __init__(self):
        """Initialize SV30 data provider."""
        self.test_duration_minutes = VIDEO_DURATION_SEC / 60
        self.current_test_data = None
        self.height_history = []
        logger.info(f"SV30DataProvider initialized (test duration: {self.test_duration_minutes} min)")
    
    def generate_t0_data(self) -> Dict[str, Any]:
        """
        Generate initial data at test start (t=0).
        
        This captures the initial CAM2 snapshot and returns baseline measurements.
        
        Returns:
            Dictionary matching SludgeData interface with t=0 measurements
        """
        try:
            logger.info("Generating t=0 data...")
            
            now = datetime.now()
            test_type = self._determine_test_type(now.hour)
            test_id = f"SV30-{now.strftime('%Y%m%d_%H%M%S')}"
            
            # Capture initial CAM2 snapshot
            from modules.video_capture import VideoRecorder
            recorder = VideoRecorder()
            recorder.capture_cam2_snapshot('t2')  # Snapshot at t=2
            
            # Initial data (no sludge yet)
            data = {
                "testId": test_id,
                "timestamp": now.isoformat(),
                "testType": test_type[0],
                "sludge_height_mm": 0.0,
                "mixture_height_mm": 1000.0,  # Starting height
                "floc_count": 0,
                "floc_avg_size_mm": 0.0,
                "rgb_clear_zone": {"r": 255, "g": 255, "b": 255},
                "rgb_sludge_zone": {"r": 200, "g": 180, "b": 150},
                "t_min": 0,
                "image_filename": f"cam2_t2.jpg",
                "image_path": os.path.join(UPLOAD_RAW_FOLDER, "cam2_t2.jpg"),
            }
            
            self.current_test_data = data
            logger.info(f"t=0 data generated: {test_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to generate t=0 data: {e}")
            raise Exception(f"SV30 pipeline failed at t=0: {e}")
    
    def generate_t30_data(
        self, 
        initial_data: Dict[str, Any], 
        test_duration_minutes: float
    ) -> Dict[str, Any]:
        """
        Generate final data at test end (after full pipeline processing).
        
        This runs the complete SV30 pipeline:
        1. Video capture (already running in background)
        2. Frame extraction
        3. Image processing
        4. Sludge detection
        5. Metrics calculation
        6. RGB analysis
        
        Args:
            initial_data: The t=0 data
            test_duration_minutes: Actual test duration
            
        Returns:
            Dictionary matching SludgeData interface with final SV30 results
        """
        try:
            logger.info("Generating final test data (running SV30 pipeline)...")
            
            test_id = initial_data.get("testId")
            
            # Note: Video capture already completed (started at t=0)
            # Video should be in UPLOAD_VIDEOS_FOLDER
            
            # Find the most recent video file
            from pathlib import Path
            video_folder = Path(UPLOAD_VIDEOS_FOLDER)
            video_files = sorted(video_folder.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if not video_files:
                raise Exception("No video file found after capture")
            
            video_path = str(video_files[0])
            logger.info(f"Processing video: {video_path}")
            
            # Run SV30 pipeline
            logger.info("[1/7] Extracting frames...")
            success, frame_count, error = extract_frames_from_video(video_path)
            if not success:
                raise Exception(f"Frame extraction failed: {error}")
            
            logger.info("[2/7] Preprocessing...")
            preprocess_batch()
            
            logger.info("[3/7] Masking...")
            mask_batch()
            
            logger.info("[4/7] Detecting sludge...")
            sludge_mask_batch()
            
            logger.info("[5/7] Detecting geometry...")
            geometry_batch()
            
            logger.info("[6/7] Calculating metrics...")
            metrics_batch()
            
            logger.info("[7/7] Analyzing RGB...")
            run_rgb_analysis()
            
            # Generate graphs
            logger.info("Generating graphs...")
            generate_graphs()
            
            # Get final results
            metrics = get_final_metrics()
            rgb = get_rgb_results()
            
            if metrics is None:
                raise Exception("No metrics generated from pipeline")
            
            # Format for HMI
            now = datetime.now()
            final_sludge_height = metrics.get("sludge_height_mm", 0)
            final_mixture_height = metrics.get("mixture_height_mm", 1000)
            
            data = {
                "testId": test_id,
                "timestamp": now.isoformat(),
                "testType": initial_data.get("testType"),
                "sludge_height_mm": final_sludge_height,
                "mixture_height_mm": final_mixture_height,
                "sv30_height_mm": final_sludge_height,
                "sv30_mL_per_L": metrics.get("sv30_pct", 0) * 10,  # Convert % to mL/L
                "velocity_mm_per_min": metrics.get("avg_velocity", 0),
                "floc_count": 0,  # Can be extracted if needed
                "floc_avg_size_mm": 0.0,
                "rgb_clear_zone": rgb.get("clear_zone", {"r": 255, "g": 255, "b": 255}),
                "rgb_sludge_zone": rgb.get("sludge_zone", {"r": 200, "g": 180, "b": 150}),
                "t_min": int(test_duration_minutes),
                "image_filename": f"cam2_t{CAM2_SNAPSHOT_T2_MIN}.jpg",
                "image_path": os.path.join(UPLOAD_RAW_FOLDER, f"cam2_t{CAM2_SNAPSHOT_T2_MIN}.jpg"),
            }
            
            logger.info(f"SV30 pipeline complete: SV30={data['sv30_mL_per_L']:.2f} mL/L")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to generate final data: {e}")
            raise Exception(f"SV30 pipeline failed: {e}")
    
    def generate_height_history(
        self,
        initial_data: Dict[str, Any],
        duration_minutes: float,
        interval_seconds: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate sludge height measurements during test.
        
        For real-time integration, this would monitor the live video feed.
        For now, returns simulated settling curve until full processing.
        
        Args:
            initial_data: The t=0 data
            duration_minutes: Test duration in minutes
            interval_seconds: Measurement interval
            
        Returns:
            List of height measurements over time
        """
        try:
            entries = []
            start_time = datetime.fromisoformat(initial_data["timestamp"])
            test_type = initial_data.get("testType")
            
            num_intervals = int((duration_minutes * 60) / interval_seconds)
            
            # Generate settling curve
            # TODO: Replace with real-time frame analysis if needed
            for i in range(num_intervals):
                elapsed_seconds = i * interval_seconds
                timestamp = start_time.timestamp() + elapsed_seconds
                
                # Simulated settling (exponential decay)
                # Final height ~300mm after 35 min
                max_height = 1000.0
                min_height = 300.0
                decay_rate = 0.05
                height = min_height + (max_height - min_height) * (1 - (1 - pow(2.71828, -decay_rate * (elapsed_seconds / 60))))
                
                entry = {
                    "timestamp": int(timestamp),
                    "dateTime": datetime.fromtimestamp(timestamp).isoformat(),
                    "height": height,
                    "testType": test_type,
                }
                entries.append(entry)
            
            self.height_history = entries
            logger.info(f"Generated {len(entries)} height history entries")
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to generate height history: {e}")
            raise Exception(f"Height history generation failed: {e}")
    
    def _determine_test_type(self, current_hour: int) -> tuple:
        """Determine test type based on time of day."""
        if 6 <= current_hour < 12:
            return ("morning", "A")
        elif 12 <= current_hour < 18:
            return ("afternoon", "E")
        else:
            return ("evening", "E")
    
    def start_video_capture_background(self) -> bool:
        """
        Start video capture in background thread.
        
        This allows the HMI to show progress while video is recording.
        
        Returns:
            success: Boolean
        """
        try:
            def capture_thread():
                logger.info("Starting background video capture...")
                success, video_path = capture_video_and_snapshots()
                if success:
                    logger.info(f"Video capture complete: {video_path}")
                else:
                    logger.error("Video capture failed!")
            
            thread = threading.Thread(target=capture_thread, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start video capture: {e}")
            return False


# For testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*60)
    print("  SV30 DATA PROVIDER TEST")
    print("="*60)
    
    provider = SV30DataProvider()
    
    # Test t=0
    print("\nGenerating t=0 data...")
    t0_data = provider.generate_t0_data()
    print(f"✅ t=0 data: {t0_data}")
    
    # Test height history
    print("\nGenerating height history...")
    history = provider.generate_height_history(t0_data, 35.0, 60)
    print(f"✅ Generated {len(history)} entries")
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60)
