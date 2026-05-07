# AI SCM Intelligence System

AI supply-chain intelligence project for mapping token demand into GPU, HBM, CoWoS, power, networking, and investment signals.

## What is included

- Multi-agent analysis pipeline in `run.py`
- Daily learning and quiz workflow in `run_daily.py`
- Topic study document generator in `run_study.py`
- Newsletter generator in `run_newsletter.py`
- Report builders for HTML, PPTX, and DOCX outputs
- Supply-demand dynamics simulator in `agents/dynamics_agent.py`
- Project skill for agentic coding workflow in `skills/agentic-coding-workflow/`
- Seed and cached state data under `data/`

## Setup

```bash
cd "/Users/idongseong/Documents/New project/ai_scm_project"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` if you want email delivery or PostgreSQL persistence. The analysis/report commands can run without email credentials.

## Common commands

```bash
# Fast pipeline using cached/seed data
python run.py --quick

# Regenerate reports from existing cached analysis
python run.py --report-only

# Skip supply intelligence collection
python run.py --quick --skip-supply

# Daily learning status
python run_daily.py --status

# Save daily email HTML instead of sending email
python run_daily.py --morning --dry-run

# Generate the next study document
python run_study.py

# Generate newsletter HTML without sending email
python run_newsletter.py --dry-run

# Run only the numeric supply-demand dynamics model
python agents/dynamics_agent.py

# Validate formula evidence and model confidence
python tools/validate_model_evidence.py

# Regenerate the global dynamics report
python tools/generate_global_dynamics_report.py
```

## Agentic coding workflow

This project is organized for agent-assisted development. Use the project skill at `skills/agentic-coding-workflow/SKILL.md` for nontrivial edits.

The working loop is:

```text
intent -> inline plan -> smallest useful implementation -> verification -> simplification -> handoff
```

Formula and report changes should pass the quality gates in `docs/agentic_coding_workflow.md` and `AGENTS.md`.

## Notes

- Generated reports are written to `outputs/reports`, `outputs/pptx`, and `outputs/final`.
- The dynamics simulator writes `data/dynamics_state.json` with scenario-level demand, supply, gap ratios, limiting layer, fulfillment rate, backlog, and price-pressure indexes.
- The current dynamics model combines token-driven utilization demand with CapEx-implied procurement demand, then maps demand into accelerator, HBM, CoWoS, power, networking, and storage requirements.
- `AI_SCM_DB` is optional. If PostgreSQL is unavailable, the DB agent falls back without stopping the pipeline.
- Gmail sending requires `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, and optionally `GMAIL_RECIPIENT`.
