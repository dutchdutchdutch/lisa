
import os
import math
import json
import time

# Default ignores to prevent scanning massive generated directories
DEFAULT_IGNORES = [
    ".git", ".lisa", ".agent", "__pycache__", "node_modules", "venv", ".env", 
    ".DS_Store", "dist", "build", "coverage", ".pytest_cache"
]

CACHE_FILE = ".lisa/context_cache.json"
MAX_FILE_SIZE = 10 * 1024 * 1024 # 10MB

# Try to load tiktoken, fallback to heuristic if missing (graceful degradation)
try:
    import tiktoken
    ENCODING = tiktoken.get_encoding("cl100k_base")
except ImportError:
    ENCODING = None

def count_tokens(text):
    """
    Counts tokens using tiktoken (cl100k_base) if available.
    Falls back to 'Character / 4' heuristic if tiktoken is missing.
    """
    if not text:
        return 0
    
    if ENCODING:
        # disallowed_special=() allows encoding special tokens like <|endoftext|>
        # which might appear in code/prompt templates.
        return len(ENCODING.encode(text, disallowed_special=()))
    
    # Fallback Heuristic
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
    Scans the workspace recursively and sums the tokens of all text files.
    Uses tiktoken for accuracy. Skips binary files (UnicodeDecodeError).
    """
    if ignores is None:
        ignores = DEFAULT_IGNORES
        
    total_tokens = 0
    file_count = 0
    
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
                # Attempt to read file as text to count tokens accurately
                # limit size to prevent reading massive files (e.g. 10MB limit)
                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    # Fallback for massive files: size / 4
                    total_tokens += math.ceil(os.path.getsize(file_path) / 4)
                    file_count += 1
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    total_tokens += count_tokens(content)
                    file_count += 1
            except UnicodeDecodeError:
                # Binary file (image, compiled, etc) -> Skip
                continue
            except (IOError, OSError):
                # Skip files we can't read or stat
                continue
                
    return total_tokens, file_count

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

def get_cache_status(limit, interval=None):
    """
    Checks cache validity and returns (token_count, health) if valid, else (None, None).
    Helper to avoid config duplication.
    """
    if interval is None:
        # If interval not provided, assume we want to check strict validity
        # But we really need the interval to check TTL.
        # So we might still need config here if not passed.
        # Let's keep it simple: Read cache, return data + timestamp.
        pass

    try:
        if os.path.exists(CACHE_FILE):
             with open(CACHE_FILE, "r") as f:
                 cache = json.load(f)
                 return cache
    except (json.JSONDecodeError, OSError):
        pass
    return {}

def get_cached_health_icon():
    """
    Lazy fetch of icon. Checks TTL. If expired, re-scans.
    """
    from .config import ConfigManager
    from .utils import find_project_root
    
    # Load config once
    try:
        root = find_project_root(os.getcwd())
        config = ConfigManager(project_root=root).load()
    except:
        config = ConfigManager().load()
    
    limit = config.get("context_limit", 20000)
    interval = config.get("context_check_interval", 600)
    
    # Check Cache
    cache = get_cache_status(limit)
    last_update = cache.get("timestamp", 0)
    current_time = time.time()
    
    # Check TTL
    if (current_time - last_update) < interval and "health" in cache:
        health = cache["health"]
    else:
        # Expired or missing -> Re-scan
        try:
             # Logic duplication meant we were resolving root/config twice.
             # Now we use the resolved root/config from above.
             # Wait, root might be missing if get_context_health is called from weird place?
             # But find_project_root logic is robust.
            if 'root' not in locals():
                 root = find_project_root(os.getcwd()) # Fallback

            token_count, _ = scan_workspace(root)
            health = get_context_health(token_count, limit)
            update_cache(token_count, health)
        except Exception:
            return "⚪"

    # Map to Icon
    if health == "GREEN": return "🟢"
    if health == "AMBER": return "🟡"
    if health == "RED": return "🔴"
    return "⚪"

