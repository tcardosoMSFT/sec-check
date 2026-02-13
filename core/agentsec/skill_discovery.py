"""
Dynamic discovery of Copilot CLI agentic skills.

The Copilot CLI searches for agentic skills in two locations:
  1. User-level:    ~/.copilot/skills/
  2. Project-level: .copilot/skills/   (relative to the workspace root)

Each skill is a directory containing a SKILL.md file with YAML frontmatter
that describes the skill (name, description) followed by documentation.
The skills typically wrap underlying CLI tools (bandit, trivy, etc.).

This module provides functions to:
  - Discover all skills from both locations
  - Parse the SKILL.md frontmatter to get skill metadata
  - Map each skill to its underlying CLI tool
  - Check whether the underlying tool is installed on the system

Usage:
    >>> from agentsec.skill_discovery import discover_all_skills
    >>> skills = discover_all_skills("/path/to/project")
    >>> for skill in skills:
    ...     status = "✅" if skill["tool_available"] else "⬜"
    ...     print(f"{status} {skill['name']} ({skill['tool_name']})")
"""

import logging
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional

# Set up logging for this module
logger = logging.getLogger(__name__)


# Known mappings from skill directory names to their underlying CLI tool.
# The key is the skill folder name; the value is the binary name to look for
# in PATH via shutil.which(). This list covers common naming patterns.
# If a skill is NOT in this map we try to derive the tool name automatically
# from the first segment of the directory name (e.g. "bandit-security-scan"
# becomes "bandit").
SKILL_TO_TOOL_MAP = {
    "bandit-security-scan": "bandit",
    "checkov-security-scan": "checkov",
    "dependency-check-security-scan": "dependency-check",
    "eslint-security-scan": "eslint",
    "graudit-security-scan": "graudit",
    "guarddog-security-scan": "guarddog",
    "shellcheck-security-scan": "shellcheck",
    "template-analyzer-security-scan": "template-analyzer",
    "trivy-security-scan": "trivy",
}


def _get_user_skills_dir() -> Path:
    """
    Return the user-level Copilot skills directory.

    The Copilot CLI looks for user-level agentic skills in:
        ~/.copilot/skills/

    Returns:
        Path to the user-level skills directory (may not exist).
    """
    return Path.home() / ".copilot" / "skills"


def _get_project_skills_dir(project_root: str) -> Path:
    """
    Return the project-level Copilot skills directory.

    The Copilot CLI looks for project-level agentic skills in:
        <project_root>/.copilot/skills/

    Args:
        project_root: Absolute path to the project (workspace) root.

    Returns:
        Path to the project-level skills directory (may not exist).
    """
    return Path(project_root) / ".copilot" / "skills"


def _parse_skill_frontmatter(skill_md_path: Path) -> dict:
    """
    Parse the YAML frontmatter from a SKILL.md file.

    SKILL.md files use a YAML frontmatter block delimited by '---' lines
    at the top of the file. Typical fields are 'name' and 'description'.

    We parse the frontmatter manually (line-by-line) instead of requiring
    PyYAML, so this function works even if PyYAML is not installed.

    Args:
        skill_md_path: Full path to the SKILL.md file.

    Returns:
        A dictionary with parsed frontmatter fields. Common keys:
        - "name": Skill name (e.g. "bandit-security-scan")
        - "description": One-line description of the skill
        Returns empty dict if frontmatter could not be parsed.

    Example:
        >>> meta = _parse_skill_frontmatter(Path("~/.copilot/skills/bandit-security-scan/SKILL.md"))
        >>> print(meta["name"])
        'bandit-security-scan'
    """
    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()
    except (FileNotFoundError, PermissionError, OSError) as error:
        logger.debug(f"Could not read {skill_md_path}: {error}")
        return {}

    # Find the frontmatter block (between first and second '---')
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter_lines = []
    found_end = False

    for line in lines[1:]:
        if line.strip() == "---":
            found_end = True
            break
        frontmatter_lines.append(line)

    if not found_end:
        return {}

    # Parse simple key: value pairs from the frontmatter
    # We handle multi-line values by treating leading whitespace as continuation
    metadata = {}
    current_key = None
    current_value_parts = []

    for line in frontmatter_lines:
        # Check if this is a new key: value pair
        key_value_match = re.match(r'^(\w[\w_-]*)\s*:\s*(.*)', line)

        if key_value_match:
            # Save any previous key
            if current_key is not None:
                metadata[current_key] = " ".join(current_value_parts).strip()

            current_key = key_value_match.group(1)
            value = key_value_match.group(2).strip()
            current_value_parts = [value] if value else []

        elif current_key is not None and line.strip():
            # Continuation of a multi-line value
            current_value_parts.append(line.strip())

    # Save the last key
    if current_key is not None:
        metadata[current_key] = " ".join(current_value_parts).strip()

    return metadata


def _derive_tool_name(skill_dir_name: str) -> str:
    """
    Derive the underlying CLI tool name from a skill directory name.

    This is a fallback when the skill is not in SKILL_TO_TOOL_MAP.
    It takes the first segment before '-security-scan', '-scan', or
    the first '-' delimited segment.

    Args:
        skill_dir_name: The directory name (e.g. "bandit-security-scan")

    Returns:
        The guessed tool name (e.g. "bandit")

    Examples:
        >>> _derive_tool_name("bandit-security-scan")
        'bandit'
        >>> _derive_tool_name("my-custom-tool")
        'my-custom-tool'
    """
    # Try removing common suffixes first
    for suffix in ("-security-scan", "-scan"):
        if skill_dir_name.endswith(suffix):
            return skill_dir_name[: -len(suffix)]

    # Fall back to the full directory name (it might be a valid tool name)
    return skill_dir_name


def _discover_skills_in_directory(skills_dir: Path, source_label: str) -> List[dict]:
    """
    Discover all Copilot skills in a single directory.

    Scans the given directory for subdirectories that contain a SKILL.md file,
    parses the frontmatter, maps to the underlying tool, and checks availability.

    Args:
        skills_dir: Path to a skills directory (e.g. ~/.copilot/skills/)
        source_label: Human-readable label for the source ("user" or "project")

    Returns:
        A list of skill dictionaries. Each dict has these keys:
        - "name":           Skill name from frontmatter (or folder name)
        - "description":    One-line description from frontmatter
        - "tool_name":      The underlying CLI tool binary name
        - "tool_available": True if the tool is found on PATH
        - "tool_path":      Full path to the tool binary (or None)
        - "source":         "user" or "project"
        - "skill_dir":      Full path to the skill directory
    """
    discovered_skills = []

    if not skills_dir.is_dir():
        logger.debug(f"Skills directory does not exist: {skills_dir}")
        return discovered_skills

    # Iterate over subdirectories in the skills directory
    try:
        entries = sorted(skills_dir.iterdir())
    except PermissionError:
        logger.warning(f"Permission denied reading: {skills_dir}")
        return discovered_skills

    for entry in entries:
        if not entry.is_dir():
            continue

        # Check for SKILL.md in this subdirectory
        skill_md_path = entry / "SKILL.md"
        if not skill_md_path.is_file():
            logger.debug(f"Skipping {entry.name}: no SKILL.md found")
            continue

        # Parse the frontmatter
        metadata = _parse_skill_frontmatter(skill_md_path)

        # Get the skill name (prefer frontmatter, fall back to dir name)
        skill_name = metadata.get("name", entry.name)

        # Get the description (first sentence only, for brevity)
        raw_description = metadata.get("description", "")
        # Truncate to the first sentence or 100 chars for display
        description = raw_description
        # Find first sentence boundary for a concise display version
        first_period = raw_description.find(".")
        if first_period > 0 and first_period < 120:
            description = raw_description[: first_period + 1]
        elif len(raw_description) > 120:
            description = raw_description[:117] + "..."

        # Determine the underlying tool name
        tool_name = SKILL_TO_TOOL_MAP.get(entry.name)
        if tool_name is None:
            tool_name = _derive_tool_name(entry.name)

        # Check if the tool is available on the system
        tool_path = shutil.which(tool_name)
        tool_available = tool_path is not None

        skill_info = {
            "name": skill_name,
            "description": description,
            "tool_name": tool_name,
            "tool_available": tool_available,
            "tool_path": tool_path,
            "source": source_label,
            "skill_dir": str(entry),
        }

        discovered_skills.append(skill_info)
        logger.debug(
            f"Discovered skill: {skill_name} "
            f"(tool={tool_name}, available={tool_available})"
        )

    return discovered_skills


def discover_all_skills(project_root: Optional[str] = None) -> List[dict]:
    """
    Discover all Copilot CLI agentic skills from both user and project levels.

    The Copilot CLI searches for skills in two locations:
      1. User-level:    ~/.copilot/skills/
      2. Project-level: <project_root>/.copilot/skills/

    This function scans both directories, parses each skill's SKILL.md
    frontmatter, maps the skill to its underlying CLI tool, and checks
    whether that tool is installed on the system.

    Args:
        project_root: Path to the project root directory.
                      If None, only user-level skills are discovered.

    Returns:
        A list of skill dictionaries, sorted by name. Each dict contains:
        - "name":           Skill name (e.g. "bandit-security-scan")
        - "description":    Short description of the skill
        - "tool_name":      CLI tool binary name (e.g. "bandit")
        - "tool_available": True if the tool is found on PATH
        - "tool_path":      Absolute path to the tool binary, or None
        - "source":         "user" or "project"
        - "skill_dir":      Absolute path to the skill directory

    Example:
        >>> skills = discover_all_skills("/home/user/my-project")
        >>> for skill in skills:
        ...     mark = "✅" if skill["tool_available"] else "⬜"
        ...     print(f"  {mark} {skill['tool_name']:<20} — {skill['description']}")
    """
    all_skills = []

    # Step 1: Discover user-level skills from ~/.copilot/skills/
    user_skills_dir = _get_user_skills_dir()
    user_skills = _discover_skills_in_directory(user_skills_dir, source_label="user")
    all_skills.extend(user_skills)

    logger.info(
        f"Found {len(user_skills)} user-level skills in {user_skills_dir}"
    )

    # Step 2: Discover project-level skills from <project>/.copilot/skills/
    if project_root is not None:
        project_skills_dir = _get_project_skills_dir(project_root)
        project_skills = _discover_skills_in_directory(
            project_skills_dir, source_label="project"
        )
        all_skills.extend(project_skills)

        logger.info(
            f"Found {len(project_skills)} project-level skills in {project_skills_dir}"
        )

    # Sort by name for consistent display
    all_skills.sort(key=lambda skill: skill["name"])

    return all_skills


def get_skill_summary(skills: List[dict]) -> dict:
    """
    Generate a summary of discovered skills.

    This function provides quick statistics for the discovered skills,
    which is useful for the CLI status display.

    Args:
        skills: List of skill dictionaries from discover_all_skills().

    Returns:
        A dictionary with:
        - "total":       Total number of skills discovered
        - "available":   Number of skills whose tool is available
        - "unavailable": Number of skills whose tool is NOT available
        - "user_count":  Number of user-level skills
        - "project_count": Number of project-level skills

    Example:
        >>> skills = discover_all_skills()
        >>> summary = get_skill_summary(skills)
        >>> print(f"Available: {summary['available']}/{summary['total']}")
    """
    total = len(skills)
    available = sum(1 for s in skills if s["tool_available"])
    unavailable = total - available
    user_count = sum(1 for s in skills if s["source"] == "user")
    project_count = sum(1 for s in skills if s["source"] == "project")

    return {
        "total": total,
        "available": available,
        "unavailable": unavailable,
        "user_count": user_count,
        "project_count": project_count,
    }
