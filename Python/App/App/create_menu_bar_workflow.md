# CLI Assistant Menu Bar Setup

## Option 1: Using Automator (Easiest)

1. **Open Automator**
2. **Create New Document** → Choose "Quick Action"
3. **Configure the workflow:**
   - Workflow receives: **no input**
   - In: **any application**
4. **Add Actions:**
   - Search for "Run Shell Script"
   - Add it to the workflow
   - Set Shell to: **/bin/bash**
   - Set Pass input to: **as arguments**
   - Add this script:
   ```bash
   cd "/Users/ben/PythonApp/Cli-App"
   python3 cli_assistant.py
   ```
5. **Save** as "CLI Assistant"
6. **Add to Menu Bar:**
   - Go to System Preferences → Keyboard → Shortcuts
   - Select "Services" from the left sidebar
   - Find "CLI Assistant" in the list
   - Check the box to enable it

## Option 2: Using the Shell Script

1. **Test the script:**
   ```bash
   ./launch_cli_assistant.sh
   ```

2. **Add to Dock:**
   - Drag the `launch_cli_assistant.sh` file to your Dock
   - Right-click the dock icon → Options → Keep in Dock

## Option 3: Using AppleScript

1. **Open Script Editor**
2. **Create New Document**
3. **Paste the AppleScript code** from `CLI_Assistant.applescript`
4. **Save** as "CLI Assistant" (Application)
5. **Drag to Dock** or **Applications folder**

## Option 4: Using a Third-Party Menu Bar App

### Using Bartender (Paid)
1. Install Bartender from the Mac App Store
2. Add the shell script to Bartender
3. It will appear in your menu bar

### Using SwiftBar (Free)
1. Install SwiftBar: `brew install swiftbar`
2. Create a plugin file:
   ```bash
   # Create ~/.config/swiftbar/plugins/cli-assistant.sh
   #!/bin/bash
   echo "CLI"
   echo "---"
   echo "Launch CLI Assistant | bash=/Users/ben/PythonApp/Cli-App/launch_cli_assistant.sh"
   ```
3. Make it executable: `chmod +x ~/.config/swiftbar/plugins/cli-assistant.sh`

## Quick Test

Run this command to test if everything works:
```bash
./launch_cli_assistant.sh
```

This should open a new Terminal window with your CLI assistant running. 