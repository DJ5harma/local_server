"""
Dummy data provider implementation for SV30 tests.

This module provides a dummy implementation of the DataProvider interface
for testing and development. It can be easily replaced with an ML model
implementation by creating a new class that implements DataProvider.
"""
import random
import logging
from datetime import timedelta, timezone
from typing import Dict, List, Any

from .data_provider import DataProvider
from ..exceptions import DataGenerationError
from ..utils.dateUtils import now_ist, now_ist_iso_utc, parse_iso_to_ist, add_minutes_ist, format_date_ist
from ..constants import (
    MORNING_START_HOUR,
    MORNING_END_HOUR,
    AFTERNOON_START_HOUR,
    AFTERNOON_END_HOUR,
    TEST_TYPE_MORNING,
    TEST_TYPE_AFTERNOON,
    TEST_TYPE_EVENING,
)

logger = logging.getLogger(__name__)


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
    if MORNING_START_HOUR <= current_hour < MORNING_END_HOUR:
        return ("morning", TEST_TYPE_MORNING)
    elif AFTERNOON_START_HOUR <= current_hour < AFTERNOON_END_HOUR:
        return ("afternoon", TEST_TYPE_AFTERNOON)
    else:
        return ("evening", TEST_TYPE_EVENING)


class DummyDataProvider(DataProvider):
    """
    Dummy data provider that generates realistic test data.
    
    This implementation uses random values within realistic ranges
    to simulate SV30 test measurements. It can be easily replaced
    with an ML model implementation.
    """
    
    def generate_t0_data(self) -> Dict[str, Any]:
        """
        Generate initial SludgeData at t=0 (start of test).
        Test type is automatically determined based on current time of day.
        
        Returns:
            Dictionary matching SludgeData interface
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
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
            
            # Determine test type based on current IST time
            now = now_ist()
            current_hour = now.hour
            test_type, test_type_code = _determine_test_type(current_hour)
            
            # Create test ID with appropriate type code (using IST date)
            date_str = format_date_ist(now)
            test_id = f"SV30-{date_str}-001-{test_type_code}"
            
            logger.info(f"Generated t=0 data: hour={current_hour} IST, test_type={test_type} ({test_type_code})")
            
            # Get timestamp in UTC format (for backend compatibility)
            # The time represents IST moment but formatted as UTC ISO string
            timestamp = now_ist_iso_utc()
            
            return {
                "testId": test_id,
                "timestamp": timestamp,
                "testType": test_type,
                "operator": "Operator",
                "t_min": 0,
                "sludge_height_mm": round(initial_sludge_height, 2),
                "mixture_height_mm": round(mixture_height, 2),
                "floc_count": floc_count,
                "floc_avg_size_mm": round(floc_avg_size, 2),
                "rgb_clear_zone": rgb_clear_zone,
                "rgb_sludge_zone": rgb_sludge_zone,
                "velocity_mm_per_min": 0.0,  # No velocity at t=0
            }
        except Exception as e:
            logger.error(f"Failed to generate t=0 data: {e}")
            raise DataGenerationError(f"Failed to generate t=0 data: {str(e)}") from e
    
    def generate_t30_data(
        self, 
        initial_data: Dict[str, Any], 
        test_duration_minutes: float = 30.0
    ) -> Dict[str, Any]:
        """
        Generate final SludgeData at end of test.
        
        Args:
            initial_data: The t=0 data to base calculations on
            test_duration_minutes: Test duration in minutes (default: 30)
            
        Returns:
            Dictionary matching SludgeData interface with SV30 calculations
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
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
            velocity_mm_per_min = (
                (initial_sludge_height - final_sludge_height) / test_duration_minutes 
                if test_duration_minutes > 0 else 0
            )
            
            # Create timestamp at end of test duration (in IST)
            # Parse initial timestamp and add duration
            initial_timestamp = parse_iso_to_ist(initial_data["timestamp"])
            final_timestamp = add_minutes_ist(initial_timestamp, test_duration_minutes)
            
            # Convert to UTC ISO format for backend (represents IST moment as UTC)
            final_timestamp_utc = final_timestamp.astimezone(timezone.utc)
            timestamp = final_timestamp_utc.isoformat().replace("+00:00", "Z")
            
            # Update RGB values slightly (clear zone might become clearer)
            rgb_clear_zone = {
                "r": min(255, initial_data["rgb_clear_zone"]["r"] + random.randint(0, 10)),
                "g": min(255, initial_data["rgb_clear_zone"]["g"] + random.randint(0, 10)),
                "b": min(255, initial_data["rgb_clear_zone"]["b"] + random.randint(0, 10))
            }
            
            logger.info(f"Generated t={test_duration_minutes} data: SV30={sv30_percentage:.1f}%")
            
            return {
                "testId": initial_data["testId"],
                "timestamp": timestamp,
                "testType": initial_data.get("testType", "morning"),
                "operator": initial_data.get("operator", "Operator"),
                "t_min": int(test_duration_minutes),
                "sludge_height_mm": round(final_sludge_height, 2),
                "mixture_height_mm": round(mixture_height, 2),
                "sv30_height_mm": round(final_sludge_height, 2),
                "sv30_mL_per_L": round(sv30_mL_per_L, 1),
                "velocity_mm_per_min": round(velocity_mm_per_min, 2),
                "floc_count": initial_data["floc_count"],
                "floc_avg_size_mm": round(initial_data["floc_avg_size_mm"], 2),
                "rgb_clear_zone": rgb_clear_zone,
                "rgb_sludge_zone": initial_data["rgb_sludge_zone"],
            }
        except Exception as e:
            logger.error(f"Failed to generate t=30 data: {e}")
            raise DataGenerationError(f"Failed to generate t=30 data: {str(e)}") from e
    
    def generate_height_history(
        self,
        initial_data: Dict[str, Any],
        duration_minutes: float = 30.0,
        interval_seconds: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate periodic sludge height measurements during the test.
        Simulates a settling curve with exponential decay.
        
        Args:
            initial_data: The t=0 data
            duration_minutes: Test duration in minutes (default: 30)
            interval_seconds: Measurement interval in seconds (default: 10)
            
        Returns:
            List of SludgeHeightEntry dictionaries with height measurements
            
        Raises:
            DataGenerationError: If data generation fails
        """
        try:
            history = []
            initial_height = initial_data["sludge_height_mm"]
            mixture_height = initial_data["mixture_height_mm"]
            
            # Get final height (use same calculation as t30)
            settling_factor = random.uniform(0.6, 0.9)
            final_height = initial_height * settling_factor
            
            # Generate measurements at intervals (using IST)
            start_time = parse_iso_to_ist(initial_data["timestamp"])
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
                
                # Calculate measurement time properly using timedelta (in IST)
                measurement_time = start_time + timedelta(seconds=elapsed_seconds)
                timestamp_ms = int(measurement_time.timestamp() * 1000)
                
                # Convert to UTC ISO format for backend compatibility
                measurement_time_utc = measurement_time.astimezone(timezone.utc)
                date_time_utc = measurement_time_utc.isoformat().replace("+00:00", "Z")
                
                history.append({
                    "timestamp": timestamp_ms,
                    "height": round(current_height, 2),
                    "dateTime": date_time_utc,
                    "testType": initial_data.get("testType", "morning")
                })
            
            logger.info(f"Generated {len(history)} height history entries")
            return history
        except Exception as e:
            logger.error(f"Failed to generate height history: {e}")
            raise DataGenerationError(f"Failed to generate height history: {str(e)}") from e

