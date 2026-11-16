"""Database layer for IPCore Tools Registry"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

DB_PATH = Path(__file__).parent / "cache" / "tools_registry.db"


def init_db():
    """Initialize tools registry database with schema."""
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tools table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            tool_type TEXT NOT NULL,
            category TEXT,
            access_url TEXT,
            access_method TEXT,
            config_path TEXT,
            parameters TEXT,
            dependencies TEXT,
            tags TEXT,
            screenshot_path TEXT,
            status TEXT DEFAULT 'untested',
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP
        )
    """)

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            color TEXT
        )
    """)

    # Tool tags table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_tags (
            tool_id INTEGER REFERENCES tools(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            PRIMARY KEY (tool_id, tag)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_type ON tools(tool_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools(tags)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_name ON tools(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_tags_tag ON tool_tags(tag)")

    # Insert default categories
    categories = [
        ("Network Automation", "Device config, backup, health monitoring", "🔧", "#3b82f6"),
        ("AI & LLM", "Claude skills, MCP servers, chatbots", "🤖", "#8b5cf6"),
        ("Workflows", "n8n automations, data sync, ETL", "⚙️", "#06b6d4"),
        ("Infrastructure", "Labs, Containerlab, Docker", "🏗️", "#f59e0b"),
        ("Governance", "GTLP decks, presentations, reporting", "📊", "#ec4899"),
        ("Documentation", "Knowledge bases, guides, READMEs", "📚", "#10b981"),
        ("Testing & Quality", "Benchmarking, RAG testing, code review", "✅", "#22c55e"),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO categories (name, description, icon, color) VALUES (?, ?, ?, ?)",
        categories
    )

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


def get_db():
    """Get database connection (read-write)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_tool(tool_data: dict) -> int:
    """Insert tool into registry, return ID."""
    conn = get_db()
    cursor = conn.cursor()

    # Extract tags if provided
    tags = tool_data.pop("tags", "")
    if isinstance(tags, list):
        tags = ",".join(tags)

    # Insert tool
    columns = ", ".join(tool_data.keys())
    placeholders = ", ".join(["?"] * len(tool_data))

    cursor.execute(
        f"INSERT INTO tools ({columns}) VALUES ({placeholders})",
        list(tool_data.values())
    )

    tool_id = cursor.lastrowid

    # Insert tags
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            cursor.execute(
                "INSERT OR IGNORE INTO tool_tags (tool_id, tag) VALUES (?, ?)",
                (tool_id, tag)
            )

    conn.commit()
    conn.close()

    return tool_id


def add_or_update_tool(tool_data: dict) -> int:
    """Insert or update tool if name already exists."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if tool with same name exists
    existing = cursor.execute(
        "SELECT id FROM tools WHERE name = ?",
        (tool_data.get("name"),)
    ).fetchone()

    conn.close()

    if existing:
        # Update existing
        tool_id = existing["id"]
        update_tool(tool_id, tool_data)
        return tool_id
    else:
        # Insert new
        return add_tool(tool_data)


def update_tool(tool_id: int, tool_data: dict):
    """Update existing tool."""
    conn = get_db()
    cursor = conn.cursor()

    # Extract tags if provided
    tags = tool_data.pop("tags", None)

    # Update tool fields
    if tool_data:
        set_clause = ", ".join([f"{k} = ?" for k in tool_data.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"

        cursor.execute(
            f"UPDATE tools SET {set_clause} WHERE id = ?",
            list(tool_data.values()) + [tool_id]
        )

    # Update tags if provided
    if tags is not None:
        # Delete existing tags
        cursor.execute("DELETE FROM tool_tags WHERE tool_id = ?", (tool_id,))

        # Insert new tags
        if isinstance(tags, str):
            tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        else:
            tag_list = tags

        for tag in tag_list:
            cursor.execute(
                "INSERT OR IGNORE INTO tool_tags (tool_id, tag) VALUES (?, ?)",
                (tool_id, tag)
            )

    conn.commit()
    conn.close()


def search_tools(
    query: Optional[str] = None,
    tool_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    tag_match: str = "any",
    status: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Search tools with filters."""
    conn = get_db()
    cursor = conn.cursor()

    sql = "SELECT DISTINCT t.* FROM tools t"
    conditions = []
    params = []

    # Tag filtering requires join
    if tags:
        if tag_match == "all":
            # Must have ALL tags - use multiple joins
            for i, tag in enumerate(tags):
                sql += f" INNER JOIN tool_tags tt{i} ON t.id = tt{i}.tool_id AND tt{i}.tag = ?"
                params.append(tag.lower())
        else:
            # Must have ANY tag - single join with IN clause
            sql += " INNER JOIN tool_tags tt ON t.id = tt.tool_id"
            placeholders = ",".join(["?"] * len(tags))
            conditions.append(f"tt.tag IN ({placeholders})")
            params.extend([tag.lower() for tag in tags])

    # Text search
    if query:
        conditions.append("(t.name LIKE ? OR t.description LIKE ? OR t.tags LIKE ?)")
        search_param = f"%{query}%"
        params.extend([search_param, search_param, search_param])

    # Type filter
    if tool_type:
        conditions.append("t.tool_type = ?")
        params.append(tool_type)

    # Category filter
    if category:
        conditions.append("t.category = ?")
        params.append(category)

    # Status filter
    if status:
        conditions.append("t.status = ?")
        params.append(status)

    # Build WHERE clause
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    # Order and limit
    sql += " ORDER BY t.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    # Convert to dict and add tags
    tools = []
    for row in rows:
        tool = dict(row)

        # Fetch tags for this tool
        cursor.execute(
            "SELECT tag FROM tool_tags WHERE tool_id = ?",
            (tool["id"],)
        )
        tool_tags = [r["tag"] for r in cursor.fetchall()]
        tool["tag_list"] = tool_tags

        tools.append(tool)

    conn.close()
    return tools


def get_tool_by_id(tool_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve single tool details."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tools WHERE id = ?", (tool_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    tool = dict(row)

    # Fetch tags
    cursor.execute(
        "SELECT tag FROM tool_tags WHERE tool_id = ?",
        (tool_id,)
    )
    tool["tag_list"] = [r["tag"] for r in cursor.fetchall()]

    conn.close()
    return tool


def get_all_tags() -> List[Dict[str, Any]]:
    """Get all tags with counts."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tag, COUNT(*) as count
        FROM tool_tags
        GROUP BY tag
        ORDER BY count DESC, tag ASC
    """)

    tags = [{"tag": row["tag"], "count": row["count"]} for row in cursor.fetchall()]

    conn.close()
    return tags


def get_all_categories() -> List[Dict[str, Any]]:
    """Get all categories with tool counts."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*, COUNT(t.id) as count
        FROM categories c
        LEFT JOIN tools t ON c.name = t.category
        GROUP BY c.id
        ORDER BY c.name
    """)

    categories = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return categories


def get_stats() -> Dict[str, Any]:
    """Get registry statistics."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM tools")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT tool_type, COUNT(*) as count FROM tools GROUP BY tool_type")
    by_type = {row["tool_type"]: row["count"] for row in cursor.fetchall()}

    cursor.execute("SELECT category, COUNT(*) as count FROM tools GROUP BY category")
    by_category = {row["category"]: row["count"] for row in cursor.fetchall()}

    conn.close()

    return {
        "total": total,
        "by_type": by_type,
        "by_category": by_category
    }


if __name__ == "__main__":
    init_db()
