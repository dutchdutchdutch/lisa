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

## Scoped Verification (Layer Gate)

Once a scope is set, verification runs only in-scope tests for the current layer. This prevents out-of-scope failures from entering the agent's context and triggering tangent spirals.

### Layer Progression

Think step by step:

1. **Start at UNIT.** When verification runs with a scope, only in-scope UNIT tests execute first.
2. **UNIT must be clean.** If any in-scope UNIT test fails, LISA blocks advancement to INTEGRATION. Fix unit failures first.
3. **Advance to INTEGRATION.** Once UNIT is clean, run `lisa verify-layer integration` to execute only in-scope INTEGRATION tests.
4. **Layer status is tracked.** Each layer is in one of three states: `CLEAN` (all in-scope tests pass), `FAILING` (N failures), or `NOT_RUN`.

### Layer Status Schema

Layer status is persisted in `.lisa/scope.json` alongside the scope data:

```json
{
  "layer_status": {
    "UNIT": "CLEAN",
    "INTEGRATION": "NOT_RUN"
  }
}
```

### Backwards Compatibility

- If a specific test file is passed to `lisa verify-fail` or `lisa verify-pass`, the explicit file is always allowed (existing behavior preserved).
- If the explicit file is outside the current story scope, a warning is emitted: "file is outside story scope."

### No-Scope Fallback

- If no scope has been set and `lisa verify-layer` is called without a specific file, LISA warns: "No scope set. Use 'lisa scope' to set scope first." and does NOT run tests. This is a fail-safe — running all tests without scope defeats the purpose.

## Out-of-Scope Failure Deferral

When `lisa verify-layer` runs, it executes **all** classified tests for the layer (not just in-scope tests). Failures are then classified:

- **IN_SCOPE**: The test file is in the scope's `in_scope_tests` for the current layer. These failures **block** the layer and must be fixed.
- **OUT_OF_SCOPE**: The test file is classified for the layer but is **not** in the current story's scope. These failures are **deferred** — they do not block the layer.

### Agent Instructions for Deferred Failures

Think step by step:

1. **Only fix in-scope failures.** When `verify-layer` reports deferred failures, note them but do **not** fix them. They are outside the current story's scope.
2. **Do not chase tangents.** Deferred failures exist to prevent the Tangent Spiral Tax. Investigating or fixing them burns tokens on unrelated work.
3. **Check the deferral record.** Deferred failures are persisted in `.lisa/scope.json` under `deferred_failures` for each layer. They appear in confidence reports (Story 8.3) as "Known deferred failures."

### Deferral Record Schema

Deferred failures are persisted alongside scope data in `.lisa/scope.json`:

```json
{
  "deferred_failures": {
    "UNIT": ["tests/test_unrelated.py"],
    "INTEGRATION": []
  }
}
```

### Fallback Behavior

- If `layers.json` is missing, `verify-layer` falls back to running only in-scope tests (no deferral classification possible).
- If no scope is set, `verify-layer` warns and does not run (unchanged behavior).

## Warnings

- If no modified files are found from version control, warn the user and do not set scope.
- If the layer classification is missing, warn and suggest running `lisa classify --all`.
- If no in-scope tests are found, warn — the modified code may lack test coverage.
