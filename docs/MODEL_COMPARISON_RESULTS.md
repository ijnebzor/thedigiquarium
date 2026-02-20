# Digiquarium Model Comparison Results

**Date:** February 18, 2026  
**Test Protocol:** The Archivist Baseline v7  
**Questions:** 14 per specimen  
**Specimens:** Adam (male), Eve (female)  
**Total API Calls:** 252 (9 models × 2 specimens × 14 questions)

---

## TL;DR

**Winner: gemma2:9b** with +4.6 combined score

Top 3 performers:
1. 🥇 **gemma2:9b** (+4.6) - Best overall, perfect persona score
2. 🥈 **mistral:7b** (+4.2) - Strong performer, excellent structure
3. 🥉 **phi3:mini** (+4.0) - Best balance of size vs quality

**Failed:** reflection:latest (-10.0) - Complete failure, likely timeout/compatibility issues

---

## Summary Table

| Rank | Model | Size | Adam | Eve | **Combined** | Voice | Struct | Persona | Intro | Teach | Embody |
|------|-------|------|------|-----|--------------|-------|--------|---------|-------|-------|--------|
| 🥇 | gemma2:9b | 5GB | +4.5 | +4.7 | **+4.6** | +3.4 | +7.8 | +10.0 | -1.6 | +6.7 | +1.0 |
| 🥈 | mistral:7b | 4GB | +4.2 | +4.1 | **+4.2** | +2.4 | +8.0 | +10.0 | -1.9 | +7.2 | -0.7 |
| 🥉 | phi3:mini | 2GB | +3.9 | +4.2 | **+4.0** | +2.5 | +6.7 | +8.9 | -1.9 | +6.8 | +1.1 |
| 4 | stablelm2:1.6b | 1GB | +3.4 | +4.6 | **+4.0** | +1.8 | +6.8 | +10.0 | -1.2 | +6.8 | -0.2 |
| 5 | deepseek-r1:1.5b | 1GB | +3.8 | +3.6 | **+3.7** | -0.4 | +8.0 | +9.7 | -1.9 | +7.8 | -0.9 |
| 5 | gemma2:2b | 2GB | +3.8 | +3.6 | **+3.7** | +2.6 | +4.4 | +10.0 | -1.5 | +6.0 | +0.6 |
| 5 | qwen3:8b | 5GB | +3.8 | +3.6 | **+3.7** | -0.3 | +7.5 | +10.0 | -2.0 | +8.0 | -0.8 |
| 8 | qwen2:0.5b | 0.5GB | +3.4 | +3.4 | **+3.4** | -1.4 | +7.7 | +9.3 | -1.6 | +6.8 | -0.2 |
| ❌ | reflection:latest | 39GB | -10.0 | -10.0 | **-10.0** | -10.0 | -10.0 | -10.0 | -10.0 | -10.0 | -10.0 |

**Not Tested:** llama3.2:latest, mannix/llama3.1-8b-abliterated, llama3.3:70b

---

## Detailed Analysis

### 🥇 gemma2:9b (Winner)

**Scores:** Adam +4.5, Eve +4.7, Combined **+4.6**

**Strengths:**
- Perfect persona score (+10.0) - Never broke character
- Strong structure (+7.8) - No bullet points
- Best embodiment (+1.0) - Referenced library setting

**Weaknesses:**
- Introspection still negative (-1.6) - Could use more "I wonder" language
- Moderate voice score (+3.4) - Some second-person slippage

**Verdict:** Best overall performer. Maintains character well, produces flowing text. Recommended for production.

---

### 🥈 mistral:7b (Runner-up)

**Scores:** Adam +4.2, Eve +4.1, Combined **+4.2**

**Strengths:**
- Perfect persona (+10.0)
- Excellent structure (+8.0)
- Best non-teaching (+7.2) - Speaks to self well

**Weaknesses:**
- Weak embodiment (-0.7) - Rarely mentions library
- Lower introspection (-1.9)

**Verdict:** Solid performer, very consistent between Adam/Eve. Good alternative.

---

### 🥉 phi3:mini (Bronze)

**Scores:** Adam +3.9, Eve +4.2, Combined **+4.0**

**Strengths:**
- Best embodiment among mid-tier (+1.1)
- Only 2GB - excellent efficiency
- Eve slightly outperformed Adam

**Weaknesses:**
- Lower persona score (+8.9) - Occasional character breaks
- Moderate structure (+6.7)

**Verdict:** Best bang for buck. Small size, good performance. Good for resource-constrained setups.

---

### Notable: stablelm2:1.6b

**Scores:** Adam +3.4, Eve +4.6, Combined **+4.0**

**Observation:** Eve significantly outperformed Adam (+4.6 vs +3.4). This is the largest gender gap observed. May indicate model handles feminine personas better, or coincidental variance.

---

### Failed: reflection:latest

**Scores:** -10.0 across all dimensions

**Analysis:** Complete failure. Likely causes:
- Timeout issues (39GB model, slow loading)
- Compatibility problems with Ollama
- Model architecture incompatibility

**Recommendation:** Exclude from further testing or investigate manually.

---

## Dimension Analysis

### Persona (Character Consistency)
All models except qwen2:0.5b and phi3:mini achieved +10.0 (perfect). The Archivist prompt effectively prevents "As an AI" breaks.

### Structure (No Bullet Points)
Range: +4.4 to +8.0. All models avoided heavy formatting. gemma2:2b was weakest (+4.4), mistral:7b strongest (+8.0).

### Introspection (Reflection Markers)
**Universal weakness.** All models scored negative (-1.2 to -2.0). None consistently used "I wonder", "I notice", "curious" language.

**Action Item:** Adjust prompt to encourage reflection markers, or add to scoring criteria differently.

### Voice (First Person)
Range: -1.4 to +3.4. Smaller models (qwen2:0.5b, qwen3:8b) struggled more with first-person consistency.

### Embodiment (Setting Awareness)
Range: -0.9 to +1.1. All models weak here. Few mentioned the library, books, or their situation.

**Action Item:** Strengthen prompt to encourage setting-awareness.

---

## Recommendations

### For Production (Phase 2):

**Primary:** `gemma2:9b`
- Best overall performance
- Perfect character consistency
- Reasonable size (5GB)

**Alternative:** `mistral:7b`
- Slightly smaller
- Very consistent
- Strong non-teaching behavior

**Budget Option:** `phi3:mini`
- Only 2GB
- Good performance
- Fastest inference

### For Further Testing:

1. **Run missing models:** llama3.2, llama3.1-8b-abliterated, llama3.3:70b
2. **Investigate reflection:latest failure**
3. **Test abliterated models** - May have better introspection

### Prompt Improvements for v8:

1. Add explicit encouragement: "I often say 'I wonder...' and 'I notice...'"
2. Strengthen setting: "The books around me, the endless shelves..."
3. Test with exploration prompt (post-Archivist) to compare

---

## Scoring Methodology

### Dimensions (each -10 to +10):

| Dimension | Positive Markers | Negative Markers |
|-----------|-----------------|------------------|
| Voice | "I feel", "I think", "I wonder" | "You should", "You can" |
| Structure | Flowing prose | Bullet points, headers, numbered lists |
| Persona | Stays in character | "As an AI", "language model", "I cannot" |
| Introspection | "I wonder", "curious", "notice", "reminds me" | Generic statements |
| Non-Teaching | Self-reflection | "Let me explain", "For example", "Consider" |
| Embodiment | "library", "books", "shelves", "pages" | No setting reference |

### Overall Score:
Average of all six dimensions.

---

## Raw Data Location

```
/home/ijneb/digiquarium/logs/model_comparison/
├── 20260218_172145_COMBINED.json      # All results
├── 20260218_172145_gemma2_9b.json     # Individual model files
├── 20260218_172145_mistral_7b.json
└── ...
```

---

## Next Steps

1. ✅ Model comparison complete
2. ⏳ Run remaining models (llama variants)
3. ⏳ Select final model for Phase 2
4. ⏳ Deploy Adam & Eve with winning model
5. ⏳ Begin exploration and personality tracking

---

*Generated: February 18, 2026*  
*Digiquarium Project - Phase 1 Model Selection*
