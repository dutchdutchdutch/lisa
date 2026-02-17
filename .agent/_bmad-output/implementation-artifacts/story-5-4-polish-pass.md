# Story 5.4: Polish Pass (Epic-Level Refactoring Skill)

Status: review

## Story

As a Tech Lead,
I want LISA to provide a reusable "Polish Pass" skill that can be executed at the end of any epic or sprint,
so that cross-cutting quality issues accumulated across multiple stories are systematically detected and resolved before moving forward.

## Acceptance Criteria

### AC1: Duplicate Code Detection & Consolidation
**Given** a codebase where multiple stories have introduced similar patterns independently,
**When** the polish pass runs,
**Then** the agent identifies duplicate utility patterns and consolidates them into shared helpers.

### AC2: Naming Convention & Style Consistency
**Given** code written across multiple stories,
**When** the polish pass runs,
**Then** naming conventions are audited and corrected to be consistent across the project.

### AC3: Error Handling Pattern Consistency
**Given** the project has established error handling patterns,
**When** the polish pass runs,
**Then** all modules follow the same error handling approach consistently.

### AC4: Project Structure Verification
**Given** the architecture defines clear boundaries and separation of concerns,
**When** the polish pass runs,
**Then** the agent verifies code is in the correct locations per the architecture.

### AC5: Regression Suite Validation
**Given** all polish/refactoring changes have been applied,
**When** the full regression test suite is executed,
**Then** all tests pass with 0 failures.

### AC6: Skill Artifact Created
**Given** the polish pass logic is defined,
**When** the story is complete,
**Then** a reusable skill definition exists in `.agent/skills/polish-pass/skill.md`,
**And** the skill can be invoked on any project where LISA is active,
**And** the skill references the project's own architecture and conventions rather than hardcoding project-specific details.

## Dev Notes

### Design Intent
This is a **generic, project-agnostic skill**. The agent executing the polish pass must:
1. Read the project's architecture document to understand its conventions
2. Scan the codebase to detect violations of those conventions
3. Fix violations while preserving behavior
4. Run the project's test suite to confirm no regressions

The skill should NOT hardcode project-specific file names, languages, or patterns. It should discover them dynamically from the project's own documentation and codebase.

### Skill Orchestration Alignment
Per `.agent/instructions/skill-orchestration.md`:
- **Phase 1 (Kernel):** Create `skill.md` with the reasoning instructions for the polish pass
- **Phase 2 (Skeleton):** No external state needed — this is a single-pass audit
- **Phase 3 (Guardrails):** The regression suite run acts as the circuit breaker

### References

- [Source: epics.md#Story 5.4](file:///Users/dutch/Dev/lisa/.agent/_bmad-output/planning-artifacts/epics.md)
- [Source: skill-orchestration.md](file:///Users/dutch/Dev/lisa/.agent/instructions/skill-orchestration.md)

## Senior Developer Review (AI)

### Review Date
2026-02-16

### Review Outcome
Changes Requested

### Action Items
- [x] [HIGH] Add magic values/constants audit phase to skill protocol
- [x] [MEDIUM] Add performance and security scan to skill protocol
- [x] [MEDIUM] Remove hardcoded `.lisa/config.json` reference — make generic
- [x] [MEDIUM] Add CLI invocation interface (`lisa polish` command)

## Dev Agent Record

### Agent Model Used

Gemini 2.5 Pro

### Debug Log References

N/A — Skill definition + lightweight CLI command.

### Completion Notes List

- ✅ Created `.agent/skills/polish-pass/skill.md` following Phase 1 (Kernel) of skill-orchestration.md
- ✅ Skill follows existing patterns: YAML frontmatter + persona + trigger + step-by-step protocol + checklist + output format
- ✅ Skill is fully project-agnostic — reads the project's own architecture doc to discover conventions
- ✅ Structure mirrors existing skills (`refactor-gate`, `tdd-gate`, `context-curator`)
- ✅ Code review fixes applied: magic values phase, perf/security scan, generic config, CLI invocation
- ✅ Added `lisa polish` command to `commands.py` + `__main__.py`
- ✅ Added 3 unit tests in `test_polish.py`
- ✅ Regression suite: 53/53 tests PASS (0 failures)

### File List

- `.agent/skills/polish-pass/skill.md` (NEW) — Polish Pass skill definition
- `scripts/lisa/commands.py` (MODIFIED) — Added `polish()` command
- `scripts/lisa/__main__.py` (MODIFIED) — Wired `polish` dispatch
- `tests/test_polish.py` (NEW) — Tests for polish command

## Change Log

- 2026-02-16: Story created and implemented. Polish Pass skill defined as project-agnostic Phase 1 Kernel artifact.
- 2026-02-16: Code review fixes applied — added magic values phase, perf/security scan, generic config ref, `lisa polish` CLI command.
