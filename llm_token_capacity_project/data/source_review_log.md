# Source Review Log

출처 원문을 확인할 때마다 이 파일에 기록합니다. 목적은 숫자 변경의 흔적을 남기는 것입니다.

| 날짜 | source_id | 확인한 항목 | 결과 | 후속 조치 |
|---|---|---|---|---|
| 2026-05-14 | 전체 | 독립 프로젝트 초기화 | 기존 생성기와 산출물 이관 | 다음 cycle에서 URL/원문 quote pack 보강 |
| 2026-05-15 | WATCH_INFERENCEX | InferenceX/SemiAnalysis benchmark source 후보 | benchmark/proxy layer 후보로 분류 | A08/A09 agent가 source-reviewed evidence로 승격 검토 |
| 2026-05-15 | WATCH_INTROL | Introl AI infrastructure source 후보 | practitioner context/proxy 후보로 분류 | A01/A02/A03/A04 agent가 deployment context로 검토 |
| 2026-05-15 | WATCH_DELOITTE_AI_DC | Deloitte AI/data center/semiconductor 리포트 후보 | consulting market context/scenario source로 분류 | A01/A02/A05/A06/A10 agent가 source-reviewed evidence로 승격 검토 |
| 2026-05-15 | WATCH_AI_2027 | AI 2027 scenario 후보 | scenario/stress-test source로 분류 | A05/A06/A08/A09/A10 및 orchestrator가 Base와 분리해 검토 |
| 2026-05-18 | WATCH_2026_SERVING_ENERGY | 2026 inference serving/energy 논문 묶음 | paper/benchmark/proxy 후보로 분류 | A08/A09가 tokens/MW, utilization, SLO, energy/query logic으로 검토 |
| 2026-05-18 | JOULE_INFERENCE_2026 | AI inference energy and test-time compute | proxy/energy sanity source로 A08 evidence 승격 | energy sanity layer 후보, Base tokens/MW 직접 변경 없음 |
| 2026-05-18 | IBM_PD_2026 | Prefill-decode disaggregation performance/energy implications | mechanism source로 A08/A09 evidence 승격 | P/D disaggregation은 scenario sensitivity, Base 직접 변경 없음 |
| 2026-05-18 | ARXIV_SLO_PD_2603 | SLO-aware P/D resource allocation | mechanism source로 A09 evidence 승격 | utilization caveat 강화 |
| 2026-05-18 | ARXIV_PREFILL_SERVICE_2604 | Prefill-as-a-service | scenario/mechanism source로 A09 evidence 승격 | agentic workload placement/network sensitivity 후보 |
| 2026-05-19 | WATCH_INFERENCEX | InferenceX benchmark repo README, `perf-changelog.yaml`, dashboard app README/.env/docs/API/release metadata | public benchmark + app + weekly DB dump source로 확인. Latest checked release: `db-dump/2026-05-11`, asset `inferencex-dump-2026-05-11.zip`; source remains Proxy/Benchmark, not company telemetry | `tools/fetch_inferencex_data.py`, `docs/inferencex_ingestion_plan.md`, Excel `12*` sheets로 ingestion layer 운영 |
| 2026-05-19 | INFERENCEX_DUMP_2026_05_11 | GitHub release full DB dump, SHA-256 `3f59aa2b4db7a0449a7bb030d70cdc3780fc59cafddf6ff071beb36365b44e2d` | 72,091 inference performance rows, 298 metric profile groups, 1,048 accuracy eval rows, 5,620 availability rows normalized. GPU power/cost mapping follows InferenceX-app `HW_REGISTRY`; source remains Proxy/Benchmark | A08/A09 evidence로 승격. Base coefficient는 변경하지 않고 `12d_ix_benchmark_results`, `12e_ix_metric_profile`, `12f_ix_accuracy_evals`에서 검증 |
| 2026-06-08 | INFERENCEX_DUMP_2026_06_08 | GitHub release full DB dump, SHA-256 `3e4fd9329143c531728f68c6e7469813a79bc5f212f483f26e4f51f0b2057e49` | 76,406 inference performance rows, 338 metric profile groups, 128 GPU-comparable main-config groups, 1,613 accuracy eval rows, 6,055 availability rows normalized. Model-level `main_framework`/`main_precision` validation passed for 9 models; source remains Proxy/Benchmark | A08/A09 evidence refresh. `12f_ix_gpu_comparable`, `12g_ix_main_config`, `12h_ix_main_validation` added so GPU comparison does not mix framework/precision |
| 2026-05-26 | SRC_MS_MAIA200 | Microsoft Maia 200 공식 발표: inference 중심 설계, Azure 배치 및 Microsoft AI/Copilot 지원 | Platform direction direct source; numeric serving mix/GW는 비공개 | A04/A11에서 platform fact로 사용하고 mix share는 scenario로 유지 |
| 2026-05-26 | SRC_META_MTIA_GENAI_2026 | Meta MTIA 공식 발표: GenAI inference production 대상 신규 세대 및 포트폴리오 접근 | Platform direction direct source; 전체 GenAI fleet split은 비공개 | A04/A11에서 platform fact로 사용하고 share는 scenario로 유지 |
| 2026-05-26 | SRC_AWS_RAINIER_ACTIVE | AWS Project Rainier/Trainium 기반 Anthropic capacity 방향 | Hosted platform/capacity direction source; Claude serving allocation share는 비공개 | Anthropic 귀속 규칙과 A11 purpose-built mix의 scenario 근거로 사용 |
| 2026-05-26 | SRC_DEEPSEEK_H800_INFERENCE | DeepSeek V3/R1 inference system overview의 H800 serving infrastructure 기술 | Hardware reference direct source; 미래 fleet mix/GW는 비공개 | DeepSeek Base를 GPU reference로 두고 efficiency architecture layer와 분리 |
| 2026-05-26 | SRC_ALIBABA_QWEN_GPU_DEPLOY; SRC_TENCENT_AI_INFRA_MOE | Qwen GPU inference deployment path 및 Tencent AI/MoE infrastructure 방향 공식 자료 | Platform/reference source; operated mix 수치 비공개 | Alibaba/Tencent는 공개 allocation 확보 전 Base GPU reference 유지 |

## 기록 규칙

- 원문에 숫자가 직접 있으면 "direct numeric source"라고 적습니다.
- 숫자가 원문에는 없고 계산으로 나온 값이면 "derived estimate"라고 적습니다.
- benchmark 또는 proxy이면 "proxy only"라고 적습니다.
- 날짜가 불명확하면 accessed date를 남기고 confidence를 낮춥니다.
