#!/bin/bash
set -eo pipefail

# LISA - Layered Isolated Scoped Agent
# The Context Governance Tool

VERSION="0.1.0"

show_help() {
    echo "LISA - Context Governance Tool v$VERSION"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  checkpoint   Validate external state (todo.md)"
    echo "  version      Show version information"
    echo "  help         Show this help message"
}

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[LISA] Warning: python3 is not installed or not in PATH."
    echo "[LISA] Skipping context governance checks (Fail-Open)."
    exit 0
fi

# Get the absolute path of the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Set PYTHONPATH to include the current directory so we can run scripts.lisa
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Exec Handover: Replace current process with Python interpreter
# We use -m scripts.lisa to run the package entry point (__main__.py)
exec python3 -m scripts.lisa "$@"
