# Story 4.3.4: Command UX - Context Health

**Status:** Done
**Epic:** 4 - Agentic Context Management
**Feature:** Context Health & Drift Detection

## Description
Implement `lisa context health` command.
**Goal:** Assess the qualitative state of the context window, specifically checking for "context drift".
**Key Metric:** Embedding distance (centroid shift) between current input and "golden" baseline.

## Acceptance Criteria

### Criteria 1: Health Metrics
**Given** the user requests context health,
**When** they run `lisa context health`,
**Then** it should return a structured report including:
-   Saturation (Token usage vs Limit)
-   Signal Ratio (Rolling summary status)
-   Drift Metric (Distance from baseline)
-   Pinned Layers (Active system instructions)
-   Overall Status (Healthy/Critical)

### Criteria 2: Drift Detection
**Given** the current context vector is significantly different from the initial goal vector (threshold TBD),
**When** `lisa context health` is run,
**Then** it should return `CRITICAL: DRIFT DETECTED` and prompt for intervention.

## Tasks

- [ ] **Research**
    - [ ] Determine library for embedding distance (e.g., `scikit-learn` or simple cosine similarity). <!-- id: 1 -->

- [ ] **Implementation**
    - [ ] Implement `drift_detection.py` module. <!-- id: 2 -->
    - [ ] Implement "Golden Baseline" capture logic (at start of task). <!-- id: 3 -->
    - [ ] Implement `context_health` command in `commands.py`. <!-- id: 4 -->
    - [ ] Register command in `__main__.py`. <!-- id: 5 -->

- [ ] **Verification**
    - [ ] Verify `lisa context health` output format. <!-- id: 6 -->
    - [ ] Verify drift warning triggers correctly. <!-- id: 7 -->

## File List
<!-- Auto-updated by dev-story workflow -->

## Change Log
<!-- Auto-updated by dev-story workflow -->
