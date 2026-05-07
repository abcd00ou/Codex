"""
Validate model evidence and produce an audit report.

This does not prove the model is correct. It makes model risk explicit:
missing evidence, low-confidence coefficients, provisional formulas, and
priority upgrades needed before investment-grade use.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs" / "reports"
EVIDENCE_PATH = DATA_DIR / "model_evidence.json"


def load_evidence() -> dict[str, Any]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def trust_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "investment_grade_candidate"
    if confidence >= 0.50:
        return "scenario_grade"
    return "research_only"


def validate(evidence: dict[str, Any]) -> dict[str, Any]:
    sources = evidence.get("sources", {})
    coefficients = evidence.get("coefficients", {})
    rules = evidence.get("validation_rules", {})
    required = rules.get("required_coefficient_fields", [])

    coefficient_audit = []
    issues = []
    for cid, coef in coefficients.items():
        missing_fields = [field for field in required if field not in coef]
        missing_sources = [
            source_id
            for source_id in coef.get("evidence_ids", [])
            if source_id not in sources
        ]
        confidence = float(coef.get("confidence", 0))
        status = coef.get("validation_status", "unspecified")
        label = trust_label(confidence)
        coefficient_audit.append({
            "coefficient_id": cid,
            "confidence": confidence,
            "trust_label": label,
            "validation_status": status,
            "audit_priority": coef.get("audit_priority", "unspecified"),
            "missing_fields": missing_fields,
            "missing_sources": missing_sources,
            "sensitivity_range": coef.get("sensitivity_range"),
            "replacement_path": coef.get("replacement_path", ""),
        })
        if missing_fields:
            issues.append({
                "severity": "error",
                "coefficient_id": cid,
                "issue": f"missing fields: {', '.join(missing_fields)}",
            })
        if missing_sources:
            issues.append({
                "severity": "error",
                "coefficient_id": cid,
                "issue": f"references missing sources: {', '.join(missing_sources)}",
            })
        if confidence < rules.get("low_confidence_threshold", 0.5):
            issues.append({
                "severity": "warning",
                "coefficient_id": cid,
                "issue": "low confidence; use for scenario exploration only",
            })
        if status in {"assumption", "calibrated_placeholder", "derived_proxy"}:
            issues.append({
                "severity": "notice",
                "coefficient_id": cid,
                "issue": f"validation status is {status}",
            })

    summary = {
        "total_coefficients": len(coefficients),
        "investment_grade_candidate": sum(1 for c in coefficient_audit if c["trust_label"] == "investment_grade_candidate"),
        "scenario_grade": sum(1 for c in coefficient_audit if c["trust_label"] == "scenario_grade"),
        "research_only": sum(1 for c in coefficient_audit if c["trust_label"] == "research_only"),
        "critical_audit_items": [
            c["coefficient_id"]
            for c in coefficient_audit
            if c["audit_priority"] == "critical"
        ],
        "issue_count": len(issues),
        "blocking_error_count": sum(1 for item in issues if item["severity"] == "error"),
    }
    return {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "coefficient_audit": coefficient_audit,
        "issues": issues,
    }


def render_markdown(audit: dict[str, Any]) -> str:
    rows = [
        "| Coefficient | Confidence | Trust Label | Status | Priority | Sensitivity Range | Upgrade Path |",
        "|---|---:|---|---|---|---|---|",
    ]
    for item in audit["coefficient_audit"]:
        rows.append(
            "| {cid} | {conf:.0%} | {label} | {status} | {priority} | {rng} | {path} |".format(
                cid=f"`{item['coefficient_id']}`",
                conf=item["confidence"],
                label=item["trust_label"],
                status=item["validation_status"],
                priority=item["audit_priority"],
                rng=item["sensitivity_range"],
                path=item["replacement_path"],
            )
        )

    issues = [
        "| Severity | Coefficient | Issue |",
        "|---|---|---|",
    ]
    for item in audit["issues"]:
        issues.append(
            f"| {item['severity']} | `{item['coefficient_id']}` | {item['issue']} |"
        )

    summary = audit["summary"]
    return f"""# AI SCM Model Evidence Validation

Generated: {audit['generated_at']}

## Summary

- Total coefficients: {summary['total_coefficients']}
- Investment-grade candidates: {summary['investment_grade_candidate']}
- Scenario-grade coefficients: {summary['scenario_grade']}
- Research-only coefficients: {summary['research_only']}
- Blocking errors: {summary['blocking_error_count']}
- Critical audit items: {', '.join(summary['critical_audit_items'])}

## Coefficient Audit

{chr(10).join(rows)}

## Issues

{chr(10).join(issues)}

## Interpretation

The model structure is usable for scenario analysis, but coefficients marked
`research_only` should not be treated as investment-grade. The highest-priority
upgrade path is:

1. Replace blended accelerator ASP with an explicit H100/H200/B200/GB200 shipment and ASP bridge.
2. Replace CoWoS normalized coefficient with package-area/yield/wafer-throughput math.
3. Split AI CapEx into building, power, networking, accelerator, storage, CPU/ASIC, and lease components by company-quarter.
4. Split network demand into scale-up NVLink and scale-out InfiniBand/Ethernet topology.
"""


def main() -> None:
    evidence = load_evidence()
    audit = validate(evidence)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "model_evidence_validation.json"
    md_path = OUT_DIR / "model_evidence_validation.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
