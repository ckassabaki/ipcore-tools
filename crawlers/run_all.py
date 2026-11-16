"""Orchestration script to run all crawlers"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills_crawler import crawl_skills
from mcp_crawler import crawl_mcp_servers
from n8n_crawler import crawl_n8n_workflows
from github_crawler import crawl_github_repos
import db_tools_registry as db
import categorizer


def sync_all_tools() -> dict:
    """
    Run all crawlers and return summary.

    Returns:
        Dictionary with counts per crawler
    """
    summary = {}

    print("🔍 Starting tool discovery...")

    # Run each crawler
    summary["skills"] = crawl_skills()
    print(f"  ✓ Skills: {summary['skills']}")

    summary["mcp_servers"] = crawl_mcp_servers()
    print(f"  ✓ MCP Servers: {summary['mcp_servers']}")

    summary["n8n_workflows"] = crawl_n8n_workflows()
    print(f"  ✓ n8n Workflows: {summary['n8n_workflows']}")

    summary["github_repos"] = crawl_github_repos()
    print(f"  ✓ GitHub Repos: {summary['github_repos']}")

    # Auto-categorize all uncategorized tools
    print("\n🏷️  Auto-categorizing tools...")
    categorized = categorizer.auto_categorize_all()

    summary["categorized"] = categorized
    summary["total"] = sum(summary.values()) - categorized

    print(f"\n✅ Discovered {summary['total']} tools total")
    print(f"✅ Auto-categorized {categorized} tools")

    return summary


if __name__ == "__main__":
    sync_all_tools()
