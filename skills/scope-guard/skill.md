# Scope Derivation (The Scope Guard)

## Purpose

Derive the test scope for the current story from modified files, so that test execution is restricted to only relevant tests and the agent cannot wander into unrelated code. This prevents the **Tangent Spiral Tax** — the cost of chasing failures in unrelated modules.

## How It Works

Think step by step:

1. **Identify modified files.** Either accept an explicit file list or derive it from version control (git diff against the base branch).
2. **Compute the dependency cone.** For each modified source file, use the importer graph to find all files that directly depend on it. The dependency cone = modified files + their direct dependents.
3. **Map to tests.** Cross-reference the dependency cone with the persisted test layer classification (`.lisa/layers.json`). A test is **in-scope** if it imports any module in the dependency cone.
4. **Group by layer.** Present in-scope tests grouped by layer (UNIT, INTEGRATION) for downstream use by the layer gate.
5. **Persist the scope.** Write the scope to `.lisa/scope.json` so that verification commands, layer gates, and the confidence report can reference it.

## Scope State Schema

The scope is persisted to `.lisa/scope.json`:

```json
{
  "modified_files": ["scripts/lisa/foo.py", "scripts/lisa/bar.py"],
  "dependency_cone": ["scripts/lisa/foo.py", "scripts/lisa/bar.py", "scripts/lisa/baz.py"],
  "in_scope_tests": {
    "UNIT": ["tests/test_foo.py", "tests/test_bar.py"],
    "INTEGRATION": ["tests/integration/test_flow.py"]
  },
  "source": "git_diff",
  "base_branch": "main",
  "created_at": 1700000000.0
}
```

## Agent Instructions

When asked to derive scope:

1. If no file list is provided, run `git diff --name-only <base_branch>...HEAD` to get modified files.
2. Filter to only source files (`.py`) — test files are targets, not inputs.
3. For each modified source file, call the importer graph to find direct dependents.
4. Load the layer classification from `.lisa/layers.json`. If no classification exists, run `lisa classify --all` first.
5. Match: a test file is in-scope if it directly imports any module in the dependency cone.
6. Persist the scope and display the results.

## Clearing Scope

Run `lisa scope --clear` to remove the scope and return to unscoped operation. This is useful when starting a new story or when scope is no longer relevant.

## Warnings

- If no modified files are found from version control, warn the user and do not set scope.
- If the layer classification is missing, warn and suggest running `lisa classify --all`.
- If no in-scope tests are found, warn — the modified code may lack test coverage.
