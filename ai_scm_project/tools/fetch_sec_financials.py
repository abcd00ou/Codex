"""
Fetch compact SEC XBRL financial statement facts for the AI SCM universe.

The output is a normalized line-item database keyed by company, period, form,
and metric. It is intentionally compact enough for the HTML dashboard while
preserving links back to SEC filing metadata in data/sec_filings.json.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
FILINGS_PATH = DATA_DIR / "sec_filings.json"
OUT_PATH = DATA_DIR / "sec_financials.json"

SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_HEADERS = {
    "User-Agent": "ai-scm-project research dashboard contact@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}


METRIC_MAP = {
    "Revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"],
    "Operating income": ["OperatingIncomeLoss"],
    "Net income": ["NetIncomeLoss", "ProfitLoss"],
    "CapEx": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "PP&E net": ["PropertyPlantAndEquipmentNet"],
    "R&D": ["ResearchAndDevelopmentExpense"],
    "Inventory": ["InventoryNet"],
    "Operating cash flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "Free cash flow bridge": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}


def fetch_json(url: str) -> dict[str, Any]:
    request = Request(url, headers=SEC_HEADERS)
    with urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding") == "gzip" or body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def load_filings() -> dict[str, Any]:
    return json.loads(FILINGS_PATH.read_text(encoding="utf-8"))


def load_companyfacts(cik: str) -> dict[str, Any]:
    return fetch_json(SEC_COMPANYFACTS_URL.format(cik=cik))


def find_metric_facts(companyfacts: dict[str, Any], candidate_tags: list[str]) -> tuple[str | None, list[dict[str, Any]]]:
    facts = companyfacts.get("facts", {})
    for namespace in ("us-gaap", "ifrs-full"):
        namespace_facts = facts.get(namespace, {})
        for tag in candidate_tags:
            if tag not in namespace_facts:
                continue
            units = namespace_facts[tag].get("units", {})
            for unit_name in ("USD", "USD/shares", "shares", "pure"):
                if unit_name in units:
                    return f"{namespace}:{tag}:{unit_name}", units[unit_name]
            if units:
                first_unit, records = next(iter(units.items()))
                return f"{namespace}:{tag}:{first_unit}", records
    return None, []


def record_period(record: dict[str, Any]) -> str:
    fy = record.get("fy")
    fp = record.get("fp")
    if fy and fp:
        return f"{fy} {fp}"
    return record.get("end") or "undated"


def normalize_records(company: dict[str, Any], metric: str, tag_key: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for record in records:
        form = record.get("form")
        if form not in {"10-K", "10-Q", "20-F", "6-K"}:
            continue
        filed = record.get("filed", "")
        if filed and filed < "2021-01-01":
            continue
        value = record.get("val")
        if value is None:
            continue
        normalized.append({
            "company_id": company["company_id"],
            "company": company["company"],
            "ticker": company["ticker"],
            "node": company["node"],
            "cik": company["cik"],
            "metric": metric,
            "tag": tag_key,
            "form": form,
            "period": record_period(record),
            "fiscal_year": record.get("fy"),
            "fiscal_period": record.get("fp"),
            "start": record.get("start"),
            "end": record.get("end"),
            "filed": filed,
            "accession_number": record.get("accn"),
            "value": value,
            "unit": tag_key.rsplit(":", 1)[-1],
            "source_type": "SEC_XBRL_companyfacts",
        })

    normalized.sort(key=lambda item: (item.get("filed") or "", item.get("end") or ""), reverse=True)

    by_period: dict[tuple[str, str], dict[str, Any]] = {}
    for item in normalized:
        key = (item["form"], item["period"])
        if key not in by_period:
            by_period[key] = item
        if len(by_period) >= 12:
            break
    return list(by_period.values())


def build_database() -> dict[str, Any]:
    filing_db = load_filings()
    companies = [company for company in filing_db.get("companies", []) if company.get("status") == "fetched" and company.get("cik")]
    all_records: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []

    for company in companies:
        companyfacts = load_companyfacts(company["cik"])
        company_record_count = 0
        missing_metrics = []
        for metric, tags in METRIC_MAP.items():
            tag_key, records = find_metric_facts(companyfacts, tags)
            if not tag_key:
                missing_metrics.append(metric)
                continue
            normalized = normalize_records(company, metric, tag_key, records)
            company_record_count += len(normalized)
            all_records.extend(normalized)

        coverage.append({
            "company_id": company["company_id"],
            "company": company["company"],
            "ticker": company["ticker"],
            "node": company["node"],
            "cik": company["cik"],
            "record_count": company_record_count,
            "missing_metrics": missing_metrics,
        })
        time.sleep(0.12)

    all_records.sort(key=lambda item: (item.get("filed") or "", item.get("company") or "", item.get("metric") or ""), reverse=True)
    return {
        "metadata": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "source": "SEC XBRL companyfacts API",
            "companyfacts_url_template": SEC_COMPANYFACTS_URL,
            "metrics": list(METRIC_MAP),
            "note": "Compact financial statement facts for dashboard/model grounding; not a substitute for audited statement review.",
        },
        "coverage": coverage,
        "records": all_records,
    }


def main() -> None:
    database = build_database()
    OUT_PATH.write_text(json.dumps(database, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_PATH)
    print(f"companies={len(database['coverage'])} records={len(database['records'])}")


if __name__ == "__main__":
    main()
