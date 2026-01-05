"""
SV30 Sludge Detection - New Algorithm (v2.0)

Three-step detection process:
  1. Detect mixture top using gradient method (first frame only)
  2. Apply Otsu masking (WHITE=clear, BLACK=sludge)
  3. Top-down scan with 10 green lines to find sludge interface
  4. Outlier rejection + average 6 closest dots
  5. Calculate SV30%

Author: Updated Dec 2024
"""

import os
import cv2
import numpy as np
import json
from sv30config import (
    GRAY_MASKED_FOLDER,
    COLOR_MASKED_FOLDER,
    SLUDGE_DEBUG_FOLDER,
    RESULTS_FOLDER,
    IMG_EXTS,
    DEV_MODE,
    # New parameters
    MIN_SLUDGE_DISTANCE_PX,
    MAX_SEARCH_DEPTH_PCT,
    NUM_SCAN_LINES,
    BLACK_PIXELS_REQUIRED,
    OUTLIER_THRESHOLD_EXTREME,
    OUTLIER_THRESHOLD_MODERATE,
)

def is_image(fname):
    """Check if file is an image"""
    return fname.lower().endswith(IMG_EXTS)

# ============================================================================
# STEP 1: MIXTURE TOP DETECTION
# ============================================================================
def detect_mixture_top(image, search_region=0.6):
    """
    Detect mixture top using brightness gradient (top-down scan)
    
    Args:
        image: Grayscale image
        search_region: Search in top X% of image
    
    Returns:
        mixture_top_y: Y coordinate of mixture top
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    h, w = gray.shape
    roi_height = int(h * search_region)
    
    # Calculate average brightness per row
    row_brightness = np.mean(gray[:roi_height, :], axis=1)
    
    # Calculate gradient
    gradient = np.diff(row_brightness)
    
    # Find biggest negative gradient (bright → dark)
    max_drop_idx = np.argmin(gradient)
    mixture_top_y = max_drop_idx + 1
    
    return mixture_top_y

# ============================================================================
# STEP 2: OTSU MASKING
# ============================================================================
def apply_otsu_mask(image):
    """
    Apply Otsu's automatic threshold
    WHITE = clear liquid, BLACK = sludge
    
    Args:
        image: Grayscale image
    
    Returns:
        binary_mask: Binary mask (255=clear, 0=sludge)
        threshold_value: Otsu threshold value
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Otsu's method
    threshold_value, binary_mask = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    
    return binary_mask, threshold_value

# ============================================================================
# STEP 3: TOP-DOWN SCAN WITH GREEN LINES
# ============================================================================
def top_down_scan(binary_mask, mixture_top_y, num_lines=10):
    """
    Top-down scan on green lines to detect sludge interface
    
    Args:
        binary_mask: Binary mask from Otsu
        mixture_top_y: Y coordinate of mixture top
        num_lines: Number of scan lines
    
    Returns:
        red_dots: List of detected interface points
    """
    h, w = binary_mask.shape
    
    # Constraints
    max_search_y = int(h * (MAX_SEARCH_DEPTH_PCT / 100))
    min_sludge_y = mixture_top_y + MIN_SLUDGE_DISTANCE_PX
    
    # Calculate X positions for scan lines (evenly spaced)
    x_positions = np.linspace(0, w-1, num_lines, dtype=int)
    
    red_dots = []
    
    for i, x in enumerate(x_positions):
        # Skip edge lines (beaker edges have reflections)
        is_edge_line = (i == 0 or i == num_lines - 1)
        if is_edge_line:
            continue
        
        # Scan from min_sludge_y downward
        sludge_y = None
        
        for y in range(min_sludge_y, min(max_search_y, h)):
            pixel_value = binary_mask[y, x]
            
            # Check if this is a BLACK pixel (start of sludge)
            if pixel_value == 0:
                # Check if there are N consecutive BLACK pixels
                has_n_black = True
                
                if y + BLACK_PIXELS_REQUIRED < h:
                    for offset in range(BLACK_PIXELS_REQUIRED):
                        if binary_mask[y + offset, x] != 0:
                            has_n_black = False
                            break
                else:
                    has_n_black = False
                
                if has_n_black:
                    sludge_y = y
                    red_dots.append({
                        'x': int(x),
                        'y': int(y),
                        'line_num': i + 1
                    })
                    break
    
    return red_dots

# ============================================================================
# STEP 4: OUTLIER REJECTION
# ============================================================================
def reject_outliers(red_dots):
    """
    Two-stage outlier rejection
    
    Stage 1: Remove extreme outliers (>100px from median)
    Stage 2: Remove moderate outliers (>threshold from new median)
    
    Args:
        red_dots: List of detected dots
    
    Returns:
        valid_dots: List of valid dots after outlier rejection
        rejected_dots: List of rejected dots
    """
    if len(red_dots) == 0:
        return [], []
    
    # Get all Y positions
    y_positions = [dot['y'] for dot in red_dots]
    median_y = np.median(y_positions)
    
    # STAGE 1: Remove extreme outliers
    stage1_valid = []
    stage1_rejected = []
    
    for dot in red_dots:
        distance = abs(dot['y'] - median_y)
        if distance <= OUTLIER_THRESHOLD_EXTREME:
            stage1_valid.append(dot)
        else:
            stage1_rejected.append(dot)
    
    if len(stage1_valid) == 0:
        return [], red_dots
    
    # Recalculate median
    stage1_y_positions = [dot['y'] for dot in stage1_valid]
    new_median_y = np.median(stage1_y_positions)
    
    # STAGE 2: Remove moderate outliers
    final_valid = []
    stage2_rejected = []
    
    for dot in stage1_valid:
        distance = abs(dot['y'] - new_median_y)
        if distance <= OUTLIER_THRESHOLD_MODERATE:
            final_valid.append(dot)
        else:
            stage2_rejected.append(dot)
    
    all_rejected = stage1_rejected + stage2_rejected
    
    return final_valid, all_rejected

# ============================================================================
# STEP 5: AVERAGE 6 CLOSEST DOTS
# ============================================================================
def average_6_closest(valid_dots):
    """
    Average 6 closest dots (smart handling for different counts)
    
    Args:
        valid_dots: List of valid dots
    
    Returns:
        final_sludge_y: Final sludge interface Y coordinate
        dots_used: List of dots used for averaging
    """
    n_dots = len(valid_dots)
    
    if n_dots < 6:
        dots_to_average = valid_dots
    elif n_dots == 6:
        dots_to_average = valid_dots
    elif n_dots == 7:
        # Remove 1 most extreme
        sorted_dots = sorted(valid_dots, key=lambda d: d['y'])
        median_y = np.median([d['y'] for d in sorted_dots])
        dist_top = abs(sorted_dots[0]['y'] - median_y)
        dist_bottom = abs(sorted_dots[-1]['y'] - median_y)
        
        if dist_top > dist_bottom:
            dots_to_average = sorted_dots[1:]
        else:
            dots_to_average = sorted_dots[:-1]
    elif n_dots == 8:
        # Remove 1 from each end
        sorted_dots = sorted(valid_dots, key=lambda d: d['y'])
        dots_to_average = sorted_dots[1:-1]
    else:  # 9+ dots
        # Remove 2 from each end
        sorted_dots = sorted(valid_dots, key=lambda d: d['y'])
        dots_to_average = sorted_dots[2:-2]
    
    # Calculate average
    y_positions = [dot['y'] for dot in dots_to_average]
    final_sludge_y = int(np.mean(y_positions))
    
    return final_sludge_y, dots_to_average

# ============================================================================
# STEP 6: CALCULATE SV30
# ============================================================================
def calculate_sv30(mixture_top_y, sludge_y, image_height):
    """
    Calculate SV30 percentage
    
    Args:
        mixture_top_y: Mixture top Y coordinate
        sludge_y: Sludge interface Y coordinate
        image_height: Total image height
    
    Returns:
        sv30_pct: SV30 percentage
    """
    sludge_height = sludge_y - mixture_top_y
    total_height = image_height - mixture_top_y
    sv30_pct = (sludge_height / total_height * 100) if total_height > 0 else 0
    return sv30_pct

# ============================================================================
# PROCESS SINGLE FRAME
# ============================================================================
def process_frame(image, mixture_top_y):
    """
    Process single frame with new detection algorithm
    
    Args:
        image: Grayscale masked image
        mixture_top_y: Mixture top Y coordinate (from first frame)
    
    Returns:
        results: Dictionary with detection results
    """
    h, w = image.shape
    
    # Step 2: Apply Otsu mask
    binary_mask, threshold = apply_otsu_mask(image)
    
    # Step 3: Top-down scan
    red_dots = top_down_scan(binary_mask, mixture_top_y, NUM_SCAN_LINES)
    
    # Step 4: Reject outliers
    valid_dots, rejected_dots = reject_outliers(red_dots)
    
    if len(valid_dots) == 0:
        # No valid dots - return mixture top as sludge interface
        return {
            'mixture_top_y': mixture_top_y,
            'sludge_interface_y': mixture_top_y,
            'sv30_pct': 0.0,
            'valid_dots': 0,
            'total_dots': len(red_dots),
            'dots_used': 0,
            'method': 'no_valid_dots'
        }
    
    # Step 5: Average 6 closest
    final_sludge_y, dots_used = average_6_closest(valid_dots)
    
    # Step 6: Calculate SV30
    sv30_pct = calculate_sv30(mixture_top_y, final_sludge_y, h)
    
    return {
        'mixture_top_y': mixture_top_y,
        'sludge_interface_y': final_sludge_y,
        'sv30_pct': sv30_pct,
        'valid_dots': len(valid_dots),
        'total_dots': len(red_dots),
        'dots_used': len(dots_used),
        'threshold': float(threshold),
        'method': 'otsu_topdown_scan'
    }

# ============================================================================
# BATCH PROCESSING
# ============================================================================
def run_batch():
    """
    Process all frames with new detection algorithm
    
    Workflow:
      1. Detect mixture top from first frame
      2. Process all frames using that mixture_top_y
      3. Save results to JSON
    """
    print(f"\n" + "="*60)
    print("  SLUDGE DETECTION (v2.0 - New Algorithm)")
    print("="*60)
    print(f"Input: {GRAY_MASKED_FOLDER}")
    print(f"Output: {SLUDGE_DEBUG_FOLDER}")
    print(f"Method: Otsu + Top-Down Scan + Outlier Rejection")
    print(f"Mode: {'DEV' if DEV_MODE else 'PROD (delete masked)'}")
    print("="*60 + "\n")
    
    frames = sorted(f for f in os.listdir(GRAY_MASKED_FOLDER) if is_image(f))
    
    if not frames:
        print("[ERROR] No grayscale masked frames found")
        return
    
    # STEP 1: Detect mixture top from first frame
    first_frame_path = os.path.join(GRAY_MASKED_FOLDER, frames[0])
    first_frame = cv2.imread(first_frame_path, cv2.IMREAD_GRAYSCALE)
    
    if first_frame is None:
        print(f"[ERROR] Cannot read first frame: {frames[0]}")
        return
    
    mixture_top_y = detect_mixture_top(first_frame)
    
    print(f"[STEP 1] Mixture Top Detection:")
    print(f"  First frame: {frames[0]}")
    print(f"  Mixture top at Y = {mixture_top_y} pixels\n")
    
    # Process all frames
    results = []
    processed_count = 0
    error_count = 0
    
    print(f"[STEP 2] Processing {len(frames)} frames...\n")
    
    for idx, fname in enumerate(frames):
        src = os.path.join(GRAY_MASKED_FOLDER, fname)
        gray = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
        
        if gray is None:
            print(f"  [ERROR] Cannot read: {fname}")
            error_count += 1
            continue
        
        try:
            result = process_frame(gray, mixture_top_y)
            result['filename'] = fname
            result['frame_index'] = idx
            results.append(result)
            
            processed_count += 1
            
            if processed_count % 30 == 0:
                print(f"  [PROGRESS] {processed_count}/{len(frames)} frames processed...")
            
            # PRODUCTION MODE: Delete masked files
            if not DEV_MODE:
                try:
                    os.remove(src)
                except Exception as e:
                    print(f"  [WARN] Could not delete {fname}: {e}")
                
                # Delete corresponding color masked
                color_src = os.path.join(COLOR_MASKED_FOLDER, fname)
                if os.path.exists(color_src):
                    try:
                        os.remove(color_src)
                    except Exception as e:
                        print(f"  [WARN] Could not delete color {fname}: {e}")
        
        except Exception as e:
            error_count += 1
            print(f"  [ERROR] {fname}: {e}")
    
    # Save results to JSON
    results_json = {
        'detection_method': 'otsu_topdown_scan_v2',
        'mixture_top_y': int(mixture_top_y),
        'total_frames': len(frames),
        'processed_frames': processed_count,
        'error_frames': error_count,
        'parameters': {
            'min_sludge_distance_px': MIN_SLUDGE_DISTANCE_PX,
            'max_search_depth_pct': MAX_SEARCH_DEPTH_PCT,
            'num_scan_lines': NUM_SCAN_LINES,
            'black_pixels_required': BLACK_PIXELS_REQUIRED,
            'outlier_threshold_extreme': OUTLIER_THRESHOLD_EXTREME,
            'outlier_threshold_moderate': OUTLIER_THRESHOLD_MODERATE,
        },
        'frames': results
    }
    
    json_path = os.path.join(RESULTS_FOLDER, 'sludge_detection_v2.json')
    with open(json_path, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    # Print summary
    if results:
        sv30_values = [r['sv30_pct'] for r in results]
        
        print(f"\n" + "="*60)
        print("  SLUDGE DETECTION COMPLETE")
        print("="*60)
        print(f"Processed: {processed_count}")
        print(f"Errors: {error_count}")
        print(f"\nSV30 Statistics:")
        print(f"  Range: {min(sv30_values):.2f}% - {max(sv30_values):.2f}%")
        print(f"  Average: {np.mean(sv30_values):.2f}%")
        print(f"  Final: {sv30_values[-1]:.2f}%")
        print(f"\nResults saved: {json_path}")
        print("="*60 + "\n")
    else:
        print(f"\n[ERROR] No frames processed successfully")

if __name__ == "__main__":
    run_batch()
