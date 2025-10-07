# CLI Assistant Setup for Ice.app Menu Bar

## Prerequisites
1. Install Ice.app from the Mac App Store
2. Make sure all dependencies are installed: `pip3 install cryptography requests tqdm psutil`

## Setup Steps

### Method 1: Using Ice.app Interface

1. **Open Ice.app**
2. **Click the "+" button** to add a new script
3. **Configure the script:**
   - **Name:** CLI Assistant
   - **Script Path:** `/Users/ben/PythonApp/Cli-App/ice_cli_assistant.sh`
   - **Icon:** Choose "Terminal" or any icon you prefer
   - **Menu Title:** CLI Assistant

4. **Save the configuration**

### Method 2: Using Configuration File

1. **Copy the configuration:**
   ```bash
   cp ice_config.json ~/Library/Application\ Support/Ice/scripts/cli_assistant.json
   ```

2. **Restart Ice.app**

### Method 3: Manual Setup

1. **In Ice.app:**
   - Click "+" to add new script
   - Set **Name:** CLI Assistant
   - Set **Script:** `/Users/ben/PythonApp/Cli-App/ice_cli_assistant.sh`
   - Set **Icon:** terminal
   - Enable **Show in Menu Bar**

2. **Test the script:**
   ```bash
   ./ice_cli_assistant.sh
   ```

## Usage

Once set up, you'll see "CLI Assistant" in your menu bar. Click it to:

- **Launch CLI Assistant** - Opens a new Terminal window with your CLI assistant
- **Open Script Directory** - Opens the folder containing your scripts

## Troubleshooting

### If the script doesn't work:
1. **Check permissions:**
   ```bash
   chmod +x ice_cli_assistant.sh
   ```

2. **Test manually:**
   ```bash
   ./ice_cli_assistant.sh
   ```

3. **Check Python path:**
   ```bash
   which python3
   ```

### If Ice.app doesn't show the script:
1. **Restart Ice.app**
2. **Check Ice.app preferences**
3. **Verify the script path is correct**

## Customization

You can customize the menu by editing the `ice_config.json` file:

```json
{
  "name": "CLI Assistant",
  "script": "/Users/ben/PythonApp/Cli-App/ice_cli_assistant.sh",
  "icon": "terminal",
  "menu": {
    "title": "CLI Assistant",
    "items": [
      {
        "title": "Launch CLI Assistant",
        "script": "/Users/ben/PythonApp/Cli-App/ice_cli_assistant.sh"
      },
      {
        "title": "Open Script Directory",
        "script": "open /Users/ben/PythonApp/Cli-App"
      }
    ]
  }
}
```

## Quick Test

Test if everything works:
```bash
./ice_cli_assistant.sh
```

This should open a new Terminal window with your CLI assistant running. 