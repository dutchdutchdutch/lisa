import json
import sys
import os
import fcntl
import time
import hashlib
import shutil
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
    _fallback_warned = set()  # Once-per-process warning per project root

    def __init__(self, state_file=None, project_root=None):
        self.project_root = project_root
        self.using_fallback = False
        if state_file:
             self.state_file = state_file
        elif project_root:
             primary = os.path.join(project_root, ".lisa", "state.json")
             if self._is_writable(primary):
                 self.state_file = primary
             else:
                 self.state_file = self._fallback_path(project_root)
                 self.using_fallback = True
        else:
             # Legacy: relative path, no project_root set. diagnose() may report
             # healthy but repair() requires project_root. No current callers use this path.
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

    def warn_if_fallback(self):
        """Emit fallback warning on stdout, once per project root per process (AC 5.8.2)."""
        if self.using_fallback and self.project_root not in StateManager._fallback_warned:
            StateManager._fallback_warned.add(self.project_root)
            print(
                f"[⚠️] State file not writable at .lisa/state.json — "
                f"using fallback: {self.state_file}\n"
                f"[⚠️] State will NOT survive reboot. Run `lisa init --fix` to repair."
            )

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

    def auto_increment_turn(self):
        """Auto-increments the turn counter once per response cycle.

        Uses epoch-second timestamp to deduplicate: multiple LISA commands
        within the same second (i.e., the same agent response) only increment once.

        Returns True if increment happened, False if deduplicated.
        """
        with self._get_lock():
            current_state = self._load_internal()
            current_ts = int(time.time())
            last_ts = current_state.get("last_auto_increment_ts", 0)

            if current_ts == last_ts:
                return False

            turn = current_state.get("turn_count", 0)
            current_state["turn_count"] = turn + 1
            current_state["last_auto_increment_ts"] = current_ts
            self._save_internal(current_state)
            return True

    def reset_turn(self):
        """Resets the turn counter and auto-increment marker to 0."""
        with self._get_lock():
            current_state = self._load_internal()
            current_state["turn_count"] = 0
            current_state.pop("last_auto_increment_ts", None)
            self._save_internal(current_state)

    def diagnose(self):
        """Check state storage health. Returns dict with diagnosis."""
        result = {"healthy": True, "issue": None, "using_fallback": self.using_fallback}

        if self.using_fallback:
            result["healthy"] = False
            result["issue"] = (
                "State is stored in a temporary directory that will not survive reboot. "
                "The primary .lisa/ directory is not writable."
            )
            return result

        # Verify current file is actually writable
        if not self._is_writable(self.state_file):
            result["healthy"] = False
            result["issue"] = f"State file is not writable: {self.state_file}"
            return result

        return result

    def repair(self):
        """Attempt to repair state storage. Returns (success, message)."""
        if not self.project_root:
            return False, "Cannot repair: no project root set."

        lisa_dir = os.path.join(self.project_root, ".lisa")
        primary = os.path.join(lisa_dir, "state.json")

        # Step 1: Ensure .lisa/ directory exists with proper permissions
        try:
            os.makedirs(lisa_dir, exist_ok=True)
        except (PermissionError, OSError) as e:
            return False, f"Cannot create .lisa/ directory: {e}"

        # Step 2: Check if primary is now writable
        if not self._is_writable(primary):
            return False, f"Primary state file still not writable at {primary}."

        # Step 3: Migrate state from fallback if applicable
        old_fallback = self.state_file if self.using_fallback else None
        if self.using_fallback and os.path.exists(self.state_file):
            try:
                shutil.copy2(self.state_file, primary)
            except (PermissionError, OSError) as e:
                return False, f"Could not migrate state from fallback: {e}"

        # Step 4: Switch to primary
        self.state_file = primary
        self.lock_file = f"{primary}.lock"
        self.using_fallback = False

        # Step 5: Clean up orphaned fallback files (best-effort)
        if old_fallback:
            try:
                fallback_dir = os.path.dirname(old_fallback)
                if os.path.exists(old_fallback):
                    os.remove(old_fallback)
                lock = f"{old_fallback}.lock"
                if os.path.exists(lock):
                    os.remove(lock)
                if os.path.isdir(fallback_dir) and not os.listdir(fallback_dir):
                    os.rmdir(fallback_dir)
            except OSError:
                pass  # Best-effort cleanup

        return True, "State storage repaired. Now using .lisa/state.json."
