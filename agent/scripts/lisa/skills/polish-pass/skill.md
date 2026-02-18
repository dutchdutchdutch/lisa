---
name: Polish Pass
description: Systematic epic-level code quality sweep that detects and resolves cross-cutting issues accumulated across multiple stories.
---

# Polish Pass: Epic Hygiene Sweep

**Use when:** An epic or sprint is complete (all stories done), before starting the next epic.
**Goal:** Catch and fix cross-cutting quality issues that individual story reviews miss.

## Core Principle
**"Each story is a brick. The polish pass checks the wall."**

Individual code reviews catch per-story issues. But across an entire epic, patterns drift:
- Utility code gets duplicated across stories
- Naming conventions diverge between sessions
- Error handling approaches become inconsistent
- Magic values accumulate unchecked
- Code migrates to the wrong structural boundaries

The Polish Pass is a **whole-codebase audit** that treats the *set of stories* as a single unit of work.

## Invocation

The skill can be triggered by an agent or user via CLI:

```bash
lisa polish
```

Or by directly referencing this skill in an agent conversation:
> "Run the Polish Pass skill on the current project."

## Trigger
Activate this skill when:
1. All **functional, code, and skill** stories in an epic are marked **Done** — documentation-only stories (e.g., README updates, architecture docs) may still be pending.
2. A sprint retrospective identifies quality debt.
3. The Tech Lead explicitly requests a polish round.
4. The agent or user runs `lisa polish`.

## The Polish Protocol

Think step by step. Execute each phase in order.

### Phase 1: Reconnaissance
**Goal:** Understand the project's standards before auditing.

1.  **Load Architecture:** Read the project's architecture document to understand:
    - Established coding conventions and naming rules
    - Project structure and boundary definitions
    - Error handling patterns and policies
    - Testing standards and frameworks
2.  **Load Config:** Check the project's configuration files for any project-specific settings or overrides.
3.  **Identify Scope:** List all source files and test files in the project.

### Phase 2: Duplicate Code Audit
**Goal:** Find and consolidate repeated patterns.

1.  **Scan** all source files for repeated code patterns:
    - Configuration loading boilerplate
    - Path resolution / project root detection
    - Error handling try/except blocks
    - Logging / output formatting
2.  **Consolidate** duplicates into shared utility functions.
3.  **Update** all call sites to use the consolidated helpers.
4.  **Verify** tests still pass after each consolidation.

### Phase 3: Magic Values & Constants
**Goal:** Eliminate hardcoded strings and numbers.

1.  **Scan** for magic values:
    - Repeated string literals (config keys, status names, error messages)
    - Hardcoded numeric thresholds or limits
    - Inline URLs, paths, or identifiers
2.  **Extract** magic values into named constants or configuration.
3.  **Update** all references to use the constants.

### Phase 4: Naming & Style Consistency
**Goal:** Ensure uniform naming across all modules.

1.  **Audit** naming conventions against the project's architecture:
    - Functions, variables, constants, classes
    - CLI commands and subcommands
    - File names and module names
2.  **Fix** any deviations from the established convention.

### Phase 5: Error Handling Consistency
**Goal:** Ensure all modules follow the same error handling approach.

1.  **Audit** each module for error handling pattern compliance:
    - Does it follow the project's error reporting pattern?
    - Does it handle edge cases consistently with other modules?
    - Does output use the project's standard logging/output mechanism?
2.  **Fix** any modules that deviate from the established patterns.

### Phase 6: Performance & Security Scan
**Goal:** Catch low-hanging performance and security issues.

1.  **Performance:** Look for:
    - Redundant file reads or repeated I/O in loops
    - N+1 patterns (loading resources one at a time instead of batch)
    - Missing caching where results are recomputed unnecessarily
2.  **Security:** Look for:
    - Hardcoded credentials, API keys, or secrets
    - Unsanitized user input passed to file operations or shell commands
    - Overly broad file permissions or directory traversal risks
3.  **Fix** or flag any issues found.

### Phase 7: Project Structure Verification
**Goal:** Ensure code is in the right place.

1.  **Verify** that the project structure matches the architecture definition:
    - No logic code in data/config directories
    - No runtime state in source code directories
    - Correct import patterns (relative vs absolute)
2.  **Fix** any structural violations.

### Phase 8: Regression Gate
**Goal:** Prove that polish changes preserved all behavior.

#### If scope is set (lisa scope was run):

Use scoped layer verification — only in-scope tests run, out-of-scope failures are deferred.

1.  **Run Unit Layer:**
    ```bash
    lisa verify-layer unit
    ```
2.  **Run Integration Layer** (blocked if unit is not clean):
    ```bash
    lisa verify-layer integration
    ```
3.  **If any in-scope test fails:** Fix the regression immediately. Do not proceed until clean.
4.  **Report** the final layer status (`lisa layer-status`).

#### If no scope is set (fallback):

1.  **Run** the full regression test suite.
2.  **If any test fails:** Fix the regression immediately. Do not proceed until green.
3.  **Report** the final test results.

## Checklist

- [ ] Architecture document reviewed for project conventions.
- [ ] Duplicate code patterns identified and consolidated.
- [ ] Magic values extracted into constants or config.
- [ ] Naming conventions audited and consistent.
- [ ] Error handling patterns audited and consistent.
- [ ] Performance and security scan completed.
- [ ] Project structure verified against architecture boundaries.
- [ ] Full regression suite passes (0 failures).

## Output

When complete, provide a summary:

> **[Polish Pass Complete]**
> - **Duplicates Found:** X patterns consolidated
> - **Magic Values:** X constants extracted
> - **Naming Fixes:** X items corrected
> - **Error Handling Fixes:** X modules aligned
> - **Perf/Security Issues:** X found and addressed
> - **Structure Issues:** X violations corrected
> - **Regression Suite:** PASS (N tests, 0 failures)
