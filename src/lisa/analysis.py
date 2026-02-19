import ast
import os
from pathlib import Path

from .utils import DEFAULT_IGNORES, is_ignored

def get_module_name(file_path, project_root):
    """
    Converts a file path to a dotted module name relative to project root.
    e.g. scripts/lisa/commands.py -> scripts.lisa.commands
    """
    abs_path = Path(file_path).resolve()
    abs_root = Path(project_root).resolve()
    
    try:
        rel_path = abs_path.relative_to(abs_root)
    except ValueError:
        return None
        
    # Remove extension and replace separators
    return str(rel_path.with_suffix('')).replace(os.sep, '.')

def find_importers(target_file, project_root=None):
    """
    Scans the project for files that import the target_file.
    Returns a list of relative file paths.
    """
    if project_root is None:
        # Default to current working directory or find git root
        project_root = os.getcwd()

    target_module = get_module_name(target_file, project_root)
    if not target_module:
        return []

    importers = []
    
    # Walk through the project
    for root, dirs, files in os.walk(project_root):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if not is_ignored(d, DEFAULT_IGNORES)]
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            # Skip the target file itself
            if os.path.abspath(file_path) == os.path.abspath(target_file):
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=file_path)
                    
                for node in ast.walk(tree):
                    # Check for "import dependencies"
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == target_module or alias.name.startswith(target_module + "."):
                                importers.append(os.path.relpath(file_path, project_root))
                                break
                    # Check for "from dependencies import ..."
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and (node.module == target_module or node.module.startswith(target_module + ".")):
                            importers.append(os.path.relpath(file_path, project_root))
                            break
            except (SyntaxError, UnicodeDecodeError):
                # Skip files that aren't valid Python or can't be read
                continue
            except Exception as e:
                # Log other errors but continue scanning
                # In a real app we might use logging.warning
                print(f"[LISA] Warning: Failed to parse {file_path}: {e}")
                continue
                
    return importers
