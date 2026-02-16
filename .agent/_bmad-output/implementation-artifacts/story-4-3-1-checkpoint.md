# Story 4.3.1: Command UX - Checkpoint

**Status:** Done
**Epic:** 4 - Agentic Context Management
**Feature:** Command UX

## Description
Change `lisa externalize` command to `lisa checkpoint`.
**Rationale:** Junior developers understand that if you don't reach a checkpoint in a game, you lose your progress when you quit. This perfectly maps to the "Context Window Overflow".

## Acceptance Criteria

### Criteria 1: Command Rename
**Given** the user or agent wants to save state,
**When** they run `lisa checkpoint`,
**Then** it performs the same validation logic as the old `externalize` command (checking `todo.md` freshness).

### Criteria 2: Skill Update
**Given** the "Externalizer" skill is active,
**When** it decides to save state,
**Then** it must use the term "Checkpoint" and run `lisa checkpoint`.

## Tasks

- [x] **Refactor Code**
    - [x] Rename `externalize` function to `checkpoint` in `commands.py`. <!-- id: 1 -->
    - [x] Update `__main__.py` dispatch from `externalize` to `checkpoint`. <!-- id: 2 -->
    - [x] Update `lisa.sh` alias. <!-- id: 3 -->

- [x] **Refactor Tests**
    - [x] Rename `tests/test_externalize.py` to `tests/test_checkpoint.py`. <!-- id: 4 -->
    - [x] Update test references to use `checkpoint`. <!-- id: 5 -->

- [x] **Refactor Skills**
    - [x] Update `.agent/skills/externalizer/skill.md` to use "Checkpoint" terminology. <!-- id: 6 -->

- [x] **Verification**
    - [x] Verify `lisa checkpoint` works. <!-- id: 7 -->

## File List
<!-- Auto-updated by dev-story workflow -->

## Change Log
<!-- Auto-updated by dev-story workflow -->
