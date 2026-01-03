"""
Type definitions for the HMI server.
"""
from typing import Dict, Any, Optional, TypedDict


class SludgeData(TypedDict, total=False):
    """Sludge data structure matching backend interface"""
    testId: Optional[str]
    timestamp: str
    testType: Optional[str]  # "morning" | "afternoon" | "evening"
    operator: Optional[str]
    image_filename: Optional[str]
    debug_vis: Optional[str]
    t_min: Optional[int]
    sludge_height_mm: float
    mixture_height_mm: float
    sv30_height_mm: Optional[float]
    sv30_mL_per_L: Optional[float]
    velocity_mm_per_min: Optional[float]
    floc_count: int
    floc_avg_size_mm: float
    rgb_clear_zone: Optional[Dict[str, int]]
    rgb_sludge_zone: Optional[Dict[str, int]]
    image_path: Optional[str]
    # Legacy fields
    sludge_height_px: Optional[float]
    liquid_height_px: Optional[float]
    sludge_level_avg_px_from_top: Optional[float]
    settling_velocity_since_last_px_per_s: Optional[float]
    overall_settling_velocity_px_per_s: Optional[float]
    particle_count: Optional[int]
    particle_areas_px2: Optional[list]


class SludgeHeightEntry(TypedDict):
    """Sludge height history entry"""
    timestamp: int
    height: float
    dateTime: str
    testType: Optional[str]


class TestResult(TypedDict):
    """Test result structure"""
    test_status: str
    test_duration_minutes: int
    sludge_height_mm: float
    sv30_percentage: float
    sv30_mL_per_L: float
    t0_data: Optional[Dict[str, Any]]
    t30_data: Optional[Dict[str, Any]]

