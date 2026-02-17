import sys
from .commands import verify_fail, verify_pass, analyze_deps, enable_spike, disable_spike, bypass_tdd, check_context, reset_context, checkpoint, init_session, context_status, context_size, context_health, run_hooks_cmd
from .config import ConfigManager

def main():
    """Main entry point for LISA Python CLI."""
    if len(sys.argv) < 2:
        print("Usage: lisa [command] [args...]")
        sys.exit(1)
        
    command = sys.argv[1]
    args = sys.argv[2:]
    
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
        from .commands import turns
        sys.exit(turns(args))
    elif command == "polish":
        from .commands import polish
        sys.exit(polish(args))
    elif command == "refactor":
        from .commands import refactor
        sys.exit(refactor(args))
    elif command == "hooks":
        sys.exit(run_hooks_cmd(args))
    elif command == "version":
        print("0.1.0") 
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
