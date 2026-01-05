import os
import cv2
import json
import numpy as np
from sv30config import (
    GEOMETRY_DEBUG_FOLDER,
    RESULTS_FOLDER,
    MIXTURE_TOP_Y,
    FRAME_INTERVAL_SEC,
    IMG_EXTS,
)

JSON_PATH = os.path.join(RESULTS_FOLDER, "sv30_metrics.json")

def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(IMG_EXTS)

def extract_red_dots_with_x(vis, x_positions):
    """
    Extract red dot positions from geometry visualization
    Returns list of (x, y) tuples for detected interface points
    """
    dots = []
    for x in x_positions:
        col = vis[:, x, :]
        # Find red pixels (R=255, G=0, B=0)
        ys = np.where(
            (col[:, 2] == 255) & (col[:, 1] == 0) & (col[:, 0] == 0)
        )[0]
        if ys.size > 0:
            dots.append((x, int(ys[0])))
    return dots

def get_single_sludge_height(h, dots):
    """
    Calculate sludge height from red dot positions
    
    Strategy:
    - Use 3rd rightmost dot to avoid edge effects
    - Height = image_height - y_coordinate
    
    Returns:
        Sludge height in pixels from bottom
    """
    if not dots or len(dots) < 3:
        return None
    
    # Sort by X position and take 3rd from right
    dots_sorted = sorted(dots, key=lambda d: d[0])
    _, y = dots_sorted[-3]
    
    # Convert Y-coordinate to height from bottom
    return h - y

def append_json(record):
    """
    Append record to JSON file
    Maintains array of frame-by-frame measurements
    """
    data = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r") as f:
                data = json.load(f)
        except:
            pass
    
    data.append(record)
    
    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

def run_stage():
    """
    Calculate SV30 metrics from geometry debug images
    
    Metrics calculated:
    - SV30 (sludge volume as % of total mixture)
    - Instantaneous settling velocity (%/sec)
    - Average settling velocity (%/sec)
    - Sludge height (pixels)
    
    Returns:
        Final metrics dictionary
    """
    print(f"\n[SV30-METRICS] Starting")
    print(f"  Input: {GEOMETRY_DEBUG_FOLDER}")
    print(f"  Output: {JSON_PATH}")
    print(f"  Mixture top Y: {MIXTURE_TOP_Y}")
    print(f"  Frame interval: {FRAME_INTERVAL_SEC}s\n")
    
    frames = sorted(f for f in os.listdir(GEOMETRY_DEBUG_FOLDER) if is_image(f))
    
    if not frames:
        print("[ERROR] No geometry debug frames found")
        return None
    
    first_sludge = None
    prev_sludge = None
    final_metrics = None
    processed_count = 0
    
    for i, fname in enumerate(frames):
        path = os.path.join(GEOMETRY_DEBUG_FOLDER, fname)
        vis = cv2.imread(path)
        
        if vis is None:
            print(f"  [SKIP] Cannot read: {fname}")
            continue
        
        h, w, _ = vis.shape
        
        # Get scan line X positions (same as detect_geometry)
        x_positions = np.linspace(int(w * 0.12), int(w * 0.88), 10).astype(int)
        
        # Extract red dots
        dots = extract_red_dots_with_x(vis, x_positions)
        sludge_h = get_single_sludge_height(h, dots)
        
        if sludge_h is None:
            print(f"  [SKIP] No dots detected: {fname}")
            continue
        
        # Store first measurement
        if first_sludge is None:
            first_sludge = sludge_h
        
        # Calculate mixture height
        mixture_height = h - MIXTURE_TOP_Y
        
        # SV30 = (sludge height / mixture height) × 100
        # This gives the % of mixture that is settled sludge
        sv30_pct = (sludge_h / mixture_height) * 100
        
        # Instantaneous velocity (%/sec)
        if prev_sludge is None:
            inst_velocity = 0.0
        else:
            # Change in sludge % per second
            delta_pct = ((sludge_h - prev_sludge) / mixture_height) * 100
            inst_velocity = delta_pct / FRAME_INTERVAL_SEC
        
        # Time elapsed
        time_elapsed = i * FRAME_INTERVAL_SEC
        
        # Average velocity (%/sec)
        if time_elapsed == 0:
            avg_velocity = 0.0
        else:
            total_delta_pct = ((sludge_h - first_sludge) / mixture_height) * 100
            avg_velocity = total_delta_pct / time_elapsed
        
        prev_sludge = sludge_h
        
        # Store metrics
        record = {
            "frame": fname,
            "time_sec": time_elapsed,
            "sludge_height_px": round(sludge_h, 2),
            "sv30_pct": round(sv30_pct, 3),
            "inst_velocity_pct_per_sec": round(inst_velocity, 6),
            "avg_velocity_pct_per_sec": round(avg_velocity, 6),
        }
        
        append_json(record)
        processed_count += 1
        print(f"  [OK] {fname}: SV30={sv30_pct:.1f}%, V_avg={avg_velocity:.4f} %/s")
        
        # Keep final metrics
        final_metrics = {
            "sv30_pct": round(sv30_pct, 3),
            "avg_velocity": round(avg_velocity, 6),
        }
    
    print(f"\n[SV30-METRICS] Complete")
    print(f"  Processed: {processed_count} frames")
    
    if final_metrics:
        print(f"\n[FINAL RESULTS]")
        print(f"  SV30: {final_metrics['sv30_pct']:.2f}%")
        print(f"  Avg Settling Velocity: {final_metrics['avg_velocity']:.6f} %/sec")
        print(f"  Saved to: {JSON_PATH}\n")
    
    return final_metrics

def get_final_metrics():
    """
    Returns final SV30 metrics for external systems (Modbus, dashboard)
    Reads last record from JSON file
    """
    if not os.path.exists(JSON_PATH):
        print("[WARN] No metrics JSON found")
        return None
    
    try:
        with open(JSON_PATH, "r") as f:
            data = json.load(f)
    except:
        print("[ERROR] Failed to read metrics JSON")
        return None
    
    if not data:
        print("[WARN] Metrics JSON is empty")
        return None
    
    final = data[-1]
    
    return {
        "sv30_pct": final.get("sv30_pct"),
        "avg_velocity": final.get("avg_velocity_pct_per_sec"),
    }

if __name__ == "__main__":
    run_stage()
