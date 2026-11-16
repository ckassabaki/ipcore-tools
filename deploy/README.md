# Deployment Guide

## Quick Start (Development)

```bash
# Clone repo
git clone https://github.com/your-org/ipcore-tools.git
cd ipcore-tools

# Install
./deploy/install.sh

# Run manually
source .venv/bin/activate
uvicorn app:app --port 8090 --reload
```

## Production Deployment (systemd service)

```bash
# Install and start service
./deploy/install_service.sh

# Service will run automatically on boot
# Access at http://server-ip:8090
```

## Manual systemd Service

If install_service.sh doesn't work, manually create:

```bash
# Create service file
nano ~/.config/systemd/user/tool-registry.service
```

Paste:
```
[Unit]
Description=IPCore Tools Registry
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/youruser/ipcore-tools
Environment="PATH=/home/youruser/ipcore-tools/.venv/bin"
ExecStart=/home/youruser/ipcore-tools/.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8090
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
systemctl --user daemon-reload
systemctl --user enable tool-registry
systemctl --user start tool-registry
```

## Updating

```bash
cd ~/ipcore-tools
git pull
systemctl --user restart tool-registry
```

## Troubleshooting

**Port already in use:**
```bash
# Check what's using port 8090
lsof -i :8090
# Or use different port in app.py
```

**Permission denied:**
```bash
chmod +x deploy/*.sh
```

**Service won't start:**
```bash
# Check logs
journalctl --user -u tool-registry -f

# Check status
systemctl --user status tool-registry
```
