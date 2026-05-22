# InferenceX 데이터 수집 및 정규화 계획

- 기준일: 2026-05-19
- 목적: InferenceX의 공개 benchmark/app/dump 자료를 A08 tokens/sec/MW, A09 utilization, GPU spec, TCO sanity layer로 반복 수집합니다.
- 핵심 원칙: dashboard DOM 크롤링보다 GitHub repo, API route, weekly DB dump release, raw CSV/export를 우선합니다.

## 확인된 공개 소스

- Benchmark repo: https://github.com/SemiAnalysisAI/InferenceX
- Dashboard app repo: https://github.com/SemiAnalysisAI/InferenceX-app
- Dashboard: https://inferencex.semianalysis.com/
- 최신 확인 DB dump: `db-dump/2026-05-11` / `inferencex-dump-2026-05-11.zip` / 2072340792 bytes
- App README 기준: dashboard는 Neon PostgreSQL 또는 static JSON dump를 데이터 소스로 사용합니다.
- Full dump parse status: `parsed`
- Full dump benchmark rows: `72091` / total records `72091`
- Full dump SHA-256: `3f59aa2b4db7a0449a7bb030d70cdc3780fc59cafddf6ff071beb36365b44e2d`

## Source 우선순위

| 우선순위 | Source | 사용 방식 | 비고 |
|---:|---|---|---|
| 1 | GitHub release DB dump / raw CSV export | 정규화 후 benchmark table 생성 | 대용량이므로 명시 옵션으로 다운로드 |
| 2 | InferenceX benchmark repo / GitHub Actions artifacts | benchmark provenance, run URL, config 추적 | public run/artifact가 열려 있을 때 사용 |
| 3 | Dashboard app API route / docs / schema | table 의미, API field mapping | source code로 schema 확인 |
| 4 | Dashboard DOM | 마지막 fallback | 표가 동적으로 바뀌므로 기본 금지 |

## Dashboard tab mapping

| Tab | 모델 내 사용처 | 필요한 key | Forecast 반영 |
|---|---|---|---|
| inference_performance | A08 tokens/sec/MW, A09 latency/utilization sensitivity | model, gpu, framework/runtime, precision, ISL, OSL, concurrency, throughput, latency | benchmark/proxy only |
| accuracy_evals | model quality guardrail when comparing precision/quantization choices | model, precision, benchmark, score, date | quality sanity check; not token capacity |
| historical_trends | software improvement CAGR, SGLang/vLLM/TRT-LLM version step changes | config key, software version, benchmark date, PR/run URL | scenario support for Bull/Base/Bear tokens/MW improvement |
| tco_calculator | cost/token and memory marketing implications | GPU, system cost, power, throughput, utilization, amortization | commercial sensitivity layer, not production volume |
| gpu_specs | GPU generation, memory capacity/bandwidth, TDP cross-check | GPU, vendor, memory, bandwidth, power/TDP | hardware sanity check for GPU/ASIC mix |

## 정규화 스키마

정규화 파일은 `data/inferencex/normalized/inferencex_normalized_schema.csv`를 기준으로 합니다.

```text
source_file, source_kind, benchmark_id, dashboard_tab, model, model_family, gpu, gpu_vendor, gpu_count, framework, runtime, precision, isl, osl, concurrency, batch_size, metric_name, metric_value, metric_unit, tok_s_user, tok_s_gpu, tok_s_mw, input_tok_s_gpu, output_tok_s_gpu, joules_token, p99_ttft_ms, p99_tpot_ms, cost_per_million_tokens_usd, power_w, benchmark_date, github_run_url, source_url, evidence_class, caveat
```

## 사용 규칙

- InferenceX 수치는 `Proxy/Benchmark`입니다. 특정 회사의 production token telemetry로 쓰지 않습니다.
- 본 보고서의 headline `inference_tokens_per_day`는 generated output token equivalent입니다. InferenceX total `tok_s_mw`는 processed token proxy일 수 있으므로 headline 검증에는 `output_tok_s_mw`와 `j_output_token`을 우선 사용합니다.
- `tok_s_mw`, `input_tok_s_mw`, `output_tok_s_mw`는 서로 다른 단위/의미로 취급합니다. input+output processed throughput을 generated output capacity로 직접 치환하지 않습니다.
- ISL/OSL, precision, framework, GPU, concurrency가 다른 값을 한 숫자로 평균 내지 않습니다.
- tokens/sec/MW는 A08 sensitivity 또는 benchmark sanity layer에만 먼저 반영합니다.
- latency/SLO, concurrency, P/D disaggregation 정보는 A09 utilization sensitivity로 분리합니다.
- TCO calculator 값은 memory marketing 및 cost/token narrative용이며 company capacity forecast를 직접 바꾸지 않습니다.

## 실행

```bash
.venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py
.venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py --input-dir /path/to/inferencex-dump
.venv/bin/python llm_token_capacity_project/tools/fetch_inferencex_data.py --download-latest-dump
```

`--download-latest-dump`는 최신 release asset이 1GB 이상일 수 있으므로 필요할 때만 실행합니다.

## 산출물

- `data/inferencex/metadata/inferencex_manifest.json`
- `data/inferencex/normalized/inferencex_source_index.csv`
- `data/inferencex/normalized/inferencex_normalized_schema.csv`
- main simulation workbook의 `12_inferencex_source_index`, `12a_inferencex_schema`, `12b_inferencex_tab_rules`
- full dump 처리 시 `inferencex_benchmark_results.csv`, `inferencex_metric_profile.csv`, `inferencex_accuracy_evals.csv`, `inferencex_dump_inventory.csv`
