#!/bin/bash
set -eo pipefail

# LISA - Layered Isolated Scoped Agent
# The Context Governance Tool

VERSION="0.2.2"

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

# SCRIPT_DIR is src/lisa/; parent (src/) goes on PYTHONPATH
# so "python3 -m lisa" resolves src/lisa/ as the lisa package.
export PYTHONPATH="$SCRIPT_DIR/..:$PYTHONPATH"

# Exec Handover: Replace current process with Python interpreter
exec python3 -m lisa "$@"
