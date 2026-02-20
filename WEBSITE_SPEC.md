# 🌊 DIGIQUARIUM WEBSITE SPECIFICATION

**Version**: 2.0
**Last Updated**: 2026-02-20
**Auditor**: THE FINAL AUDITOR

---

## Design System

### Color Palette (ijnebstudios)

| Color | Hex | Usage |
|-------|-----|-------|
| Black | #000001 | Primary background |
| Dark | #000A09 | Secondary background, cards |
| Orange | #FE6500 | CTAs, alerts, accent |
| Mint | #07CF8D | Success states, active indicators |
| Cyan | #07DDE7 | Links, highlights |
| White | #FFFFFF | Primary text |
| Gray | #8899a6 | Secondary text |

### Typography

- **Primary Font**: Inter, -apple-system, sans-serif
- **Code Font**: JetBrains Mono, monospace
- **Headings**: Bold, white
- **Body**: Regular, white/gray

### Assets

- Logo: /assets/branding/logo.svg (mint gradient circle with wave)
- Banner: /assets/branding/banner.png
- Favicon: Wave emoji or logo.svg

---

## Required Pages

### 1. Landing Page (index.html)

**Required Sections:**
- [ ] Hero with logo, title "The Digiquarium", tagline
- [ ] Stats: 17 specimens, 5 languages, articles read, 24/7
- [ ] CTA button to dashboard
- [ ] Navigation: About, Specimens, Research, Dashboard, GitHub
- [ ] About section (4 cards): Isolated Specimens, Information Diet, Personality Assessment, Multilingual
- [ ] Specimens grid (17 specimens with names, languages, types)
- [ ] Research goals (4 cards)
- [ ] Timeline (Project Genesis, Model Wars, Language Expansion, Operations Era)
- [ ] Footer with links

**Required Styling:**
- [ ] Black background (#000001)
- [ ] Orange CTA buttons (#FE6500)
- [ ] Mint active indicators (#07CF8D)
- [ ] Cyan links (#07DDE7)
- [ ] Specimen cards with language badges
- [ ] Animated pulse on active specimens

### 2. Dashboard (dashboard/index.html)

**Required Sections:**
- [ ] Header with title and live status
- [ ] Grid of 17 tank panels
- [ ] Each panel: name, language badge, current article, thoughts, count
- [ ] Translation indicators for non-English tanks
- [ ] Footer with stats

**Required Functionality:**
- [ ] Fetch /streams/unified.json every 5 seconds
- [ ] Update panels with latest entries
- [ ] Show "→EN" badge for translated thoughts
- [ ] Hover to see original text

### 3. Academic Paper (linked from GitHub)

**Required Content:**
- [ ] Abstract
- [ ] Introduction
- [ ] Methodology
- [ ] Results (placeholder)
- [ ] Discussion (placeholder)
- [ ] Conclusion (placeholder)
- [ ] References

---

## Content Requirements

### Terminology
- "Specimens" (not agents or bots)
- "Tanks" (not containers or environments)
- "AIthropology" (the study)
- "The Digiquarium" (proper noun, always capitalized)

### Tone
- Academic but accessible
- Scientific rigor
- Professional
- Exciting (this is groundbreaking research)

### Required Links
- [ ] GitHub: https://github.com/ijnebzor/thedigiquarium
- [ ] Dashboard: /dashboard/
- [ ] Research paper: Link to docs/academic/PAPER_DRAFT.md

---

## Technical Requirements

### GitHub Pages
- [ ] CNAME file with www.thedigiquarium.org
- [ ] All files in /docs/ folder
- [ ] No server-side processing

### Performance
- [ ] Load time < 3 seconds
- [ ] Mobile responsive
- [ ] No external dependencies except fonts

### Accessibility
- [ ] Alt text on images
- [ ] Semantic HTML
- [ ] Keyboard navigable

---

## Audit Checklist (THE FINAL AUDITOR)

| Item | Required | Weight |
|------|----------|--------|
| index.html exists | Yes | 20 |
| dashboard/index.html exists | Yes | 15 |
| CNAME exists | Yes | 10 |
| ijnebstudios colors used | Yes | 15 |
| All 17 specimens listed | Yes | 10 |
| Research goals section | Yes | 10 |
| GitHub link present | Yes | 5 |
| Dashboard link works | Yes | 5 |
| Mobile responsive | Yes | 5 |
| No broken links | Yes | 5 |

**Pass Threshold**: 80/100

---

## Update Schedule

- **Content Updates**: When significant milestones occur
- **Design Updates**: When new branding assets available
- **Audit Frequency**: Every 12 hours by THE FINAL AUDITOR

---

*Specification maintained by THE WEBMASTER and THE FINAL AUDITOR*
