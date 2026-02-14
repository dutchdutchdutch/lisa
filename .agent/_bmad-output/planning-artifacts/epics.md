---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: 'complete'
completedAt: '2026-02-13'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/architecture.md']
---

# LISA - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for LISA, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: The system can detect if a commit/run contains code changes without corresponding test changes.
FR2: The system can block execution if the test suite does not contain a *failing* test for the current task (Red state enforcement).
FR3: The system can allow execution to bypass verification when "Spike Mode" is explicitly active.
FR4: The system can tag output generated in Spike Mode as "Untrusted/Dirty."
FR5: The system can analyze the current context token count against a configured limit.
FR6: The system can trigger a "Compaction Alert" when usage exceeds the defined threshold (e.g., 80%).
FR7: The system can archive the current session summary before resetting context (Journey 1).
FR8: The system can display a visual status indicator (Green/Amber/Red) in the agent's output stream.
FR9: The system can output a textual "Confidence Report" summarizing test coverage for the current task.
FR10: Users can configure strictness levels (e.g., proper TDD vs. test-after) in `.lisa/config.yaml`.
FR11: Users can install the tool by copying a single script directory (Drop-in install).

### NonFunctional Requirements

NFR1: Latency: `lisa.sh` hook execution target < 50ms.
NFR2: Context Overhead: "Traffic Light" output target < 50 tokens per turn.
NFR3: Fail-Open: System should warn and proceed on internal errors rather than blocking workflow.
NFR4: Offline Capability: System should function without internet access after install.
NFR5: POSIX Compliance: Core scripts should run on standard macOS/Linux shells (Zsh/Bash).

### Additional Requirements

- **Starter Template:** Implement "Walking Skeleton" (Custom Zero-Dep) using Bash (Strict Mode) and Python 3.8+ (Standard Library only).
- **State Management:** Implement JSON File Store (`.lisa/state.json`) with file locking (`.lock`) to prevent race conditions.
- **Configuration:** Implement Hierarchical Configuration (User Defaults `~/.lisa/config.yaml` + Project Overrides `./.lisa/config.yaml`).
- **Hook Pattern:** Implement `Exec` Handover pattern (Bash traps context, exports ENV, execs Python).
- **Project Structure:** Enforce strict separation between User Space (`.lisa/`) and Repo Logic (`scripts/lisa/`).
- **Distribution:** Repo-based distribution model (scripts committed to `scripts/lisa`).

### FR Coverage Map

FR1: Epic 1 - Detect code changes without tests
FR2: Epic 1 - Block execution on Red state failure
FR3: Epic 2 - Bypass verification in Spike Mode
FR4: Epic 2 - Tag output as Dirty
FR5: Epic 3 - Analyze token count
FR6: Epic 3 - Trigger Compaction Alert
FR7: Epic 3 - Archive session summary
FR8: Epic 3 - Visual Traffic Light
FR9: Epic 3 - Confidence Report
FR10: Epic 1 - Configure strictness
FR11: Epic 1 - Drop-in install

## Epic List

### Epic 1: The Walking Skeleton (Local Enforcement)
A developer can install LISA and have it enforce the "Red-Green-Refactor" loop locally, blocking premature code.
### Story 1.1: Project Initialization & Install [DONE]

As a Developer,
I want to install LISA by copying a script directory,
So that I can start using it without complex package managers.

**Acceptance Criteria:**

**Given** I have the LISA source script
**When** I run the install command or copy the files
**Then** the `.lisa` and `scripts/lisa` directories are created
**And** `lisa.sh` is executable
**And** running `lisa.sh version` returns `0.1.0`

### Story 1.2: State Management (The Brain) [DONE]

As a LISA System,
I want to persist the current task state in a file,
So that I can track the Red-Green cycle across independent shell commands.

**Acceptance Criteria:**

**Given** multiple shell instances might run LISA
**When** state is written to `.lisa/state.json`
**Then** a file lock must be acquired to prevent race conditions
**And** the task status (RED/GREEN) is persisted
**And** the lock is released immediately after write

### Story 1.3: Configuration Loading [DONE]

As a User,
I want to configure LISA via YAML files,
So that I can set global preferences and project-specific overrides.

**Acceptance Criteria:**

**Given** a user config at `~/.lisa/config.yaml` and project config at `./.lisa/config.yaml`
**When** LISA starts
**Then** it loads the user config
**And** merges the project config on top (Project overrides User)
**And** defaults are used if no config exists

### Story 1.4: The TDD Gate (The Hook)

As a Tech Lead,
I want LISA to block commits that contain code changes without test changes,
So that developers are forced to write tests first (or at least simultaneously).

**Acceptance Criteria:**

**Given** I am in a non-SPIKE mode
**When** I try to commit code changes
**Then** LISA checks if any test files were modified
**And** if NO tests changed, the commit is blocked (Red Gate)
**And** if tests changed, the commit is allowed (Green Gate)

### Story 1.5: Documentation & Architecture Update

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 1 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

### Epic 2: The Safety Valve (Spike Mode)
A developer can explicitly bypass rules to prototype without fighting the tool.
### Story 2.1: Spike Mode Activation

As a Developer,
I want to explicitly enable "Spike Mode",
So that I can prototype rapidly without TDD enforcement.

**Acceptance Criteria:**

**Given** I am in normal mode
**When** I run `lisa spike`
**Then** the state in `.lisa/state.json` updates to `mode: SPIKE`
**And** the output confirms "Safety Harness Disengaged"

### Story 2.2: Verification Bypass

As a Developer,
I want the TDD Gate to be skipped when I am in Spike Mode,
So that I can commit "dirty" code without tests.

**Acceptance Criteria:**

**Given** the state is `mode: SPIKE`
**When** I try to commit code changes without tests
**Then** the TDD Gate (Story 1.4) allows the commit
**But** issues a warning that the code is unverified

### Story 2.3: Dirty Output Tagging

As a Tech Lead,
I want to identify logs generated during Spike Mode,
So that I don't confuse unverified output with clean TDD output.

**Acceptance Criteria:**

**Given** the state is `mode: SPIKE`
**When** any LISA command is run
**Then** the output is prefixed with `[SPIKE]` or `[DIRTY]`
**And** the standard `[LISA]` prefix is modified to reflect the mode

### Story 2.4: Documentation & Architecture Update

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 2 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

### Epic 3: Context Governance (The Governor)
A developer receives proactive alerts when context window health degrades.
### Story 3.1: Token Analysis Logic (The Scale)

As a Developer,
I want to know the "weight" of my current context window,
So that I can decide when to reset before performance degrades.

**Acceptance Criteria:**

**Given** I am running a LISA command
**When** the context analyzer runs
**Then** it estimates the token count (or file size proxy) of the current workspace state
**And** returns a "Load Percentage" based on the configured limit

### Story 3.2: Context Health Alerting

As a Developer,
I want to be warned when my context is getting full,
So that I don't waste prompts on "hallucinated" responses.

**Acceptance Criteria:**

**Given** the calculated Load Percentage from Story 3.1
**When** the load is < 70%
**Then** status is GREEN
**When** the load is 70-90%
**Then** status is AMBER ("Compaction Recommended")
**When** the load is > 90%
**Then** status is RED ("Context Saturation - Reset Required")

### Story 3.3: Visual Traffic Light UI

As a Developer,
I want instant visual feedback on my context health,
So that I can check it at a glance without running a separate command.

**Acceptance Criteria:**

**Given** the current status (GREEN/AMBER/RED)
**When** LISA prints any output
**Then** it includes a visual indicator: `[🟢]`, `[🟡]`, or `[🔴]`
**And** the indicator matches the current health state

### Story 3.4: Session Archival (The Black Box)

As a Developer,
I want to save my session history before resetting context,
So that I don't lose the "lessons learned" from a spiral.

**Acceptance Criteria:**

**Given** I am about to reset the context
**When** I run `lisa reset`
**Then** the current state and logs are copied to `.lisa/archive/{timestamp}/`
**And** the main `.lisa/state.json` is cleared to a fresh state

### Story 3.5: Documentation & Architecture Update

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 3 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->
