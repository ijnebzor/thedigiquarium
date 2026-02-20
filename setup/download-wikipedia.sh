#!/bin/bash
set -e

KIWIX_DIR="${KIWIX_DIR:-./kiwix-data}"
mkdir -p "$KIWIX_DIR"

echo "=== Downloading Wikipedia ZIM Files ==="

# Simple English (required)
echo "Downloading Simple English Wikipedia (~1GB)..."
wget -c -P "$KIWIX_DIR" "https://download.kiwix.org/zim/wikipedia/wikipedia_en_simple_all_maxi_2024-01.zim" || true

echo "✅ Download complete!"
ls -lh "$KIWIX_DIR"/*.zim 2>/dev/null
