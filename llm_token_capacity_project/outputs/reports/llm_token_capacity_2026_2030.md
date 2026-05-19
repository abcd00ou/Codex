# 상용 LLM 업체별 전력·GPU·토큰 생성량 시뮬레이션 (2026–2030)

- 생성일: 2026-05-18
- 목적: 상용 LLM owner 기준으로 전력 capacity, 추론/학습 split, GPU/ASIC mix, tokens/sec/MW, GPU benchmark reference, token 생성량을 연결한 임원 보고용 기준 시나리오 작성
- 주의: 이 문서는 투자 조언이 아니라 supply-chain / token-capacity intelligence simulation입니다.

## 핵심 결론
- **2030 core-company inference tokens/day**: 2.87 quadrillion tokens/day - 9개 상용 LLM owner의 base case 총 생성 capacity.
- **2030 inference AI IT load**: 23.02 GW inference load - PUE와 AI workload share 차감 후 inference에 배정된 IT load.
- **2030 US vs China split**: US 81% / China 19% - 회사 owner 기준 split이며 AWS/Oracle/CoreWeave 같은 host는 core row가 아님.

## 2030 기준 시나리오 순위

| 순위 | 업체 | 지역 | 추론 GW | 토큰/일 | 신뢰도 |
|---:|---|---|---:|---:|---|
| 1 | OpenAI | US | 4.86 | 0.59Q | Medium |
| 2 | Google | US | 3.65 | 0.54Q | Medium-High |
| 3 | Meta | US | 3.28 | 0.40Q | Medium |
| 4 | Microsoft | US | 3.33 | 0.37Q | Medium |
| 5 | Anthropic | US | 2.97 | 0.32Q | Medium |
| 6 | Alibaba | China | 1.75 | 0.26Q | Medium |
| 7 | Tencent | China | 1.31 | 0.17Q | Medium-Low |
| 8 | xAI | US | 1.22 | 0.13Q | Medium-Low |
| 9 | DeepSeek | China | 0.65 | 0.10Q | Parameter High / Capacity Low-Medium |

## 방법론

```text
it_load_gw = active_power_gw / pue
ai_it_load_gw = it_load_gw * ai_workload_share
inference_gw = ai_it_load_gw * inference_power_share
inference_tokens_per_day = inference_mw * tokens_per_second_per_mw * utilization * 86,400
joules_per_token = 1,000,000 / tokens_per_second_per_mw
```

## 계산식/가정 감사

| Block | Formula | 해석 | Sources |
|---|---|---|---|
| Power to AI IT load | `it_load_gw = active_power_gw / pue` | 계약/계획 전력이 아니라 실제 operational deploy된 전력에서 PUE를 차감해 IT load를 산출. | SRC_MCKINSEY_AI_WORKLOADS; SRC_EPRI_EPOCH_AI_POWER |
| AI workload allocation | `ai_it_load_gw = it_load_gw * ai_workload_share` | 데이터센터 전체 IT load 중 LLM serving/training에 쓰이는 AI load만 분리. | ASSUMP_POWER_RAMP |
| Training vs inference split | `inference_gw = ai_it_load_gw * inference_power_share; training_gw = ai_it_load_gw * (1 - inference_power_share)` | inference 비중은 company fact가 아니라 상용화 성숙도와 제품 표면에 따른 시나리오 변수. | SRC_MCKINSEY_AI_WORKLOADS; SRC_DELOITTE_AI_POWER; SRC_EPRI_EPOCH_AI_POWER; ASSUMP_INFERENCE_SHARE_NOT_FACT_60 |
| Inference token capacity | `inference_tokens_per_day = inference_gw * 1000 * tokens_per_second_per_mw * utilization * 86,400` | 전력 배정, serving 효율, 실제 utilization이 token 생성 capacity를 결정. | SRC_SEMIANALYSIS_INFERENCEX; SRC_ARXIV_INFERENCE_ENERGY |
| Energy sanity check | `joules_per_token = 1,000,000 / tokens_per_second_per_mw` | MW를 J/s로 환산해 tokens/sec/MW와 에너지/token이 상호 일관되는지 확인. | SRC_ARXIV_INFERENCE_ENERGY |
| MoE optimization | `scenario_tokens_per_second_per_mw = base_tps_per_mw * tokens_per_mw_multiplier * moe_optimization_multiplier` | DeepSeek/Qwen 같은 MoE 모델은 active parameter가 낮아 serving efficiency scenario에 별도 multiplier를 적용. | SRC_DEEPSEEK_V3; SRC_QWEN3_GITHUB; ASSUMP_MOE_EFFICIENCY |

## Fact Anchor

| Anchor | 업체 | 지표 | 값 | 날짜 | Source | 모델 반영 방식 |
|---|---|---|---|---|---|---|
| FACT_OPENAI_ORACLE_4_5GW | OpenAI | Additional Oracle datacenter capacity | 4.5 GW | 2025-07-22 | SRC_OPENAI_STARGATE_ORACLE | OpenAI 2030 contracted_power_gw 상향 anchor. active_power_gw는 energization/GPU delivery 때문에 별도 multiplier 적용. |
| FACT_OPENAI_STARGATE_10GW | OpenAI | Stargate planned capacity commitment | Nearly 7 GW announced across new sites; over 10 GW commitment stated | 2025-09-23 | SRC_OPENAI_STARGATE_PROGRESS | 2030 OpenAI contracted_power_gw 12GW는 공개 commitment를 약간 상회하지 않도록 점검하는 ceiling 역할. |
| FACT_GOOGLE_IRONWOOD_POD | Google | Ironwood TPU pod scale | 9,216 liquid-cooled chips; 42.5 exaflops per pod | 2025-04-09 | SRC_GOOGLE_IRONWOOD | Google tps_per_mw_2026 premium과 efficiency_cagr는 TPU/Ironwood inference-optimized hardware direction으로 정당화. |
| FACT_GOOGLE_TPU_V6E | Google | TPU v6e / Trillium generation | Google Cloud TPU v6e public product documentation | 2026-05-14 accessed | SRC_GOOGLE_TPU_V6E | Google serving_platform fact 보강. tokens/MW 수치는 직접 인용하지 않음. |
| FACT_DEEPSEEK_V3_MOE | DeepSeek | DeepSeek-V3 MoE parameters | 671B total parameters; 37B activated per token | 2024-12-26 | SRC_DEEPSEEK_V3 | DeepSeek MoE efficiency multiplier 적용의 가장 강한 모델-side evidence. |
| FACT_DEEPSEEK_V3_TRAINING_TOKENS | DeepSeek | DeepSeek-V3 pretraining corpus | 14.8T high-quality tokens | 2024-12-26 | SRC_DEEPSEEK_V3 | training_tokens_processed_per_day는 pretraining token scale과 order-of-magnitude 비교 가능하지만 직접 calibration은 아님. |
| FACT_QWEN3_MOE | Alibaba | Qwen3 flagship MoE parameters | 235B total parameters; 22B activated parameters | 2025-04-29 | SRC_QWEN3_GITHUB | Alibaba MoE efficiency multiplier와 parameter confidence를 보강. |
| FACT_LLAMA4_SCOUT_MAVERICK | Meta | Llama 4 MoE parameter anchors | Scout 109B total / 17B active; Maverick 400B total / 17B active | 2025-04-07 | SRC_META_LLAMA4_NVIDIA | Meta parameter band를 더 좁힘. 다만 Meta AI production routing과 active serving GW는 여전히 scenario. |
| FACT_XAI_COLOSSUS_100K | xAI | Colossus initial cluster | 100,000 NVIDIA Hopper GPUs | 2024-12-04 | SRC_XAI_NVIDIA_COLOSSUS | 100k Hopper GPU는 xAI active_power_2026_gw 0.35GW가 물리적으로 과도하지 않은지 확인하는 anchor. |
| FACT_XAI_COLOSSUS_200K | xAI | Colossus expansion direction | Expansion toward 200,000 GPUs cited by NVIDIA | 2024-12-04 | SRC_XAI_NVIDIA_COLOSSUS | xAI contracted_power_2030_gw 3GW와 active_power_2030_gw 2.5GW는 추가 clusters 포함한 scenario. |
| FACT_MS_PHI4_14B | Microsoft | Phi-4 parameter count | 14B parameters | 2024-12-12 | SRC_MS_PHI4_TECHREPORT | Microsoft model row에서 Phi/MAI owned와 OpenAI model-owner output을 분리하는 근거. |
| FACT_ANTHROPIC_AWS_5GW | Anthropic | AWS/Project Rainier hosted capacity direction | Up to 5GW-class AI compute capacity cited for Anthropic/AWS buildout | 2025-2026 | SRC_ANTHROPIC_AMAZON_COMPUTE | Anthropic contracted_power_2030_gw와 active_power_2030_gw의 상한 anchor. AWS는 host이며 model-owner attribution은 Anthropic. |
| FACT_TENCENT_HUNYUAN_100B | Tencent | Hunyuan foundation model scale | Over 100B parameters and over 2T pretraining tokens | 2023-09-07 | SRC_TENCENT_HUNYUAN | Tencent parameter band를 closed-only에서 100B+ anchor로 보강. active serving capacity는 여전히 낮은 confidence. |
| FACT_MCKINSEY_2030_INFERENCE | Cross-company | 2030 inference demand direction | Inference expected to account for more than half of AI workloads and 30-40% of data center power demand by 2030 | 2026-02-24 | SRC_MCKINSEY_AI_WORKLOADS | 2030 weighted inference share 상승의 directional anchor. 2026 60%+ 주장은 fact로 채택하지 않음. |
| FACT_DELOITTE_2026_INFERENCE | Cross-company | 2026 inference compute share outlook | Inference cited as roughly two-thirds of compute in 2026 outlook | 2025-12 | SRC_DELOITTE_AI_POWER | 2026 base/bull inference share가 60%를 넘을 수 있는 상향 전망 anchor지만, 공식 fact로는 표시하지 않음. |
| FACT_EPOCH_TRAINING_POWER_RISK | Cross-company | Frontier training power can remain material | Individual frontier training runs may require large power blocks by 2030 | 2025-08 | SRC_EPRI_EPOCH_AI_POWER | Bear/base에서 training share를 남기는 보수 anchor. |

## 시나리오 설계

| 시나리오 | 2030 가동률 배수 | 2030 추론 비중 변화 | Tokens/MW | MoE 최적화 | 설명 |
|---|---:|---:|---:|---:|---|
| Bear | 82% | -10%p | 82% | 92% | 전력 인허가/장비 조달 지연, MoE 최적화 둔화, inference 전환이 느린 경우 |
| Base | 100% | +0%p | 100% | 100% | 현재 공식 발표와 시장전망을 기준으로 한 staged deployment, MoE 효율 개선, inference mix 상승 |
| Bull | 118% | +8%p | 118% | 118% | 전력 energization이 빠르고, MoE/serving stack 최적화가 강하며, commercial inference 비중이 빠르게 상승 |
| Grid-Constrained / Efficiency-Upside | 72% | +4%p | 118% | 122% | 전력 투입은 지연되지만 MoE·quantization·batching 효율이 개선되어 token capacity 하락을 일부 상쇄 |

## 추론 60%+ Fact Check

- 2026년에 이미 전체 AI GW의 60% 이상이 inference라는 주장은 공식 company-level fact로 단정하지 않습니다.
- McKinsey/Deloitte는 inference 비중 상승 전망을 제공하지만, 업체별 active GW split disclosure가 아닙니다.
- EPRI/Epoch AI는 현재 AI power가 training, experiments, inference로 대략 나뉜다는 보수적 anchor를 제공합니다.
- 따라서 본 모델의 inference share는 `Scenario assumption`이며, source transparency에 맞춰 confidence를 별도 표기합니다.

## 2030 시나리오 범위

| 시나리오 | 가동 전력 GW | 추론 GW | 가중 추론 비중 | 토큰/일 | 기준 대비 변화 |
|---|---:|---:|---:|---:|---:|
| Bear | 34.52 | 16.39 | 66% | 1.49Q | -48.0% |
| Base | 42.10 | 23.02 | 76% | 2.87Q | 0.0% |
| Bull | 49.65 | 30.01 | 84% | 4.79Q | 66.8% |
| Grid-Constrained / Efficiency-Upside | 30.31 | 17.45 | 80% | 2.69Q | -6.2% |

## Benchmark Sanity Check

| 업체 | Proxy | Benchmark annual QTokens | Model annual QTokens | 차이 | 주의점 |
|---|---|---:|---:|---:|---|
| Microsoft | Copilot/GPT-class proxy + Phi anchor | 50.26 | 135.88 | -63.0% | Microsoft-owned/Phi와 OpenAI dependency mix가 섞인 proxy |
| Google | Gemini closed frontier proxy | 56.68 | 195.32 | -71.0% | TPU serving을 GPU-equivalent proxy로 환산 |
| Meta | Llama 4 Maverick | 149.86 | 146.84 | 2.1% | Meta AI production routing과 다를 수 있음 |
| xAI | Grok closed frontier proxy | 14.11 | 45.85 | -69.2% | Grok closed model benchmark가 없어 cluster scale 기반 proxy |
| OpenAI | gpt-oss/frontier mix proxy | 68.90 | 214.20 | -67.8% | closed GPT 실제 serving benchmark가 아니므로 sanity check로만 사용 |
| Anthropic | Claude closed frontier proxy | 33.25 | 116.18 | -71.4% | Claude 파라미터/serving benchmark는 비공개라 proxy |
| DeepSeek | DeepSeek-V3 / R1 | 84.88 | 38.09 | 122.8% | 모델 구조는 공개되어 있으나 production serving은 proxy |
| Alibaba | Qwen3 235B-A22B | 11.10 | 94.83 | -88.3% | 공개 Qwen benchmark 기반 reference; Alibaba Cloud production mix와 다를 수 있음 |
| Tencent | Hunyuan closed proxy | 13.79 | 61.09 | -77.4% | Hunyuan serving benchmark가 제한적이라 generic proxy |

## A08 Cycle 1: Energy Sanity Reference

- Base `tokens_per_second_per_mw` 값은 아직 변경하지 않았습니다.
- Joule/IBM/2026 serving sources는 company production telemetry가 아니라 energy/query, joules/token, prefill/decode trade-off 검증 레이어로 사용합니다.
- Strict-SLO/agentic long-context는 energy/token을 악화시킬 수 있고, batchable optimized serving은 개선 가능성이 있으나 둘 다 sensitivity입니다.

| 업체 | Profile | J/token | Energy implied Q/day | Model Q/day | 차이 | 해석 |
|---|---|---:|---:|---:|---:|---|
| Google | Strict-SLO / long-context agentic | 0.7633 | 0.289 | 0.535 | -45.9% | agentic/test-time compute가 증가하면 같은 MW에서 token output이 낮아질 수 있음 |
| Google | Base serving mix | 0.4126 | 0.535 | 0.535 | 0.0% | 메인 forecast와 일치시키는 기준 energy view |
| Google | Batchable / optimized serving | 0.2806 | 0.787 | 0.535 | 47.1% | serving stack 최적화가 energy/token을 낮출 수 있으나 company fact는 아님 |
| OpenAI | Strict-SLO / long-context agentic | 0.9402 | 0.317 | 0.587 | -45.9% | agentic/test-time compute가 증가하면 같은 MW에서 token output이 낮아질 수 있음 |
| OpenAI | Base serving mix | 0.5082 | 0.587 | 0.587 | 0.0% | 메인 forecast와 일치시키는 기준 energy view |
| OpenAI | Batchable / optimized serving | 0.3456 | 0.863 | 0.587 | 47.1% | serving stack 최적화가 energy/token을 낮출 수 있으나 company fact는 아님 |
| Anthropic | Strict-SLO / long-context agentic | 1.0427 | 0.172 | 0.318 | -45.9% | agentic/test-time compute가 증가하면 같은 MW에서 token output이 낮아질 수 있음 |
| Anthropic | Base serving mix | 0.5636 | 0.318 | 0.318 | -0.0% | 메인 forecast와 일치시키는 기준 energy view |
| Anthropic | Batchable / optimized serving | 0.3832 | 0.468 | 0.318 | 47.0% | serving stack 최적화가 energy/token을 낮출 수 있으나 company fact는 아님 |

## A09 Cycle 1: SLO / Utilization Sensitivity

- Base utilization band는 유지했습니다.
- utilization은 GPU 점유율이 아니라 TTFT/TPOT, batchability, placement, failover reserve가 반영된 평균값입니다.
- strict-SLO와 agentic long-context workload는 output capacity를 낮출 수 있고, batchable optimized workload는 상향 sensitivity입니다.

| 업체 | Profile | Adjusted utilization | Adjusted TPS/MW | Q/day | 기준 대비 | 설명 |
|---|---|---:|---:|---:|---:|---|
| Google | Strict-SLO real-time | 0.546 | 2229594 | 0.384 | -28.2% | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving |
| Google | Base mixed serving | 0.700 | 2423472 | 0.535 | -0.0% | 메인 forecast 기준 |
| Google | Batchable optimized | 0.784 | 2665819 | 0.659 | 23.2% | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving |
| Google | Agentic long-context stress | 0.616 | 1987247 | 0.386 | -27.8% | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress |
| Meta | Strict-SLO real-time | 0.546 | 1865683 | 0.289 | -28.2% | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving |
| Meta | Base mixed serving | 0.700 | 2027916 | 0.402 | 0.0% | 메인 forecast 기준 |
| Meta | Batchable optimized | 0.784 | 2230708 | 0.496 | 23.2% | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving |
| Meta | Agentic long-context stress | 0.616 | 1662891 | 0.290 | -27.8% | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress |
| OpenAI | Strict-SLO real-time | 0.554 | 1810175 | 0.421 | -28.2% | TTFT/TPOT와 failover reserve가 높아 평균 utilization이 낮은 serving |
| OpenAI | Base mixed serving | 0.710 | 1967582 | 0.587 | 0.0% | 메인 forecast 기준 |
| OpenAI | Batchable optimized | 0.795 | 2164340 | 0.723 | 23.2% | batching, KV cache, P/D scheduling, speculative decoding이 일부 작동하는 serving |
| OpenAI | Agentic long-context stress | 0.625 | 1613417 | 0.423 | -27.8% | 긴 context, tool-use loop, network placement 제약으로 effective throughput이 낮아지는 stress |

## InferenceX Ingestion Layer

- InferenceX는 company production telemetry가 아니라 benchmark/proxy layer입니다.
- Dashboard DOM 크롤링보다 GitHub release DB dump, benchmark repo, app API/schema를 우선합니다.
- 최신 확인 DB dump: `db-dump/2026-05-11` / `inferencex-dump-2026-05-11.zip` / `2072340792` bytes.
- Full dump parse: `parsed` / benchmark rows `72091` / metric profile rows `298` / SHA-256 `3f59aa2b4db7a0449a7bb030d70cdc3780fc59cafddf6ff071beb36365b44e2d`.
- 정규화 결과는 엑셀 `12d_ix_benchmark_results`, `12e_ix_metric_profile`, `12f_ix_accuracy_evals`, `12g_ix_dump_inventory`에 반영됩니다.

| Tab | 모델 내 사용처 | Forecast 반영 |
|---|---|---|
| inference_performance | A08 tokens/sec/MW, A09 latency/utilization sensitivity | benchmark/proxy only |
| accuracy_evals | model quality guardrail when comparing precision/quantization choices | quality sanity check; not token capacity |
| historical_trends | software improvement CAGR, SGLang/vLLM/TRT-LLM version step changes | scenario support for Bull/Base/Bear tokens/MW improvement |
| tco_calculator | cost/token and memory marketing implications | commercial sensitivity layer, not production volume |
| gpu_specs | GPU generation, memory capacity/bandwidth, TDP cross-check | hardware sanity check for GPU/ASIC mix |

## Hallucination 체크리스트

| ID | 영역 | 질문 | Pass 기준 | 심각도 | 상태 |
|---|---|---|---|---|---|
| HC01 | Source existence | 모든 source URL 또는 report name이 실제로 존재하고 접근 가능한가? | 01_sources의 URL을 열었을 때 publisher/title/date가 일치한다. | High | Needs manual URL click-through |
| HC02 | Numeric fact quote | Fact anchor의 숫자(예: 4.5GW, 671B/37B, 235B/22B, 100k GPU)가 원문에 직접 존재하는가? | 02a_fact_anchors의 value가 원문 문장/표와 직접 매칭된다. | High | Partially checked; requires final source screenshot/quote pack |
| HC03 | Fact vs estimate separation | Active GW, inference share, utilization, tokens/sec/MW가 fact로 오표기되지 않았는가? | 해당 값은 Estimate/Scenario로 표시되고 replacement_path가 있다. | High | Pass in structure |
| HC04 | Closed model parameters | OpenAI, Anthropic, Gemini, Grok 같은 closed model에 단일 precise parameter 숫자를 쓰지 않았는가? | closed model은 band/proxy로만 표시하고 benchmark는 sanity check로만 사용. | High | Pass |
| HC05 | MoE total/active | MoE 모델은 total params와 active params를 분리했는가? | DeepSeek, Qwen, Llama 4 계열은 total/active가 별도 column 또는 anchor에 존재. | Medium | Pass |
| HC06 | Host vs model owner | AWS/Google/Oracle 같은 host capacity가 model owner와 혼동되지 않았는가? | Anthropic/OpenAI capacity는 model output 기준으로 귀속하고 host는 source/context로만 표기. | High | Pass in attribution rules |
| HC07 | Microsoft/OpenAI overlap | Microsoft Copilot token과 OpenAI model token을 이중계산하지 않았는가? | OpenAI model output은 OpenAI row, Microsoft-owned/serving burden은 Microsoft row로 명시. | High | Needs sales/product routing data for final resolution |
| HC08 | Capacity boundary | active_power_gw가 contracted_power_gw를 넘지 않는가? | 모든 company-year-scenario에서 active <= contracted. | High | Automated pass |
| HC09 | Power split | training_power_share + inference_power_share = 100%인가? | 모든 row에서 합계가 1.000 +/- 0.001. | High | Automated pass |
| HC10 | Unit consistency | daily token과 annual token 단위가 섞이지 않았는가? | token/day는 86,400초, annual token은 365일 또는 31,536,000초로 환산. | High | Automated pass |
| HC11 | Benchmark proxy use | OSS/open benchmark를 closed commercial model 결론으로 직접 사용하지 않았는가? | 08d_benchmark_reference는 sanity check이며 main forecast와 분리. | High | Pass |
| HC12 | Inference share | 2026년 추론 60%+를 fact로 단정하지 않았는가? | Base 2026은 60% 미만이고 Bull에서만 60%+ 허용. | Medium | Pass |
| HC13 | Outlier review | main forecast와 benchmark reference의 차이가 큰 업체를 따로 표시했는가? | benchmark_vs_model_pct가 +/-50%를 넘으면 confidence review 대상. | Medium | Needs reviewer sign-off |
| HC14 | China transparency | 중국 업체의 낮은 공개성 때문에 수치를 임의로 페널티하거나 과신하지 않았는가? | 모델 구조 fact는 인정하고 capacity transparency만 confidence에 반영. | Medium | Pass in principle; needs Chinese primary-source review |
| HC15 | Executive wording | 슬라이드 문구가 추정치를 확정 사실처럼 표현하지 않는가? | forecast, scenario, proxy, sanity check, 추정치 표현을 유지. | High | Needs final human review |

## 귀속 기준
- **Microsoft**: Microsoft-owned token은 Phi/MAI/Copilot serving으로, OpenAI model output은 OpenAI row에도 별도 표기
- **Google**: Google-owned Gemini token generation, Anthropic hosted capacity excluded from core
- **Meta**: Meta-owned consumer and open model serving; third-party hosted Llama not counted in Meta owner tokens
- **xAI**: xAI-owned Grok token generation; X social integration counted only when model generated
- **OpenAI**: OpenAI model output counted here, including OpenAI models served through Microsoft channels when model ownership is OpenAI
- **Anthropic**: Anthropic model output counted under Anthropic, even when served through AWS/Google host capacity
- **DeepSeek**: DeepSeek direct app/API tokens counted; third-party self-hosted derivatives excluded unless DeepSeek-operated
- **Alibaba**: Alibaba-operated Qwen serving counted; open-source third-party self-hosting excluded
- **Tencent**: Tencent-operated Hunyuan/Yuanbao tokens counted; embedded non-LLM media generation separated

## 근거 관리 원칙

- Fact: official model docs/cards, company announcements, technical reports.
- Estimate: active power, 추론/학습 share, utilization, company-level tokens/sec/MW.
- Scenario: 2027–2030 ramp, software efficiency CAGR, 상용 token absorption.
- Closed model parameter는 official disclosure가 없으면 단일 숫자가 아니라 band로만 표기.
- MoE는 total parameter와 active parameter를 분리.

## Source Registry

| Source ID | Tier | Publisher | Date | Use | URL/report |
|---|---|---|---|---|---|
| SRC_OPENAI_GPT41_DOCS | Tier 1 | OpenAI | 2025-04-14 | OpenAI commercial model family and closed-model parameter disclosure boundary | https://platform.openai.com/docs/models/gpt-4.1 |
| SRC_OPENAI_STARGATE_ORACLE | Tier 1 | OpenAI | 2025-07-22 | OpenAI hosting capacity ramp anchor, not a precise active IT load | https://openai.com/index/stargate-advances-with-partnership-with-oracle/ |
| SRC_OPENAI_STARGATE_PROGRESS | Tier 1 | OpenAI | 2025-09-23 | OpenAI 2030 contracted/planned capacity upper-bound anchor | https://openai.com/index/five-new-stargate-sites/ |
| SRC_GOOGLE_GEMINI_TOKENS | Tier 1 | Google AI for Developers | 2026-05-13 accessed | Token accounting and context handling anchor for Gemini surfaces | https://ai.google.dev/gemini-api/docs/tokens |
| SRC_GOOGLE_IRONWOOD | Tier 1 | Google Cloud | 2025-04-09 | Google TPU serving platform and inference-optimized hardware direction | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ |
| SRC_META_LLAMA | Tier 1 | Meta AI | 2026-05-13 accessed | Llama model family and open model parameter disclosures where available | https://www.llama.com/ |
| SRC_XAI_MODELS | Tier 1 | xAI | 2026-05-13 accessed | Grok commercial model surface and closed-model disclosure boundary | https://docs.x.ai/docs/models |
| SRC_XAI_NVIDIA_COLOSSUS | Tier 1/2 | NVIDIA | 2024-12-04 | xAI GPU cluster scale anchor for active power and serving/training capacity scenarios | https://blogs.nvidia.com/blog/xai-colossus/ |
| SRC_DEEPSEEK_V3 | Tier 1 | DeepSeek | 2024-12-26 | MoE total and active parameter anchor | https://github.com/deepseek-ai/DeepSeek-V3 |
| SRC_DEEPSEEK_R1 | Tier 1 | DeepSeek | 2025-01-20 | Reasoning model family and distillation ecosystem anchor | https://github.com/deepseek-ai/DeepSeek-R1 |
| SRC_QWEN3_GITHUB | Tier 1 | Alibaba / Qwen Team | 2025-04-29 | Qwen3 dense/MoE family and active parameter anchor | https://github.com/QwenLM/Qwen3 |
| SRC_META_LLAMA4_NVIDIA | Tier 2 | NVIDIA Developer Blog | 2025-04-07 | Llama 4 Scout/Maverick total-active parameter anchor when official Meta page is less accessible | https://developer.nvidia.com/blog/meta-llama-4-first-nvidia-optimized-mixture-of-experts-models/ |
| SRC_TENCENT_HY3 | Tier 1 | Tencent | 2025-01-21 | Tencent Hunyuan commercial surface and model-family anchor | https://www.tencent.com/en-us/articles/2202320.html |
| SRC_TENCENT_HUNYUAN | Tier 1 | Tencent | 2023-09-07 | Tencent Hunyuan parameter and pretraining token anchor | https://www.tencent.com/en-us/articles/2201460.html |
| SRC_MS_PHI | Tier 1 | Microsoft | 2026-05-13 accessed | Microsoft-owned small language model family anchor | https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models |
| SRC_MS_PHI4_TECHREPORT | Tier 1/2 | Microsoft | 2024-12-12 | Microsoft-owned Phi-4 14B parameter anchor | https://arxiv.org/abs/2412.08905 |
| SRC_GOOGLE_TPU_V6E | Tier 1 | Google Cloud | 2026-05-14 accessed | Google TPU serving/training platform generation anchor | https://cloud.google.com/tpu/docs/v6e |
| SRC_ANTHROPIC_AMAZON_COMPUTE | Tier 1 | Anthropic / Amazon | 2025-2026 | Anthropic contracted/hosted capacity anchor; capacity attributed to Anthropic model owner | https://www.anthropic.com/news/anthropic-amazon-compute |
| SRC_ANTHROPIC_CLAUDE_DOCS | Tier 1 | Anthropic | 2026-05-14 accessed | Claude commercial model family and closed-model disclosure boundary | https://docs.anthropic.com/en/docs/about-claude/models/overview |
| SRC_SEMIANALYSIS_INFERENCEX | Tier 2 | SemiAnalysis | 2025-2026 | Benchmark layer for tokens/sec/MW sensitivity, not company capacity | https://inferencex.semianalysis.com/about |
| SRC_ARXIV_INFERENCE_ENERGY | Tier 2 | arXiv | 2024-2026 | Joules/token sanity check, prefill/decode split, batching, quantization sensitivity | https://arxiv.org/search/?query=large+language+model+inference+energy+joules+per+token&searchtype=all |
| SRC_JOULE_INFERENCE_ENERGY_2026 | Tier 2 | Joule / Cell Press | 2026 | Energy/query and joules/token sanity layer for inference forecasts | https://www.sciencedirect.com/science/article/pii/S2542435126001145 |
| SRC_IBM_PD_DISAGG_2026 | Tier 2 | IBM Research / EuroSys | 2026 | Prefill/decode disaggregation performance and energy trade-off mechanism | https://research.ibm.com/publications/revisiting-disaggregated-large-language-model-serving-for-performance-and-energy-implications |
| SRC_ARXIV_SLO_PD_2026 | Tier 2 | arXiv | 2026 | Utilization caveat for TTFT/TPOT SLO constrained serving | https://arxiv.org/abs/2603.04716 |
| SRC_ARXIV_PREFILL_AS_SERVICE_2026 | Tier 2 | arXiv | 2026 | Agentic/long-context placement and network sensitivity for utilization | https://arxiv.org/abs/2604.15039 |
| SRC_ARXIV_SPEC_DECODING_LATENCY_2026 | Tier 2 | arXiv | 2026 | Speculative decoding latency and throughput trade-off mechanism | https://arxiv.org/abs/2605.15051 |
| SRC_MCKINSEY_AI_WORKLOADS | Tier 2 | McKinsey & Company | 2026-02-24 | Inference share fact-check and 2030 workload mix directional anchor | https://www.mckinsey.com/featured-insights/week-in-charts/the-future-of-ai-workloads |
| SRC_DELOITTE_AI_POWER | Tier 2 | Deloitte | 2025-12 | Inference compute share outlook, used only as scenario cross-check | https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html |
| SRC_EPRI_EPOCH_AI_POWER | Tier 2 | EPRI / Epoch AI | 2025-08 | Current AI power allocation sanity check across training, experiments, and inference | https://epoch.ai/blog/power-demands-of-frontier-ai-training |

## 검증

- Status: **PASS**
- closed_parameter_precision: PASS - closed model rows use bands/undisclosed labels, not single precise parameter values.
- moe_total_active: PASS - DeepSeek and Alibaba rows include total and active parameter bands.
- microsoft_openai_overlap: PASS - attribution rule separates OpenAI model-owner output and Microsoft customer-facing serving.
- anthropic_scope: PASS - Anthropic is included as a core model-owner row; AWS/Google host capacity is attributed to Anthropic model output.
- benchmark_layer: PASS - GPU/effective-active-parameter benchmark reference is separated from the main tokens/sec/MW forecast.
- energy_sanity_layer: PASS - Joule/IBM/2026 serving sources are separated as sanity/sensitivity layers, not Base production telemetry.
- utilization_slo_layer: PASS - SLO/workload utilization sensitivity is separated from Base utilization band.
