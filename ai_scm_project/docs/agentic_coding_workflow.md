# Agentic Coding Workflow for AI SCM

This project uses an agentic coding workflow: large natural-language code actions, reviewed through evidence, tests, generated artifacts, and browser-visible outputs.

## Working Rules

1. Start from success criteria.
2. Use a lightweight inline plan for substantial changes.
3. Keep formulas and model coefficients evidence-linked.
4. Verify generated outputs, not just code syntax.
5. Simplify after the first working implementation.
6. Preserve unrelated user edits and comments.

## Project Quality Gates

Run these after model/formula/report changes:

```bash
.venv/bin/python -B -m compileall -q agents/dynamics_agent.py tools/generate_global_dynamics_report.py tools/validate_model_evidence.py
.venv/bin/python agents/dynamics_agent.py
.venv/bin/python tools/validate_model_evidence.py
.venv/bin/python tools/generate_global_dynamics_report.py
```

## Confidence Policy

The project should distinguish:

- **Model structure**: directional and often reliable.
- **Direct evidence**: product specs, filings, official company numbers.
- **Derived coefficients**: useful for scenario work but not investment-grade until validated.
- **Assumptions**: allowed only with sensitivity ranges and replacement paths.

## Skill Location

The reusable project skill lives at:

```text
skills/agentic-coding-workflow/SKILL.md
```

Use it when asking Codex to make nontrivial changes to this project.
