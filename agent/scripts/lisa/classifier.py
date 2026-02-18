"""Test Layer Classifier — assigns test files to UNIT or INTEGRATION layers.

Classification priority: custom rules > path patterns > naming conventions > markers > default (UNIT).
Integration sub-types (CONTRACT, API, PACT, COMPONENT) are tagged when detectable.
Results are persisted to .lisa/layers.json for downstream use.
"""
import ast
import json
import os
import fnmatch

from .utils import DEFAULT_IGNORES

LAYER_UNIT = "UNIT"
LAYER_INTEGRATION = "INTEGRATION"

SUBTYPE_CONTRACT = "CONTRACT"
SUBTYPE_API = "API"
SUBTYPE_PACT = "PACT"
SUBTYPE_COMPONENT = "COMPONENT"

_SUBTYPE_KEYWORDS = {
    "contract": SUBTYPE_CONTRACT,
    "api": SUBTYPE_API,
    "pact": SUBTYPE_PACT,
    "component": SUBTYPE_COMPONENT,
}


def discover_test_files(project_root):
    """Walk the project and return relative paths to all test files."""
    test_files = []
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORES]
        for f in files:
            if not f.endswith(".py"):
                continue
            if f.startswith("test_") or f.endswith("_test.py"):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, project_root)
                test_files.append(rel_path)
    return sorted(test_files)


def _match_custom_rules(rel_path, custom_rules):
    """Check if rel_path matches any custom rule. Returns (layer, subtype) or None."""
    for pattern, rule in custom_rules.items():
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            layer = rule if isinstance(rule, str) else rule.get("layer", LAYER_UNIT)
            subtype = None if isinstance(rule, str) else rule.get("subtype")
            return layer.upper(), subtype
    return None


def _match_path_patterns(rel_path, integration_path_patterns):
    """Check if the file lives under an integration path pattern."""
    normalized = rel_path.replace(os.sep, "/")
    for pattern in integration_path_patterns:
        pattern_normalized = pattern.replace(os.sep, "/")
        if not pattern_normalized.endswith("/"):
            pattern_normalized += "/"
        if normalized.startswith(pattern_normalized) or ("/" + pattern_normalized) in ("/" + normalized):
            return True
    return False


def _match_name_patterns(rel_path, integration_name_patterns):
    """Check if the filename matches an integration naming convention."""
    basename = os.path.basename(rel_path)
    for pattern in integration_name_patterns:
        if fnmatch.fnmatch(basename, pattern):
            return True
    return False


def _check_markers(rel_path, project_root):
    """Check for integration markers/decorators in the file source."""
    abs_path = os.path.join(project_root, rel_path)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    # Check for pytest marker
    if "@pytest.mark.integration" in source:
        return True

    # Check for class-level layer attribute
    try:
        tree = ast.parse(source, filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name) and target.id == "layer":
                                if isinstance(stmt.value, ast.Constant) and str(stmt.value.value).lower() == "integration":
                                    return True
    except SyntaxError:
        pass

    return False


def _detect_subtype(rel_path):
    """Detect integration sub-type from path or filename."""
    normalized = (rel_path.replace(os.sep, "/") + " " + os.path.basename(rel_path)).lower()
    for keyword, subtype in _SUBTYPE_KEYWORDS.items():
        if keyword in normalized:
            return subtype
    return None


def classify_file(rel_path, config, project_root):
    """Classify a single test file. Returns dict with layer, subtype, and method."""
    test_layers = config.get("test_layers", {})
    custom_rules = test_layers.get("custom_rules", {})
    integration_path_patterns = test_layers.get("integration_path_patterns", [])
    integration_name_patterns = test_layers.get("integration_name_patterns", [])

    # Priority 1: Custom rules
    if custom_rules:
        result = _match_custom_rules(rel_path, custom_rules)
        if result:
            layer, subtype = result
            if layer == LAYER_INTEGRATION and subtype is None:
                subtype = _detect_subtype(rel_path)
            return {"file": rel_path, "layer": layer, "subtype": subtype, "method": "custom_rule"}

    # Priority 2: Path patterns
    if _match_path_patterns(rel_path, integration_path_patterns):
        subtype = _detect_subtype(rel_path)
        return {"file": rel_path, "layer": LAYER_INTEGRATION, "subtype": subtype, "method": "path_pattern"}

    # Priority 3: Naming conventions
    if _match_name_patterns(rel_path, integration_name_patterns):
        subtype = _detect_subtype(rel_path)
        return {"file": rel_path, "layer": LAYER_INTEGRATION, "subtype": subtype, "method": "name_pattern"}

    # Priority 4: Markers/decorators
    if _check_markers(rel_path, project_root):
        subtype = _detect_subtype(rel_path)
        return {"file": rel_path, "layer": LAYER_INTEGRATION, "subtype": subtype, "method": "marker"}

    # Default: UNIT
    return {"file": rel_path, "layer": LAYER_UNIT, "subtype": None, "method": "default"}


def classify_all(project_root, config):
    """Classify all test files in the project. Returns list of classification dicts."""
    test_files = discover_test_files(project_root)
    results = []
    for rel_path in test_files:
        results.append(classify_file(rel_path, config, project_root))
    return results


def persist_layers(project_root, classifications):
    """Write classification results to .lisa/layers.json."""
    lisa_dir = os.path.join(project_root, ".lisa")
    os.makedirs(lisa_dir, exist_ok=True)
    layers_path = os.path.join(lisa_dir, "layers.json")
    with open(layers_path, "w") as f:
        json.dump(classifications, f, indent=2)
    return layers_path


def load_layers(project_root):
    """Load persisted classification from .lisa/layers.json. Returns list or None."""
    layers_path = os.path.join(project_root, ".lisa", "layers.json")
    if not os.path.exists(layers_path):
        return None
    try:
        with open(layers_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
