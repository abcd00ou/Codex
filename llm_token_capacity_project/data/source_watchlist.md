# Source Watchlist

이 파일은 아직 모델 숫자로 직접 반영하지 않았지만, 다음 learning cycle에서 검토할 가치가 높은 source를 관리합니다.

## Watchlist Rules

- Watchlist entry는 fact anchor가 아닙니다.
- 숫자 모델에 반영하려면 각 assumption agent의 `evidence.md`에 source-reviewed evidence로 승격해야 합니다.
- benchmark, consulting, vendor, practitioner source는 회사별 production fact가 아니라 proxy/context로 사용합니다.
- 원문 URL, 발행자, 날짜, claim 단위, 적용 가능한 assumption field를 확인해야 합니다.

## Current Watchlist

| source_id | source | publisher / owner | url | likely use | evidence class cap | target agents | status |
|---|---|---|---|---|---|---|---|
| WATCH_INFERENCEX | InferenceX / InferenceMAX | SemiAnalysis | https://inferencex.semianalysis.com/ | LLM inference benchmark, serving stack, GPU economics, tokens/MW sanity check | Proxy / Benchmark | A08, A09 | pending review |
| WATCH_INTROL | Introl AI infrastructure content | Introl | https://introl.com/ | AI data center deployment, power/cooling/rack/GPU infrastructure practitioner context | Context / Proxy | A01, A02, A03, A04 | pending review |
| WATCH_DELOITTE_AI_DC | Deloitte AI/data center/semiconductor insights | Deloitte | https://www.deloitte.com/ | AI data center demand, power/cooling investment, enterprise AI adoption, semiconductor supply-chain framing | Market Context / Scenario | A01, A02, A05, A06, A10 | pending review |
| WATCH_AI_2027 | AI 2027 scenario | AI Futures Project | https://ai-2027.com/ | Aggressive AI capability timeline, compute-demand shock, automation/takeoff scenario stress-test | Scenario / Stress Test | A05, A06, A08, A09, A10, Orchestrator | pending review |
| WATCH_2026_SERVING_ENERGY | 2026 inference serving and energy papers | IBM Research / Joule / arXiv | see docs/agent_learning_expansion_pack.md | Prefill-decode disaggregation, joules/query, SLO-aware resource allocation, speculative decoding latency | Paper / Benchmark / Proxy | A08, A09 | pending review |

## Review Notes

### WATCH_INFERENCEX

InferenceX should be treated as a benchmark/proxy layer. It can improve the `tokens_per_second_per_mw`, utilization, serving efficiency, and benchmark sanity-check assumptions, but it should not be described as a company-specific production telemetry source unless the original source explicitly provides that claim.

Recommended agent flow:

1. A08 reviews tokens/sec/GPU, tokens/sec/MW, model/hardware benchmark methodology.
2. A09 reviews utilization, batching, latency/SLO and serving-stack implications.
3. Orchestrator checks whether benchmark reference diverges from main forecast by more than 50%.

### WATCH_INTROL

Introl content should be treated as practitioner context unless an article cites a primary source. It may be useful for deployment bottlenecks, power availability, cooling, rack density, construction pace, and GPU cluster operationalization. It should not directly set company capacity numbers without a primary source.

Recommended agent flow:

1. A01 reviews whether content helps classify announced/contracted/planned/operational capacity.
2. A02 reviews active deployment bottlenecks and energization timing.
3. A03/A04 review facility overhead and AI workload share context.

### WATCH_DELOITTE_AI_DC

Deloitte reports should be treated as consulting/market context unless they cite primary company disclosures or official statistics. They are useful for understanding AI data center demand growth, power/cooling capex, enterprise AI adoption, semiconductor supply-chain pressure, and scenario framing. They should not directly set company-level active GW, inference share, or token generation values without a primary source.

Recommended agent flow:

1. A01/A02 review Deloitte data center and power-demand reports for macro deployment constraints and investment timing.
2. A05/A06 review generative AI adoption and workload mix discussions for inference/training scenario framing.
3. A10 reviews Deloitte cloud/vendor ecosystem discussion for attribution risks between model owner, cloud host, and enterprise product owner.
4. Orchestrator uses Deloitte only as market-context support unless a Deloitte figure is traced to official company, government, or standards-body data.

### WATCH_AI_2027

AI 2027 should be treated as a scenario and stress-test source, not as factual company telemetry. It is useful for exploring what happens if AI capability, agent adoption, automation, and compute demand accelerate faster than the Base scenario. It should not directly set company-level active GW, inference share, utilization, or tokens/MW values.

Recommended agent flow:

1. A05 reviews whether aggressive agent/adoption scenarios imply higher commercial inference demand.
2. A06 reviews whether faster capability development implies sustained or higher training/post-training reserve.
3. A08/A09 review whether automation and agentic workloads change tokens/sec/MW and utilization assumptions through longer context, tool-use loops, and higher reasoning/test-time compute.
4. A10 reviews whether product owner/model owner attribution becomes harder under agentic enterprise deployment.
5. Orchestrator may create a separate "AI-2027 stress" scenario only after assumptions are explicitly labeled Scenario and not mixed into Base.

### WATCH_2026_SERVING_ENERGY

This group includes IBM's 2026 work on prefill-decode disaggregation, Joule/Cell Press inference energy work, and 2026 arXiv papers on heterogeneous inference, SLO-aware allocation, prefill-as-a-service, and speculative decoding latency. These should be used to improve A08/A09 learning depth, especially benchmark-to-production gap, energy/query, utilization, and latency-SLO reserve logic.

Recommended agent flow:

1. A08 classifies each paper as mechanism, benchmark, or proxy before touching tokens/sec/MW.
2. A09 extracts utilization, SLO, batching, and disaggregation implications.
3. Orchestrator checks whether changes belong in Base, Bull/Bear, or a separate high-reasoning/test-time-compute scenario.
