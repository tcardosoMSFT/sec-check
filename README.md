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

# Use a custom configuration file
agentsec scan ./src --config ./agentsec.yaml

# Override the system message
agentsec scan ./src --system-message-file ./custom-prompt.txt

# Run scanners in parallel for faster results
agentsec scan ./test-scan --parallel

# Parallel mode with up to 5 concurrent scanners
agentsec scan ./test-scan --parallel --max-concurrent 5
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

AgentSec uses **Copilot CLI built-in tools** (`bash`, `skill`, `view`) to invoke real security scanners and analyze your code. The agent follows a structured workflow:

1. **File Discovery** — Uses `bash` with `find` to discover all files in the target folder
2. **Security Scanning** — Invokes Copilot CLI agentic skills and/or runs scanner CLIs directly:
   - **bandit** for Python AST security analysis
   - **graudit** for multi-language pattern-based auditing
   - **guarddog** for supply chain / malicious package detection
   - **shellcheck** for shell script analysis
   - **trivy** for container & filesystem scanning
   - **eslint** for JavaScript/TypeScript security
   - And more (checkov, dependency-check, template-analyzer)
3. **Manual Inspection** — Uses `view` to read suspicious files for deeper LLM analysis
4. **Report Generation** — Compiles all findings into a structured Markdown report with severity levels, line numbers, code snippets, and remediation advice

### Parallel Scanning Mode

By default, AgentSec runs all scanners sequentially in a single LLM session. With `--parallel`, it uses a **sub-agent orchestration** pattern that runs multiple scanners concurrently for faster results:

```bash
# Run available scanners in parallel (default: 3 concurrent)
agentsec scan ./my_project --parallel

# Allow up to 5 scanners at once
agentsec scan ./my_project --parallel --max-concurrent 5
```

**How parallel mode works** (3-phase workflow):

1. **Discovery** — Walks the target folder, classifies files by type, determines which scanners are relevant and available, builds a scan plan
2. **Parallel Scan** — Spawns one sub-agent session per relevant scanner. Each session focuses on exactly one scanner tool. Sessions run concurrently via `asyncio.gather` with a semaphore to cap parallelism
3. **Synthesis** — Feeds all sub-agent findings into a synthesis session that deduplicates, normalizes severity, and compiles a single consolidated Markdown report

Example parallel progress output:
```
📋 Scan plan: running bandit, graudit, trivy (skipped: eslint, shellcheck — no relevant files)

🔍 Sub-agent started: bandit
🔍 Sub-agent started: graudit
🔍 Sub-agent started: trivy
⚠️  Sub-agent finished: bandit — 3 findings (12s)
✅ Sub-agent finished: graudit — 0 findings (8s)
⚠️  Sub-agent finished: trivy — 1 findings (15s)

📝 Synthesising findings from 3 scanners...
📊 Synthesis complete
```

### Reliability Features

- **Activity-based stall detection**: The shared `session_runner.py` monitors SDK events continuously; nudges are sent after 120s of inactivity; after 3 unresponsive nudges the session is aborted
- **Transient error retry**: Rate limits (429), 5xx, and other transient session errors are automatically retried with exponential backoff (5s, 15s, 45s) via `run_session_with_retries()`. Each retry uses a fresh session created by a session factory.
- **Configurable timeout**: Default 1800s safety ceiling; activity-based detection handles the normal case; partial results returned on timeout
- **Safety guardrails**: System message (using `mode: "append"` to preserve SDK defaults) prevents execution of scanned code, blocks dangerous commands, and defends against prompt injection
- **Dynamic system message**: Available scanner skills are discovered at runtime and injected into the system message — no hardcoded scanner lists that can become stale
- **Per-sub-agent isolation** (parallel mode): Each sub-agent runs in its own session via a session factory; failures in one scanner don't affect others
- **Connectivity check**: `client.ping()` verifies Copilot CLI server health before scanning
- **Stale session cleanup**: On initialization, orphaned `agentsec-*` sessions from previous runs are automatically deleted
- **Proper resource cleanup**: Session factories with `finally`-block cleanup ensure no session leaks; `force_stop()` fallback if `client.stop()` hangs; `sys.exit()` used instead of `os._exit()` for clean shutdown
- **Context-scoped progress tracking**: Uses `contextvars.ContextVar` for safe concurrent usage in multi-scan scenarios
- **Consolidated scanner registry**: `SCANNER_REGISTRY` in `skill_discovery.py` is the single source of truth — adding a new scanner requires editing one dict entry

## Progress Tracking

AgentSec provides real-time progress feedback during scans:

```
⠋ Starting security scan of ./my_project

  📁 Found 15 files to scan

  ⠹ [██████████░░░░░░░░░░] 50% Scanning (8/15): app.py
  ⚠️  Finished app.py: 2 issues found

✅ Scan complete: 15 files scanned, 5 issues found (23s)
```

Features:
- Visual progress bar with percentage
- Current file being scanned
- Files scanned count / total files
- Elapsed time tracking
- Issues found counter
- Periodic heartbeat to show work is ongoing

## Configuration

AgentSec can be configured via:

1. **YAML config file** (`agentsec.yaml`) — Set default system message and initial prompt
2. **CLI arguments** — Override config file settings per-run
3. **External prompt files** — Store long prompts in separate files

See [agentsec.example.yaml](agentsec.example.yaml) for a full example with comments.

**CLI Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--config FILE` | `-c` | Path to YAML config file |
| `--system-message TEXT` | `-s` | Override system message |
| `--system-message-file FILE` | `-sf` | Load system message from file |
| `--prompt TEXT` | `-p` | Override initial prompt template |
| `--prompt-file FILE` | `-pf` | Load initial prompt from file |
| `--parallel` | | Run scanners concurrently as sub-agents |
| `--max-concurrent N` | | Max parallel scanners (default 3, requires `--parallel`) |
| `--verbose` | `-v` | Enable debug logging |
| `--timeout SECONDS` | | Safety ceiling timeout (default 1800) |
| `--model MODEL` | `-m` | Override LLM model (default gpt-5) |

## Documentation

- **[SETUP.md](SETUP.md)** — Complete setup and testing guide
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — Project architecture and development guide
- **[spec/plan-agentSec.md](spec/plan-agentSec.md)** — Implementation roadmap and design
- **[agentsec.example.yaml](agentsec.example.yaml)** — Example configuration file

## Architecture

AgentSec uses the GitHub Copilot SDK to create an AI agent that leverages **Copilot CLI built-in tools** for security scanning:

1. **`bash`** — Runs file discovery commands (`find`, `ls`) and invokes security scanner CLIs directly (bandit, graudit, etc.)
2. **`skill`** — Invokes pre-configured Copilot CLI agentic skills for structured scanning (bandit-security-scan, graudit-security-scan, etc.)
3. **`view`** — Reads file contents for manual LLM code inspection

The agent also has fallback `@tool` skills (`list_files`, `analyze_file`, `generate_report`) defined in `core/agentsec/skills.py`, but these are **legacy MVP code** that are not registered with any SDK session. Primary scanning uses the Copilot CLI built-in tools.

A **directive system message** (using `mode: "append"` to preserve SDK guardrails) guides the LLM through a structured scanning workflow with safety guardrails. **Activity-based stall detection** in the shared `session_runner.py` module monitors SDK events and sends context-aware nudge messages if the LLM becomes inactive.

The agent is implemented in [core/agentsec/agent.py](core/agentsec/agent.py) and shared by both the CLI and Desktop app.

### Parallel Sub-Agent Architecture

When `--parallel` is used, the `ParallelScanOrchestrator` (in [core/agentsec/orchestrator.py](core/agentsec/orchestrator.py)) manages the workflow:

```
                ┌──────────────────┐
                │  Discovery Phase │   Pure Python — classify files,
                │  (no LLM calls)  │   pick relevant scanners
                └────────┬─────────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
       ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
       │ bandit  │ │ graudit │ │  trivy  │   Concurrent SDK sessions
       │ session │ │ session │ │ session │   (capped by semaphore)
       └────┬────┘ └────┬────┘ └────┬────┘
            │            │            │
            └────────────┼────────────┘
                         │
                ┌────────▼─────────┐
                │ Synthesis Phase  │   Single SDK session —
                │ (one LLM call)   │   dedupe & compile report
                └──────────────────┘
```

Each sub-agent session is isolated: a failure or timeout in one scanner does not affect others. The semaphore (`--max-concurrent`) prevents overloading the Copilot API.

## External Security Tools (Skill Discovery)

AgentSec dynamically discovers Copilot CLI agentic skills at runtime instead of maintaining a hardcoded tool list. It scans the same directories the Copilot CLI uses:

| Location | Scope | Path |
|----------|-------|------|
| **User-level** | All projects | `~/.copilot/skills/` |
| **Project-level** | Current project only | `<project>/.copilot/skills/` |

Each skill directory contains a `SKILL.md` file with YAML frontmatter describing the skill's name and purpose. AgentSec maps each skill to its underlying CLI tool and verifies availability on the system.

**Currently discovered skills include:**

| Tool | Description | Status |
|------|-------------|--------|
| bandit | Python AST security analysis | ✅ |
| checkov | IaC misconfiguration scanning | ✅ |
| dependency-check | CVE detection in dependencies | ✅ |
| eslint | JavaScript/TypeScript security | ✅ |
| graudit | Multi-language pattern matching | ✅ |
| guarddog | Malicious package detection | ✅ |
| shellcheck | Shell script security analysis | ✅ |
| trivy | Container & filesystem scanning | ✅ |
| template-analyzer | ARM/Bicep template scanning | ⬜ |

> **Note**: The list above reflects the current system. Your available tools may differ. The CLI displays the actual discovery results at scan time.

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
