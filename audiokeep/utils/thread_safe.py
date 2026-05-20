"""Thread-safe primitives used across the application."""

import threading
from enum import Enum, auto


class RunState(Enum):
    """Lifecycle states for the audio engine."""
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    STOPPING = auto()


class StateManager:
    """Thread-safe state machine for the audio engine lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = RunState.STOPPED
        self._condition = threading.Condition(self._lock)

    @property
    def state(self) -> RunState:
        with self._lock:
            return self._state

    def transition(self, from_state: RunState, to_state: RunState) -> bool:
        """Atomically transition from one state to another.

        Returns True if the transition happened, False if the current state
        does not match ``from_state``.
        """
        with self._lock:
            if self._state == from_state:
                self._state = to_state
                self._condition.notify_all()
                return True
            return False

    def wait_for(self, state: RunState, timeout: float | None = None) -> bool:
        """Block until the state equals ``state`` or timeout elapses."""
        with self._condition:
            return self._condition.wait_for(lambda: self._state == state, timeout=timeout)

    @property
    def is_active(self) -> bool:
        return self.state in (RunState.RUNNING, RunState.STARTING)

    @property
    def is_paused(self) -> bool:
        return self.state in (RunState.PAUSED, RunState.PAUSING)
