# Story 4.3.3: Command UX - Context Size

**Status:** Done
**Epic:** 4 - Agentic Context Management
**Feature:** Context Analytics

## Description
Implement `lisa context size` command.
**Goal:** Provide quantitative metrics on the context window.
**Metrics:** Token Count, Number of Files, Number of Turns (if tracked).

## Acceptance Criteria

### Criteria 1: Detailed Metrics
**Given** the user requests context size,
**When** they run `lisa context size`,
**Then** it should return:
-   Total Token Count (estimated)
-   Number of Files in Workspace (being tracked)
-   Number of Interaction Turns (if applicable/trackable)

## Tasks

- [ ] **Implementation**
    - [ ] Update `context_stats.py` to return file count and turn count (if available). <!-- id: 1 -->
    - [ ] Implement `context_size` command in `commands.py`. <!-- id: 2 -->
    - [ ] Register command in `__main__.py`. <!-- id: 3 -->

- [ ] **Verification**
    - [ ] Verify `lisa context size` output format. <!-- id: 4 -->

## File List
<!-- Auto-updated by dev-story workflow -->

## Change Log
<!-- Auto-updated by dev-story workflow -->
