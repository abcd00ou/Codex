# Assumption Change Log

계산식, 계수, 시나리오, confidence를 바꿀 때마다 이 파일에 기록합니다.

| 날짜 | 항목 | 기존값 | 변경값 | 이유 | 영향 |
|---|---|---|---|---|---|
| 2026-05-14 | 프로젝트 구조 | ai_scm_project 내부 보고서 | llm_token_capacity_project 독립 프로젝트 | 지속적 fact-check와 숫자 정합성 관리 | 산출물과 운영 문서 분리 |
| 2026-05-18 | A08 tokens_per_second_per_mw | Base numeric band unchanged | Added proposed mechanism/proxy refinement only | Joule/IBM/2026 serving papers support energy/SLO sanity checks but not direct company production coefficient changes | Future energy sanity layer and scenario sensitivity candidate |
| 2026-05-18 | A09 utilization | 2026 45-65%, 2030 60-80% | Base band unchanged; added SLO/workload/placement caveat | 2026 prefill-decode and SLO-aware allocation sources show utilization is constrained by latency and workload shape | Future strict-SLO vs batchable sensitivity candidate |
| 2026-05-26 | A01/A02 capacity terminology | `contracted_power_gw`/`active_power_gw` reason was not company-traceable | `contracted_power_gw` is labeled sourced ceiling or scenario envelope; `active_power_gw = min(contracted, modeled operational deployment)` with company rationale | Prevent planned capacity from being read as operational token-serving power | Adds company-year-scenario reason fields and `02b_number_trace` |
| 2026-05-26 | A04 ai_workload_share | Coefficient present without a company-specific rationale trail | Dedicated-AI platform direction sourced per applicable provider; exact shares explicitly remain scenarios | Public material supports platform purpose, not internal IT allocation telemetry | Adds rationale and replacement path for every company row |
| 2026-05-26 | A11 gpu_asic_mix / A08 tokens_per_second_per_mw | Hardware description did not flow numerically into tokens/MW | Add numeric GPU/purpose-built shares, mix factor and explicit efficiency bridge | Hardware mix must be visible in the output-driving equation while undisclosed fleet share remains scenario | Base token outputs are recalculated; workbook includes `04_gpu_asic_mix`, `05_inference_efficiency`, trace sheet |
| 2026-05-26 | A09 utilization | Coefficient not sufficiently distinguished from powered-on capacity | Define utilization as realized output fraction after SLO headroom, reserve, batching and traffic variation | Prevent peak benchmark conversion into sustained commercial output | Adds traceable reason for each company-year-scenario utilization value |
| 2026-05-26 | Display-to-formula reproducibility | Annual output tokens were computed from unrounded daily value | Annual output tokens now equal the displayed integer daily output tokens multiplied by 365 | The reported daily value must exactly reconstruct the reported annual value during executive review | No material economic effect; eliminates rounding-path audit discrepancy |
| 2026-05-26 | Assumption registry completeness | `ASSUMP_CLUSTER_RAMP`, `ASSUMP_CLOSED_MODEL_BAND`, `ASSUMP_APP_EMBEDDING` were referenced but not defined in the exported registry | Add definitions, replacement paths and confidence for all three IDs | A number cannot be auditable if its assumption ID has no registered meaning | No coefficient change; fixes source/assumption trace completeness |
| 2026-05-27 | Fact vs assumption disclosure layer | Source IDs and trace existed but confirmed public values were not visually separated from modeled endpoints | Add company-by-metric `02c_fact_vs_assumption_audit` with nine audit rows per company | Executives must distinguish cited facts from reasoned scenario numbers immediately | No coefficient change; exposes OpenAI/Anthropic extension scenarios explicitly |
| 2026-05-27 | Headline token formula / A08 / A09 | Output used compounded mix, architecture, software, MoE and utilization coefficients | Use operational deployment, PUE, AI/inference allocation and selected InferenceX output TPS/MW only; keep utilization and efficiency improvements as sensitivity/reference | Favor directly inspectable benchmark inputs and eliminate weak hidden multipliers from the final token output | Headline outputs recalculated; add `05b_inferencex_core_tps` and HC22 |
| 2026-05-27 | Executive artifact visibility and Excel calculations | Workbook exposed evidence/raw/sensitivity tabs and stored calculated output as values | Publish six-tab logic-only workbook; store only necessary input values and generate downstream outputs with Excel formulas | Executive artifact should be readable as a direct calculation model while research evidence remains maintained in project records | XLSX tab set and output presentation reduced; formula-chain validation added |

## 기록 규칙

- 숫자 하나라도 바꾸면 이유를 적습니다.
- 공식 출처로 교체한 경우 source_id를 함께 적습니다.
- 시나리오 조정이면 Bear/Base/Bull 중 어떤 case에 영향을 주는지 적습니다.
- confidence 변경이면 downgrade/upgrade 이유를 적습니다.
