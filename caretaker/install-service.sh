#!/bin/bash
# Install the Digiquarium Caretaker as a systemd service
# Run this script with sudo

set -e

SERVICE_FILE="/home/ijneb/digiquarium/caretaker/digiquarium-caretaker.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Digiquarium Caretaker service..."

# Make scripts executable
chmod +x /home/ijneb/digiquarium/caretaker/start-caretaker.sh
chmod +x /home/ijneb/digiquarium/caretaker/caretaker.py

# Copy service file
cp "$SERVICE_FILE" "$SYSTEMD_DIR/"

# Reload systemd
systemctl daemon-reload

# Enable and start service
systemctl enable digiquarium-caretaker.service
systemctl start digiquarium-caretaker.service

echo ""
echo "✅ Caretaker service installed!"
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status digiquarium-caretaker"
echo "  Logs:    sudo journalctl -u digiquarium-caretaker -f"
echo "  Stop:    sudo systemctl stop digiquarium-caretaker"
echo "  Start:   sudo systemctl start digiquarium-caretaker"
echo ""