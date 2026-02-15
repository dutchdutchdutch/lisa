
import os
import math
import json
import time

# Default ignores to prevent scanning massive generated directories
DEFAULT_IGNORES = [
    ".git", ".lisa", ".agent", "__pycache__", "node_modules", "venv", ".env", 
    ".DS_Store", "dist", "build", "coverage"
]

CACHE_FILE = ".lisa/context_cache.json"

def count_tokens(text):
    """
    Estimates token count using the standard 'Character / 4' heuristic.
    Returns an integer.
    """
    if not text:
        return 0
    # Use ceil to be slightly conservative/safe
    return math.ceil(len(text) / 4)

def get_context_health(token_count, limit):
    """
    Returns the health status based on usage percentage.
    GREEN: < 70%
    AMBER: 70% - 90%
    RED: > 90%
    """
    if limit <= 0:
        return "RED" # Invalid limit

    usage = token_count / limit
    
    if usage > 0.90:
        return "RED"
    elif usage >= 0.70:
        return "AMBER"
    else:
        return "GREEN"

def scan_workspace(root_dir, ignores=None):
    """
    Scans the workspace recursively and sums the estimated tokens of all text files.
    Skips binary files and ignored directories.
    """
    if ignores is None:
        ignores = DEFAULT_IGNORES
        
    total_tokens = 0
    
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignores]
        
        for file in files:
            if file in ignores:
                continue
                
            file_path = os.path.join(root, file)
            
            # Skip symlinks to avoid loops or double counting
            if os.path.islink(file_path):
                continue
                
            try:
                # Use file size heuristic instead of reading content to avoid OOM
                size = os.path.getsize(file_path)
                # Heuristic: 1 token ~= 4 chars (bytes). 
                # This is safe for large files and requires zero memory.
                total_tokens += math.ceil(size / 4)
            except (IOError, OSError):
                # Skip files we can't read or stat
                continue
                
    return total_tokens

def update_cache(token_count, health):
    """Updates the token count cache."""
    cache_data = {
        "token_count": token_count,
        "health": health,
        "timestamp": time.time()
    }
    
    
    # Atomic Write Pattern: Write to temp file then rename
    # This prevents corruption if the process crashes during write
    try:
        dirname = os.path.dirname(CACHE_FILE)
        os.makedirs(dirname, exist_ok=True)
        
        # Create temp file in the same directory to ensure atomic move
        temp_file = CACHE_FILE + ".tmp"
        
        with open(temp_file, "w") as f:
            json.dump(cache_data, f)
            f.flush()
            os.fsync(f.fileno()) # Ensure data is on disk
            
        os.replace(temp_file, CACHE_FILE)
        
    except (IOError, OSError):
        pass # Fail silently (stats only)

def get_cached_health_icon():
    """
    Lazy fetch of icon. Checks TTL. If expired, re-scans.
    """
    from .config import ConfigManager
    from .utils import find_project_root
    
    config = ConfigManager().load()
    limit = config.get("context_limit", 20000) # Fallback if config fails
    interval = config.get("context_check_interval", 600)
    
    # Try reading cache
    cache = {}
    try:
        if os.path.exists(CACHE_FILE):
             with open(CACHE_FILE, "r") as f:
                 cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
        
    last_update = cache.get("timestamp", 0)
    current_time = time.time()
    
    # Check TTL
    if (current_time - last_update) < interval and "health" in cache:
        health = cache["health"]
    else:
        # Expired or missing -> Re-scan
        try:
            root = find_project_root(os.getcwd())
            token_count = scan_workspace(root)
            health = get_context_health(token_count, limit)
            update_cache(token_count, health)
        except Exception:
            # If scanning fails (e.g. permission), fallback to Unknown
            return "⚪"

    # Map to Icon
    if health == "GREEN": return "🟢"
    if health == "AMBER": return "🟡"
    if health == "RED": return "🔴"
    return "⚪"

