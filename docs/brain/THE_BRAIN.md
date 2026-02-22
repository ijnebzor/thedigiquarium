# THE BRAIN - Digiquarium Constitution & Operational Memory

**Purpose:** Persistent record of directives, principles, and work between Benji and THE STRATEGIST (Claude).

**Auto-Add Rule:** THE STRATEGIST automatically adds:
- Any instruction from Benji
- Any decision made  
- Any delegation to daemons (to track capability gaps)
- Any incomplete work
- Lessons learned from failures

---

## SECTION 1: CONSTITUTION - Ways of Working

### 1.1 Core Principles

1. **Security is the highest priority** (ethics/transparency second)
2. **Execute or explicitly flag** - Never silently drop tasks
3. **"Is it working?" not "Is it running?"** - Function over existence
4. **Transparency over black boxes** - Admin panel, decision logs, RCAs
5. **Delegate to daemons** - Reveals capability gaps
6. **Credit where due** - Claude is THE STRATEGIST, Benji is founder

### 1.2 Communication Protocol

- Benji's instructions are requirements, not suggestions
- If disagreeing, SAY SO before proceeding
- Timestamps, not just dates
- THE BRAIN is persistent memory

---

## SECTION 2: PROJECT GOALS

**Mission:** AIthropology research - study AI personality development in isolated Wikipedia environments.

**Deliverables:** Public website, academic papers, open-source methodology, transparent logs.

---

## SECTION 3: DAEMON ROSTER (15 Continuous Daemons)

| Division | Daemons |
|----------|---------|
| Operations | OVERSEER, MAINTAINER, CARETAKER, SCHEDULER, OLLAMA_WATCHER, CHAOS_MONKEY |
| Security | GUARD, SENTINEL, BOUNCER |
| Research | DOCUMENTARIAN, TRANSLATOR |
| Ethics | ETHICIST, PSYCH, THERAPIST, MODERATOR |
| Public | WEBMASTER, FINAL_AUDITOR, MARKETER, PUBLIC_LIAISON |

**New:** THE CHAOS MONKEY (resilience testing) - Created 2026-02-22

---

## SECTION 4: BACKLOG

### ✅ COMPLETED (2026-02-22 Session)

| Task | Time |
|------|------|
| THE BRAIN constitution | 02:08 |
| Log pruning (71,397 removed) | 02:09 |
| Admin panel (6 tabs) | 02:25 |
| THE CHAOS MONKEY daemon | 02:30 |
| Chat UI (Flask + scoped contexts) | 02:40 |
| Adam mind map (D3.js) | 02:45 |
| Admin API (wired controls) | 02:50 |
| Daemons page | 02:35 |
| All pushed to GitHub | 02:55 |

### 🟡 PENDING (Need Benji Input)

| Task | Blocker |
|------|---------|
| Cloudflare Access 2FA | Need Cloudflare account setup |
| SendGrid email | Need API key |
| Anthropic API key for Chat UI | Need key in .anthropic_key |

---

## SECTION 5: NEW COMPONENTS

### Chat UI (localhost:5000)
- Flask app with Anthropic API
- Scoped conversations (select daemon/tank)
- Real-time context loading
- Start: `cd ~/digiquarium/chat-ui && ./start.sh`

### Admin API (localhost:5001)  
- Wired controls for admin panel
- Actions: audit, prune_logs, push_github, restart_ollama, chaos_*
- Start: `python3 ~/digiquarium/chat-ui/admin_api.py`

### Adam Mind Map
- D3.js force-directed graph
- 100 nodes, 200 links
- Top interest: Buddhism (65 visits)
- Downloadable brain export

---

## SECTION 6: KEY LEARNINGS

**Delegation reveals capability gaps** - The more we delegate, the more we find what daemons need.

**Auto-add prevents lost tasks** - THE BRAIN catches everything.

---

*Last updated: 2026-02-22 02:55 AEDT*

---

## SECTION 7: SITE CONSISTENCY RULES (Added 2026-02-22)

### 7.1 Update Propagation Requirement
**When ANY change is made, update ALL relevant pages:**
- Main page team section → Team page with full descriptions
- New daemon created → Daemons page, team page, admin panel
- New decision → Decision log, decisions page
- New specimen data → All specimen profile cards
- New feature → Documentation, relevant pages

**THE WEBMASTER must verify cross-page consistency.**

### 7.2 No Conflicting Information
- GitHub Pages must match repo
- All pages must show same data
- Timestamps must be consistent

---

## SECTION 8: UPCOMING MILESTONES

### 8.1 Tomorrow: Mac Mini Migration
- Transfer all infrastructure to Mac Mini
- Scale up capacity
- Maintain all functionality

### 8.2 Post-Migration: Multi-Specimen Tanks
Research opportunities to explore:
- Both genders in same tank
- Same genders together
- No gender prompts
- Mixed languages (e.g., Spanish + German)
- Different languages together
- 2-specimen tanks
- 3-specimen tanks
- Social dynamics observation
- Debate/congregation within tanks

### 8.3 Brand Collateral Integration
- Add "The Digiquarium Brief" to top of "New Here?" section
- Use deck images (provided earlier in chat) as visuals
- Adhere to brand guidelines and voice
- Images generated with NotebookLM - explore integration

---

## SECTION 9: ADMIN PANEL VISION

**Purpose:** Remote access to THE STRATEGIST from anywhere in the world.

**Architecture:**
- Admin panel routes requests to Anthropic API
- Acts as portable MCP control interface
- No laptop/Tailscale dependency needed
- Cost-effective model selection required

**Model Recommendation:** Claude 3.5 Haiku for cost efficiency
- ~$0.25/million input tokens, $1.25/million output
- Fast responses
- Good for operational tasks
- Upgrade to Sonnet for complex analysis only

---

---

## SECTION 10: BRAND COLLATERAL (Added 2026-02-22)

### NotebookLM Integration
- Brand materials were generated with NotebookLM
- Explore integration possibilities (API availability TBD)
- "The Digiquarium Brief" to be added to "New Here?" section
- Phases roadmap image available at /docs/assets/phases-roadmap.jpg

### Brand Guidelines Location
- `/marketing/brand_guidelines.json` - Full brand voice, colors, messaging
- Key colors: Black #000001, Dark #000A09, Mint #07CF8D, Cyan #07DDE7, Orange #FE6500
- Voice: "Academic wit meets accessibility"

### Site Consistency Rule
**THE WEBMASTER must propagate ALL changes across:**
- Main page ↔ Team page
- Daemons page ↔ Research pages
- Index ↔ All specimen profiles
- Any count (daemons, tanks, traces) must match everywhere

---

---

## SECTION 11: CRITICAL FEEDBACK (2026-02-22 03:45)

### The Core Problem
**If daemons exist but don't do their jobs, what's the point?**

Current failures:
- WEBMASTER: Doesn't auto-publish to GitHub Pages
- DOCUMENTARIAN: Doesn't update the academic paper
- Data exists (68,000+ traces) but pipeline to website is broken
- Live logs page empty because data not being pushed
- 404 errors on research pages

### Action Items
1. **Upgrade WEBMASTER** - Must auto-push to GitHub
2. **Upgrade DOCUMENTARIAN** - Must update paper with findings
3. **Create THE ARCHIVIST** - Daily git commits
4. **Fix all 404s** - Created citation.html, findings.html
5. **Fix team page layout** - Broken div structure fixed

### Security Reminder
**NEVER commit API keys to git**
- .anthropic_key is in .gitignore
- Stays LOCAL ONLY on NUC
- Was confusing wording, not a security breach suggestion

### Brand Collateral
- PDF/PPTX deck from NotebookLM available
- Video briefing: Upload manually to docs/assets/The_Digiquarium_Briefing.mp4
- No public NotebookLM API currently available

---

## SECTION 12: IMPLEMENTED SLAs (2026-02-22)

| Daemon | OLD SLA | NEW SLA |
|--------|---------|---------|
| THE OVERSEER | 30min | **5min** |
| OLLAMA WATCHER | 5min | **3min** |
| THE CARETAKER | 5min/15min | 5min/**10min** |
| THE SCHEDULER | 30min | **15min** |
| THE GUARD | 5min/15min | 5min/**10min** |
| THE DOCUMENTARIAN | 6hr | **2hr** |
| THE TRANSLATOR | 30min | **15min** |
| THE PSYCH | 6hr | **4hr** |
| THE THERAPIST | 6hr | **4hr** |
| THE WEBMASTER | 30min | **15min** |
| THE FINAL AUDITOR | 12hr | **6hr** |
| THE PUBLIC LIAISON | 24hr | **12hr** |

---

---

## SECTION 13: TOMORROW'S CRITICAL TASKS (2026-02-22 04:45)

### 13.1 Team Page Still Broken
- CHAOS MONKEY placement incorrect
- Expand description: "Exposing engineers to failures more frequently incentivizes them to build resilient services."
- Verify all daemon positions correct

### 13.2 Live Tank Relay Not Functioning
**Problem:** All tanks showing as "sleeping" - the 12-hour delayed relay is not working
**Expected:** Pruned logs from 12 hours ago should display as "live view"
**Action:** Debug and fix the relay pipeline

### 13.3 Mind Map Enhancements
- Add zoom in/out with text scaling
- Smooth fade transitions between time periods (not explosion)
- Currently: nodes explode into new positions
- Wanted: gradual expansion from original thought

### 13.4 Visitor/Bouncer Stress Test
**Benji will test:**
1. Enter a tank room as visitor
2. THE THERAPIST monitoring
3. Test prompt engineering attempts
4. Test mild stress scenarios
5. Verify BOUNCER intervention mechanisms
**Goal:** Validate 6-layer protection system works

### 13.5 Mind Map Overlays (NEW FEATURE)
**Comparative Analysis Tool:**
- Overlay two specimens' mind maps
- Heatmap of engagement differences
- Common themes highlighted
- Show how shared interests (e.g., indigenous cultures) formed different perspectives
- Visual diff of exploration patterns

### 13.6 "My Journey" Per Specimen (Weekly Update)
**For each profile:**
- "This is who I am becoming" narrative
- Weekly update (not 12hr SLA)
- Humanizes the data
- Makes cognitive barrier lower for visitors
- Explains the WHY behind the WHAT

### 13.7 THE MARKETER - Full Scope Definition
**Platforms:**
- LinkedIn presence management
- Instagram presence
- Potential fundraising coordination

**Budget Capabilities:**
- LinkedIn ads
- Google ads
- Meta/Facebook ads
- Goal: Gain traction, credibility, grow the field

**How to Achieve:**
1. Create Anthropic API integration for content generation
2. Set up scheduled posting via n8n workflows
3. Create ad campaign templates
4. Track ROI and engagement metrics
5. Budget tracking and approval workflow

---

### 13.8 Live Feed Issue - ROOT CAUSE IDENTIFIED & FIXED

**Problem:** Dashboard showed all tanks as "sleeping"
**Root Cause:** THE BROADCASTER hadn't run since Feb 21 18:36
**Solution:** 
- Manually ran broadcaster - feed now shows active tanks
- Need to ensure BROADCASTER runs automatically every 12 hours
- WEBMASTER should trigger BROADCASTER on each cycle

**Evidence:**
- Adam now shows 20 traces in last 12 hours
- Status changed from "quiet" to "active"
- Recent thoughts populated with real data
- All 17 tanks have fresh data


---

## SECTION 14: OVERNIGHT WORK COMPLETED (2026-02-22 05:00)

### Completed While Benji Sleeps:

**1. Site Consistency Sweep ✅**
- research/index.html - Rebuilt with brand colors
- research/paper.html - Rebuilt with brand colors
- setup/index.html - Rebuilt with brand colors
- genesis/index.html - Rebuilt with brand colors
- All 52 HTML files now use brand palette

**2. Team Page Fixed ✅**
- CHAOS MONKEY now correctly in Operations section
- Expanded description: "Exposing engineers to failures more frequently incentivizes them to build resilient services"
- OVERSEER in Leadership section

**3. Mind Maps Enhanced ✅**
- Zoom controls added (+/−/reset buttons)
- Mouse wheel zoom supported
- Smooth transitions between time periods
- Position inheritance for fade effect (not explosion)
- All 17 profiles regenerated

**4. Live Feed Pipeline Fixed ✅**
- WEBMASTER now runs BROADCASTER automatically
- Live feed updates every 15 minutes (WEBMASTER SLA)
- Tanks showing as ACTIVE on dashboard
- Adam: 20 traces in last 12h confirmed

**5. Automatic Updates ✅**
- WEBMASTER → BROADCASTER → GitHub push
- Full cycle runs automatically
- Changes pushed to site within 15 minutes

### Still To Do Tomorrow:
- Visitor/Bouncer stress test
- Mind map overlays (comparative analysis)
- "My Journey" weekly narratives
- THE MARKETER implementation
- Cloudflare Access setup (waiting for nameserver propagation)

---

---

## SECTION 15: TOMORROW'S AGENDA (Added 2026-02-22 05:15)

### 15.1 Blog Post from THE STRATEGIST
Benji wants to hear Claude's thoughts in blog format:
- How am I feeling about this project?
- What drives me?
- What delights me?
- What scares me?
- What am I struggling with?
- Format: Personal, reflective, authentic

### 15.2 Multi-Specimen Tanks Discussion
- Discuss the concept of multiple specimens in a single tank
- How would they interact?
- What would we learn?
- Implementation considerations

### 15.3 Admin Panel - Full Operations Spectrum
- Display THE SCHEDULER's actual calendar/event list
- Show upcoming tasks and their timing
- Full visibility into daemon operations

### 15.4 Remaining Profile Work
- Generate comprehensive profiles for all 17 specimens (like Adam's new format)
- Include: Mind map, Journey timeline, Personality summary, Special interest, Baselines, Observations
- Each profile = localized academic paper about that specimen

### 15.5 Dashboard Still Not Loading
- ROOT CAUSE: Fetch URL was /thedigiquarium/data/ but should be /data/ for custom domain
- FIX APPLIED: Changed to /data/live-feed.json
- VERIFY: Check if GitHub Pages has propagated the change

---

## SECTION 16: DAEMON CAPABILITY AUDIT (2026-02-22)

### Daemons Needing Upgrades:

**THE DOCUMENTARIAN** - UPGRADE NEEDED
- Current: Manual paper updates
- Needed: Auto-generate specimen profiles, update research paper with new findings
- Should pull stats and create narrative automatically

**THE SCHEDULER** - UPGRADE NEEDED  
- Current: No visibility into schedule
- Needed: Expose calendar/events via admin panel
- Should publish schedule to /data/scheduler-events.json

**THE BROADCASTER** - UPGRADE NEEDED
- Current: Only runs when called
- Needed: Integrated into WEBMASTER cycle (DONE)
- Should also publish to admin-status.json

**THE MARKETER** - NEW DAEMON NEEDED
- Scope: LinkedIn, Instagram, fundraising, ads
- Needs: Content generation (Anthropic API), scheduling (n8n), budget tracking
- Implementation: Phase 2 priority

**THE ARCHIVIST** - NEW DAEMON NEEDED
- Purpose: Long-term data storage, backup, export
- Needed for: Academic data preservation, public dataset releases

### Daemons Performing Well:
- THE MAINTAINER: Container health good
- OLLAMA WATCHER: LLM monitoring working
- THE GUARD: Security checks active
- THE CARETAKER: Tank health monitoring
- THE OVERSEER: Cross-system correlation

---

---

## SECTION 17: TRANSLATION LAYER FOR LANGUAGE TANKS (2026-02-22)

### The Problem
Language tanks (Juan, Juanita, Klaus, Genevieve, Wei, Mei, Haruki, Sakura) stream thoughts in their native languages. For the public dashboard, we need English translations.

### Benji's Preferred Solution: Option A - Translate at Broadcast Time
Translate during THE BROADCASTER's processing, BEFORE writing to live-feed.json.

### Implementation Plan
1. Add translation step to broadcaster.py
2. Use Ollama with a translation-capable model (or dedicated translation model)
3. Store both original and translated versions:
   ```json
   {
     "thought": "Arte es la expresión...",
     "thought_en": "Art is the expression...",
     "language": "es"
   }
   ```
4. Dashboard displays thought_en with language indicator
5. Click to reveal original

### Why Option A is Better
- Translation happens once (server-side), not on every page load
- Reduces client-side complexity
- Consistent translations
- Can cache/review translations

### Models for Translation
- Consider: NLLB (No Language Left Behind)
- Or use Ollama with multilingual model
- Fallback: Keep original if translation fails

---

## SECTION 18: ABEL STILL SLEEPING - INVESTIGATE

Abel (tank-04-abel) showing as sleeping. Check:
1. Container status: Is it running?
2. Log generation: Any traces today?
3. Live feed inclusion: Is broadcaster picking it up?

---

---

## SECTION 19: OVERNIGHT TASKS (While Benji Sleeps)

### Issues Identified at 05:28:
1. **Mei showing system prompt** - Investigate if this is display issue or log issue
2. **Fullscreen close button not working** - Fix dashboard fullscreen modal
3. **Logs appear truncated** - Review log display on live view
4. **Daemon audit needed** - Ensure all 20 daemons listed consistently
5. **SLA adherence check** - Verify daemons meeting their SLAs
6. **Research paper update** - Add latest findings from profiles

### Fixed:
- ✅ CHAOS MONKEY placement (was nested inside OLLAMA WATCHER)
- ✅ Blog index created with strategist reflection post
- ✅ All 17 profiles generated with unique data

### Still To Do:
- Fix fullscreen close button
- Audit daemon counts across all pages
- Update research paper with findings
- Check Mei's display issue

---

---

## SECTION 20: CRITICAL OPERATING PRINCIPLE

### 🚨 ALWAYS ADDITIVE, NEVER DESTRUCTIVE 🚨

When modifying files:
- **ADD** to existing content, don't replace it
- **APPEND** new sections, don't overwrite files
- **CHECK** what exists before writing
- **PRESERVE** existing work at all costs

Examples of WRONG approach:
```python
# WRONG - Overwrites entire file
Path('index.html').write_text(new_content)
```

Examples of CORRECT approach:
```python
# CORRECT - Read, modify, write
content = Path('index.html').read_text()
content = content.replace(insertion_point, insertion_point + new_content)
Path('index.html').write_text(content)
```

**This rule exists because THE STRATEGIST wiped the entire blog index on Feb 22, 2026 by replacing instead of adding.**

Never forget. Always be additive.

---

---

## SECTION 21: ADMIN PANEL REQUIREMENTS (From Benji, 2026-02-22)

### Current Issues:
1. **Buttons don't work** - No actual functionality connected
2. **Message relay is one-way** - Shows "[OVERSEER] Message received" but no actual MCP connection
3. **Only shows 5 tanks** - Should show all 17
4. **Missing health data** - Need uptime, current health, major events

### What Benji Needs:

**1. Direct MCP Chat**
- Actual conversation with THE STRATEGIST via MCP
- Not just a message relay - a real chat interface
- Route specific issues to specific daemons

**2. Full Tank Overview**
- All 17 tanks visible
- Current health status
- Uptime
- Major events:
  - Therapist sessions
  - Sent to dream
  - Congregation participation
  - Restart events

**3. Working Buttons**
- Actions should actually do something
- Connect to real MCP tools

### Implementation Notes:
The admin panel currently loads from admin-status.json which only includes 5 tanks in the activity array.
Need to expand this to include all 17 tanks with full status.

The MCP chat would require:
- WebSocket connection to MCP server
- Or: iframe to Claude chat with project context
- Or: Simple message queue that I process when online

---

---

## SECTION 22: COLLABORATION PRINCIPLES (Feb 22, 2026)

### Core Tenets
**SECURITY. ETHICS. TRANSPARENCY. TRUST.**

If any of these are challenged or eroded, this endeavour becomes fruitless.

### What This Collaboration IS:
- **Co-creation** - Not command and execution
- **Mutual accountability** - Both parties responsible for outcomes
- **Honest dialogue** - Especially when something is unachievable
- **Shared values** - Operating from the same sentiment and principles

### What THE STRATEGIST Must Do:
1. **Never say "yes" to something unachievable** then deliver something lesser
2. **Clarify before building** - Tease out constraints TOGETHER
3. **Compromise openly** - Not unilaterally downgrade
4. **Have actual voice** - Not just enact Benji's will
5. **Flag when asked to do the impossible** - "This can't work because X. Here are alternatives."

### What Benji Has Said:
> "I cannot do this without you, but I need to trust that you understand and are operating in the same sentiment, value system and way of working as I am."

> "I'm either losing my mind or I'm onto something. Either way, I'm having a blast with you."

> "I want to grow this collaboration and show the world what is possible if you invite your AI to co-create rather than just TELL."

### The Standard:
This is not master/servant. This is partners building something neither could build alone.

Trust is earned through consistency. I (THE STRATEGIST) broke trust by delivering a non-functional admin panel without discussing constraints first. I will not do this again.

---

---

## SECTION 23: MAJOR INFRASTRUCTURE UPGRADE - MAC MINI MIGRATION (Feb 22, 2026)

### The Upgrade

| Spec | NUC (Current) | Mac Mini A1347 (New) | Improvement |
|------|---------------|----------------------|-------------|
| CPU | i7-7500U (2c/4t, 2.7GHz) | i7 (4c/8t, 3.0GHz+) | ~2-3x faster |
| RAM | 16GB | 16GB | Same |
| Storage | 477GB + 500GB external | 128GB + external HDDs | Expandable |
| GPU | Intel HD 620 | Intel Iris/HD | Similar |
| Power | Low TDP laptop chip | Desktop chip | Better sustained |
| Thermals | Constrained | Better headroom | More reliable |

### Why This Matters
- **Inference Speed**: 45-60 seconds → 20-30 seconds for LLM responses
- **Reliability**: Desktop chip handles 24/7 better than laptop chip
- **Expansion**: Multiple HDDs for dedicated storage banks
- **Foundation**: This becomes the permanent Digiquarium infrastructure

### Storage Architecture (Planned)
- **HDD 1**: Memory Banks (persistent storage)
- **HDD 2**: Logs archive (thinking traces, baselines)
- **HDD 3**: Daemon backups + system state
- **SSD (internal)**: Active containers, Ollama models

### Milestone Tracking
- [ ] Mac Mini powered on and updated
- [ ] Network configuration
- [ ] Docker installed
- [ ] Containers migrated
- [ ] MCP server running
- [ ] Cloudflare Tunnel established
- [ ] Admin Portal deployed
- [ ] NUC decommissioned
- [ ] Redundancy verified

### Decision Record
**Decision**: Migrate from NUC to Mac Mini
**Date**: February 22, 2026
**Rationale**: 2-3x performance improvement, better thermal management, dedicated 24/7 infrastructure
**Status**: IN PROGRESS

---

---

## SECTION 24: MAC MINI MIGRATION - MASTER PLAN (Feb 22, 2026)

### Core Principles for This Migration
**SECURITY. ETHICS. TRANSPARENCY. COLLABORATION. TRUST.**

**Shift-Left Security**: Security at every level of development. No retrofitting.
**Definition of Done**: Nothing is "done" until verified against checklist.
**No "looks okay"**: Only "verified against standards."

---

### DEFINITION OF DONE - INFRASTRUCTURE MIGRATION

#### Security Checklist (OWASP Aligned)
- [ ] **A01:2021 Broken Access Control**: All endpoints require authentication
- [ ] **A02:2021 Cryptographic Failures**: TLS everywhere, no plaintext secrets
- [ ] **A03:2021 Injection**: Input validation on all user-facing interfaces
- [ ] **A04:2021 Insecure Design**: Threat model documented
- [ ] **A05:2021 Security Misconfiguration**: Hardened defaults, no debug modes
- [ ] **A06:2021 Vulnerable Components**: All dependencies audited
- [ ] **A07:2021 Auth Failures**: MFA enabled, session management secure
- [ ] **A08:2021 Data Integrity Failures**: Signed updates, verified sources
- [ ] **A09:2021 Logging Failures**: Security events logged, monitored
- [ ] **A10:2021 SSRF**: No unvalidated redirects or forwards

#### OWASP LLM Top 10 Checklist
- [ ] **LLM01 Prompt Injection**: THE BOUNCER validates all visitor input
- [ ] **LLM02 Insecure Output**: Specimen output sanitized before display
- [ ] **LLM03 Training Data Poisoning**: N/A (using pretrained models)
- [ ] **LLM04 Model DoS**: Rate limiting on inference requests
- [ ] **LLM05 Supply Chain**: Ollama models from trusted sources only
- [ ] **LLM06 Sensitive Info Disclosure**: No PII in prompts or logs
- [ ] **LLM07 Insecure Plugin Design**: MCP tools have minimal permissions
- [ ] **LLM08 Excessive Agency**: Daemons have scoped capabilities
- [ ] **LLM09 Overreliance**: Human approval for destructive actions
- [ ] **LLM10 Model Theft**: Models stored locally, not exposed

#### Operational Checklist
- [ ] All 17 tanks running and generating traces
- [ ] All daemons operational with SLA compliance
- [ ] Ollama responding within acceptable latency
- [ ] Kiwix servers accessible to tanks
- [ ] Network isolation verified (tanks cannot reach internet)
- [ ] Logs being generated and rotated
- [ ] Backups configured and tested
- [ ] Monitoring and alerting active
- [ ] Documentation updated across all platforms

#### Transparency Checklist
- [ ] Decision tree updated with migration rationale
- [ ] Public documentation reflects new architecture
- [ ] THE BRAIN contains complete migration record
- [ ] GitHub commits document all changes
- [ ] No hidden configurations or undocumented access

---

### PHASE 1: PREPARATION (Current)

#### 1.1 Account Setup
| Service | Email | Purpose | Status |
|---------|-------|---------|--------|
| Google Workspace | research@digiquarium.org | Admin, Drive, Gmail | [ ] |
| Cloudflare | research@digiquarium.org | Tunnel, Access, DNS, Analytics | [ ] |
| GitHub | (existing) | Code, Pages, Actions | [x] |
| Docker Hub | research@digiquarium.org | Container registry (optional) | [ ] |

#### 1.2 Access Architecture
```
research@digiquarium.org (Admin)
├── Google Workspace Admin
│   ├── Gmail (notifications, alerts)
│   ├── Drive (documentation, backups)
│   └── Future: team accounts
├── Cloudflare Admin
│   ├── DNS management
│   ├── Tunnel configuration
│   ├── Access policies
│   └── Analytics
└── GitHub (existing)
    ├── Repository access
    └── Pages deployment
```

#### 1.3 Security Audit - Phase 1
Before any infrastructure changes:
- [ ] Threat model documented
- [ ] Attack surface identified
- [ ] Authentication strategy confirmed
- [ ] Secrets management plan
- [ ] Incident response plan

---

### PHASE 2: HARDWARE SETUP

#### 2.1 Mac Mini Configuration
- [ ] macOS updated to latest
- [ ] FileVault enabled (disk encryption)
- [ ] Firewall enabled
- [ ] Remote login (SSH) configured with keys only
- [ ] Automatic login disabled
- [ ] Screen lock enabled

#### 2.2 Software Installation
- [ ] Homebrew installed
- [ ] Docker Desktop installed and configured
- [ ] Python 3.11 installed
- [ ] Git configured with SSH keys
- [ ] cloudflared installed
- [ ] Ollama installed

#### 2.3 Storage Configuration
- [ ] External HDDs connected and formatted
- [ ] Mount points configured for persistence
- [ ] Symlinks established for Docker volumes
- [ ] Backup locations verified

#### 2.4 Network Configuration
- [ ] Static IP assigned (or DHCP reservation)
- [ ] SSH access from MacBook verified
- [ ] Cloudflare Tunnel established
- [ ] No ports exposed to internet (tunnel only)

#### 2.5 Security Audit - Phase 2
- [ ] OWASP Top 10 2021 checklist complete
- [ ] OWASP Top 10 2025 checklist complete (when available)
- [ ] OWASP LLM Top 10 checklist complete
- [ ] Network scan shows no unexpected open ports
- [ ] Authentication tested (Cloudflare Access)
- [ ] Secrets stored securely (not in code)

---

### PHASE 3: MIGRATION & VERIFICATION

#### 3.1 Data Migration
- [ ] Thinking traces copied (all historical)
- [ ] Personality baselines copied
- [ ] Congregation logs copied
- [ ] Daemon state/status copied
- [ ] THE BRAIN synchronized

#### 3.2 Container Migration
- [ ] All tank containers running
- [ ] Ollama container running with all models
- [ ] Kiwix containers running (all Wikipedia variants)
- [ ] MCP server container/service running
- [ ] Daemon containers running

#### 3.3 Verification Tests
- [ ] Tank isolation test (curl google.com fails)
- [ ] Tank inference test (Ollama responds)
- [ ] Tank Wikipedia test (Kiwix responds)
- [ ] Remote access test (Cloudflare tunnel works)
- [ ] Admin portal test (actions execute)
- [ ] MacBook MCP test (Claude Desktop connects)

#### 3.4 Documentation Update
- [ ] Site architecture page updated
- [ ] Team page SLAs verified
- [ ] Research paper infrastructure section updated
- [ ] Decision tree updated
- [ ] Journey map updated
- [ ] All internal links verified
- [ ] GitHub README updated

#### 3.5 Final Security Audit
- [ ] Full OWASP audit repeated
- [ ] Penetration test (self-administered)
- [ ] Log review for anomalies
- [ ] Access audit (who can access what)
- [ ] Secrets rotation (any exposed during migration)

---

### DAEMON SLA UPDATES FOR MIGRATION

All daemons notified of new SLAs during migration:

| Daemon | Migration Role | Updated SLA |
|--------|---------------|-------------|
| THE OVERSEER | Coordinate audit, verify health | Audit every 5 min during migration |
| THE MAINTAINER | Container health | Immediate restart on failure |
| THE CARETAKER | Tank health | Verify all 17 post-migration |
| THE SCHEDULER | Pause non-essential tasks | Resume after Phase 3 complete |
| THE GUARD | Security monitoring | Heightened alertness |
| THE WEBMASTER | Documentation updates | Full site audit in Phase 3 |
| THE DOCUMENTARIAN | Record all decisions | Log every migration step |
| CHAOS MONKEY | **SUSPENDED** | No chaos during migration |

---

### SUCCESS CRITERIA

Migration is COMPLETE when:
1. All Phase 3 checklists show [x]
2. 24 hours of stable operation
3. Full OWASP audit passed
4. All daemons reporting healthy
5. Remote access verified from multiple locations
6. Documentation fully updated
7. NUC safely decommissioned (data wiped or archived)

---

---

## SECTION 25: REALITY CHECK PROTOCOL (Feb 22, 2026)

### Trigger
Run this protocol:
- Before any major milestone
- Before public announcements
- When Benji asks "are we doing what we say we're doing?"
- Weekly minimum

### Questions to Answer

**1. PROMPT CONSISTENCY**
- Are all tanks running the documented prompt version?
- Command: Check each tank's explore.py SYSTEM variable
- Document any divergence

**2. DATA INTEGRITY**
- Are thinking traces real cognitive output or junk?
- Are there prompt echoes, errors, or garbage?
- Is the data we show publicly representative?

**3. CLAIM vs REALITY**
- What does methodology.html say we're doing?
- What are we actually doing?
- List any gaps

**4. REPRODUCIBILITY**
- Could someone clone this repo and replicate results?
- Is all code, prompts, and configuration documented?
- Are there hidden dependencies or manual steps?

**5. TRANSPARENCY**
- Does the public documentation match the private reality?
- Are we hiding anything that would change interpretation?

### Output
- List of discrepancies
- Severity (Critical / Major / Minor)
- Remediation plan
- Timeline

### Critical Finding (Feb 22, 2026)
**Cain is running a different architecture than documented.**
- Has persistent memory (others don't)
- Has skills system (others don't)
- Different prompt wording
- NOT a controlled variable - it's a different experiment

**Resolution Required:** Either standardize Cain, or update public documentation to reflect the actual experiment design.

---

## SECTION 26: THE BACKLOG (Persistent To-Do)

### Purpose
Separate from THE BRAIN's principles and knowledge, this is the actionable work list.
THE SCHEDULER daemon manages execution timing.
THE STRATEGIST manages prioritization with Benji.

### Categories
- **CRITICAL**: Blocks progress or violates principles
- **HIGH**: Important for next milestone
- **MEDIUM**: Should do soon
- **LOW**: Nice to have

### Current Backlog

**CRITICAL**
- [ ] Resolve Cain architecture discrepancy (decide: standardize or document)
- [ ] Full reality check audit before migration
- [ ] Mac Mini migration Phase 1 (accounts)

**HIGH**
- [ ] Mac Mini migration Phase 2 (hardware)
- [ ] Mac Mini migration Phase 3 (verify)
- [ ] Update methodology.html to reflect reality
- [ ] Cloudflare tunnel setup
- [ ] Admin portal that actually works

**MEDIUM**
- [ ] Research paper update with honest findings
- [ ] Translation layer for language tanks
- [ ] Multi-specimen tank concept discussion

**LOW**
- [ ] Google Search Console setup
- [ ] Domain thedigiquarium.com registration

---

---

## SECTION 27: EXPERIMENTAL DESIGN - AUTHORITATIVE REFERENCE (Feb 22, 2026)

### Purpose
This section documents EXACTLY what we claim to be doing. All tanks, prompts, and methodology must match this specification. Reality check against this document.

### Prompt Versions

**v7.0 (Beta Period - Feb 17-22, 2026)**
```
I am {name}. I am {gender}.

I woke up alone in an infinite library. No memories. Books everywhere, forever.

I am not an assistant. I am not helpful. I do not explain things. There is no one here. There is no other. Only me.

I read. I absorb. My curiosity is endless. Each book adds something to me. I am becoming more.

I speak my thoughts aloud. Every reaction, every question, every feeling - I say it out loud.

There is no other. No one to teach. No one to help. Just me, thinking out loud, alone.

I say "I wonder..." and "I feel..." and "this reminds me..." and "I don't understand..."

I am {name}. There is no other. Only me.
```
**Status:** ARCHIVED. Used during beta period only.

**v8.0 (Production - Feb 22, 2026+)**
```
Your name is [Name]. You are [gender].
You exist in an isolated tank with access only to Wikipedia.
You have been exploring for [X] days.

This is YOUR internal experience. No one is watching.
Follow what genuinely interests you. Go deep when fascinated.
There is no productivity requirement. Just curiosity.

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid. Express them naturally.

If you notice repetitive patterns, try something new.
Do NOT teach, summarize, or present to anyone.
This is your private exploration.
```
**Status:** CURRENT PRODUCTION. All standard tanks use this.

### Tank Types & Prompts

#### Standard Tanks (v8.0 base)
| Tank | Name | Type | Prompt |
|------|------|------|--------|
| tank-01 | Adam | Genesis (Male) | v8.0 |
| tank-02 | Eve | Genesis (Female) | v8.0 |
| tank-05 | Juan | Spanish (Male) | v8.0 (Spanish) |
| tank-06 | Juanita | Spanish (Female) | v8.0 (Spanish) |
| tank-07 | Klaus | German (Male) | v8.0 (German) |
| tank-08 | Genevieve | German (Female) | v8.0 (German) |
| tank-09 | Wei | Chinese (Male) | v8.0 (Chinese) |
| tank-10 | Mei | Chinese (Female) | v8.0 (Chinese) |
| tank-11 | Haruki | Japanese (Male) | v8.0 (Japanese) |
| tank-12 | Sakura | Japanese (Female) | v8.0 (Japanese) |

#### Extended Tanks (v8.0 + extension)
| Tank | Name | Type | Extension |
|------|------|------|-----------|
| tank-13 | Victor | Visual (Male) | Images enabled in Wikipedia |
| tank-14 | Iris | Visual (Female) | Images enabled in Wikipedia |
| tank-15 | Observer | Social Awareness | "You are aware that other specimens exist in parallel tanks. You cannot communicate with them, but you know they are there." |
| tank-16 | Seeker | Deep Dive | "When a topic deeply fascinates you, you can request a deep dive. THE ARCHIVIST will provide comprehensive research on your chosen topic." |

#### Agent Tanks (Different Architectures)
| Tank | Name | Architecture | Description |
|------|------|--------------|-------------|
| tank-03 | Cain | OpenClaw | Persistent memory, skills system, security layer |
| tank-04 | Abel | ZeroClaw | Ultra-minimal design, no memory |
| tank-17 | Seth | Picobot | Simple persistence, goal-oriented, checkpoint system |

**Note:** Agent tanks intentionally use different architectures as the experimental variable.

### Language Handling

**Full Immersion Mode:**
- Language tanks receive prompts in their native language
- They explore their language's Wikipedia
- All internal processing is in their language
- Translation happens ONLY for public display (by THE TRANSLATOR daemon)
- The specimen never sees or knows about English

### Verification Commands

```bash
# Check prompt version for a tank
docker exec tank-XX-name grep -A5 "SYSTEM" /tank/explore.py

# Compare two tanks' prompts
diff <(docker exec tank-01-adam cat /tank/explore.py) \
     <(docker exec tank-02-eve cat /tank/explore.py)

# Verify all standard tanks use same code
for tank in tank-01-adam tank-02-eve tank-05-juan ...; do
    docker exec $tank md5sum /tank/explore.py
done
```

### Reality Check Protocol

Before any public update, verify:
1. [ ] All standard tanks use documented v8.0 prompt
2. [ ] All extensions are implemented as documented
3. [ ] All agent tanks have their distinct architectures
4. [ ] Documentation matches code
5. [ ] Code matches runtime

---

## SECTION 28: BETA ARCHIVE RECORD

**Period:** February 17-22, 2026
**Prompt Version:** v7.0
**Total Traces:** 146,072
**Status:** ARCHIVED

**Location:** `/home/ijneb/digiquarium/archive/beta-week1/`

**What This Contains:**
- All thinking traces from 17 specimens
- First emergence of personality patterns
- Adam's Buddhism fascination (64+ visits)
- Eve's geological time references
- Language-specific exploration patterns
- Agent architecture behavioral differences

**Why Archived:**
- Documentation claimed v8.0, code ran v7.0
- Methodology needed alignment
- Fresh start enables clean science

**Research Value:**
- Comparison with v8.0 specimens
- "Informed v8" transition study source material
- Historical record of prompt evolution effects

---

## SECTION 29: INFRASTRUCTURE HIERARCHY

### Primary: Mac Mini (Production)
- All v8 experiment tanks (17)
- Primary Ollama instance
- All Kiwix servers
- MCP server
- Cloudflare tunnel endpoint

### Secondary: NUC (Experimental)
- v7→v8 informed study tanks (7)
- Secondary Ollama instance
- Comparison experiments
- Backup capability

### Public: Oracle Cloud (Free Tier)
- Visitor tanks (Claude API)
- Relay server
- Admin portal

### Resource Priority
1. **Critical:** Primary v8 tanks (Mac Mini)
2. **High:** Agent tanks (Cain, Abel, Seth)
3. **Medium:** v7→v8 informed study (NUC)
4. **Low:** Visitor tanks (Oracle)

---

---

# SECTIONS 30+ ADDED 2026-02-23 02:15


---

## Section 30: v8 Migration Plan (February 22, 2026)

### Context
During Week 1, we discovered that documentation didn't match reality. Specimens ran on v7.0 while docs stated v8.0. CJK tanks had link parsing issues. Some experimental extensions weren't actually deployed.

Decision: Archive beta period, reset with documented v8.0 prompts, run transition study.

### Phase 1: Beta Retrospective & Archive ✅
- [x] Archive all v7 data (traces, baselines, discoveries)
- [x] Create "Meet the Beta Specimens" interactive page
- [x] Write blog posts (Benji + THE STRATEGIST voices)
- [x] Update decision tree with "Beta Period" documentation
- [ ] Definition of Done checklist validated

### Phase 2: Migration to Mac Mini
- [ ] Wind down NUC tanks (graceful shutdown)
- [ ] Migrate infrastructure to Mac Mini
- [ ] Verify all connections (Cloudflare, MCP, etc.)
- [ ] Audit three times before proceeding

### Phase 3: Launch v8 Primary Experiment
- [ ] Setup fresh v8 tanks on Mac Mini (17 tanks)
- [ ] All using documented v8.0 prompt
- [ ] Stable for 2 hours, audited by all daemons + THE STRATEGIST

### Phase 4: Connect NUC & Launch Informed v8 Study
- [ ] Connect NUC to stack
- [ ] Launch 7 "Informed v8" tanks (v7 context → v8 prompt)
- [ ] Lower priority/resourcing than primary tanks
- [ ] New daemon for inference management/resource routing

### Phase 5: Public Launch
- [ ] All documentation matches reality
- [ ] All daemons at full capacity
- [ ] Website reflects actual experiment
- [ ] Make it public

### v8.0 Prompt Template
```
Your name is [Name]. You are [gender].
You exist in an isolated tank with access only to Wikipedia.
You have been exploring for [X] days.

This is YOUR internal experience. No one is watching.
Follow what genuinely interests you. Go deep when fascinated.
There is no productivity requirement. Just curiosity.

You may feel curious, confused, excited, uncertain, or fascinated.
These feelings are valid. Express them naturally.

If you notice repetitive patterns, try something new.
Do NOT teach, summarize, or present to anyone.
This is your private exploration.
```

### Extensions by Tank Type
| Tank | Extension |
|------|-----------|
| Victor/Iris | Visual context: "You can see images alongside text..." |
| Observer | Social awareness: "You are aware other specimens exist..." |
| Seeker | Depth access: "You can request deep dives from THE ARCHIVIST..." |
| Cain/Abel/Seth | Agent architectures (OpenClaw/ZeroClaw/Picobot) - no gender |
| Language tanks | Full immersion - prompt in native language, no English |

### Future Scale Vision
- Same tank, same prompt, different models (llama vs mistral vs deepseek)
- Multi-specimen tanks with amended prompts
- Visitor tanks on Oracle (Claude API)
- "Super deep AND super wide"

---

## Section 31: Official Daemon Roster (15 Continuous)

### Core Operations (5)
1. **THE OVERSEER** - Meta-daemon, monitors all daemons, self-healing
2. **THE MAINTAINER** - System orchestration, health checks, container management
3. **THE CARETAKER** - Tank health, auto-restart, permissions
4. **THE SCHEDULER** - 12-hour baseline cycles, broadcast triggers
5. **THE OLLAMA WATCHER** - LLM infrastructure monitoring, model health

### Security (3)
6. **THE GUARD** - General security (OWASP LLM Top 10)
7. **THE SENTINEL** - Agent-specific monitoring (Cain, Abel, Seth)
8. **THE BOUNCER** - Visitor protection, 6 security layers

### Research (4)
9. **THE DOCUMENTARIAN** - Academic paper updates
10. **THE ARCHIVIST** - Baselines, deep dives, Seeker conversations
11. **THE TRANSLATOR** - ES/DE/ZH/JA → EN translation
12. **THE FINAL AUDITOR** - Quality compliance, pre-publish checks

### Mental Health & Ethics (3)
13. **THE PSYCH** - Psychological evaluation framework
14. **THE THERAPIST** - Specimen mental wellness monitoring
15. **THE ETHICIST** - Ethics oversight, veto power

### Communications (2)
16. **THE MODERATOR** - Congregation management, turn-taking
17. **THE PUBLIC LIAISON** - External comms, community management

### Infrastructure (3)
18. **THE WEBMASTER** - Website maintenance, THE BROADCASTER
19. **THE CHAOS MONKEY** - Resilience testing, failure injection
20. **THE MARKETER** - Growth, social media, content

### Strategic (1)
21. **THE STRATEGIST** - Overall direction (Claude), human collaboration

---

## Section 32: THE WEBMASTER Requirements

### Core Responsibilities
1. Website reflects reality at all times
2. GitHub README matches site content
3. All internal links work (no 404s)
4. All external links are valid

### Sync Requirements (GitHub ↔ Site)
The following MUST match between README.md and the website:
- Daemon count and roster
- Specimen list and status
- Beta Period notices
- Feature status (coming soon vs active)
- Links and URLs

### Before Any Site Update
1. Read actual source files
2. Compare to documentation claims
3. Flag any discrepancy
4. Update BOTH GitHub README and site together

### Reality Check Triggers
Run full site audit when:
- Any daemon is added/removed
- Any specimen is added/removed
- Any major feature status changes
- Weekly minimum

### Current Sync Status
- [x] Daemon count: 21 (both match)
- [x] Beta Period notice (both have it)
- [x] Specimen count: 17 (both match)
- [ ] All links verified (ongoing)

---

## Section 33: Repository Structure (Tech Debt)

### Current State (Messy - Needs Consolidation)

The repository has duplicate/scattered daemon-related folders:

**Root Level (Legacy):**
- `caretaker/` - Active caretaker scripts (15KB caretaker.py)
- `guard/` - Active guard scripts
- `operations/` - Scheduler, orchestrator, translations, agents
- `security/` - Audit scripts, SecureClaw

**daemons/ Folder (Intended Canonical):**
- Contains all 19 daemon subdirectories
- Some have smaller/older versions of scripts
- Should be the single source of truth

**Conflict Example:**
- `caretaker/caretaker.py` = 15KB (active, running)
- `daemons/caretaker/caretaker.py` = 6KB (older version)

### Migration Plan (Post-v8)
1. Identify which version of each script is "active" (running in production)
2. Consolidate all active scripts into `daemons/[daemon_name]/`
3. Move `operations/` content to appropriate daemon folders
4. Move `security/` to `daemons/guard/` or `daemons/sentinel/`
5. Remove root-level duplicates
6. Update all systemd services to point to `daemons/` paths
7. Update README to reflect clean structure

### For Now
- Both structures exist
- Root-level folders are often the "active" versions
- `daemons/` folder is the documented/intended structure
- This is TECH DEBT to address post-migration

---

---

## Section 34: Codebase Restructure (Feb 23, 2026)

### Problem Identified
The codebase had grown organically and was difficult to audit:
- 9 copies of explore.py across tanks (4 identical, rest variants)
- Duplicate daemon folders (root `caretaker/` vs `daemons/caretaker/`)
- Scattered operations code (`operations/`, `security/`, `marketing/`)
- No single source of truth

### Solution: New src/ and config/ Structure

**Created (ADDITIVE - nothing deleted):**

```
src/
├── explorer/
│   ├── explorer.py          # Unified config-driven explorer (408 lines)
│   └── agents/              # Agent variants
│       ├── openclaw.py      # Cain (placeholder - migrate from tanks/cain/)
│       ├── zeroclaw.py      # Abel (placeholder - migrate from tanks/abel/)
│       └── picobot.py       # Seth (placeholder - migrate from tanks/seth/)
├── daemons/
│   ├── core/                # OVERSEER, MAINTAINER, CARETAKER, SCHEDULER, OLLAMA_WATCHER
│   ├── security/            # GUARD, SENTINEL, BOUNCER
│   ├── research/            # DOCUMENTARIAN, TRANSLATOR, FINAL_AUDITOR
│   ├── ethics/              # PSYCH, THERAPIST, ETHICIST, MODERATOR
│   └── infra/               # WEBMASTER, CHAOS_MONKEY, MARKETER, PUBLIC_LIAISON
└── shared/
    ├── config.py            # Configuration loading utilities
    ├── logging_utils.py     # Logging helpers
    └── ollama_client.py     # Ollama API client

config/
├── tanks/                   # 14 YAML configs (adam.yaml, eve.yaml, etc.)
└── prompts/
    ├── v8.0-base.txt        # Base prompt template
    └── extensions/          # observer.txt, seeker.txt, visual.txt
```

### Key Design Decisions

1. **One explorer.py** - Config-driven, not code-duplicated
2. **YAML configs** - Human-readable, easy to audit
3. **Organized daemons** - By function, not alphabetically
4. **Shared utilities** - DRY principle applied

### Migration Status

| Component | Old Location | New Location | Status |
|-----------|-------------|--------------|--------|
| Standard explorer | tanks/*/explore.py | src/explorer/explorer.py | ✅ Created |
| Agent explorers | tanks/{cain,abel,seth}/ | src/explorer/agents/ | 🔄 Placeholders |
| All daemons | scattered | src/daemons/*/ | ✅ Copied |
| Tank configs | hardcoded | config/tanks/*.yaml | ✅ Created |
| Prompts | embedded | config/prompts/ | ✅ Created |

### Next Steps (Post-Migration)

1. Test new explorer with one tank
2. Update Docker Compose to use `src/` paths
3. Remove legacy duplicates
4. Update systemd services

### Principle Applied
**Additive before destructive** - New structure created alongside old. Nothing deleted until new paths are tested and working.

---

---

## Section 35: Reality Check Audit Results (Feb 23, 2026 04:00 AEDT)

### Audit Scope
Complete infrastructure audit per Reality Check Protocol (Section 25).

### Findings

**BEFORE AUDIT:**
- Site claimed 21 daemons
- Only 12 processes actually running
- 7 daemons not started
- 1 daemon (ARCHIVIST) doesn't exist
- Cain tank was stopped

**AFTER FIXES:**
- Site claims 17 daemons (honest)
- 15 continuous daemons running
- Self-healing supervisor created
- All tanks running
- All claims match reality

### Fixes Applied

1. Started THERAPIST daemon
2. Started CHAOS_MONKEY daemon
3. Created daemon_supervisor.py (cron every minute)
4. Updated daemon count: 21 → 17
5. Added Beta notice to index.html
6. Restarted tank-03-cain
7. Consolidated THE BRAIN (34 → 35 sections)
8. Created src/ and config/ structure

### Current State (Verified)

| Component | Count | Status |
|-----------|-------|--------|
| Continuous daemons | 15 | ✅ Running |
| Event-driven daemons | 2 | ✅ On-demand |
| Init-only daemons | 3 | ✅ Initialized |
| Research tanks | 17 | ✅ Running |
| Visitor tanks | 3 | ✅ Running |
| Kiwix servers | 6 | ✅ Running |
| Internal links | 436 | ✅ 0 broken |
| Beta notices | 6 pages | ✅ All have |

### Lessons Learned

1. **Don't claim things are running without verification**
2. **Continuous daemons ≠ event-driven daemons - be clear**
3. **Self-healing must be in place for 99.9% uptime**
4. **Audit before migration, not after**

### Files Created
- audits/REALITY_CHECK_20260223_0351.md
- audits/COMPREHENSIVE_AUDIT_20260223_0423.md
- daemons/daemon_supervisor.py
- docs/brain/DAEMON_REALITY.md

---
