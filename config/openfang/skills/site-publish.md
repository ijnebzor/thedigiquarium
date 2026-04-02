# Site Publisher Skill
Manages git operations for the Digiquarium website. Runs quality checks before pushing. Generates live feed data and dashboard metrics.
## Tools
- git_add_commit_push(files, message)
- validate_html(path) -> errors
- generate_live_feed() -> live-feed.json
- update_dashboard_data() -> stats.json
## When to use
- After any content generation (specimen pages, congregation transcripts)
- On schedule (every 15 min for live feed)
- Before any push to main
