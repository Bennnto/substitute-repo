#!/bin/bash

# Generic Mac App Deletion Script
# This script can remove any app and its related files from macOS

echo "🗑️  Mac App Deletion Script"
echo "============================="

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

# Function to check if app is running and offer to quit it
check_and_quit_app() {
    local app_name="$1"
    if pgrep -f "$app_name" > /dev/null; then
        echo "⚠️  $app_name is currently running"
        read -p "Quit $app_name before deletion? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo "Skipping app quit"
        else
            echo "Quitting $app_name..."
            pkill -f "$app_name"
            sleep 2
        fi
    fi
}

# Function to list available apps
list_available_apps() {
    echo ""
    echo "🔍 Scanning for available apps..."
    echo ""
    
    local apps=()
    local app_types=()
    local counter=1
    
    # Scan GUI apps in Applications folders
    echo "📱 GUI Applications:"
    for app in /Applications/*.app ~/Applications/*.app; do
        if [ -d "$app" ]; then
            app_name=$(basename "$app" .app)
            echo "  $counter) $app_name (GUI App)"
            apps+=("$app_name")
            app_types+=("GUI")
            ((counter++))
        fi
    done
    
    # Scan command line tools in current directory
    echo ""
    echo "💻 Command Line Tools (current directory):"
    for file in *.py *.sh *.app *.command; do
        if [ -f "$file" ] && [ "$file" != "delete_any_app.sh" ] && [ "$file" != "delete_app.sh" ]; then
            app_name=$(basename "$file" | sed 's/\.[^.]*$//')
            echo "  $counter) $app_name (CLI Tool)"
            apps+=("$app_name")
            app_types+=("CLI")
            ((counter++))
        fi
    done
    
    # Scan Python packages
    echo ""
    echo "📦 Python Packages:"
    if command -v pip > /dev/null; then
        pip list --format=freeze | cut -d'=' -f1 | while read package; do
            if [ -n "$package" ]; then
                echo "  $counter) $package (Python Package)"
                apps+=("$package")
                app_types+=("Python")
                ((counter++))
            fi
        done
    fi
    
    # Scan Homebrew packages
    echo ""
    echo "🍺 Homebrew Packages:"
    if command -v brew > /dev/null; then
        brew list | while read package; do
            if [ -n "$package" ]; then
                echo "  $counter) $package (Homebrew Package)"
                apps+=("$package")
                app_types+=("Homebrew")
                ((counter++))
            fi
        done
    fi
    
    echo ""
    echo "0) Enter custom app name"
    echo ""
    
    # Store apps in a temporary file for selection
    printf "%s\n" "${apps[@]}" > /tmp/available_apps.txt
    printf "%s\n" "${app_types[@]}" > /tmp/app_types.txt
    
    return $((counter - 1))
}

# Function to get app selection from user
get_app_selection() {
    local max_apps=$1
    
    while true; do
        read -p "Select app number (0-$max_apps): " selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 0 ] && [ "$selection" -le "$max_apps" ]; then
            if [ "$selection" -eq 0 ]; then
                # Custom app name
                read -p "Enter the name of the app to delete: " app_name
                app_name=$(echo "$app_name" | tr '[:upper:]' '[:lower:]')
                if [ -z "$app_name" ]; then
                    echo "❌ No app name provided. Please try again."
                    continue
                fi
                app_type="Custom"
            else
                # Selected from list
                app_name=$(sed -n "${selection}p" /tmp/available_apps.txt)
                app_type=$(sed -n "${selection}p" /tmp/app_types.txt)
            fi
            break
        else
            echo "❌ Invalid selection. Please enter a number between 0 and $max_apps."
        fi
    done
}

# Main script logic
echo ""
echo "Choose an option:"
echo "1) List and select from available apps"
echo "2) Enter app name manually"
echo ""
read -p "Enter your choice (1-2): " choice

case $choice in
    1)
        list_available_apps
        max_apps=$?
        get_app_selection $max_apps
        ;;
    2)
        read -p "Enter the name of the app to delete: " app_name
        app_name=$(echo "$app_name" | tr '[:upper:]' '[:lower:]')
        app_type="Manual"
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

if [ -z "$app_name" ]; then
    echo "❌ No app name provided. Exiting."
    exit 1
fi

echo ""
echo "🎯 Selected: $app_name ($app_type)"
echo "🔍 Searching for $app_name..."

# Check if it's a GUI app in Applications folder
app_paths=()
if [ -d "/Applications/$app_name.app" ]; then
    app_paths+=("/Applications/$app_name.app")
fi
if [ -d "$HOME/Applications/$app_name.app" ]; then
    app_paths+=("$HOME/Applications/$app_name.app")
fi

# Check if it's a command line tool or script in current directory
if [ -f "$app_name.py" ] || [ -f "$app_name.sh" ] || [ -f "$app_name" ]; then
    app_paths+=(".")
fi

# Check if it's a Python package
if pip list | grep -i "$app_name" > /dev/null; then
    echo "📦 Found Python package: $app_name"
    read -p "Remove Python package? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing Python package..."
        pip uninstall -y "$app_name"
    fi
fi

# Check if it's a Homebrew package
if command -v brew > /dev/null && brew list | grep -i "$app_name" > /dev/null; then
    echo "🍺 Found Homebrew package: $app_name"
    read -p "Remove Homebrew package? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing Homebrew package..."
        brew uninstall "$app_name"
    fi
fi

# Remove GUI apps
for app_path in "${app_paths[@]}"; do
    if [ "$app_path" = "/Applications/$app_name.app" ] || [ "$app_path" = "$HOME/Applications/$app_name.app" ]; then
        echo "📱 Found GUI app: $app_path"
        check_and_quit_app "$app_name"
        
        read -p "Remove GUI app? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Removing GUI app..."
            remove_if_exists "$app_path"
        fi
    fi
done

# Remove command line files in current directory
if [ "$app_paths" = "." ]; then
    echo "💻 Found command line files in current directory"
    
    # Remove main app files
    remove_file_if_exists "$app_name.py"
    remove_file_if_exists "$app_name.sh"
    remove_file_if_exists "$app_name"
    remove_file_if_exists "${app_name}_app.py"
    remove_file_if_exists "${app_name}_requirements.txt"
    remove_file_if_exists "start_${app_name}.py"
    remove_file_if_exists "quick_start.py"
    remove_file_if_exists "${app_name}_launcher.sh"
    remove_file_if_exists "${app_name}_launcher.bat"
    remove_file_if_exists "launch_scripts.md"
    
    # Remove templates and static files
    remove_if_exists "templates/${app_name}.html"
    remove_if_exists "static/${app_name}.js"
    remove_if_exists "static/${app_name}.css"
fi

# Remove data files (optional - ask user)
echo ""
read -p "🗂️  Remove $app_name data files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing $app_name data files..."
    remove_if_exists "data/${app_name}_*.json"
    remove_if_exists "data/${app_name}_*.txt"
    remove_if_exists "data/${app_name}_*.db"
    remove_if_exists "data/${app_name}_*.sqlite"
fi

# Remove backup files
echo ""
read -p "🗂️  Remove $app_name backup files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing $app_name backup files..."
    remove_if_exists "backups/${app_name}_*"
    remove_if_exists "*.backup"
fi

# Remove virtual environment (optional)
echo ""
read -p "🐍 Remove virtual environment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing virtual environment..."
    remove_if_exists "venv"
    remove_if_exists "mpvenv"
    remove_if_exists ".venv"
    remove_if_exists "env"
fi

# Remove configuration files
echo ""
read -p "⚙️  Remove $app_name configuration files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing $app_name configuration files..."
    remove_file_if_exists "${app_name}_config.json"
    remove_file_if_exists "${app_name}_config.yaml"
    remove_file_if_exists "${app_name}_config.yml"
    remove_file_if_exists ".${app_name}rc"
    remove_file_if_exists ".${app_name}_config"
fi

# Remove any remaining app-related files
echo ""
echo "🔍 Looking for any remaining $app_name files..."
find . -name "*${app_name}*" -type f 2>/dev/null | while read file; do
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

# Check for app in LaunchAgents and LaunchDaemons
echo ""
echo "🔍 Checking for launch agents and daemons..."
launch_agents=($(find ~/Library/LaunchAgents -name "*${app_name}*" 2>/dev/null))
launch_daemons=($(find /Library/LaunchDaemons -name "*${app_name}*" 2>/dev/null))

if [ ${#launch_agents[@]} -gt 0 ] || [ ${#launch_daemons[@]} -gt 0 ]; then
    echo "Found launch items:"
    for item in "${launch_agents[@]}" "${launch_daemons[@]}"; do
        echo "  $item"
    done
    
    read -p "Remove launch items? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for item in "${launch_agents[@]}" "${launch_daemons[@]}"; do
            if [ -f "$item" ]; then
                echo "Removing: $item"
                rm "$item"
            fi
        done
    fi
fi

# Check for app preferences
echo ""
echo "🔍 Checking for app preferences..."
pref_files=($(find ~/Library/Preferences -name "*${app_name}*" 2>/dev/null))
if [ ${#pref_files[@]} -gt 0 ]; then
    echo "Found preference files:"
    for pref in "${pref_files[@]}"; do
        echo "  $pref"
    done
    
    read -p "Remove preference files? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for pref in "${pref_files[@]}"; do
            if [ -f "$pref" ]; then
                echo "Removing: $pref"
                rm "$pref"
            fi
        done
    fi
fi

# Clean up temporary files
rm -f /tmp/available_apps.txt /tmp/app_types.txt

echo ""
echo "✅ $app_name Deletion Complete!"
echo ""
echo "📋 Summary:"
echo "  - Removed GUI app (if found)"
echo "  - Removed command line files (if found)"
echo "  - Removed Python/Homebrew packages (if selected)"
echo "  - Cleaned up data files (if selected)"
echo "  - Cleaned up backup files (if selected)"
echo "  - Cleaned up virtual environment (if selected)"
echo "  - Cleaned up configuration files (if selected)"
echo "  - Cleaned up launch items (if selected)"
echo "  - Cleaned up preferences (if selected)"
echo ""
echo "💡 Tip: Some apps may require a system restart to complete cleanup"
echo ""
