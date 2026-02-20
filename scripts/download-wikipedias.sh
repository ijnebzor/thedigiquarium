#!/bin/bash
# Download Wikipedia ZIM files for Digiquarium
# Includes both nopic (text-only) and maxi (full with images) variants

KIWIX_DATA="./kiwix-data"
BASE_URL="https://download.kiwix.org/zim/wikipedia"

echo "================================================"
echo "DIGIQUARIUM Wikipedia Collection Downloader"
echo "================================================"
echo ""

cd ~/digiquarium
mkdir -p "$KIWIX_DATA"

# =============================================================================
# NOPIC VARIANTS (Full articles, no images) - For baseline experiments
# =============================================================================
declare -A WIKIS_NOPIC=(
    # Core requested languages
    ["es-nopic"]="wikipedia_es_all_nopic_2026-01.zim|~3.5GB|Spanish (text-only)"
    ["de-nopic"]="wikipedia_de_all_nopic_2026-01.zim|~7GB|German (text-only)"
    ["zh-nopic"]="wikipedia_zh_all_nopic_2026-01.zim|~3GB|Chinese (text-only)"
    ["ja-nopic"]="wikipedia_ja_all_nopic_2026-01.zim|~4GB|Japanese (text-only)"
    
    # Cultural/philosophical diversity
    ["ru-nopic"]="wikipedia_ru_all_nopic_2026-01.zim|~4.5GB|Russian (text-only)"
    ["ar-nopic"]="wikipedia_ar_all_nopic_2026-01.zim|~1.5GB|Arabic (text-only)"
    ["hi-nopic"]="wikipedia_hi_all_nopic_2026-01.zim|~500MB|Hindi (text-only)"
    ["he-nopic"]="wikipedia_he_all_nopic_2026-01.zim|~800MB|Hebrew (text-only)"
    ["fr-nopic"]="wikipedia_fr_all_nopic_2026-01.zim|~5GB|French (text-only)"
    
    # Full English for comparison with Simple English
    ["en-nopic"]="wikipedia_en_all_nopic_2026-01.zim|~25GB|English Full (text-only)"
)

# =============================================================================
# MAXI VARIANTS (Full articles WITH images) - For visual context experiments
# =============================================================================
declare -A WIKIS_MAXI=(
    # Primary visual experiment - English with images
    ["en-maxi"]="wikipedia_en_all_maxi_2026-01.zim|~100GB|English Full (WITH IMAGES)"
    
    # Visual variants for cross-cultural comparison
    ["es-maxi"]="wikipedia_es_all_maxi_2026-01.zim|~15GB|Spanish (WITH IMAGES)"
    ["de-maxi"]="wikipedia_de_all_maxi_2026-01.zim|~30GB|German (WITH IMAGES)"
    ["zh-maxi"]="wikipedia_zh_all_maxi_2026-01.zim|~12GB|Chinese (WITH IMAGES)"
    ["ja-maxi"]="wikipedia_ja_all_maxi_2026-01.zim|~18GB|Japanese (WITH IMAGES)"
    
    # Simple English with images (smaller, good for testing)
    ["simple-maxi"]="wikipedia_en_simple_all_maxi_2026-02.zim|~2GB|Simple English (WITH IMAGES)"
)

# Combine both for --all
declare -A WIKIS_ALL
for key in "${!WIKIS_NOPIC[@]}"; do WIKIS_ALL["$key"]="${WIKIS_NOPIC[$key]}"; done
for key in "${!WIKIS_MAXI[@]}"; do WIKIS_ALL["$key"]="${WIKIS_MAXI[$key]}"; done

# Download function with resume support
download_wiki() {
    local key=$1
    local file size desc
    
    # Check which array has this key
    if [ -n "${WIKIS_NOPIC[$key]}" ]; then
        IFS='|' read -r file size desc <<< "${WIKIS_NOPIC[$key]}"
    elif [ -n "${WIKIS_MAXI[$key]}" ]; then
        IFS='|' read -r file size desc <<< "${WIKIS_MAXI[$key]}"
    else
        echo "Unknown key: $key"
        return 1
    fi
    
    echo ""
    echo "========================================"
    echo "Downloading: $desc"
    echo "File: $file"
    echo "Size: $size"
    echo "========================================"
    
    if [ -f "$KIWIX_DATA/$file" ]; then
        echo "✓ Already exists, skipping"
        return 0
    fi
    
    wget -c -P "$KIWIX_DATA" "$BASE_URL/$file"
    
    if [ $? -eq 0 ]; then
        echo "✓ Downloaded: $file"
    else
        echo "✗ Failed: $file"
        return 1
    fi
}

show_help() {
    echo "Usage: $0 [OPTIONS] [LANGUAGE_CODES...]"
    echo ""
    echo "Options:"
    echo "  --all-nopic    Download all text-only variants (~55GB)"
    echo "  --all-maxi     Download all image variants (~177GB)"
    echo "  --all          Download everything (~232GB)"
    echo "  --core         Download core 4 languages (es, de, zh, ja) nopic (~18GB)"
    echo "  --core-maxi    Download core 4 languages with images (~75GB)"
    echo "  --list         List all available downloads"
    echo ""
    echo "Language codes (append -nopic or -maxi):"
    echo "  es-nopic, es-maxi    Spanish"
    echo "  de-nopic, de-maxi    German"
    echo "  zh-nopic, zh-maxi    Chinese"
    echo "  ja-nopic, ja-maxi    Japanese"
    echo "  ru-nopic             Russian"
    echo "  ar-nopic             Arabic"
    echo "  hi-nopic             Hindi"
    echo "  he-nopic             Hebrew"
    echo "  fr-nopic             French"
    echo "  en-nopic, en-maxi    English Full"
    echo "  simple-maxi          Simple English with images"
    echo ""
    echo "Examples:"
    echo "  $0 --core                    # Download es, de, zh, ja text-only"
    echo "  $0 simple-maxi               # Simple English with images (2GB)"
    echo "  $0 es-nopic es-maxi          # Spanish both variants"
    echo "  $0 --all-nopic               # All text-only versions"
}

list_all() {
    echo "TEXT-ONLY (nopic) variants:"
    echo "----------------------------"
    for key in "${!WIKIS_NOPIC[@]}"; do
        IFS='|' read -r file size desc <<< "${WIKIS_NOPIC[$key]}"
        status="[ ]"
        [ -f "$KIWIX_DATA/$file" ] && status="[✓]"
        printf "  $status %-15s %8s  %s\n" "$key" "$size" "$desc"
    done | sort
    
    echo ""
    echo "WITH IMAGES (maxi) variants:"
    echo "----------------------------"
    for key in "${!WIKIS_MAXI[@]}"; do
        IFS='|' read -r file size desc <<< "${WIKIS_MAXI[$key]}"
        status="[ ]"
        [ -f "$KIWIX_DATA/$file" ] && status="[✓]"
        printf "  $status %-15s %8s  %s\n" "$key" "$size" "$desc"
    done | sort
    
    echo ""
    echo "Already downloaded:"
    ls -lh "$KIWIX_DATA"/*.zim 2>/dev/null || echo "  (none yet)"
}

# Parse arguments
case "$1" in
    --help|-h)
        show_help
        ;;
    --list)
        list_all
        ;;
    --all-nopic)
        echo "Downloading ALL text-only variants (~55GB)..."
        for key in "${!WIKIS_NOPIC[@]}"; do
            download_wiki "$key"
        done
        ;;
    --all-maxi)
        echo "Downloading ALL image variants (~177GB)..."
        for key in "${!WIKIS_MAXI[@]}"; do
            download_wiki "$key"
        done
        ;;
    --all)
        echo "Downloading EVERYTHING (~232GB)..."
        for key in "${!WIKIS_ALL[@]}"; do
            download_wiki "$key"
        done
        ;;
    --core)
        echo "Downloading core 4 languages (text-only, ~18GB)..."
        for lang in es-nopic de-nopic zh-nopic ja-nopic; do
            download_wiki "$lang"
        done
        ;;
    --core-maxi)
        echo "Downloading core 4 languages (with images, ~75GB)..."
        for lang in es-maxi de-maxi zh-maxi ja-maxi; do
            download_wiki "$lang"
        done
        ;;
    "")
        show_help
        ;;
    *)
        # Download specific codes
        for code in "$@"; do
            download_wiki "$code"
        done
        ;;
esac

echo ""
echo "Done! Current collection:"
ls -lh "$KIWIX_DATA"/*.zim 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
