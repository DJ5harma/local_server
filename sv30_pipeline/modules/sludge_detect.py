"""
Sludge Detection Module

Detects sludge interface and calculates SV30 from binary images.

Algorithm:
1. Use SECOND frame (frame[1]) to detect mixture top
2. Create 10 scan lines centered in image (7px spacing)
3. Top-down scan in top 50% of mixture:
   - Start from mixture_top, scan downward
   - Stop at 50% of mixture height
   - Find first WHITE pixel with 5 consecutive BLACK pixels BELOW it
4. Two-stage outlier rejection
5. Average 6 closest dots
6. Calculate SV30%

Author: Jan 2026
"""

import os
import sys
import cv2
import numpy as np
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sv30config as config

logger = logging.getLogger(__name__)


# Detection parameters
NUM_SCAN_LINES = 10
SCAN_LINE_SPACING = 7  # pixels between lines
BLACK_PIXELS_REQUIRED = 5  # Consecutive black pixels below white pixel
SCAN_DEPTH_PCT = 50  # Scan in top 50% of mixture
OUTLIER_THRESHOLD_EXTREME = 100  # pixels
OUTLIER_THRESHOLD_MODERATE = 30  # pixels


def is_image(f):
    """Check if file is an image"""
    return f.lower().endswith(('.png', '.jpg', '.jpeg'))


def detect_mixture_top(binary_image, search_region=0.6):
    """
    Detect mixture top using brightness gradient (top-down scan).
    
    Args:
        binary_image: Binary image (grayscale)
        search_region: Search in top X% of image
    
    Returns:
        int: Y coordinate of mixture top
    """
    h, w = binary_image.shape
    roi_height = int(h * search_region)
    
    # Calculate average brightness per row
    row_brightness = np.mean(binary_image[:roi_height, :], axis=1)
    
    # Calculate gradient (difference between consecutive rows)
    gradient = np.diff(row_brightness)
    
    # Find biggest negative gradient (bright → dark transition)
    max_drop_idx = np.argmin(gradient)
    mixture_top_y = max_drop_idx + 1
    
    return int(mixture_top_y)


def get_centered_scan_line_positions(image_width):
    """
    Calculate scan line x-positions centered in image with 7px spacing.
    
    Args:
        image_width: Width of image
        
    Returns:
        numpy.ndarray: X-positions for scan lines
    """
    center_x = image_width // 2
    
    # For 10 lines: 5 lines on each side of center
    # Spacing: 7 pixels
    if NUM_SCAN_LINES % 2 == 0:
        # Even number of lines
        half_lines = NUM_SCAN_LINES // 2
        offsets = []
        for i in range(half_lines):
            # Left side: -31.5, -24.5, -17.5, -10.5, -3.5
            offsets.append(-(half_lines - i - 0.5) * SCAN_LINE_SPACING)
        for i in range(half_lines):
            # Right side: 3.5, 10.5, 17.5, 24.5, 31.5
            offsets.append((i + 0.5) * SCAN_LINE_SPACING)
    else:
        # Odd number of lines
        half_lines = NUM_SCAN_LINES // 2
        offsets = [0]  # Center line
        for i in range(1, half_lines + 1):
            offsets.append(-i * SCAN_LINE_SPACING)  # Left
            offsets.append(i * SCAN_LINE_SPACING)   # Right
        offsets.sort()
    
    x_positions = np.array([center_x + offset for offset in offsets], dtype=int)
    
    logger.info(f"  Image center: x = {center_x}")
    logger.info(f"  Scan lines: {NUM_SCAN_LINES} lines, {SCAN_LINE_SPACING}px spacing")
    logger.info(f"  X-positions: {x_positions.tolist()}")
    
    return x_positions


def top_down_scan_in_top_50(binary_image, mixture_top_y, x_positions):
    """
    Top-down scan in top 50% of mixture to detect sludge interface.
    
    Scans from mixture_top downward in top 50% of mixture, looking for:
    - First WHITE pixel that has 5 consecutive BLACK pixels BELOW it
    
    Args:
        binary_image: Binary image (255=clear, 0=sludge)
        mixture_top_y: Y coordinate of mixture top
        x_positions: X positions for scan lines
        
    Returns:
        list: List of detected points [{"x": x, "y": y}, ...]
    """
    h, w = binary_image.shape
    
    # Calculate mixture height
    mixture_height = h - mixture_top_y
    
    # Scan in top 50% of mixture
    scan_depth = int(mixture_height * (SCAN_DEPTH_PCT / 100))
    scan_stop_y = mixture_top_y + scan_depth
    
    logger.info(f"  Mixture height: {mixture_height} px")
    logger.info(f"  Scan depth: {scan_depth} px ({SCAN_DEPTH_PCT}% of mixture)")
    logger.info(f"  Scan range: y={mixture_top_y} to y={scan_stop_y}")
    
    red_dots = []
    
    for x in x_positions:
        # Scan from mixture_top downward to scan_stop_y
        for y in range(mixture_top_y, min(scan_stop_y, h - BLACK_PIXELS_REQUIRED)):
            pixel_value = binary_image[y, x]
            
            # Check if this is a WHITE pixel
            if pixel_value == 255:
                # Check if 5 consecutive BLACK pixels BELOW this white pixel
                has_n_black_below = True
                
                for offset in range(1, BLACK_PIXELS_REQUIRED + 1):
                    if binary_image[y + offset, x] != 0:
                        has_n_black_below = False
                        break
                
                if has_n_black_below:
                    # Found sludge interface!
                    red_dots.append({"x": int(x), "y": int(y)})
                    break  # Found sludge on this line, move to next line
    
    return red_dots


def reject_outliers(red_dots):
    """
    Two-stage outlier rejection.
    
    Stage 1: Remove extreme outliers (>100px from median)
    Stage 2: Remove moderate outliers (>30px from new median)
    
    Args:
        red_dots: List of detected points
        
    Returns:
        tuple: (valid_dots, rejected_dots)
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


def average_6_closest(valid_dots):
    """
    Average 6 closest dots (smart handling for different counts).
    
    Args:
        valid_dots: List of valid dots
        
    Returns:
        tuple: (final_sludge_y, dots_used)
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


def calculate_sv30(mixture_top_y, sludge_y, image_height):
    """
    Calculate SV30 percentage.
    
    Args:
        mixture_top_y: Y coordinate of mixture top
        sludge_y: Y coordinate of sludge interface
        image_height: Total image height
        
    Returns:
        float: SV30 percentage
    """
    sludge_height = sludge_y - mixture_top_y
    mixture_height = image_height - mixture_top_y
    
    if mixture_height <= 0:
        return 0.0
    
    sv30_pct = (sludge_height / mixture_height) * 100
    
    return float(sv30_pct)


def create_debug_image(binary_image, mixture_top_y, scan_stop_y, x_positions, 
                       red_dots, valid_dots, dots_used, final_sludge_y, sv30_pct):
    """
    Create debug visualization.
    
    Returns:
        numpy.ndarray: Color debug image with annotations
    """
    # Convert to color
    debug_img = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    h, w = binary_image.shape
    
    # Draw mixture top line (BLUE)
    cv2.line(debug_img, (0, mixture_top_y), (w, mixture_top_y), (255, 0, 0), 2)
    cv2.putText(debug_img, "Mixture Top", (w - 150, mixture_top_y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # Draw scan stop line (CYAN)
    cv2.line(debug_img, (0, scan_stop_y), (w, scan_stop_y), (255, 255, 0), 1)
    
    # Draw scan lines (GREEN) from mixture_top to scan_stop
    for x in x_positions:
        cv2.line(debug_img, (x, mixture_top_y), (x, scan_stop_y), (0, 255, 0), 1)
    
    # Draw rejected dots (ORANGE)
    rejected_dots = [d for d in red_dots if d not in valid_dots]
    for dot in rejected_dots:
        cv2.circle(debug_img, (dot['x'], dot['y']), 5, (0, 165, 255), -1)
    
    # Draw valid dots (GREEN circles)
    for dot in valid_dots:
        if dot in dots_used:
            # Used in average - larger circle
            cv2.circle(debug_img, (dot['x'], dot['y']), 7, (0, 255, 0), -1)
        else:
            # Valid but not used - smaller circle
            cv2.circle(debug_img, (dot['x'], dot['y']), 5, (0, 255, 0), 2)
    
    # Draw final sludge interface line (RED)
    cv2.line(debug_img, (0, final_sludge_y), (w, final_sludge_y), (0, 0, 255), 2)
    cv2.putText(debug_img, "Sludge Interface", (w - 180, final_sludge_y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Add text overlay
    cv2.putText(debug_img, f"SV30: {sv30_pct:.1f}%", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(debug_img, f"Valid dots: {len(valid_dots)}/{len(red_dots)}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
    cv2.putText(debug_img, f"Dots used: {len(dots_used)}", (10, 85), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
    
    return debug_img


def process_all():
    """
    Process all binary frames to detect sludge and calculate SV30.
    
    Workflow:
    1. Load SECOND frame (frame[1]) to detect mixture top
    2. Get scan line positions (centered, 7px spacing)
    3. Process each frame:
       - Top-down scan in top 50% of mixture
       - Outlier rejection
       - Average 6 closest
       - Calculate SV30
    4. Save results to JSON
    5. Create debug images if DEV_MODE
    """
    logger.info("\n" + "="*70)
    logger.info("  SLUDGE DETECTION (Top-Down in Top 50%)")
    logger.info("="*70)
    logger.info(f"Input: {config.OTSU_BINARY_FOLDER}")
    logger.info(f"Output: {config.RESULTS_FOLDER}/sludge_detection.json")
    logger.info(f"Debug: {config.SLUDGE_DEBUG_FOLDER} (if DEV_MODE)")
    logger.info("="*70 + "\n")
    
    # Get all binary frames
    frames = sorted([f for f in os.listdir(config.OTSU_BINARY_FOLDER) if is_image(f)])
    
    if not frames:
        logger.error("[ERROR] No binary frames found!")
        return None
    
    if len(frames) < 2:
        logger.error("[ERROR] Need at least 2 frames! Only found 1.")
        return None
    
    logger.info(f"Found {len(frames)} frames\n")
    
    # STEP 1: Load SECOND frame (frame[1])
    frame2_name = frames[1]
    frame2_path = os.path.join(config.OTSU_BINARY_FOLDER, frame2_name)
    frame2 = cv2.imread(frame2_path, cv2.IMREAD_GRAYSCALE)
    
    if frame2 is None:
        logger.error(f"[ERROR] Cannot read frame: {frame2_name}")
        return None
    
    h, w = frame2.shape
    logger.info(f"[SETUP] Using SECOND frame: {frame2_name}")
    logger.info(f"  Image size: {w}x{h}")
    
    # STEP 2: Detect mixture top from frame 2
    mixture_top_y = detect_mixture_top(frame2)
    logger.info(f"  Mixture top: y = {mixture_top_y}\n")
    
    # STEP 3: Get scan line positions (centered, 7px spacing)
    x_positions = get_centered_scan_line_positions(w)
    logger.info("")
    
    # Calculate scan stop position for logging
    mixture_height = h - mixture_top_y
    scan_depth = int(mixture_height * (SCAN_DEPTH_PCT / 100))
    scan_stop_y = mixture_top_y + scan_depth
    
    # STEP 4: Process all frames
    logger.info(f"[PROCESSING] Analyzing {len(frames)} frames (top-down scan)...\n")
    
    results = []
    processed = 0
    errors = 0
    
    for i, fname in enumerate(frames):
        src_path = os.path.join(config.OTSU_BINARY_FOLDER, fname)
        binary = cv2.imread(src_path, cv2.IMREAD_GRAYSCALE)
        
        if binary is None:
            logger.error(f"  [ERROR] Cannot read: {fname}")
            errors += 1
            continue
        
        try:
            h, w = binary.shape
            
            # Top-down scan in top 50%
            red_dots = top_down_scan_in_top_50(binary, mixture_top_y, x_positions)
            
            # Outlier rejection
            valid_dots, rejected_dots = reject_outliers(red_dots)
            
            if len(valid_dots) == 0:
                # No valid dots - use mixture top as sludge interface
                final_sludge_y = mixture_top_y
                dots_used = []
                sv30_pct = 0.0
            else:
                # Average 6 closest
                final_sludge_y, dots_used = average_6_closest(valid_dots)
                
                # Calculate SV30
                sv30_pct = calculate_sv30(mixture_top_y, final_sludge_y, h)
            
            # Store result
            result = {
                "filename": fname,
                "frame_index": i,
                "mixture_top_y": int(mixture_top_y),
                "sludge_interface_y": int(final_sludge_y),
                "sv30_pct": float(sv30_pct),
                "total_dots": len(red_dots),
                "valid_dots": len(valid_dots),
                "dots_used": len(dots_used)
            }
            results.append(result)
            
            # Create debug image if DEV_MODE
            if config.DEV_MODE:
                debug_img = create_debug_image(
                    binary, mixture_top_y, scan_stop_y, x_positions, red_dots,
                    valid_dots, dots_used, final_sludge_y, sv30_pct
                )
                debug_path = os.path.join(config.SLUDGE_DEBUG_FOLDER, f"debug_{fname}")
                cv2.imwrite(debug_path, debug_img)
            
            processed += 1
            
            # Progress (only log for first frame to avoid spam about scan range)
            if i == 0:
                pass  # Already logged in function
            elif (i + 1) % 10 == 0:
                logger.info(f"  Processed {i + 1}/{len(frames)} frames...")
            
        except Exception as e:
            errors += 1
            logger.error(f"  [ERROR] {fname}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results to JSON
    results_json = {
        "detection_method": "otsu_topdown_scan_top50",
        "scan_direction": "top_to_bottom",
        "scan_depth_pct": SCAN_DEPTH_PCT,
        "mixture_top_y": int(mixture_top_y),
        "scan_line_positions": x_positions.tolist(),
        "total_frames": len(frames),
        "processed_frames": processed,
        "error_frames": errors,
        "frames": results
    }
    
    json_path = os.path.join(config.RESULTS_FOLDER, "sludge_detection.json")
    with open(json_path, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    # Summary
    if results:
        sv30_values = [r['sv30_pct'] for r in results]
        
        logger.info("\n" + "="*70)
        logger.info("  SLUDGE DETECTION COMPLETE")
        logger.info("="*70)
        logger.info(f"Processed: {processed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"\nSV30 Statistics:")
        logger.info(f"  Range: {min(sv30_values):.2f}% - {max(sv30_values):.2f}%")
        logger.info(f"  Average: {np.mean(sv30_values):.2f}%")
        logger.info(f"  Final: {sv30_values[-1]:.2f}%")
        logger.info(f"\nResults: {json_path}")
        if config.DEV_MODE:
            logger.info(f"Debug images: {config.SLUDGE_DEBUG_FOLDER}")
        logger.info("="*70 + "\n")
    else:
        logger.error("\n[ERROR] No frames processed successfully")
    
    return results


if __name__ == "__main__":
    # Test sludge detection
    results = process_all()
    if results:
        print(f"✅ Processed {len(results)} frames successfully!")
    else:
        print("❌ Sludge detection failed!")
        sys.exit(1)