"""
Test service for managing SV30 test lifecycle.

This service handles all test-related business logic, including
starting tests, managing state, generating data, and communicating
with the backend.
"""
import logging
import threading
from typing import Dict, Any, Optional

from ..models import TestStateManager, TestState
from ..models.types import SludgeData
from ..exceptions import TestStateError, DataGenerationError
from ..constants import DEFAULT_HEIGHT_UPDATE_INTERVAL_SECONDS
from .data_provider import DataProvider
from .backend_client import BackendSender

logger = logging.getLogger(__name__)


class TestService:
    """
    Service for managing SV30 test lifecycle.
    
    This service coordinates between the test state manager,
    data provider, and backend sender to handle test operations.
    """
    
    def __init__(
        self,
        test_manager: TestStateManager,
        data_provider: DataProvider,
        backend_sender: BackendSender
    ):
        """
        Initialize test service.
        
        Args:
            test_manager: Test state manager instance
            data_provider: Data provider for generating test data
            backend_sender: Backend sender for transmitting data
        """
        self.test_manager = test_manager
        self.data_provider = data_provider
        self.backend_sender = backend_sender
        self._height_update_thread: Optional[threading.Thread] = None
    
    def start_test(self) -> Dict[str, Any]:
        """
        Start a new test cycle.
        
        Returns:
            Dictionary with success status and state
            
        Raises:
            TestStateError: If test cannot be started (already running, etc.)
            DataGenerationError: If data generation fails
        """
        # Check state - must be IDLE
        if self.test_manager.state != TestState.IDLE:
            raise TestStateError(
                f"Test already running or not in idle state (current: {self.test_manager.state.value})"
            )
        
        # Start test (sets state to STARTING)
        if not self.test_manager.start_test():
            raise TestStateError("Failed to start test")
        
        try:
            # Generate and store t=0 data (for local use only - frontend display, height history)
            # NOTE: t=0 data is NOT sent to backend - backend only needs final t=30 data
            logger.info("Generating t=0 data (local use only)...")
            t0_data = self.data_provider.generate_t0_data()
            self.test_manager.set_test_data("t0_data", t0_data)
            
            # Transition to RUNNING
            self.test_manager.confirm_start()
            logger.info("Test started successfully")
            
            # Start background tasks (non-blocking, errors are non-critical)
            def background_tasks():
                # NOTE: t=0 data is NOT sent to backend - backend only needs final t=30 data
                # t=0 data is kept locally for frontend display and height history generation
                
                try:
                    # Start periodic height updates (uses t=0 data for initial state)
                    self._start_periodic_updates(t0_data)
                except Exception as e:
                    logger.warning(f"Periodic updates failed (non-critical): {e}")
            
            threading.Thread(target=background_tasks, daemon=True).start()
            
            return {
                "success": True,
                "state": self.test_manager.state.value
            }
        except DataGenerationError:
            # Reset state on data generation failure
            self.test_manager.reset_to_idle()
            raise
        except Exception as e:
            # Reset state on any other error
            logger.error(f"Error starting test: {e}")
            try:
                if self.test_manager.state == TestState.STARTING:
                    self.test_manager.reset_to_idle()
            except:
                pass
            raise TestStateError(f"Failed to start test: {str(e)}") from e
    
    def abort_test(self) -> Dict[str, Any]:
        """
        Abort the currently running test.
        
        Returns:
            Dictionary with success status and state
            
        Raises:
            TestStateError: If no test is running
        """
        if self.test_manager.state not in [TestState.STARTING, TestState.RUNNING]:
            raise TestStateError("No test running to abort")
        
        if self.test_manager.abort_test():
            self._stop_periodic_updates()
            logger.info("Test aborted successfully")
            return {
                "success": True,
                "state": self.test_manager.state.value
            }
        else:
            raise TestStateError("Failed to abort test")
    
    def get_test_status(self) -> Dict[str, Any]:
        """
        Get current test status.
        
        Returns:
            Dictionary with test status information
        """
        return self.test_manager.get_status_dict()
    
    def get_test_data(self) -> Dict[str, Any]:
        """
        Get current test data for real-time updates.
        
        Returns:
            Dictionary with t0_data (local use only), t30_data, latest_height, and height_history
            NOTE: t0_data is kept locally for frontend display and height history generation.
            Only t30_data is sent to backend.
        """
        t0_data = self.test_manager.get_test_data("t0_data")
        t30_data = self.test_manager.get_test_data("t30_data")
        height_history = self.test_manager.get_height_history()
        
        # Get latest height from history
        latest_height = None
        if height_history:
            latest_height = height_history[-1]["height"]
        
        return {
            "t0_data": t0_data,
            "t30_data": t30_data,
            "latest_height": latest_height,
            "height_history": height_history[-10:] if height_history else []
        }
    
    def complete_test(self) -> None:
        """
        Complete the test and generate t=30 data.
        
        This method is called when the test duration has elapsed.
        It generates t=30 data and sends it to the backend.
        NOTE: Only t=30 data is sent to backend (t=0 is kept locally only).
        """
        if self.test_manager.state != TestState.RUNNING:
            logger.warning(f"Cannot complete test in state: {self.test_manager.state.value}")
            return
        
        self.test_manager.complete_test()
        logger.info("Test completed after duration")
        
        # Stop periodic updates
        self._stop_periodic_updates()
        
        # Generate and send t30 data to backend
        t0_data = self.test_manager.get_test_data("t0_data")
        if t0_data:
            def generate_and_send_t30():
                try:
                    logger.info("Generating t=30 data after completion...")
                    # Get test duration from status
                    status = self.test_manager.get_status_dict()
                    test_duration = status.get("test_duration_minutes", 30.0)
                    t30_data = self.data_provider.generate_t30_data(
                        t0_data,
                        test_duration
                    )
                    self.test_manager.set_test_data("t30_data", t30_data)
                    
                    logger.info("Sending t=30 data to backend...")
                    self.backend_sender.send_sludge_data(t30_data)
                    logger.info("t=30 data sent to backend")
                except Exception as e:
                    logger.error(f"Error generating/sending t=30 data: {e}")
            
            # Send in background thread
            t30_thread = threading.Thread(target=generate_and_send_t30, daemon=True)
            t30_thread.start()
    
    def get_test_result(self) -> Dict[str, Any]:
        """
        Get final test result.
        
        Returns:
            Dictionary with test result including SV30 percentage
            
        Raises:
            TestStateError: If test is not completed
        """
        if self.test_manager.state != TestState.COMPLETED:
            raise TestStateError("Test not completed")
        
        t0_data = self.test_manager.get_test_data("t0_data")
        t30_data = self.test_manager.get_test_data("t30_data")
        
        if not t30_data:
            # Generate t30 data if not already generated
            if t0_data:
                logger.info("Generating t=30 data for result...")
                # Get test duration from status
                status = self.test_manager.get_status_dict()
                test_duration = status.get("test_duration_minutes", 30.0)
                t30_data = self.data_provider.generate_t30_data(
                    t0_data,
                    test_duration
                )
                self.test_manager.set_test_data("t30_data", t30_data)
                
                # Send t=30 data to backend (non-blocking)
                # NOTE: Only t=30 final data is sent to backend, not t=0
                def send_t30_data_async():
                    try:
                        logger.info("Sending t=30 data to backend...")
                        self.backend_sender.send_sludge_data(t30_data)
                        logger.info("t=30 data sent to backend")
                    except Exception as e:
                        logger.warning(f"Failed to send t=30 data to backend (non-critical): {e}")
                
                send_thread = threading.Thread(target=send_t30_data_async, daemon=True)
                send_thread.start()
            else:
                raise TestStateError("Initial test data not found")
        
        if not t30_data:
            raise TestStateError("Test data not found")
        
        # Calculate SV30 percentage
        sludge_height = t30_data.get("sludge_height_mm", 0)
        mixture_height = t30_data.get("mixture_height_mm", 1)
        sv30_percentage = (sludge_height / mixture_height) * 100 if mixture_height > 0 else 0
        
        # Get test duration from status
        status = self.test_manager.get_status_dict()
        test_duration = status.get("test_duration_minutes", 30.0)
        
        return {
            "test_status": "Completed",
            "test_duration_minutes": round(test_duration, 2),
            "sludge_height_mm": round(sludge_height, 2),
            "sv30_percentage": round(sv30_percentage, 2),
            "sv30_mL_per_L": t30_data.get("sv30_mL_per_L", 0),
            "t0_data": t0_data,
            "t30_data": t30_data
        }
    
    def reset_test(self) -> Dict[str, Any]:
        """
        Reset test state to idle.
        
        Returns:
            Dictionary with success status and state
        """
        self._stop_periodic_updates()
        self.test_manager.reset_to_idle()
        
        # Verify state is actually idle
        final_state = self.test_manager.state
        if final_state != TestState.IDLE:
            logger.warning(f"Warning: Reset did not result in IDLE state, got: {final_state}")
            # Force it again
            self.test_manager.reset_to_idle()
            final_state = self.test_manager.state
        
        logger.info("Test reset to idle")
        return {
            "success": True,
            "state": final_state.value
        }
    
    def recover_test(self) -> Dict[str, Any]:
        """
        Recovery endpoint: reset stuck states.
        
        Returns:
            Dictionary with recovery status
        """
        current_state = self.test_manager.state
        
        # If stuck in STARTING, reset to IDLE
        if current_state == TestState.STARTING:
            logger.info("Recovering from stuck STARTING state")
            self.test_manager.reset_to_idle()
            return {
                "success": True,
                "message": "Recovered from stuck STARTING state",
                "state": self.test_manager.state.value
            }
        
        # If in RUNNING but no test data, something is wrong
        if current_state == TestState.RUNNING:
            t0_data = self.test_manager.get_test_data("t0_data")
            if not t0_data:
                logger.info("Recovering from RUNNING state without data")
                self.test_manager.reset_to_idle()
                return {
                    "success": True,
                    "message": "Recovered from invalid RUNNING state",
                    "state": self.test_manager.state.value
                }
        
        return {
            "success": True,
            "message": "No recovery needed",
            "state": current_state.value
        }
    
    def _start_periodic_updates(self, initial_data: Dict[str, Any]) -> None:
        """
        Start sending periodic height updates during test.
        
        Args:
            initial_data: The t=0 data
        """
        import time
        
        def send_updates():
            try:
                # Generate height history once
                status = self.test_manager.get_status_dict()
                test_duration = status.get("test_duration_minutes", 30.0)
                height_history = self.data_provider.generate_height_history(
                    initial_data,
                    test_duration,
                    interval_seconds=DEFAULT_HEIGHT_UPDATE_INTERVAL_SECONDS
                )
                logger.info(f"Generated {len(height_history)} height history entries")
            except Exception as e:
                logger.error(f"Error generating height history: {e}")
                return
            
            start_time = time.time()
            
            # Send updates every 10 seconds
            for i, entry in enumerate(height_history):
                # Check if test is still running
                if self.test_manager.state != TestState.RUNNING:
                    break
                
                # Wait until it's time for this update
                target_time = start_time + (i * DEFAULT_HEIGHT_UPDATE_INTERVAL_SECONDS)
                wait_seconds = max(0, target_time - time.time())
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                
                # Double-check state before storing
                if self.test_manager.state == TestState.RUNNING:
                    self.test_manager.add_height_entry(entry)
                    
                    # Send to backend (non-critical if it fails)
                    try:
                        self.backend_sender.send_height_update(
                            entry.get("height"),
                            entry.get("dateTime"),
                            entry.get("testType")
                        )
                    except Exception:
                        pass  # Non-critical
        
        self._height_update_thread = threading.Thread(target=send_updates, daemon=True)
        self._height_update_thread.start()
    
    def _stop_periodic_updates(self) -> None:
        """Stop periodic height updates."""
        # The thread will stop naturally when state changes
        # or when the loop detects state != RUNNING
        self._height_update_thread = None

