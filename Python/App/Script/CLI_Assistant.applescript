-- CLI Assistant Launcher for macOS Menu Bar
-- This AppleScript launches the CLI assistant in a new terminal window

-- Get the path to the script directory
set scriptPath to do shell script "dirname " & quoted form of POSIX path of (path to me)

-- Change to the script directory and launch CLI assistant
set launchCommand to "cd " & quoted form of scriptPath & " && python3 cli_assistant.py"

tell application "Terminal"
	activate
	do script launchCommand
end tell 