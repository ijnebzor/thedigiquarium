#!/bin/bash
# =============================================================================
# DIGIQUARIUM MAC MINI MIGRATION SCRIPT
# Run this on the Mac Mini to set up the new home for the Digiquarium
# =============================================================================

set -e

echo "=============================================="
echo "🌊 DIGIQUARIUM - MAC MINI SETUP"
echo "=============================================="
echo ""

# Configuration
NUC_IP="192.168.50.48"
NUC_USER="benji"
INSTALL_DIR="$HOME/digiquarium"

echo "This script will:"
echo "  1. Install Docker Desktop (if needed)"
echo "  2. Install Ollama"
echo "  3. Create digiquarium directory structure"
echo "  4. Transfer all data from NUC ($NUC_IP)"
echo "  5. Configure and start tanks"
echo ""
read -p "Press Enter to continue..."

# =============================================================================
# STEP 1: Check/Install Dependencies
# =============================================================================

echo ""
echo "=== STEP 1: Checking dependencies ==="

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Please install Docker Desktop manually:"
    echo "   https://www.docker.com/products/docker-desktop/"
    echo ""
    read -p "Press Enter after installing Docker Desktop..."
fi

# Check Docker is running
if ! docker info &> /dev/null; then
    echo "⚠️  Docker is not running. Please start Docker Desktop."
    read -p "Press Enter after Docker is running..."
fi

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    brew install ollama
fi

echo "✅ Dependencies ready"

# =============================================================================
# STEP 2: Create Directory Structure
# =============================================================================

echo ""
echo "=== STEP 2: Creating directory structure ==="

mkdir -p "$INSTALL_DIR"/{kiwix-data,ollama-data,logs,tanks,mcp-server,scripts,docs}
mkdir -p "$INSTALL_DIR"/logs/{tank-01-adam,tank-02-eve,tank-03-cain,tank-04-abel,tank-05-juan,tank-06-juanita,tank-07-klaus,tank-08-genevieve,tank-09-wei,tank-10-mei,tank-11-haruki,tank-12-sakura,tank-13-victor,tank-14-iris,tank-15-observer,tank-16-seeker,tank-17-seth}

echo "✅ Directories created at $INSTALL_DIR"

# =============================================================================
# STEP 3: Transfer Data from NUC
# =============================================================================

echo ""
echo "=== STEP 3: Transferring data from NUC ==="

# Test SSH connection
echo "Testing SSH connection to NUC..."
if ! ssh -o ConnectTimeout=5 "$NUC_USER@$NUC_IP" "echo 'SSH OK'" &> /dev/null; then
    echo "⚠️  Cannot connect to NUC. Please ensure:"
    echo "   1. NUC is powered on"
    echo "   2. SSH key is set up: ssh-copy-id $NUC_USER@$NUC_IP"
    echo ""
    read -p "Press Enter after fixing SSH access..."
fi

echo "Transferring Wikipedia ZIM files (this may take a while)..."
rsync -avz --progress "$NUC_USER@$NUC_IP:/home/ijneb/digiquarium/kiwix-data/*.zim" "$INSTALL_DIR/kiwix-data/"

echo "Transferring tank logs and baselines..."
rsync -avz --progress "$NUC_USER@$NUC_IP:/home/ijneb/digiquarium/logs/" "$INSTALL_DIR/logs/"

echo "Transferring tank code..."
rsync -avz --progress "$NUC_USER@$NUC_IP:/home/ijneb/digiquarium/tanks/" "$INSTALL_DIR/tanks/"

echo "Transferring docker-compose and configs..."
rsync -avz --progress "$NUC_USER@$NUC_IP:/home/ijneb/digiquarium/docker-compose.yml" "$INSTALL_DIR/"
rsync -avz --progress "$NUC_USER@$NUC_IP:/home/ijneb/digiquarium/docs/" "$INSTALL_DIR/docs/"

echo "✅ Data transfer complete"

# =============================================================================
# STEP 4: Pull Ollama Model
# =============================================================================

echo ""
echo "=== STEP 4: Setting up Ollama ==="

# Start Ollama service
ollama serve &> /dev/null &
sleep 3

# Pull the model
echo "Pulling llama3.2:latest model..."
ollama pull llama3.2:latest

echo "✅ Ollama ready"

# =============================================================================
# STEP 5: Update docker-compose for Mac
# =============================================================================

echo ""
echo "=== STEP 5: Configuring for Mac Mini ==="

cd "$INSTALL_DIR"

# Update Ollama URL to localhost (Mac runs Ollama natively)
sed -i.bak 's/192.168.50.94/host.docker.internal/g' docker-compose.yml
rm docker-compose.yml.bak

echo "✅ Configuration updated"

# =============================================================================
# STEP 6: Start Tanks
# =============================================================================

echo ""
echo "=== STEP 6: Starting Digiquarium ==="

docker compose up -d kiwix-simple kiwix-maxi
sleep 5

docker compose up -d tank-01-adam tank-02-eve
docker compose --profile visual up -d
docker compose --profile special up -d
docker compose --profile languages up -d

echo ""
echo "=============================================="
echo "✅ DIGIQUARIUM MIGRATION COMPLETE!"
echo "=============================================="
echo ""
echo "Running tanks:"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "Next steps:"
echo "  1. Monitor tanks: docker compose logs -f"
echo "  2. Check a tank: docker logs tank-01-adam"
echo "  3. Stop all: docker compose down"
echo ""
echo "Data location: $INSTALL_DIR"
echo "Logs: $INSTALL_DIR/logs/"
