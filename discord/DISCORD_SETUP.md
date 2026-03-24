# 🎮 THE DIGIQUARIUM - Discord Server Setup

**Server Name**: The Digiquarium
**Purpose**: Community engagement, live monitoring, escalation alerts

---

## Server Structure

### Categories & Channels

```
📢 ANNOUNCEMENTS
├── #welcome
├── #announcements
└── #rules

🔬 RESEARCH
├── #methodology
├── #observations
├── #findings
└── #paper-discussion

🐠 SPECIMENS
├── #adam-eve (control group)
├── #cain-abel-seth (agents)
├── #spanish-tanks
├── #german-tanks
├── #chinese-tanks
├── #japanese-tanks
└── #visual-tanks

📊 LIVE FEEDS
├── #tank-activity (bot posts)
├── #baselines (bot posts)
├── #discoveries (bot posts)
└── #translations (bot posts)

🚨 OPERATIONS
├── #alerts (daemon escalations)
├── #system-status
└── #maintenance-log

💬 COMMUNITY
├── #general
├── #questions
└── #suggestions

🔒 PRIVATE (Admin only)
├── #admin
├── #security-alerts
└── #escalations
```

---

## Bot Configuration

### Digiquarium Bot
- **Purpose**: Post live updates from daemons
- **Prefix**: `!dq`
- **Commands**:
  - `!dq status` - System status
  - `!dq tank <name>` - Tank info
  - `!dq latest` - Latest discoveries

### Webhooks

| Webhook | Channel | Purpose |
|---------|---------|---------|
| `alerts` | #alerts | Daemon escalations |
| `activity` | #tank-activity | Live tank updates |
| `security` | #security-alerts | Security findings |

---

## Role Structure

| Role | Color | Permissions |
|------|-------|-------------|
| @Owner | Orange #FE6500 | All |
| @Researcher | Mint #07CF8D | Read all, post research |
| @Observer | Cyan #07DDE7 | Read only |
| @Bot | White | Post in designated channels |

---

## Setup Steps

1. Create Discord server "The Digiquarium"
2. Create categories and channels per structure above
3. Create roles with colors
4. Create webhooks for #alerts, #tank-activity, #security-alerts
5. Save webhook URLs to $DIGIQUARIUM_HOME/discord/webhooks.json
6. Update SecureClaw config with webhook URL

---

## Webhook Configuration File

Create `$DIGIQUARIUM_HOME/discord/webhooks.json`:

```json
{
  "alerts": "https://discord.com/api/webhooks/...",
  "activity": "https://discord.com/api/webhooks/...",
  "security": "https://discord.com/api/webhooks/..."
}
```

---

*Setup guide by THE STRATEGIST*
