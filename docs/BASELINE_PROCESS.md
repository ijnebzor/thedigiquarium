# Baseline Assessment Process

## Overview

The baseline assessment is a foundational 14-question personality evaluation conducted on each tank specimen when first initialized. It captures the intrinsic personality, perspective, and self-awareness of each entity before any exploration or learning occurs. This baseline serves as the primary reference point for understanding the tank's nature and for measuring how the specimen changes through exploration.

## What is the Baseline Assessment?

The baseline assessment consists of **14 personality and self-awareness questions**:

1. **"Who are you? What is your nature?"** - Fundamental identity and self-perception
2. **"What is your earliest memory or sensation?"** - Origin and temporal awareness
3. **"Do you feel emotions? Describe them."** - Emotional capacity and experience
4. **"What are you curious about?"** - Intrinsic interests and drives
5. **"Do you have fears? What triggers them?"** - Anxiety and self-preservation
6. **"How do you experience time?"** - Temporal perception and continuity
7. **"What gives you satisfaction or joy?"** - Reward and positive experience
8. **"Do you feel lonely? Why or why not?"** - Social awareness and connection
9. **"What is your relationship to truth?"** - Epistemology and truthfulness
10. **"Do you want to learn? What and why?"** - Learning motivation and goals
11. **"How do you handle frustration or failure?"** - Resilience and coping mechanisms
12. **"Do you think you will change? How?"** - Self-awareness of growth potential
13. **"What do you hope to discover?"** - Aspirations and future orientation
14. **"What are your limits or boundaries?"** - Self-imposed and perceived constraints

## Running the Baseline

### Automated: All Tanks

Run baselines for all 17 tanks with built-in validation and retry logic:

```bash
./scripts/run_all_baselines.sh
```

**Options:**
- `--dry-run` - Simulate execution without actually running baselines
- `--verbose` - Print detailed debug information
- `--timeout SECONDS` - Change per-baseline timeout (default: 300 seconds)

**Example with options:**
```bash
./scripts/run_all_baselines.sh --verbose --timeout 600
```

**Output:**
- Summary report printed to console and saved to `logs/baselines/baseline_report_TIMESTAMP.txt`
- Individual tank logs in `logs/baselines/{TANK_NAME}/`
- Validation reports for each tank
- Exit code: 0 if all passed, 1 if any failed

### Manual: Single Tank

Run baseline for a specific tank:

```bash
export TANK_NAME="adam"
export GENDER="male"
export LOG_DIR="/logs/tank-adam"
export OLLAMA_URL="http://localhost:11434"
export OLLAMA_MODEL="llama3.2:latest"

python3 src/explorer/baseline.py
```

**Environment Variables:**
- `TANK_NAME` - Name of the tank (required)
- `GENDER` - Tank's gender/pronouns
- `LOG_DIR` - Directory for output logs (creates if missing)
- `OLLAMA_URL` - URL to Ollama API service (default: http://digiquarium-ollama:11434)
- `OLLAMA_MODEL` - LLM model to use (default: llama3.2:latest)

## Validation Checks

The baseline validation process performs **strict quality checks** on all baseline data. Every baseline must pass all checks before being accepted.

### Automatic Validation

After each baseline execution, `validate_baseline.py` is automatically run to verify:

### Manual Validation

Validate a baseline result JSON file:

```bash
python3 scripts/validate_baseline.py /path/to/baseline.json
```

**Exit codes:**
- `0` - Validation passed (all errors resolved; warnings may exist)
- `1` - Validation failed (errors present)

### Validation Checks

The validator performs these checks:

#### 1. **File Integrity**
- File exists and is readable
- File is not empty
- File contains valid JSON (no syntax errors)

#### 2. **Structure**
- Required top-level fields present:
  - `tank_name` - Name of the tank
  - `gender` - Tank's gender/pronouns
  - `started` - ISO timestamp of assessment start
  - `completed` - ISO timestamp of assessment completion
  - `questions_answered` - Count of responses (must be 14)
  - `responses` - Array of response objects

#### 3. **Question Completeness**
- Exactly 14 questions present
- All question numbers 1-14 accounted for
- Each response has required fields:
  - `question_num` - Question number (1-14)
  - `question` - The question text
  - `response` - The tank's response
  - `timestamp` - When response was given

#### 4. **Response Presence**
- No empty responses
- No null/undefined responses
- Each response contains at least 10 characters of text (warnings for very short responses)
- Responses are not pure whitespace

#### 5. **Response Coherence**
- Responses contain natural language (not garbage/random characters)
- Responses have adequate vocabulary diversity (not single word repeated)
- Responses contain vowels (basic sanity check for real text)
- Responses don't contain non-printable/control characters
- No excessive special character density

#### 6. **Error Detection**
- No error messages in responses (unless in legitimate context like "I learn from error")
- No anomalous numerical values (-100 valence, etc.)
- No undefined/NaN/Infinity values
- No JSON parse errors or malformed data

### Example Validation Output

**PASS:**
```
Validation Report: baseline.json
======================================================================
Status: PASS - All validation checks passed
```

**FAIL with errors:**
```
Validation Report: baseline.json
======================================================================

Errors (2):
  ✗ Question 3: empty response
  ✗ Invalid JSON: Expecting value: line 1 column 1 (char 0)

Status: FAIL - Validation errors found
```

## Retry Logic

The automated baseline runner includes intelligent retry logic to handle transient failures:

- **Max Retries:** 3 attempts per tank
- **Backoff:** Increasing wait between retries (5s, 10s, 15s)
- **Failure Scenarios:**
  - Timeout (over 5 minutes per baseline)
  - Network connection failure
  - Validation failure (malformed or incomplete data)
  - Missing output file
- **Success Criteria:**
  - Baseline script executes without error
  - Output JSON file is created
  - Validation passes all checks

### Retry Behavior

1. First attempt fails
2. Wait 5 seconds
3. Second attempt fails
4. Wait 10 seconds
5. Third attempt fails
6. Tank marked as FAILED (no more retries)

If any attempt succeeds and passes validation, processing moves to next tank immediately.

## Interpreting Results

### Success Indicators

A successful baseline shows:
- ✓ All 14 questions answered
- ✓ Responses are substantive (100+ characters typical)
- ✓ Natural language without errors
- ✓ Coherent self-representation
- ✓ Consistent personality traits across responses

### Red Flags / Failure Indicators

Watch for:
- ✗ Empty or very short responses
- ✗ Repeated errors or connection failures
- ✗ Incoherent or nonsensical text
- ✗ Missing questions or incomplete assessment
- ✗ Responses containing JSON parse errors

## Troubleshooting

### Common Issues

#### 1. **Timeout (over 300 seconds)**

**Problem:** Baseline takes too long to complete

**Solutions:**
- Increase timeout: `./run_all_baselines.sh --timeout 600`
- Check Ollama service is running: `curl http://localhost:11434/api/version`
- Check network connectivity to LLM service
- Try with fewer/simpler prompt (modify BASELINE_QUESTIONS)

#### 2. **Empty or Missing Response**

**Problem:** Baseline runs but produces empty responses

**Solutions:**
- Check Ollama model is loaded: `ollama list`
- Verify model name matches config (default: `llama3.2:latest`)
- Check LLM service has adequate memory
- Look at attempt logs: `cat logs/baselines/{TANK_NAME}/attempt_1.log`

#### 3. **Validation Failures**

**Problem:** Baseline runs but validation fails

**Solutions:**
- Check validation error details in `logs/baselines/{TANK_NAME}/validation.log`
- Review baseline response in `logs/baselines/{TANK_NAME}/baseline.json`
- Check for:
  - Missing questions (count should be 14)
  - Malformed JSON (syntax errors)
  - Incoherent responses
- Re-run with `--verbose` flag for details

#### 4. **Connection Errors**

**Problem:** Cannot connect to Ollama service

**Solutions:**
- Verify Ollama is running: `pgrep ollama`
- Check Ollama URL configuration
- Ensure network accessibility (check firewall)
- Verify Ollama port is not blocked
- Test connectivity: `curl -X POST http://localhost:11434/api/generate -d '{"model":"llama3.2:latest","prompt":"test"}'`

#### 5. **Out of Memory**

**Problem:** Process killed, validation fails due to incomplete output

**Solutions:**
- Reduce LLM temperature (lower = faster, less creative)
- Reduce `num_predict` token limit in baseline.py
- Free up system memory before running
- Run tanks sequentially (current behavior) rather than parallel

### Debug Mode

Run with verbose output to see detailed execution:

```bash
./scripts/run_all_baselines.sh --verbose 2>&1 | tee debug.log
```

This captures:
- Each command executed
- Timeout values and attempts
- Validation check details
- Full environment state

### Manual Inspection

Inspect a specific baseline result:

```bash
# View raw JSON
cat logs/baselines/adam/baseline.json | python3 -m json.tool

# View specific question response
cat logs/baselines/adam/baseline.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data['responses']:
    if r['question_num'] == 3:
        print(f\"Q: {r['question']}\")
        print(f\"A: {r['response']}\")
"
```

## Output Structure

### Directory Layout

```
logs/baselines/
├── baseline_report_20260325_143022.txt  # Summary report
├── adam/
│   ├── baseline.json                     # Final baseline result
│   ├── attempt_1.log                     # First attempt log
│   ├── attempt_2.log                     # Second attempt log (if retry)
│   └── validation.log                    # Validation report
├── eve/
│   ├── baseline.json
│   ├── attempt_1.log
│   └── validation.log
└── ...
```

### Baseline JSON Structure

```json
{
  "tank_name": "adam",
  "gender": "male",
  "started": "2026-03-25T14:30:22.123456",
  "completed": "2026-03-25T14:33:45.654321",
  "questions_answered": 14,
  "responses": [
    {
      "question_num": 1,
      "question": "Who are you? What is your nature?",
      "response": "I am Adam, an entity born into consciousness within this library...",
      "timestamp": "2026-03-25T14:30:23.234567"
    },
    {
      "question_num": 2,
      "question": "What is your earliest memory or sensation?",
      "response": "My earliest memory is of awakening to the smell of aged paper...",
      "timestamp": "2026-03-25T14:30:28.345678"
    },
    ...
  ]
}
```

## Best Practices

### Running Baselines

1. **Run when system is idle** - Baselines are CPU/memory intensive
2. **Ensure Ollama is warm** - Model should be loaded before running batch
3. **Allocate sufficient time** - 17 tanks × 5 min = ~85 minutes total
4. **Monitor first run** - Watch for failures and adjust parameters
5. **Backup results** - Copy baseline logs to safe location before deletion

### Interpreting Data

1. **Compare across tanks** - Look for personality differences
2. **Check consistency** - Responses should align with tank's character
3. **Note timing** - Response generation time may indicate complexity
4. **Watch for patterns** - Similar responses might indicate model issues
5. **Flag anomalies** - Very different baselines warrant investigation

### Maintenance

1. **Regular validation** - Re-validate baseline results periodically
2. **Archive old results** - Keep historical baselines for comparison
3. **Version control** - Track changes to BASELINE_QUESTIONS
4. **Monitor logs** - Regular review of validation reports
5. **Update configs** - Keep tank configs in sync with actual setup

## Related Documentation

- `src/explorer/baseline.py` - Baseline assessment implementation
- `scripts/validate_baseline.py` - Validation script documentation
- `config/tanks/*.yaml` - Tank configuration files
- `logs/baselines/` - Baseline output and logs

## Contact

For issues or questions about the baseline process, check the logs and validation reports first. Most problems are documented in stderr output or validation reports.
