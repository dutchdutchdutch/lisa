import json
import os
import fcntl
import time
from contextlib import contextmanager

class StateManager:
    def __init__(self, state_file=".lisa/state.json"):
        self.state_file = state_file
        self.lock_file = f"{state_file}.lock"
        self._ensure_dir()

    @property
    def _default_state(self):
        return {
            "taskId": "none",
            "status": "GREEN",
            "mode": "NORMAL",
            "lastUpdated": time.time()
        }

    def _ensure_dir(self):
        dirname = os.path.dirname(self.state_file)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    @contextmanager
    def _get_lock(self):
        """Acquires an exclusive lock on the lock file."""
        # Ensure lock directory exists
        lock_dir = os.path.dirname(self.lock_file)
        if lock_dir:
            os.makedirs(lock_dir, exist_ok=True)
            
        with open(self.lock_file, "w") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _load_internal(self):
        """Internal load without locking."""
        if not os.path.exists(self.state_file):
            return self._default_state
            
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
             return self._default_state
        except json.JSONDecodeError:
            # TODO: Warn user about corruption using a logger or stderr
            # For now, per NFR3 (Fail-Open), we return default state to allow proceeding
            return self._default_state

    def _save_internal(self, state):
        """Internal save without locking, using atomic rename."""
        state["lastUpdated"] = time.time()
        
        # Write to temp file first
        tmp_file = f"{self.state_file}.tmp"
        with open(tmp_file, "w") as f:
            json.dump(state, f, indent=2)
            
        # Atomic rename
        os.replace(tmp_file, self.state_file)

    def load(self):
        """Loads the current state from the state file (thread-safe)."""
        with self._get_lock():
            return self._load_internal()

    def save(self, state):
        """Saves the state to the state file (thread-safe)."""
        with self._get_lock():
            self._save_internal(state)

    def update(self, key, value):
        """Updates a specific key in the state transactionally."""
        with self._get_lock():
            current_state = self._load_internal()
            current_state[key] = value
            self._save_internal(current_state)
