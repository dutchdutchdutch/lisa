# Story 1.1: Project Initialization & Install

**Epic:** 1: The Walking Skeleton (Local Enforcement)
**Status:** In Progress
**Priority:** High

## User Story

As a Developer,
I want to install LISA by copying a script directory,
So that I can start using it without complex package managers.

## Acceptance Criteria

- [ ] Given I have the LISA source script, When I run the install command or copy the files, Then the `.lisa` and `scripts/lisa` directories are created
- [ ] And `lisa.sh` is executable
- [ ] And running `lisa.sh version` returns `0.1.0`

## Tasks/Subtasks

- [x] Create `.lisa` directory structure
- [x] Create `lisa.sh` at project root with executable permissions
- [x] Implement `version` command in `lisa.sh` returning `0.1.0`
- [x] Verify directory structure and version output

## Dev Notes

*   **Architecture:** Walking Skeleton approach. Zero explicit dependencies.
*   **Structure (Source Repo):**
    *   `.lisa/`: User config/state (hidden).
    *   `lisa.sh`: Core Logic (at root).
*   **Structure (User Install):**
    *   User copies `lisa.sh` to their `scripts/lisa/` folder.
*   **Bash Strict Mode:** `set -euo pipefail` in `lisa.sh`.

## Dev Agent Record

### Implementation Notes

*   [2026-02-13] Started implementation.
*   [2026-02-13] Completed implementation. Verified `lisa.sh version` returns `0.1.0`.

### Debug Log

*   `0.1.0` output verified.

## File List

*   `.lisa/` (Directory)
*   `scripts/lisa/` (Directory)
*   `scripts/lisa/lisa.sh` (New)

## Senior Developer Review (AI)

**Review Date:** 2026-02-13
**Outcome:** Changes Requested

### Action Items
- [ ] [AI-Review][Medium] File List Discrepancy: Story lists `scripts/lisa/lisa.sh` but file is at `./lisa.sh`. Update File List to match reality.
- [ ] [AI-Review][Low] `lisa.sh` Input Validation: Main dispatcher lacks input sanitization (basic `call "$1"` pattern is safe here but worth noting for future).

## Status
Review
