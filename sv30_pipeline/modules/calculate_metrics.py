"""
Calculate Final Metrics Module

CORRECT Calculations:
- Sludge height = image_bottom - sludge_interface_y (NOT interface - top!)
- SV30% = (sludge_height_t30 / mixture_height_t0) × 100

Author: Jan 2026
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)

# Constants
BEAKER_HEIGHT_MM = 214.0  # Standard beaker height (for pixel conversion)
TEST_DURATION_MIN = 35.0  # Test duration in minutes


def calculate_metrics():
    """
    Calculate final metrics from sludge detection results.
    
    Returns:
        dict: Final metrics with SV30%, heights, settling rate
    """
    logger.info("\n" + "="*70)
    logger.info("  CALCULATE FINAL METRICS")
    logger.info("="*70)
    
    # Load sludge detection results
    sludge_json_path = os.path.join(config.RESULTS_FOLDER, "sludge_detection.json")
    
    if not os.path.exists(sludge_json_path):
        logger.error(f"[ERROR] Sludge detection results not found: {sludge_json_path}")
        return None
    
    with open(sludge_json_path, 'r') as f:
        sludge_data = json.load(f)
    
    # Get data
    mixture_top_y = sludge_data['mixture_top_y']
    frames = sludge_data['frames']
    
    if not frames:
        logger.error("[ERROR] No frame data in sludge_detection.json")
        return None
    
    # Get first frame (t=0) and last frame (t=30)
    first_frame = frames[0]
    last_frame = frames[-1]
    
    # Get image dimensions
    first_binary_file = first_frame['filename']
    first_binary_path = os.path.join(config.OTSU_BINARY_FOLDER, first_binary_file)
    
    import cv2
    img = cv2.imread(first_binary_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.error(f"[ERROR] Cannot read image: {first_binary_path}")
        return None
    
    image_height_px = img.shape[0]
    
    # PIXEL TO MM CONVERSION
    px_to_mm = BEAKER_HEIGHT_MM / image_height_px
    
    logger.info(f"Pixel to MM conversion:")
    logger.info(f"  Image height: {image_height_px} px")
    logger.info(f"  Beaker reference: {BEAKER_HEIGHT_MM} mm")
    logger.info(f"  Conversion ratio: {px_to_mm:.6f} mm/px\n")
    
    # MIXTURE HEIGHT (from t=0 image)
    mixture_height_px = image_height_px - mixture_top_y
    mixture_height_mm = mixture_height_px * px_to_mm
    
    logger.info(f"Mixture at t=0:")
    logger.info(f"  Mixture top: {mixture_top_y} px")
    logger.info(f"  Image bottom: {image_height_px} px")
    logger.info(f"  Mixture height: {mixture_height_px} px = {mixture_height_mm:.2f} mm\n")
    
    # t=0: At start, sludge = entire mixture (nothing settled yet)
    t0_sludge_height_mm = mixture_height_mm
    
    # t=30: SETTLED SLUDGE
    # Sludge interface Y tells us where sludge STARTS
    # So sludge height = distance from interface to bottom
    t30_sludge_interface_y = last_frame['sludge_interface_y']
    t30_sludge_height_px = image_height_px - t30_sludge_interface_y  # FIXED!
    t30_sludge_height_mm = t30_sludge_height_px * px_to_mm
    
    # Clear liquid height (for reference)
    clear_liquid_height_px = t30_sludge_interface_y - mixture_top_y
    clear_liquid_height_mm = clear_liquid_height_px * px_to_mm
    
    logger.info(f"Settled state at t=30:")
    logger.info(f"  Sludge interface: {t30_sludge_interface_y} px")
    logger.info(f"  Clear liquid: {clear_liquid_height_px} px = {clear_liquid_height_mm:.2f} mm")
    logger.info(f"  Sludge height: {t30_sludge_height_px} px = {t30_sludge_height_mm:.2f} mm\n")
    
    # CALCULATE SV30
    # SV30% = (remaining sludge at t=30 / initial mixture at t=0) × 100
    sv30_pct = (t30_sludge_height_mm / mixture_height_mm) * 100
    
    # For mL/L: multiply by 10
    sv30_mL_per_L = sv30_pct * 10
    
    # CALCULATE SETTLING RATE
    settling_rate_mm_per_min = clear_liquid_height_mm / TEST_DURATION_MIN
    
    # Generate test ID
    from datetime import datetime
    test_id = f"SV30-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Build final metrics
    metrics = {
        "test_id": test_id,
        "test_duration_min": TEST_DURATION_MIN,
        
        # Heights (in mm)
        "mixture_height_mm": round(mixture_height_mm, 2),
        "sludge_height_t0_mm": round(t0_sludge_height_mm, 2),
        "sludge_height_t30_mm": round(t30_sludge_height_mm, 2),
        
        # SV30
        "sv30_pct": round(sv30_pct, 2),
        "sv30_mL_per_L": round(sv30_mL_per_L, 2),
        
        # Settling rate
        "settling_rate_mm_per_min": round(settling_rate_mm_per_min, 4),
        
        # Pixel info (for debugging)
        "px_to_mm_ratio": round(px_to_mm, 6),
        "mixture_top_y_px": mixture_top_y,
        "mixture_height_px": mixture_height_px,
        "sludge_interface_t30_y_px": t30_sludge_interface_y,
        "sludge_height_t30_px": t30_sludge_height_px,
        
        # Frame info
        "total_frames_analyzed": len(frames),
        "first_frame": first_frame['filename'],
        "last_frame": last_frame['filename']
    }
    
    # Save to JSON
    metrics_path = os.path.join(config.RESULTS_FOLDER, "final_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Print summary
    logger.info("="*70)
    logger.info("  FINAL METRICS")
    logger.info("="*70)
    logger.info(f"Test Duration: {TEST_DURATION_MIN} minutes")
    logger.info(f"\nHeights:")
    logger.info(f"  Mixture (t=0):      {mixture_height_mm:.2f} mm")
    logger.info(f"  Sludge (t=30):      {t30_sludge_height_mm:.2f} mm")
    logger.info(f"  Clear liquid (t=30): {clear_liquid_height_mm:.2f} mm")
    logger.info(f"\nResults:")
    logger.info(f"  SV30: {sv30_pct:.2f}% ({sv30_mL_per_L:.2f} mL/L)")
    logger.info(f"  Settling rate: {settling_rate_mm_per_min:.4f} mm/min")
    logger.info(f"\nSaved: {metrics_path}")
    logger.info("="*70 + "\n")
    
    return metrics


if __name__ == "__main__":
    # Test metrics calculation
    metrics = calculate_metrics()
    if metrics:
        print(f"✅ Metrics calculated successfully!")
        print(f"   SV30: {metrics['sv30_pct']}%")
        print(f"   Mixture: {metrics['mixture_height_mm']}mm")
        print(f"   Sludge: {metrics['sludge_height_t30_mm']}mm")
    else:
        print("❌ Metrics calculation failed!")
        sys.exit(1)