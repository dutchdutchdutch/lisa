"""Scope Derivation — derives test scope from modified files (Story 7.2).

Computes the dependency cone for modified source files, maps to in-scope
test files grouped by layer, and persists the scope for downstream use.
"""
import json
import os
import subprocess
import time

from .analysis import find_importers, get_module_name
from .classifier import load_layers


def derive_modified_files_from_git(project_root, base_branch="main"):
    """Derive modified source files from git diff against base branch.

    Returns list of relative paths (normalized to os.sep) for .py source files,
    excluding test files. Returns empty list on git failure or no changes.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
    except (FileNotFoundError, OSError):
        return []

    files = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if not line or not line.endswith(".py"):
            continue
        basename = os.path.basename(line)
        # Exclude test files (they are targets, not inputs)
        if basename.startswith("test_") or basename.endswith("_test.py"):
            continue
        # Normalize path separators
        normalized = os.path.join(*line.split("/")) if "/" in line else line
        files.append(normalized)
    return sorted(files)


def compute_dependency_cone(modified_files, project_root):
    """Compute the dependency cone: modified files + their direct dependents.

    Uses the existing importer graph (analysis.find_importers) to find all files
    that directly import the modified modules.

    Returns a deduplicated sorted list of relative file paths.
    """
    if not modified_files:
        return []

    cone = set()
    for rel_path in modified_files:
        cone.add(rel_path)
        abs_path = os.path.join(project_root, rel_path)
        importers = find_importers(abs_path, project_root)
        for imp in importers:
            cone.add(imp)

    return sorted(cone)


def _test_imports_cone_module(test_file, cone, project_root):
    """Check if a test file imports any module in the dependency cone."""
    import ast

    abs_test = os.path.join(project_root, test_file)
    if not os.path.exists(abs_test):
        return False

    # Build set of module names from cone
    cone_modules = set()
    for f in cone:
        mod = get_module_name(os.path.join(project_root, f), project_root)
        if mod:
            cone_modules.add(mod)

    try:
        with open(abs_test, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=test_file)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for cm in cone_modules:
                    if alias.name == cm or alias.name.startswith(cm + "."):
                        return True
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for cm in cone_modules:
                    if node.module == cm or node.module.startswith(cm + "."):
                        return True
    return False


def find_in_scope_tests(dependency_cone, classifications, project_root):
    """Find test files that import modules in the dependency cone.

    Returns dict with UNIT and INTEGRATION lists of in-scope test file paths.
    """
    result = {"UNIT": [], "INTEGRATION": []}

    if not dependency_cone or not classifications:
        return result

    for entry in classifications:
        test_file = entry["file"]
        layer = entry.get("layer", "UNIT")
        if _test_imports_cone_module(test_file, dependency_cone, project_root):
            if layer in result:
                result[layer].append(test_file)

    return result


def derive_scope(project_root, modified_files, base_branch="main", source="explicit"):
    """Full scope derivation pipeline.

    Loads layer classifications, computes dependency cone, finds in-scope tests.
    Returns scope dict or None if layers.json is missing.
    """
    classifications = load_layers(project_root)
    if classifications is None:
        return None

    cone = compute_dependency_cone(modified_files, project_root)
    in_scope = find_in_scope_tests(cone, classifications, project_root)

    return {
        "modified_files": list(modified_files),
        "dependency_cone": cone,
        "in_scope_tests": in_scope,
        "source": source,
        "base_branch": base_branch,
        "created_at": time.time(),
    }


def persist_scope(project_root, scope_data):
    """Write scope to .lisa/scope.json."""
    lisa_dir = os.path.join(project_root, ".lisa")
    os.makedirs(lisa_dir, exist_ok=True)
    scope_path = os.path.join(lisa_dir, "scope.json")
    with open(scope_path, "w") as f:
        json.dump(scope_data, f, indent=2)
    return scope_path


def load_scope(project_root):
    """Load persisted scope from .lisa/scope.json. Returns dict or None."""
    scope_path = os.path.join(project_root, ".lisa", "scope.json")
    if not os.path.exists(scope_path):
        return None
    try:
        with open(scope_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def clear_scope(project_root):
    """Remove .lisa/scope.json. Returns True if removed, False if not found."""
    scope_path = os.path.join(project_root, ".lisa", "scope.json")
    if not os.path.exists(scope_path):
        return False
    os.remove(scope_path)
    return True
