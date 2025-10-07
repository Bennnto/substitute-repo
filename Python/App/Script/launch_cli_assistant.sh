#!/bin/bash

# CLI Assistant Launcher Script for macOS Menu Bar
# This script launches the CLI assistant in a new terminal window

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "Error" message "Python3 is not installed or not in PATH"'
    exit 1
fi

# Launch the CLI assistant in a new terminal window
osascript <<EOF
tell application "Terminal"
    activate
    do script "cd '$SCRIPT_DIR' && python3 cli_assistant.py"
end tell
EOF 