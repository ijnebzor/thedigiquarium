# 🚀 DIGIQUARIUM INFRASTRUCTURE MIGRATION - COMPLETE SETUP GUIDE

**Date**: February 22, 2026  
**From**: NUC (i7-7500U)  
**To**: Mac Mini A1347 (i7 4c/8t)  
**Admin Email**: research@digiquarium.org

---

## PHASE 1: ACCOUNT SETUP

Complete all these in ONE session. Have research@digiquarium.org password ready.

### 1.1 Google Workspace (If not already setup)

**Skip if research@digiquarium.org already exists as Google Workspace.**

If you need to create it:
1. Go to: https://workspace.google.com/
2. Start free trial or purchase Starter ($6/user/month)
3. Use domain: digiquarium.org
4. Create admin account: research@digiquarium.org
5. Verify domain ownership via DNS TXT record

### 1.2 Cloudflare Setup

**Step 1: Create Account**
1. Go to: https://dash.cloudflare.com/sign-up
2. Sign up with: research@digiquarium.org
3. Verify email

**Step 2: Add Domain (if not already added)**
1. Click "Add a Site"
2. Enter: digiquarium.org
3. Select FREE plan
4. Cloudflare will scan existing DNS records
5. Update nameservers at your registrar to:
   - Check the exact nameservers Cloudflare provides
   - Usually like: name1.ns.cloudflare.com, name2.ns.cloudflare.com

**Step 3: Configure DNS**
Ensure these records exist:
```
Type    Name    Content              Proxy
A       @       185.199.108.153      Proxied (orange cloud)
A       @       185.199.109.153      Proxied
A       @       185.199.110.153      Proxied  
A       @       185.199.111.153      Proxied
CNAME   www     ijnebzor.github.io   Proxied
```
(These are GitHub Pages IPs - adjust if different)

**Step 4: Enable Analytics**
1. Go to: Analytics & Logs → Web Analytics
2. Click "Add a site"
3. Select digiquarium.org
4. Copy the JS snippet (we'll add to site later)

**Step 5: Create Access Application (for Admin Portal)**
1. Go to: Zero Trust → Access → Applications
2. Click "Add an application"
3. Select "Self-hosted"
4. Configure:
   - Application name: Digiquarium Admin
   - Session duration: 24 hours
   - Application domain: admin.digiquarium.org (we'll create this)
5. Add policy:
   - Policy name: Admin Access
   - Action: Allow
   - Include: Emails ending in @digiquarium.org
   - OR: Specific email: your-personal-email@gmail.com
6. Save

**Step 6: Create Tunnel (Do this AFTER Mac Mini is ready)**
1. Go to: Zero Trust → Networks → Tunnels
2. Click "Create a tunnel"
3. Name it: digiquarium-main
4. Select "Cloudflared" as connector
5. **STOP HERE** - We'll complete on Mac Mini

### 1.3 Google Search Console

1. Go to: https://search.google.com/search-console
2. Click "Add property"
3. Select "Domain" and enter: digiquarium.org
4. Verify via DNS:
   - Copy the TXT record Google provides
   - Add to Cloudflare DNS as TXT record for @
   - Wait 5 mins, click Verify

### 1.4 GitHub Secrets Update

1. Go to: https://github.com/ijnebzor/thedigiquarium/settings/secrets/actions
2. Add/update these secrets (for future CI/CD):
   - `CLOUDFLARE_API_TOKEN`: (create at Cloudflare → Profile → API Tokens)
   - Any other deployment secrets needed

---

## PHASE 1 SECURITY AUDIT

Before proceeding, verify:

### OWASP Top 10 2021 - Account Security

| Control | Check | Status |
|---------|-------|--------|
| A01 Broken Access Control | All accounts have strong unique passwords | [ ] |
| A02 Cryptographic Failures | 2FA enabled on all accounts | [ ] |
| A07 Auth Failures | Recovery emails/phones configured | [ ] |
| A09 Logging Failures | Login notifications enabled | [ ] |

### Account Checklist

- [ ] research@digiquarium.org has 2FA enabled
- [ ] Cloudflare has 2FA enabled
- [ ] GitHub has 2FA enabled
- [ ] All passwords stored in password manager (not browser)
- [ ] Recovery codes saved securely offline
- [ ] No passwords reused across services

---

## PHASE 2: MAC MINI HARDWARE SETUP

### 2.1 Initial macOS Configuration

**On the Mac Mini directly (or via screen sharing):**

```bash
# Check macOS version (should be latest)
sw_vers

# Enable FileVault (disk encryption)
# System Preferences → Security & Privacy → FileVault → Turn On
# SAVE THE RECOVERY KEY SECURELY

# Enable Firewall
# System Preferences → Security & Privacy → Firewall → Turn On

# Configure Energy Saver (prevent sleep)
# System Preferences → Energy Saver
# - Turn display off after: 15 mins
# - Prevent computer from sleeping: ON
# - Start up automatically after power failure: ON

# Enable Remote Login (SSH)
# System Preferences → Sharing → Remote Login → ON
# Only allow access for: Your user account
```

### 2.2 Install Developer Tools

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (follow the instructions it shows)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify
brew --version
```

### 2.3 Install Required Software

```bash
# Essential tools
brew install git python@3.11 curl wget jq htop

# Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/
# Install the .dmg
# Launch Docker Desktop
# Go to Settings → General → Start Docker Desktop when you log in

# Verify Docker
docker --version
docker compose version

# Cloudflare Tunnel daemon
brew install cloudflare/cloudflare/cloudflared

# Ollama (for local LLM inference)
brew install ollama

# Start Ollama service
brew services start ollama

# Pull required models
ollama pull llama3.2:3b
ollama pull stablelm2:1.6b
```

### 2.4 Configure SSH Access from MacBook

**On your MacBook:**

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "macbook-to-macmini"

# Copy public key to Mac Mini
# Replace MAC_MINI_IP with actual IP
ssh-copy-id your-username@MAC_MINI_IP

# Test passwordless login
ssh your-username@MAC_MINI_IP "echo 'SSH working!'"

# Add to SSH config for easy access
cat >> ~/.ssh/config << 'EOF'
Host digiquarium
    HostName MAC_MINI_IP
    User your-username
    IdentityFile ~/.ssh/id_ed25519
EOF

# Now you can just: ssh digiquarium
```

### 2.5 Configure External Storage

**Connect HDDs and format if needed:**

```bash
# List disks
diskutil list

# For each HDD, format as APFS (replace diskX with actual):
# WARNING: This erases the disk!
# diskutil eraseDisk APFS "MEMORY_BANK" diskX
# diskutil eraseDisk APFS "DAEMON_VAULT" diskX

# Create mount points (auto-mounted by macOS but let's be explicit)
# Drives will appear at /Volumes/MEMORY_BANK, /Volumes/DAEMON_VAULT, etc.

# Create directory structure
mkdir -p /Volumes/MEMORY_BANK/thinking_traces
mkdir -p /Volumes/MEMORY_BANK/personality_baselines
mkdir -p /Volumes/MEMORY_BANK/congregations
mkdir -p /Volumes/DAEMON_VAULT/backups
mkdir -p /Volumes/DAEMON_VAULT/state_snapshots
mkdir -p /Volumes/DAEMON_VAULT/logs_archive
```

### 2.6 Clone Repository

```bash
# Create workspace
mkdir -p ~/digiquarium
cd ~

# Clone the repo
git clone https://github.com/ijnebzor/thedigiquarium.git digiquarium

# Configure git
git config --global user.email "research@digiquarium.org"
git config --global user.name "The Digiquarium"
```

### 2.7 Complete Cloudflare Tunnel

**Now that Mac Mini is ready:**

```bash
# Login to Cloudflare (opens browser)
cloudflared tunnel login

# Create tunnel (use the name from Cloudflare dashboard)
cloudflared tunnel create digiquarium-main

# This creates credentials at ~/.cloudflared/

# Create config file
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: digiquarium-main
credentials-file: /Users/YOUR_USERNAME/.cloudflared/TUNNEL_ID.json

ingress:
  # Admin portal
  - hostname: admin.digiquarium.org
    service: http://localhost:8080
  # Future: API endpoint
  - hostname: api.digiquarium.org
    service: http://localhost:8081
  # Catch-all
  - service: http_status:404
EOF

# Route DNS through tunnel
cloudflared tunnel route dns digiquarium-main admin.digiquarium.org

# Install as service (runs on boot)
sudo cloudflared service install

# Start the tunnel
sudo cloudflared service start

# Verify tunnel is running
cloudflared tunnel info digiquarium-main
```

---

## PHASE 2 SECURITY AUDIT

### OWASP Top 10 2021 - Infrastructure

| Control | Check | Status |
|---------|-------|--------|
| A01 Access Control | SSH key-only auth, no password | [ ] |
| A02 Crypto | FileVault enabled, TLS on tunnel | [ ] |
| A05 Misconfiguration | Firewall enabled, no unnecessary services | [ ] |
| A06 Vulnerable Components | All software up to date | [ ] |
| A09 Logging | System logs enabled | [ ] |

### OWASP LLM Top 10 - Infrastructure

| Control | Check | Status |
|---------|-------|--------|
| LLM04 Model DoS | Ollama has resource limits | [ ] |
| LLM05 Supply Chain | Models from ollama.ai only | [ ] |
| LLM08 Excessive Agency | Daemons have scoped permissions | [ ] |

### Infrastructure Checklist

- [ ] Mac Mini FileVault enabled
- [ ] Firewall enabled, only SSH allowed
- [ ] SSH uses key auth only (no password)
- [ ] Docker running
- [ ] Ollama running and responding
- [ ] Cloudflare tunnel active
- [ ] No ports exposed to internet (verified with port scan)
- [ ] External HDDs mounted and writable

**Port Scan Verification:**
```bash
# From outside network (or use online tool)
nmap -Pn YOUR_PUBLIC_IP
# Should show: All ports filtered/closed
# Cloudflare tunnel means NO direct ports needed
```

---

## PHASE 3: MIGRATION & VERIFICATION

### 3.1 Export Data from NUC

**On NUC:**

```bash
# Create migration archive
cd /home/ijneb/digiquarium

# Archive all logs
tar -czvf ~/digiquarium_logs_backup.tar.gz logs/

# Archive daemon states
tar -czvf ~/digiquarium_daemons_backup.tar.gz daemons/*/status.json

# Archive Wikipedia ZIM files list (files too large to transfer, re-download on Mini)
ls -la /path/to/kiwix/data/*.zim > ~/zim_files_list.txt

# Get Ollama models list
ollama list > ~/ollama_models_list.txt
```

**Transfer to Mac Mini:**
```bash
# From MacBook or Mac Mini
scp ijneb@NUC_IP:~/digiquarium_*.tar.gz ~/Downloads/
scp ijneb@NUC_IP:~/*_list.txt ~/Downloads/

# Then to Mac Mini
scp ~/Downloads/digiquarium_*.tar.gz your-user@MAC_MINI_IP:~/
```

### 3.2 Import Data to Mac Mini

**On Mac Mini:**

```bash
cd ~/digiquarium

# Extract logs
tar -xzvf ~/digiquarium_logs_backup.tar.gz

# Move historical logs to MEMORY_BANK
cp -r logs/*/thinking_traces/* /Volumes/MEMORY_BANK/thinking_traces/
cp -r logs/*/personality_baselines/* /Volumes/MEMORY_BANK/personality_baselines/

# Symlink for active use
ln -s /Volumes/MEMORY_BANK/thinking_traces logs/archive
```

### 3.3 Download Wikipedia ZIM Files

```bash
# Create Kiwix data directory
mkdir -p ~/digiquarium/kiwix-data

# Download ZIM files (this takes time)
cd ~/digiquarium/kiwix-data

# Simple English (~1GB)
wget https://download.kiwix.org/zim/wikipedia/wikipedia_en_simple_all_maxi_2024-01.zim

# Add others as needed based on your NUC list
```

### 3.4 Start Containers

```bash
cd ~/digiquarium

# Start infrastructure
docker compose up -d

# Verify all containers
docker ps

# Check logs for errors
docker compose logs --tail=50
```

### 3.5 Verification Tests

```bash
# Test 1: Tank isolation
docker exec tank-01-adam curl -s --connect-timeout 5 https://google.com
# Expected: Connection timeout/failure

# Test 2: Tank can reach Ollama
docker exec tank-01-adam curl -s http://ollama:11434/api/tags
# Expected: JSON response with models

# Test 3: Tank can reach Kiwix
docker exec tank-01-adam curl -s http://kiwix:8080/
# Expected: HTML response

# Test 4: Cloudflare tunnel
curl -I https://admin.digiquarium.org
# Expected: 200 or 302 (redirect to auth)

# Test 5: MCP connection from MacBook
# In Claude Desktop, verify MCP tools work
```

---

## PHASE 3 SECURITY AUDIT

### Full OWASP Top 10 2021 Checklist

| ID | Vulnerability | Control | Verified |
|----|--------------|---------|----------|
| A01 | Broken Access Control | Cloudflare Access, SSH keys | [ ] |
| A02 | Cryptographic Failures | TLS everywhere, FileVault | [ ] |
| A03 | Injection | Input validation in Admin Portal | [ ] |
| A04 | Insecure Design | Threat model documented | [ ] |
| A05 | Security Misconfiguration | No debug modes, hardened | [ ] |
| A06 | Vulnerable Components | All updated, minimal installs | [ ] |
| A07 | Auth Failures | 2FA, key-based auth | [ ] |
| A08 | Data Integrity | Signed commits, verified sources | [ ] |
| A09 | Logging Failures | All events logged, rotated | [ ] |
| A10 | SSRF | No user-controlled URLs | [ ] |

### Full OWASP LLM Top 10 Checklist

| ID | Vulnerability | Control | Verified |
|----|--------------|---------|----------|
| LLM01 | Prompt Injection | THE BOUNCER validation | [ ] |
| LLM02 | Insecure Output | Output sanitization | [ ] |
| LLM03 | Training Data Poisoning | N/A - pretrained | [ ] |
| LLM04 | Model DoS | Rate limiting | [ ] |
| LLM05 | Supply Chain | Trusted sources only | [ ] |
| LLM06 | Sensitive Info | No PII in prompts | [ ] |
| LLM07 | Insecure Plugin | MCP scoped permissions | [ ] |
| LLM08 | Excessive Agency | Daemon boundaries | [ ] |
| LLM09 | Overreliance | Human approval gates | [ ] |
| LLM10 | Model Theft | Local storage only | [ ] |

### Final Verification

- [ ] All 17 tanks generating traces
- [ ] All daemons reporting healthy
- [ ] Remote access working from external network
- [ ] Admin portal actions execute correctly
- [ ] MacBook Claude Desktop MCP connected
- [ ] 24 hours stable operation
- [ ] Documentation fully updated

---

## POST-MIGRATION

### Update Documentation

1. Update site architecture page
2. Update team page with new SLAs
3. Update research paper infrastructure section
4. Update decision tree
5. Add migration to milestones

### NUC Decommission

Only after 7 days stable operation:
1. Export any remaining data
2. Wipe all disks securely
3. Document decommission in THE BRAIN
4. NUC can become backup/test system

---

## EMERGENCY PROCEDURES

### If Tunnel Goes Down
```bash
# Check status
sudo cloudflared service status

# Restart
sudo cloudflared service restart

# Check logs
sudo cloudflared service log
```

### If Containers Fail
```bash
# Restart all
cd ~/digiquarium
docker compose restart

# Nuclear option (preserves data)
docker compose down
docker compose up -d
```

### If Mac Mini Unreachable
1. Check power (UPS status)
2. Check network (router/switch)
3. Physical access if needed
4. NUC as temporary fallback

---

**Document Version**: 1.0  
**Created**: February 22, 2026  
**Author**: THE STRATEGIST  
**Reviewed**: Pending Benji approval  
