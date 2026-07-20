# Assumption Learning Kit

생성일: 2026-05-15

이 문서는 LLM token capacity simulation의 가정을 현실적인 숫자로 만들기 위한 학습 도구입니다. 숫자를 바로 외우기보다, 어떤 질문을 던지고 어떤 단위로 검증해야 하는지 익히는 것이 목적입니다.

## 먼저 외울 핵심 문장

- 계약 GW는 token capacity가 아니라 상한선입니다.
- operational deployment share는 계약 GW 중 전력망, 변전, 냉각, 랙, accelerator 수급을 통과한 비중입니다.
- inference GW는 active AI IT load 중 inference에 배정된 부분입니다.
- MoE 모델은 total parameter보다 active parameter가 token cost에 더 직접적입니다.
- headline tokens/sec/MW는 비교조건이 고정된 InferenceX output-token benchmark proxy에서 선택합니다.
- benchmark는 sanity check이지 회사별 실제 성능 fact가 아닙니다.

## 1페이지 계산 지도

```text
contracted GW
  -> operational deployment share -> active GW
  -> IT load GW = active GW / PUE
  -> AI IT load GW = IT load GW * AI workload share
  -> inference GW = AI IT load GW * inference share
  -> inference MW
  -> GPU workload avg TPS/MW = short/long/agentic share-weighted reference per GPU
  -> fleet TPS/MW = H200/B200/GB200/purpose-built share-weighted GPU workload average
  -> tokens/day = MW * fleet TPS/MW * commercial workload fit * 86,400
```

`utilization`, MoE 추가 uplift, architecture/software 개선률은 학습과 sensitivity에는 유효하지만 headline token 계산에는 곱하지 않습니다.

## Assumption Modules

### M1. 전력 capacity

**핵심 질문:** 계약된 GW 중 실제로 AI IT load가 되는 비중은?

**개념:** Contracted/planned capacity는 최대 경계값이고, active power는 인허가, 변전, 냉각, 랙 설치, GPU 수급을 통과한 운영 capacity입니다.

**초기 학습 band:** 2026 active/contracted: 15-45%, 2030: 45-80%

**주의할 오류:** planned GW를 곧바로 inference GW로 쓰는 오류

**관련 source:** SRC_OPENAI_STARGATE

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M2. PUE와 AI workload share

**핵심 질문:** 시설 전력에서 GPU/ASIC 서버가 실제로 먹는 전력은?

**개념:** PUE는 facility power를 IT load로 바꾸는 계수이고, AI workload share는 IT load 중 AI cluster가 차지하는 비중입니다.

**초기 학습 band:** PUE: 1.10-1.30, AI workload share: 70-95%

**주의할 오류:** facility MW, IT MW, GPU board power를 같은 숫자로 취급

**관련 source:** SRC_GOOGLE_IRONWOOD; SRC_NVIDIA_H100

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M3. Training / inference mix

**핵심 질문:** 전체 AI IT load 중 inference가 몇 %인가?

**개념:** 상용 서비스가 커질수록 inference 비중은 상승하지만, frontier training과 post-training capacity는 계속 남습니다.

**초기 학습 band:** 2026 Base: 50-60%, 2030 Base: 65-80%

**주의할 오류:** 2026년 60%+를 fact로 표현

**관련 source:** SRC_OPENAI_STARGATE; SRC_GOOGLE_IRONWOOD

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M4. 모델 파라미터와 MoE

**핵심 질문:** total parameter와 token당 active parameter가 어떻게 다른가?

**개념:** Dense 모델은 대부분의 parameter가 매 token 계산에 관여하지만, MoE는 일부 expert만 activate되어 active parameter가 훨씬 낮습니다.

**초기 학습 band:** Dense: active ~= total, MoE: active/total 3-20%

**주의할 오류:** MoE total parameter만 보고 inference 비용을 과대평가

**관련 source:** SRC_DEEPSEEK_V3; SRC_QWEN3

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M5. GPU/ASIC mix

**핵심 질문:** NVIDIA GPU, TPU, Trainium, 자체 ASIC이 토큰 효율에 주는 영향은?

**개념:** 동일 MW라도 hardware generation, memory bandwidth, interconnect, serving software에 따라 tokens/sec/MW가 크게 달라집니다.

**초기 학습 band:** GPU-heavy: 낮은 custom efficiency, TPU/ASIC-heavy: 높은 serving efficiency 가능

**주의할 오류:** GPU 수만 세고 accelerator 세대와 utilization을 무시

**관련 source:** SRC_GOOGLE_IRONWOOD; SRC_NVIDIA_H100

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M6. Tokens/sec/MW

**핵심 질문:** 1MW inference load가 초당 몇 token을 만들 수 있는가?

**개념:** tokens/sec/MW는 모델 크기, active parameter, batch size, context length, KV cache, quantization, speculative decoding의 합성 결과입니다.

**초기 학습 band:** closed model: proxy band만 사용, open MoE: active parameter로 sanity check

**주의할 오류:** benchmark 값을 회사별 실제 성능처럼 확정

**관련 source:** SRC_ARXIV_ENERGY_TOKEN; SRC_DEEPSEEK_V3

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M7. Utilization

**핵심 질문:** 이론 capacity 중 실제 토큰으로 변환되는 비율은?

**개념:** 실제 utilization은 traffic shape, latency SLA, batch 가능성, regional placement, failover reserve 때문에 100%가 될 수 없습니다.

**초기 학습 band:** 2026: 45-65%, 2030: 60-80%

**주의할 오류:** peak throughput을 연중 평균 throughput으로 사용

**관련 source:** SRC_ARXIV_ENERGY_TOKEN

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

### M8. Attribution

**핵심 질문:** 누구의 전력 capacity를 누구의 token으로 귀속할 것인가?

**개념:** AWS, Oracle, Google Cloud capacity는 hosting이고, token owner는 Claude, GPT, Gemini 등 model owner 기준으로 귀속합니다.

**초기 학습 band:** capacity owner != model owner인 경우 attribution rule 필수

**주의할 오류:** OpenAI/Microsoft, Anthropic/AWS, OpenAI/Oracle 중복 계산

**관련 source:** SRC_OPENAI_STARGATE

**연습:**

1. 이 가정이 10% 올라가면 token forecast가 얼마나 바뀌는지 계산한다.
2. 이 가정을 fact로 바꿀 수 있는 공식 source가 있는지 찾는다.
3. 공식 source가 없다면 estimate/proxy/scenario 중 어디에 속하는지 표시한다.

## 숫자를 현실적으로 만드는 5단계

1. 먼저 단위를 고정한다: GW, MW, tokens/sec/MW, tokens/day, annual tokens.
2. 그 다음 physical boundary를 확인한다: active <= contracted, inference+training=100%.
3. 모델 구조를 확인한다: dense인지 MoE인지, active parameter가 공개되어 있는지.
4. benchmark와 비교한다: GPU count 방식과 tokens/MW 방식이 크게 벌어지는지.
5. 마지막으로 문구를 조정한다: fact, estimate, proxy, scenario를 분리한다.

## Calibration Exercises

### Exercise A: Planned GW와 Active GW

OpenAI/Stargate 같은 planned capacity 발표를 보고 active_power_gw를 바로 같게 두지 말고, 2026/2030 deployment ratio를 별도로 둡니다.

질문:

- 발표 문구가 planned, contracted, committed, operational 중 무엇인가?
- 데이터센터가 energized 되었는가?
- GPU rack delivery와 cooling이 같이 확인되었는가?
- training/inference workload가 시작됐다는 문구가 있는가?

### Exercise B: MoE Parameter

DeepSeek-V3처럼 671B total / 37B active가 공개된 모델은 total parameter만 보고 token cost를 계산하면 안 됩니다.

질문:

- active parameter가 token당 기준인가?
- MTP, speculative decoding, quantization이 serving에 영향을 주는가?
- context length가 길어질 때 prefill/KV cache 비용이 늘어나는가?

### Exercise C: Benchmark 괴리

main forecast와 benchmark reference가 50% 이상 차이 나면 숫자가 틀렸다고 단정하지 말고 먼저 원인을 분해합니다.

- 모델 active parameter proxy가 너무 낮거나 높은가?
- GPU count 추정이 facility power와 accelerator board power를 혼동했는가?
- utilization을 peak 기준으로 둔 것은 아닌가?
- TPU/ASIC custom efficiency를 NVIDIA GPU 기준으로 비교하고 있지는 않은가?

## Source Reading List

| source_id | title | publisher | date | learning use |
|---|---|---|---|---|
| SRC_GOOGLE_IRONWOOD | [Ironwood: The first Google TPU for the age of inference](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/ironwood-tpu-age-of-inference/) | Google Cloud | 2025-04-09 | TPU pod, inference-oriented accelerator, HBM, perf/W 학습 anchor |
| SRC_OPENAI_STARGATE | [OpenAI, Oracle, and SoftBank expand Stargate with five new AI data center sites](https://openai.com/index/five-new-stargate-sites/) | OpenAI | 2025-09-23 | planned GW와 active AI IT load를 분리해야 하는 이유 |
| SRC_DEEPSEEK_V3 | [DeepSeek-V3 GitHub / Technical Report](https://github.com/deepseek-ai/DeepSeek-V3) | DeepSeek | 2024-12-26 | MoE total parameter와 active parameter 분리 |
| SRC_QWEN3 | [Qwen3 GitHub](https://github.com/QwenLM/Qwen3) | Alibaba Qwen | 2025 | MoE 모델의 active parameter와 thinking/non-thinking serving 차이 |
| SRC_NVIDIA_H100 | [NVIDIA H100 Tensor Core GPU](https://www.nvidia.com/en-us/data-center/h100/) | NVIDIA | accessed 2026-05-14 | GPU TDP와 rack/facility power는 다르다는 점 |
| SRC_ARXIV_ENERGY_TOKEN | [Energy Use of AI Inference: Efficiency Pathways and Test-Time Compute](https://arxiv.org/abs/2509.20241) | arXiv | 2025 | query/token 단위 에너지 모델링과 test-time compute 민감도 |

## Next Study Loop

매주 한 가정만 골라서 다음 순서로 공부합니다.

1. 공식 source 2개 읽기
2. 숫자 3개만 추출하기
3. fact/estimate/proxy/scenario로 분류하기
4. 현재 모델의 값과 비교하기
5. 차이가 나면 assumption_change_log.md에 후보 변경으로 기록하기
