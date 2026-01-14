#!/bin/bash
# Wrapper script for document audit agent

set -e

cd "$(dirname "$0")/.."

# Ensure Python dependencies are available
if ! python3 -c "import httpx" 2>/dev/null; then
    echo "Installing required dependencies..."
    pip install httpx pyyaml
fi

# Run the audit agent
python3 scripts/docs_audit_agent.py "$@"
