# Cli-To

A simple and extensible command line interface tool built with Python.

## Installation

You can install Cli-To directly from the source:

```bash
pip install -e .
```

Or run it directly with Python:

```bash
python cli_to.py
```

## Usage

After installation, you can use the `cli-to` command:

```bash
# Show help
cli-to --help

# Show version
cli-to --version

# Basic usage
cli-to

# Execute a command with verbose output
cli-to -v hello world

# Execute a command with multiple arguments
cli-to command arg1 arg2 arg3
```

### Command Line Options

- `--version`: Show the version number
- `-v, --verbose`: Enable verbose output
- `command`: The command to execute (optional)
- `args`: Additional arguments for the command

## Development

To contribute to this project:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make your changes
4. Test the CLI functionality

## Requirements

- Python 3.7 or higher
- No external dependencies (uses Python standard library only)