"""Crawler for n8n workflow JSON files"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import db_tools_registry as db


def is_n8n_workflow(json_file: Path) -> bool:
    """Check if JSON file is an n8n workflow."""
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        # n8n workflows have 'nodes' and 'connections'
        return isinstance(data, dict) and "nodes" in data and "connections" in data

    except Exception:
        return False


def crawl_n8n_workflows(search_dir: Path = None) -> int:
    """
    Scan directory for n8n workflow JSON files.

    Args:
        search_dir: Directory to search (defaults to home directory)

    Returns:
        Number of workflows discovered
    """
    if search_dir is None:
        search_dir = Path.home()

    discovered_tools = []

    # Search for *.json files (only top-level, not recursive to avoid deep scans)
    for json_file in search_dir.glob("*.json"):
        if not is_n8n_workflow(json_file):
            continue

        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            workflow_name = data.get("name", json_file.stem)
            node_count = len(data.get("nodes", []))

            tool_data = {
                "name": workflow_name,
                "description": f"n8n workflow - {node_count} nodes",
                "tool_type": "n8n_workflow",
                "access_url": None,
                "access_method": "filesystem",
                "config_path": str(json_file),
                "tags": "n8n,workflow,automation",
                "source": "crawler:n8n",
            }

            discovered_tools.append(tool_data)

        except Exception as e:
            print(f"Failed to parse {json_file}: {e}")
            continue

    # Bulk insert/update
    for tool in discovered_tools:
        db.add_or_update_tool(tool)

    return len(discovered_tools)


if __name__ == "__main__":
    count = crawl_n8n_workflows()
    print(f"✅ Discovered {count} n8n workflows")
