# TinyFish Browse Skill
Enables controlled internet access for experimental tanks via TinyFish API. Mediates all web requests — tanks never touch the internet directly.
## Tools
- browse_url(url, goal) -> page content
- search_web(query) -> results
- extract_article(url) -> clean text
## Configuration
- API key: TINYFISH_API_KEY from .env
- Endpoint: https://agent.tinyfish.ai/v1/automation/run-sse
- Rate limit: 100 requests/day per tank
## When to use
- Experimental tanks with internet access (News Diet, Social Mirror, Cultural Exchange)
- Automated website QA testing
## Guardrails
- All requests logged
- Content filtered before reaching tank
- No access to social media login pages
- No PII collection
