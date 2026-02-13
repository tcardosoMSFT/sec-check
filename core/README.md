# AgentSec Core

The core package for AgentSec, providing the `SecurityScannerAgent` class, configuration management, and all `@tool`-decorated skill functions. Both the CLI and Desktop app import from this package to perform security scanning.

## Installation

```bash
pip install -e ./core
```

## Package Structure

- `agentsec/agent.py` — `SecurityScannerAgent` class (main entry point)
- `agentsec/config.py` — `AgentSecConfig` class for configuration management
- `agentsec/progress.py` — `ProgressTracker` class for real-time scan feedback
- `agentsec/skills.py` — `@tool` skill functions (list_files, analyze_file, generate_report)
- `tests/` — Unit and integration tests

## Configuration

The `AgentSecConfig` class manages configuration for the agent:

```python
from agentsec.config import AgentSecConfig

# Load from YAML file
config = AgentSecConfig.load("./agentsec.yaml")

# Or create with custom values
config = AgentSecConfig(
    system_message="You are a security scanner...",
    initial_prompt="Scan {folder_path} for issues."
)

# Apply CLI overrides
config = config.with_overrides(
    system_message_file="./custom-system.txt"
)
```

### Configuration Options

| Setting | Description |
|---------|-------------|
| `system_message` | The AI's system prompt (who it is, what it does) |
| `system_message_file` | Path to file containing system message |
| `initial_prompt` | Prompt template for scans (use `{folder_path}` placeholder) |
| `initial_prompt_file` | Path to file containing initial prompt |

### Config File Search Paths

`AgentSecConfig.load()` searches for config files in:
1. Current directory (`agentsec.yaml`, `agentsec.yml`, `.agentsec.yaml`, `.agentsec.yml`)
2. User home directory
3. `~/.config/agentsec/`

## Agent Usage

```python
from agentsec.agent import SecurityScannerAgent
from agentsec.config import AgentSecConfig

# With default configuration
agent = SecurityScannerAgent()

# With custom configuration
config = AgentSecConfig.load("./agentsec.yaml")
agent = SecurityScannerAgent(config=config)

try:
    await agent.initialize()
    result = await agent.scan("./my-project")
    print(result["result"])
finally:
    await agent.cleanup()
```

## Progress Tracking

The core package provides a `ProgressTracker` class for real-time scan feedback:

```python
from agentsec.progress import (
    ProgressTracker,
    ProgressEvent,
    ProgressEventType,
    set_global_tracker,
)

# Create a callback to handle progress events
def on_progress(event: ProgressEvent):
    if event.type == ProgressEventType.FILE_STARTED:
        print(f"Scanning: {event.current_file}")
    elif event.type == ProgressEventType.FILE_FINISHED:
        print(f"Done: {event.files_scanned}/{event.total_files} files")
    elif event.type == ProgressEventType.SCAN_FINISHED:
        print(f"Complete: {event.issues_found} issues in {event.elapsed_seconds:.1f}s")

# Create and register the tracker
tracker = ProgressTracker(callback=on_progress, heartbeat_interval=3.0)
set_global_tracker(tracker)

# Run the scan (skills will automatically report progress)
tracker.start_scan("./my-project")
result = await agent.scan("./my-project")
tracker.finish_scan()

# Clear the tracker when done
set_global_tracker(None)
```

### Progress Events

| Event Type | Description |
|------------|-------------|
| `SCAN_STARTED` | Scan has begun |
| `FILES_DISCOVERED` | Total files to scan has been determined |
| `FILE_STARTED` | Started analyzing a specific file |
| `FILE_FINISHED` | Finished analyzing a file (includes issue count) |
| `HEARTBEAT` | Periodic update showing scan is still active |
| `SCAN_FINISHED` | Scan complete with final summary |
| `WARNING` | Non-fatal issue during scan |
| `ERROR` | Serious problem during scan |
