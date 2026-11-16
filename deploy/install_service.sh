#!/bin/bash
# Install IPCore Tools Registry as systemd service

set -e

INSTALL_DIR=$(pwd)
SERVICE_NAME="tool-registry"
SERVICE_FILE="$HOME/.config/systemd/user/$SERVICE_NAME.service"

echo "📦 Installing systemd service..."

# Create systemd user directory
mkdir -p "$HOME/.config/systemd/user"

# Replace placeholders in service file
sed "s|%USER%|$USER|g; s|%INSTALL_DIR%|$INSTALL_DIR|g" \
    deploy/tool-registry.service > "$SERVICE_FILE"

# Reload systemd
systemctl --user daemon-reload

# Enable and start service
systemctl --user enable $SERVICE_NAME
systemctl --user start $SERVICE_NAME

# Check status
sleep 2
systemctl --user status $SERVICE_NAME --no-pager

echo ""
echo "✅ Service installed and started!"
echo ""
echo "Commands:"
echo "  systemctl --user status $SERVICE_NAME     # Check status"
echo "  systemctl --user restart $SERVICE_NAME    # Restart"
echo "  systemctl --user stop $SERVICE_NAME       # Stop"
echo "  systemctl --user logs -f $SERVICE_NAME    # View logs"
echo ""
echo "Access at: http://$(hostname):8090"
echo ""
