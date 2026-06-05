# LLMServingSim 상세 독해

LLMServingSim은 박종세 교수님 연구 중 현재 프로젝트와 가장 직접적으로 연결되는 축입니다. `tokens/sec/MW`를 계산할 때 단순 GPU benchmark를 그대로 쓰면 위험하다는 점을 가장 잘 보여줍니다.

## 1. 왜 LLM serving simulator가 필요한가

LLM inference는 일반적인 image classification이나 단일 DNN inference와 다릅니다. 사용자가 prompt를 보내면 모델은 prompt를 읽고, output token을 하나씩 생성합니다. 이 과정은 request마다 길이가 다르고, batch 안의 request들도 서로 다른 시점에 끝납니다. 따라서 static benchmark로는 실제 serving behavior를 잘 설명하기 어렵습니다.

기존 accelerator simulator는 cycle-level로 정확하게 동작을 모사할 수 있지만 너무 느립니다. LLM serving은 수많은 token iteration과 request trace를 다뤄야 하므로, 지나치게 느린 simulator로는 datacenter-scale serving을 평가하기 어렵습니다.

LLMServingSim은 이 문제를 해결하기 위해 HW/SW co-simulation 방식을 택합니다. hardware behavior와 software scheduler behavior를 함께 보되, LLM decoder block의 반복성을 활용해 simulation을 빠르게 만듭니다.

## 2. LLMServingSim 2024의 핵심

2024 IISWC 논문인 `LLMServingSim: A HW/SW Co-Simulation Infrastructure for LLM Inference Serving at Scale`은 대규모 LLM serving을 빠르게 시뮬레이션하는 인프라입니다.

핵심 문제는 세 가지입니다.

1. Autoregressive generation 때문에 iteration마다 workload가 달라진다.
2. KV cache와 batch composition 때문에 memory behavior가 계속 바뀐다.
3. 기존 simulator는 정확하지만 serving trace 전체를 돌리기에는 너무 느리다.

LLMServingSim은 decoder block과 iteration-level behavior의 반복성을 이용합니다. 완전히 처음부터 모든 token generation을 cycle-level로 다시 시뮬레이션하지 않고, 반복되는 pattern을 재사용해 빠르게 전체 serving behavior를 추정합니다.

이 접근은 현재 프로젝트에서 매우 중요합니다. Public benchmark는 보통 특정 input/output length와 batch setting에서 나온 숫자입니다. 그러나 production에서는 request arrival, prompt length, output length, scheduler, KV cache pressure가 모두 변합니다. LLMServingSim은 이 차이를 줄이는 중간 layer입니다.

## 3. LLMServingSim 2.0의 확장

LLMServingSim 2.0은 2024 버전보다 더 넓은 serving infrastructure를 다룹니다. 핵심 확장은 heterogeneous and disaggregated serving입니다.

### Heterogeneous hardware

GPU만 보는 것이 아니라 CPU, CXL memory, PIM 같은 다른 hardware tier를 함께 고려합니다. 실제 datacenter는 점점 GPU-only 구조에서 벗어나 memory tier, host CPU, networking, offload device가 섞인 구조가 됩니다.

### Disaggregated memory

LLM serving에서 HBM이 부족하면 KV cache를 다른 memory tier로 옮기거나, CXL memory pool을 활용하거나, memory를 compute와 분리하는 설계를 고려할 수 있습니다. 하지만 이때 latency와 bandwidth penalty가 생기므로 simulator가 필요합니다.

### Parallelism support

LLMServingSim 2.0은 tensor parallelism, pipeline parallelism, expert parallelism, data parallelism 조합을 다룰 수 있는 방향을 갖습니다. 이는 MoE 모델과 대형 closed model serving에서 매우 중요합니다.

### Workload trace

ShareGPT-style trace나 agentic session workload를 다룬다는 점이 중요합니다. 실제 LLM 사용은 uniform single-turn prompt가 아닙니다. Agent가 tool을 호출하고, 여러 sub-task를 만들고, 긴 context를 유지하면 request pattern이 복잡해집니다.

## 4. 프로젝트에서 LLMServingSim을 어떻게 읽어야 하는가

현재 `llm_token_capacity_project`는 company별 power, GPU/ASIC mix, inference/training share, tokens/sec/MW를 추정합니다. 이때 가장 위험한 가정은 public benchmark의 `output_tok_s_mw`를 production capacity로 변환하는 부분입니다.

LLMServingSim은 이 변환에 필요한 질문들을 제공합니다.

- Benchmark의 input length와 production prompt length가 같은가.
- Output length와 user-facing session length가 같은가.
- Batch size가 SLO를 깨지 않는 수준인가.
- KV cache가 HBM 안에 들어가는가.
- Long-context/RAG/agentic workload에서 cache pressure가 얼마나 커지는가.
- Tensor/pipeline/expert parallelism이 network overhead를 얼마나 만든다.
- CXL/PIM offload가 throughput은 높이지만 latency를 악화시키지는 않는가.

## 5. 프로젝트에 반영할 수 있는 모델 구조

기존 구조가 다음과 같다면:

```text
GPU generation mix -> public output tokens/sec/MW -> commercial workload fit factor -> tokens/day
```

LLMServingSim을 반영한 구조는 다음에 가까워야 합니다.

```text
GPU/ASIC/PIM/CXL mix
-> model architecture class
-> context length and KV cache profile
-> request trace and batch policy
-> SLO target
-> parallelism and network topology
-> simulator-calibrated serving throughput
-> commercial workload fit factor
-> tokens/day
```

즉 `commercial_workload_fit_factor`를 하나의 감각적 haircut으로 두지 말고, system factor로 분해해야 합니다.

## 6. LLMServingSim이 박종세 교수 전문성을 보여주는 이유

이 연구는 박종세 교수님이 단순히 더 빠른 accelerator를 설계하는 연구자가 아니라는 점을 보여줍니다. 그는 LLM serving을 다음 요소가 결합된 시스템으로 봅니다.

- model architecture
- runtime scheduler
- memory hierarchy
- accelerator microarchitecture
- parallelism strategy
- workload trace
- user-facing latency
- simulator fidelity

이 관점은 현재 AI infrastructure modeling에 매우 중요합니다. 왜냐하면 2026-2030년의 token capacity는 GPU 구매량만으로 결정되지 않고, HBM, scheduler, memory tier, CXL/PIM, MoE routing, software maturity에 의해 크게 달라질 것이기 때문입니다.

## 7. 한 문장 요약

LLMServingSim은 `GPU가 이론적으로 몇 token/sec를 낼 수 있는가`가 아니라 `실제 serving system이 SLO를 만족하면서 몇 token/sec를 낼 수 있는가`를 묻는 연구입니다.
