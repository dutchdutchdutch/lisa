import json
import sys
import os
import fcntl
import time
from contextlib import contextmanager

class LISA_MODES:
    NORMAL = "NORMAL"
    SPIKE = "SPIKE"
    BYPASS_TDD = "BYPASS_TDD"

class ContextActivity:
    ACTIVE = "active"
    MONITORING = "monitoring"
    COMPACTING = "compacting"
    CHECKPOINTING = "checkpointing"
    RESETTING = "resetting"
    ARCHIVING = "archiving"

class StateManager:
    def __init__(self, state_file=None, project_root=None):
        if state_file:
             self.state_file = state_file
        elif project_root:
             self.state_file = os.path.join(project_root, ".lisa", "state.json")
        else:
             # Fallback default (fragile if not at root, but keeps backward compat)
             self.state_file = ".lisa/state.json"
             
        self.lock_file = f"{self.state_file}.lock"
        self._ensure_dir()

    @property
    def _default_state(self):
        return {
            "taskId": "none",
            "status": "GREEN",
            "mode": LISA_MODES.NORMAL,
            "activity": "active",
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
            
        try:
            f = open(self.lock_file, "w")
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
                f.close()
        except (PermissionError, OSError) as e:
            # NFR3: Fail-Open
            # If we can't lock, we proceed without locking.
            # We warn on stderr so it doesn't break JSON output parsing if any.
            sys.stderr.write(f"[LISA] [WARNING] Could not acquire lock on {self.lock_file}: {e}\n")
            yield

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
