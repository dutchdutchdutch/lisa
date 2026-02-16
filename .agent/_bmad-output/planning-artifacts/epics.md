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

### Story 1.4: The TDD Audit (Automated Verification) [DONE]

As a Tech Lead,
I want the system to automatically enforce the "Red-Green" state transitions,
So that I know TDD was followed without having to manually gate every step.

**Acceptance Criteria:**

Criteria 1: Red State Enforcement (Automated)
**Given** a new test has been written
**When** the agent runs `lisa verify-fail <test_file>`
**Then** the tool runs the test execution
**And** IF the test FAILS (Exit Code != 0) -> Returns SUCCESS (0) and logs "RED State Verified"
**And** IF the test PASSES (Exit Code 0) -> Returns FAILURE (1) and logs "Error: Test Passed unexpectedly"
**And** NO user input is required by default.

Criteria 2: Interactive Mode (Optional)
**Given** the user explicitly wants to check the test
**When** the agent runs `lisa verify-fail <test_file> --interactive`
**Then** the tool pauses for user confirmation before running the automated check.

Criteria 3: Green State Verification
**Given** implementation is done
**When** the agent runs `lisa verify-pass <test_file>`
**Then** the tool runs the test and asserts it PASSES (Exit Code 0).



### Story 1.5: Story: Local Regression Verification & Refactoring [DONE]
As a Tech Lead,
I want LISA to enforce a "Direct Dependency" verification loop and Refactoring phase,
So that the agent confirms the new implementation hasn't regressed related logic and code quality is maintained.

Acceptance Criteria (The "Gherkin")

Criteria 1: The Refactor Phase
**Given** the new story-specific tests have reached a "Pass" state (Green)
**When** the agent identifies code smells (duplication, complexity) or optimization opportunities
**Then** the agent MUST refactor the code to improve quality without changing behavior
**And** MUST verify that the tests still pass (Green) after every refactor step.

Criteria 2: Validating the Impact Zone
**Given** the Refactor phase is complete and tests are Green
**When** the agent identifies tests for directly related modules and dependencies.
**Then** the agent MUST present this "Impact Suite" to the Human Partner for approval before execution.
**And** the Human Partner may hold execution or prune the suite if the scope triggers unnecessary "Context Import Tariffs".
**And** if failures occur in these approved tests, the agent MUST prioritize fixing the implementation code rather than mutating the tests to fit the new behavior.

### Story 1.6: Documentation & Architecture Update

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 1 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

### Epic 2: The Safety Valve (Spike Mode) [DONE]        
A developer can explicitly bypass rules to prototype without fighting the tool.

### Story 2.1: Spike Mode Activation [DONE]

As a Developer,
I want to explicitly enable "Spike Mode",
So that I can prototype rapidly without TDD enforcement.

**Acceptance Criteria:**

**Given** I am in normal mode
**When** I run `lisa spike`
**Then** the state in `.lisa/state.json` updates to `mode: SPIKE`
**And** the output confirms "Safety Harness Disengaged"

### Story 2.2: Verification Bypass [DONE]           

As a Developer,
I want the TDD Gate to be skipped when I am in Spike Mode,
So that I can commit "dirty" code without tests.

**Acceptance Criteria:**

**Given** the state is `mode: SPIKE`
**When** I start on a story
**Then** the TDD Gate (Story 1.4) does not alert or enforce me to write a failing test first
**And** the TDD Gate (Story 1.4) does not alert or enforce me to write a passing test after implementation
**And** the TDD Gate (Story 1.4) does not alert or enforce me to refactor the code
**But** issues a warning that the code is unverified


**Given** the state is `mode: SPIKE`
**When** I try to commit code changes without tests
**Then** the TDD Gate (Story 1.4) allows the commit
**But** issues a warning that the code is unverified

### Story 2.3: Dirty Output Tagging [DONE]

As a Tech Lead,
I want to identify logs generated during Spike Mode,
So that I don't confuse unverified output with clean TDD output.

**Acceptance Criteria:**

**Given** the state is `mode: SPIKE`
**When** any LISA command is run
**Then** the output is prefixed with `[SPIKE]` or `[DIRTY]`
**And** the standard `[LISA]` prefix is modified to reflect the mode

### Story 2.4: Bypasss TDD Gate [DONE]
As a developer I don't need to write a test for stories that are non-functional changes, so that the system isn't blocked by unnecessary tests.

**Acceptance Criteria:**

**Given** I am in normal mode
**When** I start on story that is scoped as non-functional changes: such as text updates, alignment, font sizes, other layout changes, or documentation updates
**Then** the coding agent can directly run`lisa bypass-tdd` to update the state in `.lisa/state.json` to `mode: BYPASS_TDD`
**And** the output confirms "TDD Gate Bypassed"
**And** once the story is completed, the coding agent can run `lisa normal-mode` to update the state in `.lisa/state.json` to `mode: NORMAL`
**And** the output confirms "TDD Gate Enabled"



### Story 2.5: Documentation & Architecture Update [DONE]

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 2 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

### Epic 3: Context Governance (The Governor) [DONE]
A developer receives proactive alerts when context window health degrades.
### Story 3.1: Token Analysis Logic (The Scale) [DONE]

As a Developer,
I want to know the "weight" of my current context window,
So that I can decide when to reset before performance degrades.

**Acceptance Criteria:**

**Given** I am running a LISA command
**When**  the context analyzer runs
**Then** it estimates the token count (or file size proxy) of the current workspace state
**And** returns a "Load Percentage" based on the configured limit

### Story 3.2: Context Health Alerting [DONE]

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

### Story 3.3: Visual Traffic Light UI [DONE]

As a Developer,
I want instant visual feedback on my context health,
So that I can check it at a glance without running a separate command.

**Acceptance Criteria:**

**Given** the current status (GREEN/AMBER/RED)
**When** LISA prints any output
**Then** it includes a visual indicator: `[🟢]`, `[🟡]`, or `[🔴]`
**And** the indicator matches the current health state

### Story 3.4: Session Archival (The Black Box) [DONE]

As a Developer,
I want to save my session history before resetting context,
So that I don't lose the "lessons learned" from a spiral.

**Acceptance Criteria:**

**Given** I am about to reset the context
**When** I run `lisa reset`
**Then** the current state and logs are copied to `.lisa/archive/{timestamp}/`
**And** the main `.lisa/state.json` is cleared to a fresh state

### Story 3.5: Documentation & Architecture Update [DONE] 

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 3 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

### Epic 4: Agentic Context Management [DONE]

### Story 4.1: Continuous Curation (The Rolling Summary) [DONE]
As a Steering Architect
I want to implement a "rolling summary" mechanism that compresses conversation history and "pins" core directives
So that the worker agent maintains a high signal-to-noise ratio and avoids "instruction drift" caused by "attention scarcity" as the context window fills.

**Acceptance Criteria:**

Criteria 1: Compression on Threshold 

**Given** the current conversation history exceeds the defined token warning threshold (e.g., 80% of context),
**When** the Steering Agent constructs the next prompt for the worker,
**Then** it must summarize the middle 60% of the interaction into a concise paragraph, retaining only state changes and key decisions,
**And** it must discard the raw natural language of those middle turns to free up "active memory".

Criteria 2: Pinning the Constitution 
**Given** the context window is being compacted or modified,
**When** the new prompt is generated,
**Then** the original System Instructions must be "pinned" to the very top of the context window,
**And** the agent must not allow recent user inputs to push these foundational constraints out of the model's immediate view


### Story 4.2: Externalization (Artifact-Based State) [DONE]
As a Developer 
I want to enforce an "Initializer and Coder" paradigm using external artifacts (like todo.txt or progress.md)
So that long-running tasks can survive "context window overflow" and effectively reset their memory between sessions without losing the core objective.

**Acceptance Criteria:**

Criteria 1: Mandatory State Commit (The Coder) 
**Given** the Worker Agent has completed a unit of work or reached a "circuit breaker" time limit, 
**When** the agent attempts to terminate the current session, 
**Then** the system must validate that the agent has updated the external state file (e.g., todo.txt) with a clear description of pending tasks, 
**And** it must block termination if this artifact has not been modified.

Criteria 2: Amnesiac Initialization (The Initializer) 
**Given** a new execution session is starting for an existing task, 
**When** the "Initializer Agent" spins up the environment, 
**Then** it must programmatically inject the contents of the external state file into the new context window, 
**And** the Agent must resume execution exactly from the last checkpoint defined in that file, treating the previous raw chat history as irrelevant

### Story 4.3 Command UX

4.3.1 Change lisa externalize command to lisa checkpoint. 
Rational Junior developers understand that if you don't reach a checkpoint in a game, you lose your progress when you quit. This perfectly maps to the "Context Window Overflow"

Extending lisa context:

### Story 4.3.1: Command UX (Checkpoint) [DONE]

As a Developer,
I want the `lisa externalize` command to be renamed to `lisa checkpoint`,
So that it aligns with my mental model of "saving progress" in a game or workflow.

**Acceptance Criteria:**

Criteria 1: Command Rename
**Given** the user or agent wants to save state,
**When** they run `lisa checkpoint`,
**Then** it performs the same validation logic as the old `externalize` command (checking state file freshness).

Criteria 2: Skill Update
**Given** the "Externalizer" skill is active,
**When** it decides to save state,
**Then** it must use the term "Checkpoint" and run `lisa checkpoint`.

### Story 4.3.2: Command UX (Context Status) [DONE]

As a Developer,
I want to know the current activity of the context system,
So that I understand if it is active, monitoring, compacting, or archiving.

**Acceptance Criteria:**

Criteria 1: Status Reporting
**Given** the user runs `lisa context status`,
**When** the system is in a specific state (e.g., Monitoring),
**Then** it should return that state clearly to the user.

### Story 4.3.3: Command UX (Context Size) [DONE]

As a Developer,
I want to see quantitative metrics about my context window,
So that I know how much "space" consumes.

**Acceptance Criteria:**

Criteria 1: Detailed Metrics
**Given** the user requests context size,
**When** they run `lisa context size`,
**Then** it should return:
-   Total Token Count (estimated)
-   Number of Files in Workspace
-   Number of Interaction Turns (if available)

### Story 4.3.4: Command UX (Context Health) [DONE]

As a Developer,
I want to assess the qualitative health of my context and detect drift,
So that I can intervene before the agent loses focus.

**Acceptance Criteria:**

Criteria 1: Health Metrics
**Given** the user runs `lisa context health`,
**Then** it should return a report including Saturation, Signal Ratio, and Drift Metric.

Criteria 2: Drift Detection
**Given** the current context vector is significantly different from the "golden" baseline,
**When** `lisa context health` is run,
**Then** it should return `CRITICAL: DRIFT DETECTED` and prompt for intervention.

### Story 4.4: Documentation & Architecture Update [DONE]

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 4 features are implemented
**When** I review the `README.md` , `architecture.md`, and 'user_guide.md'
**Then** they utilize the latest file structure and configuration formats
    **And** installation instructions are accurate for the current version
    **And** user guide updates are accurate for the current version

Epic 5: Polish  MVP for user testing

Beyond the skeleton and basic features. 

### Story 5.1: Permission Handling
**Permission Handling:** The tool crashes with a raw `PermissionError` instead of a user-friendly "Please fix permissions on .lisa/" message. This violates **NFR3 (Fail-Open/Warn)**.

**Acceptance Criteria:**

Criteria 1: Permission Handling
**Given** the user runs `lisa init`,
**When** the tool encounters a permission error,
**Then** it should return a user-friendly error message instead of crashing.

### Story 5.2: Token Heuristic
**Token Heuristic:** The current `char/4` token counting in `context_stats.py` is simplistic and may be inaccurate for code-heavy repos. Consider moving to `tiktoken` or similar for better precision in future. [Added during Story 4.1 Review]

**Acceptance Criteria:**

Criteria 1: Token Counting
**Given** the user runs `lisa context size`,
**When** the system counts tokens using the `char/4` heuristic,
**Then** it should return an accurate token count.

### Story 5.3: Story: Agentic Turn-Watchdog (Logic Durability Monitor)
As a Tech Lead,
I want LISA to track the number of discrete reasoning cycles (turns) in a session,
So that I can intervene before the agent’s internal model of the problem decays or drifts away from the original story boundary.

**Acceptance Criteria (The "Gherkin")**

Scenario 1: The "Goldfish" Threshold (Turn 12)
**Given** an agent is working in a complicated or complex domain.
**When** the agent completes its 12th discrete turn (one turn = one request-response cycle).
**Then** the skill MUST pause execution and issue a "Logic Alignment Check" 
**And** it MUST explicitly ask  itself (the agent): "Am I still solving the original problem, or have I entered a Tangent Spiral?"**.

Scenario 2: Detecting "Silent" Assumption Drift
**Given** the Turn-Watchdog is active.
**When** a turn involves the agent modifying code outside the Selective Scope defined at the start of the story.
**Then** the watchdog MUST flag this turn as a "Boundary Violation".
**And** it MUST force a human review to determine if the turn represents a legitimate "Ask for Expansion" or unmanaged scope drift.

Scenario 3: Turn-Based Compaction Recovery
**Given** the agent has surpassed 15 turns and the internal context is becoming "noisy" with terminal output and logs.
**When** a human intervention occurs.
**Then** the skill MUST generate a "Grounding Snapshot"—a concise summary of the current state of the code vs. the original requirements.
**And** it MUST suggest a "Context Purge" (starting a fresh session with only this snapshot) to eliminate the risk of compound context decay. use existing Lisa skills to manage the context purge.

Why focus on turns over tokens?
While your token counter monitors the "size" of the container, the Turn-Watchdog monitors the "signal-to-noise ratio." In complex environments, an agent can be well within its token limit but still be "confidently solving the wrong problem" because it has built on 12 turns of subtly incorrect assumptions.

This watchdog acts as the "chaperone" to ensure the agent doesn't wander into a high-cost Tangent Spiral.

### Story 5.4: Run Polish pass at the end of each epic 
turning these manual instructions into a skill:
At the end of each epic, run a polish pass to check for: 
Duplicate Code: Common utilities (e.g., config loading, path resolution).
Consistency: Naming conventions, error handling patterns.
Project Structure: Ensuring clear separation of concerns.
run regression suite after polishing 

### Story 5.5: Documentation & Architecture Update 

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 5 features are implemented
**When** I review the `README.md` and `architecture.md`
**Then** they utilize the latest file structure and configuration formats
**And** installation instructions are accurate for the current version

Epic 6: Security & Sanitization
### Story 5.1: Context Minimization (Security Sanitization)

As a Security Engineer,
I want to implement a "Context-Minimization" layer that extracts only necessary variables from untrusted data,
So that I can prevent "prompt injection" attacks and ensure the reasoning engine never processes raw, malicious natural language.

**Acceptance Criteria:**

Criteria 1: Sanitized Variable Extraction
**Given** an input stream containing untrusted user data (e.g., emails or web forms),
**When** the data is received by the system,
**Then** a restricted parser or "boundary model" must extract only the specific fields defined in the schema (e.g., {"category": "refund", "amount": 50}),
**And** it must discard all surrounding body text or free-form commentary.

Criteria 2: Isolated Reasoning Construction
**Given** the "Core Reasoning Agent" is preparing to make a decision,
**When** the prompt is constructed,
**Then** it must include only the sanitized JSON data extracted in the previous step,
**And** it must strictly exclude the original raw input string to ensure any hidden instructions (injections) are physically absent from the context


### Story 6.2: Documentation & Architecture Update 

As a Tech Lead,
I want the project documentation to reflect the delivered features,
So that the system remains maintainable and understandable.

**Acceptance Criteria:**

**Given** Epic 5 features are implemented
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

### Tech debt and minor issues


4. **Drift Detection:** Story 4.3.4 requested embedding-based drift detection. This has been deferred in favor of a simpler heuristic or future implementation. [Added during Story 4.3 Review]
2. Polish pass at the end of each epic check for: 
Duplicate Code: Common utilities (e.g., config loading, path resolution).
Consistency: Naming conventions, error handling patterns.
Project Structure: Ensuring clear separation of concerns.
-run regression suite after polishing
