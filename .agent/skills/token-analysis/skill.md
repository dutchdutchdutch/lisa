
---
name: Token Analysis
description: Allows agents to check their current workspace token usage and health status.
---

# Token Analysis (The Scale)

**Use when:** You are about to write large files, or after significant code generation, to check if you need to reset the context window.
**Goal:** Prevent prompt failures and hallucinations by maintaining context hygiene.

## Usage

Run the following command to check current context usage:

```bash
lisa context
```

## Output Interpretation

The command returns one of three statuses:

### [🟢] GREEN (< 70% Usage)
*   **Meaning:** Safe to continue.
*   **Action:** Proceed with normal tasks.

### [🟡] AMBER (70% - 90% Usage)
*   **Meaning:** Context window is getting full.
*   **Action:**
    *   Finish current thought/task immediately.
    *   Do NOT start a new major task.
    *   Prepare for a context reset (summarize state).

### [🔴] RED (> 90% Usage)
*   **Meaning:** Context saturation imminent.
*   **Action:**
    *   **STOP WRITING CODE.**
    *   Run `lisa reset` immediately (if available).
    *   Or ask the user to reset the session.

## Configuration

The default limit is 8000 tokens. This can be configured in `.lisa/config.json`:

```json
{
  "context_limit": 16000
}
```
