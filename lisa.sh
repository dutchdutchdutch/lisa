#!/bin/bash
set -euo pipefail

# LISA - Layered Isolated Scoped Agent
# The Context Governance Tool

VERSION="0.1.0"

show_help() {
    echo "LISA - Context Governance Tool v$VERSION"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  version   Show version information"
    echo "  help      Show this help message"
}

version() {
    echo "$VERSION"
}

# Main command dispatcher
COMMAND="${1:-help}"

case "$COMMAND" in
    version)
        version
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
