---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: ['docs/background.md']
date: 2026-02-12
author: Dutch
---

# Product Brief: .agent


## Executive Summary

LISA (Layered, Isolated, Scoped, Ask) is an architectural discipline plugin for coding agents that **unlocks complexity** by arresting the failure modes of "tangent spirals" and context decay. Acting as a safety harness for capability agents, LISA enforces a strict verification hierarchy—Unit, then API, then Manual—that systematically purifies the agent's context window. By preventing agents from polluting their own workspace with indiscriminate test failures, LISA preserves high signal-to-noise ratios, enabling them to solve complex problems that typically degrade into incoherence. Distributed as a deployable plugin (e.g., `deploy.yml`), LISA targets a >40% improvement in context economics and cycle time.

---

## Core Vision

### Problem Statement

Coding agents in complex domains suffer from a **lack of enforcement of a boundary model**, a gap that disproportionately impacts less experienced developers. While best practices (like keeping contexts small) are documented, they are often forgotten or deprioritized until project complexity scales. Agents operating without these hard constraints effectively "treat accessibility as permission," running full test suites or noisy UI simulations on every turn. This mental model mismatch leads them to confidently solve the wrong problems or spiral into expensive debugging tangents triggered by unrelated failures.

### Problem Impact

*   **Tangent Spiral Tax:** High token waste investigating out-of-scope failures.
*   **Context Pollution:** Critical signal is crowded out by failure logs and hallucinated dependencies, degrading agent intelligence over time.
*   **Complexity Ceiling:** Without boundary enforcement, agents hit a "complexity wall" where they can no longer maintain coherence on real-world legacy projects.

### Why Existing Solutions Fall Short

Current agentic frameworks rely on abstract principles (e.g., "System Message: always do TDD") that are **durable only until context pressure increases**. As the context window fills, these soft constraints erode, and the agent reverts to undisciplined behavior. They provide a posture, not a hard decision tree that protects the context window.

### Proposed Solution

LISA is not a new agent, but a **deployable context governance plugin** (via `deploy.yml`) that standardizes the verification loop for existing agents (like Claude). It implements a rigid decision tree to maximize **Context Economics**:
1.  **Layered Tests:** Unit > API > Manual. No progression until the current layer is clean.
2.  **Isolated Incubation:** Failures are fixed only at the layer they occur, preventing higher-order noise from entering the context.
3.  **Selective Scope:** The agent is explicitly forbidden from fixing out-of-scope errors.

### Key Differentiators

*   **Enabler of Complexity:** LISA is not just a referee; she is the safety harness that allows agents to operate in complex brownfield environments where they usually fail.
*   **Context Purity:** The primary mechanism of action is maintaining a high **Signal-to-Noise Ratio** in the context window, preventing the "compounding confusion" that kills agent performance.
*   **Anti-Fragile Economics:** specifically optimized to hedge against context decay and rising inference constants.


## Target Users

### Primary Users

**"Leo" (The Risk-Aware Developer)**
*   **Role:** Mid-Level Developer / Senior Individual Contributor.
*   **Motivation:** Wants to maintain high-velocity execution using agents but fears the "Big Bang Merge"—large, irreversible changes that break hidden dependencies. He values **sustained progress** over burst speed.
*   **The Pain:** "Babysitting" the agent. He spends hours reverting "fixes" that broke two other things. He feels the "Tangent Spiral Tax" personally—it's his weekend on the line.
*   **LISA's Role:** His **Risk Manager**. She enforces a high cadence of small, reversible steps (Unit > API > Manual) so he never has to revert a week's worth of work.

### Secondary Users

**"Sarah" (The Tech Lead)**
*   **Role:** Architect / Repo Owner.
*   **The Pain:** "Agent Slop" in PRs—code that passes tests but degrades maintainability (duplication, unused tables, weird filenames).
*   **LISA's Role:** Her **Deputy**. LISA flags tech debt *during* story dev and proposes refactoring tasks (TDD-style) instead of letting the agent execute them blindly. Sarah trusts PRs more because LISA was the chaperone.

**The "Agent" (Component User)**
*   **Role:** The engine (e.g., Claude/Ralph).
*   **Interaction:** Consumes LISA's constraints as an API. Benefits from a "Context Purity" flywheel—clean context makes the agent smarter, which leads to cleaner code, which keeps the context clean.

### User Journey (The 5 Aha! Moments)

1.  **The Context Reset:** *Scenario:* Leo is deep in a debugging session. *Intervention:* LISA forces a context refresh before he creates a new story file. *Value:* "She just saved me from burning 50k tokens on stale data."
2.  **The TDD Check:** *Scenario:* Agent suggests a fix and a test update simultaneously. *Intervention:* LISA pauses: "I need to see a failing test first. Do you understand *what* is being tested?" *Value:* "She stopped the agent from cheating the test."
3.  **The Layered Defense:** *Scenario:* Agent wants to run the full E2E suite. *Intervention:* LISA optimizes: "Let's run these 3 Unit Tests first. If they pass, we'll check the API." *Value:* "Fast feedback loop instead of a 10-minute wait."
4.  **The Debt Noter:** *Scenario:* Agent creates a messy workaround. *Intervention:* LISA logs it to `implementation_plan.md` or `backlog.md` rather than stopping flow. *Value:* "Focus kept, debt tracked, no Jira context switching."
5.  **The Refactor Gate:** *Scenario:* Periodic review detects code duplication. *Intervention:* LISA proposes a TDD-based refactor plan but *blocks* immediate execution until approved. *Value:* "She caught the rot before it set in."


## Success Metrics

### User Success (Value Realization)

*   **Tangent Spiral Rate:** Reduction in turns spent on out-of-scope files or unrelated debugging.
*   **Revert Rate:** Decrease in frequency of reverting agent-generated code due to hidden dependency breaks.
*   **Churn Reduction:** Lower tokens per git commit/PR in later stages of a story, indicating cleaner, more decisive agent execution.

### Business Objectives (System Health & Velocity)

*   **Primary Driver:** **Sustained Velocity**. Achieving a predictable, low-variance flow of story delivery across sprints. The goal is reliability and avoiding "sprint-and-crash" cycles, rather than just maximizing a single sprint's output.
*   **Efficiency Metric:** **"Weighted Velocity"** (Stories delivered / Time / Token spend).
    *   *Philosophy:* 3 stories in 1 day (at higher token cost) is preferable to 3 stories in 3 days (at lower cost). LISA optimizes for speed first, efficiency second.
*   **Secondary Driver:** **Cost Hedge**. Reduced token consumption per story serves as insurance against future inference cost increases or energy caps.

### Key Performance Indicators (KPIs)

*   **Velocity Variance:**
    *   **Goal:** Maintain story delivery consistency within a +/- 15% band across sprints.
*   **Effectiveness Norms:**
    *   **Target:** 80% of stories completed within <48 hours (evolving to <24h), with minimal "stuck" stories.
*   **Context Purity Score:**
    *   **Measure:** Frequency of forced context refreshes (at minimum 1 per story).
    *   **Limit:** Hard upper limit warnings on token count to trigger resets.
*   **Adoption Signal:**
    *   **Metric:** "The Sarah Nod." Tech Lead approval rate on first PR review increases.


## MVP Scope

### Core Features (The "Walking Skeleton")

*   **Local Enforcement Engine:** A runnable script/hook (e.g., `.lisa/hooks/pre-run`) that the Agent must execute before generating code. It enforces rules locally/in-sandbox *before* any git commit or CI/CD action.
*   **The TDD Gate:**
    *   **Mechanism:** Forces the Agent to verify a *failing test* exists for the active Story Criteria before writing implementation code.
    *   **Prompt Injection:** A system prompt override that strictly forbids writing `src/` code without a corresponding `test/` failure log.
*   **Context Purifier:**
    *   **Mechanism:** A "freshness check" that alerts the user/agent when the context window exceeds a clean limit (forcing a reset/summarization) or when crossing story boundaries.
*   **Context Health Monitor (The Sentinel):**
    *   **Mechanism:** Automated injection of self-assessment prompts (e.g., "Is your context window still intact?") at configurable intervals.
    *   **Value:** Proactive alerts for drift, hallucinations, or tool limit proximity before they cause damage.
*   **Configuration:** A simple `.lisa/config.yaml` to define strictness levels.

### Out of Scope for MVP

*   **Automated Refactor Proposals:** The "Refactor Gate" logic (analyzing duplication/dead code) will be manual for now.
*   **Integration:** No direct Jira, Linear, or GitHub Issues integration. "The Debt Noter" will log to local Markdown files (`backlog.md`).
*   **Visual Dashboards:** No complex velocity graphs or web UI. CLI/Log output only.
*   **Spike Mode:** No "relaxed rules" mode initially; we focus on strict enforcement to prove the value first.

### MVP Success Criteria

*   **Behavioral:** Early adopter (Leo) successfully completes 3 stories without a "revert loop."
*   **Technical:** The "TDD Gate" successfully blocks premature implementation code in >90% of attempts.
*   **Qualitative:** "The Sarah Nod" — Tech Lead reviewing the PR confirms the code structure follows the "Layered" approach.

### Future Vision (Roadmap)

*   **Phase 1 (The Sentinel - Health Checks):** Implementation of automated "Lucidity Checks." Simple, high-value alerts where the agent self-assesses context drift and tool limits.
*   **Phase 2 (The Governor - TDD & Scope):** Strict local enforcement of TDD (Red/Green) and Context Hygiene. Enforces the **"Selective Scope"** tenet by blocking tangent spirals at the source.
*   **Phase 3 (The Strategist - Layers & Isolation):** Implementation of **"Layered Tests"** (Unit > API) and **"Isolated Incubation"** (Fixes constrained to their layer). The agent cannot progress to API tests until Unit tests pass.
*   **Phase 4 (The Deputy - Maintenance & Alignment):** Intelligent "Refactor Gate" and **"Ask for Expansion."** LISA proactively identifies technical debt (duplication, dead code) and negotiates larger refactors or manual verification steps, ensuring the **"Risk Management"** cadence.

### Long-Term Vision (V2.0 & Scaling)

*   **Cost/Benefit Quantifier:** (Post-MVP) Introducing "Refactor Cost Estimates" where LISA calculates the token cost vs. debt paydown value of a proposed refactor, giving the Scrum Master tangible data for prioritization.

## Appendix: Implementation FAQ

*   **Q: Can I bypass LISA for prototyping or scripts?**
    *   **A:** Yes. LISA is designed as a "Safety Harness," not a straightjacket. Commands like `lisa pause` or `--no-verify` will be available for "Spike Mode" or migration scripts, though the default posture is strict adherence to the "Governor."
*   **Q: How does LISA handle mocks?**
    *   **A:** (Phase 2 Detail) LISA will enforce "Mock Integrity" to prevent agents from simply changing mocks to force a passing test. Changes to mocks will require higher-order validation or explicit approval.
*   **Q: When do Health Checks run?**
    *   **A:** (Implementation Detail) LISA will determine the optimal cadence (e.g., every 3-5 rapid exchanges, or after heavy context loads) to balance safety with prompt overhead. "Heavy" responses may trigger immediate post-checks.



<!-- Content will be appended sequentially through collaborative workflow steps -->




