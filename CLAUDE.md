
## Security
- Security is constitutional — the #1 priority. Pause features if compromised.
- All tanks: isolated network (no internet), non-root (UID 1000), read-only filesystem, seccomp BPF profiles, all capabilities dropped.
- API keys: only in inference proxy container, never in tank environment.
- SecureClaw v2 in all system prompts (explorer, openclaw, zeroclaw, picobot).
- Memory dedup at 60% word-overlap threshold. Output sanitization on all traces.
- Null traces never logged — no thought = no trace.
- ISO 27001 + NIST CSF v2 dual-pass audited.
- Shift left: every phase gets pre-phase and post-phase security audit.
