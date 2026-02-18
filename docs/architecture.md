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
*   **Relaxed Constraint:** "Zero-Dependency" (Standard Library only) was strict for MVP, but now relaxed to allow high-value dependencies like `tiktoken`.
*   Dependency on user having Python/Node environment (or just Shell).

### Cross-Cutting Concerns Identified
*   **Observability:** Injecting status into agent streams.
*   **Configuration Management:** Hierarchical config (Repo > User > Default).
*   **State Management:** Persisting task state across shell commands.

## Starter Template Evaluation

### Primary Technology Domain
**Agentic Skill + Support CLI** based on project requirements analysis.

### Starter Options Considered

1.  **Pure Prompt:**
    *   *Pros:* Zero code.
    *   *Cons:* Agents "drift" and ignore soft constraints under pressure.

2.  **Heavy Framework:**
    *   *Pros:* Total control.
    *   *Cons:* High friction, complex install.

3.  **Skill-First with Tool Enforcers (Selected):**
    *   *Pros:* Uses the agent's native reasoning (Skill) for the majority of the workflow. Uses minimal atomic scripts (Tools) only where hardware verification or state constraints are strictly required (e.g., "Prove the test failed").
    *   *Rationale:* Facilitates Evaluation Driven Development (EDD). We define the behavior in the Skill. If the model fails to adhere, we introduce a Script/Tool to enforce it.

### Selected Architecture: Skill + Enforcer Tools

**Definition:**
*   **The Brain (Skill):** A markdown definition (`.agent/skills/tdd-gate/skill.md`) that instructs the agent on the Red-Green-Refactor loop.
*   **The Muscle (CLI):** A lightweight Python CLI (`lisa`) providing atomic tools that the Skill *requires* the agent to call (e.g., `lisa verify-fail`).

**Initialization Command:**

```bash
mkdir -p .lisa/hooks agent/scripts/lisa agent/scripts/lisa/skills/tdd-gate
touch .lisa/config.json .agent/skills/tdd-gate/skill.md
# Core logic: Skill Markdown + Python Tools
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
    1.  Load `~/.lisa/config.json` (User Defaults).
    2.  Merge with `./.lisa/config.json` (Project Overrides).
*   **Rationale:** Allows users to set global preferences (e.g., "Always Spike Mode") while respecting project strictness.

### Infrastructure & Deployment
*   **Decision:** Repo-based Distribution (Phase 1).
*   **Pattern:** Scripts committed to `agent/scripts/lisa`.
*   **Rationale:** "Walking Skeleton" approach. External dependencies (like `pytest`) are permitted where they add significant value over standard library, provided they are documented.

### Decision Impact Analysis

**Implementation Sequence:**
1.  **State Store:** Implement `StateManager` class (Python) to read/write JSON with locking.
2.  **Config Loader:** Implement `ConfigManager` class (Python) to merge JSONs.
3.  **The Hook:** Implement `lisa.sh` to trap git/shell events and call Python.

**Cross-Component Dependencies:**
*   `lisa.sh` depends on `StateManager` to know if it should block or allow.
*   `StateManager` depends on `ConfigLoader` to know where to store state.

## Implementation Patterns & Consistency Rules

### Hook Invocation Pattern (The "Handover")
*   **Pattern:** `Exec` Handover.
*   **Rule:** `lisa.sh` collects git/shell context, exports them as `ENV_VARS`, then `exec python3 -m lisa`.
*   **Why:** Replaces the shell process with Python. Cleaner signal handling (Ctrl+C kills Python, not just the shell wrapper).

### State Schema (The "Memory")
*   **Pattern:** Flat Task Map.
*   **Structure:**
    ```json
    {
      "current_task": "task-123",
      "status": "RED",
      "mode": "NORMAL",
      "last_run": "2023-10-27T10:00:00Z"
    }
    ```
*   **Modes:**
    *   `NORMAL`: Strict TDD Enforcement.
    *   `SPIKE`: Safety Harness Disengaged (No verification).
    *   `BYPASS_TDD`: Single-task bypass for non-functional changes.
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
│   ├── config.json             # Project-specific overrides
│   ├── state.json              # Task state (The Brain's Memory)
│   └── hooks/                  # Git hooks directory (symlinked to from .git/hooks)
│       └── pre-commit          # The specific hook entry point
├── scripts/
│   └── lisa/                   # The Core Logic (Repo Space - Committed)
│       ├── __main__.py         # CLI Entry Point & Dispatch
│       ├── config.py           # Config Manager Module
│       ├── state.py            # State Manager Module
│       ├── commands.py         # Command Logic
│       ├── runner.py           # Test Runner
│       ├── analysis.py         # Dependency Analysis
│       ├── context_stats.py    # Token Analysis (tiktoken)
│       ├── archiver.py         # Session Archival
│       ├── hooks.py            # Lifecycle Hooks Engine
│       ├── logger.py           # Centralized Output with Status Icons
│       ├── utils.py            # Utilities (project root detection)
│       └── __init__.py         # Package Marker
├── tests/                      # Unit Tests (unittest)
├── .agent/
│   ├── skills/                 # LISA Skill Definitions
│   │   ├── tdd-gate/           # Red-Green-Refactor enforcement
│   │   ├── refactor-gate/      # Refactor phase regression guard
│   │   ├── polish-pass/        # Epic-level refactoring audit
│   │   ├── context-curator/    # Context compression protocol
│   │   ├── externalizer/       # State externalization
│   │   ├── session-management/ # Session lifecycle
│   │   └── token-analysis/     # Token counting strategy
│   └── test-artifacts/         # Verification Scripts/Artifacts
├── lisa.sh                     # The "Exec" Wrapper & Entry Point
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
*   **Config Interface:** `ConfigManager` class abstracts hierarchical merging.

**Data Boundaries:**
*   **State Data:** Confined to `.lisa/state.json`.
*   **Config Data:** Merged from `~/.lisa/config` and `.lisa/config`.

### Requirements to Structure Mapping

**Feature Mapping:**
*   **Workflow Enforcement (FR1-FR4):** Implemented in `agent/scripts/lisa/commands.py`
*   **Context Governance (FR5-FR7):** Implemented in `agent/scripts/lisa/context_stats.py` and `agent/scripts/lisa/archiver.py`
*   **User Interaction (FR8-FR9):** Implemented in `main.py` (Output Formatting)

**Cross-Cutting Concerns:**
*   **Observability:** `[LISA]` prefix handling in `main.py`.
*   **Configuration:** `agent/scripts/lisa/config.py` module.

## Architecture Validation Results

### Coherence Validation ✅
*   **Compatibility:** The "Walking Skeleton" (Bash+Python) fits perfectly with requirements.
*   **Latency:** <50ms target is achievable with this architecture.
*   **Structure:** The User Space vs Repo Logic separation is clean.

### Requirements Coverage Validation ✅
*   **Workflow Gates (FR1-FR4):** Covered by `lisa.sh` hook logic.
*   **Context Governance (FR5-FR7):** Covered by `agent/scripts/lisa/context_stats.py`.
*   **Traffic Light (FR8):** Covered by `main.py`.
*   **Zero-Dependency (NFR):** Relaxed in Epic 5 to support `tiktoken`. Now "Low-Dependency".

### Architecture Readiness Assessment
**Overall Status:** IMPLEMENTATION COMPLETE (Epic 5 Complete)

## Epic 3: Context Governance Architecture

### Token Analysis Strategy
*   **Decision:** `tiktoken` (Exact count).
*   **History:** Originally Heuristic (Chars / 4) for zero-dep.
*   **Rationale:** Precision is critical for large contexts. "Zero-Dep" constraint relaxed to prioritize reliability.
*   **Performance:** Recursive file scan with `.gitignore` respect.

### Context Caching (The Traffic Light)
*   **Decision:** Lazy Read / Atomic Write.
*   **Pattern:**
    1.  **Lazy:** Commands check `context_cache.json`. If `timestamp < 10m`, use cached status.
    2.  **Force:** significant events (Verification Pass, Explicit Check) force a re-scan.
    3.  **Atomic:** Writes use temp file + rename to prevent corruption.

### Session Archival (The Black Box)
*   **Decision:** State Snapshot.
*   **Pattern:** `lisa reset` copies `.lisa/state.json` and recent logs to `.lisa/archive/{timestamp}/`.
*   **Rationale:** Preserves learning from failed contexts before clearing state for a fresh start.

**Confidence Level:** High

**Implementation Handoff:**
*   **First Priority:** Run the initialization command to create the directory structure.
*   **Guideline:** Do not introduce `pip` or `npm` dependencies without a formal architecture review (Phase 2+).

## Epic 4: Agentic Context Management

### Context Curation Pattern
*   **Decision:** "Rolling Summary" Protocol.
*   **Pattern:** When context health hits AMBER (70%), the agent must Curate (summarize) before proceeding.
*   **Mechanism:** `lisa context` outputs specific instructions at saturation thresholds.

### Externalization Strategy (The Heap)
*   **Decision:** Artifact-Based State (`todo.md`).
*   **Rationale:** Large Language Models (LLMs) lose "working memory" as context fills. By forcing state into a file (`todo.md`), we offload memory to disk.
*   **Enforcement:** `lisa checkpoint` verifies this file exists and has been modified recently (freshness check).

### Command UX Standardization
*   **Decision:** Sub-command Architecture for Context.
*   **Pattern:** `lisa context [status|size|health]`.
*   **Rationale:** Groups related inspection tools under a single namespace, reducing root-level command clutter.
*   **Migration:** `lisa externalize` renamed to `lisa checkpoint` to better align with the mental model of "saving game state".

**Confidence Level:** High
**Status:** IMPLEMENTATION COMPLETE

## Epic 5: MVP Polish

### Token Heuristic Migration
*   **Decision:** Migrate from `char/4` heuristic to `tiktoken` (`p50k_base`).
*   **Rationale:** Benchmarking showed `tiktoken` provides significantly more accurate token estimates for code-heavy repos. Worth the single dependency.
*   **Impact:** `requirements.txt` now includes `tiktoken`. "Zero-dependency" constraint formally relaxed to "Low-dependency".

### Turn Watchdog (Logic Durability Monitor)
*   **Decision:** Turn-based reasoning decay detection.
*   **Pattern:** `lisa turns` increments a turn counter in `state.json`. The `lisa context` output displays current turn count alongside token metrics.
*   **Thresholds:**
    *   **Turn 12 (Goldfish):** "Logic Alignment Check" — agent self-evaluates for tangent spirals.
    *   **Turn 20+ (Compaction):** "Grounding Snapshot" — agent summarizes state and suggests context purge.
*   **Rationale:** An agent can be within token limits but "confidently solving the wrong problem" after many turns of subtly incorrect assumptions. Turns track signal-to-noise decay.

### Polish Pass Skill Architecture
*   **Decision:** Reusable, project-agnostic skill artifact.
*   **Pattern:** `.agent/skills/polish-pass/skill.md` defines a multi-phase audit protocol. `lisa polish` CLI command reads and outputs the skill for agent consumption.
*   **Phases:** Duplicate detection → Naming audit → Error handling consistency → Magic value scan → Performance/security review → Project structure verification → Regression suite.
*   **Design Principle:** The skill reads the project's own architecture doc to discover conventions dynamically — no hardcoded project references.

### Lifecycle Hooks Engine
*   **Decision:** Event-driven skill invocation at story lifecycle boundaries.
*   **Pattern:** Configurable hook points in `.lisa/config.json` map lifecycle events to LISA commands.
*   **Events:** `story-kickoff`, `story-in-dev`, `story-test`, `story-complete`, `context-reset`.
*   **Orchestration:** `story-complete` uses a dedicated orchestrator: `lisa polish` → context health check → conditional remediation (curator/externalizer/session-management) based on health status.
*   **Config Keys:**
    *   `hooks_mode`: `"auto"` (default) or `"interactive"` — controls whether remediation runs automatically or prompts.
    *   `lifecycle_hooks`: Map of event name → list of CLI commands to execute.
*   **NFR3 Compliance:** All hook failures are caught and logged as warnings. Hooks never block workflow.

**Confidence Level:** High
**Status:** IMPLEMENTATION COMPLETE
