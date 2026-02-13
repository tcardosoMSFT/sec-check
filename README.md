# AgentSec

AI-powered security scanner for your code, built with the GitHub Copilot SDK.

## Overview

AgentSec is a monorepo containing three packages:
- **core/** — Shared agent and skills library (Python)
- **cli/** — Command-line interface (Python)
- **desktop/** — GUI application with FastAPI backend and Next.js frontend

## Quick Start

### Prerequisites

- Python 3.12+ (3.11 minimum)
- GitHub Copilot subscription
- GitHub Copilot CLI installed and authenticated

### 1. Activate Environment

```bash
# Simple activation (recommended)
source activate.sh

# Or manual activation
source venv/bin/activate
```

### 2. Authenticate Copilot CLI

```bash
# Check authentication status
copilot --version

# If needed, authenticate
copilot auth login
```

### 3. Run Your First Scan

```bash
# Scan the test folder
agentsec scan ./test-scan

# Scan current directory
agentsec scan .

# Scan any project
agentsec scan /path/to/your/project
```

## Setup Details

The virtual environment and packages are **already installed**! If you need to reinstall:

```bash
# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages in editable mode
pip install -e ./core
pip install -e ./cli
```

For detailed setup instructions, troubleshooting, and development workflow, see [SETUP.md](SETUP.md).

## What Gets Scanned

AgentSec currently detects:
- 🚨 **High Risk**: `eval()` and `exec()` calls (arbitrary code execution)
- ⚠️ **Medium Risk**: Hardcoded credentials and secrets
- ℹ️ **Low Risk**: Potentially dangerous imports (`subprocess`, `os`, `pickle`)

## Documentation

- **[SETUP.md](SETUP.md)** — Complete setup and testing guide
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — Project architecture and development guide
- **[spec/plan-agentSec.md](spec/plan-agentSec.md)** — Implementation roadmap and design

## Architecture

AgentSec uses the GitHub Copilot SDK to create an AI agent that:
1. Lists files in a directory (`list_files` skill)
2. Analyzes each file for security issues (`analyze_file` skill)
3. Generates a summary report (`generate_report` skill)

The agent is implemented in [core/agentsec/agent.py](core/agentsec/agent.py) and shared by both the CLI and Desktop app.

## Development

Since packages are installed in editable mode, changes to the code are immediately available:

```bash
# Edit skills
vim core/agentsec/skills.py

# Changes are live - no reinstall needed
agentsec scan ./test-scan
```

Run tests:

```bash
cd core
pytest tests/
```

## License

Coming soon.
