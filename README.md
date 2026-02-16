# LISA - Layered Isolated Scoped Agent

LISA is a context governance tool for AI-assisted development. It enforces a Red-Green-Refactor loop locally, manages context window health, and prevents premature commits without tests.

## Installation

1.  Copy `lisa.sh` to your project root.
2.  Copy `scripts/lisa` to `scripts/lisa`.

For detailed installation instructions, see the [User Guide](docs/user_guide.md#installation).

## Usage

**For detailed command usage, please refer to the [User Guide](docs/user_guide.md).**

Run LISA commands via the shell wrapper:

```bash
./lisa.sh [command]
```

## Modules & Skills

LISA is built on a set of core skills that enforce development best practices.

### `tdd-gate`
Enforces the **Red-Green-Refactor** cycle. The TDD Gate prevents implementation code from being written until a failing test (Red State) has been verified.

### `refactor-gate`
Ensures code quality and regression testing explicitly during the Refactor phase, preventing regressions in existing functionality.

### `refactor-gate`
Enforces code quality and regression testing explicitly during the Refactor phase, preventing regressions in existing functionality.

### Spike Mode & Bypasses
LISA supports "Spike Mode" (`lisa spike`) and "TDD Bypass" (`lisa bypass-tdd`) to temporarily disengage safety harnesses for prototyping or non-functional work.

### Context Governance
LISA proactively monitors your prompt context window usage.
-   **Traffic Light:** Every command output includes a health indicator (e.g., `[🟢]`, `[🟡]`, `[🔴]`).
-   **Check Context:** Run `lisa context` to see detailed token usage stats.
-   **Context Analytics:** 
    -   `lisa context status`: View current system activity.
    -   `lisa context size`: View token and file counts.
    -   `lisa context health`: View saturation and health metrics.
-   **Session Reset:** Run `lisa reset` to archive the current session and start fresh.
-   **State Checkpoint:** Run `lisa checkpoint` (formerly `externalize`) to validate your external state artifact (`todo.md`) is present and up-to-date.

## Configuration

LISA supports hierarchical configuration (User > Project). See the [User Guide](docs/user_guide.md#configuration) for details.

## State Management

LISA maintains its state in `.lisa/state.json`. It uses file locking to ensure state integrity across multiple concurrent shell sessions.
