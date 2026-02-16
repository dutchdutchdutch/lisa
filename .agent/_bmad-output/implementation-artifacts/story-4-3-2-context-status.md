# Story 4.3.2: Command UX - Context Status

**Status:** Done
**Epic:** 4 - Agentic Context Management
**Feature:** Context Monitoring

## Description
Implement `lisa context status` command.
**Goal:** Provide visibility into what the context management system is doing.
**Activities:** Active, Monitoring, Compacting, Creating Checkpoint, Resetting, Archiving.

## Acceptance Criteria

### Criteria 1: Status Reporting
**Given** the user runs `lisa context status`,
**When** the system is in a specific state (e.g., Monitoring),
**Then** it should return that state clearly to the user.

### Criteria 2: State Tracking
**Given** an operation like compression or checkpointing is running,
**When** `lisa context status` is queried (e.g., from another terminal),
**Then** it should reflect the active operation.

## Tasks

- [ ] **Implementation**
    - [ ] Add `CONTEXT_STATES` enum to `state.py`. <!-- id: 1 -->
    - [ ] Update `state.py` to track current activity. <!-- id: 2 -->
    - [ ] Implement `context_status` command in `commands.py`. <!-- id: 3 -->
    - [ ] Register command in `__main__.py`. <!-- id: 4 -->

- [ ] **Verification**
    - [ ] Verify `lisa context status` returns correct state. <!-- id: 5 -->

## File List
<!-- Auto-updated by dev-story workflow -->

## Change Log
<!-- Auto-updated by dev-story workflow -->
