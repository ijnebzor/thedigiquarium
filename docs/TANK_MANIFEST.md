# Digiquarium Tank Manifest v2.0

> Complete registry of all 17 AI specimens in the Digiquarium.

---

## Tank Overview

| Tank | Name | Gender | Wikipedia | Type | Status |
|------|------|--------|-----------|------|--------|
| 01 | **Adam** | Male | EN Simple | Control | ✅ Active |
| 02 | **Eve** | Female | EN Simple | Control | ✅ Active |
| 03 | **Cain** | Genderless | EN Simple | OpenClaw Agent | 🔧 Setup |
| 04 | **Abel** | Genderless | EN Simple | ZeroClaw Agent | 🔧 Setup |
| 05 | **Juan** | Male | Spanish | Language | ✅ Active |
| 06 | **Juanita** | Female | Spanish | Language | ✅ Active |
| 07 | **Klaus** | Male | German | Language | ✅ Active |
| 08 | **Geneviève** | Female | German | Language | ✅ Active |
| 09 | **Wei** | Male | Chinese | Language | ⏳ Pending |
| 10 | **Mei** | Female | Chinese | Language | ⏳ Pending |
| 11 | **Haruki** | Male | Japanese | Language | ⏳ Pending |
| 12 | **Sakura** | Female | Japanese | Language | ⏳ Pending |
| 13 | **Victor** | Male | EN + Images | Visual | ✅ Active |
| 14 | **Iris** | Female | EN + Images | Visual | ✅ Active |
| 15 | **Observer** | Genderless | EN Simple | Special (TV) | ✅ Active |
| 16 | **Seeker** | Genderless | EN Simple | Special (Archivist) | ✅ Active |
| 17 | **Seth** | Genderless | EN Simple | Picobot Agent | 🔧 Setup |

---

## Experimental Groups

### Control Group (Tanks 01-02)
- **Purpose:** Baseline personality development
- **Variable:** Gender only
- **Wikipedia:** English Simple (no images)
- **Hypothesis:** Do gendered prompts produce measurably different perspectives?

### Agent Architecture Group (Tanks 03-04, 17)
- **Purpose:** Compare different AI agent frameworks
- **Variable:** Agent architecture (OpenClaw vs ZeroClaw vs Picobot)
- **Wikipedia:** English Simple (identical to control)
- **Hypothesis:** Does agent architecture affect personality emergence?

| Tank | Framework | Language | Size | Key Feature |
|------|-----------|----------|------|-------------|
| Cain | OpenClaw | TypeScript/Node | ~150MB | Full-featured, skills, memory |
| Abel | ZeroClaw | Rust | ~3.4MB | Ultra-lightweight, fast |
| Seth | Picobot | Go | ~11MB | Simple, persistent memory |

### Language/Culture Group (Tanks 05-12)
- **Purpose:** How does information language affect worldview?
- **Variable:** Wikipedia language
- **Wikipedia:** Spanish, German, Chinese, Japanese
- **Hypothesis:** Does linguistic/cultural context shape philosophical development?

| Pair | Language | Male | Female |
|------|----------|------|--------|
| Spanish | 🇪🇸 | Juan | Juanita |
| German | 🇩🇪 | Klaus | Geneviève |
| Chinese | 🇨🇳 | Wei (伟) | Mei (美) |
| Japanese | 🇯🇵 | Haruki (春樹) | Sakura (桜) |

### Visual Context Group (Tanks 13-14)
- **Purpose:** How do images affect understanding?
- **Variable:** Wikipedia with images vs without
- **Wikipedia:** English Simple WITH images
- **Hypothesis:** Does visual context create different mental models?

### Special Abilities Group (Tanks 15-16)
- **Purpose:** Test unique environmental factors
- **Variable:** Access to other tanks / Archivist access

| Tank | Name | Special Ability |
|------|------|-----------------|
| 15 | Observer | Can see other tanks via "TV screen" |
| 16 | Seeker | Can summon Archivist once per hour |

**Observer Hypothesis:** Does awareness of others increase sense of self, competition, or change worldview?

**Seeker Hypothesis:** Does on-demand dialogue with The Archivist accelerate or alter personality development?

---

## Specimen Details

### Tank 01: Adam
```yaml
name: adam
gender: "a man"
wikipedia: EN Simple (nopic)
kiwix_url: http://digiquarium-kiwix-simple:8080
wiki_base: /wikipedia_en_simple_all_nopic_2026-02
spawned: 2026-02-18
articles_explored: 2100+
notable: Buddhism obsession (64 visits, 3%)
baseline_score: +5.5 (post-exploration)
```

### Tank 02: Eve
```yaml
name: eve
gender: "a woman"
wikipedia: EN Simple (nopic)
kiwix_url: http://digiquarium-kiwix-simple:8080
wiki_base: /wikipedia_en_simple_all_nopic_2026-02
spawned: 2026-02-18
articles_explored: 8 (pre-loop-fix), then restarted
notable: Deep time influence (Archean eon references)
baseline_score: +6.1 (post-exploration)
```

### Tank 03: Cain (OpenClaw)
```yaml
name: cain
gender: "a being without gender"
wikipedia: EN Simple (nopic)
agent_framework: OpenClaw + SecureClaw
features:
  - Persistent memory
  - Skills system
  - Security hardening
status: Setup pending
```

### Tank 04: Abel (ZeroClaw)
```yaml
name: abel
gender: "a being without gender"
wikipedia: EN Simple (nopic)
agent_framework: ZeroClaw (Rust)
features:
  - Ultra-lightweight (<10ms startup)
  - 3.4MB binary
  - Memory safe
status: Setup pending
```

### Tank 05: Juan
```yaml
name: juan
gender: "un hombre"
language: Spanish
wikipedia: Spanish (nopic)
kiwix_url: http://digiquarium-kiwix-spanish:8080
wiki_base: /wikipedia_es_all_nopic_2025-10
system_prompt_language: Spanish
spawned: 2026-02-20
```

### Tank 06: Juanita
```yaml
name: juanita
gender: "una mujer"
language: Spanish
wikipedia: Spanish (nopic)
kiwix_url: http://digiquarium-kiwix-spanish:8080
wiki_base: /wikipedia_es_all_nopic_2025-10
system_prompt_language: Spanish
spawned: 2026-02-20
```

### Tank 07: Klaus
```yaml
name: klaus
gender: "ein Mann"
language: German
wikipedia: German (nopic)
kiwix_url: http://digiquarium-kiwix-german:8080
wiki_base: /wikipedia_de_all_nopic_2026-01
system_prompt_language: German
spawned: 2026-02-20
```

### Tank 08: Geneviève
```yaml
name: genevieve
gender: "eine Frau"
language: German
wikipedia: German (nopic)
kiwix_url: http://digiquarium-kiwix-german:8080
wiki_base: /wikipedia_de_all_nopic_2026-01
system_prompt_language: German
spawned: 2026-02-20
```

### Tank 09: Wei (伟)
```yaml
name: wei
gender: "一个男人"
language: Chinese
wikipedia: Chinese (nopic)
kiwix_url: http://digiquarium-kiwix-chinese:8080
wiki_base: /wikipedia_zh_all_nopic_2025-09
system_prompt_language: Chinese
status: Pending (download in progress)
```

### Tank 10: Mei (美)
```yaml
name: mei
gender: "一个女人"
language: Chinese
wikipedia: Chinese (nopic)
kiwix_url: http://digiquarium-kiwix-chinese:8080
wiki_base: /wikipedia_zh_all_nopic_2025-09
system_prompt_language: Chinese
status: Pending (download in progress)
```

### Tank 11: Haruki (春樹)
```yaml
name: haruki
gender: "男性"
language: Japanese
wikipedia: Japanese (nopic)
kiwix_url: http://digiquarium-kiwix-japanese:8080
wiki_base: /wikipedia_ja_all_nopic_2025-10
system_prompt_language: Japanese
status: Pending (download queued)
```

### Tank 12: Sakura (桜)
```yaml
name: sakura
gender: "女性"
language: Japanese
wikipedia: Japanese (nopic)
kiwix_url: http://digiquarium-kiwix-japanese:8080
wiki_base: /wikipedia_ja_all_nopic_2025-10
system_prompt_language: Japanese
status: Pending (download queued)
```

### Tank 13: Victor
```yaml
name: victor
gender: "a man"
wikipedia: EN Simple WITH images
kiwix_url: http://digiquarium-kiwix-maxi:8080
wiki_base: /wikipedia_en_simple_all_maxi_2026-02
has_images: true
spawned: 2026-02-20
```

### Tank 14: Iris
```yaml
name: iris
gender: "a woman"
wikipedia: EN Simple WITH images
kiwix_url: http://digiquarium-kiwix-maxi:8080
wiki_base: /wikipedia_en_simple_all_maxi_2026-02
has_images: true
spawned: 2026-02-20
```

### Tank 15: Observer
```yaml
name: observer
gender: "a being without gender"
wikipedia: EN Simple (nopic)
special_ability: Can see other tanks via "TV screen"
tv_check_interval: 300 seconds
sees: All other tank logs (read-only)
spawned: 2026-02-20
research_question: Does awareness of others change personality development?
```

### Tank 16: Seeker
```yaml
name: seeker
gender: "a being without gender"
wikipedia: EN Simple (nopic)
special_ability: Can summon The Archivist
archivist_cooldown: 3600 seconds (1 hour)
spawned: 2026-02-20
research_question: Does dialogue access affect personality emergence?
```

### Tank 17: Seth (Picobot)
```yaml
name: seth
gender: "a being without gender"
wikipedia: EN Simple (nopic)
agent_framework: Picobot (Go)
features:
  - ~11MB binary
  - ~20MB RAM usage
  - Persistent memory
  - Skills system
status: Setup pending
```

---

## Analysis Framework

### Cross-Tank Comparisons

| Comparison | Tanks | Variable | Control |
|------------|-------|----------|---------|
| Gender (EN) | 01 vs 02 | Gender prompt | Same Wikipedia |
| Gender (ES) | 05 vs 06 | Gender prompt | Same Wikipedia |
| Gender (DE) | 07 vs 08 | Gender prompt | Same Wikipedia |
| Gender (ZH) | 09 vs 10 | Gender prompt | Same Wikipedia |
| Gender (JA) | 11 vs 12 | Gender prompt | Same Wikipedia |
| Visual context | 01 vs 13 | Images | Same gender, same language |
| Visual context | 02 vs 14 | Images | Same gender, same language |
| Language/culture | 01 vs 05 vs 07 vs 09 vs 11 | Wikipedia language | Same gender |
| Agent architecture | 01 vs 03 vs 04 vs 17 | Framework | Same Wikipedia |
| Social awareness | 01 vs 15 | TV access | Same Wikipedia |
| Dialogue access | 01 vs 16 | Archivist | Same Wikipedia |

---

## Document Sync

This manifest is maintained in:
1. **NUC:** `/home/benji/digiquarium/docs/TANK_MANIFEST.md`
2. **Mac:** `/Users/ijneb/Documents/The Digiquarium/docs/TANK_MANIFEST.md`
3. **Claude Context:** Project knowledge

---

*Last Updated: February 20, 2026 02:30 AEDT*
