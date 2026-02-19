---
name: checking-workspace-size
description: Checks the token footprint of project source files on disk. Use when assessing whether the project is large enough to risk overwhelming an agent's context window if loaded carelessly, or after adding many files to the project.
---

# Workspace Size

**Use when:** You want to know how large the project is on disk (in tokens), or before loading large portions of the project into an agent's context window.
**Goal:** Understand the workspace token footprint so you can make informed decisions about what to load into context.

## Usage

Run the following command to check workspace size:

```bash
lisa workspace
```

## Workspace Size Thresholds

Use this table to assess agent impact based on workspace token count:

| Workspace Size | Agent Impact | Action |
|---|---|---|
| < 50K tokens | Agent can read most files comfortably | No concerns |
| 50K - 100K tokens | Agent needs to be selective about file loading | Use targeted reads, avoid loading entire project |
| 100K - 300K tokens | Agent cannot hold the full project picture | Strong architectural boundaries needed; load only relevant modules |
| 300K+ tokens | Single-agent reasoning breaks down | Consider splitting into separate components or repos |

## Output Interpretation

The command returns workspace size metrics with a usage indicator:

### [🟢] GREEN (< 70% of workspace token budget)
*   **Meaning:** Project is well within budget.
*   **Action:** Proceed normally.

### [🟡] AMBER (70% - 90% of workspace token budget)
*   **Meaning:** Project is getting large relative to the configured budget.
*   **Action:**
    *   Be selective about which files you load into context.
    *   Consider updating `.lisa/config.json` scan ignores to exclude non-essential files.

### [🔴] RED (> 90% of workspace token budget)
*   **Meaning:** Project exceeds the workspace token budget.
*   **Action:**
    *   Do NOT attempt to load the entire project into context.
    *   Use targeted file reads instead of broad workspace scans.
    *   Consider increasing `context_limit` if the budget is too conservative.

## Important

**This measures files on disk, not the agent's active context window.** A large workspace does not mean your context window is full — it means you should be careful about how much of it you load. For actual context window pressure, use turn-based health signals (`lisa context health`).

## Configuration

The `context_limit` in `.lisa/config.json` defines the workspace token budget. It defaults to **100,000 tokens** — roughly the point where an agent needs to be disciplined about selective file loading. This is a project-size budget, **not** derived from the model's context window size. Adjust it based on your project's actual size.

```json
{
  "context_limit": 100000
}
```
