# LISA User Guide

This guide provides detailed instructions on how to use LISA (Layered Isolated Scoped Agent) for your daily development workflow.

## Installation

LISA is designed as a zero-dependency drop-in tool.

1.  **Copy Files**:
    *   Copy `lisa.sh` to your project root.
    *   Copy the `scripts/lisa` directory to your project's `scripts/` directory.
2.  **Prerequisites**:
    *   Python 3.8+ installed and available as `python3` in your PATH.
    *   A POSIX-compliant shell (Bash/Zsh).

## Configuration

LISA uses a hierarchical configuration system.

1.  **Global User Config**: `~/.lisa/config.json` (apply to all your projects).
2.  **Project Config**: `./.lisa/config.json` (overrides user config for this specific project).

**Example `config.json`:**

```json
{
  "strictness": "strict",
  "spike_mode_allowed": true,
  "context_limit": 20000,
  "context_check_interval": 600
}
```

## Commands

### `lisa verify-fail <test_file>`

**Purpose**: Verifies that a new test fails as expected (RED State). This is the "TDD Audit".

**Usage**:

```bash
./lisa.sh verify-fail tests/test_my_feature.py
```

*   **Automated Mode (Default)**: Runs the test.
    *   If the test **FAILS**: Success (Exit Code 0).
    *   If the test **PASSES**: Error (Exit Code 1). You must fix the test to fail before implementing logic.
*   **Interactive Mode**:
    *   Use `--interactive` to pause for confirmation before running the check.
    *   `./lisa.sh verify-fail tests/test_my_feature.py --interactive`

### `lisa verify-pass <test_file>`

**Purpose**: Verifies that a test passes (GREEN State). Run this after implementing your feature.

**Usage**:

```bash
./lisa.sh verify-pass tests/test_my_feature.py
```

*   Runs the test normally.
*   If the test **PASSES**: Success (Cycle Complete).
*   If the test **PASSES**: Success (Cycle Complete).
*   If the test **FAILS**: Error. You need to fix your implementation.

### `lisa spike`

**Purpose**: Disengages the "Safety Harness" (TDD enforcement), allowing you to prototype rapidly without verification blocks.

**Usage**:

```bash
./lisa.sh spike
```

*   Sets mode to `SPIKE`.
*   All consequent `verify-fail` or `verify-pass` commands will **SKIP** verification and exit with success, logging a warning.
*   Useful for: Experimental coding, learning new APIs, or throwing away code later.

### `lisa normal`

**Purpose**: Re-engages the Safety Harness (TDD enforcement). Run this when you are done spiking or bypassing.

**Usage**:

```bash
./lisa.sh normal
```

*   Sets mode to `NORMAL`.
*   Restores strict TDD enforcement.

### `lisa bypass-tdd`

**Purpose**: Skips TDD enforcement for the current task. Intended for **non-functional changes** (docs, formatting, config) where TDD is overhead.

**Usage**:

```bash
./lisa.sh bypass-tdd
```

*   Sets mode to `BYPASS_TDD`.
*   Similar to Spike Mode, but indicates a deliberate choice for non-functional work rather than hacking.
*   Remember to run `lisa normal` when finished.

### `lisa analyze <file_path>`

**Purpose**: Performs Impact Analysis to find other files that depend on the target file. Use this before refactoring or to understand what tests to run.

**Usage**:

```bash
./lisa.sh analyze scripts/lisa/utils.py
```

*   **Output**: Lists all files in the project that import the target file.
*   **Note**: Requires you to be in the project root or a subdirectory of a LISA project.

### `lisa context`

**Purpose**: specific Analysis of your current workspace's token usage. Use this to check if you are approaching the context window limit.

**Usage**:

```bash
./lisa.sh context
```

*   **Output includes**:
    *   **Traffic Light**: `[🟢]`, `[🟡]`, or `[🔴]` indicating health.
    *   **Token Count**: Estimated tokens in the workspace.
    *   **Usage %**: Percentage of the configured `context_limit`.
*   **Automatic Checks**: LISA automatically checks this in the background (Lazy Check) and updates the Traffic Light on every command.

### `lisa reset`

**Purpose**: Archives the current session and resets the context state. Use this when the traffic light turns **RED** or you want to start a fresh task without losing history.

**Usage**:

```bash
./lisa.sh reset
```

*   **Archival**: Copies the current `.lisa/state.json` and recent logs to `.lisa/archive/{timestamp}/`.
*   **Reset**: Clears the active `state.json` to default (Green/Idle).
*   **Result**: You are ready to start a new task with a clean slate.

### `lisa version`

**Purpose**: detailed version information.

**Usage**:

```bash
./lisa.sh version
```

## Troubleshooting

-   **"python3 not found"**: Ensure Python is installed and in your PATH.
-   **"Could not determine project root"**: Ensure `lisa.sh` is in the root of your project and you are running it from there or a subdirectory.
-   **"Context Limit Exceeded"**: Run `lisa reset` to archive and clear your session.
-   **"[🔴] Context Red"**: Your workspace is too large. Clean up files or run `lisa reset`.
