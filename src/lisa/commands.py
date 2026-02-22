import sys
import os
import time
from .runner import run_test
from .archiver import archive_session, reset_session
from .analysis import find_importers
from .utils import find_project_root
from .context_stats import scan_workspace, get_context_health, update_cache, get_cached_health_icon, get_cache_status, build_ignores, get_turn_health
from .config import ConfigManager
from .logger import print_with_status
from .state import StateManager, LISA_MODES, ContextActivity
from .hooks import LIFECYCLE_EVENTS, run_hooks, run_story_complete
from .classifier import classify_file, classify_all, persist_layers, LAYER_UNIT, LAYER_INTEGRATION
import shutil
# Skills are bundled inside the package directory
_SKILL_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")

from .scope import (
    derive_modified_files_from_git, derive_scope, persist_scope, load_scope, clear_scope,
    get_layer_status, update_layer_status, get_layer_failure_counts,
    get_in_scope_tests_for_layer,
    check_layer_advancement, is_file_in_scope, get_all_tests_for_layer,
    record_deferred_failures, get_deferred_failures, record_ui_handoff, LAYER_ORDER,
    STATUS_CLEAN, STATUS_FAILING, STATUS_NOT_RUN,
)

def resolve_skill_path(project_root, skill_filename, internal_skill_rel_path):
    """
    Resolves skill path based on config, with {project-root} support and internal fallback.
    """
    try:
        config = ConfigManager(project_root=project_root).load()
        skill_path_config = config.get("skill_base_path", ".lisa/skills")
        
        # Replace {project-root} placeholder
        if project_root and "{project-root}" in skill_path_config:
            skill_path_config = skill_path_config.replace("{project-root}", project_root)
        
        # Resolve path
        if project_root and not os.path.isabs(skill_path_config):
            local_skill_base = os.path.join(project_root, skill_path_config)
        else:
            local_skill_base = skill_path_config
            
        skill_path = os.path.join(local_skill_base, skill_filename)
        
        if os.path.exists(skill_path):
            return skill_path
    except Exception:
        pass

    # Fallback to internal
    return os.path.join(_SKILL_BASE, internal_skill_rel_path)

def check_mode_bypass(project_root=None):
    """Checks if current mode allows bypassing verification."""
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    state = state_manager.load()
    mode = state.get("mode", LISA_MODES.NORMAL)

    if mode in [LISA_MODES.SPIKE, LISA_MODES.BYPASS_TDD]:
        print_with_status(f"[{mode}] MODE ACTIVE: Skipping Verification.")
        print_with_status("       Warning: Code is unverified.")
        return True
    return False


def _print_scope_context(project_root):
    """Print scope context summary for skill commands (refactor, polish).

    Shows in-scope test counts, layer status, and deferred failures
    when scope is set, or a fallback message when not.
    """
    scope = load_scope(project_root)
    if scope is None:
        print_with_status("Scope: Not set — using manual impact analysis flow.", status_icon="ℹ️")
        return

    print_with_status("Scope Context", status_icon="🔭")
    print("---------------------------------------------------")

    # In-scope test counts by layer
    in_scope = scope.get("in_scope_tests", {})
    for layer_name in LAYER_ORDER:
        tests = in_scope.get(layer_name, [])
        print_with_status(f"  {layer_name}: {len(tests)} in-scope test(s)", status_icon="📋")

    # Layer status
    status = get_layer_status(project_root)
    if status:
        for layer_name in LAYER_ORDER:
            layer_state = status.get(layer_name, STATUS_NOT_RUN)
            icon = "🟢" if layer_state == STATUS_CLEAN else "🔴" if layer_state == STATUS_FAILING else "⬜"
            print_with_status(f"  {layer_name} status: {layer_state}", status_icon=icon)

    # Deferred failures
    deferred = get_deferred_failures(project_root)
    if deferred:
        total = sum(len(files) for files in deferred.values())
        print_with_status(f"  Deferred failures: {total} (outside story scope)", status_icon="⚠️")


def verify_fail(args):
    """
    Verifies that a test fails.
    Usage: lisa verify-fail <test_file> [--interactive]
    """
    if not args:
        print("Usage: lisa verify-fail <test_file> [--interactive]")
        return 1
        
    test_file = args[0]
    interactive = "--interactive" in args
    
    print_with_status(f"TDD Gate: Verifying RED State for {test_file}")
    print("---------------------------------------------------")

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    if check_mode_bypass(project_root):
        return 0

    # AC3: Scope-aware warning for explicit files
    _warn_if_outside_scope(project_root, test_file)

    # 1. Verification (Interactive Optional)
    if interactive:
        print(f"File: {test_file}")
        try:
            response = input("Does this test accurately reflect the requirement and is expected to fail? [y/N] ").strip().lower()
        except KeyboardInterrupt:
            print("\n[LISA] Aborted by user.")
            return 1

        if response != 'y':
            print_with_status("Verification rejected. Please revise the test.")
            return 1
    else:
        print_with_status("Automated Mode (Non-interactive)")

    # 2. Automated Fail Verification
    print_with_status(f"Running test (Expecting Failure)...")
    ret_code = run_test(test_file)

    if ret_code == 0:
        print_with_status(f"[ERROR] Test Passed! Expected failure (RED state).", status_icon="🔴")
        print_with_status("Please check that the test is actually asserting the new behavior.", status_icon="🔴")
        return 1
    else:
        print_with_status(f"[SUCCESS] RED State Verified. Test failed as expected.")
        return 0

def verify_pass(args):
    """
    Verifies that a test passes.
    Usage: lisa verify-pass <test_file>
    """
    if not args:
        print("Usage: lisa verify-pass <test_file>")
        return 1

    test_file = args[0]
    
    print_with_status(f"TDD Gate: Verifying GREEN State for {test_file}")
    print("---------------------------------------------------")

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    if check_mode_bypass(project_root):
        return 0

    # AC3: Scope-aware warning for explicit files
    _warn_if_outside_scope(project_root, test_file)

    # 1. Automated Pass Verification
    print_with_status("Running test (Expecting Success)...")
    ret_code = run_test(test_file)
    
    if ret_code != 0:
        print_with_status("[ERROR] Test Failed! Expected success (GREEN state).", status_icon="🔴")
        print_with_status("Please fix the implementation or test.", status_icon="🔴")
        return 1
    else:
        print_with_status("[SUCCESS] Test Passed. Cycle Complete.")

        # Fire story-complete lifecycle hooks (AC1)
        # This runs health check + remediation via run_story_complete()
        try:
            run_story_complete(project_root)
        except Exception:
            pass  # NFR3: Fail-open
            
        return 0

def analyze_deps(args):
    """
    Analyzes file dependencies to find potential impact zones.
    Usage: lisa analyze <file_path>
    """
    if not args:
        print("Usage: lisa analyze <file_path>")
        return 1
        
    file_path = args[0]
    
    if not os.path.exists(file_path):
        print(f"[LISA] Error: File not found: {file_path}")
        return 1
        
    print_with_status(f"Impact Analysis: Finding dependents of {file_path}")
    print("---------------------------------------------------")
    
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print("[LISA] Error: Could not determine project root. Are you inside a LISA project?")
        return 1

    importers = find_importers(file_path, project_root)
    
    if not importers:
        print_with_status("No direct dependents found.")
    else:
        print_with_status(f"Found {len(importers)} dependent files:")
        for imp in importers:
            print_with_status(f"  - {imp}")
            
    return 0

def enable_spike(args):
    """
    Enables Spike Mode (Safety Harness Disengaged).
    Usage: lisa spike
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
    
    # Initialize State Manager
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()

    # Update state to SPIKE
    state_manager.update("mode", LISA_MODES.SPIKE)
    
    print("\n[LISA] Safety Harness Disengaged")
    print("       MODE: SPIKE (TDD Enforcement Disabled)")
    return 0

def disable_spike(args):
    """
    Disables Spike Mode (Re-engages Safety Harness).
    Usage: lisa normal
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
    
    # Initialize State Manager
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()

    # Update state to NORMAL
    state_manager.update("mode", LISA_MODES.NORMAL)
    
    print("\n[LISA] Safety Harness Engaged")
    print("       MODE: NORMAL (TDD Enforcement Active)")
    return 0

def bypass_tdd(args):
    """
    Enables TDD Bypass Mode (Specific to a task).
    Usage: lisa bypass-tdd
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
    
    # Initialize State Manager
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()

    # Update state to BYPASS_TDD
    state_manager.update("mode", LISA_MODES.BYPASS_TDD)
    
    print("\n[LISA] TDD Gate Bypassed")
    print("       MODE: BYPASS_TDD (Verification Skipped)")
    return 0

def turns(args):
    """
    Manages the agentic turn counter.
    Usage: lisa turns        (report current turn)
           lisa turns <N>    (set turn to N)
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
        
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()

    if not args:
        # Report mode: show current turn count
        state = state_manager.load()
        current_turn = state.get("turn_count", 0)
        print_with_status(f"Current Turn: {current_turn}", status_icon="⏱️")
        return 0
    
    # Set mode: set turn to explicit value
    try:
        turn_number = int(args[0])
    except ValueError:
        print_with_status(f"Error: '{args[0]}' is not a valid turn number.", status_icon="🔴")
        return 1
    
    if turn_number < 0:
        print_with_status("Error: Turn number must be non-negative.", status_icon="🔴")
        return 1
    
    state_manager.update("turn_count", turn_number)
    print_with_status(f"Turn Counter Set: {turn_number}", status_icon="⏱️")
    return 0

def check_context(args):
    """
    Checks context health: turn-based pressure (primary) and workspace size (supplementary).
    Usage: lisa context [force]
    """
    print_with_status("Context Analysis")
    print("-----------------------------------")

    force = "force" in args

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    config = ConfigManager(project_root=project_root).load()

    # --- Primary: Context Pressure (Turns) ---
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    state = state_manager.load()
    turn_count = state.get("turn_count", 0)

    turn_warning = config.get("turn_warning_threshold", 12)
    turn_limit_val = config.get("turn_limit", 20)

    turn_health = get_turn_health(turn_count, turn_warning, turn_limit_val)

    turn_icon = "🟢"
    if turn_health == "RED":
        turn_icon = "🔴"
    elif turn_health == "AMBER":
        turn_icon = "🟡"

    print_with_status("Context Pressure (Turns)")
    print("-----------------------------------")
    print_with_status(f"Current Turn: {turn_count}", status_icon=turn_icon)
    print_with_status(f"Status: {turn_health}", status_icon=turn_icon)

    if turn_health == "RED":
         print_with_status(f"CRITICAL: Turn Limit Exceeded (>{turn_limit_val}).", status_icon="🔴")
         print_with_status("    Action Required: Perform 'Context Purge' (Compact & Reset).", status_icon="🔴")
    elif turn_health == "AMBER":
         print_with_status(f"WARNING: Approaching Turn Limit ({turn_warning}-{turn_limit_val}).", status_icon="🟡")
         print_with_status("    Action Recommended: Check for drift. Consider wrapping up story.", status_icon="🟡")

    # --- Supplementary: Workspace Size (On-Disk) ---
    print("")
    print_with_status("Workspace Size (On-Disk)")
    print("-----------------------------------")

    limit = config.get("context_limit", 20000)
    interval = config.get("context_check_interval", 600)

    cache = get_cache_status(limit)
    last_update = cache.get("timestamp", 0)
    current_time = time.time()
    is_fresh = (current_time - last_update) < interval

    if is_fresh and not force and "token_count" in cache:
        token_count = cache["token_count"]
        print_with_status(f"Scanning workspace: {project_root} (Cached)", status_icon="ℹ️")
        file_count = "N/A (Cached)"
    else:
        print_with_status(f"Scanning workspace: {project_root}")
        ignores = build_ignores(config)
        token_count, file_count = scan_workspace(project_root, ignores=ignores)
        health = get_context_health(token_count, limit)
        update_cache(token_count, health)

    health = get_context_health(token_count, limit)

    token_icon = "🟢"
    if health == "AMBER":
        token_icon = "🟡"
    elif health == "RED":
        token_icon = "🔴"

    percentage = (token_count / limit) * 100

    print_with_status(f"Estimated Tokens: {token_count} / {limit}", status_icon=token_icon)
    print("    Approximation method across models for watchdog purposes. Not billing grade accurate.")
    print_with_status(f"Usage: {percentage:.1f}%", status_icon=token_icon)
    print_with_status(f"Status: {health}", status_icon=token_icon)

    if health == "RED":
         print_with_status("CRITICAL: Workspace token budget exceeded.", status_icon="🔴")
         print_with_status("    Action Required: Run 'lisa reset' or compact files.", status_icon="🔴")
    elif health == "AMBER":
         print_with_status("WARNING: Approaching workspace token budget.", status_icon="🟡")
         print_with_status("    Action Recommended: Review scan_ignores or increase context_limit.", status_icon="🟡")

    return 0

def reset_context(args):
    """
    Archives the current session and resets state.
    Usage: lisa reset
    """
    print_with_status("Initializing Session Reset...")
    
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
        
    # 1. Archive
    try:
        archive_path = archive_session(project_root)
        print_with_status(f"Session Archived to: {os.path.relpath(archive_path, project_root)}")
    except Exception as e:
        print_with_status(f"[ERROR] Archival failed: {e}", status_icon="🔴")
        return 1
        
    # 2. Reset
    if reset_session(project_root):
        print_with_status("State Reset to Defaults (Green/Idle).")
        # 3. Clear scope (archived in step 1, now remove to prevent leaking across stories)
        try:
            clear_scope(project_root)
            print_with_status("Scope cleared (archived above).")
        except Exception:
            pass  # Fail-open: scope.json may not exist
        print_with_status("System Ready for New Task.")
        # Fire context-reset lifecycle hooks
        try:
            run_hooks("context-reset", project_root)
        except Exception:
            pass  # NFR3: Fail-open
        return 0
    else:
        print_with_status("[ERROR] State reset failed.", status_icon="🔴")
        return 1

def checkpoint(args):
    """
    Validates that the external state artifact (todo.md) exists and is fresh.
    Usage: lisa checkpoint
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    # Load Config
    config = ConfigManager(project_root=project_root).load()
    filename = config.get("external_state_file", "todo.md")
    ttl = config.get("external_state_ttl", 600)

    todo_path = os.path.join(project_root, filename)
    
    # 1. Check Existence
    if not os.path.exists(todo_path):
        print_with_status(f"Error: '{filename}' not found.", status_icon="🔴")
        print_with_status(f"    Action Required: Create '{filename}' in project root.", status_icon="🔴")
        return 1
        
    # 2. Check Freshness (e.g., modified in last X seconds)
    mtime = os.path.getmtime(todo_path)
    now = time.time()
    elapsed = now - mtime
    
    if elapsed > ttl:
        print_with_status(f"Error: '{filename}' is stale (Last modified {int(elapsed/60)} mins ago).", status_icon="🔴")
        print_with_status(f"    Action Required: Update '{filename}' with current progress.", status_icon="🔴")
        return 1
        
    print_with_status(f"Checkpoint Verified ({filename}).", status_icon="🟢")
    return 0

def init_session(args):
    """
    Prints the content of the external state file to stdout for context injection.
    With --fix: diagnoses and repairs state persistence issues.
    Usage: lisa init [--fix] [--setup]
    """
    project_root = None
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        # If we're doing --setup, we can fallback to os.getcwd()
        if "--setup" in args or "setup" in args:
            project_root = os.getcwd()
        else:
            print_with_status("Error: Could not determine project root. Run 'lisa init --setup' to initialize.", status_icon="🔴")
            return 1

    # Handle --fix flag (Criteria 3: Self-Healing via Init)
    if "--fix" in args or "fix" in args:
        return _init_fix(project_root)

    # Handle --setup flag (Story 9.1: Universal Installer)
    if "--setup" in args or "setup" in args:
        return _init_setup(project_root)

    try:
        # Load Config
        config = ConfigManager(project_root=project_root).load()
        filename = config.get("external_state_file", "todo.md")

        todo_path = os.path.join(project_root, filename)
        
        if not os.path.exists(todo_path):
            print_with_status(f"Error: '{filename}' not found. Cannot initialize state.", status_icon="🔴")
            return 1
            
        print_with_status(f"Initializing Context from {filename}...", status_icon="🟢")
        print("---------------------------------------------------")

        with open(todo_path, "r") as f:
            content = f.read()
            print(content)
            
        print("---------------------------------------------------")
        print_with_status("Context Injected.", status_icon="🟢")
        return 0
        
    except PermissionError:
        print_with_status("Error: Permission denied. Please check permissions on .lisa/ or the project root.", status_icon="🔴")
        return 1
    except Exception as e:
        print_with_status(f"Error: {e}", status_icon="🔴")
        return 1


def _install_git_hook(hooks_dir, hook_name, command):
    """Install or update a git hook with a LISA handover command."""
    hook_path = os.path.join(hooks_dir, hook_name)
    handover = f"\n# LISA Handover: {hook_name}\n{command}\n"
    
    try:
        if os.path.exists(hook_path):
            with open(hook_path, "r") as f:
                content = f.read()
            if command not in content:
                # Ensure the file ends with a newline before appending
                prefix = "" if content.endswith("\n") else "\n"
                with open(hook_path, "a") as f:
                    f.write(prefix + handover)
                print_with_status(f"Updated git hook: {hook_name}", status_icon="🪝")
        else:
            with open(hook_path, "w") as f:
                f.write("#!/bin/bash\n" + handover)
            os.chmod(hook_path, 0o755)
            print_with_status(f"Created git hook: {hook_name}", status_icon="🪝")
    except Exception as e:
        print_with_status(f"[WARNING] Could not install git hook {hook_name}: {e}", status_icon="⚠️")

def _init_setup(project_root):
    """Standardized Repository Bootstrapping (Universal Installer)."""
    print_with_status("LISA Universal Installer (Story 9.1)", status_icon="🚀")
    print("---------------------------------------------------")

    # 1. Create directory structure
    dirs = [".lisa", ".lisa/skills", ".lisa/archive"]
    for d in dirs:
        path = os.path.join(project_root, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print_with_status(f"Created directory: {d}", status_icon="📁")

    # 2. Initialize default config
    config_path = os.path.join(project_root, ".lisa", "config.yaml")
    if not os.path.exists(config_path):
        default_config = """# LISA Project Configuration
# Epic 9: Standardized Repository Bootstrapping

strictness: strict
spike_mode_allowed: true
context_limit: 200000
turn_limit: 25
skill_base_path: ".lisa/skills"
installation_type: "resident"

# Life Cycle Hooks
lifecycle_hooks:
  story-kickoff: []
  story-in-dev: ["lisa turns"]
  story-test: ["lisa refactor"]
  story-complete: ["lisa polish"]
  context-reset: ["lisa checkpoint"]
"""
        with open(config_path, "w") as f:
            f.write(default_config)
        print_with_status("Initialized default config: .lisa/config.yaml", status_icon="⚙️")

    # 3. Copy skill instructions
    skills_to_map = {
        "polish-pass/skill.md": "polish.md",
        "refactor-gate/skill.md": "refactor.md",
        "ui-handoff/skill.md": "ui-handoff.md"
    }
    dest_skills_dir = os.path.join(project_root, ".lisa", "skills")
    
    for src_rel, dst_name in skills_to_map.items():
        src = os.path.join(_SKILL_BASE, src_rel)
        dst = os.path.join(dest_skills_dir, dst_name)
        
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            print_with_status(f"Copied core skill: {dst_name}", status_icon="📜")

    # 4. Copy lisa.sh as the resident bridge
    lisa_sh_src = os.path.join(os.path.dirname(__file__), "lisa.sh")
    lisa_sh_dst = os.path.join(project_root, ".lisa", "lisa.sh")
    if os.path.exists(lisa_sh_src):
        try:
            shutil.copy2(lisa_sh_src, lisa_sh_dst)
            os.chmod(lisa_sh_dst, 0o755)
            print_with_status("Created resident bridge: .lisa/lisa.sh", status_icon="🌉")
        except Exception as e:
            print_with_status(f"[WARNING] Could not create resident bridge: {e}", status_icon="⚠️")

    # 5. Inject git hooks
    git_dir = os.path.join(project_root, ".git")
    if os.path.isdir(git_dir):
        hooks_dir = os.path.join(git_dir, "hooks")
        # Use relative path in hooks so they are portable within the repo
        _install_git_hook(hooks_dir, "post-commit", ".lisa/lisa.sh hooks story-in-dev")
        _install_git_hook(hooks_dir, "pre-push", ".lisa/lisa.sh hooks story-test")

    print("---------------------------------------------------")
    print_with_status("Installation Complete. Activating...", status_icon="✅")
    
    # Run status to confirm
    return status_cmd([])


def _init_fix(project_root):
    """Self-healing: diagnose and repair state persistence issues."""
    print_with_status("Diagnosing state persistence...", status_icon="🔧")
    print("---------------------------------------------------")

    state_manager = StateManager(project_root=project_root)
    diagnosis = state_manager.diagnose()

    if diagnosis["healthy"]:
        print_with_status("State storage is healthy. No repairs needed.", status_icon="🟢")
        print_with_status(f"State file: {state_manager.state_file}", status_icon="ℹ️")
        return 0

    # Report issue
    print_with_status(f"Issue detected: {diagnosis['issue']}", status_icon="⚠️")
    print_with_status("Attempting repair...", status_icon="🔧")

    success, message = state_manager.repair()

    if success:
        # Verify write works
        try:
            state = state_manager.load()
            state_manager.save(state)
            print_with_status(message, status_icon="🟢")
            print_with_status(f"State file: {state_manager.state_file}", status_icon="ℹ️")
            print_with_status("Verified: state is writable.", status_icon="🟢")
            return 0
        except Exception as e:
            print_with_status(f"Repair succeeded but verification failed: {e}", status_icon="🔴")
            return 1
    else:
        print_with_status(f"Repair failed: {message}", status_icon="🔴")
        return 1

def context_status(args):
    """
    Reports the current activity of the context system.
    Usage: lisa context status
    """
    return status_cmd(args)

def status_cmd(args):
    """
    Unified Status & Activity Reporting.
    Usage: lisa status
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("LISA is Inactive (Not a LISA project)", status_icon="⚪")
        return 0

    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    state = state_manager.load()
    
    activity = state.get("activity", ContextActivity.IDLE)
    mode = state.get("mode", LISA_MODES.NORMAL)
    turn_count = state.get("turn_count", 0)
    
    # Activity mapping
    activity_map = {
        ContextActivity.IDLE: "Idle / Ready",
        ContextActivity.ACTIVE: "Idle / Ready",
        ContextActivity.MONITORING: "Actively Monitoring",
        ContextActivity.ARCHIVING: "Context Archiving",
        ContextActivity.COMPACTING: "Context Compacting",
        ContextActivity.CHECKPOINTING: "Saving Checkpoint",
        ContextActivity.RESETTING: "Resetting Session",
        ContextActivity.VERIFYING: "Verification Gate Active"
    }
    
    display_activity = activity_map.get(activity, f"Unknown ({activity})")
    
    # Token estimation (optional AC)
    health_icon = get_cached_health_icon()
    
    print_with_status("LISA Operational Status")
    print("---------------------------------------------------")
    print_with_status(f"Activity: {display_activity}", status_icon="📡")
    print_with_status(f"Mode:     {mode}", status_icon="🛡️")
    print_with_status(f"Turn:     {turn_count}", status_icon="🔢")
    
    # Show health preview if available
    config = ConfigManager(project_root=project_root).load()
    limit = config.get("context_limit", 160000)
    cache = get_cache_status(limit)
    if cache:
        tokens = cache.get("total_tokens", 0)
        print_with_status(f"Context:  ~{tokens} tokens {health_icon}", status_icon="🧠")
    
    return 0

def activate_cmd(args):
    """
    Explicitly activates LISA monitoring for the current project.
    Usage: lisa activate
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root. Run 'lisa init' first.", status_icon="🔴")
        return 1

    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    
    # Set to monitoring
    state_manager.update("activity", ContextActivity.MONITORING)
    
    print_with_status("LISA Activated", status_icon="🚀")
    print_with_status("Safety Harness Engaged — Actively Monitoring context health.", status_icon="🛡️")
    print_with_status("Use 'lisa status' to verify operational state.", status_icon="ℹ️")
    
    return 0

def workspace_size(args):
    """
    Reports workspace size metrics (token footprint of project files on disk).
    Usage: lisa workspace
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    print_with_status("Workspace Size (On-Disk)")
    print("---------------------")

    config = ConfigManager(project_root=project_root).load()
    limit = config.get("context_limit", 20000)
    ignores = build_ignores(config)
    token_count, file_count = scan_workspace(project_root, ignores=ignores)

    percentage = (token_count / limit) * 100 if limit > 0 else 0

    # Determine health icon based on workspace usage
    ws_icon = "🟢"
    if percentage > 90:
        ws_icon = "🔴"
    elif percentage >= 70:
        ws_icon = "🟡"

    print_with_status(f"Token Count: {token_count} / {limit}", status_icon="📊")
    print("    Approximation method across models for watchdog purposes. Not billing grade accurate.")
    print_with_status(f"File Count:  {file_count}", status_icon="📂")
    print_with_status(f"Usage:       {percentage:.1f}%", status_icon=ws_icon)
    return 0


def context_size(args):
    """
    Reports quantitative context metrics (workspace on-disk).
    Usage: lisa context size
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    print_with_status("Workspace Metrics (On-Disk)")
    print("---------------------")

    config = ConfigManager(project_root=project_root).load()
    ignores = build_ignores(config)
    token_count, file_count = scan_workspace(project_root, ignores=ignores)
    
    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    state = state_manager.load()
    turn_count = state.get("turn_count", 0)

    print_with_status(f"Token Count: {token_count}", status_icon="📊")
    print_with_status(f"File Count:  {file_count}", status_icon="📂")
    print_with_status(f"Turn Count:  {turn_count}", status_icon="⏱️")
    return 0

def context_health(args):
    """
    Reports context health: turn-based pressure (primary) and workspace size (secondary).
    Usage: lisa context health
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    config = ConfigManager(project_root=project_root).load()

    # --- Primary: Context Pressure (Turns) ---
    print_with_status("Context Health Report")
    print("---------------------")

    state_manager = StateManager(project_root=project_root)
    state_manager.warn_if_fallback()
    state = state_manager.load()
    turn_count = state.get("turn_count", 0)

    turn_warning = config.get("turn_warning_threshold", 12)
    turn_limit_val = config.get("turn_limit", 20)

    turn_health = get_turn_health(turn_count, turn_warning, turn_limit_val)

    turn_icon = "🟢"
    if turn_health == "RED":
        turn_icon = "🔴"
    elif turn_health == "AMBER":
        turn_icon = "🟡"

    print_with_status("Context Pressure (Turns)", status_icon=turn_icon)
    print_with_status(f"Turn Count:      {turn_count}", status_icon=turn_icon)
    print_with_status(f"Status:          {turn_health}", status_icon=turn_icon)

    if turn_health == "RED":
        print_with_status(f"CRITICAL: Turn Limit Exceeded (>{turn_limit_val}).", status_icon="🔴")
        print_with_status("    Action Required: Perform 'Context Purge' (Compact & Reset).", status_icon="🔴")
    elif turn_health == "AMBER":
        print_with_status(f"WARNING: Approaching Turn Limit ({turn_warning}-{turn_limit_val}).", status_icon="🟡")
        print_with_status("    Action Recommended: Check for drift. Consider wrapping up story.", status_icon="🟡")

    # --- Secondary: Workspace Size (Files on Disk) ---
    print("")
    limit = config.get("context_limit", 20000)
    ignores = build_ignores(config)
    token_count, _ = scan_workspace(project_root, ignores=ignores)

    from .drift_detection import DriftDetector
    detector = DriftDetector(token_count, limit)
    report = detector.check_health()

    sat_pct = int(report.saturation * 100)
    print_with_status("Workspace Size (Files on Disk)", status_icon="📂")
    print_with_status(f"Saturation:      {sat_pct}% ({token_count} / {limit} tokens)", status_icon="📈")
    print_with_status(f"Signal Ratio:    {report.signal_ratio}", status_icon="📡")
    print_with_status(f"Status:          {report.status}", status_icon="rx")

    return 0

def polish(args):
    """
    Outputs the Polish Pass skill instructions for agent or human consumption.
    Usage: lisa polish
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
    except Exception:
        project_root = None

    skill_path = resolve_skill_path(project_root, "polish.md", "polish-pass/skill.md")

    if not os.path.exists(skill_path):
        print_with_status(f"Error: Polish Pass skill not found at {skill_path}", status_icon="🔴")
        print_with_status("Install the skill or create it manually.", status_icon="💡")
        return 1

    try:
        with open(skill_path, "r") as f:
            content = f.read()
        
        print_with_status("Polish Pass: Loading skill instructions...", status_icon="🧹")
        print("=" * 60)
        print(content)
        print("=" * 60)
        _print_scope_context(project_root)
        print_with_status("Follow the protocol above to execute the Polish Pass.", status_icon="🧹")
        return 0
    except Exception as e:
        print_with_status(f"Error reading skill file: {e}", status_icon="🔴")
        return 1

def refactor(args):
    """
    Outputs the Refactor Gate skill instructions for agent or human consumption.
    Usage: lisa refactor
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
    except Exception:
        project_root = None

    skill_path = resolve_skill_path(project_root, "refactor.md", "refactor-gate/skill.md")

    if not os.path.exists(skill_path):
        print_with_status(f"Error: Refactor Gate skill not found at {skill_path}", status_icon="🔴")
        print_with_status("Install the skill or create it manually.", status_icon="💡")
        return 1

    try:
        with open(skill_path, "r") as f:
            content = f.read()
        
        print_with_status("Refactor Gate: Loading skill instructions...", status_icon="🔧")
        print("=" * 60)
        print(content)
        print("=" * 60)
        _print_scope_context(project_root)
        print_with_status("Follow the protocol above to execute the Refactor Gate.", status_icon="🔧")
        return 0
    except Exception as e:
        print_with_status(f"Error reading skill file: {e}", status_icon="🔴")
        return 1

def run_hooks_cmd(args):
    """
    Runs lifecycle hooks for a given event.
    Usage: lisa hooks <event>
    """
    if not args:
        print_with_status("Usage: lisa hooks <event>", status_icon="🔴")
        print_with_status(f"Valid events: {', '.join(LIFECYCLE_EVENTS)}", status_icon="ℹ️")
        return 1

    event_name = args[0]

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    if event_name not in LIFECYCLE_EVENTS:
        print_with_status(f"Error: Unknown lifecycle event '{event_name}'", status_icon="🔴")
        print_with_status(f"Valid events: {', '.join(LIFECYCLE_EVENTS)}", status_icon="ℹ️")
        return 1

    # story-complete uses the orchestrator
    if event_name == "story-complete":
        return run_story_complete(project_root)

    # All other events use the generic hook runner
    try:
        results = run_hooks(event_name, project_root)
        if not results:
            print_with_status(f"No hooks configured for '{event_name}'", status_icon="ℹ️")
        return 0
    except Exception as e:
        # NFR3: Fail-open
        print_with_status(f"[WARNING] Hook execution error: {e}", status_icon="⚠️")
        return 0

def classify(args):
    """
    Classifies test files into layers (UNIT, INTEGRATION).
    Usage: lisa classify <file>    (classify single file)
           lisa classify --all     (classify all test files, show overview)
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    config = ConfigManager(project_root=project_root).load()

    if not args or args[0] == "--all":
        # Layer overview mode (AC3)
        print_with_status("Test Layer Classification")
        print("---------------------------------------------------")

        results = classify_all(project_root, config)

        if not results:
            print_with_status("No test files found.", status_icon="⚠️")
            return 0

        # Persist for downstream use (AC1)
        layers_path = persist_layers(project_root, results)

        # Group by layer
        unit_files = [r for r in results if r["layer"] == LAYER_UNIT]
        integration_files = [r for r in results if r["layer"] == LAYER_INTEGRATION]

        # Count defaults for warning (AC2)
        default_classified = [r for r in results if r["method"] == "default"]

        print_with_status(f"UNIT: {len(unit_files)} files", status_icon="🧪")
        for r in unit_files:
            method_tag = f" [{r['method']}]" if r["method"] != "default" else ""
            print_with_status(f"  {r['file']}{method_tag}")

        print("")
        print_with_status(f"INTEGRATION: {len(integration_files)} files", status_icon="🔗")
        for r in integration_files:
            subtype_tag = f" ({r['subtype']})" if r.get("subtype") else ""
            print_with_status(f"  {r['file']}{subtype_tag} [{r['method']}]")

        print("")
        print_with_status(f"Total: {len(results)} files ({len(unit_files)} unit, {len(integration_files)} integration)", status_icon="📊")

        if default_classified:
            print_with_status(f"Note: {len(default_classified)} files classified as UNIT by default (no matching rule)", status_icon="⚠️")

        print_with_status(f"Layers persisted to: {os.path.relpath(layers_path, project_root)}", status_icon="💾")
        return 0

    else:
        # Single file mode (AC1)
        file_path = args[0]
        rel_path = os.path.relpath(file_path, project_root) if os.path.isabs(file_path) else file_path

        if not os.path.exists(os.path.join(project_root, rel_path)):
            print_with_status(f"Error: File not found: {rel_path}", status_icon="🔴")
            return 1

        result = classify_file(rel_path, config, project_root)

        subtype_display = f" ({result['subtype']})" if result.get("subtype") else ""
        print_with_status(f"File: {result['file']}")
        print_with_status(f"Layer: {result['layer']}{subtype_display}", status_icon="🏷️")
        print_with_status(f"Method: {result['method']}", status_icon="ℹ️")

        if result["method"] == "default":
            print_with_status("Note: No matching rule — classified as UNIT by default", status_icon="⚠️")

        return 0

def scope_cmd(args):
    """
    Derives and manages the test scope from modified files.
    Usage: lisa scope                    (show current scope)
           lisa scope <file1> <file2>    (set scope from explicit files)
           lisa scope --git              (derive scope from git diff)
           lisa scope --clear            (clear the current scope)
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    # Handle --clear
    if "--clear" in args:
        if clear_scope(project_root):
            print_with_status("Scope cleared.", status_icon="🟢")
        else:
            print_with_status("No scope was set.", status_icon="ℹ️")
        return 0

    # Handle --git (derive from version control)
    if "--git" in args:
        config = ConfigManager(project_root=project_root).load()
        base_branch = config.get("base_branch", "main")
        modified = derive_modified_files_from_git(project_root, base_branch=base_branch)
        if not modified:
            print_with_status("No modified source files found against base branch.", status_icon="⚠️")
            return 1

        scope = derive_scope(project_root, modified, base_branch=base_branch, source="git_diff")
        if scope is None:
            print_with_status("Error: No layer classification found. Run 'lisa classify --all' first.", status_icon="🔴")
            return 1

        persist_scope(project_root, scope)
        _print_scope(scope)
        return 0

    # Handle explicit file list
    file_args = [a for a in args if not a.startswith("--")]
    if file_args:
        scope = derive_scope(project_root, file_args, source="explicit")
        if scope is None:
            print_with_status("Error: No layer classification found. Run 'lisa classify --all' first.", status_icon="🔴")
            return 1

        persist_scope(project_root, scope)
        _print_scope(scope)
        return 0

    # Default: show current scope
    scope = load_scope(project_root)
    if scope is None:
        print_with_status("No scope is currently set.", status_icon="ℹ️")
        print_with_status("Use 'lisa scope <files>' or 'lisa scope --git' to set scope.", status_icon="💡")
        return 0

    _print_scope(scope)
    return 0


def _print_scope(scope):
    """Format and display scope data."""
    print_with_status("Scope Derivation")
    print("---------------------------------------------------")

    print_with_status(f"Source: {scope.get('source', 'unknown')}", status_icon="ℹ️")

    print("")
    print_with_status("Modified Files:", status_icon="📝")
    for f in scope.get("modified_files", []):
        print_with_status(f"  {f}")

    print("")
    print_with_status("Dependency Cone:", status_icon="🔗")
    for f in scope.get("dependency_cone", []):
        print_with_status(f"  {f}")

    in_scope = scope.get("in_scope_tests", {})
    unit_tests = in_scope.get(LAYER_UNIT, [])
    integration_tests = in_scope.get(LAYER_INTEGRATION, [])

    print("")
    print_with_status(f"In-Scope Tests — {LAYER_UNIT}: {len(unit_tests)}", status_icon="🧪")
    for t in unit_tests:
        print_with_status(f"  {t}")

    print_with_status(f"In-Scope Tests — {LAYER_INTEGRATION}: {len(integration_tests)}", status_icon="🔗")
    for t in integration_tests:
        print_with_status(f"  {t}")

    total = len(unit_tests) + len(integration_tests)
    print("")
    print_with_status(f"Total in-scope tests: {total}", status_icon="📊")


def _warn_if_outside_scope(project_root, test_file):
    """Emit a warning if the test file is outside the current story scope (AC3)."""
    in_scope = is_file_in_scope(project_root, test_file)
    if in_scope is False:
        print_with_status(
            f"Warning: '{test_file}' is outside the current story scope.",
            status_icon="⚠️"
        )


def verify_layer(args):
    """
    Runs scoped verification for a specific test layer.
    Usage: lisa verify-layer <unit|integration>
    """
    if not args:
        print_with_status("Usage: lisa verify-layer <unit|integration>", status_icon="🔴")
        return 1

    layer = args[0].upper()
    if layer not in LAYER_ORDER:
        print_with_status(f"Error: Unknown layer '{args[0]}'. Use 'unit' or 'integration'.", status_icon="🔴")
        return 1

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    if check_mode_bypass(project_root):
        return 0

    # No-scope fallback
    in_scope_tests = get_in_scope_tests_for_layer(project_root, layer)
    if in_scope_tests is None:
        print_with_status("No scope is set. Use 'lisa scope' to set scope first.", status_icon="⚠️")
        return 1

    # Layer advancement check
    allowed, reason = check_layer_advancement(project_root, layer)
    if not allowed:
        print_with_status(f"Layer gate blocked: {reason}", status_icon="🔴")
        return 1

    # Determine test set: all classified tests if available, else in-scope only
    all_tests = get_all_tests_for_layer(project_root, layer)
    tests = all_tests if all_tests is not None else in_scope_tests
    in_scope_set = set(in_scope_tests)

    if not tests:
        print_with_status(f"No in-scope {layer} tests to run.", status_icon="ℹ️")
        update_layer_status(project_root, layer, STATUS_CLEAN, failure_count=0)
        record_deferred_failures(project_root, layer, [])
        _fire_story_complete_if_all_clean(project_root)
        return 0

    print_with_status(f"Scoped Verification: {layer} Layer ({len(tests)} tests)")
    print("---------------------------------------------------")

    in_scope_failures = []
    out_of_scope_failures = []
    for test_file in tests:
        print_with_status(f"  Running: {test_file}")
        ret_code = run_test(test_file)
        if ret_code != 0:
            if test_file in in_scope_set:
                in_scope_failures.append(test_file)
            else:
                out_of_scope_failures.append(test_file)

    # Record deferred failures (AC4)
    record_deferred_failures(project_root, layer, out_of_scope_failures)

    # Display in-scope failures (main output)
    if in_scope_failures:
        update_layer_status(project_root, layer, STATUS_FAILING, failure_count=len(in_scope_failures))
        print_with_status(f"{layer} Layer: {len(in_scope_failures)} in-scope failure(s).", status_icon="🔴")
        for f in in_scope_failures:
            print_with_status(f"  FAILED: {f}", status_icon="🔴")
        # AC2 (Story 7.5): Fix-at-layer guidance for INTEGRATION
        if layer == LAYER_INTEGRATION:
            print_with_status(
                "Fix at the INTEGRATION layer. Do not revisit unit code unless a unit test also fails.",
                status_icon="ℹ️"
            )
    else:
        update_layer_status(project_root, layer, STATUS_CLEAN, failure_count=0)
        print_with_status(f"{layer} Layer: All in-scope tests passed.", status_icon="🟢")

    # Display out-of-scope failures in deferred section (AC2)
    if out_of_scope_failures:
        print_with_status(f"Deferred Failures ({len(out_of_scope_failures)} outside story scope — do not fix):", status_icon="⚠️")
        for f in out_of_scope_failures:
            print_with_status(f"  DEFERRED: {f}", status_icon="⚠️")

    # AC3: Only in-scope failures block layer progression
    if in_scope_failures:
        return 1

    # Fire story-complete lifecycle when all layers are clean
    _fire_story_complete_if_all_clean(project_root)
    return 0


def _fire_story_complete_if_all_clean(project_root):
    """Check if all layers are CLEAN and fire story-complete lifecycle if so."""
    status = get_layer_status(project_root)
    if status is None:
        return
    for layer_name in LAYER_ORDER:
        if status.get(layer_name, STATUS_NOT_RUN) != STATUS_CLEAN:
            return
    # All layers clean — fire story-complete lifecycle
    try:
        run_story_complete(project_root)
    except Exception:
        pass  # NFR3: Fail-open


def layer_status_cmd(args):
    """
    Displays the current status of each test layer.
    Usage: lisa layer-status
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    status = get_layer_status(project_root)
    if status is None:
        print_with_status("No scope is set. Layer status is not available.", status_icon="ℹ️")
        return 0

    failure_counts = get_layer_failure_counts(project_root) or {}

    print_with_status("Layer Status")
    print("---------------------------------------------------")

    for layer_name in LAYER_ORDER:
        layer_state = status.get(layer_name, STATUS_NOT_RUN)
        icon = "🟢" if layer_state == STATUS_CLEAN else "🔴" if layer_state == STATUS_FAILING else "⬜"
        if layer_state == STATUS_FAILING:
            count = failure_counts.get(layer_name, 0)
            display = f"{layer_state} ({count} in-scope failure{'s' if count != 1 else ''})"
        else:
            display = layer_state
        print_with_status(f"  {layer_name}: {display}", status_icon=icon)

    return 0


def ui_handoff(args):
    """
    Generates a manual UI test script for the story's affected behavior.
    Usage: lisa ui-handoff
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    if check_mode_bypass(project_root):
        return 0

    # Check scope exists
    scope = load_scope(project_root)
    if scope is None:
        print_with_status("No scope is set. Use 'lisa scope' to set scope first.", status_icon="⚠️")
        return 1

    # AC1: All automated layers must be CLEAN
    status = get_layer_status(project_root)
    if status is None:
        print_with_status("No layer status available. Run automated tests first.", status_icon="⚠️")
        return 1

    not_clean = []
    for layer_name in LAYER_ORDER:
        layer_state = status.get(layer_name, STATUS_NOT_RUN)
        if layer_state != STATUS_CLEAN:
            not_clean.append(f"{layer_name} ({layer_state})")
    if not_clean:
        print_with_status(
            f"Automated layers not clean: {', '.join(not_clean)}. "
            "Resolve automated failures before UI handoff.",
            status_icon="🔴"
        )
        return 1

    # Skill resolution
    skill_path = resolve_skill_path(project_root, "ui-handoff.md", "ui-handoff/skill.md")

    if not os.path.exists(skill_path):
        print_with_status(
            f"Error: UI Handoff skill not found at {skill_path}",
            status_icon="🔴"
        )
        return 1

    # AC2: Print scope context — modified files and dependency cone
    modified_files = scope.get("modified_files", [])
    dependency_cone = scope.get("dependency_cone", [])

    print_with_status("UI Test Handoff", status_icon="🧪")
    print("=" * 60)

    print_with_status("Modified Files:", status_icon="📝")
    for f in modified_files:
        print_with_status(f"  {f}")
    if not modified_files:
        print_with_status("  (none)")

    if dependency_cone:
        print_with_status("Dependency Cone:", status_icon="🔗")
        for f in dependency_cone:
            print_with_status(f"  {f}")

    print("---")

    # Print skill instructions
    try:
        with open(skill_path, "r") as f:
            content = f.read()
        print(content)
    except Exception as e:
        print_with_status(f"Error reading skill file: {e}", status_icon="🔴")
        return 1

    print("=" * 60)

    # AC4: Record handoff and note non-blocking completion
    record_ui_handoff(project_root)
    print_with_status(
        "UI verification pending — manual test script provided.",
        status_icon="🧪"
    )

    return 0
