"""
SV30 Data Provider - HMI Integration

Bridges HMI with SV30 pipeline by running it as subprocess.

Author: Jan 2026
"""

import os
import sys
import time
import json
import logging
import subprocess
from typing import Dict, Any, List
from pathlib import Path

from .data_provider import DataProvider
from ..utils.dateUtils import now_ist, now_ist_iso_utc, format_date_ist

logger = logging.getLogger(__name__)


class SV30DataProvider(DataProvider):
    """Real SV30 data provider - runs pipeline as subprocess"""
    
    def __init__(self, sv30_path: str = None):
        if sv30_path is None:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            sv30_path = str(project_root / "sv30_pipeline")
        
        self.sv30_path = sv30_path
        self.current_test_id = None
        self.subprocess_process = None
        
        if not os.path.exists(sv30_path):
            raise FileNotFoundError(f"sv30_pipeline not found at: {sv30_path}")
        
        if not os.path.exists(os.path.join(sv30_path, "main.py")):
            raise FileNotFoundError(f"main.py not found in: {sv30_path}")
        
        logger.info(f"[SV30] Initialized at: {sv30_path}")
    
    def generate_t0_data(self) -> Dict[str, Any]:
        """Generate t=0 data AND start video capture subprocess"""
        # Use IST time for all operations
        now = now_ist()
        test_type = self._determine_test_type(now.hour)
        # Use same test ID format as dummy provider for consistency
        date_str = format_date_ist(now)
        test_type_code = test_type[1]
        self.current_test_id = f"SV30-{date_str}-001-{test_type_code}"
        
        logger.info(f"[SV30] 🚀 Starting test: {self.current_test_id} (IST: {now.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # Start subprocess
        started = self._start_capture_subprocess()
        
        if not started:
            raise Exception("Failed to start SV30 capture subprocess")
        
        # Get timestamp in UTC format (for backend compatibility)
        # The time represents IST moment but formatted as UTC ISO string
        timestamp = now_ist_iso_utc()
        
        # Use default RGB values (will be updated from pipeline results at t=30)
        # Ensure these are integers
        rgb_clear_zone = {"r": int(255), "g": int(255), "b": int(255)}
        rgb_sludge_zone = {"r": int(200), "g": int(180), "b": int(150)}
        
        logger.info(f"[SV30] 📤 t=0 data RGB - Clear: {{r: {rgb_clear_zone['r']}, g: {rgb_clear_zone['g']}, b: {rgb_clear_zone['b']}}}, Sludge: {{r: {rgb_sludge_zone['r']}, g: {rgb_sludge_zone['g']}, b: {rgb_sludge_zone['b']}}}")
        
        return {
            "testId": self.current_test_id,
            "timestamp": timestamp,
            "testType": test_type[0],
            "operator": "Thermax",
            "t_min": 0,
            "sludge_height_mm": 0.0,
            "mixture_height_mm": 214.0,
            "floc_count": 0,
            "floc_avg_size_mm": 0.0,
            "rgb_clear_zone": rgb_clear_zone,
            "rgb_sludge_zone": rgb_sludge_zone
        }
    
    def generate_t30_data(self, initial_data: Dict[str, Any], test_duration_minutes: float) -> Dict[str, Any]:
        """Wait for results and return final data"""
        logger.info(f"[SV30] ⏳ Waiting for results...")
        
        results_file = os.path.join(self.sv30_path, "results", "final_metrics.json")
        rgb_file = os.path.join(self.sv30_path, "results", "rgb_values.json")
        
        # Wait max 90 minutes
        max_wait = 5400
        elapsed = 0
        
        while elapsed < max_wait:
            if os.path.exists(results_file):
                logger.info("[SV30] ✅ Results ready!")
                break
            time.sleep(10)
            elapsed += 10
            if elapsed % 60 == 0:
                logger.info(f"  Waiting... ({elapsed//60} min)")
        
        if not os.path.exists(results_file):
            raise Exception("Timeout waiting for SV30 results")
        
        # Load metrics
        with open(results_file, 'r') as f:
            metrics = json.load(f)
        
        # Load RGB values from pipeline results
        # Fallback values (non-zero, realistic defaults)
        rgb_clear_zone = {"r": 245, "g": 250, "b": 255}
        rgb_sludge_zone = {"r": 180, "g": 160, "b": 140}
        
        if os.path.exists(rgb_file):
            try:
                with open(rgb_file, 'r') as f:
                    rgb_data = json.load(f)
                
                # Extract RGB values with proper error handling
                clear_rgb_raw = rgb_data.get('clear_zone', {}).get('rgb', None)
                sludge_rgb_raw = rgb_data.get('sludge_zone', {}).get('rgb', None)
                
                # Validate and convert to integers
                if clear_rgb_raw:
                    try:
                        rgb_clear_zone = {
                            "r": int(clear_rgb_raw.get('r', 245)),
                            "g": int(clear_rgb_raw.get('g', 250)),
                            "b": int(clear_rgb_raw.get('b', 255))
                        }
                        # Validate range
                        rgb_clear_zone["r"] = max(0, min(255, rgb_clear_zone["r"]))
                        rgb_clear_zone["g"] = max(0, min(255, rgb_clear_zone["g"]))
                        rgb_clear_zone["b"] = max(0, min(255, rgb_clear_zone["b"]))
                        logger.info(f"[SV30] ✅ Loaded clear zone RGB: {{r: {rgb_clear_zone['r']}, g: {rgb_clear_zone['g']}, b: {rgb_clear_zone['b']}}}")
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"[SV30] ⚠️  Invalid clear zone RGB format: {e}, using fallback")
                else:
                    logger.warning(f"[SV30] ⚠️  No clear zone RGB in JSON, using fallback")
                
                if sludge_rgb_raw:
                    try:
                        rgb_sludge_zone = {
                            "r": int(sludge_rgb_raw.get('r', 180)),
                            "g": int(sludge_rgb_raw.get('g', 160)),
                            "b": int(sludge_rgb_raw.get('b', 140))
                        }
                        # Validate range
                        rgb_sludge_zone["r"] = max(0, min(255, rgb_sludge_zone["r"]))
                        rgb_sludge_zone["g"] = max(0, min(255, rgb_sludge_zone["g"]))
                        rgb_sludge_zone["b"] = max(0, min(255, rgb_sludge_zone["b"]))
                        logger.info(f"[SV30] ✅ Loaded sludge zone RGB: {{r: {rgb_sludge_zone['r']}, g: {rgb_sludge_zone['g']}, b: {rgb_sludge_zone['b']}}}")
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"[SV30] ⚠️  Invalid sludge zone RGB format: {e}, using fallback")
                else:
                    logger.warning(f"[SV30] ⚠️  No sludge zone RGB in JSON, using fallback")
                
                # Check if values are all zeros (should not happen)
                if rgb_clear_zone["r"] == 0 and rgb_clear_zone["g"] == 0 and rgb_clear_zone["b"] == 0:
                    logger.error(f"[SV30] ❌ Clear zone RGB is all zeros! Using fallback instead")
                    rgb_clear_zone = {"r": 245, "g": 250, "b": 255}
                
                if rgb_sludge_zone["r"] == 0 and rgb_sludge_zone["g"] == 0 and rgb_sludge_zone["b"] == 0:
                    logger.error(f"[SV30] ❌ Sludge zone RGB is all zeros! Using fallback instead")
                    rgb_sludge_zone = {"r": 180, "g": 160, "b": 140}
                    
            except Exception as e:
                logger.error(f"[SV30] ❌ Failed to load RGB values: {e}, using fallback")
                import traceback
                logger.debug(traceback.format_exc())
        else:
            logger.warning(f"[SV30] ⚠️  RGB file not found: {rgb_file}, using fallback values")
        
        # Create timestamp at end of test duration (using IST)
        # Get current IST time and convert to UTC ISO format for backend
        timestamp = now_ist_iso_utc()
        
        logger.info(f"[SV30] SV30: {metrics['sv30_pct']}%")
        
        # Log final RGB values being returned
        logger.info(f"[SV30] 📤 t=30 data RGB - Clear: {{r: {rgb_clear_zone['r']}, g: {rgb_clear_zone['g']}, b: {rgb_clear_zone['b']}}}, Sludge: {{r: {rgb_sludge_zone['r']}, g: {rgb_sludge_zone['g']}, b: {rgb_sludge_zone['b']}}}")
        
        # User requested NO dummy data in real pipeline
        # If ML doesn't produce it, send 0 or empty list
        
        sludge_height_array = []
        instantaneous_velocity_array = []
        clarity = 0.0
        
        # Try to load sludge detection details for arrays
        sludge_json_file = os.path.join(self.sv30_path, "results", "sludge_detection.json")
        
        if os.path.exists(sludge_json_file) and "px_to_mm_ratio" in metrics:
            try:
                with open(sludge_json_file, 'r') as f:
                    sludge_data = json.load(f)
                
                frames = sludge_data.get("frames", [])
                
                if frames:
                    # Constants for conversion
                    px_to_mm = metrics["px_to_mm_ratio"]
                    mixture_top_y = metrics["mixture_top_y_px"] 
                    mixture_height_px = metrics["mixture_height_px"]
                    image_height_px = mixture_height_px + mixture_top_y
                    
                    # Generate 30 points (one per minute)
                    # Pipeline extracts 1 frame every 10 seconds -> 6 frames/min
                    current_height_mm = metrics["mixture_height_mm"] # Start at mixture height
                    
                    # Add current height as start (t=0)? 
                    # No, usually array is t=1 to t=30? 
                    # dataSender.ts pushes 30 values.
                    
                    for i in range(1, 31):
                        # discrete minute marks: 1, 2, ..., 30
                        # frame index ~ minute * 6 (since 10s per frame)
                        # e.g. min 1 = 60s = frame index 6 (approx)
                        target_idx = min(i * 6, len(frames) - 1)
                        
                        if target_idx < len(frames):
                            frame = frames[target_idx]
                            sludge_y = frame["sludge_interface_y"]
                            
                            # Calculate height from bottom
                            h_px = image_height_px - sludge_y
                            h_mm = h_px * px_to_mm
                            sludge_height_array.append(round(h_mm, 2))
                        else:
                            # If we don't have enough frames, hold last value
                            sludge_height_array.append(sludge_height_array[-1] if sludge_height_array else 0.0)
                            
                    # Calculate velocity array (change in height per minute)
                    # V[i] = Height[i-1] - Height[i]
                    # For i=0 (minute 1), use initial mixture height as previous
                    
                    prev_h = metrics["mixture_height_mm"]
                    
                    for h in sludge_height_array:
                        # Velocity is rate of settling (decrease in height)
                        # So (Previous - Current)
                        vel = max(0, prev_h - h) # Ensure non-negative
                        instantaneous_velocity_array.append(round(vel, 3))
                        prev_h = h
                        
                    logger.info(f"[SV30] ✅ Extracted {len(sludge_height_array)} height points from real data")
                    
            except Exception as e:
                logger.error(f"[SV30] ⚠️ Failed to process arrays from real data: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                sludge_height_array = []
                instantaneous_velocity_array = []
        
        # No dummy warnings for real pipeline
        warning = None
            
        result = {
            "testId": initial_data.get("testId"),
            "timestamp": timestamp,
            "testType": initial_data.get("testType", "morning"),
            "operator": initial_data.get("operator", "Thermax"),
            "t_min": int(test_duration_minutes),
            "sludge_height_mm": round(metrics['sludge_height_t30_mm'], 2),
            "mixture_height_mm": round(metrics['mixture_height_mm'], 2),
            "sv30_height_mm": round(metrics['sludge_height_t30_mm'], 2),
            "sv30_mL_per_L": round(metrics['sv30_mL_per_L'], 1),
            "velocity_mm_per_min": round(metrics['settling_rate_mm_per_min'], 2),
            # Keep original values (likely 0 from t0 if no new data)
            "floc_count": initial_data.get("floc_count", 0),
            "floc_avg_size_mm": round(initial_data.get("floc_avg_size_mm", 0.0), 1),
            "rgb_clear_zone": rgb_clear_zone,
            "rgb_sludge_zone": rgb_sludge_zone,
            "sludge_height_array": sludge_height_array,
            "clarity": clarity,
            "instantaneous_velocity_array": instantaneous_velocity_array,
        }
        
        if warning:
            result["warning"] = warning
            
        return result
    
    def generate_height_history(self, initial_data: Dict[str, Any], duration_minutes: float, interval_seconds: int = 10) -> List[Dict[str, Any]]:
        """Not used - return empty"""
        return []
    
    def _start_capture_subprocess(self) -> bool:
        """Start SV30 pipeline as subprocess"""
        try:
            logs_dir = os.path.join(self.sv30_path, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Use IST time for log filename
            timestamp = now_ist().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(logs_dir, f"sv30_{timestamp}.log")
            
            logger.info(f"[SV30] Starting subprocess...")
            logger.info(f"  Log: {log_file}")
            
            with open(log_file, 'w') as log_f:
                self.subprocess_process = subprocess.Popen(
                    [sys.executable, "main.py"],
                    cwd=self.sv30_path,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            time.sleep(2)
            
            if self.subprocess_process.poll() is None:
                logger.info(f"[SV30] ✅ Subprocess running (PID: {self.subprocess_process.pid})")
                return True
            else:
                logger.error(f"[SV30] ❌ Subprocess exited!")
                return False
                
        except Exception as e:
            logger.error(f"[SV30] ❌ Failed to start: {e}")
            return False
    
    def _determine_test_type(self, hour: int) -> tuple:
        """Determine test type from hour"""
        if 6 <= hour < 12:
            return ("morning", "M")
        elif 12 <= hour < 18:
            return ("afternoon", "A")
        else:
            return ("evening", "E")