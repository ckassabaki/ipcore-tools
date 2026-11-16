"""API routes for IPCore Tools Registry"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional, List
import db_tools_registry as db
import categorizer
from pathlib import Path
import json
import csv
import io

router = APIRouter(prefix="/api/tools", tags=["tools"])

# Pydantic models
class ToolCreate(BaseModel):
    name: str
    description: str
    tool_type: str
    access_url: Optional[str] = None
    access_method: Optional[str] = None
    config_path: Optional[str] = None
    parameters: Optional[str] = None
    dependencies: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = "untested"


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_type: Optional[str] = None
    access_url: Optional[str] = None
    access_method: Optional[str] = None
    config_path: Optional[str] = None
    parameters: Optional[str] = None
    dependencies: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class SmartImport(BaseModel):
    url: str


@router.get("/")
async def list_tools(
    search: Optional[str] = None,
    tool_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,  # comma-separated
    tag_match: str = "any",  # "any" or "all"
    status: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0
):
    """
    List/search tools with filtering.

    Args:
        search: Text search in name/description
        tool_type: Filter by type (skill, mcp_server, n8n_workflow, web_ui, lab, other)
        category: Filter by category
        tags: Comma-separated tags to filter by
        tag_match: "any" (OR) or "all" (AND) for tag matching
        status: Filter by status (working, untested, broken, deprecated)
        limit: Max results (default 1000)
        offset: Pagination offset

    Returns:
        JSON with tools array and count
    """
    tag_list = None
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

    tools = db.search_tools(
        query=search,
        tool_type=tool_type,
        category=category,
        tags=tag_list,
        tag_match=tag_match,
        status=status,
        limit=limit,
        offset=offset
    )

    return JSONResponse({
        "tools": tools,
        "count": len(tools),
        "filters": {
            "search": search,
            "tool_type": tool_type,
            "category": category,
            "tags": tag_list,
            "tag_match": tag_match,
            "status": status
        }
    })


@router.get("/{tool_id}")
async def get_tool(tool_id: int):
    """Get single tool details by ID."""
    tool = db.get_tool_by_id(tool_id)

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")

    return JSONResponse(tool)


@router.post("/")
async def create_tool(tool: ToolCreate):
    """
    Create new tool (manual submission).

    Returns created tool ID.
    """
    tool_dict = tool.dict(exclude_none=True)
    tool_dict["source"] = "manual"

    # Auto-categorize if no category provided
    if not tool_dict.get("category"):
        category = categorizer.auto_categorize_tool(tool_dict)
        if category:
            tool_dict["category"] = category

    try:
        tool_id = db.add_tool(tool_dict)
        return JSONResponse({
            "id": tool_id,
            "status": "created",
            "category": tool_dict.get("category")
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tool: {str(e)}")


@router.put("/{tool_id}")
async def update_tool(tool_id: int, tool: ToolUpdate):
    """Update existing tool."""
    existing = db.get_tool_by_id(tool_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")

    tool_dict = tool.dict(exclude_none=True)

    try:
        db.update_tool(tool_id, tool_dict)
        return JSONResponse({"id": tool_id, "status": "updated"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tool: {str(e)}")


@router.delete("/{tool_id}")
async def delete_tool(tool_id: int):
    """Delete a tool."""
    existing = db.get_tool_by_id(tool_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    conn.commit()
    conn.close()

    return JSONResponse({"id": tool_id, "status": "deleted"})


@router.post("/{tool_id}/screenshot")
async def upload_screenshot(tool_id: int, file: UploadFile = File(...)):
    """Upload screenshot/demo image for a tool."""
    tool = db.get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")

    # Save screenshot
    screenshots_dir = Path(__file__).parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    file_ext = Path(file.filename).suffix
    screenshot_path = screenshots_dir / f"tool_{tool_id}{file_ext}"

    with open(screenshot_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update tool record
    db.update_tool(tool_id, {"screenshot_path": str(screenshot_path)})

    return JSONResponse({
        "tool_id": tool_id,
        "screenshot_path": str(screenshot_path),
        "status": "uploaded"
    })


@router.get("/tags/all")
async def list_tags():
    """Get all tags with counts."""
    tags = db.get_all_tags()
    return JSONResponse({"tags": tags, "count": len(tags)})


@router.get("/categories/all")
async def list_categories():
    """Get all categories with tool counts."""
    categories = db.get_all_categories()
    return JSONResponse({"categories": categories, "count": len(categories)})


@router.get("/stats")
async def get_stats():
    """Get registry statistics."""
    stats = db.get_stats()
    return JSONResponse(stats)


@router.post("/sync")
async def sync_tools():
    """
    Trigger crawler sync to discover tools.
    This runs all crawlers and returns summary.
    """
    try:
        from crawlers.run_all import sync_all_tools
        summary = sync_all_tools()

        # Auto-categorize newly discovered tools
        categorizer.auto_categorize_all()

        return JSONResponse({
            "status": "synced",
            "summary": summary
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/import")
async def smart_import(data: SmartImport):
    """
    Smart import from URL (GitHub, web, etc.).
    Auto-detects tool type and extracts metadata.
    """
    url = data.url

    try:
        # Detect source type and scan
        if "github.com" in url:
            from crawlers.github_crawler import scan_single_repo
            discovered = scan_single_repo(url)
        elif url.startswith("http"):
            # Web URL - basic scraping
            discovered = [{
                "name": url.split("/")[-1] or "Web Tool",
                "description": f"Tool at {url}",
                "tool_type": "web_ui",
                "access_url": url,
                "access_method": "web",
                "source": "smart_import"
            }]
        else:
            raise HTTPException(status_code=400, detail="Unsupported URL format")

        # Auto-categorize discovered tools
        for tool in discovered:
            if not tool.get("category"):
                category = categorizer.auto_categorize_tool(tool)
                if category:
                    tool["category"] = category

        return JSONResponse({
            "discovered": discovered,
            "count": len(discovered),
            "url": url
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/import/confirm")
async def confirm_import(tools: List[dict]):
    """
    User reviewed and confirmed tools to import.
    Bulk insert into database.
    """
    imported_ids = []

    for tool in tools:
        tool["source"] = "smart_import"
        try:
            tool_id = db.add_tool(tool)
            imported_ids.append(tool_id)
        except Exception as e:
            print(f"Failed to import tool: {e}")
            continue

    return JSONResponse({
        "imported": len(imported_ids),
        "ids": imported_ids
    })


@router.post("/bulk")
async def bulk_import(file: UploadFile = File(...)):
    """
    Import tools from CSV file.

    Expected CSV columns: name,description,tool_type,access_url,tags
    """
    try:
        content = await file.read()
        text = content.decode("utf-8")

        reader = csv.DictReader(io.StringIO(text))

        imported = 0
        for row in reader:
            row["source"] = "bulk_import"

            # Auto-categorize
            category = categorizer.auto_categorize_tool(row)
            if category:
                row["category"] = category

            db.add_tool(row)
            imported += 1

        return JSONResponse({
            "imported": imported,
            "status": "success"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")


@router.get("/export")
async def export_tools(format: str = "json"):
    """
    Export all tools in specified format.

    Args:
        format: "json", "csv", or "markdown"

    Returns:
        Exported data
    """
    tools = db.search_tools()

    if format == "json":
        return JSONResponse({
            "tools": tools,
            "count": len(tools),
            "exported_at": str(db.datetime.now())
        })

    elif format == "csv":
        output = io.StringIO()
        if tools:
            writer = csv.DictWriter(output, fieldnames=tools[0].keys())
            writer.writeheader()
            writer.writerows(tools)

        return PlainTextResponse(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ipcore-tools.csv"}
        )

    elif format == "markdown":
        lines = ["# IPCore Tools Registry\n"]

        # Group by category
        by_category = {}
        for tool in tools:
            cat = tool.get("category") or "Uncategorized"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(tool)

        for category, cat_tools in sorted(by_category.items()):
            lines.append(f"\n## {category}\n")
            for tool in cat_tools:
                lines.append(f"### {tool['name']}")
                lines.append(f"{tool['description']}\n")
                if tool.get("access_url"):
                    lines.append(f"- **URL:** {tool['access_url']}")
                if tool.get("tags"):
                    lines.append(f"- **Tags:** {tool['tags']}")
                lines.append("")

        return PlainTextResponse(
            content="\n".join(lines),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=ipcore-tools.md"}
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
