# Token Analysis Logic (Story 3.1)

- [x] Create Token Analysis Skill Definition (skill.md) <!-- id: 0 -->
- [x] Implement Token Counting Logic (context_stats.py) <!-- id: 1 -->
- [x] Implement CLI Command (commands.py, __main__.py) <!-- id: 2 -->
- [x] Verify Implementation <!-- id: 3 -->

# Context Health & Traffic Light (Story 3.2 & 3.3)

- [x] Implement Context Caching Logic (context_stats.py, logger.py) <!-- id: 4 -->
- [x] Integrate Traffic Light into all Commands (commands.py) <!-- id: 5 -->
- [x] Verify Performance (Caching) <!-- id: 6 -->

# Code Review Refactoring (Stories 3.1-3.3)

- [x] Create Tests for Caching Logic (tests/test_caching.py) <!-- id: 7 -->
- [x] Refactor `scan_workspace` for Memory Safety (context_stats.py) <!-- id: 8 -->
- [x] Implement Atomic Cache Writes (context_stats.py) <!-- id: 9 -->

# Session Archival (Story 3.4)

- [x] Create Session Management Skill (Kernel) (skill.md) <!-- id: 10 -->
- [x] Create Unit Tests for Archiver (tests/test_archiver.py) <!-- id: 11 -->
- [x] Implement Archiver Logic (archiver.py) <!-- id: 12 -->
- [x] Integrate `lisa reset` Command (commands.py) <!-- id: 13 -->
- [x] Verification (lisa reset) <!-- id: 14 -->

# Code Review Refactoring (Story 3.4)

- [x] Implement Error Logging in `archive_session` (archiver.py) <!-- id: 15 -->
- [x] Remove Debug Print from `reset_session` (archiver.py) <!-- id: 16 -->
- [x] Add Robustness Tests (PermissionError) (tests/test_archiver.py) <!-- id: 17 -->
- [x] Fix Lazy Context Check in `logger.py` (Bug Fix) <!-- id: 18 -->

# Epic 3 Refactoring & Polish

- [x] Holistic Code Review (Epic 3 Features) <!-- id: 19 -->
- [x] Refactoring & Cleanup (commands.py imports, output standardization) <!-- id: 20 -->

# Documentation & Architecture (Story 3.5)

- [x] Update README.md and architecture.md <!-- id: 21 -->
- [x] Create Walkthrough Artifact (walkthrough.md) <!-- id: 22 -->

# Epic 4: Agentic Context Management

## Story 4.1: Continuous Curation

- [x] Define Context Curator Skill (skill.md) <!-- id: 23 -->
- [x] Create Context Threshold Logic (context_stats.py updates) <!-- id: 24 -->
- [x] Implement `lisa summarize` or similar trigger mechanisms <!-- id: 25 -->
- [x] Verify Curation Behavior <!-- id: 26 -->

## Story 4.2: Externalization (Artifact-Based State)

- [x] Define Externalization Skill (skill.md) <!-- id: 27 -->
- [x] Implement State Manager Logic (state.py updates) <!-- id: 28 -->
- [x] Implement `lisa externalize` command (or similar) <!-- id: 29 -->
- [x] Verify State Recovery <!-- id: 30 -->

## Story 4.3.1: Command UX (Checkpoint)
- [x] Rename `externalize` to `checkpoint` in commands and skills <!-- id: 31 -->
- [x] Verify `lisa checkpoint` alias <!-- id: 32 -->

## Story 4.3.2: Command UX (Context Status)
- [x] Implement `lisa context status` command <!-- id: 33 -->
- [x] Verify status reporting <!-- id: 34 -->

## Story 4.3.3: Command UX (Context Size)
- [x] Implement `lisa context size` command <!-- id: 35 -->
- [x] Verify size metrics (tokens, files) <!-- id: 36 -->

## Story 4.3.4: Command UX (Context Health)
- [x] Research embedding distance library <!-- id: 37 -->
- [x] Implement `lisa context health` with drift detection <!-- id: 38 -->
- [x] Verify drift alerts <!-- id: 39 -->

## Story 4.4: Documentation and Architecture Update
- [x] Update README.md with Epic 4 features <!-- id: 40 -->
- [x] Update architecture.md with Epic 4 decisions <!-- id: 41 -->
- [x] Run final regression suite <!-- id: 42 -->
