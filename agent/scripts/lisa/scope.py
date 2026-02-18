"""Scope Derivation — derives test scope from modified files (Story 7.2).

Computes the dependency cone for modified source files, maps to in-scope
test files grouped by layer, and persists the scope for downstream use.
"""
import ast
import json
import os
import subprocess
import time

from .analysis import find_importers, get_module_name
from .classifier import load_layers, LAYER_UNIT, LAYER_INTEGRATION

# Layer status values (used in scope.json layer_status and by verify-layer)
STATUS_CLEAN = "CLEAN"
STATUS_FAILING = "FAILING"
STATUS_NOT_RUN = "NOT_RUN"


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


def _test_imports_cone_module(test_file, cone_modules, project_root):
    """Check if a test file imports any module in the dependency cone."""
    abs_test = os.path.join(project_root, test_file)
    if not os.path.exists(abs_test):
        return False

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
    result = {LAYER_UNIT: [], LAYER_INTEGRATION: []}

    if not dependency_cone or not classifications:
        return result

    # optimization: pre-calculate cone modules once
    cone_modules = set()
    for f in dependency_cone:
        mod = get_module_name(os.path.join(project_root, f), project_root)
        if mod:
            cone_modules.add(mod)

    for entry in classifications:
        test_file = entry["file"]
        layer = entry.get("layer", LAYER_UNIT)
        if _test_imports_cone_module(test_file, cone_modules, project_root):
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


# --- Layer Gate (Story 7.3) ---

LAYER_ORDER = [LAYER_UNIT, LAYER_INTEGRATION]


def get_layer_status(project_root):
    """Get current layer status from scope. Returns dict or None if no scope."""
    scope = load_scope(project_root)
    if scope is None:
        return None
    status = scope.get("layer_status", {})
    return {
        LAYER_UNIT: status.get(LAYER_UNIT, STATUS_NOT_RUN),
        LAYER_INTEGRATION: status.get(LAYER_INTEGRATION, STATUS_NOT_RUN),
    }


def update_layer_status(project_root, layer, status, failure_count=None):
    """Update the status for a specific layer in the persisted scope."""
    scope = load_scope(project_root)
    if scope is None:
        return
    if "layer_status" not in scope:
        scope["layer_status"] = {}
    scope["layer_status"][layer] = status

    if "layer_failure_counts" not in scope:
        scope["layer_failure_counts"] = {}
    if failure_count is not None:
        scope["layer_failure_counts"][layer] = failure_count
    elif status == STATUS_CLEAN:
        scope["layer_failure_counts"][layer] = 0

    persist_scope(project_root, scope)


def get_layer_failure_counts(project_root):
    """Get failure counts for each layer. Returns dict or None if no scope."""
    scope = load_scope(project_root)
    if scope is None:
        return None
    return scope.get("layer_failure_counts", {})


def get_in_scope_tests_for_layer(project_root, layer):
    """Get the in-scope test files for a specific layer.

    Returns list of test file paths, or None if no scope is set.
    """
    scope = load_scope(project_root)
    if scope is None:
        return None
    in_scope = scope.get("in_scope_tests", {})
    return in_scope.get(layer, [])


def check_layer_advancement(project_root, target_layer):
    """Check if the agent can advance to the target layer.

    Returns (allowed: bool, reason: str). reason is empty if allowed.
    UNIT is always allowed. INTEGRATION requires UNIT to be CLEAN (or empty).
    """
    scope = load_scope(project_root)
    if scope is None:
        return False, "No scope is set. Use 'lisa scope' to set scope first."

    if target_layer == LAYER_UNIT:
        return True, ""

    if target_layer == LAYER_INTEGRATION:
        # If no UNIT tests in scope, nothing to block on
        in_scope = scope.get("in_scope_tests", {})
        unit_tests = in_scope.get(LAYER_UNIT, [])
        if not unit_tests:
            return True, ""

        status = scope.get("layer_status", {})
        unit_status = status.get(LAYER_UNIT, STATUS_NOT_RUN)
        if unit_status == STATUS_CLEAN:
            return True, ""
        failure_counts = scope.get("layer_failure_counts", {})
        count = failure_counts.get(LAYER_UNIT, 0)
        if count > 0:
            count_detail = f", {count} in-scope failure{'s' if count != 1 else ''}"
        else:
            count_detail = ""
        return False, f"UNIT layer is not clean (status: {unit_status}{count_detail}). Resolve unit failures before integration testing."

    return False, f"Unknown layer: {target_layer}"


def is_file_in_scope(project_root, test_file):
    """Check if a specific test file is within the current scope.

    Returns True if in scope, False if out of scope, None if no scope is set.
    """
    scope = load_scope(project_root)
    if scope is None:
        return None
    in_scope = scope.get("in_scope_tests", {})
    all_in_scope = in_scope.get(LAYER_UNIT, []) + in_scope.get(LAYER_INTEGRATION, [])
    return test_file in all_in_scope


# --- Out-of-Scope Failure Deferral (Story 7.4) ---


def get_all_tests_for_layer(project_root, layer):
    """Get every classified test file for a layer from layers.json.

    Returns list of test file paths, or None if layers.json is missing.
    """
    classifications = load_layers(project_root)
    if classifications is None:
        return None
    return [entry["file"] for entry in classifications if entry.get("layer") == layer]


def record_deferred_failures(project_root, layer, failures):
    """Persist out-of-scope failures into scope.json under deferred_failures."""
    scope = load_scope(project_root)
    if scope is None:
        return
    if "deferred_failures" not in scope:
        scope["deferred_failures"] = {}
    scope["deferred_failures"][layer] = list(failures)
    persist_scope(project_root, scope)


def get_deferred_failures(project_root):
    """Retrieve deferred failures from scope.json.

    Returns dict of {layer: [file, ...]} or None if no scope is set.
    """
    scope = load_scope(project_root)
    if scope is None:
        return None
    return scope.get("deferred_failures", {})


# --- UI Test Handoff (Story 7.6) ---


def record_ui_handoff(project_root):
    """Record that the UI test handoff script has been generated."""
    scope = load_scope(project_root)
    if scope is None:
        return
    scope["ui_handoff_status"] = "script_generated"
    persist_scope(project_root, scope)


def get_ui_handoff_status(project_root):
    """Get the UI handoff status. Returns status string or None if no scope."""
    scope = load_scope(project_root)
    if scope is None:
        return None
    return scope.get("ui_handoff_status", "pending")
