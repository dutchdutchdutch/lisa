---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
status: 'complete'
completedAt: '2026-02-13'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/product-brief-.agent-2026-02-12.md']
workflowType: 'architecture'
project_name: 'LISA'
user_name: 'Dutch'
date: '2026-02-13'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
*   **Workflow Enforcement:** Strict Red -> Green TDD cycle. Requires state tracking of the current task.
*   **Context Governance:** Monitoring token usage and enforcing limits.
*   **User Interaction:** visually non-intrusive "Traffic Light" system.

**Non-Functional Requirements:**
*   **Performance:** <50ms latency for hook execution.
*   **Reliability:** Fail-Open architecture (Safety Valve).
*   **Compatibility:** POSIX shell compliance (Bash/Zsh).

**Scale & Complexity:**
*   Primary domain: Developer Tool / CLI
*   Complexity level: Low logic, High impact
*   Estimated architectural components: 3 (Hook, Analyzer, State Store)

### Technical Constraints & Dependencies
*   Must run locally without external services (Phase 1).
*   Must not require compiled binaries for MVP (Script-based).
*   Dependency on user having Python/Node environment (or just Shell).

### Cross-Cutting Concerns Identified
*   **Observability:** Injecting status into agent streams.
*   **Configuration Management:** Hierarchical config (Repo > User > Default).
*   **State Management:** Persisting task state across shell commands.

## Starter Template Evaluation

### Primary Technology Domain
**CLI Tool / Shell Hook** based on project requirements analysis.

### Starter Options Considered

1.  **Modern Python CLI (Typer/Click):**
    *   *Pros:* Type hints, auto-help generation, rich ecosystem.
    *   *Cons:* Requires `pip install` and venv management, violating "Drop-in" requirement.

2.  **Bash Frameworks (Bashly):**
    *   *Pros:* Structured bash generation.
    *   *Cons:* Ruby dependency for generation, added complexity.

3.  **The "Walking Skeleton" (Custom Zero-Dep):**
    *   *Pros:* Zero external dependencies. Uses standard `argparse` and `sys`. Fits "Drop-in" requirement perfectly.
    *   *Cons:* More manual boilerplate code.

### Selected Starter: The Walking Skeleton (Custom)

**Rationale for Selection:**
Selected to strictly adhere to the **Phase 1 "Drop-in Install" Requirement**. Avoiding external dependencies (pip/npm) is critical for adoption friction reduction.

**Initialization Command:**

```bash
mkdir -p .lisa/hooks scripts/lisa
touch .lisa/config.yaml
# Core logic will be plain Python3 + Bash
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
*   **Shell:** Bash (Strict Mode: `set -euo pipefail`)
*   **Logic:** Python 3.8+ (Standard Library only)

**Styling Solution:**
*   **Output:** ANSI Color Codes (Manual or simple helper class).

**Testing Framework:**
*   **Unit:** `unittest` (Standard Library) to avoid `pytest` dependency initially.
*   **Integration:** Bats (Bash Automated Testing System) - *Optional dev-dependency only*.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
*   **State Store Strategy:** Must be defined to track TDD state.
*   **Configuration Schema:** Must be defined to allow user overrides.

**Important Decisions (Shape Architecture):**
*   **Hook invocation pattern:** How bash calls python.

**Deferred Decisions (Post-MVP):**
*   **SQLite Database:** Deferred to Phase 3 (Context Governor).
*   **Binary Distribution:** Deferred to Phase 4.

### Data Architecture (State Management)
*   **Decision:** JSON File Store (`.lisa/state.json`).
*   **Rationale:** Zero-dependency, human-readable, sufficient for single-user local CLI.
*   **Constraint:** File locking needed (simple `.lock` file) to prevent race conditions if multiple shells are open.

### Configuration & Customization
*   **Decision:** Hierarchical Configuration.
*   **Pattern:**
    1.  Load `~/.lisa/config.yaml` (User Defaults).
    2.  Merge with `./.lisa/config.yaml` (Project Overrides).
*   **Rationale:** Allows users to set global preferences (e.g., "Always Spike Mode") while respecting project strictness.

### Infrastructure & Deployment
*   **Decision:** Repo-based Distribution (Phase 1).
*   **Pattern:** Scripts committed to `scripts/lisa`.
*   **Rationale:** "Walking Skeleton" approach. No external package manager required.

### Decision Impact Analysis

**Implementation Sequence:**
1.  **State Store:** Implement `StateManager` class (Python) to read/write JSON with locking.
2.  **Config Loader:** Implement `ConfigLoader` class (Python) to merge YAMLs.
3.  **The Hook:** Implement `lisa.sh` to trap git/shell events and call Python.

**Cross-Component Dependencies:**
*   `lisa.sh` depends on `StateManager` to know if it should block or allow.
*   `StateManager` depends on `ConfigLoader` to know where to store state.

## Implementation Patterns & Consistency Rules

### Hook Invocation Pattern (The "Handover")
*   **Pattern:** `Exec` Handover.
*   **Rule:** `lisa.sh` collects git/shell context, exports them as `ENV_VARS`, then `exec python3 scripts/lisa/main.py`.
*   **Why:** Replaces the shell process with Python. Cleaner signal handling (Ctrl+C kills Python, not just the shell wrapper).

### State Schema (The "Memory")
*   **Pattern:** Flat Task Map.
*   **Structure:**
    ```json
    {
      "current_task": "task-123",
      "status": "RED",
      "last_run": "2023-10-27T10:00:00Z"
    }
    ```
*   **Locking:** `state.json.lock` must be acquired before writing.

### Error Handling (The "Safety Valve")
*   **Pattern:** Fail-Open Catch-All.
*   **Rule:** Top-level `try/except` in Python. If *any* crash occurs, print `[LISA] Internal Error. Proceeding...` and exit `0` (Success).
*   **Why:** Tool bugs must never block developer work.

### Output Styling
*   **Pattern:** ANSI prefix.
*   **Rule:** All output prefixed with `[LISA]`. Colors: Red (Block), Amber (Warn), Green (Pass).

### Enforcement Guidelines
**All AI Agents MUST:**
*   Use the `exec` pattern for handovers.
*   Wrap all write operations in a file lock.
*   Never return non-zero exit codes for internal exceptions.

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
/
├── .lisa/                      # Hidden runtime directory (User Space)
│   ├── config.yaml             # Project-specific overrides
│   ├── state.json              # Task state (The Brain's Memory)
│   └── hooks/                  # Git hooks directory (symlinked to from .git/hooks)
│       └── pre-commit          # The specific hook entry point
├── scripts/
│   └── lisa/                   # The Core Logic (Repo Space - Committed)
│       ├── lisa.sh             # The "Exec" Wrapper & Entry Point
│       ├── main.py             # Python Entry Point
│       ├── config/             # Config Loader Module
│       ├── state/              # State Manager Module
│       ├── commands/           # Command Logic (commit, run, spike)
│       └── tests/              # Unit Tests (unittest)
└── .git/
    └── hooks/
        └── pre-commit -> ../../.lisa/hooks/pre-commit  # Symlink Integration
```

### Architectural Boundaries

**API Boundaries:**
*   **External:** CLI Arguments (`lisa commit`, `lisa run`)
*   **Internal:** `lisa.sh` -> `main.py` (via ENV_VARS + ARGS)

**Component Boundaries:**
*   **State Interface:** `StateManager` class abstracts all JSON file I/O.
*   **Config Interface:** `ConfigLoader` class abstracts hierarchical merging.

**Data Boundaries:**
*   **State Data:** Confined to `.lisa/state.json`.
*   **Config Data:** Merged from `~/.lisa/config` and `.lisa/config`.

### Requirements to Structure Mapping

**Feature Mapping:**
*   **Workflow Enforcement (FR1-FR4):** Implemented in `scripts/lisa/commands/`
*   **Context Governance (FR5-FR7):** Implemented in `scripts/lisa/commands/check.py`
*   **User Interaction (FR8-FR9):** Implemented in `main.py` (Output Formatting)

**Cross-Cutting Concerns:**
*   **Observability:** `[LISA]` prefix handling in `main.py`.
*   **Configuration:** `scripts/lisa/config/` module.

## Architecture Validation Results

### Coherence Validation ✅
*   **Compatibility:** The "Walking Skeleton" (Bash+Python) fits perfectly with requirements.
*   **Latency:** <50ms target is achievable with this architecture.
*   **Structure:** The User Space vs Repo Logic separation is clean.

### Requirements Coverage Validation ✅
*   **Workflow Gates (FR1-FR4):** Covered by `lisa.sh` hook logic.
*   **Context Governance (FR5-FR7):** Covered by `scripts/lisa/commands/check.py`.
*   **Traffic Light (FR8):** Covered by `main.py`.
*   **Zero-Dependency (NFR):** Strictly adhered to (only standard library).

### Architecture Readiness Assessment
**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Implementation Handoff:**
*   **First Priority:** Run the initialization command to create the directory structure.
*   **Guideline:** Do not introduce `pip` or `npm` dependencies without a formal architecture review (Phase 2+).






