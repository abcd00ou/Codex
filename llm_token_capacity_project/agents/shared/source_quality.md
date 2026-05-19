# Source Quality Guide

source quality는 숫자보다 중요합니다. 낮은 품질의 source에서 온 숫자는 모델을 망칠 수 있습니다.

## Preferred Sources

- 회사 공식 블로그/뉴스룸
- SEC filing, annual report, earnings transcript
- cloud product documentation
- model card, GitHub official repo, technical report
- IEA, LBNL/DOE, CRS, EPRI, Uptime Institute, Epoch AI 등 기관/연구 자료
- arXiv 논문은 mechanism과 benchmark로 사용

## Warning Signs

- 날짜가 없음
- 원문 숫자가 아니라 재인용 숫자
- "reportedly", "rumored", "sources say"만 존재
- 단위가 불명확
- peak, planned, operational이 섞여 있음
- TWh/year와 GW를 구분하지 않음
- model owner와 host provider를 구분하지 않음

## Confidence Cap

| Source condition | Max confidence |
|---|---|
| 공식 source + 직접 숫자 | High |
| 공식 source + 해석 필요 | Medium |
| 논문 benchmark를 company proxy로 사용 | Medium-Low |
| 언론 보도 단독 | Low-Medium |
| anonymous/undated | Reject |

## Named Watch Sources

아래 source는 유용하지만 사용 범위를 제한합니다.

| Source | Allowed use | Not allowed |
|---|---|---|
| SemiAnalysis InferenceX / InferenceMAX | Benchmark/proxy for serving efficiency, GPU economics, tokens/sec/MW sanity check; GitHub release DB dumps may be normalized as benchmark evidence | Company-specific production telemetry로 확정 사용; dashboard DOM scrape를 원천 데이터처럼 사용 |
| Introl AI infrastructure content | Practitioner context for deployment bottlenecks, power/cooling/rack operationalization | Primary capacity fact로 직접 사용, unless traced to official source |
| Deloitte AI/data center/semiconductor reports | Market context, scenario framing, demand/capex/power constraint background | Company-level active GW, inference share, or token generation fact로 직접 사용 |
| AI 2027 / AI Futures Project | Scenario stress-test for capability acceleration, agent adoption, compute-demand shock | Base-case fact, company-level telemetry, or production capacity input으로 직접 사용 |
| 2026 inference serving/energy papers | Mechanism/proxy for prefill-decode, energy/query, SLO reserve, utilization and serving efficiency | Company-specific production tokens/MW or utilization fact로 직접 사용 |

## InferenceX Specific Rules

- Preferred ingestion order: weekly DB dump or raw CSV/export, benchmark GitHub artifacts, dashboard app API/schema/docs, dashboard DOM only as final fallback.
- Every normalized row must retain model, GPU, framework/runtime, precision, ISL, OSL, concurrency, metric unit, benchmark date, and source URL/run URL where available.
- Do not average across ISL/OSL, precision, GPU, or framework unless the aggregation method is explicitly documented.
- Treat TCO calculator values as commercial sensitivity and memory-marketing support, not as production token volume.
- Treat accuracy evals as quality guardrails for quantization/precision, not as throughput evidence.
- The 2026-05-11 full dump has verified SHA-256 `3f59aa2b4db7a0449a7bb030d70cdc3780fc59cafddf6ff071beb36365b44e2d`; use `inferencex_benchmark_results.csv` for row-level audit and `inferencex_metric_profile.csv` for grouped p10/p50/p90 bands.
