"""
Add SEC filing anchors from data/sec_filings.json to model_evidence.json.

This does not change coefficient values. It strengthens traceability by
linking provisional coefficients to company filing anchors that should be
parsed in the next model-upgrade step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
EVIDENCE_PATH = DATA_DIR / "model_evidence.json"
SEC_PATH = DATA_DIR / "sec_filings.json"
FINANCIALS_PATH = DATA_DIR / "sec_financials.json"


PRIMARY_FORMS = {"10-Q", "10-K", "20-F", "6-K"}


SOURCE_TARGETS = {
    "microsoft": "SRC_SEC_MSFT_LATEST_PRIMARY",
    "amazon": "SRC_SEC_AMZN_LATEST_PRIMARY",
    "alphabet": "SRC_SEC_GOOGL_LATEST_PRIMARY",
    "meta": "SRC_SEC_META_LATEST_PRIMARY",
    "oracle": "SRC_SEC_ORCL_LATEST_PRIMARY",
    "nvidia": "SRC_SEC_NVDA_LATEST_PRIMARY",
    "amd": "SRC_SEC_AMD_LATEST_PRIMARY",
    "micron": "SRC_SEC_MU_LATEST_PRIMARY",
    "broadcom": "SRC_SEC_AVGO_LATEST_PRIMARY",
    "marvell": "SRC_SEC_MRVL_LATEST_PRIMARY",
    "arista": "SRC_SEC_ANET_LATEST_PRIMARY",
    "cisco": "SRC_SEC_CSCO_LATEST_PRIMARY",
    "vertiv": "SRC_SEC_VRT_LATEST_PRIMARY",
    "eaton": "SRC_SEC_ETN_LATEST_PRIMARY",
    "ge_vernova": "SRC_SEC_GEV_LATEST_PRIMARY",
    "tsmc": "SRC_SEC_TSM_LATEST_PRIMARY",
}


COEFFICIENT_LINKS = {
    "COEF_CAPEX_AI_INFRA_SHARE": [
        "SRC_SEC_MSFT_LATEST_PRIMARY",
        "SRC_SEC_AMZN_LATEST_PRIMARY",
        "SRC_SEC_GOOGL_LATEST_PRIMARY",
        "SRC_SEC_META_LATEST_PRIMARY",
        "SRC_SEC_ORCL_LATEST_PRIMARY",
    ],
    "COEF_CAPEX_ACCELERATOR_SHARE": [
        "SRC_SEC_MSFT_LATEST_PRIMARY",
        "SRC_SEC_AMZN_LATEST_PRIMARY",
        "SRC_SEC_GOOGL_LATEST_PRIMARY",
        "SRC_SEC_META_LATEST_PRIMARY",
        "SRC_SEC_NVDA_LATEST_PRIMARY",
        "SRC_SEC_AMD_LATEST_PRIMARY",
    ],
    "COEF_AVG_ACCELERATOR_ASP_USD": [
        "SRC_SEC_NVDA_LATEST_PRIMARY",
        "SRC_SEC_AMD_LATEST_PRIMARY",
    ],
    "COEF_COWOS_WPM_PER_ACCELERATOR": [
        "SRC_SEC_NVDA_LATEST_PRIMARY",
        "SRC_SEC_AMD_LATEST_PRIMARY",
        "SRC_SEC_TSM_LATEST_PRIMARY",
    ],
    "COEF_NETWORK_TBPS_PER_ACCELERATOR": [
        "SRC_SEC_AVGO_LATEST_PRIMARY",
        "SRC_SEC_MRVL_LATEST_PRIMARY",
        "SRC_SEC_ANET_LATEST_PRIMARY",
        "SRC_SEC_CSCO_LATEST_PRIMARY",
    ],
    "COEF_RAG_STORAGE_RATIO": [
        "SRC_SEC_MSFT_LATEST_PRIMARY",
        "SRC_SEC_AMZN_LATEST_PRIMARY",
        "SRC_SEC_GOOGL_LATEST_PRIMARY",
        "SRC_SEC_META_LATEST_PRIMARY",
    ],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_primary_filings(sec_db: dict[str, Any]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for filing in sec_db.get("filings", []):
        if filing.get("form") not in PRIMARY_FORMS:
            continue
        company_id = filing.get("company_id")
        if not company_id or company_id in latest:
            continue
        latest[company_id] = filing
    return latest


def source_from_filing(source_id: str, filing: dict[str, Any]) -> dict[str, Any]:
    return {
        "publisher": "SEC EDGAR",
        "title": f"{filing['company']} {filing['form']} filing for {filing.get('period', 'period n/a')}",
        "url": filing["sec_url"],
        "observations": {
            "company": filing["company"],
            "ticker": filing["ticker"],
            "cik": filing["cik"],
            "form": filing["form"],
            "filing_date": filing.get("filing_date"),
            "report_date": filing.get("report_date"),
            "period": filing.get("period"),
            "accession_number": filing.get("accession_number"),
            "primary_document": filing.get("primary_document"),
            "source_id": source_id,
        },
        "derivation_type": "direct_company_filing_metadata",
        "confidence": 0.95,
    }


def add_unique(existing: list[str], additions: list[str], available_sources: set[str]) -> list[str]:
    merged = list(existing)
    for source_id in additions:
        if source_id in available_sources and source_id not in merged:
            merged.append(source_id)
    return merged


def main() -> None:
    evidence = load_json(EVIDENCE_PATH)
    sec_db = load_json(SEC_PATH)
    financials_db = load_json(FINANCIALS_PATH) if FINANCIALS_PATH.exists() else {}
    latest = latest_primary_filings(sec_db)
    sources = evidence.setdefault("sources", {})

    filings = sec_db.get("filings", [])
    form_counts: dict[str, int] = {}
    for filing in filings:
        form = filing.get("form", "unknown")
        form_counts[form] = form_counts.get(form, 0) + 1

    sources["SRC_SEC_FILINGS_DB_20260504"] = {
        "publisher": "SEC EDGAR",
        "title": "AI SCM company filing metadata database",
        "url": "data/sec_filings.json",
        "observations": {
            "generated_at": sec_db.get("metadata", {}).get("generated_at"),
            "company_count": len(sec_db.get("companies", [])),
            "filing_count": len(filings),
            "form_counts": form_counts,
            "domestic_issuer_forms": ["10-K", "10-Q"],
            "foreign_private_issuer_forms": ["20-F", "6-K"],
            "note": "Metadata DB. Full statement line-item extraction is a next-stage parser task.",
        },
        "derivation_type": "direct_sec_metadata_database",
        "confidence": 0.95,
    }

    if financials_db:
        sources["SRC_SEC_FINANCIALS_DB_20260504"] = {
            "publisher": "SEC XBRL companyfacts",
            "title": "AI SCM company financial statement facts database",
            "url": "data/sec_financials.json",
            "observations": {
                "generated_at": financials_db.get("metadata", {}).get("generated_at"),
                "company_count": len(financials_db.get("coverage", [])),
                "record_count": len(financials_db.get("records", [])),
                "metrics": financials_db.get("metadata", {}).get("metrics", []),
                "note": "Compact XBRL line-item DB for revenue, operating income, net income, CapEx, PP&E, R&D, inventory, and operating cash flow.",
            },
            "derivation_type": "direct_sec_xbrl_financial_statement_database",
            "confidence": 0.95,
        }

    for company_id, source_id in SOURCE_TARGETS.items():
        filing = latest.get(company_id)
        if filing:
            sources[source_id] = source_from_filing(source_id, filing)

    available_sources = set(sources)
    for coefficient_id, additions in COEFFICIENT_LINKS.items():
        coefficient = evidence.get("coefficients", {}).get(coefficient_id)
        if not coefficient:
            continue
        coefficient["evidence_ids"] = add_unique(coefficient.get("evidence_ids", []), additions, available_sources)
        coefficient["evidence_ids"] = add_unique(coefficient.get("evidence_ids", []), ["SRC_SEC_FINANCIALS_DB_20260504"], available_sources)
        replacement_path = coefficient.get("replacement_path", "")
        if "sec_filings.json" not in replacement_path:
            coefficient["replacement_path"] = (
                replacement_path
                + " Next: parse `data/sec_filings.json` filing URLs into company-quarter CapEx, segment revenue, PP&E, lease, inventory, and backlog line items."
            ).strip()

    evidence.setdefault("filing_database", {})["sec_filings"] = {
        "path": "data/sec_filings.json",
        "generated_at": sec_db.get("metadata", {}).get("generated_at"),
        "forms_included": sec_db.get("metadata", {}).get("forms_included", []),
        "filing_count": len(filings),
        "company_count": len(sec_db.get("companies", [])),
        "model_upgrade_status": "metadata_linked_line_item_extraction_pending",
    }
    if financials_db:
        evidence.setdefault("filing_database", {})["sec_financials"] = {
            "path": "data/sec_financials.json",
            "generated_at": financials_db.get("metadata", {}).get("generated_at"),
            "metrics": financials_db.get("metadata", {}).get("metrics", []),
            "record_count": len(financials_db.get("records", [])),
            "company_count": len(financials_db.get("coverage", [])),
            "model_upgrade_status": "financial_line_items_linked_metric_normalization_pending",
        }

    save_json(EVIDENCE_PATH, evidence)
    print(EVIDENCE_PATH)
    print(f"added_sources={1 + sum(1 for cid in SOURCE_TARGETS if cid in latest)}")


if __name__ == "__main__":
    main()
