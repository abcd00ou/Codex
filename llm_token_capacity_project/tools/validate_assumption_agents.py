"""Validate the Markdown-based assumption agent system."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = ROOT / "agents"
ASSUMPTION_ROOT = AGENTS_ROOT / "assumptions"
DOCS_ROOT = ROOT / "docs" / "assumptions"

EXPECTED_AGENTS = [
    "A01_contracted_power_gw",
    "A02_active_power_gw",
    "A03_pue",
    "A04_ai_workload_share",
    "A05_inference_power_share",
    "A06_training_power_share",
    "A07_active_parameters",
    "A08_tokens_per_second_per_mw",
    "A09_utilization",
    "A10_attribution_rule",
]

REQUIRED_AGENT_FILES = ["README.md", "state.md", "evidence.md", "learning_queue.md"]

REQUIRED_SHARED_FILES = [
    "README.md",
    "shared/evidence_rules.md",
    "shared/source_quality.md",
    "shared/update_protocol.md",
    "orchestrator/README.md",
    "orchestrator/cycle_log.md",
]


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate() -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    for relative in REQUIRED_SHARED_FILES:
        path = AGENTS_ROOT / relative
        require(path.exists(), f"Missing shared/orchestrator file: {relative}", errors)
        if path.exists():
            require(path.stat().st_size > 200, f"Shared/orchestrator file too small: {relative}", errors)

    agent_dirs = sorted(path.name for path in ASSUMPTION_ROOT.glob("A*_*") if path.is_dir())
    require(agent_dirs == EXPECTED_AGENTS, f"Agent directories mismatch: {agent_dirs}", errors)

    for agent_name in EXPECTED_AGENTS:
        agent_dir = ASSUMPTION_ROOT / agent_name
        assumption_doc = DOCS_ROOT / f"{agent_name}.md"
        require(assumption_doc.exists(), f"Missing assumption textbook for {agent_name}", errors)

        for filename in REQUIRED_AGENT_FILES:
            path = agent_dir / filename
            require(path.exists(), f"Missing {filename} for {agent_name}", errors)
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            require(len(text) > 200, f"{agent_name}/{filename} is unexpectedly short", errors)

        readme = agent_dir / "README.md"
        state = agent_dir / "state.md"
        evidence = agent_dir / "evidence.md"
        queue = agent_dir / "learning_queue.md"

        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            require("Mission" in text, f"{agent_name}/README.md missing Mission", errors)
            require("Owned Field" in text, f"{agent_name}/README.md missing Owned Field", errors)
            require("Watchouts" in text, f"{agent_name}/README.md missing Watchouts", errors)

        if state.exists():
            text = state.read_text(encoding="utf-8")
            require("Proposed Changes" in text, f"{agent_name}/state.md missing Proposed Changes", errors)
            require("confidence" in text.lower(), f"{agent_name}/state.md missing confidence", errors)

        if evidence.exists():
            text = evidence.read_text(encoding="utf-8")
            require("Evidence Table" in text, f"{agent_name}/evidence.md missing Evidence Table", errors)
            require("evidence_class" in text, f"{agent_name}/evidence.md missing evidence_class", errors)

        if queue.exists():
            text = queue.read_text(encoding="utf-8")
            require("Next Agent Prompt" in text, f"{agent_name}/learning_queue.md missing Next Agent Prompt", errors)
            if "open |" not in text:
                warnings.append(f"{agent_name}/learning_queue.md has no open learning task")

    status = "PASS" if not errors else "FAIL"
    return {
        "status": status,
        "agent_count": len(agent_dirs),
        "expected_agent_count": len(EXPECTED_AGENTS),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
