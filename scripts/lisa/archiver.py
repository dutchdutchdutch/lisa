
import os
import shutil
import time
import json
from .state import StateManager, LISA_MODES

def archive_session(root_dir):
    """
    Archives the current session state and logs to .lisa/archive/{timestamp}.
    Returns the path to the created archive.
    """
    lisa_dir = os.path.join(root_dir, ".lisa")
    archive_root = os.path.join(lisa_dir, "archive")
    
    # Generate timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(archive_root, timestamp)
    
    # Create archive directory
    os.makedirs(archive_path, exist_ok=True)
    
    # Files to archive
    # We archive everything in .lisa EXCEPT the archive folder itself and lock files
    if os.path.exists(lisa_dir):
        for item in os.listdir(lisa_dir):
            s = os.path.join(lisa_dir, item)
            d = os.path.join(archive_path, item)
            
            # Skip the archive directory itself to avoid recursion
            if item == "archive":
                continue
                
            # Skip lock files
            if item.endswith(".lock"):
                continue
                
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            except Exception as e:
                import sys
                sys.stderr.write(f"[LISA] [WARNING] Could not archive {item}: {e}\n")
                
    return archive_path

def reset_session(root_dir):
    """
    Resets the session state to defaults.
    """
    # Fix: StateManager expects a file path, not a dir path
    state_file = os.path.join(root_dir, ".lisa", "state.json")
    state_manager = StateManager(state_file)
    
    # Reset to default state
    new_state = {
        "mode": LISA_MODES.NORMAL,
        "status": "IDLE",
        "task": None,
        "step": None,
        "lastUpdated": time.time()
    }
    
    # Use StateManager's save method which handles locking and atomic writing
    try:
        state_manager.save(new_state)
        return True
    except Exception as e:
        import sys
        sys.stderr.write(f"[LISA] [ERROR] Reset failed: {e}\n")
        return False
