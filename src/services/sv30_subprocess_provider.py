"""SV30 Subprocess Provider - Runs SV30 as separate process"""
from typing import Dict, Any, List
from datetime import datetime
import subprocess, json, os, time, logging

logger = logging.getLogger(__name__)

class SV30SubprocessProvider:
    def __init__(self, sv30_path="/home/recomputer/Desktop/sv30"):
        self.sv30_path = sv30_path
        self.current_test_id = None
        logger.info(f"[SV30 Provider] Init: {sv30_path}")
    
    def generate_t0_data(self) -> Dict[str, Any]:
        now = datetime.now()
        test_type = self._determine_test_type(now.hour)
        self.current_test_id = f"SV30-{now.strftime('%Y-%m-%d-%H%M%S')}-{test_type[1]}"
        return {
            "testId": self.current_test_id, "timestamp": now.isoformat(),
            "testType": test_type[0], "sludge_height_mm": 0.0,
            "mixture_height_mm": 214.0, "floc_count": 0,
            "floc_avg_size_mm": 0.0, "t_min": 0,
            "rgb_clear_zone": {"r": 255, "g": 255, "b": 255},
            "rgb_sludge_zone": {"r": 200, "g": 180, "b": 150}
        }
    
    def start_test_capture(self) -> bool:
        try:
            os.makedirs(f"{self.sv30_path}/logs", exist_ok=True)
            log_file = f"{self.sv30_path}/logs/sv30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(log_file, 'w') as f:
                subprocess.Popen(["/usr/bin/python3", "main.py"], cwd=self.sv30_path, 
                               stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
            logger.info(f"✅ SV30 started, log: {log_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Start failed: {e}")
            return False
    
    def generate_t30_data(self, initial_data: Dict, test_duration_minutes: float) -> Dict[str, Any]:
        results_file = f"{self.sv30_path}/results/final_metrics.json"
        for _ in range(540):  # Wait 90 min max
            if os.path.exists(results_file):
                break
            time.sleep(10)
        
        with open(results_file) as f:
            results = json.load(f)
        
        return {
            "testId": initial_data["testId"], "timestamp": datetime.now().isoformat(),
            "testType": initial_data["testType"],
            "sludge_height_mm": results.get("sludge_height_mm", 0),
            "mixture_height_mm": 214.0,
            "sv30_mL_per_L": results.get("sv30_pct", 0) * 10,
            "velocity_mm_per_min": results.get("avg_velocity", 0),
            "t_min": int(test_duration_minutes)
        }
    
    def generate_height_history(self, *args) -> List:
        return []
    
    def _determine_test_type(self, hour: int) -> tuple:
        if 6 <= hour < 12: return ("morning", "A")
        elif 12 <= hour < 18: return ("afternoon", "E")
        else: return ("evening", "E")
