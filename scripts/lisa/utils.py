import os
from pathlib import Path

DEFAULT_IGNORES = [".git", ".lisa", "__pycache__", "node_modules", "venv", ".env", ".agent"]

def find_project_root(start_path: str = None) -> str:
    """
    Finds the project root by looking for marker files/directories
    (.lisa, lisa.sh, .git) starting from start_path and walking up.
    
    Args:
        start_path: The path to start searching from. Defaults to cwd.
        
    Returns:
        Absolute path to the project root.
        
    Raises:
        FileNotFoundError: If project root cannot be found.
    """
    if start_path is None:
        start_path = os.getcwd()
        
    current_path = Path(start_path).resolve()
    
    # Root of filesystem
    root_path = Path(current_path.root)

    while current_path != root_path:
        # Check for markers
        if (current_path / ".lisa").exists() and (current_path / ".lisa").is_dir():
            return str(current_path)
        if (current_path / "lisa.sh").exists() and (current_path / "lisa.sh").is_file():
            return str(current_path)
        if (current_path / ".git").exists() and (current_path / ".git").is_dir():
            return str(current_path)
            
        # Move up
        parent = current_path.parent
        if parent == current_path: # Infinite loop protection (should be caught by root_path check but just in case)
            break
        current_path = parent
        
    raise FileNotFoundError("Could not find project root (looking for .lisa, lisa.sh, or .git)")
