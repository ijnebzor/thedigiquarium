# Beta Period Archive Manifest
## Archive Period: 2026-02-17 to 2026-02-23

**Archive Created:** 2026-03-25
**Purpose:** Complete backup of all beta-period data from February 2026 testing phase

---

## Archive Contents Summary

### Directories Archived

1. **tanks/** (35 files)
   - All tank data including traces, observations, thinking trails
   - Subdirectories: agent_baseline.py and all tank-specific files
   - Complete record of all specimen tank operations

2. **data/** (81 files)
   - JSON feeds: live-feed.json, live_stats.json
   - Tank status files: admin-status.json, tank-audit.json
   - Journey tracking: journey.json
   - Dashboard index files
   - All data feed files for the beta period

3. **operations/** (20 files)
   - orchestrator.py - operation orchestration script
   - scheduler.py - scheduling system
   - baseline_queue.json - baseline operation queue
   - agents/ directory - agent operation logs
   - calendar/ directory - operation calendar
   - reports/ directory - operation reports
   - translations/ directory - operation translations

4. **audits/** (16 files)
   - COMPREHENSIVE_AUDIT_20260223_0423.md
   - REALITY_CHECK_20260223_0351.md
   - link_audit_20260222_0155.md
   - website_audit_* files (9 files) - daily audit snapshots
   - broken_links_20260222.json
   - 20260220/ directory - February 20 audit files

5. **dashboard/** (2 files)
   - index.html - dashboard interface
   - live-data.js - dashboard data feed

6. **specimens/** (53 files)
   - CSV/JSON observation files for each specimen:
     - abel-graph.json, abel-timeseries.json, abel.html
     - adam-graph.json, adam-timeseries.json, adam.html
     - cain-graph.json, cain-timeseries.json, cain.html
     - eve-graph.json, eve-timeseries.json, eve.html
     - genevieve-graph.json, genevieve-timeseries.json, genevieve.html
     - haruki-graph.json, haruki-timeseries.json, haruki.html
     - iris-graph.json, iris-timeseries.json, iris.html
     - juan-graph.json, juan-timeseries.json, juan.html
     - juanita-graph.json, juanita-timeseries.json, juanita.html
     - klaus-graph.json, klaus-timeseries.json, klaus.html
     - mei-graph.json, mei-timeseries.json, mei.html
     - observer-graph.json, observer-timeseries.json, observer.html
     - sakura-graph.json, sakura-timeseries.json, sakura.html
     - seeker-graph.json, seeker-timeseries.json, seeker.html
     - seth-graph.json, seth-timeseries.json, seth.html
     - victor-graph.json, victor-timeseries.json, victor.html
     - wei-graph.json, wei-timeseries.json, wei.html
     - all-specimens-data.json - aggregated data
     - index.html

7. **incidents/** (1 file)
   - INC-20260222-OLLAMA-ZOMBIES.md - incident report

8. **beta-week1/** (3,817 files)
   - Existing archive containing all beta-week1 data
   - Organized by tank directories with discoveries and baselines subdirectories
   - Multiple baseline JSON files per tank
   - Complete discovery logs for each tank

### Root Level Analysis Documents (7 files)

- BASELINE_ANALYSIS_2026-02-20.md
- BASELINE_COMPARISON_FINAL_2026-02-20.md
- BASELINE_COMPARISON_REPORT_2026-02-20.md
- INCIDENT_REPORT_2026-02-21.md
- MODEL_COMPARISON_RESULTS.md
- OVERNIGHT_SUMMARY_2026-02-20.md
- WEEKLY_ANALYSIS_2026-02-20.md

---

## File Count Summary

| Directory | File Count |
|-----------|-----------|
| tanks | 35 |
| data | 81 |
| operations | 20 |
| audits | 16 |
| dashboard | 2 |
| specimens | 53 |
| incidents | 1 |
| beta-week1 | 3,817 |
| Root level docs | 7 |
| **TOTAL** | **4,032** |

---

## Date Ranges Covered

- **Primary Period:** February 17-23, 2026
- **Data Dates:** February 20-23, 2026 (most recent activity)
- **Audit Period:** February 20-23, 2026
- **Historical Data:** Includes beta-week1 data (February 17-23, 2026)

---

## Data Integrity Verification

- All files copied using `cp -r` (non-destructive copy)
- File count verified: Source and archive match
- No data loss - original files remain in source locations
- Archives include:
  - All tank traces and observations
  - All baseline results and analysis
  - All incident reports
  - All audit logs and website audits
  - All dashboard data
  - All specimen observation data
  - All operational records
  - Complete beta-week1 historical archive

---

## Archive Purpose

This archive preserves all data generated during the beta testing period (February 17-23, 2026) including:
- Tank system performance data
- Specimen observations and behavior logs
- Baseline measurements and comparisons
- Incident reports and audits
- Operational logs and scheduling records
- Analysis and findings from the beta period

All data has been preserved in its original state for historical reference, compliance, and potential future analysis.

---

**Archive Location:** `/sessions/modest-intelligent-noether/thedigiquarium/archive/beta-period-2026-02-17-to-2026-02-23/`

**Archive Status:** COMPLETE - No data loss

