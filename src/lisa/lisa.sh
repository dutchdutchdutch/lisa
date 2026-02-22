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

# Logic for finding LISA:
# 1. If we are in a 'src/' dir (dev mode), add parent to PYTHONPATH
# 2. If we are in '.lisa/' (resident mode), try to find where we were installed from
# 3. Default to just 'python3 -m lisa' (assuming pip install)

if [ -d "$SCRIPT_DIR/../lisa" ]; then
    # Likely dev mode (src/lisa/lisa.sh)
    export PYTHONPATH="$SCRIPT_DIR/..:$PYTHONPATH"
elif [ -f "$SCRIPT_DIR/../setup.py" ] || [ -f "$SCRIPT_DIR/../pyproject.toml" ]; then
    # Likely at project root (if someone copied it there)
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
fi

# Exec Handover: Replace current process with Python interpreter
exec python3 -m lisa "$@"
