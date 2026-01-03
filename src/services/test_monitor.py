"""
Background test monitoring service.

This service monitors test progress in the background and automatically
completes tests when the duration has elapsed.
"""
import logging
import time
import threading
from typing import Optional

from ..models import TestStateManager, TestState
from ..constants import MAX_STARTING_STATE_TIME_SECONDS
from .test_service import TestService

logger = logging.getLogger(__name__)


class TestMonitor:
    """
    Background service that monitors test progress.
    
    This monitor runs in a separate thread and:
    - Detects when test duration has elapsed
    - Automatically completes tests
    - Handles stuck states (e.g., stuck in STARTING)
    - Emits state change events via SocketIO
    """
    
    def __init__(
        self,
        test_manager: TestStateManager,
        test_service: TestService,
        socketio=None
    ):
        """
        Initialize test monitor.
        
        Args:
            test_manager: Test state manager instance
            test_service: Test service for completing tests
            socketio: SocketIO instance for emitting events (optional)
        """
        self.test_manager = test_manager
        self.test_service = test_service
        self.socketio = socketio
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start the monitoring thread."""
        if self._running:
            logger.warning("Test monitor is already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Test monitor started")
    
    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Test monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        last_state = None
        starting_state_time = None
        
        while self._running:
            try:
                time.sleep(1)  # Check every second
                
                current_state = self.test_manager.state
                
                # Detect state changes
                if current_state != last_state:
                    logger.info(f"State changed: {last_state} -> {current_state}")
                    last_state = current_state
                    
                    # Track when we enter STARTING state
                    if current_state == TestState.STARTING:
                        starting_state_time = time.time()
                    else:
                        starting_state_time = None
                
                # Recovery: If stuck in STARTING state for too long, reset to IDLE
                if current_state == TestState.STARTING and starting_state_time:
                    elapsed = time.time() - starting_state_time
                    if elapsed > MAX_STARTING_STATE_TIME_SECONDS:
                        logger.warning(
                            f"Test stuck in STARTING state for {elapsed:.1f}s, resetting to IDLE"
                        )
                        self.test_manager.reset_to_idle()
                        last_state = TestState.IDLE
                        starting_state_time = None
                        # Emit state update
                        self._emit_state_update()
                
                # Monitor running tests
                if current_state == TestState.RUNNING:
                    if self.test_manager.is_test_complete():
                        logger.info("Test duration elapsed, completing test...")
                        self.test_service.complete_test()
                        
                        # Emit completion event via SocketIO
                        if self.socketio:
                            try:
                                self.socketio.emit(
                                    "test_completed",
                                    {"type": "test_completed"},
                                    namespace='/'
                                )
                            except Exception as e:
                                logger.warning(f"Error emitting completion event: {e}")
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(1)
    
    def _emit_state_update(self) -> None:
        """Emit state update via SocketIO."""
        if not self.socketio:
            return
        
        try:
            status = self.test_manager.get_status_dict()
            # Get test data directly from test service if available
            if hasattr(self.test_service, 'get_test_data'):
                test_data = self.test_service.get_test_data()
            else:
                test_data = {
                    "t0_data": None,
                    "t30_data": None,
                    "latest_height": None,
                    "height_history": []
                }
            
            self.socketio.emit("update", {
                "status": status,
                "data": test_data
            }, namespace='/')
        except Exception as e:
            logger.warning(f"Failed to emit state update: {e}")

