# 기술 용어와 논문 구조 해설

이 파일은 논문을 읽기 전에 알아야 할 기술 용어를 비전공자 기준으로 풀어쓴 자료입니다. 박종세 교수님 논문들은 computer architecture, AI accelerator, memory system, serving scheduler, simulator가 섞여 있어 용어를 먼저 잡는 것이 중요합니다.

## 1. LLM inference serving 기본 구조

LLM serving은 사용자가 질문을 보냈을 때 모델이 답변 token을 생성해 반환하는 시스템입니다. 단순히 GPU가 빠른지만 보면 안 되고, 사용자가 체감하는 지연 시간과 동시에 처리할 수 있는 요청량을 함께 봐야 합니다.

### Prefill

사용자 prompt를 한 번에 읽어 모델 내부 상태를 만드는 단계입니다. 긴 prompt, 긴 context, RAG 문서, tool log가 많으면 prefill 비용이 커집니다. Prefill은 상대적으로 큰 행렬곱이 많아 GPU/NPU의 compute 성능이 중요합니다.

### Decode 또는 Generation

모델이 output token을 하나씩 생성하는 단계입니다. 다음 token을 만들려면 이전 token들의 key/value 정보를 계속 참조해야 합니다. 이때 KV cache를 읽는 비용이 커지고 memory bandwidth가 병목이 되기 쉽습니다.

### TTFT

Time To First Token입니다. 사용자가 요청한 뒤 첫 token이 나오기까지 걸리는 시간입니다. 사용자 경험과 agentic workflow에서 중요합니다. Prefill, queueing, scheduler, cold start가 TTFT에 영향을 줍니다.

### TPOT

Time Per Output Token입니다. 첫 token 이후 token 하나를 추가로 생성하는 데 걸리는 시간입니다. 긴 답변에서는 TPOT가 전체 latency를 좌우합니다. Decode 단계의 memory bandwidth와 KV cache 효율이 중요합니다.

### Throughput

단위 시간당 처리할 수 있는 token 수 또는 request 수입니다. 하지만 throughput이 높아도 TTFT/TPOT가 나쁘면 production serving에서는 쓸 수 없습니다. 그래서 논문들은 SLO를 함께 봅니다.

### SLO

Service Level Objective입니다. 예를 들어 첫 token은 1초 안에, 이후 token은 일정 속도 이상으로 반환해야 한다는 서비스 목표입니다. AI capacity는 raw throughput이 아니라 SLO를 만족하는 throughput으로 봐야 합니다.

## 2. KV cache와 HBM 병목

### KV cache

Transformer는 attention을 계산할 때 이전 token들의 key와 value를 저장합니다. 매번 처음부터 다시 계산하지 않기 위해 저장하는데, 이것이 KV cache입니다. Context length와 batch size가 커질수록 KV cache가 급격히 커집니다.

### HBM

High Bandwidth Memory입니다. GPU 옆에 붙는 매우 빠른 memory입니다. LLM serving에서는 모델 weight와 KV cache를 빠르게 읽어야 하므로 HBM 용량과 bandwidth가 모두 중요합니다.

### Memory capacity bottleneck

HBM에 저장할 수 있는 양이 부족한 상황입니다. 긴 context와 많은 동시 요청이 있으면 KV cache가 HBM을 채웁니다. 이때 batch size를 줄이거나, 더 많은 GPU를 쓰거나, cache를 압축하거나, CXL/DDR tier로 spill해야 합니다.

### Memory bandwidth bottleneck

저장 공간은 있어도 읽고 쓰는 속도가 부족한 상황입니다. Decode는 token마다 KV cache를 계속 읽기 때문에 memory bandwidth가 token 생성 속도를 제한할 수 있습니다.

## 3. Accelerator 종류

### GPU

범용 병렬 연산에 강한 accelerator입니다. NVIDIA H100/H200/B200/GB200 같은 GPU가 AI datacenter의 중심입니다. 장점은 software ecosystem과 범용성이고, 단점은 특정 inference workload에서 energy efficiency가 ASIC보다 낮을 수 있다는 점입니다.

### NPU

Neural Processing Unit입니다. DNN/LLM 같은 neural network 연산에 맞춘 accelerator입니다. GPU보다 특정 연산에 효율적일 수 있지만, software stack과 workload flexibility가 중요합니다.

### PIM

Processing-in-Memory입니다. memory 근처 또는 memory 내부에서 일부 연산을 수행해 data movement를 줄이는 방식입니다. NeuPIMs와 Pimba에서 중요한 개념입니다. 특히 memory bandwidth가 병목인 GEMV, attention, state update에 유리할 수 있습니다.

### ASIC

Application-Specific Integrated Circuit입니다. 특정 workload에 맞춘 전용 칩입니다. LPU, TPU, Trainium, Maia, MTIA 등이 이 범주에 들어갈 수 있습니다. 효율은 높을 수 있지만 workload가 바뀌면 장점이 줄어들 수 있습니다.

### CXL memory

Compute Express Link 기반 memory 확장/공유 기술입니다. HBM보다 느릴 수 있지만 더 큰 memory pool을 제공할 수 있습니다. LLM KV cache나 long-context serving에서 HBM 부족을 완화할 수 있지만 latency와 bandwidth penalty가 생깁니다.

## 4. 병렬화와 scheduler

### Batching

여러 요청을 묶어서 한 번에 처리하는 방식입니다. GPU utilization을 높이지만 request별 latency와 KV cache pressure가 커질 수 있습니다.

### Continuous batching

새 요청과 진행 중인 요청을 동적으로 섞어 batch를 유지하는 serving 기법입니다. vLLM 같은 runtime에서 중요합니다.

### Tensor parallelism

모델의 큰 행렬 연산을 여러 GPU에 나눠 계산하는 방식입니다. GPU 간 통신이 중요합니다.

### Pipeline parallelism

모델 layer를 여러 GPU에 나눠 순차적으로 실행하는 방식입니다. pipeline bubble과 scheduling이 중요합니다.

### Expert parallelism

MoE 모델에서 expert를 여러 GPU에 나눠 배치하는 방식입니다. all-to-all communication과 routing overhead가 생깁니다.

### Data parallelism

같은 모델 복제본을 여러 GPU에 두고 request를 나눠 처리하는 방식입니다. serving에서는 replication과 autoscaling에 연결됩니다.

## 5. 논문을 읽는 구조

박종세 교수님 논문은 보통 다음 구조로 읽으면 이해가 쉽습니다.

1. Problem: 기존 GPU/NPU/serving system이 어떤 병목을 갖는가.
2. Observation: 실제 workload를 분석하면 병목이 compute인지 memory인지 scheduler인지 밝힌다.
3. Mechanism: 병목을 줄이는 hardware/software 구조를 제안한다.
4. Evaluation: baseline 대비 latency, throughput, energy, accuracy loss, simulation error를 비교한다.
5. Implication: 이 결과가 production AI infrastructure에 어떤 의미를 갖는지 해석한다.

## 6. 내 프로젝트에 필요한 번역표

| 영어 용어 | 한국어 의미 | 프로젝트에서의 쓰임 |
|---|---|---|
| serving | 모델을 서비스로 배포해 요청을 처리하는 것 | token capacity 계산의 실제 대상 |
| inference | 학습된 모델로 답을 생성하는 것 | training과 분리되는 전력 사용처 |
| prefill | prompt를 읽어 초기 상태를 만드는 단계 | 긴 context/RAG 비용 |
| decode | output token을 하나씩 생성하는 단계 | KV cache/HBM 병목 |
| KV cache | 이전 token의 key/value 저장소 | HBM capacity와 bandwidth driver |
| TTFT | 첫 token까지 시간 | 사용자 체감 latency |
| TPOT | token 하나당 생성 시간 | 긴 답변 latency |
| SLO | 서비스 목표 지연 시간 | raw throughput이 아닌 production capacity 기준 |
| PIM | memory 근처에서 연산하는 구조 | memory-bound workload 보완 |
| CXL | memory 확장/공유 인터페이스 | HBM 부족 완화, latency risk |
| NPU | neural network 전용 accelerator | purpose-built accelerator 가정 |
| ASIC | 특정 용도 전용 칩 | GPU 대비 efficiency uplift 검토 |
| simulator | 실제 hardware/software 동작을 모사하는 도구 | benchmark와 production 사이 evidence layer |
