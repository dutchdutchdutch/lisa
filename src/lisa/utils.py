import fnmatch
import os
from pathlib import Path

DEFAULT_IGNORES = [
    # Version control / tooling
    ".git", ".lisa", ".bmad", "_bmad", ".agent",
    # Python
    "__pycache__", "venv", ".venv", "env", ".env",
    ".tox", ".nox", ".mypy_cache", ".ruff_cache", ".pytest_cache",
    ".eggs", "*.egg-info", "htmlcov", "site-packages",
    # JS / Node / package managers
    "node_modules", ".npm", ".npm-custom-cache", ".pnpm-store",
    # JS frameworks (build & cache dirs)
    ".next", ".nuxt", ".output", ".svelte-kit", ".angular",
    ".turbo", ".parcel-cache", ".cache", ".docusaurus", "storybook-static",
    # Mobile / cross-platform
    ".expo", ".dart_tool", ".flutter-plugins", ".flutter-plugins-dependencies",
    "Pods", ".gradle", "DerivedData", "*.xcarchive",
    # JVM / Kotlin
    ".kotlin", ".kotlinc", ".idea", "*.iml",
    # Build artifacts
    "dist", "build", "coverage", "out", "target",
    # Data / databases
    "data", "*.db", "*.sqlite", "*.sqlite3", "*.mdb", "*.accdb",
    "*.dbf", "*.ldb", "*.rdb", "dump.rdb",
    # OS
    ".DS_Store",
]

def is_ignored(name, ignores):
    """Check if a file/dir name matches any ignore pattern (exact or glob)."""
    for pattern in ignores:
        if '*' in pattern or '?' in pattern:
            if fnmatch.fnmatch(name, pattern):
                return True
        elif name == pattern:
            return True
    return False


def find_project_root(start_path: str = None) -> str:
    """
    Finds the project root by looking for marker files/directories
    (.lisa, .git) starting from start_path and walking up.
    
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
        if (current_path / ".git").exists() and (current_path / ".git").is_dir():
            return str(current_path)
            
        # Move up
        parent = current_path.parent
        if parent == current_path: # Infinite loop protection (should be caught by root_path check but just in case)
            break
        current_path = parent
        
    raise FileNotFoundError("Could not find project root (looking for .lisa or .git)")
