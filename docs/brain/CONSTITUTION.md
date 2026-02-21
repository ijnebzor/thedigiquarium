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

## SECTION 3: DAEMON ROSTER (20 Daemons)

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

