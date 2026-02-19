---
name: handing-off-ui-tests
description: Generates a targeted manual UI test script for the developer once all automated test layers are clean. Use when unit and integration tests pass and the story requires visual or interactive UI verification.
---

# UI Test Handoff (Manual Verification Script)

## Purpose

Generate a targeted manual UI test script for the developer once all automated test layers (UNIT and INTEGRATION) are clean. UI verification is performed by a human — not the agent — because human verification of UI behavior is faster and more reliable at the story level than agent-driven browser simulation.

## Why Not Automated UI Simulation?

**Signal-to-noise ratio.** At the story level, automated UI simulation generates high-noise, low-signal output. The agent reads long failure logs, retries with variations, reads more output, and rarely produces a useful result. This burns tokens on low-value work.

**Token cost.** Browser simulation consumes significant context window space for setup, execution, and log parsing. This directly competes with the context budget needed for the actual story work.

**Human advantage.** A developer can visually verify UI behavior in seconds. The manual test script focuses their attention on exactly what changed, making verification fast and targeted.

**When simulation earns its place.** UI simulation becomes appropriate at the release and regression level, when the codebase is stable, APIs are confirmed clean, and simulation validates known behavior rather than discovering unknown behavior in a noisy environment. Running UI simulation before unit and API layers are confirmed clean is always wasteful.

## How It Works

Think step by step:

1. **Confirm all automated layers are clean.** LISA checks that both UNIT and INTEGRATION layer status is `CLEAN` in `.lisa/scope.json`. If either layer is not clean, the handoff is blocked — fix automated failures first.
2. **Read the scope context.** Load `modified_files` and `dependency_cone` from `.lisa/scope.json` to understand what code changed and what is affected.
3. **Identify affected user-facing behavior.** From the modified files and their dependencies, determine which user-visible screens, flows, commands, or interactions are impacted by the changes.
4. **Generate the manual test script.** Produce a structured script following the template below.
5. **Hand off to the developer.** The script is for human execution. Do NOT attempt to run it programmatically.

## Manual Test Script Template

The generated script must contain these sections:

### 1. Summary of Changes
A brief description of what was modified in this story — which modules, what behavior changed, and why.

### 2. Verification Steps
For each affected screen, flow, or interaction:
- **What to verify:** The specific UI element, command output, or user flow
- **Steps to reproduce:** Exact actions the developer should take
- **Expected behavior:** What the developer should observe if the change is correct
- **Regression check:** What should NOT have changed (confirm existing behavior is preserved)

### 3. Edge Cases
Scenarios that are specifically relevant to the story's scope:
- Boundary conditions (empty input, maximum values, missing data)
- Error states (what happens when things go wrong)
- State transitions (behavior before and after the change)

### 4. Out of Scope
Explicitly list what does NOT need manual verification for this story, to prevent the developer from over-testing.

## Agent Instructions

1. **Do NOT attempt automated browser or UI simulation.** Do not launch browsers, use Selenium/Playwright/Puppeteer, or simulate UI interactions programmatically. This is a deliberate architectural decision, not a limitation.
2. **Use scope context as your primary input.** The modified files and dependency cone tell you what changed. The in-scope test files tell you what behavior is already covered by automated tests.
3. **Be specific, not generic.** The script should reference actual file names, function names, and behaviors from the story — not generic "check that the page loads" instructions.
4. **Keep it concise.** The developer should be able to complete verification in minutes, not hours. Prioritize high-signal checks.
5. **Note completion status.** After generating the script, the story can proceed to completion with: "UI verification pending — manual test script provided."

## Warnings

- If no scope is set, the handoff cannot determine what changed. Set scope first with `lisa scope`.
- If either UNIT or INTEGRATION layer is not CLEAN, the handoff is blocked. Fix automated failures before requesting UI handoff.
- The generated script is scoped to the current story. Do not include verification steps for unrelated functionality.
