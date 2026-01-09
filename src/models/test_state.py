"""
Test state machine and lifecycle management for SV30 tests.
Thread-safe state management.
"""
import threading
import time
from enum import Enum
from typing import Optional, Dict, Any


class TestState(Enum):
    """Test state enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


class TestStateManager:
    """Thread-safe test state manager"""
    
    def __init__(self, test_duration_minutes: float = 30.0):
        # Use RLock (reentrant lock) to avoid deadlocks when methods call each other
        self._lock = threading.RLock()
        self._state = TestState.IDLE
        self._test_start_time: Optional[float] = None
        self._test_duration_minutes = test_duration_minutes
        self._test_data: Dict[str, Any] = {}
        self._height_history: list = []
        
    @property
    def state(self) -> TestState:
        """Get current test state"""
        with self._lock:
            return self._state
    
    @state.setter
    def state(self, new_state: TestState):
        """Set test state (thread-safe)"""
        with self._lock:
            self._state = new_state
    
    def start_test(self) -> bool:
        """
        Start a new test cycle.
        
        Returns:
            True if test started successfully, False if already running
        """
        with self._lock:
            if self._state != TestState.IDLE:
                return False
            
            self._state = TestState.STARTING
            self._test_start_time = time.time()
            self._test_data = {}
            self._height_history = []
            return True
    
    def confirm_start(self):
        """Confirm test has started (transition from STARTING to RUNNING)"""
        with self._lock:
            if self._state == TestState.STARTING:
                self._state = TestState.RUNNING
    
    def abort_test(self) -> bool:
        """
        Abort the currently running test.
        
        Returns:
            True if test was aborted, False if no test running
        """
        with self._lock:
            if self._state not in [TestState.STARTING, TestState.RUNNING]:
                return False
            
            self._state = TestState.ABORTED
            self._test_start_time = None
            return True
    
    def complete_test(self):
        """Mark test as completed"""
        with self._lock:
            if self._state == TestState.RUNNING:
                self._state = TestState.COMPLETED
    
    def reset_to_idle(self):
        """Reset state to IDLE (after viewing results)"""
        with self._lock:
            self._state = TestState.IDLE
            self._test_start_time = None
            self._test_data = {}
            self._height_history = []
    
    def _get_elapsed_time_unlocked(self) -> float:
        """
        Get elapsed time without acquiring lock (must be called within lock context).
        
        Returns:
            Elapsed time in seconds, or 0 if no test running
        """
        if self._test_start_time is None:
            return 0.0
        return time.time() - self._test_start_time
    
    def _get_remaining_time_unlocked(self) -> float:
        """
        Get remaining time without acquiring lock (must be called within lock context).
        
        Returns:
            Remaining time in seconds, or 0 if test not running
        """
        if self._test_start_time is None or self._state != TestState.RUNNING:
            return 0.0
        
        elapsed = self._get_elapsed_time_unlocked()
        total_seconds = self._test_duration_minutes * 60
        remaining = total_seconds - elapsed
        return max(0.0, remaining)
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since test start in seconds.
        
        Returns:
            Elapsed time in seconds, or 0 if no test running
        """
        with self._lock:
            return self._get_elapsed_time_unlocked()
    
    def get_remaining_time(self) -> float:
        """
        Get remaining time until test completion in seconds.
        
        Returns:
            Remaining time in seconds, or 0 if test not running
        """
        with self._lock:
            return self._get_remaining_time_unlocked()
    
    def is_test_complete(self) -> bool:
        """
        Check if test duration has elapsed.
        
        Returns:
            True if test should be completed, False otherwise
        """
        with self._lock:
            if self._test_start_time is None or self._state != TestState.RUNNING:
                return False
            
            elapsed = self._get_elapsed_time_unlocked()
            total_seconds = self._test_duration_minutes * 60
            return elapsed >= total_seconds
    
    def set_test_data(self, key: str, value: Any):
        """Store test data (thread-safe)"""
        with self._lock:
            self._test_data[key] = value
    
    def get_test_data(self, key: str, default: Any = None) -> Any:
        """Get test data (thread-safe)"""
        with self._lock:
            return self._test_data.get(key, default)
    
    def get_all_test_data(self) -> Dict[str, Any]:
        """Get all test data (thread-safe)"""
        with self._lock:
            return self._test_data.copy()
    
    def add_height_entry(self, entry: Dict[str, Any]):
        """Add a height history entry (thread-safe)"""
        with self._lock:
            self._height_history.append(entry)
    
    def get_height_history(self) -> list:
        """Get height history (thread-safe)"""
        with self._lock:
            return self._height_history.copy()
    
    def get_status_dict(self) -> Dict[str, Any]:
        """
        Get current status as dictionary for API responses.
        
        Returns:
            Dictionary with state, elapsed time, remaining time, etc.
        """
        with self._lock:
            elapsed = self._get_elapsed_time_unlocked()
            remaining = self._get_remaining_time_unlocked()
            
            return {
                "state": self._state.value,
                "elapsed_seconds": round(elapsed, 1),
                "remaining_seconds": round(remaining, 1),
                "elapsed_minutes": round(elapsed / 60, 1),
                "remaining_minutes": round(remaining / 60, 1),
                "test_duration_minutes": self._test_duration_minutes,
                "is_running": self._state == TestState.RUNNING,
                "is_complete": self._state == TestState.COMPLETED,
                "is_aborted": self._state == TestState.ABORTED,
            }
