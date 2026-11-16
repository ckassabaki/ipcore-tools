"""Auto-categorization engine for tools"""

from typing import Optional, Dict
import db_tools_registry as db


CATEGORY_KEYWORDS = {
    "Network Automation": [
        "network", "juniper", "nokia", "router", "switch", "device",
        "config", "backup", "netconf", "ssh", "telnet", "snmp",
        "bgp", "ospf", "isis", "mpls", "vlan", "interface",
        "sros", "junos", "ios", "nxos", "eos"
    ],
    "AI & LLM": [
        "claude", "ai", "mcp", "chatbot", "assistant", "llm",
        "prompt", "anthropic", "openai", "gpt", "model",
        "agent", "rag", "embedding", "vector"
    ],
    "Workflows": [
        "n8n", "workflow", "automation", "sync", "etl",
        "pipeline", "orchestration", "integration", "webhook",
        "schedule", "cron", "trigger"
    ],
    "Infrastructure": [
        "docker", "containerlab", "lab", "deploy", "systemd",
        "kubernetes", "k8s", "compose", "container", "vm",
        "virtual", "testbed", "topology", "clab"
    ],
    "Governance": [
        "gtlp", "presentation", "deck", "powerpoint", "slidev",
        "governance", "compliance", "report", "dashboard",
        "metrics", "kpi"
    ],
    "Documentation": [
        "readme", "docs", "guide", "wiki", "documentation",
        "reference", "manual", "tutorial", "howto", "knowledge"
    ],
    "Testing & Quality": [
        "test", "benchmark", "rag", "quality", "validation",
        "verify", "check", "lint", "scan", "audit"
    ]
}


def auto_categorize_tool(tool: Dict) -> Optional[str]:
    """
    Assign category based on keywords in name/description/tags.

    Args:
        tool: Tool dictionary with name, description, tags fields

    Returns:
        Category name or None if no match
    """
    # Combine searchable text
    text = " ".join([
        tool.get("name", ""),
        tool.get("description", ""),
        tool.get("tags", ""),
        tool.get("tool_type", "")
    ]).lower()

    # Score each category
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[category] = score

    # Return category with highest score (if > 0)
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)

    return None


def auto_categorize_all():
    """Categorize all tools missing category field."""
    conn = db.get_db()
    cursor = conn.cursor()

    # Get tools without category
    cursor.execute("SELECT * FROM tools WHERE category IS NULL OR category = ''")
    tools = cursor.fetchall()

    updated = 0
    for tool in tools:
        category = auto_categorize_tool(dict(tool))
        if category:
            cursor.execute(
                "UPDATE tools SET category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (category, tool["id"])
            )
            updated += 1

    conn.commit()
    conn.close()

    print(f"✅ Auto-categorized {updated} tools")
    return updated


def extract_tags_from_text(text: str, max_tags: int = 10) -> list[str]:
    """
    Extract potential tags from text using common keywords.

    Args:
        text: Text to extract tags from
        max_tags: Maximum number of tags to return

    Returns:
        List of tag strings
    """
    text = text.lower()
    found_tags = set()

    # Check all category keywords as potential tags
    for keywords in CATEGORY_KEYWORDS.values():
        for keyword in keywords:
            if keyword in text and len(keyword) > 2:  # Skip very short words
                found_tags.add(keyword)

    # Return most relevant tags (limited)
    return sorted(list(found_tags))[:max_tags]


if __name__ == "__main__":
    # Test categorization
    auto_categorize_all()
