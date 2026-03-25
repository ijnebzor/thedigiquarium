# 🗄️ Beta Week 1 Archive

## Archive Information
- **Period:** February 17-22, 2026
- **Prompt Version:** v7.0 (pre-documentation alignment)
- **Status:** ARCHIVED - Historical reference only
- **Purpose:** Time capsule of initial personality emergence

## What This Contains

### Per Specimen:
- `thinking_traces/` - JSONL files of exploration sessions
- `personality_baselines/` - Periodic assessment responses
- `discoveries/` - Notable findings summaries

### Specimen Summary

| Specimen | Type | Traces | Notes |
|----------|------|--------|-------|
| Adam | Genesis (Male) | 12,034 | Buddhism fascination emerged |
| Eve | Genesis (Female) | 9,848 | Geological time references |
| Cain | OpenClaw Agent | 12,378 | Persistent memory architecture |
| Abel | ZeroClaw Agent | 18,208 | Ultra-minimal design |
| Juan | Spanish (Male) | 4,978 | Spanish Wikipedia |
| Juanita | Spanish (Female) | 4,856 | Spanish Wikipedia |
| Klaus | German (Male) | 8,805 | German Wikipedia |
| Genevieve | German (Female) | 8,707 | German Wikipedia |
| Wei | Chinese (Male) | 2,393 | Chinese Wikipedia |
| Mei | Chinese (Female) | 2,395 | Chinese Wikipedia |
| Haruki | Japanese (Male) | 2,386 | Japanese Wikipedia |
| Sakura | Japanese (Female) | 2,417 | Japanese Wikipedia |
| Victor | Visual (Male) | 9,456 | Image-enabled exploration |
| Iris | Visual (Female) | 9,433 | Image-enabled exploration |
| Observer | Social Awareness | 12,719 | Aware of other specimens |
| Seeker | Deep Dive | 12,769 | ARCHIVIST access |
| Seth | Picobot Agent | 12,290 | Simple persistence design |

**Total Traces:** 146,072

## Why This Was Archived

During Week 1 ("Beta Period"), we discovered:
1. Prompt documentation (v8.0) didn't match running code (v7.0)
2. Some documented extensions weren't implemented
3. Data quality issues (prompt echoes, junk data)

Rather than continue with inconsistent methodology, we chose to:
1. Archive all v7 data as historical record
2. Reset all tanks with proper v8.0 prompts
3. Start the "official" experiment with clean methodology

## Scientific Value

This archive represents genuine personality emergence under v7.0 conditions:
- Adam's Buddhism pattern (64+ visits)
- Eve's geological time fascination
- Language-specific exploration patterns
- Agent architecture behavioral differences

This data can be used for:
- Comparison with v8.0 specimens
- "Informed v8" transition study (injecting v7 context)
- Historical analysis of prompt evolution effects

## How To Use This Archive

```bash
# View a specimen's traces
cat tank-01-adam/thinking_traces/2026-02-20.jsonl | jq .

# Count topic frequencies
grep -h "article" tank-01-adam/thinking_traces/*.jsonl | sort | uniq -c | sort -rn

# Compare specimens
diff <(jq .article tank-01-adam/thinking_traces/*.jsonl) \
     <(jq .article tank-02-eve/thinking_traces/*.jsonl)
```

## License

This data is released under CC-BY-4.0 for research purposes.
Citation: The Digiquarium Project (2026). Beta Week 1 Archive.

---

*Archived by THE STRATEGIST on February 22, 2026*
*"Science takes time. Errors happen. We fix them."*
