# AgentSec CLI

**AI-powered security scanner for your code, from the command line.**

AgentSec CLI scans your project folders for security vulnerabilities using an AI agent built on the GitHub Copilot SDK. It analyzes your code and reports potential issues — all from a single terminal command.

---

## Prerequisites

Before using AgentSec CLI, make sure you have:

1. **Python 3.10 or newer** — Check with `python --version`
2. **Copilot CLI installed** — Install from [GitHub Copilot CLI docs](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
3. **Copilot CLI authenticated** — Run `copilot auth login` and follow the prompts

---

## Installation

### For Users (from PyPI)

```bash
pip install agentsec
```

### For Developers (editable install from source)

```bash
# Clone the repo and install in editable mode
git clone <repo-url>
cd AgentSec
pip install -e ./core      # Install shared agent library first
pip install -e ./cli        # Install CLI package
```

---

## Usage

### Scan a project folder

```bash
agentsec scan ./my_project
```

This scans all files in `./my_project` and prints a security report to your terminal.

### Scan the current directory

```bash
agentsec scan .
```

### Show the version number

```bash
agentsec --version
```

### Show help

```bash
agentsec --help
```

---

## Configuration

AgentSec uses environment variables for configuration. A `.env.example` file is provided at the workspace root with all available settings.

To configure:

1. Copy the example file: `cp .env.example .env`
2. Edit `.env` with your preferred settings
3. AgentSec will automatically load values from `.env` when running

See [`.env.example`](../.env.example) in the project root for all available options.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | **Success** — scan completed without errors |
| `1`  | **Error** — something went wrong (bad path, import failure, agent error) |
| `2`  | **Timeout** — the scan took too long to complete |

You can use these exit codes in scripts and CI pipelines:

```bash
agentsec scan ./src
if [ $? -ne 0 ]; then
    echo "Security scan failed!"
fi
```

---

## Troubleshooting

### "Copilot CLI not found"

The Copilot CLI is not installed or not on your PATH.

**Fix:**
1. Install Copilot CLI: [installation guide](https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli)
2. Authenticate: `copilot auth login`
3. Verify it works: `copilot --version`

### "Folder not found"

The folder path you provided does not exist.

**Fix:**
- Double-check the path for typos
- Use an absolute path if relative paths are confusing: `agentsec scan C:\code\myapp`
- Make sure the folder exists: `ls ./my_project` (or `dir` on Windows)

### "Timeout"

The scan took too long. This usually happens with very large projects.

**Fix:**
- Try scanning a smaller subfolder first: `agentsec scan ./src/api`
- Close other programs to free up resources
- Check your network connection (the agent calls the Copilot API)

### "Agent not initialized" or "Could not import SecurityScannerAgent"

The agent could not start, usually due to authentication issues.

**Fix:**
1. Make sure Copilot CLI is authenticated: `copilot auth login`
2. Verify the core package is installed: `pip install -e ./core`
3. Check that your Copilot subscription is active

---

## Examples

```bash
# Scan a Python project
agentsec scan ./my-flask-app

# Scan a Node.js project
agentsec scan ./express-server

# Scan the current directory
agentsec scan .

# Use in a CI script
agentsec scan ./src || exit 1
```

---

## Project Links

- [Main AgentSec README](../README.md) — overview of the full project
- [Core package](../core/) — shared agent and skills library
- [Implementation plan](../spec/implementation-plan.md) — project roadmap

---

## License

See the [main project README](../README.md) for license information.
