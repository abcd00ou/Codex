# AI SCM Agent Instructions

Use the project skill at `skills/agentic-coding-workflow/SKILL.md` for nontrivial changes.

## Default Loop

```text
intent -> inline plan -> implementation -> verification -> simplification -> handoff
```

## Formula and Evidence Work

When changing formulas, coefficients, dynamics, reports, or Excel model outputs:

1. Update `data/model_evidence.json` before changing dependent calculations.
2. Keep every coefficient evidence-linked with confidence, validation status, sensitivity range, audit priority, and replacement path.
3. Regenerate outputs in this order:

```bash
.venv/bin/python agents/dynamics_agent.py
.venv/bin/python tools/validate_model_evidence.py
.venv/bin/python tools/generate_global_dynamics_report.py
```

4. Verify generated artifacts, not just source code.

## Coding Style

- Prefer the smallest correct implementation first.
- Avoid abstraction bloat.
- Preserve unrelated user edits and comments.
- Surface confidence gaps and assumptions instead of hiding them.
- Treat generated reports and spreadsheets as artifacts that must be checked.
