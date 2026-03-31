# Together.ai API Key Verification
**Date:** 2026-03-31
**Key prefix:** tgp_v1_MTjCmiv6...
**Tested from:** tank-01-adam container via docker exec

## Result: FAILED
- **HTTP Status:** 403 Forbidden
- **Error Code:** 1010 (Cloudflare access denied)
- **Endpoint:** https://api.together.xyz/v1/chat/completions
- **Model tested:** meta-llama/Llama-3.3-70B-Instruct-Turbo

## Analysis
The key is rejected at the Cloudflare layer (error 1010), which typically means:
1. The API key has been revoked or expired
2. The request is being blocked by Cloudflare's bot protection from the container's IP
3. The account may have been suspended

## Impact
The inference chain (Cerebras → Together → Groq → Ollama) will skip Together.ai and fall through to Groq, then Ollama as failsafe. No service disruption expected — the chain is designed to handle provider failures gracefully.

## Action Required
- Generate a new Together.ai API key at https://api.together.xyz/settings/api-keys
- Update .env with the new TOGETHER_API_KEY value
- Restart containers: `docker compose up -d`
