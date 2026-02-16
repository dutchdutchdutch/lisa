import sys
import os
import time
from .runner import run_test
from .archiver import archive_session, reset_session
from .analysis import find_importers
from .utils import find_project_root
from .context_stats import scan_workspace, get_context_health, update_cache, get_cached_health_icon
from .config import ConfigManager
from .logger import print_with_status
from .state import StateManager, LISA_MODES, ContextActivity

def check_mode_bypass():
    """Checks if current mode allows bypassing verification."""
    state = StateManager().load()
    mode = state.get("mode", LISA_MODES.NORMAL)
# ... (rest of imports are fine, just appending archiver)

# ... (omitted functions)






def check_mode_bypass(project_root=None):
    """Checks if current mode allows bypassing verification."""
    state = StateManager(project_root=project_root).load()
    mode = state.get("mode", LISA_MODES.NORMAL)

    if mode in [LISA_MODES.SPIKE, LISA_MODES.BYPASS_TDD]:
        print_with_status(f"[{mode}] MODE ACTIVE: Skipping Verification.")
        print_with_status("       Warning: Code is unverified.")
        return True
    return False

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
    
    # 1. Automated Pass Verification
    print_with_status("Running test (Expecting Success)...")
    ret_code = run_test(test_file)
    
    if ret_code != 0:
        print_with_status("[ERROR] Test Failed! Expected success (GREEN state).", status_icon="🔴")
        print_with_status("Please fix the implementation or test.", status_icon="🔴")
        return 1
    else:
        print_with_status("[SUCCESS] Test Passed. Cycle Complete.")
        
        # Story Complete: Force Update Context Cache
        try:
            # We don't want to be too noisy, so maybe just do it.
            # But let's show we are doing it.
            config = ConfigManager(project_root=project_root).load()
            limit = config.get("context_limit", 20000)
            token_count, _ = scan_workspace(project_root)
            health = get_context_health(token_count, limit)
            update_cache(token_count, health)
        except Exception:
            pass # Fail silently
            
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
    
    # Update state to BYPASS_TDD
    state_manager.update("mode", LISA_MODES.BYPASS_TDD)
    
    print("\n[LISA] TDD Gate Bypassed")
    print("       MODE: BYPASS_TDD (Verification Skipped)")
    return 0

def check_context(args):
    """
    Checks the estimated token count of the workspace.
    Usage: lisa context
    """
    print_with_status("Context Analysis (The Scale)")
    print("-----------------------------------")
    
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1
        
    config = ConfigManager(project_root=project_root).load()
    limit = config.get("context_limit", 8000)
    
    print_with_status(f"Scanning workspace: {project_root}")
    token_count, file_count = scan_workspace(project_root)
    
    health = get_context_health(token_count, limit)
    
    # Force update cache
    update_cache(token_count, health)
    
    # Determine icon
    icon = "🟢"
    if health == "AMBER":
        icon = "🟡"
    elif health == "RED":
        icon = "🔴"
        
    percentage = (token_count / limit) * 100
    
    print_with_status(f"Estimated Tokens: {token_count} / {limit}", status_icon=icon)
    print_with_status(f"Usage: {percentage:.1f}%", status_icon=icon)
    print_with_status(f"Status: {health}", status_icon=icon)
    
    if health == "RED":
         print_with_status("CRITICAL: Context Limit Exceeded.", status_icon="🔴")
         print_with_status("    Action Required: Run 'lisa reset' or compact files.", status_icon="🔴")
    elif health == "AMBER":
         print_with_status("WARNING: Approaching Context Limit.", status_icon="🟡")
         print_with_status("    Action Recommended: Perform Context Curation (Summarize History).", status_icon="🟡")
         return 2 # Return code 2 for AMBER state (Scriptable trigger)
         
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
        print_with_status("System Ready for New Task.")
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
    prints the content of the external state file to stdout for context injection.
    Usage: lisa init
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    # Load Config
    config = ConfigManager(project_root=project_root).load()
    filename = config.get("external_state_file", "todo.md")

    todo_path = os.path.join(project_root, filename)
    
    if not os.path.exists(todo_path):
        print_with_status(f"Error: '{filename}' not found. Cannot initialize state.", status_icon="🔴")
        return 1
        
    print_with_status(f"Initializing Context from {filename}...", status_icon="🟢")
    print("---------------------------------------------------")
    try:
        with open(todo_path, "r") as f:
            content = f.read()
            print(content)
    except Exception as e:
        print_with_status(f"Error reading state file: {e}", status_icon="🔴")
        return 1
        
    print("---------------------------------------------------")
    print_with_status("Context Injected.", status_icon="🟢")
    return 0

def context_status(args):
    """
    Reports the current activity of the context system.
    Usage: lisa context status
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    state_manager = StateManager(project_root=project_root)
    state = state_manager.load()
    activity = state.get("activity", "unknown")
    
    # Capitalize for display
    display_activity = activity.capitalize() if activity else "Unknown"
    
    print_with_status("Context System Status")
    print("---------------------")
    print_with_status(f"Current Activity: {display_activity}", status_icon="ℹ️")
    return 0

def context_size(args):
    """
    Reports quantitative context metrics.
    Usage: lisa context size
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    print_with_status("Context Metrics")
    print("---------------------")
    
    token_count, file_count = scan_workspace(project_root)
    
    # We don't have turn count tracking yet (Story 4.3.3 Task 1 partial)
    # But acceptance criteria asks for it if available.
    # For now, we omit or show N/A.
    
    print_with_status(f"Token Count: {token_count}", status_icon="📊")
    print_with_status(f"File Count:  {file_count}", status_icon="📂")
    return 0

def context_health(args):
    """
    Reports qualitative context health and drift metrics.
    Usage: lisa context health
    """
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print_with_status("Error: Could not determine project root.", status_icon="🔴")
        return 1

    config = ConfigManager(project_root=project_root).load()
    limit = config.get("context_limit", 20000)
    
    token_count, _ = scan_workspace(project_root)
    
    from .drift_detection import DriftDetector
    detector = DriftDetector(token_count, limit)
    report = detector.check_health()
    
    print_with_status("Context Health Report")
    print("---------------------")
    
    # Format Saturation
    sat_pct = int(report.saturation * 100)
    print_with_status(f"Saturation:      {sat_pct}% ({token_count} / {limit} tokens)", status_icon="📈")
    print_with_status(f"Signal Ratio:    {report.signal_ratio}", status_icon="📡")
    # Drift Metric deferred to tech debt
    print_with_status(f"Status:          {report.status}", status_icon="rx") # rx maps to a health icon usually, or just use text
    
    return 0

