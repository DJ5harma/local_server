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
from datetime import datetime
from pathlib import Path

from .data_provider import DataProvider

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
        now = datetime.now()
        test_type = self._determine_test_type(now.hour)
        # Use same test ID format as dummy provider for consistency
        date_str = now.strftime("%Y-%m-%d")
        test_type_code = test_type[1]
        self.current_test_id = f"SV30-{date_str}-001-{test_type_code}"
        
        logger.info(f"[SV30] 🚀 Starting test: {self.current_test_id}")
        
        # Start subprocess
        started = self._start_capture_subprocess()
        
        if not started:
            raise Exception("Failed to start SV30 capture subprocess")
        
        # Ensure timestamp has Z suffix for ISO 8601 UTC format
        timestamp = now.isoformat()
        if not timestamp.endswith('Z'):
            timestamp = timestamp + "Z"
        
        # Use default RGB values (will be updated from pipeline results at t=30)
        rgb_clear_zone = {"r": 255, "g": 255, "b": 255}
        rgb_sludge_zone = {"r": 200, "g": 180, "b": 150}
        
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
        rgb_clear_zone = {"r": 245, "g": 250, "b": 255}  # Fallback
        rgb_sludge_zone = {"r": 180, "g": 160, "b": 140}  # Fallback
        
        if os.path.exists(rgb_file):
            try:
                with open(rgb_file, 'r') as f:
                    rgb_data = json.load(f)
                rgb_clear_zone = rgb_data.get('clear_zone', {}).get('rgb', rgb_clear_zone)
                rgb_sludge_zone = rgb_data.get('sludge_zone', {}).get('rgb', rgb_sludge_zone)
                logger.info(f"[SV30] Loaded RGB values from pipeline results")
            except Exception as e:
                logger.warning(f"[SV30] Failed to load RGB values: {e}, using fallback")
        else:
            logger.warning(f"[SV30] RGB file not found: {rgb_file}, using fallback values")
        
        # Create timestamp at end of test duration
        now = datetime.now()
        timestamp = now.isoformat()
        if not timestamp.endswith('Z'):
            timestamp = timestamp + "Z"
        
        logger.info(f"[SV30] SV30: {metrics['sv30_pct']}%")
        
        return {
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
            "floc_count": initial_data.get("floc_count", 0),
            "floc_avg_size_mm": round(initial_data.get("floc_avg_size_mm", 0.0), 2),
            "rgb_clear_zone": rgb_clear_zone,
            "rgb_sludge_zone": rgb_sludge_zone
        }
    
    def generate_height_history(self, initial_data: Dict[str, Any], duration_minutes: float, interval_seconds: int = 10) -> List[Dict[str, Any]]:
        """Not used - return empty"""
        return []
    
    def _start_capture_subprocess(self) -> bool:
        """Start SV30 pipeline as subprocess"""
        try:
            logs_dir = os.path.join(self.sv30_path, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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