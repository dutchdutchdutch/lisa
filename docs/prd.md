---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['docs/background.md', '_bmad-output/planning-artifacts/product-brief-.agent-2026-02-12.md']
classification:
  projectType: 'Developer Tool'
  domain: 'AI Development / DevTools'
  complexity: 'Medium'
  projectContext: 'Greenfield'
workflowType: 'prd'
---

# Product Requirements Document - .agent

**Author:** Dutch
**Date:** 2026-02-13

## Executive Summary

LISA (Layered, Isolated, Scoped, Ask) is an architectural discipline plugin for coding agents that **unlocks complexity** by arresting the failure modes of "tangent spirals" and context decay. Acting as a safety harness for capability agents, LISA enforces a strict verification hierarchy —Unit, then API, then Manual— that systematically purifies the agent's context window. By preventing agents from polluting their own workspace with indiscriminate test failures, LISA preserves high signal-to-noise ratios, enabling them to solve complex problems that typically degrade into incoherence. Distributed as a deployable plugin (e.g., `deploy.yml`), LISA targets a >40% improvement in context economics and cycle time.

## Core Vision

### Problem Statement

Coding agents in complex domains suffer from a **lack of enforcement of a boundary model**, a gap that disproportionately impacts less experienced developers. While best practices (like keeping contexts small) are documented, they are often forgotten or deprioritized until project complexity scales. Agents operating without these hard constraints effectively "treat accessibility as permission," running full test suites or noisy UI simulations on every turn. This mental model mismatch leads them to confidently solve the wrong problems or spiral into expensive debugging tangents triggered by unrelated failures.

### Proposed Solution

LISA is not a new agent, but a **deployable context governance plugin** (via `deploy.yml`) that standardizes the verification loop for existing agents (like Claude). It implements a rigid decision tree to maximize **Context Economics**:
1.  **Layered Tests:** Unit > API > Manual. No progression until the current layer is clean.
2.  **Isolated Incubation:** Failures are fixed only at the layer they occur, preventing higher-order noise from entering the context.
3.  **Selective Scope:** The agent is explicitly forbidden from fixing out-of-scope errors.

## Target Users

### Primary Users

**"Leo" (The Risk-Aware Developer)**
*   **Role:** Mid-Level Developer / Senior Individual Contributor.
*   **Pain:** "Babysitting" the agent. He spends hours reverting "fixes" that broke two other things.
*   **LISA's Role:** His **Risk Manager**. Enforces high cadence of small, reversible steps.

**"Sarah" (The Tech Lead)**
*   **Role:** Architect / Repo Owner.
*   **Pain:** "Agent Slop" in PRs—code that passes tests but degrades maintainability.
*   **LISA's Role:** Her **Deputy**. Flags tech debt *during* story dev and proposes refactoring.

**The "Agent" (Component User)**
*   **Role:** The engine (e.g., Claude/Ralph).
*   **Interaction:** Consumes LISA's constraints as an API.

## Success Criteria

### User Success

*   **Tangent Spiral Elimination:** "Leo" (Risk-Aware Dev) completes 3 consecutive stories without entering a "doom loop" of unrelated debugging.
*   **Revert Rate Reduction:** "Sarah" (Tech Lead) approves PRs with >90% acceptance rate on first review ("The Sarah Nod"), citing cleaner code structure.
*   **Confidence:** Developers feel "protected" by the harness, reducing hesitation to tackle complex refactors.

### Business Success

*   **Sustained Velocity:** Achieving a predictable flow of story delivery (variance < +/- 15%) across sprints, avoiding "sprint-and-crash" cycles.
*   **Weighted Velocity efficiency:** Improvements in the ratio of (Stories delivered / Time / Token spend).
*   **Cost Management:** Reduced token consumption per story as a hedge against future inference cost increases.

### Technical Success

*   **Context Purity:** High Signal-to-Noise Ratio (SNR) in the agent's context window.
*   **Gate Effectiveness:** The "TDD Gate" successfully blocks premature implementation code >90% of the time.
*   **Automated Hygiene:** Context refreshes trigger automatically before token limits or signal degradation impact quality.

### Measurable Outcomes

*   **80% of stories completed within < 48 hours.**
*   **Zero "hidden dependency" breaks** released to main branch.
*   **Context Purity Score:** Maintain high relevance density in context window (qualitative audit initially).

## Product Principles

1.  **Safety, Not Shackles (The "Spike" Principle):** LISA is a safety harness, not a straightjacket. Developers must always have an escape hatch ("Spike Mode") to explore freely. We prioritize *informed* deviation over forced compliance.
2.  **Alert, Don't Erase (The "No-Wipe" Principle):** LISA *never* deletes or wipes context directly. She acts as a "Fuel Gauge," alerting the user when context ("fuel") is low or "engine" (context window) is struggling, empowering *them* to choose when to reset.
3.  **Clarity over Control:** The primary value is the *relief* of working in a noise-free environment. Interventions should feel like a helpful tap on the shoulder ("You're drifting"), not a slap on the wrist.
4.  **Signal-to-Noise is King:** Every feature must be measured by how much it improves the ratio of useful tokens to waste tokens.

## Product Scope

### MVP - Minimum Viable Product (The Walking Skeleton)

*   **Local Enforcement Engine:** A runnable script/hook (e.g., `.lisa/hooks/pre-run`) that runs before commit/push.
*   **The TDD Gate:** Strict enforcement that a failing test must exist (Red) before implementation (Green).
*   **Context Purifier:** Automated checks for context freshness and forced resets at story boundaries.
*   **Context Health Monitor ("The Sentinel"):** Proactive alerts for context drift or hallucination risks.
*   **Configuration:** Simple `.lisa/config.yaml` for defining strictness levels.

### Growth Features (Post-MVP)

*   **Layered Tests & Isolated Incubation:** Implementing the strict hierarchy (Unit > API > Manual) and preventing progression until the current layer is clean.
*   **Automated Refactor Proposals:** "The Refactor Gate" logic to analyze code for duplication/dead code.
*   **"Spike Mode":** A distinct mode with relaxed rules for prototyping or migration scripts.

### Vision (Future)

*   **Phase 4 (The Deputy):** Intelligent technical debt negotiation and "Ask for Expansion" capabilities.
*   **Cost/Benefit Quantifier:** Economic analysis of refactoring vs. debt, providing data for prioritization.
*   **Context Economics Analytics:** Detailed reporting on token ROI per story.

## User Journeys

### Journey 1: Leo's Moment of Clarity (The "Governor" Experience)
**Persona:** "Leo" (Mid-Level Dev) - *The Risk-Aware Developer*
*   **The Scenario:** Leo has been debugging a race condition for 2 hours. His context window is 80% full of "noisy" logs from previous failed attempts.
*   **The Conflict:** He's about to ask the agent to "try again," which would likely result in a hallucinated fix due to context decay.
*   **The Intervention:** LISA intervenes with a **Context Health Alert**: *"Context Saturation at 85%. Signal-to-Noise ratio is critical. Compaction is imminent."* She doesn't wipe anything. She simply flags the danger.
*   **The Resolution:** Leo takes a breath, realizes he's spiraling, and manually initiates a new session with a clean summary.
*   **The "Aha" Moment:** The relief he feels isn't from the tool; it's from the clarity. He solves the issue in the next turn because the agent isn't confused by 2 hours of noise. LISA was the "Governor" that prevented the crash.

### Journey 2: Sarah's Trust (The Proof of Discipline)
**Persona:** "Sarah" (Tech Lead) - *The Architect*
*   **The Scenario:** Sarah opens a PR from Leo for a new feature. Usually, she dreads "Agent Slop"—files scattered everywhere, unused functions, weird naming.
*   **The Conflict:** She needs to verify if the code is solid without spending 2 hours reviewing it.
*   **The Intervention:** She sees a **LISA Report** attached to the PR: *"Verified: 3 Unit Tests passed. 0 API/Integration tests attempted (Scope: Unit Layer). No 'Spike Mode' flags."*
*   **The Resolution:** She sees that the "TDD Gate" was respected. The code is structured.
*   **The "Aha" Moment:** She approves the PR with a "Sarah Nod." She trusts the agent's output because she knows LISA enforced the discipline she didn't have time to police herself.

### Journey 3: The "Spike" Escape (The Safety Valve)
**Persona:** "Amelia" (Senior Dev) - *The Pragmatist*
*   **The Scenario:** Amelia needs to prototype a crazy idea fast. She doesn't want TDD; she wants to hack.
*   **The Conflict:** LISA's default strictness would block her rapid iteration.
*   **The Intervention:** Amelia invokes `lisa spike`. LISA responds: *"Safety Harness Disengaged. Rules Suspended. I will tag this session as 'Experimental'."*
*   **The Resolution:** Amelia hacks freely. When she tries to merge, LISA flags it: *"Warning: This code was generated in Spike Mode and is untrusted. Please add tests to verify."*
*   **The "Aha" Moment:** Amelia realizes she got the speed she wanted *without* compromising the repo's long-term health. LISA got out of the way but didn't let the mess leak into `main`.

### Journey Requirements Summary

*   **Context Monitoring:** Real-time analysis of context window health (token count + "noise" density) with non-destructive alerts.
*   **Spike Mode:** A clear, explicit "opt-out" state that suspends rules but marks output as "dirty/unverified."
*   **Verification Reporting:** Automated generation of a "Compliance Report" for PRs/Commits.
*   **Layered Enforcement:** Logic that distinguishes between "Unit" task types and "Integration" task types to enforce appropriate scoping.

## Appendix: Implementation FAQ

*   **Q: Can I bypass LISA for prototyping or scripts?**
    *   **A:** Yes. LISA is designed as a "Safety Harness," not a straightjacket. Commands like `lisa spike` or `--no-verify` will be available.
*   **Q: How does LISA handle mocks?**
    *   **A:** (Phase 2 Detail) LISA will enforce "Mock Integrity" to prevent agents from simply changing mocks to force a passing test.

## Domain-Specific Requirements

### Ecosystem Integration
- **Shell Agnostic:** Must run in standard shells (Bash, Zsh) used by agents.
- **Git Hooks:** Must integrate seamlessly with `.git/hooks` without breaking existing workflows.
- **Agent Agnostic:** The core logic must be independent of the specific agent (Claude, generic LLMs).

### Performance & Latency
- **Zero-Latency Overhead:** The "Pre-Run" checks must execute in milliseconds (<50ms ideal).
- **Minimal Token Overhead:** Reports/alerts must be concise to preserve context window.

### Safety & Reliability
- **Non-Destructive:** LISA must never auto-delete user code or history without explicit confirmation.
- **Fail-Open:** If LISA crashes or encounters an error, she must fail-open (warn but allow proceeding) to prevent blocking work.

### Data Privacy
- **Local Execution:** All analysis must happen locally. No external data transmission unless explicitly configured.

## Innovation & Novel Patterns

### Detected Innovation Areas

1.  **Context Governance as a First-Class Citizen:**
    *   *Novelty:* Most agents focus on *autonomy* (doing more). LISA focuses on *constraint* (doing less to do more).
    *   *Concept:* **"Context Economics"** — treating the context window as a finite financial resource that requires strict ROI management.

2.  **The "Governor" Architecture:**
    *   *Novelty:* Separating the "Intelligence" (Claude/LLM) from the "Discipline" (LISA).
    *   *Concept:* A "Super-Ego" for the AI that enforces TDD and layering, which the LLM (Id) naturally ignores in favor of speed.

3.  **"Dirty" State Management (Spike Mode):**
    *   *Novelty:* Explicitly tracking the "purity" of a session. Allowing "Spike Mode" but permanently tagging the output as "Untrusted" until verification. This bridges the gap between prototyping speed and production safety.

### Market Context & Competitive Landscape
*   *Current Landscape:* Tools like Cursor/Copilot are "Accelerators" (gas pedal).
*   *LISA's Position:* LISA is the "Brakes/Steering" (Control System). The market lacks "Safety Harnesses" for autonomous agents.

### Validation Approach
*   **Metric:** *Context Purity Score* (Ratio of relevant vs. irrelevant tokens at hour 4 of a session).
*   **Test:** A/B test "Leo" on a complex task with and without LISA. Measure "Tangent Spirals" (time lost to hallucinated rabbit holes).

### Risk Mitigation
*   *Risk:* Developers reject the "shackles."
*   *Mitigation:* **Spike Mode** (The Escape Hatch) and **Fail-Open** architecture.

## Developer Tool Specific Requirements

### Project-Type Overview
LISA is a lightweight **Context Governance Tool** designed to be dropped into any project via simple script copying. It prioritizes transparency and ease of modification over binary performance, avoiding "black box" logic.

### Technical Architecture Considerations
*   **Language Support:**
    *   **Phase 1:** Pure Shell/Python/Node scripts (Interpreted). No compiled binaries (Go/Rust) initially to ensure users can read/audit the logic.
*   **Distribution Strategy:**
    *   **MVP:** "Drop-in" installation. Users manually copy `lisa.sh` and prompt templates (e.g., `CLAUDE.md`) into a `scripts/lisa/` directory.
    *   **Goal:** Zero-dependency setup (beyond standard Bash/Python).

### Implementation Considerations
*   **Visualization (The "Traffic Light"):**
    *   Status is communicated via textual indicators in the agent chat response:
        *   **🟢 GREEN:** "Context Clean. TDD Gates Open."
        *   **🟡 AMBER:** "Context Saturation > 70%. Compaction recommended."
        *   **🔴 RED:** "Tangent Spiral Detected. Stop. Reset Context."
*   **File Structure:**
    *   `.lisa/config.yaml` (Configuration)
    *   `scripts/lisa/lisa.sh` (Core Logic)
    *   `scripts/lisa/templates/` (Prompt constraints)

## Project Scoping & Phased Development

### MVP Strategy & Philosophy
**MVP Approach:** "Walking Skeleton" (Vertical Slice)
**Philosophy:** Prove the **TDD Gate** works first. If we can arrest the "Tangent Spiral" with just a manual script, we earn the right to build the full platform.

### Phase 1: The "Walking Skeleton" MVP
**Goal:** A purely local, manual-install script that enforces the **Strict TDD Workflow**.
**Core User Journeys:**
*   Leo's Moment of Clarity (Context Reset)
*   Amelia's Spike Mode (Escape Hatch)

**Must-Have Capabilities:**
*   **Strict TDD Gate:** Enforces that a *failing test* (Red) must exist for a story *before* any implementation code (Green) is accepted.
    *   *Mechanism:* Pre-commit/Pre-run hook checks for new test files with failing status relative to the task.
*   **Traffic Light UI:** Text-based status (Red/Amber/Green) in chat.
*   **Spike Mode:** `lisa spike` command to bypass checks.
*   **Drop-in Install:** Manual script copy.

### Phase 2: The Context Health Monitor
**Goal:** Give the agent/user real-time visibility into "Context Economics."
**Capabilities:**
*   **Context Saturation Alerts:** Warning when context window fills up.
*   **Signal-to-Noise Calculation:** Alerting on "Tangent Spirals" (e.g., high edit churn with low pass rate).

### Phase 3: The Context Governor
**Goal:** Advanced logic and architectural enforcement.
**Capabilities:**
*   **Layered Verification:** Distinguishing Unit vs. API tests (Unit > API > Manual).
*   **Refactor Proposals:** Agent suggesting cleanup.

### Phase 4: The Platform (Expansion)
**Goal:** Enterprise scale and frictionless distribution.
**Capabilities:**
*   CI/CD Integration.
*   Binary Distribution (Brew/NPM).

### Risk Mitigation Strategy
*   **Technical Risk (Adoption Friction):** Mitigated by Phase 1 "Drop-in" script. No complex binary to install.
*   **Market Risk (Developer Rebellion):** Mitigated by **Spike Mode** in Phase 1. Without it, LISA would be rejected immediately.

## Functional Requirements

### Workflow Enforcement (The "Gate")
*   **FR1:** The system can detect if a commit/run contains code changes without corresponding test changes.
*   **FR2:** The system can block execution if the test suite does not contain a *failing* test for the current task (Red state enforcement).
*   **FR3:** The system can allow execution to bypass verification when "Spike Mode" is explicitly active.
*   **FR4:** The system can tag output generated in Spike Mode as "Untrusted/Dirty."

### Context Management (The "Governor")
*   **FR5:** The system can analyze the current context token count against a configured limit.
*   **FR6:** The system can trigger a "Compaction Alert" when usage exceeds the defined threshold (e.g., 80%).
*   **FR7:** The system can archive the current session summary before resetting context (Journey 1).

### User Interaction (The "Traffic Light")
*   **FR8:** The system can display a visual status indicator (Green/Amber/Red) in the agent's output stream.
*   **FR9:** The system can output a textual "Confidence Report" summarizing test coverage for the current task.

### Configuration & Setup
*   **FR10:** Users can configure strictness levels (e.g., proper TDD vs. test-after) in `.lisa/config.yaml`.
*   **FR11:** Users can install the tool by copying a single script directory (Drop-in install).

## Non-Functional Requirements (Performance Targets)

*Note: For the MVP, these are tuning goals to monitor, not hard blockers.*

### Performance Targets
*   **Latency:** `lisa.sh` hook execution target < 50ms.
*   **Context Overhead:** "Traffic Light" output target < 50 tokens per turn.

### Reliability Goals
*   **Fail-Open:** System should warn and proceed on internal errors rather than blocking workflow.
*   **Offline Capability:** System should function without internet access after install.

### Compatibility
*   **POSIX Compliance:** Core scripts should run on standard macOS/Linux shells (Zsh/Bash).






