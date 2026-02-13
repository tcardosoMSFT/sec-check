"""
AgentSec CLI — command-line interface for security scanning.

This module provides the entry point for the `agentsec` command.
It uses argparse to parse commands and calls the SecurityScannerAgent
from the core package.

Usage:
    agentsec scan ./my_project
    agentsec --version
    agentsec --help
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# NOTE: We do NOT import SecurityScannerAgent at the top level.
# The agent module requires the Copilot SDK, which may not be installed.
# Instead, we import it lazily inside run_scan() so that --version and
# --help still work even when the SDK is missing.

# Configure logging for the CLI
# We use INFO level so users see important messages but not debug noise
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple format for CLI output
)
logger = logging.getLogger(__name__)


async def run_scan(folder: str) -> int:
    """
    Execute a security scan on the given folder.

    This function:
    1. Validates that the folder exists
    2. Creates and initializes the SecurityScannerAgent
    3. Runs the scan
    4. Prints results to stdout
    5. Cleans up the agent resources

    Args:
        folder: Path to the folder to scan (absolute or relative)

    Returns:
        Exit code: 0 for success, 1 for error, 2 for timeout
    """
    # Step 1: Validate the folder path
    folder_path = Path(folder).resolve()

    if not folder_path.exists():
        print(f"Error: Folder not found: {folder_path}", file=sys.stderr)
        return 1

    if not folder_path.is_dir():
        print(f"Error: Not a directory: {folder_path}", file=sys.stderr)
        return 1

    # Step 2: Import the agent (lazy import to avoid crashing on --help/--version
    # when the Copilot SDK is not installed)
    try:
        from agentsec.agent import SecurityScannerAgent
    except ImportError as import_error:
        print(
            f"Error: Could not import SecurityScannerAgent: {import_error}\n"
            "Make sure the Copilot SDK is installed:\n"
            "  pip install copilot-sdk",
            file=sys.stderr,
        )
        return 1

    # Step 3: Create the agent
    agent = SecurityScannerAgent()

    try:
        # Step 4: Initialize (connect to Copilot)
        print("Starting AgentSec security scanner...")
        print()
        await agent.initialize()

        # Step 5: Run the scan
        print(f"Scanning: {folder_path}")
        print("This may take a moment...")
        print()

        result = await agent.scan(str(folder_path))

        # Step 6: Display results based on status
        if result["status"] == "success":
            print(result["result"])
            return 0

        elif result["status"] == "timeout":
            print(f"Timeout: {result['error']}", file=sys.stderr)
            return 2

        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1

    except FileNotFoundError:
        print(
            "Error: Copilot CLI not found.\n"
            "Install it: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli\n"
            "Then run: copilot auth login",
            file=sys.stderr,
        )
        return 1

    except Exception as error:
        print(f"Unexpected error: {error}", file=sys.stderr)
        return 1

    finally:
        # Step 7: Always clean up resources
        await agent.cleanup()


def main() -> None:
    """
    Main entry point for the agentsec CLI command.

    This function:
    1. Sets up the argument parser with commands
    2. Parses the user's input
    3. Routes to the appropriate command handler
    4. Sets the process exit code

    Commands:
        scan <folder>   Scan a folder for security issues
        --version       Show the version number
        --help          Show help message
    """
    # Create the top-level parser
    parser = argparse.ArgumentParser(
        prog="agentsec",
        description="AgentSec — AI-powered security scanner for code",
        epilog=(
            "Examples:\n"
            "  agentsec scan ./my_project     Scan a project folder\n"
            "  agentsec scan .                Scan current directory\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add --version to the top-level parser
    parser.add_argument(
        "--version",
        action="version",
        version="agentsec 0.1.0",
    )

    # Create subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
    )

    # Add the 'scan' subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a folder for security vulnerabilities",
        description="Scan all files in a folder for security issues",
    )
    scan_parser.add_argument(
        "folder",
        help="Path to the folder to scan (e.g., ./src or C:\\code\\myapp)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Route to the correct command
    if args.command == "scan":
        exit_code = asyncio.run(run_scan(args.folder))
        sys.exit(exit_code)
    else:
        # No command given — show help
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
