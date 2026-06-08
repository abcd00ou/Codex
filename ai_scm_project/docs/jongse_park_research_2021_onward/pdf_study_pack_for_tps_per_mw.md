# 박종세 교수 논문 기반 TPS/MW 공부자료와 모델링 노트

작성일: 2026-06-08  
입력 자료: 사용자가 로컬 폴더에 복사한 박종세 교수 관련 PDF 11개  
목적: InferenceX benchmark 기반 `tokens/sec/MW` 설계 근거를 강화하고, 실제 simulation 도구 개발 방향을 잡는다.

## 1. 이 자료의 목적

현재 프로젝트는 InferenceX benchmark에서 얻은 `output_tok_s_mw`를 사용해 LLM token capacity를 계산한다. 문제는 benchmark 숫자가 곧바로 production serving capacity가 아니라는 점이다.

박종세 교수님 논문들은 이 간극을 메우는 데 매우 좋다.

```text
InferenceX
-> 조건부 benchmark: GPU/model/precision/ISL/OSL/concurrency별 tok/s/MW

박종세 교수 논문
-> 왜 benchmark가 실제 serving에서 달라지는지 설명
-> KV cache, HBM, scheduler, PIM, CXL, quantization, simulator 근거 제공

우리 도구
-> InferenceX row를 LLMServingSim-style workload scenario로 변환
-> TPS/MW에 serving realism factor를 붙이는 준비
```

## 2. 우선순위 논문

### 1순위: LLMServingSim 2.0

파일:

- `2026-ispass-llmservingsim2.0.pdf`
- `2025-cal-llmservingsim2.0.pdf`
- `2024-iiswc-llmservingsim.pdf`
- `2024-mlarchsys-llmservingsim.pdf`

핵심 메시지:

LLM serving 성능은 hardware 또는 software 선택 하나로 결정되지 않는다. Runtime에서 batching, routing, placement, caching, offloading, memory management, interconnect, power가 서로 영향을 주며 변한다.

중요한 수치:

- 2024 LLMServingSim: 실제 GPU serving behavior를 평균 14.7% 이하 error로 따라가고, 기존 accelerator simulator 대비 91.5배 빠른 simulation speed를 제시.
- 2026 LLMServingSim 2.0: throughput, latency breakdown, memory usage, power consumption을 실제 serving deployment 대비 평균 0.95% error로 재현한다고 주장. 복잡한 configuration에서도 약 10분 단위 practical simulation time을 제시.

프로젝트 의미:

`commercial_workload_fit_factor`를 감으로 두지 말고, 다음 factor로 나눠야 한다.

```text
serving_realism_factor =
  f(ISL/OSL distribution,
    request arrival,
    batching policy,
    TTFT/TPOT SLO,
    KV cache residency,
    memory tier,
    parallelism,
    offloading,
    power model)
```

### 2순위: Oaken

파일:

- `2025-isca-oaken.pdf`

핵심 메시지:

LLM serving에서 batching은 throughput을 높이지만, attention operation은 request별 KV cache를 계속 읽어야 하므로 memory bandwidth bottleneck이 된다. HBM은 bandwidth는 높지만 capacity가 제한적이고, long context는 KV cache size를 더 키운다.

Oaken의 구조:

```text
문제:
  KV cache가 HBM capacity와 bandwidth를 동시에 압박

기존 해결:
  KV cache quantization

기존 한계:
  online outlier detection 또는 mixed precision cost가 너무 커서 speedup을 잡아먹음

Oaken:
  offline threshold + online scaling
  quantization/dequantization engine
  memory management unit
```

프로젝트 의미:

InferenceX에 `precision`이 있다고 해도 이것이 항상 KV cache precision을 의미하지는 않는다. 따라서 TPS/MW 모델에서는 다음을 구분해야 한다.

| 구분 | 모델링 의미 |
|---|---|
| weight/activation quantization | GEMM throughput과 memory footprint에 영향 |
| KV cache quantization | decode memory bandwidth/capacity에 직접 영향 |
| Oaken-style hybrid KV quantization | long-context TPS/MW 회복 scenario |

### 3순위: Pimba

파일:

- `2025-micro-pimba.pdf`
- `2025-micro-pimba-2.pdf`

핵심 메시지:

Transformer 이후의 post-transformer 모델, 예를 들어 SSM, Mamba-2, linear attention, RNN 계열도 long-context serving에서 memory bandwidth bottleneck을 피하지 못한다. 병목의 이름이 KV cache에서 state update로 바뀔 수 있을 뿐이다.

Pimba의 구조:

```text
Transformer:
  QKV generation
  previous KV cache fetch
  new KV cache append
  attention
  FFN

SSM / Mamba-style:
  state fetch
  state update
  recurrent/linear operations

Pimba:
  state update와 attention 계열 operation을 PIM으로 offload
  MX8 quantized arithmetic 사용
  GPU와 PIM을 함께 쓰는 heterogeneous serving 구조
```

중요한 수치:

- LLM-optimized GPU 대비 최대 4.1배 generation throughput.
- GPU+PIM system 대비 최대 2.1배 generation throughput.

프로젝트 의미:

장기적으로 transformer-only TPS/MW 가정은 위험하다. post-transformer가 확산되면 KV cache pressure는 줄어들 수 있지만 state update memory pressure가 생긴다. PIM은 GPU 대체가 아니라 memory-bound operation offload로 보는 것이 더 정확하다.

### 4순위: PyTorchSim

파일:

- `2025-micro-pytorchsim.pdf`

핵심 메시지:

NPU/ASIC 성능을 믿을 만하게 평가하려면 simulator가 필요하다. PyTorchSim은 PyTorch 2, MLIR/LLVM, RISC-V ISA, Gem5/Spike, tile-level simulation을 연결한다.

중요한 수치:

- TPUv3 대비 mean absolute error 11.5%.
- Accel-Sim 대비 최대 139배 speedup.

프로젝트 의미:

TPU, Trainium, Maia, MTIA, LPU 같은 purpose-built accelerator의 TPS/MW를 vendor claim으로만 쓰면 안 된다. Simulator fidelity tier를 둬야 한다.

### 5순위: Neo, Cocoon, PLDI partial tracing

파일:

- `2026-asplos-neo.pdf`
- `2510.07304v1.pdf`
- `pldi26.pdf`

프로젝트 직접성은 낮지만 다음 맥락을 준다.

| 논문 | 의미 |
|---|---|
| Neo | text token 밖의 3D/AR/on-device workload도 memory bandwidth bottleneck이 큼 |
| Cocoon | privacy-preserving training은 extra overhead와 near-memory processing 필요 |
| PLDI partial tracing | production system의 runtime/memory safety도 latency와 efficiency에 영향 |

## 3. 공부 순서

처음부터 논문 전체를 완벽히 읽으려고 하면 길을 잃기 쉽다. 아래 순서로 보면 된다.

### Step 1. LLM serving 기본 구조

먼저 이 네 단어를 이해한다.

| 용어 | 직관 |
|---|---|
| Prefill | prompt를 읽는 단계. 긴 input이면 비싸다. |
| Decode | output token을 하나씩 만드는 단계. KV cache를 계속 읽는다. |
| TTFT | 첫 token까지 걸리는 시간. 사용자가 기다리는 첫 체감 latency. |
| TPOT | token 하나당 생성 시간. 긴 답변의 속도. |

### Step 2. KV cache와 HBM

KV cache는 이전 token의 key/value activation 저장소다. Context가 길고 batch가 클수록 커진다.

```text
KV pressure roughly grows with:
  model layers
  hidden/head dimensions
  ISL + generated tokens
  concurrency
  KV precision bytes
```

현재 bridge tool은 단순 proxy로 다음을 쓴다.

```text
kv_pressure_proxy = ISL * concurrency
decode_work_proxy = OSL * concurrency
```

이 proxy는 물리적 byte 모델은 아니지만, 어떤 benchmark row가 long-context pressure를 크게 받는지 줄 세우는 데는 쓸 수 있다.

### Step 3. InferenceX와 LLMServingSim의 차이

InferenceX는 다음 질문에 답한다.

```text
이 GPU/model/precision/ISL/OSL/concurrency 조건에서 tok/s/MW가 얼마인가?
```

LLMServingSim은 다음 질문에 답한다.

```text
그 조건들이 실제 request stream으로 들어오고,
scheduler가 batch를 만들고,
KV cache가 HBM/CXL/PIM tier에 놓이며,
SLO를 만족해야 할 때
실제 serving throughput과 latency는 어떻게 변하는가?
```

### Step 4. TPS/MW 모델에 붙이는 법

기존 모델:

```text
InferenceX output_tok_s_mw
* commercial_workload_fit_factor
= production_like_tps_per_mw
```

개선 모델:

```text
InferenceX output_tok_s_mw
* sequence_realization_factor
* scheduler_realization_factor
* memory_tier_factor
* kv_quantization_factor
* power_correction_factor
= production_like_tps_per_mw
```

여기서 첫 번째로 구현 가능한 것은 `sequence_realization_factor`다.

```text
sequence_realization_factor =
  output_tok_s_mw(ISL, OSL, concurrency)
  / output_tok_s_mw(1024, 1024, same config)
```

## 4. 실제 도구 개발 현황

추가한 도구:

```text
llm_token_capacity_project/tools/generate_llmservingsim_bridge.py
```

실행:

```bash
.venv/bin/python llm_token_capacity_project/tools/generate_llmservingsim_bridge.py
```

생성물:

```text
llm_token_capacity_project/outputs/reports/llmservingsim_bridge_surface.csv
llm_token_capacity_project/outputs/reports/llmservingsim_bridge_report.md
```

도구가 하는 일:

1. InferenceX normalized benchmark CSV를 읽는다.
2. H200/B200/GB200 기준으로 model, gpu, framework, precision, gpu_count, ISL, OSL, concurrency별 row를 묶는다.
3. `output_tok_s_mw`, `input_tok_s_mw`, `total_tok_s_mw`, TTFT/TPOT, power의 중앙값을 계산한다.
4. `ISL * concurrency`로 KV pressure proxy를 만든다.
5. 같은 config의 `1024/1024` baseline 대비 realization factor를 계산한다.
6. LLMServingSim workload JSONL로 넘기기 쉬운 scenario table을 만든다.

## 5. 이번 실행에서 보이는 초기 insight

도구 실행 결과 900개의 grouped benchmark surface row가 생성됐다.

가장 큰 long-context degradation 예시는 Llama 70B 계열에서 많이 보였다. 같은 config의 `1024/1024` baseline 대비 `8192/1024` 조건에서 realization이 0.21-0.40 수준까지 내려가는 row들이 있었다.

이것은 중요한 신호다.

```text
1024/1024 benchmark만 보고 TPS/MW를 쓰면
long-context workload capacity를 크게 과대평가할 수 있다.
```

다만 이 값은 아직 simulator output이 아니다. InferenceX benchmark surface 안에서의 sequence sensitivity다. 다음 단계는 이 row들을 LLMServingSim workload JSONL로 변환해 dynamic batching, queueing, KV cache residency, SLO까지 반영하는 것이다.

## 6. 다음 개발 단계

### v0.1 완료

- InferenceX benchmark surface 생성.
- ISL/OSL/concurrency 기반 sequence sensitivity 계산.
- KV pressure proxy 생성.
- CSV/Markdown report 생성.

### v0.2

- `llmservingsim_workload_scenarios.jsonl` 자동 생성.
- short chat, RAG, coding agent, long-context agent 4개 scenario 생성.
- arrival rate를 synthetic하게 부여.

### v0.3

- model architecture metadata 추가.
- layer 수, head 수, hidden dimension, KV heads, KV dtype bytes 기반 explicit KV cache byte estimator 추가.

### v0.4

- LLMServingSim output CSV를 읽어서 InferenceX row와 join.
- `simulated_realization_factor` 계산.
- company별 workload mix에 weighted factor 적용.

### v0.5

- 기존 `generate_llm_token_capacity_report.py`의 `commercial_workload_fit_factor`를 근거 테이블 기반으로 교체.

## 7. 보고서에 넣기 좋은 문장

아래 문장은 executive report에 바로 들어갈 수 있다.

```text
Public InferenceX throughput is treated as a benchmark anchor, not as production capacity. To avoid overestimating commercial token supply, we apply a serving-realism layer motivated by LLMServingSim 2.0, which models runtime interaction among batching, routing, KV-cache residency, memory tiering, interconnect behavior, and power. Sequence-length sensitivity is first approximated from InferenceX ISL/OSL/concurrency grids; future iterations will replace this proxy with simulator-backed realization factors.
```

한글:

```text
InferenceX의 public throughput은 생산 capacity 자체가 아니라 benchmark anchor로 취급한다. 상용 token 공급능력 과대평가를 피하기 위해 LLMServingSim 2.0의 관점, 즉 batching, routing, KV cache residency, memory tiering, interconnect, power가 runtime에서 상호작용한다는 관점을 serving-realism layer로 반영한다. 현재는 InferenceX의 ISL/OSL/concurrency grid에서 sequence-length sensitivity를 먼저 추정하고, 이후 LLMServingSim 실행 결과 기반 realization factor로 교체한다.
```

