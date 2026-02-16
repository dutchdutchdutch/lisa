# Story 4.2: Externalization (Artifact-Based State)

**Status:** Ready for Dev
**Epic:** 4 - Agentic Context Management
**Feature:** External State Management

## Description
As a Developer, I want to enforce an "Initializer and Coder" paradigm using external artifacts (like `todo.md`) so that long-running tasks can survive "context window overflow" and effectively reset their memory between sessions without losing the core objective.

## Acceptance Criteria

### Criteria 1: Mandatory State Commit (The Coder)
**Given** the Worker Agent has completed a unit of work or reached a "circuit breaker" time limit,
**When** the agent attempts to terminate the current session,
**Then** the system must validate that the agent has updated the external state file (e.g., `todo.md`) with a clear description of pending tasks,
**And** it must block termination if this artifact has not been modified.

### Criteria 2: Amnesiac Initialization (The Initializer)
**Given** a new execution session is starting for an existing task,
**When** the "Initializer Agent" spins up the environment,
**Then** it must programmatically inject the contents of the external state file into the new context window,
**And** the Agent must resume execution exactly from the last checkpoint defined in that file, treating the previous raw chat history as irrelevant.

## Dev Notes
- **Pattern:** Follow `skill-orchestration.md`.
- **Artifact:** Use `todo.md` in the project root.
- **Command:** Implement `lisa externalize` to perform the validation check (Criteria 1).
- **Injection:** Focus on the validation command first.

## Tasks

- [x] **Phase 1: Kernel (Skill Definition)**
    - [x] Create `.agent/skills/externalizer/skill.md` defining the Persona and "Read/Write `todo.md`" protocol. <!-- id: 1 -->

- [x] **Phase 2: Skeleton (State Artifact)**
    - [x] Define the `todo.md` template structure in `skill.md` or a separate template file. <!-- id: 2 -->

- [x] **Phase 3: Guardrails (The Command) - TDD**
    - [x] [RED] Create `tests/test_externalize.py` ensuring `lisa externalize` fails if `todo.md` is stale. <!-- id: 3 -->
    - [x] [GREEN] Implement `externalize` command in `commands.py`. <!-- id: 4 -->
    - [x] [REFACTOR] Ensure clean integration. <!-- id: 5 -->

- [x] **Phase 4: Mirror (Verification)**
    - [x] Verify `lisa externalize` command manually. <!-- id: 6 -->

## File List
<!-- Auto-updated by dev-story workflow -->

## Change Log
<!-- Auto-updated by dev-story workflow -->
