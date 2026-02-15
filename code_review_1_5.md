# Code Review: Story 1.5 (Local Regression Verification)

## Summary
**Status:** 🔴 **REQUEST CHANGES**
The implementation of Story 1.5 provides the core functionality but lacks critical engineering practices required for a production-ready tool.

## Findings

### 1. [CRITICAL] Missing Automated Tests
**Severity:** High
**Location:** `scripts/lisa/analysis.py`
**Description:** The dependency analysis logic is completely untested by automated suites.
- Reliance on manual verification (`lisa analyze`) is insufficient for a core logic component.
- **Risk:** Future changes to `verification.py` or project structure could break dependency finding without warning, leading to false negatives in regression testing.
- **Requirement:** Add `tests/test_analysis.py` covering:
    - Direct imports
    - `from ... import`
    - Relative imports
    - Nested directory imports

### 2. [MAJOR] Broad Exception Swallowing
**Severity:** Medium
**Location:** `scripts/lisa/analysis.py:53` -> `except Exception:`
**Description:** The AST parser swallows `Exception` silently.
- If `ast.parse` fails due to a syntax error, that's fine.
- But if it fails due to a `MemoryError` or `PermissionError`, we should probably know.
- **Recommendation:** Catch specific `SyntaxError` or `UnicodeDecodeError`. Log others as warnings to stderr.

### 3. [MINOR] Delayed Import in Commands
**Severity:** Low
**Location:** `scripts/lisa/commands.py:83`
**Description:** `from .analysis import find_importers` is inside the `analyze_deps` function.
- Unless `analysis` is heavy (it isn't, just `ast`), this should be a top-level import to expose dependencies clearly and fail early on import errors.
- **Recommendation:** Move to top-level.

### 4. [MINOR] Hardcoded Directory Exclusions
**Severity:** Low
**Location:** `scripts/lisa/analysis.py:34`
**Description:** Exclusions for `.git`, `.lisa`, `__pycache__` are hardcoded.
- **Risk:** If a user has a `node_modules` or `venv` directory, we scan it (slow!).
- **Recommendation:** Add a default ignore list or read `.gitignore` (start with a simple `DEFAULT_IGNORES` list constant).

### 5. [UX] Working Directory Assumption
**Severity:** Medium
**Location:** `scripts/lisa/commands.py:92`
**Description:** `os.getcwd()` is passed as `project_root`.
- **Issue:** If I run `lisa analyze ../other/file.py` from a subdir, the relative path calculation in `get_module_name` might break or produce incorrect module strings if the project root logic isn't robust.
- **Recommendation:** Calculate project root relative to `lisa.sh` location or use a config value, rather than assuming `cwd` is root.

## Actions Required
1.  Implement `tests/test_analysis.py`.
2.  Refactor `analysis.py` to handle errors more specifically and use `DEFAULT_IGNORES`.
3.  Fix imports in `commands.py`.
4.  (Optional) Improve root detection.
