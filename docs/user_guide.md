# LISA User Guide

This guide provides detailed instructions on how to use LISA (Layered Isolated Scoped Agent) for your daily development workflow.

## Installation

LISA is designed as a zero-dependency drop-in tool.

1.  **Copy Files**:
    *   Copy `lisa.sh` to your project root.
    *   Copy the `scripts/lisa` directory to your project's `scripts/` directory.
2.  **Install Dependencies**:
    *   `pip install tiktoken` (required for accurate token counting).
3.  **Prerequisites**:
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
  "context_check_interval": 600,
  "hooks_mode": "auto",
  "lifecycle_hooks": {
    "story-kickoff": [],
    "story-in-dev": ["lisa turns"],
    "story-test": [],
    "story-complete": ["lisa polish"],
    "context-reset": ["lisa checkpoint"]
  }
}
```

**Configuration Keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `strictness` | `"strict"` | TDD enforcement level |
| `spike_mode_allowed` | `true` | Whether spike mode is permitted |
| `context_limit` | `20000` | Token threshold for context alerts |
| `context_check_interval` | `600` | Seconds between lazy context checks |
| `hooks_mode` | `"auto"` | `"auto"` runs remediation automatically; `"interactive"` prompts first |
| `lifecycle_hooks` | (see above) | Map of lifecycle events to LISA commands |

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

### `lisa turns`

**Purpose**: Manages the agentic turn counter. Used by the Turn Watchdog to track reasoning cycles and detect logic drift.

**Usage**:

```bash
./lisa.sh turns          # Report current turn count
./lisa.sh turns 7        # Set turn to 7 (agent knows its own turn)
```

*   **Report mode** (no args): Shows current turn count.
*   **Set mode** (`lisa turns <N>`): Sets the turn counter to the exact number — the agent always knows what turn it's on, so it sets rather than blindly incrementing.
*   The turn count is displayed in `lisa context` output.
*   **Turn 12 (Goldfish Threshold):** Triggers a "Logic Alignment Check".
*   **Turn 20+ (Compaction Recovery):** Recommends a "Grounding Snapshot".

### `lisa polish`

**Purpose**: Loads the Polish Pass skill protocol for epic-level quality auditing. Runs a multi-phase scan for duplicate code, naming inconsistencies, error handling gaps, magic values, and performance/security issues.

**Usage**:

```bash
./lisa.sh polish
```

*   Reads and outputs `skills/polish-pass/skill.md`.
*   Follow the printed protocol to execute the Polish Pass.
*   Best used at the end of an epic or sprint.

### `lisa hooks <event>`

**Purpose**: Triggers lifecycle hooks for a given event. Hooks are configured in `.lisa/config.json` and execute LISA commands at key story lifecycle boundaries.

**Usage**:

```bash
./lisa.sh hooks story-complete
```

**Valid Events:**

| Event | Default Hook | Description |
|-------|-------------|-------------|
| `story-kickoff` | (none) | When a story starts |
| `story-in-dev` | `lisa turns` | Each development turn |
| `story-test` | (none) | After green phase |
| `story-complete` | `lisa polish` | Story marked complete (also runs health + remediation) |
| `context-reset` | `lisa checkpoint` | After context reset |

*   **`story-complete`** uses a special orchestrator: runs polish, context health check, and conditional remediation (context-curator, externalizer, session-management) based on health status.
*   **Fail-Open:** Hook failures are logged as warnings and never block workflow.

### `lisa version`

**Purpose**: Detailed version information.

**Usage**:

```bash
./lisa.sh version
```

## Troubleshooting

-   **"python3 not found"**: Ensure Python is installed and in your PATH.
-   **"Could not determine project root"**: Ensure `lisa.sh` is in the root of your project and you are running it from there or a subdirectory.
-   **"Context Limit Exceeded"**: Run `lisa reset` to archive and clear your session.
-   **"[🔴] Context Red"**: Your workspace is too large. Clean up files or run `lisa reset`.
-   **"Please fix permissions on .lisa/"**: Check file permissions on the `.lisa/` directory. LISA requires read/write access.
-   **"Polish Pass skill not found"**: Ensure `skills/polish-pass/skill.md` exists. Install the skill or create it manually.
-   **"Unknown lifecycle event"**: Check valid events with `lisa hooks` (no arguments).
