# LISA User Guide

This guide provides detailed instructions on how to use LISA (Layered Isolated Scoped Agent) for your daily development workflow.

## Installation

LISA is designed to be a zero-dependency drop-in tool. Because LISA is not currently distributed via package managers like pip, you must clone the source code to use it in a new project.

### Global Installation (Recommended)

Install LISA once and use it across all projects. This is the easiest way to use LISA across multiple blank projects.

1. **Clone the repository to a global location:**

    ```bash
    mkdir -p ~/.agent
    git clone https://github.com/dutchdutchdutch/lisa.git ~/.agent/lisa
    ```

2. **Create a global alias:**

    Add this to your shell profile (`~/.bashrc`, `~/.zshrc`):

    ```bash
    alias lisa='~/.agent/lisa/src/lisa/lisa.sh'
    ```
    
    *Remember to reload your shell profile (e.g., `source ~/.zshrc`) after adding the alias.*

3. **Initialize and Setup in your project:**

    Navigate to your blank project directory and run:

    ```bash
    cd my-blank-project
    lisa init --setup
    ```

    This command will:
    - Create `.lisa/`, `.lisa/skills/`, and `.lisa/archive/`.
    - Create a default `.lisa/config.yaml`.
    - Copy core skills (Polish Pass, Refactor Gate, UI Handoff) to `.lisa/skills/`.
    - **Automated Hook Activation**: Copy a resident bridge script (`.lisa/lisa.sh`) and inject git hooks into `.git/hooks/` (post-commit and pre-push) that call LISA automatically.

4. **Install dependencies:**

    ```bash
    pip install tiktoken
    ```

    If using a virtual environment, activate it first. Without tiktoken, LISA falls back to a character-based token estimate.

5. **Verify installation:**

    ```bash
    lisa version
    ```

> **Note:** With global installation, LISA discovers the project root dynamically by walking up from the current directory to find `.git/`. Per-project configuration (`.lisa/config.json`) still lives in each project root.

### Local Project Installation

If you prefer to set up LISA contained entirely within a single project (for example, to ensure all teammates use the same version without global setup):

1. **Clone LISA into your project:**

    ```bash
    # Inside your blank project root
    mkdir -p .agent
    git clone https://github.com/dutchdutchdutch/lisa.git .agent/lisa
    ```

2. **Set up a local alias:**

    ```bash
    alias lisa='./.agent/lisa/src/lisa/lisa.sh'
    ```

3. **Initialize and Setup:**

    ```bash
    lisa init --setup
    ```

4. **Install dependencies:**

    ```bash
    pip install tiktoken
    ```

### Manual Installation (Backup)

If you prefer to set up LISA manually or are in an environment where the installer isn't suitable, follow these steps:

1. **Copy files:**

    ```bash
    # Assuming you have the LISA source somewhere
    mkdir -p .lisa/skills
    cp -r <lisa-source>/skills/* .lisa/skills/
    ```

2. **Create config**: Create a `.lisa/config.yaml` with your project settings.

3. **Bridge script**: Copy the `lisa.sh` script to your project root or `.lisa/` and make it executable.

### Directory Layout

```
project-root/
├── .agent/
│   └── lisa/               # LISA - context governance
│       ├── lisa.sh         # shell entry point
│       ├── __main__.py
│       ├── commands.py
│       ├── ...
│       └── skills/
│           ├── polish-pass/
│           ├── refactor-gate/
│           └── ...
├── .lisa/                  # runtime state (auto-created)
│   ├── config.json
│   └── state.json
└── ...
```

> All examples in this guide assume the `lisa` alias is configured. If not using the alias, substitute `./.agent/lisa/lisa.sh` for `lisa`.

## Configuration

LISA uses a hierarchical configuration system.

1.  **Global User Config**: `~/.lisa/config.json` (apply to all your projects).
2.  **Project Config**: `./.lisa/config.json` (overrides user config for this specific project).

**Example `config.json`:**

```json
{
  "strictness": "strict",
  "spike_mode_allowed": true,
  "context_limit": 100000,
  "context_check_interval": 600,
  "scan_ignores": [],
  "hooks_mode": "auto",
  "lifecycle_hooks": {
    "story-kickoff": [],
    "story-in-dev": ["lisa turns"],
    "story-test": ["lisa refactor"],
    "story-complete": ["lisa polish"],
    "context-reset": ["lisa checkpoint"]
  }
}
```

**Configuration Keys:**

| Key | Default | Description |
|-----|---------|-------------|
| `strictness` | `"strict"` | TDD enforcement level |
| `spike_mode_allowed` | `true` | Whether spike mode is permitted |
| `context_limit` | `200000` | Workspace token budget |
| `turn_limit` | `20` | Turn count for RED status |
| `turn_warning_threshold` | `12` | Turn count for AMBER status |
| `skill_base_path` | `".lisa/skills"` | Path to skill instructions (supports `{project-root}`) |
| `hooks_mode` | `"auto"` | Remediation mode |
| `lifecycle_hooks` | (see above) | Map of lifecycle events to LISA commands |

> **Note:** `context_limit` is a **workspace size budget** (files on disk), not a model context window limit. The default of 100,000 tokens is roughly where an agent needs to be disciplined about selective file loading. Adjust based on your project size. For context window pressure signals, see `lisa context health` which uses turn-based metrics.

### Scan Exclusions

LISA's workspace scanner estimates token count by reading all text files in your project. To avoid inflated counts, LISA automatically skips these directories:

`.git`, `.lisa`, `.bmad`, `_bmad`, `.agent`, `__pycache__`, `venv`, `.venv`, `env`, `.env`, `.tox`, `.nox`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.eggs`, `*.egg-info`, `htmlcov`, `site-packages`, `node_modules`, `dist`, `build`, `coverage`, `out`, `target`, `.DS_Store`

If your project has additional directories that should be excluded (data directories, vendor folders, generated code, etc.), add them to `scan_ignores` in your project's `.lisa/config.json`:

```json
{
  "scan_ignores": ["data", "vendor", "generated", "logs", ".terraform"]
}
```

These are merged with the built-in defaults — you only need to list what's not already covered.

## Commands

### `lisa verify-fail <test_file>`

**Purpose**: Verifies that a new test fails as expected (RED State). This is the "TDD Audit".

**Usage**:

```bash
lisa verify-fail tests/test_my_feature.py
```

*   **Automated Mode (Default)**: Runs the test.
    *   If the test **FAILS**: Success (Exit Code 0).
    *   If the test **PASSES**: Error (Exit Code 1). You must fix the test to fail before implementing logic.
*   **Interactive Mode**:
    *   Use `--interactive` to pause for confirmation before running the check.
    *   `lisa verify-fail tests/test_my_feature.py --interactive`

### `lisa verify-pass <test_file>`

**Purpose**: Verifies that a test passes (GREEN State). Run this after implementing your feature.

**Usage**:

```bash
lisa verify-pass tests/test_my_feature.py
```

*   Runs the test normally.
*   If the test **PASSES**: Success (Cycle Complete).
*   If the test **FAILS**: Error. You need to fix your implementation.

### `lisa spike`

**Purpose**: Disengages the "Safety Harness" (TDD enforcement), allowing you to prototype rapidly without verification blocks.

**Usage**:

```bash
lisa spike
```

*   Sets mode to `SPIKE`.
*   All consequent `verify-fail` or `verify-pass` commands will **SKIP** verification and exit with success, logging a warning.
*   Useful for: Experimental coding, learning new APIs, or throwing away code later.

### `lisa normal`

**Purpose**: Re-engages the Safety Harness (TDD enforcement). Run this when you are done spiking or bypassing.

**Usage**:

```bash
lisa normal
```

*   Sets mode to `NORMAL`.
*   Restores strict TDD enforcement.

### `lisa bypass-tdd`

**Purpose**: Skips TDD enforcement for the current task. Intended for **non-functional changes** (docs, formatting, config) where TDD is overhead.

**Usage**:

```bash
lisa bypass-tdd
```

*   Sets mode to `BYPASS_TDD`.
*   Similar to Spike Mode, but indicates a deliberate choice for non-functional work rather than hacking.
*   Remember to run `lisa normal` when finished.

### `lisa analyze <file_path>`

**Purpose**: Performs Impact Analysis to find other files that depend on the target file. Use this before refactoring or to understand what tests to run.

**Usage**:

```bash
lisa analyze src/utils.py
```

*   **Output**: Lists all files in the project that import the target file.
*   **Note**: Requires you to be in the project root or a subdirectory of a LISA project.

### `lisa context`

**Purpose**: specific Analysis of your current workspace's token usage. Use this to check if you are approaching the context window limit.

**Usage**:

```bash
lisa context
```

*   **Output includes**:
    *   **Traffic Light**: `[🟢]`, `[🟡]`, or `[🔴]` indicating health.
    *   **Token Count**: Estimated tokens in the workspace.
    *   **Usage %**: Percentage of the configured `context_limit`.
*   **Automatic Checks**: LISA automatically checks this in the background (Lazy Check) and updates the Traffic Light on every command.

### `lisa workspace`

**Purpose**: Reports the token footprint of your project's source files on disk. Use this to understand whether the project is large enough to risk overwhelming an agent's context window if loaded carelessly.

**Usage**:

```bash
lisa workspace
```

*   **Output includes**:
    *   **Token Count**: Estimated tokens across all source files (with configured budget).
    *   **File Count**: Number of files scanned.
    *   **Usage %**: Percentage of the configured `context_limit` with color-coded icon.
*   **Important**: This measures files on disk, not the agent's active context window. A large workspace doesn't mean your context is full — it means you should be selective about what you load.

**Workspace Size Thresholds**:

| Workspace Size | Agent Impact | Action |
|---|---|---|
| < 50K tokens | Agent can read most files comfortably | No concerns |
| 50K - 100K tokens | Agent needs to be selective about file loading | Use targeted reads |
| 100K - 300K tokens | Agent cannot hold the full project picture | Load only relevant modules |
| 300K+ tokens | Single-agent reasoning breaks down | Consider splitting into components |

### `lisa reset`

**Purpose**: Archives the current session and resets the context state. Use this when the traffic light turns **RED** or you want to start a fresh task without losing history.

**Usage**:

```bash
lisa reset
```

*   **Archival**: Copies everything in `.lisa/` (state, scope, layers, config) to `.lisa/archive/{timestamp}/`.
*   **Reset**: Clears the active state to default (Green/Idle) and removes `scope.json` so scope doesn't leak across stories.
*   **Result**: You are ready to start a new task with a clean slate.

### `lisa turns`

**Purpose**: Manages the agentic turn counter. Used by the Turn Watchdog to track reasoning cycles and detect logic drift.

**Auto-tracking**: Turns are automatically incremented once per agent response cycle. Every invocation of any `lisa` command triggers a deduplication check — if the current epoch second differs from the last auto-increment, the counter advances by 1. Multiple `lisa` commands within the same response (same second) count as a single turn.

**Usage**:

```bash
lisa turns          # Report current turn count (auto-tracked)
lisa turns 7        # Explicitly set turn to 7 (overrides auto-tracking)
```

*   **Report mode** (no args): Shows current turn count.
*   **Set mode** (`lisa turns <N>`): Explicitly sets the turn counter — overrides the auto-tracked value.
*   **Auto-tracking**: The counter increments automatically on each agent response, so agents no longer need to explicitly call `lisa turns <N>` for tracking to work. Unstructured or exploratory sessions are covered by default.
*   The turn count is displayed in `lisa context` output.
*   **Turn 12 (Goldfish Threshold):** Triggers a "Logic Alignment Check".
*   **Turn 20+ (Compaction Recovery):** Recommends a "Grounding Snapshot".

### `lisa polish`

**Purpose**: Loads the Polish Pass skill protocol for epic-level quality auditing. Runs a multi-phase scan for duplicate code, naming inconsistencies, error handling gaps, magic values, and performance/security issues.

**Usage**:

```bash
lisa polish
```

*   Reads and outputs the Polish Pass skill protocol.
*   Appends **scope context** (in-scope test counts, layer status, deferred failures) when scope is set, guiding the agent to use scoped layer verification for the regression gate instead of a full test suite.
*   Follow the printed protocol to execute the Polish Pass.
*   Best used at the end of an epic or sprint.

### `lisa refactor`

**Purpose**: Loads the Refactor Gate skill protocol. Guides a structured refactor loop — improve code quality without changing behavior, then verify impact on dependent modules.

**Usage**:

```bash
lisa refactor
```

*   Reads and outputs the Refactor Gate skill protocol.
*   Appends **scope context** (in-scope test counts, layer status, deferred failures) when scope is set, guiding the agent to use `lisa verify-layer` for impact verification instead of manual impact analysis.
*   Follow the printed protocol to execute the Refactor Gate.
*   Runs automatically at the `story-test` lifecycle stage.

### `lisa hooks <event>`

**Purpose**: Triggers lifecycle hooks for a given event. Hooks are configured in `.lisa/config.yaml` and execute LISA commands at key story lifecycle boundaries.

**Usage**:

```bash
lisa hooks story-complete
```

**Automated Git Integration**: 
When initialized with `lisa init --setup`, LISA automatically installs git hooks that call these lifecycle events:
- **`post-commit`**: Calls `hooks story-in-dev` to track turns and check health after every commit.
- **`pre-push`**: Calls `hooks story-test` to ensure the Refactor Gate passes before pushing code.

**Valid Events:**

| Event | Default Hook | Description |
|-------|-------------|-------------|
| `story-kickoff` | (none) | When a story starts |
| `story-in-dev` | `lisa turns` | Each development turn. Automatically triggered by `post-commit` git hook. |
| `story-test` | `lisa refactor` | After green phase. Automatically triggered by `pre-push` git hook. |
| `story-complete` | `lisa polish` | Story marked complete. Runs polish + health check. |
| `context-reset` | `lisa checkpoint` | After context reset. Archives and clears scope state. |

*   **`story-complete`** uses a special orchestrator: runs polish, context health check, and conditional remediation (context-curator, externalizer, session-management) based on health status. Also fires automatically when `lisa verify-layer` marks all layers (UNIT + INTEGRATION) as CLEAN.
*   **Scope-aware verification:** When scope is set (`lisa scope`), both the Refactor Gate and Polish Pass use `lisa verify-layer` instead of manual impact analysis or full regression. Scope presence acts as an implicit mode switch — no configuration needed.
*   **Fail-Open:** Hook failures are logged as warnings and never block workflow.

### `lisa version`

**Purpose**: Displays version and diagnostic information. Use this to verify installation.

**Usage**:

```bash
lisa version
```

*   **Output includes**: LISA version, Python version, detected project root, and tiktoken availability.
*   Use this as a smoke test after installation to confirm the full shell-to-Python chain is working.

## Verifying LISA is Running

After installation, use these commands to confirm LISA is operational:

**Quick check** — confirms installation and reports diagnostics:

```bash
lisa version
```

**Functional check** — confirms state management and token counting work:

```bash
lisa context health
```

**From agent chat** — paste this into your coding agent to verify LISA is accessible:

> Run `lisa version` and confirm LISA is installed correctly.

## Troubleshooting

-   **"python3 not found"**: Ensure Python is installed and in your PATH.
-   **"Could not determine project root"**: Ensure you are running `lisa` from within a git repository. LISA walks up from the current directory to find the project root.
-   **"Context Limit Exceeded"**: Run `lisa reset` to archive and clear your session.
-   **"[🔴] Context Red"**: Your workspace is too large. Clean up files or run `lisa reset`.
-   **"Please fix permissions on .lisa/"**: Check file permissions on the `.lisa/` directory. LISA requires read/write access.
-   **"Polish Pass skill not found"**: Ensure `.agent/lisa/skills/polish-pass/skill.md` exists relative to your project root.
-   **"Unknown lifecycle event"**: Check valid events with `lisa hooks` (no arguments).
