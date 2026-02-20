#!/bin/bash
# =============================================================================
# RUN THIS SCRIPT ON THE NUC TO INSTALL THE AUTONOMOUS CARETAKER
# =============================================================================
# Usage: sudo ~/digiquarium/caretaker/INSTALL_NOW.sh
# =============================================================================

set -e

echo "=============================================="
echo "  INSTALLING DIGIQUARIUM AUTONOMOUS CARETAKER"
echo "=============================================="

# Make scripts executable
chmod +x /home/ijneb/digiquarium/caretaker/caretaker.py
chmod +x /home/ijneb/digiquarium/caretaker/start-caretaker.sh

# Copy service file to systemd
cp /home/ijneb/digiquarium/caretaker/digiquarium-caretaker.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable digiquarium-caretaker.service

# Start the service now
systemctl start digiquarium-caretaker.service

echo ""
echo "✅ CARETAKER SERVICE INSTALLED AND RUNNING!"
echo ""

# Show status
systemctl status digiquarium-caretaker.service --no-pager

echo ""
echo "=============================================="
echo "  USEFUL COMMANDS"
echo "=============================================="
echo "  View logs:   sudo journalctl -u digiquarium-caretaker -f"
echo "  Status:      sudo systemctl status digiquarium-caretaker"
echo "  Restart:     sudo systemctl restart digiquarium-caretaker"
echo "  Stop:        sudo systemctl stop digiquarium-caretaker"
echo ""
echo "The caretaker will:"
echo "  - Check container health every 15 minutes"
echo "  - Auto-restart crashed containers"
echo "  - Run personality baselines at 3 AM Melbourne time"
echo "  - Generate daily reports at 11 PM"
echo "=============================================="
