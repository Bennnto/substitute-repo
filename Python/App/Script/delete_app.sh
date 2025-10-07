#!/bin/bash

# Delete Canvas App Script
# This script removes the canvas app and related files

echo "🗑️  Canvas App Cleanup Script"
echo "================================"

# Function to check if file/directory exists and remove it
remove_if_exists() {
    if [ -e "$1" ]; then
        echo "Removing: $1"
        rm -rf "$1"
    else
        echo "Not found: $1"
    fi
}

# Function to check if file exists and remove it
remove_file_if_exists() {
    if [ -f "$1" ]; then
        echo "Removing file: $1"
        rm "$1"
    else
        echo "File not found: $1"
    fi
}

echo ""
echo "📁 Removing Canvas App Files..."

# Remove main app files
remove_file_if_exists "canvas_app.py"
remove_file_if_exists "canvas_requirements.txt"
remove_file_if_exists "start_canvas.py"
remove_file_if_exists "quick_start.py"
remove_file_if_exists "canvas_launcher.sh"
remove_file_if_exists "canvas_launcher.bat"
remove_file_if_exists "launch_scripts.md"

# Remove templates and static files
remove_if_exists "templates/canvas.html"
remove_if_exists "static/canvas.js"
remove_if_exists "static/canvas.css"

# Remove data files (optional - ask user)
echo ""
read -p "🗂️  Remove canvas data files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing canvas data files..."
    remove_if_exists "data/canvas_*.json"
    remove_if_exists "data/canvas_*.txt"
else
    echo "Keeping canvas data files"
fi

# Remove backup files
echo ""
read -p "🗂️  Remove canvas backup files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing canvas backup files..."
    remove_if_exists "backups/canvas_*"
    remove_if_exists "*.backup"
else
    echo "Keeping canvas backup files"
fi

# Remove virtual environment (optional)
echo ""
read -p "🐍 Remove canvas virtual environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing canvas virtual environment..."
    remove_if_exists "venv"
    remove_if_exists "mpvenv"
else
    echo "Keeping virtual environment"
fi

# Remove any remaining canvas-related files
echo ""
echo "🔍 Looking for any remaining canvas files..."
find . -name "*canvas*" -type f 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        echo "Found: $file"
        read -p "Remove this file? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm "$file"
            echo "Removed: $file"
        fi
    fi
done

echo ""
echo "✅ Canvas App Cleanup Complete!"
echo ""
echo "📋 Summary:"
echo "  - Removed canvas app files"
echo "  - Removed templates and static files"
echo "  - Cleaned up data files (if selected)"
echo "  - Cleaned up backup files (if selected)"
echo "  - Cleaned up virtual environment (if selected)"
echo ""
echo "💡 Tip: You can restore the canvas app by running the original setup script"
echo "" 