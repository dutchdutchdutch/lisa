"""Lifecycle hooks engine for LISA.

Executes configured commands at story lifecycle events with fail-open semantics.
"""
import subprocess
from .config import ConfigManager
from .logger import print_with_status


# Valid lifecycle event names
LIFECYCLE_EVENTS = [
    "story-kickoff",
    "story-in-dev",
    "story-test",
    "story-complete",
    "context-reset",
]

# Timeout for individual hook commands (seconds)
_HOOK_TIMEOUT = 30


def run_hooks(event_name, project_root):
    """Execute configured hook commands for a lifecycle event.
    
    Args:
        event_name: Name of the lifecycle event (e.g., "story-complete")
        project_root: Absolute path to the project root
        
    Returns:
        List of (command, success, output) tuples
    """
    config = ConfigManager(project_root=project_root)
    hooks_config = config.get("lifecycle_hooks")
    
    if not hooks_config:
        return []
    
    commands = hooks_config.get(event_name, [])
    if not commands:
        return []
    
    print_with_status(f"Running lifecycle hooks for: {event_name}", status_icon="🪝")
    
    results = []
    for cmd in commands:
        try:
            print_with_status(f"  Hook: {cmd}", status_icon="▶️")
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=_HOOK_TIMEOUT,
                cwd=project_root,
            )
            success = proc.returncode == 0
            output = proc.stdout or proc.stderr or ""
            if success:
                print_with_status(f"  ✅ {cmd}", status_icon="✅")
            else:
                print_with_status(f"  [WARNING] Hook returned non-zero: {cmd} (exit {proc.returncode})", status_icon="⚠️")
            results.append((cmd, success, output))
        except Exception as e:
            # NFR3: Fail-open — log warning, don't block
            print_with_status(f"  [WARNING] Hook failed: {cmd} — {e}", status_icon="⚠️")
            results.append((cmd, False, str(e)))
    
    return results


def run_story_complete(project_root):
    """Orchestrate the story-complete lifecycle event.
    
    Runs configured hooks, then performs a health check.
    If health is AMBER/RED, triggers remediation based on hooks_mode.
    
    Note: Regression tests are NOT required for documentation-only stories
    (i.e., when mode is BYPASS_TDD). The health check and polish pass still
    run, but the dev-story workflow should skip the regression suite for
    non-functional changes.
    
    Args:
        project_root: Absolute path to the project root
        
    Returns:
        0 (always succeeds — fail-open)
    """
    config = ConfigManager(project_root=project_root)
    hooks_mode = config.get("hooks_mode", "auto")
    
    print_with_status("Story Complete: Running lifecycle hooks...", status_icon="🏁")
    
    # 1. Run configured story-complete hooks
    try:
        run_hooks("story-complete", project_root)
    except Exception as e:
        print_with_status(f"[WARNING] Hook execution error: {e}", status_icon="⚠️")
    
    # 2. Health check
    health_result = None
    try:
        print_with_status("Running post-story health check...", status_icon="🩺")
        from .commands import check_context  # Lazy import to avoid circular dependency
        health_result = check_context([])
    except Exception as e:
        print_with_status(f"[WARNING] Health check failed: {e}", status_icon="⚠️")
    
    # 3. Remediation (if needed)
    if health_result is not None and health_result != 0:
        if hooks_mode == "auto":
            print_with_status("Health check flagged issues — running auto-remediation...", status_icon="🔧")
            print_with_status("  → Context Curator: Compress conversation history", status_icon="📋")
            print_with_status("  → Checkpoint: Saving state to todo.md (lisa checkpoint)", status_icon="💾")
            print_with_status("  → Session Management: Consider running 'lisa reset' if context is RED", status_icon="📦")
            # Execute checkpoint as a concrete remediation step
            try:
                subprocess.run(
                    "lisa checkpoint",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=_HOOK_TIMEOUT,
                    cwd=project_root,
                )
            except Exception:
                pass  # Fail-open
        elif hooks_mode == "interactive":
            print_with_status("Health check flagged issues — manual intervention recommended:", status_icon="⏸️")
            print_with_status("  1. Run context curator to compress history", status_icon="📋")
            print_with_status("  2. Run 'lisa checkpoint' to save state", status_icon="💾")
            print_with_status("  3. Consider 'lisa reset' if context is saturated", status_icon="📦")
    else:
        print_with_status("Health check: GREEN — all clear.", status_icon="✅")
    
    return 0
