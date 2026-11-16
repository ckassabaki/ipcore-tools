"""Crawler for Claude Code skills"""

from pathlib import Path
import sys

# Add parent directory to path for db import
sys.path.insert(0, str(Path(__file__).parent.parent))
import db_tools_registry as db


SKILLS_DIR = Path.home() / ".claude" / "skills"


def parse_skill_frontmatter(skill_md_path: Path) -> dict:
    """Parse SKILL.md frontmatter to extract metadata."""
    try:
        with open(skill_md_path, encoding="utf-8") as f:
            content = f.read()

        # Extract YAML frontmatter between --- markers
        if not content.startswith("---"):
            return {}

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}

        frontmatter = parts[1].strip()
        metadata = {}

        # Simple YAML parsing (name: value)
        for line in frontmatter.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"\'')

        return metadata

    except Exception as e:
        print(f"Failed to parse {skill_md_path}: {e}")
        return {}


def crawl_skills() -> int:
    """
    Scan ~/.claude/skills/ for SKILL.md files, extract metadata.

    Returns:
        Number of skills discovered
    """
    if not SKILLS_DIR.exists():
        print(f"⚠️  Skills directory not found: {SKILLS_DIR}")
        return 0

    discovered_tools = []

    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        # Parse frontmatter
        metadata = parse_skill_frontmatter(skill_md)

        if not metadata:
            # Fallback: use directory name
            metadata = {"name": skill_dir.name}

        tool_data = {
            "name": metadata.get("name", skill_dir.name),
            "description": metadata.get("description", f"Claude skill: {skill_dir.name}"),
            "tool_type": "skill",
            "access_url": None,  # Skills are local
            "access_method": "skill",
            "config_path": str(skill_md),
            "tags": f"claude,skill,{skill_dir.name}",
            "source": "crawler:skills",
        }

        discovered_tools.append(tool_data)

    # Bulk insert/update in database
    for tool in discovered_tools:
        db.add_or_update_tool(tool)

    return len(discovered_tools)


if __name__ == "__main__":
    count = crawl_skills()
    print(f"✅ Discovered {count} skills")
