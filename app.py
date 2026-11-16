"""IPCore Tools Registry - Main FastAPI Application"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn

# Import routes and database
from tools_routes import router as tools_router
import db_tools_registry as db

# Create FastAPI app
app = FastAPI(
    title="IPCore Tools Registry",
    description="Centralized searchable catalog of IP Core team AI tools, scripts, and automation utilities",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (screenshots)
screenshots_dir = Path("screenshots")
screenshots_dir.mkdir(exist_ok=True)
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# Include API routes
app.include_router(tools_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and run auto-discovery on startup."""
    print("🚀 Starting IPCore Tools Registry...")

    # Initialize database
    db.init_db()

    # Run crawler sync in background (optional - can comment out for faster startup)
    # Uncomment to auto-discover tools on startup:
    # import asyncio
    # from crawlers.run_all import sync_all_tools
    # asyncio.create_task(asyncio.to_thread(sync_all_tools))

    print("✅ IPCore Tools Registry ready at http://localhost:8090")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render main tools registry UI."""
    return templates.TemplateResponse("tools.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    stats = db.get_stats()
    return {
        "status": "healthy",
        "tools_count": stats["total"],
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Run with: python app.py
    # Or: uvicorn app:app --port 8081 --reload
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )
