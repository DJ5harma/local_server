import os
import cv2
import json
import numpy as np
from sv30config import (
    UPLOAD_RAW_FOLDER,
    RESULTS_FOLDER,
    RGB_TOP_POINT,
    RGB_BOTTOM_POINT,
    RGB_PATCH_SIZE,
)

RGB_JSON_PATH = os.path.join(RESULTS_FOLDER, "rgb_values.json")

def avg_rgb(img, x, y, n):
    """
    Extract average RGB values from patch around point (x, y)
    
    Args:
        img: BGR image
        x, y: Center coordinates
        n: Patch size (±n pixels)
    
    Returns:
        (R, G, B) tuple
    """
    h, w, _ = img.shape
    
    # Define patch boundaries
    x1, x2 = max(0, x - n), min(w, x + n)
    y1, y2 = max(0, y - n), min(h, y + n)
    
    patch = img[y1:y2, x1:x2]
    
    if patch.size == 0:
        return 0, 0, 0
    
    # Calculate average BGR, convert to RGB
    b, g, r = np.mean(patch.reshape(-1, 3), axis=0)
    
    return int(r), int(g), int(b)

def run_rgb_analysis():
    """
    Extract RGB values from Camera 2 snapshots (t=0 and t=30)
    
    Analyzes two points:
    - TOP: Top of mixture (supernatant clarity point)
    - BOTTOM: Bottom of mixture (sludge color point)
    
    Compares t=0 (start) vs t=30 (end) to see color changes
    
    Returns:
        Dictionary with RGB values at both timepoints
    """
    print(f"\n" + "="*60)
    print("  RGB ANALYSIS")
    print("="*60)
    print(f"Input folder: {UPLOAD_RAW_FOLDER}")
    print(f"Output: {RGB_JSON_PATH}")
    print(f"Top point: {RGB_TOP_POINT}")
    print(f"Bottom point: {RGB_BOTTOM_POINT}")
    print(f"Patch size: ±{RGB_PATCH_SIZE}px")
    print("="*60 + "\n")
    
    # Define expected snapshot filenames
    t0_filename = "cam2_t0.jpg"
    t30_filename = "cam2_t30.jpg"
    
    t0_path = os.path.join(UPLOAD_RAW_FOLDER, t0_filename)
    t30_path = os.path.join(UPLOAD_RAW_FOLDER, t30_filename)
    
    # Check if files exist
    if not os.path.exists(t0_path):
        print(f"[ERROR] t=0 snapshot not found: {t0_path}")
        return None
    
    if not os.path.exists(t30_path):
        print(f"[ERROR] t=30 snapshot not found: {t30_path}")
        return None
    
    # Load images
    img_t0 = cv2.imread(t0_path)
    img_t30 = cv2.imread(t30_path)
    
    if img_t0 is None:
        print(f"[ERROR] Failed to read: {t0_filename}")
        return None
    
    if img_t30 is None:
        print(f"[ERROR] Failed to read: {t30_filename}")
        return None
    
    print(f"[OK] Loaded {t0_filename}: {img_t0.shape}")
    print(f"[OK] Loaded {t30_filename}: {img_t30.shape}\n")
    
    # Extract RGB from t=0
    t0_top_r, t0_top_g, t0_top_b = avg_rgb(img_t0, *RGB_TOP_POINT, RGB_PATCH_SIZE)
    t0_bottom_r, t0_bottom_g, t0_bottom_b = avg_rgb(img_t0, *RGB_BOTTOM_POINT, RGB_PATCH_SIZE)
    
    # Extract RGB from t=30
    t30_top_r, t30_top_g, t30_top_b = avg_rgb(img_t30, *RGB_TOP_POINT, RGB_PATCH_SIZE)
    t30_bottom_r, t30_bottom_g, t30_bottom_b = avg_rgb(img_t30, *RGB_BOTTOM_POINT, RGB_PATCH_SIZE)
    
    # Calculate changes
    top_brightness_change = ((t30_top_r + t30_top_g + t30_top_b) - 
                             (t0_top_r + t0_top_g + t0_top_b)) / 3
    bottom_brightness_change = ((t30_bottom_r + t30_bottom_g + t30_bottom_b) - 
                                (t0_bottom_r + t0_bottom_g + t0_bottom_b)) / 3
    
    results = {
        "snapshots": {
            "t0": t0_filename,
            "t30": t30_filename
        },
        "t0_top_rgb": {
            "r": t0_top_r,
            "g": t0_top_g,
            "b": t0_top_b
        },
        "t0_bottom_rgb": {
            "r": t0_bottom_r,
            "g": t0_bottom_g,
            "b": t0_bottom_b
        },
        "t30_top_rgb": {
            "r": t30_top_r,
            "g": t30_top_g,
            "b": t30_top_b
        },
        "t30_bottom_rgb": {
            "r": t30_bottom_r,
            "g": t30_bottom_g,
            "b": t30_bottom_b
        },
        "changes": {
            "top_brightness_delta": round(top_brightness_change, 2),
            "bottom_brightness_delta": round(bottom_brightness_change, 2)
        }
    }
    
    # Save to JSON
    with open(RGB_JSON_PATH, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"[RGB ANALYSIS] Complete\n")
    print(f"  t=0 TOP:    RGB({t0_top_r}, {t0_top_g}, {t0_top_b})")
    print(f"  t=0 BOTTOM: RGB({t0_bottom_r}, {t0_bottom_g}, {t0_bottom_b})")
    print(f"  t=30 TOP:    RGB({t30_top_r}, {t30_top_g}, {t30_top_b})")
    print(f"  t=30 BOTTOM: RGB({t30_bottom_r}, {t30_bottom_g}, {t30_bottom_b})")
    print(f"\n  Top brightness change: {top_brightness_change:+.2f}")
    print(f"  Bottom brightness change: {bottom_brightness_change:+.2f}")
    print(f"\n  Saved to: {RGB_JSON_PATH}")
    print("="*60 + "\n")
    
    return results

def get_rgb_results():
    """
    Returns RGB values for external systems (dashboard, reports)
    Reads from saved JSON file
    """
    if not os.path.exists(RGB_JSON_PATH):
        print("[WARN] No RGB JSON found")
        return None
    
    try:
        with open(RGB_JSON_PATH, "r") as f:
            data = json.load(f)
        return data
    except:
        print("[ERROR] Failed to read RGB JSON")
        return None

if __name__ == "__main__":
    run_rgb_analysis()
