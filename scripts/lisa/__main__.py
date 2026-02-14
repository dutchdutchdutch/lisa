import sys
from .commands import verify_fail, verify_pass
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
    elif command == "version":
        print("0.1.0") 
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
