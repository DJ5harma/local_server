"""
Data generator for SV30 tests.
Currently uses dummy data - will be replaced with actual ML model calls later.
"""
import random
import time
from datetime import datetime
from typing import Dict, List, Any
from ..models.types import SludgeData, SludgeHeightEntry


def _determine_test_type(current_hour: int) -> tuple[str, str]:
    """
    Determine test type based on current hour of day.
    
    Args:
        current_hour: Current hour (0-23)
        
    Returns:
        Tuple of (test_type, test_type_code)
        - test_type: "morning", "afternoon", or "evening"
        - test_type_code: "M", "A", or "E"
    """
    # Morning: 6 AM - 11:59 AM (hours 6-11)
    # Afternoon: 12 PM - 5:59 PM (hours 12-17)
    # Evening: 6 PM - 5:59 AM (hours 18-23 or 0-5)
    if 6 <= current_hour < 12:
        return ("morning", "M")
    elif 12 <= current_hour < 18:
        return ("afternoon", "A")
    else:
        return ("evening", "E")


def generate_t0_data() -> Dict[str, Any]:
    """
    Generate initial SludgeData at t=0 (start of test).
    Test type is automatically determined based on current time of day:
    - Morning: 6 AM - 11:59 AM
    - Afternoon: 12 PM - 5:59 PM
    - Evening: 6 PM - 5:59 AM
    
    Returns:
        Dictionary matching SludgeData interface
    """
    # Realistic initial values
    mixture_height = random.uniform(800, 1000)  # mm
    initial_sludge_height = random.uniform(0, 50)  # mm
    
    # Generate RGB values for clear and sludge zones
    rgb_clear_zone = {
        "r": random.randint(240, 255),
        "g": random.randint(245, 255),
        "b": random.randint(250, 255)
    }
    
    rgb_sludge_zone = {
        "r": random.randint(150, 200),
        "g": random.randint(130, 180),
        "b": random.randint(100, 150)
    }
    
    # Generate floc data
    floc_count = random.randint(40, 80)
    floc_avg_size = random.uniform(1.5, 3.5)  # mm
    
    # Determine test type based on current time
    now = datetime.now()
    current_hour = now.hour
    test_type, test_type_code = _determine_test_type(current_hour)
    
    # Create test ID with appropriate type code
    date_str = now.strftime("%Y-%m-%d")
    test_id = f"SV30-{date_str}-001-{test_type_code}"
    
    print(f"🕐 Current hour: {current_hour}, Test type: {test_type} ({test_type_code})")
    
    return {
        "testId": test_id,
        "timestamp": now.isoformat() + "Z",
        "testType": test_type,  # Automatically determined by time of day
        "operator": "Operator",
        "t_min": 0,
        "sludge_height_mm": initial_sludge_height,
        "mixture_height_mm": mixture_height,
        "floc_count": floc_count,
        "floc_avg_size_mm": floc_avg_size,
        "rgb_clear_zone": rgb_clear_zone,
        "rgb_sludge_zone": rgb_sludge_zone,
        "velocity_mm_per_min": 0,  # No velocity at t=0
    }


def generate_t30_data(initial_data: Dict[str, Any], test_duration_minutes: float = 30.0) -> Dict[str, Any]:
    """
    Generate final SludgeData at end of test.
    
    Args:
        initial_data: The t=0 data to base calculations on
        test_duration_minutes: Test duration in minutes (default: 30)
        
    Returns:
        Dictionary matching SludgeData interface with SV30 calculations
    """
    mixture_height = initial_data["mixture_height_mm"]
    initial_sludge_height = initial_data["sludge_height_mm"]
    
    # Simulate settling: sludge height decreases over time
    # Use exponential decay model for realistic settling curve
    # Final height is typically 60-90% of initial (depending on settling)
    settling_factor = random.uniform(0.6, 0.9)
    final_sludge_height = initial_sludge_height * settling_factor
    
    # Calculate SV30 values
    sv30_mL_per_L = (final_sludge_height / mixture_height) * 1000
    sv30_percentage = (final_sludge_height / mixture_height) * 100
    
    # Calculate average velocity (mm per minute)
    velocity_mm_per_min = (initial_sludge_height - final_sludge_height) / test_duration_minutes if test_duration_minutes > 0 else 0
    
    # Create timestamp at end of test duration
    from datetime import timedelta
    initial_timestamp = datetime.fromisoformat(initial_data["timestamp"].replace("Z", "+00:00"))
    final_timestamp = initial_timestamp + timedelta(minutes=test_duration_minutes)
    
    # Update RGB values slightly (clear zone might become clearer)
    rgb_clear_zone = {
        "r": min(255, initial_data["rgb_clear_zone"]["r"] + random.randint(0, 10)),
        "g": min(255, initial_data["rgb_clear_zone"]["g"] + random.randint(0, 10)),
        "b": min(255, initial_data["rgb_clear_zone"]["b"] + random.randint(0, 10))
    }
    
    return {
        "testId": initial_data["testId"],
        "timestamp": final_timestamp.isoformat().replace("+00:00", "Z"),
        "testType": initial_data.get("testType", "morning"),
        "operator": initial_data.get("operator", "Operator"),
        "t_min": int(test_duration_minutes),
        "sludge_height_mm": final_sludge_height,
        "mixture_height_mm": mixture_height,
        "sv30_height_mm": final_sludge_height,
        "sv30_mL_per_L": round(sv30_mL_per_L, 1),
        "velocity_mm_per_min": round(velocity_mm_per_min, 2),
        "floc_count": initial_data["floc_count"],
        "floc_avg_size_mm": initial_data["floc_avg_size_mm"],
        "rgb_clear_zone": rgb_clear_zone,
        "rgb_sludge_zone": initial_data["rgb_sludge_zone"],
    }


def generate_height_history(initial_data: Dict[str, Any], duration_minutes: float = 30.0, interval_seconds: int = 10) -> List[Dict[str, Any]]:
    """
    Generate periodic sludge height measurements during the test.
    Simulates a settling curve with exponential decay.
    
    Args:
        initial_data: The t=0 data
        duration_minutes: Test duration in minutes (default: 30)
        interval_seconds: Measurement interval in seconds (default: 10)
        
    Returns:
        List of SludgeHeightEntry dictionaries
    """
    history = []
    initial_height = initial_data["sludge_height_mm"]
    mixture_height = initial_data["mixture_height_mm"]
    
    # Get final height (use same calculation as t30)
    settling_factor = random.uniform(0.6, 0.9)
    final_height = initial_height * settling_factor
    
    # Generate measurements at intervals
    start_time = datetime.fromisoformat(initial_data["timestamp"].replace("Z", "+00:00"))
    total_seconds = duration_minutes * 60
    # For very short durations, ensure at least 2 measurements (start and end)
    # Also adjust interval if duration is shorter than interval
    if total_seconds < interval_seconds:
        # For durations shorter than interval, use smaller intervals
        adjusted_interval = max(1, int(total_seconds / 2))  # At least 2 measurements
        num_measurements = 2
    else:
        adjusted_interval = interval_seconds
        num_measurements = max(2, int(total_seconds // adjusted_interval) + 1)  # At least start and end
    
    for i in range(num_measurements):
        elapsed_seconds = i * adjusted_interval
        # Ensure last measurement is at the end
        if i == num_measurements - 1:
            elapsed_seconds = total_seconds
        elapsed_minutes = elapsed_seconds / 60.0
        
        # Exponential decay model for settling
        # Progress from initial to final height
        progress = elapsed_minutes / duration_minutes if duration_minutes > 0 else 1.0
        # Use exponential decay: height = initial * (final/initial)^progress
        if final_height > 0:
            current_height = initial_height * ((final_height / initial_height) ** progress)
        else:
            current_height = initial_height * (1 - progress)
        
        # Add some small random variation for realism
        current_height += random.uniform(-2, 2)
        current_height = max(0, min(mixture_height, current_height))  # Clamp to valid range
        
        # Calculate measurement time properly using timedelta
        from datetime import timedelta
        measurement_time = start_time + timedelta(seconds=elapsed_seconds)
        timestamp_ms = int(measurement_time.timestamp() * 1000)
        
        history.append({
            "timestamp": timestamp_ms,
            "height": round(current_height, 2),
            "dateTime": measurement_time.isoformat().replace("+00:00", "Z"),
            "testType": initial_data.get("testType", "morning")
        })
    
    return history

