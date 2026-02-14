# LISA - Layered Isolated Scoped Agent

LISA is a context governance tool for AI-assisted development. It enforces a Red-Green-Refactor loop locally, manages context window health, and prevents premature commits without tests.

## Installation

LISA is designed as a zero-dependency drop-in tool.

1.  Copy `lisa.sh` to your project root.
2.  Copy the `scripts/lisa` directory to `scripts/lisa`.
3.  Ensure you have Python 3.8+ installed (Standard Library only).

## Usage

Run LISA commands via the shell wrapper:

```bash
./lisa.sh [command]
```

## Configuration

LISA uses a hierarchical configuration system. Settings are loaded in the following order (last one wins):

1.  **Defaults**: Internal hardcoded defaults.
2.  **User Config**: `~/.lisa/config.json` (Global user preferences).
3.  **Project Config**: `./.lisa/config.json` (Project-specific overrides).

### Example Configuration (`config.json`)

```json
{
  "strictness": "strict",
  "spike_mode_allowed": true,
  "context_limit": 8000
}
```

## State Management

LISA maintains its state in `.lisa/state.json`. It uses file locking to ensure state integrity across multiple concurrent shell sessions.
