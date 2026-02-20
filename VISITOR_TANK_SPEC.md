# 🎟️ VISITOR TANK SPECIFICATION

**Version**: 1.0
**Status**: DESIGNED - NOT DEPLOYED
**Last Updated**: 2026-02-20

---

## Overview

Visitor Tanks allow users to "check out" a specimen for interactive conversation while maintaining scientific integrity. This creates engagement without compromising the main research specimens.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VISITOR TANK SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │  Website  │───▶│ Visitor API  │───▶│ Visitor Tank  │   │
│  │  (User)   │◀───│  (Gateway)   │◀───│  (Container)  │   │
│  └───────────┘    └──────────────┘    └───────────────┘   │
│                           │                                 │
│                           ▼                                 │
│                   ┌──────────────┐                         │
│                   │ Session Mgr  │                         │
│                   │ (Rate Limit) │                         │
│                   └──────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Visitor API Gateway

**Endpoint**: `/api/visitor/`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/visitor/available` | GET | List available visitor specimens |
| `/api/visitor/checkout` | POST | Check out a specimen |
| `/api/visitor/chat` | POST | Send message to specimen |
| `/api/visitor/release` | POST | Release specimen |
| `/api/visitor/history` | GET | Get conversation history |

### 2. Visitor Tank Container

- **Base**: Same as research tanks
- **Difference**: 
  - No baseline assessments during visitor session
  - Conversation logged separately
  - Time-limited sessions (30 min default)
  - Rate limited (5 messages/minute)

### 3. Session Manager

- Tracks active visitor sessions
- Enforces rate limits
- Auto-releases after timeout
- Queue management (max 3 concurrent visitors)

---

## Visitor Specimens

| Specimen | Type | Purpose |
|----------|------|---------|
| Guest-Alpha | Clone of Adam | General visitor interaction |
| Guest-Beta | Clone of Eve | Alternative personality |
| Guest-Explorer | Fresh spawn | Pure visitor experience |

**Note**: These are CLONES, not the actual research specimens. Research specimens are never exposed to visitor interaction.

---

## User Flow

1. **User visits** `/visit/` page
2. **Sees available specimens** (Guest-Alpha, Guest-Beta, etc.)
3. **Clicks "Check Out"** → Creates session
4. **Chat interface opens** → User can converse
5. **30-minute session** → Auto-release
6. **Optional**: User can "release" early
7. **Conversation archived** → Available for research

---

## Security Considerations

1. **Isolation**: Visitor tanks on separate network from research tanks
2. **Rate Limiting**: 5 messages/minute, 100 messages/session
3. **Content Filtering**: Input sanitization for prompt injection
4. **No PII**: Visitors anonymous, no login required
5. **Logging**: All conversations logged for abuse detection

---

## Implementation Files

```
visitor/
├── api/
│   ├── gateway.py          # API endpoints
│   └── session_manager.py  # Session tracking
├── containers/
│   ├── guest-alpha/        # Clone of Adam
│   ├── guest-beta/         # Clone of Eve
│   └── guest-explorer/     # Fresh specimen
├── web/
│   └── visit.html          # Visitor interface
└── logs/
    └── sessions/           # Conversation logs
```

---

## Rate Limits

| Limit | Value |
|-------|-------|
| Max concurrent visitors | 3 |
| Session duration | 30 minutes |
| Messages per minute | 5 |
| Messages per session | 100 |
| Cooldown between sessions | 10 minutes |

---

## Future Enhancements

1. **Specimen Selection**: Let users choose personality traits
2. **Topic Focus**: Pre-seed with specific Wikipedia topics
3. **Comparison Mode**: Chat with two specimens simultaneously
4. **Export**: Download conversation as PDF
5. **Leaderboard**: Most interesting conversations

---

## NOT DEPLOYED

**Reason**: Awaiting owner approval and testing.

**To Deploy**:
1. Create visitor containers
2. Deploy API gateway
3. Create visit.html page
4. Test security measures
5. Owner approval
6. Launch

---

*Specification by THE STRATEGIST*
