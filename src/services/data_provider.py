"""
Abstract interface for data generation in SV30 tests.

This module defines the DataProvider interface that must be implemented
by any data generation module (dummy data, ML model, etc.).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ..models.types import SludgeData, SludgeHeightEntry


class DataProvider(ABC):
    """
    Abstract base class for data generation providers.
    
    This interface allows easy swapping between dummy data generation
    and real ML model implementations.
    """
    
    @abstractmethod
    def generate_t0_data(self) -> Dict[str, Any]:
        """
        Generate initial SludgeData at t=0 (start of test).
        
        Returns:
            Dictionary matching SludgeData interface with initial measurements
            
        Raises:
            DataGenerationError: If data generation fails
        """
        pass
    
    @abstractmethod
    def generate_t30_data(
        self, 
        initial_data: Dict[str, Any], 
        test_duration_minutes: float
    ) -> Dict[str, Any]:
        """
        Generate final SludgeData at end of test (t=30 or test duration).
        
        Args:
            initial_data: The t=0 data to base calculations on
            test_duration_minutes: Test duration in minutes
            
        Returns:
            Dictionary matching SludgeData interface with final measurements
            including SV30 calculations
            
        Raises:
            DataGenerationError: If data generation fails
        """
        pass
    
    @abstractmethod
    def generate_height_history(
        self,
        initial_data: Dict[str, Any],
        duration_minutes: float,
        interval_seconds: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate periodic sludge height measurements during the test.
        
        Args:
            initial_data: The t=0 data
            duration_minutes: Test duration in minutes
            interval_seconds: Measurement interval in seconds (default: 10)
            
        Returns:
            List of SludgeHeightEntry dictionaries with height measurements
            at regular intervals
            
        Raises:
            DataGenerationError: If data generation fails
        """
        pass

