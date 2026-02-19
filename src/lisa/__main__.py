import sys
from .commands import (
    verify_fail, verify_pass, analyze_deps, enable_spike, disable_spike,
    bypass_tdd, check_context, reset_context, checkpoint, init_session,
    context_status, context_size, context_health, run_hooks_cmd,
    turns, polish, refactor, classify, scope_cmd, verify_layer, layer_status_cmd,
    ui_handoff, workspace_size,
)
from .config import ConfigManager
from .state import StateManager
from .utils import find_project_root

def main():
    """Main entry point for LISA Python CLI."""
    if len(sys.argv) < 2:
        print("Usage: lisa [command] [args...]")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Commands that work without a project root (smoke test)
    if command == "version":
        print("0.3.0")
        sys.exit(0)

    # Auto-increment turn counter once per response cycle (Story 5.9)
    try:
        project_root = find_project_root()
        state_manager = StateManager(project_root=project_root)
        state_manager.auto_increment_turn()
    except Exception:
        pass  # Fail-open: don't block commands if auto-increment fails

    # Dispatch
    if command == "verify-fail":
        sys.exit(verify_fail(args))
    elif command == "verify-pass":
        sys.exit(verify_pass(args))
    elif command == "analyze":
        sys.exit(analyze_deps(args))
    elif command == "spike":
        sys.exit(enable_spike(args))
    elif command == "normal":
        sys.exit(disable_spike(args))
    elif command == "bypass-tdd":
        sys.exit(bypass_tdd(args))
    elif command == "context":
        if args and args[0] == "status":
            sys.exit(context_status(args[1:]))
        elif args and args[0] == "size":
            sys.exit(context_size(args[1:]))
        elif args and args[0] == "health":
            sys.exit(context_health(args[1:]))
        else:
            sys.exit(check_context(args))
    elif command == "reset":
        sys.exit(reset_context(args))
    elif command == "checkpoint":
        sys.exit(checkpoint(args))
    elif command == "init":
        sys.exit(init_session(args))
    elif command == "turns":
        sys.exit(turns(args))
    elif command == "polish":
        sys.exit(polish(args))
    elif command == "refactor":
        sys.exit(refactor(args))
    elif command == "hooks":
        sys.exit(run_hooks_cmd(args))
    elif command == "classify":
        sys.exit(classify(args))
    elif command == "scope":
        sys.exit(scope_cmd(args))
    elif command == "verify-layer":
        sys.exit(verify_layer(args))
    elif command == "layer-status":
        sys.exit(layer_status_cmd(args))
    elif command == "ui-handoff":
        sys.exit(ui_handoff(args))
    elif command == "workspace":
        sys.exit(workspace_size(args))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
