#!/bin/bash
set -e

KIWIX_DIR="/home/ijneb/digiquarium/kiwix-data"
cd "$KIWIX_DIR"

echo "=============================================="
echo "🌊 DIGIQUARIUM - LANGUAGE WIKIPEDIA DOWNLOADS"
echo "=============================================="
echo "Started: $(date)"
echo "Disk space: $(df -h / | tail -1 | awk '{print $4}') free"
echo ""

BASE="https://download.kiwix.org/zim/wikipedia"

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
    if wget -c --show-progress "$url" -O "$filename.partial"; then
        mv "$filename.partial" "$filename"
        echo "   ✅ Complete: $filename ($(ls -lh $filename | awk '{print $5}'))"
    else
        echo "   ❌ Failed: $filename"
        rm -f "$filename.partial"
        return 1
    fi
}

echo "📚 [1/4] Spanish Wikipedia"
download_zim "Spanish" "wikipedia_es_all_nopic_2025-10.zim"

echo ""
echo "📚 [2/4] German Wikipedia"
download_zim "German" "wikipedia_de_all_nopic_2026-01.zim"

echo ""
echo "📚 [3/4] Chinese Wikipedia"
download_zim "Chinese" "wikipedia_zh_all_nopic_2025-09.zim"

echo ""
echo "📚 [4/4] Japanese Wikipedia"
download_zim "Japanese" "wikipedia_ja_all_nopic_2025-10.zim"

echo ""
echo "=============================================="
echo "✅ DOWNLOADS COMPLETE - $(date)"
echo "=============================================="
ls -lh "$KIWIX_DIR"/*.zim
