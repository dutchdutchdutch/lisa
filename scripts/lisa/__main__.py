import sys
from .commands import verify_fail, verify_pass, analyze_deps, enable_spike, disable_spike, bypass_tdd, check_context
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
        sys.exit(check_context(args))
    elif command == "version":
        print("0.1.0") 
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
