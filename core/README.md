# AgentSec Core

The core package for AgentSec, providing the `SecurityScannerAgent` class and all `@tool`-decorated skill functions. Both the CLI and Desktop app import from this package to perform security scanning.

## Installation

```bash
pip install -e ./core
```

## Package Structure

- `agentsec/agent.py` — `SecurityScannerAgent` class (main entry point)
- `agentsec/skills.py` — `@tool` skill functions (list_files, analyze_file, generate_report)
- `tests/` — Unit and integration tests
