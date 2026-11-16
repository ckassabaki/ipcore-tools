# 🚀 Deployment Instructions

## Next Steps to Get This Running

### 1. Push to GitHub

```bash
# On your Windows machine:
cd C:\Users\T6002038\ipcore-tools

# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR-ORG/ipcore-tools.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Server1

```bash
# SSH to Server1
ssh user@server1

# Clone the repo
cd ~
git clone https://github.com/YOUR-ORG/ipcore-tools.git
cd ipcore-tools

# Run install script
chmod +x deploy/*.sh
./deploy/install.sh

# Install as systemd service
./deploy/install_service.sh
```

### 3. Access the Registry

Open browser to: **http://server1:8008**

---

## Local Testing (Optional)

Want to test locally first?

```bash
# On Windows (in Git Bash or WSL):
cd C:\Users\T6002038\ipcore-tools

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python db_tools_registry.py

# Run the app
python app.py

# Open: http://localhost:8008
```

---

## Quick Commands Reference

### On Server1 (after deployment):

```bash
# Check service status
systemctl --user status tool-registry

# Restart service
systemctl --user restart tool-registry

# View logs
journalctl --user -u tool-registry -f

# Pull updates
cd ~/ipcore-tools
git pull
systemctl --user restart tool-registry

# Run crawlers manually
cd ~/ipcore-tools
source .venv/bin/activate
python crawlers/run_all.py
```

---

## Features Ready to Use

✅ **Search & Filter**
- Search by name, description, keywords
- Filter by type, category, status
- Tag-based filtering (#juniper #backup)

✅ **Submit Tools**
- Click [+ Submit New Tool] button
- Fill in name, description, type, URL, tags
- Auto-categorization

✅ **Auto-Discovery**
- Click [🔄 Sync] to run crawlers
- Discovers: Skills, MCP servers, n8n workflows, GitHub repos

✅ **Export**
- Export JSON, CSV, or Markdown
- Share with team

---

## Troubleshooting

**Port 8008 already in use?**
Edit `app.py` line 72: change `port=8008` to another port

**Permission denied on scripts?**
```bash
chmod +x deploy/*.sh
```

**Database errors?**
```bash
rm cache/tools_registry.db
python db_tools_registry.py
```

---

## What's Next?

1. Push to GitHub
2. Deploy on Server1
3. Run crawlers to discover existing tools
4. Share URL with team
5. Post in GChat for submissions!

**Your tool registry will be live at:** `http://server1:8008`
