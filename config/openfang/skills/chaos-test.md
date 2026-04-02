# Chaos Testing Skill
Injects controlled failures to test system resilience. Kills random daemons, pauses tanks, simulates inference failures.
## Tools
- kill_random_daemon() -> daemon name
- pause_random_tank(duration_seconds) -> tank name
- simulate_inference_failure(duration_seconds)
- verify_self_healing(timeout_seconds) -> report
## When to use
- Scheduled weekly resilience test
- After infrastructure changes
- Before migration to verify recovery
## Guardrails
- Never kill overseer or ollama_watcher
- Max 1 tank paused at a time
- Require approval for multi-failure scenarios
