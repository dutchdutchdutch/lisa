# LISA Loop — Background

## Intro and audience

Lisa governs where Ralph wanders. Lisa is a chaperone to Ralph and peers. Lisa promotes good engineering practices.

A significant number of engineers are already applying sound engineering discipline to their agentic workflows — scoping context carefully, managing test loops deliberately, and treating agent-assisted development as a complicated domain that requires structured practices. They are not the audience for this Lisa project and are unlikely to recognize their own workflow in the problems described here.

This is written for the population that isn't there yet. Developers and teams who have experienced the productivity promise of coding agents on simple tasks and are now facing challenges on real projects without a clear path forward.


## Problem Statement

Coding agents running test loops are consuming disproportionate amounts of tokens and developer time.

Without explicit strategy, agents default to broad, indiscriminate test execution: loading full test suites into context on every run, chasing unrelated failures, simulating UI interactions in noisy virtual environments, and making sweeping code changes in response to failures that have nothing to do with the work at hand. The result is a feedback loop that is expensive, slow, and often counterproductive.

This is the agent equivalent of `SELECT *` — technically it works, but it signals a missing mental model for what's actually happening under the hood.


### The underlying problem is the risk of mental model mismatches.

**Risk 1: Complexity mis-classification**

Much evidence that coding agents are transformative comes from influencers demoing one-page web apps. The demos are real. Agents *are* genuinely impressive on simple, self-contained problems. The disease, to borrow Jobs' framing on Scully, is assuming that a great demonstration is 90% of the solution. In practice it's closer to single digits. The rest is execution discipline, and execution discipline on a real project looks nothing like a demo.

Dave Snowden's Cynefin framework makes this precise. The jump from *simple* to *complicated* to *complex* domains is not a linear increase in difficulty — it's a categorical shift in what kinds of solutions work. Practices that are correct for simple problems are actively harmful when applied to complicated ones. The vast majority of agent workflows being promoted today are designed for simple domains and mis-applied to complicated and complex ones. Real projects are rarely simple.

The practical consequence: most of the time saved on initial agent-assisted development gets consumed, and  often exceeded, by extended debugging and refactoring cycles that result directly from under-engineered context discipline.

**Risk 2: Compound context decay**

Even when developers correctly recognize they're working in a complicated domain, the second failure mode is underestimating how context degrades across agent turns.

Three forces combine:

*Small errors accumulate.* An agent operating with a slightly incorrect assumption in turn 3 will build on that assumption in turns 4, 5, and 6. Each subsequent turn is correct relative to the flawed premise. By turn 15 the agent is confidently solving a coherent but subtly wrong problem, and no single turn looks obviously broken.

*Scope drift goes undetected.* Without explicit constraints, agents naturally expand scope in response to what they find — a failing test here, a related refactor opportunity there. Each expansion is locally reasonable. Cumulatively they pull the agent away from the original problem. The test loop validates the expanded scope, not the story.

*Lossy context compaction degrades silently.* When a context window fills, the agent compresses earlier turns to make room. That compression is always lossy. Constraints get softened. Edge cases that were established early get dropped. Nuance evaporates. The agent's internal model of the problem decays without any visible signal that it has done so. The agent doesn't know it has forgotten something. It just proceeds with less.

These three forces multiply. The causal chain is direct:

> *Mis-classify the complexity → under-engineer the context discipline → decay compounds unchecked → agent confidently solves the wrong problem at increasing cost*

LISA is a response to both stages. Layered tests and selective scope address complexity mis-classification by imposing appropriate discipline for a complicated domain. Isolated incubation and asking for expansion interrupt compound context decay by containing failures at the right layer before they can propagate into a widening context.


---

## Who Is Affected

**Developers using coding agents** in scenarios where:

- Multiple stories are being developed in parallel or in rapid succession -  context bleeds between stories. Agents carry assumptions from the last story into the next without knowing they're doing it.
- Backend/frontend via REST API — contract mismatches between layers are silent until integration. Agents fix one side without seeing the other.
- A data product runs on a managed platform with external dependencies - Pplatform errors look like code errors. Agents chase the wrong cause, burning context on noise they can't resolve.
- Historically mounting tech debt is depriortized for more scope - agents amplify existing fragility. What was a manageable crack becomes a compounding fault line under agentic velocity.

Tech leads, agentic in-the-loop or humans on-the-loop, inherit the consequences in the form of longer PR cycles, noisier test output, and agents that have made changes outside the story scope.

---

## Current State and Alternatives

Several agentic frameworks and skill sets include testing guidance. The issue is one of resolution and durability.

Many existing strategies operate at the principle level: *"use TDD," "write tests before code," "ensure coverage before merging."* These are correct but abstract. They give the agent a posture, not a decision tree. Under pressure, a failing test, an unexpected dependency, a noisy virtual environment, the agent falls back on what it does by default, for example:
- Run the entire test suite on every change
- Load all related (and unrelated) source files into context to analyze failures
- Attempt to simulate user actions in virtual environments, which are often unstable and generate high-noise output
- Investigate and attempt to fix failures outside the scope of the current story
- Re-run full suites after each attempted fix, compounding token consumption


The principle doesn't survive contact with a complicated real-world context.

This isn't purely a framework design issue. It reflects how language models handle long contexts. Instructions stated early in a session — in a system prompt, a role definition, or an initial briefing — carry weight at the start. That weight diminishes relative to recent context as the session progresses.

The practical consequence is that even well-intentioned agentic frameworks see their test strategies erode mid-session. The agent isn't ignoring the instruction — it's operating in a context where more recent and more concrete signals have effectively displaced it.

LISA is an attempt to establish a prompt-based test strategy pattern for coding agents at the story, release, or refactor level.

---

## Value Hypothesis

**The value hypothesis is that token consumption and cycle time can be reduced ay least 40% per story cycle, and potentially 70%+ on stories where the agent would otherwise spiral into tangent investigation — with no reduction in defect detection effectiveness.**

The savings come from three primary sources:

**1. Tangent Spiral Tax**
When an agent encounters an unrelated test failure it will load additional context, attempt fixes, potentially create new failures, load more context to analyze those, and so on. A single tangent can cost as much as 3–4 normal story test cycles in tokens alone. LISA eliminates this by explicitly deferring out-of-scope failures rather than pursuing them.

**2. Context Import Tariff**
Loading a full test suite into context on every run pulls in code the agent doesn't need, burns context window, and forces earlier context truncation — which degrades decision quality on subsequent steps. LISA scopes context to the story's affected modules only.

**3. UI Simulation Waste**
Virtual environment UI simulation generates high-noise, low-signal output. The agent reads long failure logs, retries with variations, reads more output, and rarely produces a useful result.

LISA defers UI simulation in Round 1 (story level) entirely, replacing it with a targeted manual verification checklist handed to the developer. Human verification of UI behavior is faster and more reliable at this stage. UI simulation earns its place later in the cycle as the signal-to-noise ratio improves. At the release level it is conditional, preferred for large releases with many integration points once APIs are confirmed clean. At the refactor and regression level it is appropriate, the codebase is stable, the agent has clean context, and simulation is validating known behavior rather than discovering unknown behavior in a noisy environment.

The layering principle is durable. The specific round where simulation becomes appropriate is not fixed and should be revisited as tooling evolves.

What won't change: running UI simulation before unit and API layers are confirmed clean will always be wasteful regardless of how capable the simulator becomes. The hierarchy is about isolating failure root cause efficiently, not about model capability.

The underlying principle is that UI simulation should only run when the layers beneath it are confirmed.

The release test cycle shows more modest savings — roughly 25–40% — since it is already more intentional, but eliminating redundant re-testing of story-level functionality and deferring UI verification still compounds meaningfully across a release.

---

## Core Tenets

These hierarchy tenets are about isolating failure root cause efficiently, not about model capability.

**Layered tests including eval tests**
Tests run in layers: unit tests first, then API tests, then a developer-verified manual check. Eval tests — agent-specific validation — are a first-class layer, not an afterthought. You don't proceed to the next layer until the current layer passes.

**Isolated incubation**
Failures are contained at the layer where they are found. The agent fixes at that layer and does not escalate outward until the current layer is clean. This prevents a unit-level bug from triggering a cascade of API and integration test failures that obscure the actual problem.

The layering principle is durable. However layers will need to adjust e.g. the specific round where simulation becomes appropriate should be revisited as tooling evolves.

**Selective scope**
Test execution is always scoped to the story's modified code and its direct dependencies. Out-of-scope failures are noted and deferred. The agent does not have permission to wander.

**Ask for expansion**
The agent works within its confirmed layer and defers outward expansion to a human decision. For story-level work this means requesting developer verification before moving to UI. For release-level work this means providing a clear manual test checklist rather than attempting automated E2E simulation.

**Non-goals**
LISA is not a replacement for a full regression suite. It does not eliminate the need for broader test coverage on major refactors or large-scope releases
.
LISA is not a permanent argument against UI automation. The deferral of UI simulation at the story level reflects current signal-to-noise realities in virtual environments, not a categorical position. As virtual environment stability improves, as computer use agents mature, and as models get better at interpreting UI test output, the appropriate round for introducing UI simulation will shift earlier.

---

## Vision and Future State

LISA is framed as a deployable skill that can operate in two modes:

**Standalone** — LISA governs the test loop for a project where no prior test strategy exists.

**Ralph chaperone** — LISA is layered on top of an existing agent configuration that runs unconstrained (a RALPH loop), constraining its test behavior without replacing its other capabilities.

*Lisa governs where Ralph wanders.*

The longer-term vision is for LISA to become a reusable, version-controlled prompt skill that lives in the repository alongside the code it governs. This means:

- Test strategy is explicit, documented, and consistent across the team
- New developers onboard to the discipline immediately
- The strategy evolves with the codebase through normal version control workflows
- Story-level, release-level, and refactor-level strategies are distinct prompts with clear handoff points between them

As coding agents become more deeply embedded in development workflows, token efficiency and context discipline will move from nice-to-have to a core engineering competency. LISA is a starting point for building that muscle.

The RALPH loop will still exist, improve and likely flourish. There are ample legitimate moments for it.  *"Did you run a RALPH?"* should become,a code review flag.

**A note on economics**

Token unit costs have trended down and competition makes a price reversal unlikely in the near term. The economic argument for efficiency discipline doesn't depend on that changing.

The real driver is volume. As agents become embedded in daily development workflows, token consumption scales multiplicativel. A sloppy loop on one story is a rounding error. A sloppy loop across a team, across every story, across every sprint is a meaningful cost center regardless of unit price.

The wildcard is energy. Data center power demand is already outpacing grid capacity in most major markets. There are credible arguments that power becomes a hard ceiling on compute supply within this decade. Most current assumptions about inference cost trajectories are off. Efficiency discipline adopted now is a hedge against that scenario, not just a present-day optimization.

*Build the discipline while it's optional. It may not stay that way.*
