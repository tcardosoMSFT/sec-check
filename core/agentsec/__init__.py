"""
AgentSec Core — shared agent and skills library.

This package provides the SecurityScannerAgent, configuration management,
progress tracking, and all @tool-decorated skill functions used by both
the CLI and the Desktop app.
"""

__version__ = "0.1.0"

# Import configuration (always available, no external dependencies)
from agentsec.config import AgentSecConfig

# Import progress tracking (always available, no external dependencies)
from agentsec.progress import (
    ProgressTracker,
    ProgressEvent,
    ProgressEventType,
    ProgressCallback,
    get_global_tracker,
    set_global_tracker,
)

try:
    from agentsec.agent import SecurityScannerAgent
    __all__ = [
        "SecurityScannerAgent",
        "AgentSecConfig",
        "ProgressTracker",
        "ProgressEvent",
        "ProgressEventType",
        "ProgressCallback",
        "get_global_tracker",
        "set_global_tracker",
    ]
except ImportError:
    # If the Copilot SDK is not installed, the agent class won't be available.
    # Config, progress tracking, and skills can still be used for testing.
    __all__ = [
        "AgentSecConfig",
        "ProgressTracker",
        "ProgressEvent",
        "ProgressEventType",
        "ProgressCallback",
        "get_global_tracker",
        "set_global_tracker",
    ]
