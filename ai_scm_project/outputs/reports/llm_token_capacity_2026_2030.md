# 상용 LLM 업체별 전력·GPU·토큰 생성량 시뮬레이션 (2026–2030)

- 생성일: 2026-05-14
- 목적: 상용 LLM owner 기준으로 전력 capacity, inference/training split, GPU/ASIC mix, tokens/sec/MW, token 생성량을 연결한 임원 보고용 base case 작성
- 주의: 이 문서는 투자 조언이 아니라 supply-chain / token-capacity intelligence simulation입니다.

## 핵심 결론
- **2030 core-company inference tokens/day**: 2.55 quadrillion tokens/day - 8개 상용 LLM owner의 base case 총 생성 capacity.
- **2030 inference AI IT load**: 20.05 GW inference load - PUE와 AI workload share 차감 후 inference에 배정된 IT load.
- **2030 US vs China split**: US 79% / China 21% - 회사 owner 기준 split이며 AWS/Oracle/CoreWeave 같은 host는 core row가 아님.

## 2030 Base Case Ranking

| Rank | Company | Region | Inference GW | Tokens/day | Confidence |
|---:|---|---|---:|---:|---|
| 1 | OpenAI | US | 4.86 | 0.59Q | Medium |
| 2 | Google | US | 3.65 | 0.54Q | Medium-High |
| 3 | Meta | US | 3.28 | 0.40Q | Medium |
| 4 | Microsoft | US | 3.33 | 0.37Q | Medium |
| 5 | Alibaba | China | 1.75 | 0.26Q | Medium |
| 6 | Tencent | China | 1.31 | 0.17Q | Medium-Low |
| 7 | xAI | US | 1.22 | 0.13Q | Medium-Low |
| 8 | DeepSeek | China | 0.65 | 0.10Q | Parameter High / Capacity Low-Medium |

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

## Fact Anchors

| Anchor | Company | Metric | Value | Date | Source | Model use |
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
| FACT_TENCENT_HUNYUAN_100B | Tencent | Hunyuan foundation model scale | Over 100B parameters and over 2T pretraining tokens | 2023-09-07 | SRC_TENCENT_HUNYUAN | Tencent parameter band를 closed-only에서 100B+ anchor로 보강. active serving capacity는 여전히 낮은 confidence. |
| FACT_MCKINSEY_2030_INFERENCE | Cross-company | 2030 inference demand direction | Inference expected to account for more than half of AI workloads and 30-40% of data center power demand by 2030 | 2026-02-24 | SRC_MCKINSEY_AI_WORKLOADS | 2030 weighted inference share 상승의 directional anchor. 2026 60%+ 주장은 fact로 채택하지 않음. |
| FACT_DELOITTE_2026_INFERENCE | Cross-company | 2026 inference compute share outlook | Inference cited as roughly two-thirds of compute in 2026 outlook | 2025-12 | SRC_DELOITTE_AI_POWER | 2026 base/bull inference share가 60%를 넘을 수 있는 상향 전망 anchor지만, 공식 fact로는 표시하지 않음. |
| FACT_EPOCH_TRAINING_POWER_RISK | Cross-company | Frontier training power can remain material | Individual frontier training runs may require large power blocks by 2030 | 2025-08 | SRC_EPRI_EPOCH_AI_POWER | Bear/base에서 training share를 남기는 보수 anchor. |

## Scenario Design

| Scenario | Deploy 2030 | Inference delta 2030 | Tokens/MW | MoE optimization | 설명 |
|---|---:|---:|---:|---:|---|
| Bear | 82% | -10%p | 82% | 92% | 전력 인허가/장비 조달 지연, MoE 최적화 둔화, inference 전환이 느린 경우 |
| Base | 100% | +0%p | 100% | 100% | 현재 공식 발표와 시장전망을 기준으로 한 staged deployment, MoE 효율 개선, inference mix 상승 |
| Bull | 118% | +8%p | 118% | 118% | 전력 energization이 빠르고, MoE/serving stack 최적화가 강하며, commercial inference 비중이 빠르게 상승 |
| Grid-Constrained / Efficiency-Upside | 72% | +4%p | 118% | 122% | 전력 투입은 지연되지만 MoE·quantization·batching 효율이 개선되어 token capacity 하락을 일부 상쇄 |

## Inference 60%+ Fact Check

- 2026년에 이미 전체 AI GW의 60% 이상이 inference라는 주장은 공식 company-level fact로 단정하지 않습니다.
- McKinsey/Deloitte는 inference 비중 상승 전망을 제공하지만, 업체별 active GW split disclosure가 아닙니다.
- EPRI/Epoch AI는 현재 AI power가 training, experiments, inference로 대략 나뉜다는 보수적 anchor를 제공합니다.
- 따라서 본 모델의 inference share는 `Scenario assumption`이며, source transparency에 맞춰 confidence를 별도 표기합니다.

## 2030 Scenario Envelope

| Scenario | Active power GW | Inference GW | Weighted inference share | Tokens/day | Delta vs Base 2030 |
|---|---:|---:|---:|---:|---:|
| Bear | 30.01 | 14.29 | 66% | 1.33Q | -48.0% |
| Base | 36.60 | 20.05 | 76% | 2.55Q | 0.0% |
| Bull | 43.16 | 26.14 | 84% | 4.27Q | 67.2% |
| Grid-Constrained / Efficiency-Upside | 26.35 | 15.20 | 80% | 2.40Q | -5.9% |

## Attribution Rules
- **Microsoft**: Microsoft-owned token은 Phi/MAI/Copilot serving으로, OpenAI model output은 OpenAI row에도 별도 표기
- **Google**: Google-owned Gemini token generation, Anthropic hosted capacity excluded from core
- **Meta**: Meta-owned consumer and open model serving; third-party hosted Llama not counted in Meta owner tokens
- **xAI**: xAI-owned Grok token generation; X social integration counted only when model generated
- **OpenAI**: OpenAI model output counted here, including OpenAI models served through Microsoft channels when model ownership is OpenAI
- **DeepSeek**: DeepSeek direct app/API tokens counted; third-party self-hosted derivatives excluded unless DeepSeek-operated
- **Alibaba**: Alibaba-operated Qwen serving counted; open-source third-party self-hosting excluded
- **Tencent**: Tencent-operated Hunyuan/Yuanbao tokens counted; embedded non-LLM media generation separated

## Evidence Rules

- Fact: official model docs/cards, company announcements, technical reports.
- Estimate: active power, inference/training share, utilization, company-level tokens/sec/MW.
- Scenario: 2027–2030 ramp, software efficiency CAGR, commercial token absorption.
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
| SRC_SEMIANALYSIS_INFERENCEX | Tier 2 | SemiAnalysis | 2025-2026 | Benchmark layer for tokens/sec/MW sensitivity, not company capacity | https://inferencex.semianalysis.com/about |
| SRC_ARXIV_INFERENCE_ENERGY | Tier 2 | arXiv | 2024-2026 | Joules/token sanity check, prefill/decode split, batching, quantization sensitivity | https://arxiv.org/search/?query=large+language+model+inference+energy+joules+per+token&searchtype=all |
| SRC_MCKINSEY_AI_WORKLOADS | Tier 2 | McKinsey & Company | 2026-02-24 | Inference share fact-check and 2030 workload mix directional anchor | https://www.mckinsey.com/featured-insights/week-in-charts/the-future-of-ai-workloads |
| SRC_DELOITTE_AI_POWER | Tier 2 | Deloitte | 2025-12 | Inference compute share outlook, used only as scenario cross-check | https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/compute-power-ai.html |
| SRC_EPRI_EPOCH_AI_POWER | Tier 2 | EPRI / Epoch AI | 2025-08 | Current AI power allocation sanity check across training, experiments, and inference | https://epoch.ai/blog/power-demands-of-frontier-ai-training |

## Validation

- Status: **PASS**
- closed_parameter_precision: PASS - closed model rows use bands/undisclosed labels, not single precise parameter values.
- moe_total_active: PASS - DeepSeek and Alibaba rows include total and active parameter bands.
- microsoft_openai_overlap: PASS - attribution rule separates OpenAI model-owner output and Microsoft customer-facing serving.
- anthropic_scope: PASS - Anthropic is excluded from core rows and reserved for comparator/hosted sensitivity.
