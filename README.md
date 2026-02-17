# LISA - Layered Isolated Scoped Agent

LISA is a context governance tool for AI-assisted development. It enforces a Red-Green-Refactor loop locally, manages context window health, and prevents premature commits without tests.

Coding agents in complex domains lack enforced boundaries — a gap that disproportionately impacts vibe coders and less experienced developers. Best practices like keeping contexts small are well-documented but easily forgotten once project complexity scales.

Without hard constraints, agents treat accessibility as permission: running full test suites or noisy UI simulations on every turn, burning context on unrelated failures, and confidently solving the wrong problem. The result is lengthy and expensive debugging spirals that compound rather than converge.


#### Lisa's Role is complementary

Lisa is a governance layer on top of Claude Code (or other coding agents), not a replacement.

- **Claude Code** handles mechanical compression when the context window fills (~83.5% capacity).
- **Lisa** adds structured discipline: tracking turns, detecting drift, checkpointing state *before* compaction can lose it, and archiving sessions for post-mortems.

Lisa treats context as an economic resource — monitoring ROI per token — rather than a technical buffer that gets silently recycled. It addresses a failure mode that compaction alone can't: logic drift that occurs even with plenty of tokens remaining.

#### What Lisa Does Differently

Claude Code's compaction asks the model to summarize well. Lisa defines explicit rules for what survives, what gets dropped, and what gets pinned — then separately writes critical state to disk so a lossy summary can't kill the session.

The Externalizer skill in particular has no Claude Code equivalent. It addresses a concrete failure mode: compaction summaries that silently drop important context with no way to recover it.


## Installation

1.  Copy `lisa.sh` to your project root.
2.  Copy `scripts/lisa` to `scripts/lisa`.
3.  Install dependencies: `pip install tiktoken` (without tiktoken, LISA falls back to characters/4 as a proxy).

For detailed installation instructions, see the [User Guide](docs/user_guide.md#installation).

## Usage

**For detailed command usage, please refer to the [User Guide](docs/user_guide.md).**

Run LISA commands via the shell wrapper:

```bash
./lisa.sh [command]
```

## Lifecycle Stages

LISA monitors along common story or task lifecycle stages. Each stage can trigger hooks and skills automatically.

| Stage | Default Hook / Skill | Description |
|-------|---------------------|-------------|
| **`story-kickoff`** | *(none)* | Story begins. Configurable entry point for initializing context or loading state. |
| **`story-in-dev`** | `lisa turns` → **Turn Watchdog** | Each development turn. Tracks reasoning cycles; fires drift warnings at turn 12 (Goldfish Threshold) and compaction alerts at turn 20+. |
| **`story-test`** | **Refactor Gate** | Tests are green. Runs a structured refactor loop — improve code quality without changing behavior, then verify impact on dependent modules via `lisa analyze`. |
| **`story-complete`** · Step 1 | `lisa polish` → **Polish Pass** | Runs a multi-phase quality scan: duplicate code, naming audit, error handling gaps, magic values, and performance/security review. |
| **`story-complete`** · Step 2 | `lisa context` → **Context Health Check** | Measures token usage via **tiktoken** against your configured limit. Reports a traffic light (🟢🟡🔴) plus turn-count drift analysis. |
| **`story-complete`** · Step 3 | Auto-remediation (if 🟡 or 🔴) | **Context Curator** — compress and summarize conversation history. **Checkpoint** — pin critical state to `todo.md`. **Session Management** — recommend `lisa reset` to archive and start fresh when context is saturated. |
| **`context-reset`** | `lisa checkpoint` → **Checkpoint** | After `lisa reset`. Validates that the external state artifact (`todo.md`) exists and is fresh. |

> Hooks are configurable via `lifecycle_hooks` in `.lisa/config.json`. All hooks are **fail-open** — failures log warnings but never block workflow.

## Modules & Skills

LISA is built on a set of core skills that enforce development best practices.

### `tdd-gate`
Enforces the **Red-Green-Refactor** cycle. The TDD Gate prevents implementation code from being written until a failing test (Red State) has been verified.

### `refactor-gate`
Ensures code quality and regression testing explicitly during the Refactor phase, preventing regressions in existing functionality.

### Spike Mode & Bypasses
LISA supports "Spike Mode" (`lisa spike`) and "TDD Bypass" (`lisa bypass-tdd`) to temporarily disengage safety harnesses for prototyping or non-functional work.

### Context Governance
LISA proactively monitors your prompt context window usage using **tiktoken** for accurate token counting.
-   **Traffic Light:** Every command output includes a health indicator (e.g., `[🟢]`, `[🟡]`, `[🔴]`).
-   **Check Context:** Run `lisa context` to see detailed token usage stats.
-   **Context Analytics:**
    -   `lisa context status`: View current system activity.
    -   `lisa context size`: View token and file counts.
    -   `lisa context health`: View saturation and health metrics.
-   **Session Reset:** Run `lisa reset` to archive the current session and start fresh.
-   **State Checkpoint:** Run `lisa checkpoint` to validate your external state artifact (`todo.md`) is present and up-to-date.

### Turn Watchdog
Tracks discrete agentic reasoning cycles to detect logic drift before context decay sets in.
-   **Turns:** Run `lisa turns` to increment the turn counter after each reasoning cycle.
-   **Goldfish Threshold:** At turn 12, a "Logic Alignment Check" is triggered.
-   **Compaction Recovery:** At turn 20+, a "Grounding Snapshot" is recommended.

### Polish Pass
A reusable epic-level refactoring skill that detects cross-cutting quality issues.
-   **Invoke:** Run `lisa polish` to load the Polish Pass skill protocol.
-   **Phases:** Duplicate detection, naming audit, error handling consistency, magic value scan, performance/security review, and project structure verification.
-   **Skill:** `skills/polish-pass/skill.md`

### Lifecycle Hooks
Automatically invoke LISA skills at key story lifecycle boundaries.
-   **Trigger:** Run `lisa hooks <event>` to fire hooks for a lifecycle event.
-   **Events:** `story-kickoff`, `story-in-dev`, `story-test`, `story-complete`, `context-reset`.
-   **Story Completion:** `story-complete` automatically runs `lisa polish`, a context health check, and conditional remediation.
-   **Fail-Open:** Hook failures are logged as warnings and never block workflow.

## Configuration

LISA supports hierarchical configuration (User > Project). See the [User Guide](docs/user_guide.md#configuration) for details.

## State Management

LISA maintains its state in `.lisa/state.json`. It uses file locking to ensure state integrity across multiple concurrent shell sessions.
