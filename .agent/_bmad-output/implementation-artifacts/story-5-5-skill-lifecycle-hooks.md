# Story 5.5: Skill Lifecycle Hooks

## Story

As a Tech Lead,
I want LISA skills to be automatically invoked at key story lifecycle boundaries (e.g., story start, story completion, context reset),
so that agents don't have to remember to run health checks manually and critical skills like context monitoring are reliably executed.

## Status

complete

## Acceptance Criteria

### AC1: Post-Story Health Check
**Given** a story has just been marked complete or moved to review,
**When** the dev-story workflow reaches its completion step,
**Then** `lisa context` (or equivalent health check) is automatically run and its output is included in the completion report.

### AC2: Configurable Hook Points
**Given** the project has installed LISA skills,
**When** I configure lifecycle hooks in the project config,
**Then** I can specify which commands run at which lifecycle events (story-kickoff, story-in-dev, story-test, story-complete, context-reset).

### AC3: Fail-Open Execution
**Given** a lifecycle hook command fails (e.g., permission error, missing dependency),
**When** the hook fires,
**Then** the failure is logged as a warning but does NOT block story completion.

### AC4: Story-Complete Orchestration
**Given** a story is marked complete,
**When** the `story-complete` hooks fire,
**Then** `lisa polish` runs, `lisa context` runs a health check, and if health is AMBER/RED remediation skills (context-curator, externalizer, session-management) are invoked.

### AC5: Auto/Interactive Execution Modes
**Given** the project config has `hooks_mode` set to `auto` or `interactive`,
**When** remediation hooks would fire,
**Then** auto mode executes remediation automatically, interactive mode prompts the user before proceeding.

## Tasks/Subtasks

- [x] **Task 1: Lifecycle hooks engine**
  - [x] 1.1 Add `lifecycle_hooks` and `hooks_mode` config keys to `ConfigManager._DEFAULTS`
  - [x] 1.2 Create `hooks.py` module with `LIFECYCLE_EVENTS`, `run_hooks()`, `run_story_complete()`
  - [x] 1.3 `run_hooks` loads config, finds hooks for event, executes each via subprocess, catches errors (fail-open)
  - [x] 1.4 `run_story_complete` orchestrates: polish → health check → conditional remediation based on `hooks_mode`
  - [x] 1.5 Write unit tests for `hooks.py`

- [x] **Task 2: CLI command for hooks**
  - [x] 2.1 Add `run_hooks_cmd(args)` to `commands.py`
  - [x] 2.2 Register `lisa hooks <event>` in `__main__.py`
  - [x] 2.3 Write unit tests for the CLI command

- [x] **Task 3: Integration into existing commands**
  - [x] 3.1 Call `run_hooks("context-reset", ...)` inside `reset_context()`
  - [x] 3.2 Call `run_hooks("story-complete", ...)` inside `verify_pass()`
  - [x] 3.3 Write integration tests

- [x] **Task 4: Regression suite**
  - [x] 4.1 Run full regression suite and fix any failures (70/70 pass)

## Dev Notes

### Architecture
- Follow existing pattern: new module in `scripts/lisa/`, tests in `tests/`
- Config is JSON (`.lisa/config.json`), merged with defaults via `ConfigManager`
- NFR3 (Fail-Open): hooks must never block workflow on failure
- Skills are markdown files in `.agent/skills/`; hooks invoke their CLI commands

### Lifecycle Events
- `story-kickoff`: Story starts → TDD gate setup
- `story-in-dev`: Each dev turn → turn watchdog
- `story-test`: After green phase → refactor gate
- `story-complete`: Story → review → polish + health + remediation
- `context-reset`: After reset → checkpoint

### Config Format
```json
{
    "hooks_mode": "auto",
    "lifecycle_hooks": {
        "story-kickoff": [],
        "story-in-dev": ["lisa tick"],
        "story-test": [],
        "story-complete": ["lisa polish"],
        "context-reset": ["lisa checkpoint"]
    }
}
```

## Dev Agent Record

### Debug Log
- Fixed circular import: `hooks.py` ↔ `commands.py`. Used lazy import of `check_context` inside `run_story_complete()`.
- Fixed GREEN path test: "no remediation needed" message contained "remediation", tripping the assertion. Changed to "all clear".
- Code review fix: removed triple health scan in `verify_pass` (pre-existing scan + hook + orchestrator).
- Code review fix: changed default story-complete hook from `lisa context` to `lisa polish` (orchestrator calls `check_context` directly).
- Code review fix: removed unused `import sys` in `hooks.py`.

### Completion Notes
- All 5 ACs met. 17 new tests, 70/70 total pass.
- `hooks_mode` defaults to `"auto"`. Remediation chain fires on AMBER/RED.

### Review Follow-ups (Tech Debt)
- [ ] [AI-Review][HIGH] `ConfigManager.load()` uses shallow `dict.update()` — nested config like `lifecycle_hooks` gets fully replaced instead of deep-merged. Refactor to use deep merge strategy.

## File List
- `scripts/lisa/hooks.py` [NEW] — Core hooks engine
- `scripts/lisa/config.py` [MODIFIED] — Added `hooks_mode` and `lifecycle_hooks` defaults
- `scripts/lisa/commands.py` [MODIFIED] — Added `run_hooks_cmd`, integrated hooks into `verify_pass` and `reset_context`
- `scripts/lisa/__main__.py` [MODIFIED] — Registered `lisa hooks` command
- `tests/test_hooks.py` [NEW] — 12 tests for hooks engine
- `tests/test_hooks_cmd.py` [NEW] — 5 tests for CLI command
