---
name: LISA Refactor Gate
description: Enforces code quality and prevents regressions by guiding the agent through a structured Refactor and Impact Verification process.
---

# LISA Refactor Gate: Quality & Stability

**Use when:** A task implementation is complete and tests are Green.
**Goal:** Improve code quality and verify no regressions in dependent modules.

## Phase 1: The Refactor Loop

**Principle:** "Make it work, then make it right."
Now that the tests are Green, you must look for opportunities to improve the code *without changing behavior*.

1.  **Analyze Code:** Look for:
    *   Duplication (DRY violations)
    *   Complex logic (High Cyclomatic Complexity)
    *   Unclear naming
    *   Magic numbers/strings
    *   Inefficient algorithms

2.  **Refactor:** Apply changes to improve the above.
    *   *Constraint:* Do not change the external behavior.

3.  **Verify:** After *every* significant refactor step, run the verification command:
    ```bash
    lisa verify-pass path/to/current_test_file.py
    ```
    *   If it fails, **UNDO** and fix the refactor.

## Phase 2: Impact Zone Verification

**Principle:** "Don't break the neighbors."
Changes in one file can break others. You must verify dependencies.

### If scope is set (lisa scope was run):

Use scoped layer verification — it handles dependency analysis, scope filtering, and failure deferral automatically.

1.  **Run Unit Layer:**
    ```bash
    lisa verify-layer unit
    ```
    *   Runs only in-scope unit tests. Out-of-scope failures are deferred (logged but do not block).
    *   If in-scope failures exist, fix them before proceeding.

2.  **Run Integration Layer:**
    ```bash
    lisa verify-layer integration
    ```
    *   Blocked if the unit layer is not clean (layer progression gate).
    *   Runs only in-scope integration tests with the same deferral rules.
    *   If in-scope failures exist, fix at the integration layer — do not revisit unit code unless a unit test also fails.

### If no scope is set (fallback):

1.  **Analyze Dependencies:**
    *   Run the analysis tool to find files that import your modified code:
        ```bash
        lisa analyze path/to/modified_file.py
        ```
    *   This will output a list of dependent files.

2.  **Identify Dependent Tests:**
    *   For each dependent file found, identify its corresponding test file.
    *   List these tests as the "Impact Suite".

3.  **Human Approval (Context Cost Check):**
    *   **STOP** and ask the Human Partner:
        > "I have identified the following dependent tests (Impact Suite): [List tests]. Should I run them to verify regression?"
    *   Wait for approval.

4.  **Verify Impact:**
    *   If approved, run `lisa verify-pass` on each approved dependent test.
    *   **If a dependent test fails:**
        *   **DO NOT** change the test (unless the API change was intentional and approved).
        *   **FIX** your implementation to restore compatibility.

## Checklist

- [ ] Refactored for clarity and simplicity.
- [ ] Requirements test still PASSES.
- [ ] Impact verified (scoped layer verification OR manual impact suite).
- [ ] All in-scope tests PASS.
