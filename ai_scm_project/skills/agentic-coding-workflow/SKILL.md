---
name: agentic-coding-workflow
description: Use when modifying this project with LLM coding agents, especially for multi-file changes, model/report generation, evidence-backed formulas, browser-verifiable outputs, refactors, or any task where Codex should plan lightly, implement in large code actions, verify with tests/artifacts, avoid overengineering, and preserve user code.
---

# Agentic Coding Workflow

## Operating Posture

Use English/Korean natural-language programming for leverage, but keep a skeptical IDE-style review loop. Treat the agent as powerful, tireless, and fallible.

Default to this loop:

```text
intent -> inline plan -> smallest useful implementation -> verification -> simplification -> handoff
```

Prefer declarative success criteria over long imperative step lists. When the user gives a goal, translate it into observable completion checks before editing.

## Inline Plan Mode

Use a lightweight plan before substantial edits:

1. State the target outcome in one sentence.
2. Name the files or surfaces likely to change.
3. Name the verification checks.
4. Call out assumptions that could be wrong.

Do not over-plan. If the change is small, one or two sentences are enough.

## Guardrails

- Check assumptions before running with them.
- Surface contradictions, missing data, and confidence gaps.
- Push back when the requested model, formula, or abstraction is not yet evidence-grade.
- Do not silently remove comments, dead-looking code, generated outputs, or user edits unless the task requires it.
- Avoid abstraction bloat. Build the simple version first, then generalize only when the repeated pattern is real.
- Prefer a correct naive algorithm before optimization.
- Prefer evidence-linked formulas over “nice looking” formulas.
- Make model confidence explicit: structure can be trusted more than provisional coefficients.

## Project-Specific Workflow

For this AI SCM project:

1. Read the current source of truth before changing behavior:
   - `data/model_evidence.json`
   - `data/dynamics_state.json`
   - `agents/dynamics_agent.py`
   - `tools/generate_global_dynamics_report.py`
   - `docs/model_methodology.md`
2. If changing formulas or coefficients, update `model_evidence.json` first.
3. Every coefficient must include:
   - `evidence_ids`
   - `confidence`
   - `validation_status`
   - `sensitivity_range`
   - `audit_priority`
   - `replacement_path`
4. Run the evidence validator after formula or coefficient changes:

```bash
.venv/bin/python tools/validate_model_evidence.py
```

5. Regenerate dependent outputs in order:

```bash
.venv/bin/python agents/dynamics_agent.py
.venv/bin/python tools/validate_model_evidence.py
.venv/bin/python tools/generate_global_dynamics_report.py
```

6. If the browser is open to a generated report, reload and verify the relevant DOM text or visual section.

## Verification Ladder

Use the cheapest sufficient check, but do not skip verification.

- Syntax: `python -m compileall` for changed Python modules.
- Evidence: `tools/validate_model_evidence.py`.
- Model: run `agents/dynamics_agent.py`.
- Report: run `tools/generate_global_dynamics_report.py`.
- Browser: verify generated HTML sections and graph visibility when relevant.
- Spreadsheet: inspect formulas/errors and render key sheets when changing `.xlsx`.

## Simplification Pass

Before final handoff, ask:

- Can this be 100 lines instead of 1000?
- Did I add an abstraction before the shape was proven?
- Did I leave dead code, stale generated files, or duplicated logic?
- Did I preserve user edits outside the task?
- Did the final answer distinguish verified facts from assumptions?

## Reference

For the source essay that motivated this workflow, read `references/agentic-coding-notes.md` only when you need the original philosophy or wording.
