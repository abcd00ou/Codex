# LLMServingSim 2.0: A Unified Simulator for Heterogeneous and Disaggregated LLM Serving Infrastructure

## Source and Scope

Venue: ISPASS 2026, Best Paper Award  
Source: https://llmservingsim.ai/ and https://github.com/casys-kaist/LLMServingSim  
Copyright note: This note is a paraphrased research reading, not a reproduction of the original paper.

## Detailed English Reading

LLMServingSim 2.0 is one of the most directly relevant works for this project. It treats LLM serving as an infrastructure simulation problem rather than a single-device benchmark problem. The project page emphasizes production-fidelity metrics such as TTFT, TPOT, and throughput, driven by a vLLM-based layerwise profiler. It also supports heterogeneous hardware tiers including GPU, CPU, CXL, and PIM, plus parallelism strategies such as tensor, pipeline, expert, and data-parallel combinations.

The conceptual leap is that LLM inference has several layers of behavior that public benchmarks often hide. A request can go through prefill and decode phases. The decode phase is autoregressive and often memory-bound. Serving systems batch requests, evict or page KV cache, use multiple parallelism strategies, and respond to real workload traces rather than a fixed synthetic prompt. Disaggregated serving adds further complexity because compute, memory, and network resources may be separated.

LLMServingSim 2.0 therefore gives a framework for asking whether a proposed infrastructure configuration can actually deliver the intended user-facing latency and token throughput. It also includes ShareGPT-style traces and closed-loop agentic sessions, which is important because future workloads will involve tool calls, sub-requests, and irregular conversation flows rather than uniform single-turn prompts.

For a capacity model, this paper is a warning against using peak GPU throughput as a direct production token capacity number. It implies that a credible model needs a serving layer between hardware benchmark and business output.

## 상세 한글 독해 및 번역 요약

LLMServingSim 2.0은 이 프로젝트와 가장 직접적으로 연결되는 논문이다. 이 논문은 LLM inference를 GPU 한 장의 benchmark 문제가 아니라, datacenter serving infrastructure 전체의 simulation 문제로 본다. 중요한 지표는 단순 tokens/sec가 아니라 TTFT, TPOT, throughput, parallelism, scheduler behavior, memory tier, workload trace다.

LLM serving은 prefill과 decode 단계가 다르고, decode는 autoregressive 방식으로 token을 하나씩 생성한다. 이 과정에서 KV cache를 계속 읽고 쓰며, batch size와 context length에 따라 memory pressure가 크게 달라진다. 실제 serving system은 vLLM 같은 runtime scheduler, continuous batching, parallelism, cache management, network topology에 의해 성능이 결정된다. 따라서 public benchmark에서 특정 GPU가 높은 throughput을 보였다고 해서 그 값이 production token capacity가 되는 것은 아니다.

LLMServingSim 2.0이 중요한 또 하나의 이유는 heterogeneous and disaggregated infrastructure를 다룬다는 점이다. GPU만이 아니라 CPU, CXL, PIM 같은 tier가 섞이고, tensor/pipeline/expert/data parallelism이 결합될 수 있다. 또한 agentic workload처럼 tool call과 sub-request가 섞인 trace까지 고려한다.

요약하면 이 논문은 LLM capacity를 계산할 때 hardware benchmark와 실제 product output 사이에 반드시 serving simulation layer가 필요하다는 근거를 제공한다.

## 박종세 교수 전문성 관점

박 교수님은 LLM serving을 hardware, software, runtime, memory, network, workload trace가 결합된 end-to-end system으로 분석하는 전문가다. 특히 simulator artifact를 실제 연구 도구로 공개하는 점이 강하다.

## 내 프로젝트와의 연결점

`llm_token_capacity_project`의 `commercial_workload_fit_factor`는 이 논문을 기반으로 더 명확히 정의할 수 있다. 단일 haircut이 아니라 TTFT/TPOT, context length, KV cache, scheduler, parallelism, disaggregated memory, network, agentic trace를 포함하는 serving realism factor가 되어야 한다.
