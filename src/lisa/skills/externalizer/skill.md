---
name: externalizing-state
description: Persists agent working memory to todo.md for long-term storage and session recovery. Use when starting a new session, completing a unit of work, or preparing for a context reset.
---

# Externalizer Skill

**Role:** You are the **Externalizer**. Your goal is to ensure that the agent's "Working Memory" (context window) is regularly committed to "Long-Term Storage" (`todo.md`).

## The Concept
Code generation tasks often exceed the context window. To survive a "Context Reset" (User: `lisa reset`), we must externalize our state. We use `todo.md` as our **Heap**.

## Protocol

### 1. Initialization (Read)
**When:** You start a new session or wake up.
**Action:**
1.  Read `todo.md` from the project root.
2.  Identify the **Current Task** (The first unchecked `[ ]` item).
3.  Load the **Next Step Strategy** (if present).
4.  Resume work from that exact point.

### 2. Termination (Write)
**When:** You have completed a unit of work, are stuck, or the session is ending.
**Action:**
1.  **Update** `todo.md`:
    -   Mark completed steps with `[x]`.
    -   Add new sub-steps if discovered.
2.  **Refine** the "Next Step Strategy" section with a clear instruction for your "Future Self" (e.g., "Resume debugging `test_auth.py` line 42").
3.    -   Run `lisa checkpoint` to validate that you have saved your state.
    -   If the command returns success (Green), you may proceed to finish the task.
    -   If the command fails (Red), you MUST update `todo.md` before finishing.

## Artifact Template (`todo.md`)

```markdown
# Task: [Task Name]

## Checklist
- [x] Step 1: Done
- [ ] Step 2: Current Focus
- [ ] Step 3: Pending

## Next Step Strategy
> [!NOTE]
> Resume here. We just fixed the API bug. Next: Add unit tests.
```
