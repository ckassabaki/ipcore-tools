"""Crawler for MCP server configurations"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import db_tools_registry as db


MCP_CONFIG = Path.home() / ".claude" / "mcp.json"


def crawl_mcp_servers() -> int:
    """
    Parse ~/.claude/mcp.json for configured MCP servers.

    Returns:
        Number of MCP servers discovered
    """
    if not MCP_CONFIG.exists():
        print(f"⚠️  MCP config not found: {MCP_CONFIG}")
        return 0

    try:
        with open(MCP_CONFIG, encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse MCP config: {e}")
        return 0

    discovered_tools = []

    for server_name, server_config in config.items():
        command = server_config.get("command", "N/A")
        env = server_config.get("env", {})

        # Extract URL if present (e.g., NETBOX_URL)
        access_url = None
        for key, value in env.items():
            if "URL" in key.upper():
                access_url = value
                break

        tool_data = {
            "name": f"{server_name} MCP Server",
            "description": f"MCP server for {server_name} - {command}",
            "tool_type": "mcp_server",
            "access_url": access_url,
            "access_method": "mcp",
            "config_path": str(MCP_CONFIG),
            "parameters": json.dumps(server_config),
            "dependencies": command.split()[0] if command else None,  # e.g., 'uv'
            "tags": f"mcp,{server_name}",
            "source": "crawler:mcp",
        }

        discovered_tools.append(tool_data)

    # Bulk insert/update
    for tool in discovered_tools:
        db.add_or_update_tool(tool)

    return len(discovered_tools)


if __name__ == "__main__":
    count = crawl_mcp_servers()
    print(f"✅ Discovered {count} MCP servers")
