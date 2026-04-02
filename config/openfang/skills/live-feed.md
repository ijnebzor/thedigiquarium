# Live Feed Skill
Exports real-time tank data for the website dashboard. Reads brain.md growth rates, thinking traces, and baseline status.
## Tools
- export_tank_metrics(tank_ids) -> metrics JSON
- export_brain_growth_chart(tank_id, days) -> chart data
- export_trace_summary(tank_id, date) -> summary
## When to use
- Every 15 minutes (scheduled)
- On demand for dashboard refresh
