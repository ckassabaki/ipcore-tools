# IPCore Tools Registry

Centralized searchable catalog of IP Core team AI tools, scripts, MCP servers, workflows, and automation utilities.

## Features

- 🔍 **Smart Search** - Search by name, description, tags
- 🏷️ **Tag Filtering** - Filter by multiple tags (#juniper #backup #mcp)
- 📂 **Category Browse** - Network, AI/LLM, Workflows, Infrastructure, etc.
- ➕ **Quick Submit** - Add tools via simple web form
- 🔗 **Smart Import** - Paste GitHub/URL to auto-extract tool info
- 🤖 **Auto-Discovery** - Crawls for local skills, MCP configs, n8n workflows
- 📤 **Export** - JSON, CSV, Markdown formats
- 💚 **Status Tracking** - Working, Untested, Broken, Deprecated

## Quick Start

### Local Development

```bash
# Clone the repo
git clone https://github.com/your-org/ipcore-tools.git
cd ipcore-tools

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from db_tools_registry import init_db; init_db()"

# Run the app
uvicorn app:app --port 8081 --reload

# Open browser
# http://localhost:8081
```

### Production Deployment (Server1)

```bash
# Clone on server
cd ~
git clone https://github.com/your-org/ipcore-tools.git
cd ipcore-tools

# Run install script
./deploy/install.sh

# Service runs at http://server1:8081
```

## Usage

### Browse Tools
Visit `http://server1:8090` and browse by category or search.

### Submit a Tool
Click **[+ Submit Tool]** button, fill in:
- Name (required)
- Description (required)
- Type (required): Skill, MCP Server, n8n Workflow, Web UI, Lab, Other
- URL (optional)
- Tags (optional, comma-separated)
- Screenshot (optional)

### Smart Import
Click **[🔗 Import from Link]**, paste:
- GitHub repo URL
- Web UI URL
- Local file path

System auto-detects tool type and fills form.

### Search by Tags
Search bar supports tag filtering:
```
#juniper #backup          → Tools with both tags
network #mcp              → "network" in text + #mcp tag
```

Or click tags in the tag cloud sidebar.

## API

### Endpoints

```bash
# List all tools
GET /api/tools

# Search
GET /api/tools?search=backup

# Filter by category
GET /api/tools?category=Network%20Automation

# Filter by tags
GET /api/tools?tags=juniper,backup&tag_match=all

# Get specific tool
GET /api/tools/{id}

# Create tool
POST /api/tools
Body: {"name": "...", "description": "...", "tool_type": "..."}

# Smart import
POST /api/tools/import
Body: {"url": "https://github.com/..."}

# Trigger crawler sync
POST /api/tools/sync

# Export
GET /api/tools/export?format=json|csv|markdown
```

## Project Structure

```
ipcore-tools/
├── app.py                     # Main FastAPI application
├── db_tools_registry.py       # Database layer (SQLite)
├── tools_routes.py            # API routes
├── categorizer.py             # Auto-categorization engine
├── templates/
│   └── tools.html             # Web UI
├── crawlers/
│   ├── skills_crawler.py      # Scan ~/.claude/skills
│   ├── mcp_crawler.py         # Parse mcp.json
│   ├── n8n_crawler.py         # Find n8n workflows
│   ├── github_crawler.py      # Scan git repos
│   └── run_all.py             # Orchestration
├── deploy/
│   ├── install.sh             # Setup script
│   └── tool-registry.service  # systemd service
├── cache/
│   └── tools_registry.db      # SQLite database (created on first run)
└── screenshots/               # Uploaded screenshots
```

## Updating

```bash
# Pull latest changes
cd ~/ipcore-tools
git pull

# Restart service
systemctl --user restart tool-registry
```

## Contributing

### Add Your Tools

1. Visit the web UI and submit via form, OR
2. Use smart import with your GitHub repo URL, OR
3. Export your local tools and create PR:
   ```bash
   # On your machine
   curl http://localhost:8090/api/tools/export?format=json > my-tools.json
   
   # Create PR with my-tools.json
   ```

## Database

SQLite database at `cache/tools_registry.db` with tables:
- `tools` - Tool metadata
- `categories` - Tool categories
- `tool_tags` - Tag associations

## Auto-Discovery

On startup (or via `/api/tools/sync`), crawlers scan for:
- **Claude Skills** - `~/.claude/skills/*/SKILL.md`
- **MCP Servers** - `~/.claude/mcp.json`
- **n8n Workflows** - `~/*.json` (matching n8n structure)
- **GitHub Repos** - `~/**/.git` directories

## Configuration

Edit `app.py` to change:
- Port number (default: 8090)
- Database path (default: cache/tools_registry.db)
- Crawler paths

## Troubleshooting

**Port already in use:**
```bash
# Change port in app.py or run with:
uvicorn app:app --port 9000
```

**Database locked:**
```bash
# Check for running instances
ps aux | grep uvicorn
# Kill if needed, restart
```

**No tools found:**
```bash
# Manually trigger crawlers
python crawlers/run_all.py
```

## License

Internal use - IP Core Lab team

## Support

Questions? Ask in GChat or create an issue.
