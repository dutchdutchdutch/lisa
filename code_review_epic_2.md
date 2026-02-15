# Adversarial Code Review - Epic 2

**Reviewer:** LISA AI (Adversarial Mode)
**Target:** Epic 2 Implementation (Stories 2.1 - 2.5)
**Status:** **CHANGES REQUESTED**

## Summary
The implementation satisfies the functional requirements of Epic 2 (Spike/Bypass modes), but exhibits **Architectural Smells** and **Safety Risks** that should be addressed before considering it "Production Ready".

## Critical Issues

### 1. Magic String Duplication (Maintenance/Safety Risk)
-   **Location:** `scripts/lisa/commands.py` (Lines 26, 76, 121, 138, 156, 174)
-   **Issue:** The string literals `"SPIKE"`, `"NORMAL"`, and `"BYPASS_TDD"` are scattered throughout the codebase.
-   **Risk:** Typo-proneness. If one string is misspelled (e.g., `"ByPASS_TDD"`), the logic silently fails to skip verification, potentially blocking a user during a critical fix.
-   **Recommendation:** Centralize these states in a `LISA_MODES` constant or Enum in `state.py`.

### 2. Duplicated logic in Verification Commands (DRY Violation)
-   **Location:** `verify_fail` and `verify_pass`
-   **Issue:** The logic to load state, check mode, and print warning is copy-pasted.
-   **Risk:** If we add a new mode (e.g., "STRICT_TDD"), we have to update multiple places.
-   **Recommendation:** Extract `check_mode_bypass()` decorator or helper function.

## Nitpicks

-   **Output Formatting:** `disable_spike` prints `"MODE: NORMAL"` twice (Line 159-160).
-   **Permission Handling:** The tool crashes with a raw `PermissionError` instead of a user-friendly "Please fix permissions on .lisa/" message. This violates **NFR3 (Fail-Open/Warn)**.

## Story Validation

| Story | Status | Notes |
| :--- | :--- | :--- |
| **2.1 Spike Mode** | **PASS** | `lisa spike` works. |
| **2.2 Verify Bypass** | **PASS** | Verification skipped in Spike mode. |
| **2.3 Dirty Tagging** | **PASS** | Output tagged `[SPIKE]`. |
| **2.4 Bypass TDD** | **PASS** | `lisa bypass-tdd` works. |
| **2.5 Documentation** | **PASS** | Docs updated. |

## Recommendation
**Approve with Comments.** The feature works, but refactoring the Magic Strings and fixing the double-print bug is highly recommended immediately. The Permission Error handling should be a follow-up task.
