"""
Fetch SEC filing metadata for the AI supply-chain company universe.

This stores filing metadata only. It does not scrape full 10-K/10-Q text.
The output is used as a dated filing database for model evidence and the
interactive supply-chain dashboard.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_PATH = DATA_DIR / "sec_filings.json"

SEC_HEADERS = {
    "User-Agent": "ai-scm-project research dashboard contact@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{primary_doc}"
SEC_BROWSE_URL = "https://www.sec.gov/edgar/browse/?CIK={ticker}"


COMPANY_UNIVERSE = [
    {"company_id": "microsoft", "company": "Microsoft", "ticker": "MSFT", "node": "microsoft", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "amazon", "company": "Amazon", "ticker": "AMZN", "node": "aws", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "alphabet", "company": "Alphabet", "ticker": "GOOGL", "node": "google", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "meta", "company": "Meta Platforms", "ticker": "META", "node": "meta", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "oracle", "company": "Oracle", "ticker": "ORCL", "node": "oracle", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "nvidia", "company": "NVIDIA", "ticker": "NVDA", "node": "nvidia", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "amd", "company": "AMD", "ticker": "AMD", "node": "amd", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "micron", "company": "Micron", "ticker": "MU", "node": "micron", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "broadcom", "company": "Broadcom", "ticker": "AVGO", "node": "networking", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "marvell", "company": "Marvell", "ticker": "MRVL", "node": "networking", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "arista", "company": "Arista Networks", "ticker": "ANET", "node": "networking", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "cisco", "company": "Cisco", "ticker": "CSCO", "node": "networking", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "vertiv", "company": "Vertiv", "ticker": "VRT", "node": "power", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "eaton", "company": "Eaton", "ticker": "ETN", "node": "power", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "ge_vernova", "company": "GE Vernova", "ticker": "GEV", "node": "power", "reporting_basis": "US_SEC_10K_10Q"},
    {"company_id": "tsmc", "company": "TSMC", "ticker": "TSM", "node": "tsmc", "reporting_basis": "SEC_foreign_private_issuer_20F_6K"},
    {"company_id": "sk_hynix", "company": "SK Hynix", "ticker": "000660.KS", "node": "sk_hynix", "reporting_basis": "non_US_DART_IR"},
    {"company_id": "samsung", "company": "Samsung Electronics", "ticker": "005930.KS", "node": "samsung", "reporting_basis": "non_US_DART_IR"},
    {"company_id": "coreweave", "company": "CoreWeave", "ticker": "CRWV", "node": "coreweave", "reporting_basis": "US_SEC_if_public"},
]


PRIMARY_FORMS = {"10-K", "10-Q", "20-F", "6-K"}
MODEL_RELEVANT_FORMS = {"10-K", "10-Q", "20-F", "6-K", "8-K"}


def fetch_json(url: str, host: str = "data.sec.gov") -> dict[str, Any]:
    headers = dict(SEC_HEADERS)
    headers["Host"] = host
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding") == "gzip" or body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def cik_from_ticker(ticker_map: dict[str, Any], ticker: str) -> str | None:
    ticker_upper = ticker.upper()
    for item in ticker_map.values():
        if item.get("ticker", "").upper() == ticker_upper:
            return f"{int(item['cik_str']):010d}"
    return None


def period_label(form: str, report_date: str) -> str:
    if not report_date:
        return "undated"
    try:
        date_value = dt.date.fromisoformat(report_date)
    except ValueError:
        return report_date
    if form in {"10-K", "20-F"}:
        return f"FY{date_value.year}"
    quarter = ((date_value.month - 1) // 3) + 1
    return f"{date_value.year} Q{quarter}"


def normalize_accession(accession: str) -> str:
    return accession.replace("-", "")


def extract_filings(company: dict[str, str], submissions: dict[str, Any], limit_per_form: int = 8) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])
    cik = str(submissions.get("cik", "")).zfill(10)
    cik_int = str(int(cik)) if cik.isdigit() else cik

    counts: dict[str, int] = {}
    filings: list[dict[str, Any]] = []
    for index, form in enumerate(forms):
        if form not in MODEL_RELEVANT_FORMS:
            continue
        if counts.get(form, 0) >= limit_per_form:
            continue
        accession = accession_numbers[index]
        primary_doc = primary_docs[index]
        report_date = report_dates[index] if index < len(report_dates) else ""
        filing_date = filing_dates[index] if index < len(filing_dates) else ""
        filing = {
            "company_id": company["company_id"],
            "company": company["company"],
            "ticker": company["ticker"],
            "node": company["node"],
            "cik": cik,
            "form": form,
            "filing_date": filing_date,
            "report_date": report_date,
            "period": period_label(form, report_date),
            "accession_number": accession,
            "primary_document": primary_doc,
            "description": descriptions[index] if index < len(descriptions) else "",
            "sec_url": SEC_ARCHIVE_URL.format(cik_int=cik_int, accession=normalize_accession(accession), primary_doc=primary_doc),
            "filing_index_url": SEC_BROWSE_URL.format(ticker=company["ticker"]),
            "source_type": "SEC_EDGAR",
            "model_use": "company_filing_anchor",
        }
        filings.append(filing)
        counts[form] = counts.get(form, 0) + 1

    return filings


def placeholder_company(company: dict[str, str], reason: str) -> dict[str, Any]:
    return {
        **company,
        "cik": None,
        "status": "not_fetched",
        "reason": reason,
        "filings": [],
        "notes": (
            "10-K/10-Q are SEC domestic issuer forms. Use 20-F/6-K for SEC foreign private issuers "
            "or local exchange/DART/IR filings for non-US reporters."
        ),
    }


def build_database() -> dict[str, Any]:
    ticker_map = fetch_json(SEC_COMPANY_TICKERS_URL, host="www.sec.gov")
    companies: list[dict[str, Any]] = []
    filing_items: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []

    for company in COMPANY_UNIVERSE:
        reporting_basis = company["reporting_basis"]
        ticker = company["ticker"]
        if reporting_basis == "non_US_DART_IR":
            companies.append(placeholder_company(company, "non_us_company_use_dart_or_ir"))
            continue

        cik = cik_from_ticker(ticker_map, ticker)
        if not cik:
            companies.append(placeholder_company(company, "ticker_not_found_in_sec_company_tickers"))
            issues.append({"ticker": ticker, "issue": "ticker_not_found"})
            continue

        try:
            submissions = fetch_json(SEC_SUBMISSIONS_URL.format(cik=cik))
        except (HTTPError, URLError, TimeoutError) as exc:
            companies.append(placeholder_company(company, f"sec_fetch_failed: {exc}"))
            issues.append({"ticker": ticker, "issue": f"sec_fetch_failed: {exc}"})
            continue

        filings = extract_filings(company, submissions)
        primary_count = sum(1 for filing in filings if filing["form"] in PRIMARY_FORMS)
        companies.append({
            **company,
            "cik": cik,
            "entity_name": submissions.get("name"),
            "sic": submissions.get("sic"),
            "sic_description": submissions.get("sicDescription"),
            "status": "fetched",
            "primary_filing_count": primary_count,
            "filings": filings,
        })
        filing_items.extend(filings)
        time.sleep(0.12)

    return {
        "metadata": {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "source": "SEC EDGAR submissions API and SEC company_tickers.json",
            "company_tickers_url": SEC_COMPANY_TICKERS_URL,
            "forms_included": sorted(MODEL_RELEVANT_FORMS),
            "domestic_issuer_forms": ["10-K", "10-Q"],
            "foreign_private_issuer_forms": ["20-F", "6-K"],
            "note": "Metadata only; financial statement extraction is a next-stage parser task.",
        },
        "companies": companies,
        "filings": sorted(
            filing_items,
            key=lambda filing: (filing.get("filing_date") or "", filing.get("company") or ""),
            reverse=True,
        ),
        "issues": issues,
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    database = build_database()
    OUT_PATH.write_text(json.dumps(database, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_PATH)
    print(f"companies={len(database['companies'])} filings={len(database['filings'])} issues={len(database['issues'])}")


if __name__ == "__main__":
    main()
