# Reference Research Landscape

생성일: 2026-05-15

이 문서는 LLM token capacity simulation과 assumption agent 학습에 사용할 고전문성 리포트/논문 후보를 정리합니다. 각 자료는 바로 숫자에 반영하는 것이 아니라, source quality와 evidence class를 검토한 뒤 해당 agent의 `evidence.md`로 승격해야 합니다.

더 긴 학습 커리큘럼은 `docs/expert_learning_pack.md`와 `outputs/reports/expert_learning_pack_kr.docx`를 사용합니다.

## 사용 원칙

- 회사 공식 발표, 정부/기관 보고서, peer-reviewed 또는 arXiv 논문은 우선 검토합니다.
- 컨설팅/시장조사 리포트는 market context와 scenario framing에 유용하지만, company-level active GW나 token generation fact로 직접 쓰지 않습니다.
- benchmark와 inference engineering 논문은 mechanism/proxy로 사용합니다.
- 유료 리포트나 뉴스 전문은 복사하지 않고, title, publisher, date, URL, 핵심 claim, 적용 가능한 assumption만 기록합니다.

## 1. Power, Grid, Data Center Energy

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| Energy and AI | IEA | https://www.iea.org/reports/energy-and-ai | 글로벌 데이터센터 전력 수요, 전력 공급, macro boundary | A01, A02, A03 |
| Key Questions on Energy and AI | IEA | https://www.iea.org/reports/key-questions-on-energy-and-ai | AI 전력 수요 관련 FAQ와 업데이트된 policy framing | A01, A02 |
| 2024 United States Data Center Energy Usage Report | LBNL / DOE | https://buildings.lbl.gov/publications/2024-lbnl-data-center-energy-usage-report | 미국 데이터센터 에너지 사용 baseline, AI server power assumptions | A01, A02, A03, A04 |
| Powering Intelligence | EPRI | https://www.epri.com/research/products/000000003002028905 | 미국 데이터센터 전력 시나리오, grid planning context | A01, A02 |
| Scaling Intelligence | EPRI / Epoch AI | https://www.epri.com/research/products/000000003002033669 | frontier training power, total AI power capacity scenario | A02, A06 |
| Global Data Center Survey 2024 | Uptime Institute | https://uptimeinstitute.com/resources/research-and-reports/uptime-institute-global-data-center-survey-results-2024 | PUE, power/cooling, 운영자 설문 기반 데이터센터 현실 | A03, A04 |
| Cooling Systems Survey 2024 | Uptime Institute | https://intelligence.uptimeinstitute.com/sites/default/files/2024-05/Uptime%20Institute%20Cooling%20Systems%20Survey%202024_0.pdf | liquid cooling, cooling architecture, rack density context | A03 |
| Data Centers and Their Energy Consumption: FAQ | Congressional Research Service | https://www.congress.gov/crs-product/R48646 | 미국 정책/전력망 관점의 데이터센터 FAQ | A01, A02 |
| Electricity Demand and Grid Impacts of AI Data Centers | arXiv | https://arxiv.org/abs/2509.07218 | AI 데이터센터 load 특성과 grid impact review | A01, A02, A05, A06 |

## 2. Training Compute, Scaling Laws, Frontier Model Cost

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| Scaling Laws for Neural Language Models | Kaplan et al. | https://arxiv.org/abs/2001.08361 | training compute, model size, data scaling의 이론 기반 | A06, A07 |
| Training Compute-Optimal Large Language Models | Hoffmann et al. | https://arxiv.org/abs/2203.15556 | Chinchilla scaling, compute-optimal model/data allocation | A06, A07 |
| Compute Trends Across Three Eras of Machine Learning | Sevilla et al. | https://arxiv.org/abs/2202.05924 | historical training compute trend | A06 |
| Training compute of frontier AI models grows by 4-5x per year | Epoch AI | https://epoch.ai/blog/training-compute-of-frontier-ai-models-grows-by-4-5x-per-year | frontier training compute growth anchor | A06 |
| How much power will frontier AI training demand in 2030? | Epoch AI | https://epoch.ai/blog/power-demands-of-frontier-ai-training | training run power envelope, not annual average | A02, A06 |
| Can AI scaling continue through 2030? | Epoch AI | https://epoch.ai/blog/can-ai-scaling-continue-through-2030 | 2030 training scale feasibility, power/data/capex bottlenecks | A06 |
| The rising costs of training frontier AI models | arXiv | https://arxiv.org/abs/2405.21015 | training cost model, hardware/energy/cloud/staff cost | A06 |
| Stanford AI Index 2025 | Stanford HAI | https://hai.stanford.edu/ai-index/2025-ai-index-report | AI capability, cost, hardware, inference cost macro tracking | A06, A08, A10 |

## 3. Inference Serving, Tokens/MW, Utilization

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| Efficient Memory Management for LLM Serving with PagedAttention | arXiv / vLLM | https://arxiv.org/abs/2309.06180 | KV cache, memory fragmentation, serving throughput mechanism | A08, A09 |
| Splitwise: Efficient generative LLM inference using phase splitting | arXiv / Microsoft Research | https://arxiv.org/abs/2311.18677 | prefill/decode phase split, heterogeneous serving cluster | A08, A09 |
| Splitwise Microsoft Research blog | Microsoft Research | https://www.microsoft.com/en-us/research/blog/splitwise-improves-gpu-usage-by-splitting-llm-inference-phases/ | practitioner-friendly explanation of phase splitting | A08, A09 |
| DistServe: Disaggregating Prefill and Decoding | arXiv / OSDI | https://arxiv.org/abs/2401.09670 | TTFT/TPOT SLO, goodput, prefill/decode disaggregation | A08, A09 |
| Prefill-Decode Aggregation or Disaggregation? | arXiv | https://arxiv.org/abs/2508.01989 | when PD aggregation/disaggregation is optimal | A08, A09 |
| InferenceX / InferenceMAX | SemiAnalysis | https://inferencex.semianalysis.com/ | benchmark/proxy for serving efficiency and tokens/MW sanity check | A08, A09 |
| LLM inference price trends | Epoch AI | https://epoch.ai/data-insights/llm-inference-price-trends | inference price trend proxy, not production efficiency fact | A08 |

## 4. Hardware, Accelerator, Cluster Architecture

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| NVIDIA GB200 NVL72 | NVIDIA | https://www.nvidia.com/en-us/data-center/gb200-nvl72/ | rack-scale Blackwell system, NVLink domain, liquid-cooled AI system | A02, A03, A08 |
| NVIDIA DGX GB Rack Scale Systems User Guide | NVIDIA Docs | https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html | rack hardware, liquid cooling, power shelf, NVL72 architecture | A02, A03 |
| NVIDIA H100 Tensor Core GPU | NVIDIA | https://www.nvidia.com/en-us/data-center/h100/ | Hopper baseline for GPU TDP/performance assumptions | A08 |
| NVIDIA H200 Tensor Core GPU | NVIDIA | https://www.nvidia.com/en-us/data-center/h200/ | HBM capacity/bandwidth uplift versus H100 | A08 |
| Ironwood: TPU for the age of inference | Google Cloud | https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ | Google inference-oriented TPU, scale-up pod, HBM, perf/W direction | A05, A08 |
| Cloud TPU v5e documentation | Google Cloud | https://docs.cloud.google.com/tpu/docs/v5e | TPU serving/training deployment concepts | A05, A08, A09 |
| Project Rainier | AWS / Amazon | https://www.aboutamazon.com/news/aws/aws-project-rainier-ai-trainium-chips-compute-cluster | Anthropic/AWS Trainium2 cluster, host/model-owner attribution | A02, A06, A10 |
| Amazon EC2 Trn2 | AWS | https://aws.amazon.com/ec2/instance-types/trn2/ | Trainium2 instance positioning and specs | A08, A10 |
| Amazon EC2 Inf2 | AWS | https://aws.amazon.com/ec2/instance-types/inf2/ | Inferentia2 inference accelerator context | A08 |

## 5. Market, Consulting, Investment Context

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| AI infrastructure gaps | Deloitte Insights | https://www.deloitte.com/us/en/insights/industry/power-and-utilities/data-center-infrastructure-artificial-intelligence.html | AI data center infrastructure survey, power/grid challenge framing | A01, A02, A05 |
| Beyond compute: Infrastructure that powers and cools AI data centers | McKinsey | https://www.mckinsey.com/industries/industrials-and-electronics/our-insights/beyond-compute-infrastructure-that-powers-and-cools-ai-data-centers | power/cooling infrastructure investment and constraints | A02, A03 |
| How data centers and energy sector can sate AI's hunger for power | McKinsey | https://www.mckinsey.com/industries/private-capital/our-insights/how-data-centers-and-the-energy-sector-can-sate-ais-hunger-for-power | US data center power demand, build timelines, generation/transmission mismatch | A01, A02 |
| The next big shifts in AI workloads and hyperscaler strategies | McKinsey | https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-next-big-shifts-in-ai-workloads-and-hyperscaler-strategies | workload split, hyperscaler AI strategy context | A05, A06, A10 |
| AI Changes Big and Small Computing | Bain & Company | https://www.bain.com/insights/ai-changes-big-and-small-computing-tech-report-2024/ | AI computing architecture, edge/data center shift, supply chain framing | A04, A05, A10 |
| Semiconductor and Beyond 2026 | PwC | https://www.pwc.com/gx/en/industries/technology/pwc-semiconductor-and-beyond-2026-full-report.pdf | semiconductor/HBM/datacenter server market context | A07, A08 |
| AI 2027 | AI Futures Project | https://ai-2027.com/ | aggressive capability/adoption stress scenario only | A05, A06, A08, A09, A10 |

## 6. AI Data Center Build-Out, TCO, and Infrastructure Detail

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| SemiAnalysis Datacenter Industry Model | SemiAnalysis | https://newsletter.semianalysis.com/p/datacenter-model | critical IT power, AI accelerator deployment, facility-level modeling | A01, A02, A04 |
| SemiAnalysis Models & Research | SemiAnalysis | https://semianalysis.com/models-research/ | AI cloud TCO, datacenter model, compute supply/demand | A01, A02, A08, A10 |
| 100,000 H100 Clusters | SemiAnalysis | https://newsletter.semianalysis.com/p/100000-h100-clusters-power-network | cluster power, network topology, reliability, checkpointing context | A02, A04, A06 |
| Datacenter Anatomy Part 1: Electrical Systems | SemiAnalysis | https://newsletter.semianalysis.com/p/datacenter-anatomy-part-1-electrical | electrical system, critical IT power, power chain | A01, A02, A03 |
| GPUs account for about 40% of power usage in AI data centers | Epoch AI | https://epoch.ai/data-insights/gpus-power-usage-in-ai-data-centers | GPU/server/IT/facility power decomposition | A03, A04 |
| Data Center Switch Sales in AI Back-End Networks | Dell'Oro Group | https://www.prnewswire.com/news-releases/data-center-switch-sales-in-ai-back-end-networks-to-exceed-100-b-over-the-next-five-years-according-to-delloro-group-302367070.html | AI back-end network demand context | A04, A08 |

## 7. Memory and Supply Chain Context

| Source | Publisher | Link | Best Use | Target Agents |
|---|---|---|---|---|
| Semiconductor and Beyond 2026 | PwC / Omdia | https://www.pwc.com/gx/en/industries/technology/pwc-semiconductor-and-beyond-2026-full-report.pdf | HBM, semiconductor market, datacenter server growth | A07, A08 |
| AI Changes Big and Small Computing | Bain | https://www.bain.com/insights/ai-changes-big-and-small-computing-tech-report-2024/ | memory, storage, networking, data center supply-chain framing | A04, A08 |
| TrendForce Data Center Power Guide | TrendForce | https://www.trendforce.com/insights/data-center-power | power/cooling, HBM/DDR5/MRDIMM infrastructure context | A03, A04, A08 |
| SemiAnalysis memory / AI datacenter research | SemiAnalysis | https://semianalysis.com/ | HBM, accelerator, AI datacenter supply chain context | A07, A08 |

## Prioritized Reading Queue

### First 10 sources to read

1. IEA - Energy and AI
2. LBNL / DOE - 2024 U.S. Data Center Energy Usage Report
3. EPRI / Epoch AI - Scaling Intelligence
4. Epoch AI - Power demands of frontier AI training
5. PagedAttention / vLLM paper
6. Splitwise paper
7. DistServe paper
8. Google Ironwood TPU official blog
9. NVIDIA DGX GB Rack Scale Systems User Guide
10. SemiAnalysis Datacenter Anatomy / Datacenter Model

### Best use by assumption

| Assumption | Best first sources |
|---|---|
| A01 contracted_power_gw | IEA, LBNL, EPRI, McKinsey, SemiAnalysis Datacenter Model |
| A02 active_power_gw | LBNL, SemiAnalysis Datacenter Anatomy, NVIDIA DGX GB guide, AWS Project Rainier |
| A03 pue | Uptime, Google Data Centers, NREL, LBNL |
| A04 ai_workload_share | Epoch GPU power decomposition, SemiAnalysis 100k H100 cluster, Dell'Oro AI networks |
| A05 inference_power_share | Google Ironwood, TPU docs, McKinsey workload shifts, AI 2027 stress scenario |
| A06 training_power_share | Kaplan, Chinchilla, Epoch training compute, EPRI/Epoch Scaling Intelligence |
| A07 active_parameters | DeepSeek, Qwen, OpenAI docs, model cards |
| A08 tokens_per_second_per_mw | PagedAttention, Splitwise, DistServe, InferenceX, hardware docs |
| A09 utilization | DistServe, Splitwise, vLLM, InferenceX |
| A10 attribution_rule | OpenAI infrastructure, AWS/Anthropic, Microsoft/OpenAI, Deloitte/McKinsey ecosystem context |

## Evidence Promotion Rule

Before using any source in the numeric model:

1. Add it to `data/source_review_log.md`.
2. Add source-reviewed evidence to the relevant agent's `evidence.md`.
3. Classify the claim as Fact, Derived Estimate, Proxy, or Scenario.
4. If it changes a model field, add a proposed change to `state.md`.
5. Get orchestrator review if the change affects active power, inference share, training share, tokens/MW, utilization, or attribution.
