#!/bin/bash
# Archive tank logs
TANK=${1:-adam}
LABEL=${2:-$(date +%Y%m%d_%H%M%S)}

ARCHIVE_DIR="/home/ijneb/digiquarium/archives/${TANK}-${LABEL}"
mkdir -p "$ARCHIVE_DIR"

# Copy logs
cp -r /home/ijneb/digiquarium/logs/tank-01-${TANK}/* "$ARCHIVE_DIR/" 2>/dev/null || true

# Get container logs
docker logs tank-01-${TANK} > "$ARCHIVE_DIR/container_log.txt" 2>&1

# Create info file
echo "Archived: $(date)" > "$ARCHIVE_DIR/ARCHIVE_INFO.txt"
echo "Tank: $TANK" >> "$ARCHIVE_DIR/ARCHIVE_INFO.txt"
echo "Label: $LABEL" >> "$ARCHIVE_DIR/ARCHIVE_INFO.txt"

echo "✅ Archived to $ARCHIVE_DIR"
