#!/bin/bash
# =============================================================================
# DIGIQUARIUM PHASE 2: Download Wikipedia ZIM Files
# =============================================================================

set -e

KIWIX_DIR="/home/ijneb/digiquarium/kiwix-data"
cd "$KIWIX_DIR"

echo "=============================================="
echo "🌊 DIGIQUARIUM - WIKIPEDIA DOWNLOADS"
echo "=============================================="
echo ""
echo "Current disk space: $(df -h / | tail -1 | awk '{print $4}') free"
echo ""

# Kiwix download base URL
BASE="https://download.kiwix.org/zim/wikipedia"

# Function to download with resume support
download_zim() {
    local name=$1
    local filename=$2
    local url="$BASE/$filename"
    
    if [ -f "$filename" ]; then
        echo "   ✅ Already exists: $filename ($(ls -lh $filename | awk '{print $5}'))"
        return 0
    fi
    
    echo "   ⬇️  Downloading $name..."
    echo "      URL: $url"
    wget -c --progress=bar:force:noscroll "$url" -O "$filename.partial" && mv "$filename.partial" "$filename"
    echo "   ✅ Complete: $filename"
}

# Download in order of size (smallest first)

echo ""
echo "📚 [1/5] Chinese Wikipedia (nopic) - ~2.5GB"
download_zim "Chinese" "wikipedia_zh_all_nopic_2024-11.zim"

echo ""
echo "📚 [2/5] Japanese Wikipedia (nopic) - ~3GB"  
download_zim "Japanese" "wikipedia_ja_all_nopic_2024-11.zim"

echo ""
echo "📚 [3/5] Spanish Wikipedia (nopic) - ~5GB"
download_zim "Spanish" "wikipedia_es_all_nopic_2024-11.zim"

echo ""
echo "📚 [4/5] German Wikipedia (nopic) - ~7GB"
download_zim "German" "wikipedia_de_all_nopic_2024-11.zim"

echo ""
echo "📚 [5/5] English Full Wikipedia (maxi) - ~100GB"
echo "      ⚠️  This is the largest file and will take several hours"
download_zim "English Full" "wikipedia_en_all_maxi_2024-10.zim"

echo ""
echo "=============================================="
echo "✅ ALL DOWNLOADS COMPLETE"
echo "=============================================="
echo ""
echo "Files downloaded:"
ls -lh "$KIWIX_DIR"/*.zim
echo ""
echo "Disk space remaining: $(df -h / | tail -1 | awk '{print $4}')"
