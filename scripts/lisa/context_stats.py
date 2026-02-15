
import os
import math

# Default ignores to prevent scanning massive generated directories
DEFAULT_IGNORES = [
    ".git", ".lisa", ".agent", "__pycache__", "node_modules", "venv", ".env", 
    ".DS_Store", "dist", "build", "coverage"
]

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
                # Attempt to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    total_tokens += count_tokens(content)
            except (IOError, OSError):
                # Skip files we can't read
                continue
                
    return total_tokens
