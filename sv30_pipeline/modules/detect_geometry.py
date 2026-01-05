import os
import cv2
import numpy as np
from sv30config import (
    SLUDGE_DEBUG_FOLDER,
    GEOMETRY_DEBUG_FOLDER,
    MIXTURE_TOP_Y,
    SCAN_OFFSET,
    SCAN_BOTTOM_IGNORE,
    IMG_EXTS,
)

def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(IMG_EXTS)

def run_batch():
    """
    Detect sludge interface height across frame width
    
    Process:
    1. Draw 10 vertical green scan lines across beaker
    2. For each line, scan bottom-up
    3. Find first transition from sludge (255) to liquid (0)
    4. Mark with red dot
    5. Ignore bottom region (SCAN_BOTTOM_IGNORE) to avoid false positives
    6. Ignore transitions too close to mixture top (SCAN_OFFSET)
    
    Output:
        Visualization images with green scan lines and red interface dots
    """
    print(f"\n[GEOMETRY] Starting")
    print(f"  Input: {SLUDGE_DEBUG_FOLDER}")
    print(f"  Output: {GEOMETRY_DEBUG_FOLDER}")
    print(f"  Mixture top Y: {MIXTURE_TOP_Y}")
    print(f"  Scan offset: {SCAN_OFFSET}px (ignore near top)")
    print(f"  Bottom ignore: {SCAN_BOTTOM_IGNORE}px\n")
    
    frames = sorted(f for f in os.listdir(SLUDGE_DEBUG_FOLDER) if is_image(f))
    
    if not frames:
        print("[ERROR] No sludge mask files found")
        return
    
    processed_count = 0
    error_count = 0
    
    for fname in frames:
        mask_path = os.path.join(SLUDGE_DEBUG_FOLDER, fname)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        
        if mask is None:
            print(f"  [ERROR] Cannot read: {fname}")
            error_count += 1
            continue
        
        try:
            h, w = mask.shape
            
            # Create color visualization
            vis = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            
            # Define mixture top and bottom
            mix_y = int(np.clip(MIXTURE_TOP_Y, 1, h - 2))
            bottom_y = h - 1
            
            # Create 10 vertical scan lines across beaker width
            # Positioned from 12% to 88% of width to avoid edges
            x_positions = np.linspace(int(w * 0.12), int(w * 0.88), 10).astype(int)
            
            for x in x_positions:
                # Draw green scan line
                cv2.line(vis, (x, mix_y), (x, bottom_y), (0, 255, 0), 2)
                
                # Bottom-up scan for sludge-to-liquid transition
                last_is_sludge = False
                red_dot_y = None
                
                # Start scan from (bottom - SCAN_BOTTOM_IGNORE)
                scan_start = bottom_y - SCAN_BOTTOM_IGNORE
                
                for y in range(scan_start, mix_y - 1, -1):
                    pixel = mask[y, x]
                    
                    if pixel == 255:  # Sludge pixel
                        last_is_sludge = True
                        continue
                    
                    if pixel == 0 and last_is_sludge:  # Transition found
                        # Ignore transitions too close to mixture top
                        if (y - mix_y) < SCAN_OFFSET:
                            continue
                        
                        red_dot_y = y
                        break
                
                # Mark interface with red dot
                if red_dot_y is not None:
                    cv2.circle(vis, (x, red_dot_y), 6, (0, 0, 255), -1)
            
            # Save visualization
            out_name = os.path.splitext(fname)[0].replace("_mask", "") + "_geometry.png"
            out_path = os.path.join(GEOMETRY_DEBUG_FOLDER, out_name)
            cv2.imwrite(out_path, vis)
            
            processed_count += 1
            print(f"  [OK] {fname} → {out_name}")
        
        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {fname}: {e}")
    
    print(f"\n[GEOMETRY] Complete")
    print(f"  Processed: {processed_count}")
    print(f"  Errors: {error_count}\n")

if __name__ == "__main__":
    run_batch()
