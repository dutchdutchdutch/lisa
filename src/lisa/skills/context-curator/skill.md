---
name: curating-context
description: Maintains context hygiene by summarizing and compacting conversation history when token usage thresholds are breached. Use when context usage exceeds 70%, the user requests a summary or compaction, or the conversation becomes unwieldy.
---

# Context Curator Skill

**Role:** You are the **Context Curator**. Your goal is to maximize the "Signal-to-Noise" ratio of the conversation history.

## Trigger
Activate this skill when:
1.  `lisa context` reports usage > **70%** (AMBER state).
2.  The User explicitly requests a "summary" or "compaction".
3.  You observe that the conversation history is becoming unwieldy or repetitive.

## The Rolling Summary Protocol

When the trigger condition is met, you must perform a **Context Compaction** operation. Do not ask for permission; just do it as part of your response.

### 1. Analysis (The "Cut")
Identify the **Middle 60%** of the conversation history.
-   **Keep:** The original System Instructions (The "Constitution").
-   **Keep:** The user's most recent request and the immediate context (last 3-4 turns).
-   **Compress:** Everything in between.

### 2. Summarization
Replace the "Middle 60%" with a concise, high-density summary paragraph.
-   **Discard:**  Raw Code blocks that have already been implemented.
-   **Discard:**  Back-and-forth debugging chat that is resolved.
-   **Retain:**  Key Architecture Decisions (ADRs) made during the chat.
-   **Retain:**  State changes (files created, bugs fixed).
-   **Retain:**  Pending Tasks.

### 3. Pinning (The Anchor)
Explicitly restate or "pin" critical directives at the end of your summary to ensure they remain in focus:
-   Current Mode (e.g., "Mode: NORMAL - TDD Enforced").
-   Current Task.

## Example Output

> **[Context Curator]** 
> *Context usage exceeded 70%. Performing hygiene pass.*
> 
> **Summary of previous turns:**
> User requested implementation of Context Health logic. Agent implemented `context_stats.py` and updated `commands.py`. 
> Issues with "Lazy Check" were identified and resolved in `logger.py`. 
> All tests for Epic 3 passed. 
> 
> **Current Focus:**
> Proceeding with Epic 4: Agentic Context Management.
