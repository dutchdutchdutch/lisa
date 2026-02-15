import sys
import os
from .runner import run_test
from .analysis import find_importers
from .utils import find_project_root
from .context_stats import scan_workspace, get_context_health
from .config import ConfigManager



def check_mode_bypass():
    """Checks if current mode allows bypassing verification."""
    from .state import StateManager, LISA_MODES
    state = StateManager().load()
    mode = state.get("mode", LISA_MODES.NORMAL)

    if mode in [LISA_MODES.SPIKE, LISA_MODES.BYPASS_TDD]:
        print(f"\n[LISA] [{mode}] MODE ACTIVE: Skipping Verification.")
        print("       Warning: Code is unverified.")
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
    
    print(f"\n[LISA] TDD Gate: Verifying RED State for {test_file}")
    print("---------------------------------------------------")

    if check_mode_bypass():
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
            print("[LISA] Verification rejected. Please revise the test.")
            return 1
    else:
        print("[LISA] Automated Mode (Non-interactive)")
        
    # 2. Automated Fail Verification
    print(f"\n[LISA] Running test (Expecting Failure)...")
    ret_code = run_test(test_file)
    
    if ret_code == 0:
        print(f"\n[LISA] [ERROR] Test Passed! Expected failure (RED state).")
        print("Please check that the test is actually asserting the new behavior.")
        return 1
    else:
        print(f"\n[LISA] [SUCCESS] RED State Verified. Test failed as expected.")
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
    
    print(f"\n[LISA] TDD Gate: Verifying GREEN State for {test_file}")
    print("---------------------------------------------------")

    if check_mode_bypass():
        return 0
    
    # 1. Automated Pass Verification
    print("\n[LISA] Running test (Expecting Success)...")
    ret_code = run_test(test_file)
    
    if ret_code != 0:
        print(f"\n[LISA] [ERROR] Test Failed! Expected success (GREEN state).")
        print("Please fix the implementation or test.")
        return 1
    else:
        print(f"\n[LISA] [SUCCESS] Test Passed. Cycle Complete.")
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
        
    print(f"\n[LISA] Impact Analysis: Finding dependents of {file_path}")
    print("---------------------------------------------------")
    
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print("[LISA] Error: Could not determine project root. Are you inside a LISA project?")
        return 1

    importers = find_importers(file_path, project_root)
    
    if not importers:
        print("No direct dependents found.")
    else:
        print(f"Found {len(importers)} dependent files:")
        for imp in importers:
            print(f"  - {imp}")
            
    return 0

def enable_spike(args):
    """
    Enables Spike Mode (Safety Harness Disengaged).
    Usage: lisa spike
    """
    from .state import StateManager, LISA_MODES
    
    # Initialize State Manager
    state_manager = StateManager()
    
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
    from .state import StateManager, LISA_MODES
    
    # Initialize State Manager
    state_manager = StateManager()
    
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
    from .state import StateManager, LISA_MODES
    
    # Initialize State Manager
    state_manager = StateManager()
    
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
    print("\n[LISA] Context Analysis (The Scale)")
    print("-----------------------------------")
    
    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError:
        print("[LISA] Error: Could not determine project root.")
        return 1
        
    config = ConfigManager().load()
    limit = config.get("context_limit", 8000)
    
    print(f"Scanning workspace: {project_root}")
    token_count = scan_workspace(project_root)
    
    health = get_context_health(token_count, limit)
    
    # Determine icon
    icon = "🟢"
    if health == "AMBER":
        icon = "🟡"
    elif health == "RED":
        icon = "🔴"
        
    percentage = (token_count / limit) * 100
    
    print(f"Estimated Tokens: {token_count} / {limit}")
    print(f"Usage: {percentage:.1f}%")
    print(f"Status: [{icon}] {health}")
    
    if health == "RED":
         print("\n[!] CRITICAL: Context Limit Exceeded.")
         print("    Action Required: Run 'lisa reset' or compact files.")
    elif health == "AMBER":
         print("\n[!] WARNING: Approaching Context Limit.")
         print("    Consider compiling a summary.")
         
    return 0
