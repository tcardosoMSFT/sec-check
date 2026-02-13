"""
AgentSec Core — shared agent and skills library.

This package provides the SecurityScannerAgent and all @tool-decorated
skill functions used by both the CLI and the Desktop app.
"""

__version__ = "0.1.0"

try:
    from agentsec.agent import SecurityScannerAgent
    __all__ = ["SecurityScannerAgent"]
except ImportError:
    # If the Copilot SDK is not installed, the agent class won't be available.
    # Skills can still be used directly for testing and development.
    __all__ = []
