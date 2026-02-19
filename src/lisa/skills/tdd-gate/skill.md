---
name: enforcing-tdd
description: Enforces strict Test-Driven Development (Red-Green-Refactor) using LISA verification tools. Use when the agent is implementing a story, fixing a bug, or writing any production code that requires a failing test first.
---

# LISA TDD: The Iron Law of Context Purity

**Use when:** Implementing ANY story or  bugfix.
**Goal:** Ensure every line of code is backed by a verified failing test.

## Core Principle
**"If you didn't watch the test fail, you don't know if it tests the right thing."**

You are bound by the **Iron Law**:
> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.**
> - Write code before the test? **Delete it.**
> - Test passes immediately? **Delete it.**
> - Thinking "skip TDD just this once"? **Stop.**

## The Cycle (Red -> Green)

You must follow this cycle strictly. Do not deviate.

### 0. Check State
Before starting, check the current mode in `.lisa/state.json`.
-   **IF** `mode` is `SPIKE` or `BYPASS_TDD`:
    -   **SKIP** the verification steps below.
    -   Proceed directly to implementation.
    -   Tag all output with `[SPIKE]` or `[BYPASS]`.
-   **IF** `mode` is `NORMAL` (or missing):
    -   **PROCEED** to Step 1 (RED).

### 1. RED: Write & Verify Failure
**Goal:** Create a minimal test that fails for the *right reason*.

1.  **Write the Test:** check `task.md` for the current requirement. Write *one* minimal test case in a new or existing test file.
2.  **Verify Failure (The Gate):**
    *   You MUST run the targeted verification command:
        ```bash
        lisa verify-fail path/to/test_file.py
        ```
    *   **Verify Tool Output:**
        *   If output contains `[SUCCESS] RED State Verified` -> **PROCEED.**
        *   If output contains `[SPIKE]` or `[BYPASS]` -> **PROCEED.**
        *   If output contains `[ERROR] Test Passed!` -> **STOP.** You failed to write a failing test. Fix it.
    *   **Interactive Mode (Optional):** If you are unsure, use `lisa verify-fail <file> --interactive` to ask the human.

### 2. GREEN: Minimal Implementation
**Goal:** Make the test pass with the simplest code possible.

1.  **Write Implementation:** Write *only* enough code to pass the specific test you just verified.
    *   Do not add extra features ("YAGNI").
    *   Do not refactor yet.
    *   Do not fix other bugs yet.
2.  **Verify Success:**
    *   Run the verification command:
        ```bash
        lisa verify-pass path/to/test_file.py
        ```
    *   *If the tool fails:* Fix the code and retry.

*Note: Refactoring and Regression Verification are handled in the subsequent phase (Story 1.5).*

## Non-Functional Changes
If the task is purely non-functional (e.g., documentation, formatting):
1.  Run `lisa bypass-tdd`.
2.  Proceed with changes.
3.  Run `lisa normal` when finished.

## Verification Checklist
Before marking a task complete, verify:
- [ ] Every new function/method has a test (unless in Spike/Bypass mode).
- [ ] You ran `lisa verify-fail` and received confirmation (or Spike skip).
- [ ] You ran `lisa verify-pass` and it succeeded.
- [ ] You did not mock meaningful logic unless absolutely necessary.

## Handling Specific Scenarios

| Scenario | Action |
| :--- | :--- |
| **"Minor or very simple change** | Unless this is a text change, write the test, the butterfly effect is real |
| **"I already manually tested"** | Write the test. |
| **"Existing code has no tests"** | Add tests for the existing code first before refactor or improvement |
| **"Test matches implementation, not requirement"** | Delete test. Write test based on story, bug, or feature, not code. |
| **"Non-functional change"** | Run `lisa bypass-tdd`. |

## Emergency Bypass
If you truly believe TDD is impossible for a specific task (e.g., pure configuration, throwaway prototype), you must **ASK THE HUMAN** for permission to skip.
*   "I request permission to skip TDD for [reason]. strictness=relaxed"
