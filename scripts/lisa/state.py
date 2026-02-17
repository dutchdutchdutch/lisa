import json
import sys
import os
import fcntl
import time
import hashlib
import tempfile
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
             primary = os.path.join(project_root, ".lisa", "state.json")
             if self._is_writable(primary):
                 self.state_file = primary
             else:
                 self.state_file = self._fallback_path(project_root)
                 sys.stderr.write(
                     f"[LISA] [INFO] State file not writable at .lisa/state.json — "
                     f"using fallback: {self.state_file}\n"
                 )
        else:
             # Fallback default (fragile if not at root, but keeps backward compat)
             self.state_file = ".lisa/state.json"
             
        self.lock_file = f"{self.state_file}.lock"
        self._ensure_dir()

    @staticmethod
    def _is_writable(path):
        """Test if a file path is writable (create or append)."""
        try:
            if os.path.exists(path):
                with open(path, "r+"):
                    return True
            else:
                # Try creating it
                with open(path, "w") as f:
                    json.dump({}, f)
                return True
        except (PermissionError, OSError):
            return False

    @staticmethod
    def _fallback_path(project_root):
        """Generate a deterministic fallback path in the system temp directory."""
        project_hash = hashlib.md5(project_root.encode()).hexdigest()[:12]
        fallback_dir = os.path.join(tempfile.gettempdir(), f".lisa-{project_hash}")
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, "state.json")

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
        """Internal save without locking, using atomic rename with fallback."""
        state["lastUpdated"] = time.time()
        
        # Write to temp file first
        tmp_file = f"{self.state_file}.temp"
        try:
            with open(tmp_file, "w") as f:
                json.dump(state, f, indent=2)
                
            # Atomic rename
            os.replace(tmp_file, self.state_file)
        except (PermissionError, OSError) as e:
            # Fallback: Write directly to state file if temp file/rename fails
            # This risks corruption but ensures we can write if permissions allow direct write
            # but block temp file creation/rename (distinction sometimes made by container runtimes)
            sys.stderr.write(f"[LISA] [WARNING] Atomic save failed ({e}). Attempting direct write...\n")
            try:
                with open(self.state_file, "w") as f:
                    json.dump(state, f, indent=2)
            except Exception as e2:
                sys.stderr.write(f"[LISA] [ERROR] Could not save state: {e2}\n")

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

    def increment_turn(self):
        """Increments the turn counter transactionally."""
        with self._get_lock():
            current_state = self._load_internal()
            turn = current_state.get("turn_count", 0)
            new_turn = turn + 1
            current_state["turn_count"] = new_turn
            self._save_internal(current_state)
            return new_turn

    def reset_turn(self):
        """Resets the turn counter to 0."""
        self.update("turn_count", 0)
